# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: all
#     notebook_metadata_filter: all,-language_info
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.13.7
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# + trusted=true
import pandas as pd
import numpy as np
from statsmodels.stats.proportion import proportions_ztest, proportions_chisquare
import statsmodels.api as sm

# + trusted=true
import sys
from pathlib import Path
import os
cwd = os.getcwd()
parent = str(Path(cwd).parents[0])
sys.path.append(parent)

# + trusted=true
#importing custom functions for analysis

from lib.functions import ci_calc, z_test, summarizer, check_dupes, simple_logistic_regression, crosstab

#ci_calc will compute a simple confidence interval around a proportion
#summarizer gives a nice output of proportions and CIs and returns and item with them
#check_dupes helps with the date analysis
#simple_logicstic_regression and crosstab do what they say on the tin
# -

# # Data Loading and Setup

# + trusted=true
#Loading in all the data and creating the analysis dataset.

#Primary dataset with dates turned into dates
df = pd.read_csv(parent + '/data/final_dataset/final_dataset.csv')
df['euctr_results_date'] = pd.to_datetime(df['euctr_results_date'])
df['ctgov_results_date'] = pd.to_datetime(df['ctgov_results_date'])
df['isrctn_results_date'] = pd.to_datetime(df['isrctn_results_date'])
df['journal_pub_date'] = pd.to_datetime(df['journal_pub_date'])

#Manually collected sponsor data for regression
regression = pd.read_csv(parent + '/data/additional_data/manual_reg_data.csv')

#Regression data derived from the EUCTR
other_reg_data = pd.read_csv(parent + '/data/additional_data/spon_country_data.csv')

#the original sample (and replacements) for data on inferred dates
sample = pd.read_csv(parent + '/data/samples/euctr_search_sample_final.csv')
replacements  = pd.read_csv(parent + '/data/samples/replacement_sample.csv')
full_sample = pd.concat([sample,replacements])

#the results section scrape and making one column we need into dates
dec_results = pd.read_csv(parent + '/data/source_data/' + 'euctr_data_quality_results_scrape_dec_2020.csv.zip')
dec_results['first_version_date'] = pd.to_datetime(dec_results.first_version_date)
# + trusted=true
#Setting search reference dates
search_start_date = pd.to_datetime('2020-12-11')
primary_search_completion_date = pd.to_datetime('2021-07-22')
last_search_any = pd.to_datetime('2023-01-03')
# -

# # Analysis Prep

# ## Detail the exclusions and get the inferred status of the final sample

# + trusted=true
#Number and reason for exclusions
exclusions = df[df.replaced == 1]
exclusions.replaced_reason.value_counts()

# + trusted=true
sample_inferred_status = df[df.replaced.isna()][['euctr_id']].merge(full_sample[['eudract_number', 'inferred']], how='left', left_on='euctr_id', right_on='eudract_number')

# + trusted=true
#Inferred completion date status of the final sample
sample_inferred_status.inferred.value_counts()

# + trusted=true
exclusions_inferred_status = exclusions[['euctr_id']].merge(full_sample[['eudract_number', 'inferred']], how='left', left_on='euctr_id', right_on='eudract_number')

# + trusted=true
#Inferred completion date status of the trials we had to replace
exclusions_inferred_status.inferred.value_counts()
# -

# ## Setting up the analysis dataset

# + trusted=true
#For the analysis, we don't want to include these excluded trials so we will make an analyses dataframe moving forward.
analysis_df = df[df.replaced != 1].reset_index(drop=True)

#Quick check the final dataset is the length we expect
assert(len(analysis_df) == 500)

# + trusted=true
#Here we make binary variable to indicate whether recorded results were published after our cutoff. 
#Per protocol, nothing available after we began searches should be included in the final results.
#Creating binary variables allows us to only correct for this once, rather than have to keep doing it throughout.

#Included EUCTR results
analysis_df['euctr_results_inc'] = np.where((analysis_df.euctr_results == 'Yes') & 
                                            (analysis_df.euctr_results_date <= search_start_date), 1, 0)

#Included clinicaltrials.gov results
analysis_df['ctgov_results_inc'] = np.where((analysis_df.ctgov_results == 'Yes') & 
                                            (analysis_df.ctgov_results_date <= search_start_date), 1, 0)

#Included ISRCTN results
analysis_df['isrctn_results_inc'] = np.where((analysis_df.isrctn_results == 'Yes') & 
                                            (analysis_df.isrctn_results_date <= search_start_date), 1, 0)

#Included journal results
analysis_df['journal_results_inc'] = np.where((analysis_df.journal_result == 'Yes') & 
                                            (analysis_df.journal_pub_date <= search_start_date), 1, 0)

#A catch-all for any result
analysis_df['any_results_inc'] = np.where(((analysis_df.euctr_results_inc == 1) | 
                                          (analysis_df.ctgov_results_inc == 1) | 
                                          (analysis_df.isrctn_results_inc == 1) | 
                                          (analysis_df.journal_results_inc == 1)), 1, 0)

# + trusted=true
#Exporting the analysis dataset so it can be used elsewhere.

analysis_df.to_csv(parent + '/data/final_dataset/' + 'analysis_df.csv')

# + [markdown] tags=[]
# # Main Analysis

# + trusted=true
analysis_df.head()

# + trusted=true
full_sample.head()

# + trusted=true
temp = analysis_df.merge(full_sample[['eudract_number', 'inferred']], how='left', left_on='euctr_id', right_on='eudract_number')

# + trusted=true
temp2.columns

# + trusted=true
temp2 = temp[temp.inferred == 1]
temp2[(temp2.nct_id.notnull()) | (temp2.isrctn_id.notnull()) | (temp2.journal_results_inc == 1)]
# -

# ## Results on the EUCTR

# + trusted=true
euctr_results = analysis_df[(analysis_df.euctr_results_inc == 1)]
total_found_euctr = len(euctr_results)
summarizer(total_found_euctr, len(analysis_df))

# + trusted=true
#What do these results look like?
euctr_results.euctr_results_format.value_counts()


# + trusted=true
#Lets get percents and CIs for these.
results_types = euctr_results.euctr_results_format.value_counts().to_frame()
results_types['percent'] = round((results_types.euctr_results_format / total_found_euctr) * 100,2)

#Adding CIs (i'm sure there's a more elegant way to do this with .map() or .apply() 
#but it's too much of a weird edge case to bother
ci_lower = []
ci_upper = []
for x in results_types.euctr_results_format.to_list():
    cis = ci_calc(x, total_found_euctr, printer=False)
    ci_lower.append(round(cis[0] * 100,2))
    ci_upper.append(round(cis[2] * 100,2))
    
results_types['ci_lower'] = ci_lower
results_types['ci_upper'] = ci_upper

results_types = results_types.reset_index().rename(columns={'index':'results_type'})
results_types
# + trusted=true
#Now we want to group like with like to get our final descriptive stats to report

#Total with just tabular results
summarizer(results_types[results_types.results_type == 'Tabular'].euctr_results_format[0], total_found_euctr)

# + trusted=true
#Total with just a Document
doc_types = ['CSR Synopsis', 
             'ClinicalTrials.gov Results', 
             'Journal Article', 
             'Short Report', 
             'Report', 
             'Notice of termination with low enrollment']
ci_calc(results_types[results_types.results_type.isin(doc_types)].euctr_results_format.sum(), total_found_euctr)

# + trusted=true
#Total with both Tabular and Document results
ci_calc(results_types[~results_types.results_type.isin(doc_types + ['Tabular'])].euctr_results_format.sum(), total_found_euctr)
# -

# ## Cross-Registration and results availability on other registries

# + trusted=true
#First we'll look at cross-registration on ClinicalTrials.gov
ctg_xreg = analysis_df[analysis_df.nct_id.notnull()]
print(f'Out of {len(analysis_df)} trials {len(ctg_xreg)} were cross-registered on ClinicalTrials.gov')
ci_calc(len(ctg_xreg),len(analysis_df))

# + trusted=true
#CTG x-reg results rate
ctg_results = ctg_xreg[(ctg_xreg.ctgov_results_inc == 1)]
print(f'Of the {len(ctg_xreg)} trials registered on ClinicalTrials.gov, {len(ctg_results)} had results')
ci_calc(len(ctg_results), len(ctg_xreg))

# + trusted=true
#Proportion cross-registered on the ISRCTN 
isrctn_xreg = analysis_df[analysis_df.isrctn_id.notnull()]
print(f'Out of {len(analysis_df)} trials {len(isrctn_xreg)} were cross-registered on the ISRCTN')
ci_calc(len(isrctn_xreg), len(analysis_df))

# + trusted=true
#ISRCTN x-reg results rate
isrctn_results = isrctn_xreg[(isrctn_xreg.isrctn_results_inc == 1)]
print(f'Of the {len(isrctn_xreg)} trials registered on the ISRCTN, {len(isrctn_results)} had results')
ci_calc(len(isrctn_results), len(isrctn_xreg))

# + trusted=true
#How many trials registered on all three registries
triple_reg = len(analysis_df[analysis_df.nct_id.notnull() & analysis_df.isrctn_id.notnull()])
print(f'{triple_reg} registered on all three registires')
ci_calc(triple_reg, len(analysis_df))
# -

# ## Results in the literature

# + trusted=true
#How many had results in the literature
journal_results = analysis_df[(analysis_df.journal_results_inc == 1)]
print(f'Out of {len(analysis_df)} trials on the EUCTR, {len(journal_results)} had results in the literature')
ci_calc(len(journal_results), len(analysis_df))

# + trusted=true
#How did we find journal results?

journal_results.journal_source.value_counts()
# -

# ## Summarizing results availability

# + trusted=true
#Getting lists of ids for all results types

all_trial_ids = set(analysis_df.euctr_id.to_list())
euctr_results_ids = set(euctr_results.euctr_id.to_list())
ctg_results_ids = set(ctg_results.euctr_id.to_list())
isrctn_results_ids = set(isrctn_results.euctr_id.to_list())
journal_results_ids = set(journal_results.euctr_id.to_list())

# + trusted=true
#Overall, inclusive of duplicates, how many results did we locate?
len(euctr_results_ids) + len(ctg_results_ids) + len(isrctn_results_ids) + len(journal_results_ids)

# + trusted=true
#How many had results anywhere?
results_nowhere = all_trial_ids - euctr_results_ids - ctg_results_ids - isrctn_results_ids - journal_results_ids
has_some_result = len(analysis_df) - len(results_nowhere)
#sense check
assert(len(results_nowhere) + has_some_result == 500)

print(f'{has_some_result} of {len(analysis_df)} trials had results somewhere')
ci_calc(has_some_result,len(analysis_df))

# + trusted=true
#What did enrollment look like for the trials with no results?
#This uses enrollment numbers from the manual data we collected on enrollment

no_results = analysis_df[analysis_df.euctr_id.isin(results_nowhere)].reset_index(drop=True)
no_results[['euctr_id']].merge(regression[['Trial ID', 'Enrollment']], how='left', left_on='euctr_id', right_on='Trial ID').Enrollment.sum()
# -

# ## What results were unique to each dissemination route?

# + trusted=true
#How many had results on just the EUCTR?
just_euctr = len(euctr_results_ids - ctg_results_ids - isrctn_results_ids - journal_results_ids)
print(f'{just_euctr} trials had results on just the EUCTR')
ci_calc(just_euctr, len(euctr_results))

# + trusted=true
#What did the distribution of documents look like for unique results

just_euctr_ids = euctr_results_ids - ctg_results_ids - isrctn_results_ids - journal_results_ids
euctr_results[euctr_results.euctr_id.isin(just_euctr_ids)].euctr_results_format.value_counts()

# + trusted=true
#How many had results on just on ClinicalTrials.gov?
just_ctg = len(ctg_results_ids - euctr_results_ids - isrctn_results_ids - journal_results_ids)
print(f'{just_ctg} trials had results on just ClinicalTrials.gov')
ci_calc(just_ctg,len(ctg_results))

# + trusted=true
#How many had results on just on the ISRCTN?
just_isrctn = len(isrctn_results_ids - euctr_results_ids - ctg_results_ids - journal_results_ids)
print(f'{just_isrctn} trials had results on just the ISRCTN')

# + trusted=true
#How many had results just in the literature?
just_pub = len(journal_results_ids - euctr_results_ids - ctg_results_ids - isrctn_results_ids)
print(f'{just_pub} trials had results only in a journal publication')
ci_calc(just_pub,len(journal_results))

# + trusted=true
#How many have no results on the EUCTR but results anywhere else?
not_euctr = analysis_df[(analysis_df.euctr_results_inc == 0) & ((analysis_df.ctgov_results_inc == 1) | 
                                                               (analysis_df.isrctn_results_inc == 1) | 
                                                               (analysis_df.journal_results_inc == 1))]
print(f'{len(not_euctr)} trials without EUCTR results had results somewhere else')
ci_calc(len(not_euctr), len(analysis_df))

# + trusted=true
#How many had results nowhere?
print(f'{len(results_nowhere)} trials had no results located')
ci_calc(len(results_nowhere), len(analysis_df))
# -

# ## Getting data on combinations of results availability
#
# We will visualise these in an upset chart in the paper

# + trusted=true
upset_plot_data = analysis_df[['euctr_results_inc', 'ctgov_results_inc', 'isrctn_results_inc', 'journal_results_inc']]

upset_plot_data.to_csv(parent + '/data/graphing_data/upset_data.csv')
# -

# # Data Quality, Completion Status, and Reporting
#
# For overall population numbers, see the `Data Processing` notebooke

# + trusted=true
#Making a new DF for this population to investiage results availability by inferred and available completion dates

analysis_df_2 = analysis_df.merge(full_sample[['eudract_number', 'inferred']], 
                                  how='left', 
                                  left_on='euctr_id', right_on='eudract_number').drop('eudract_number', axis=1)

inferred = analysis_df_2[analysis_df_2.inferred == 1]
print(f'Inferred: {len(inferred)}; {round((len(inferred)/len(analysis_df_2)) * 100, 2)}%')
stated = analysis_df_2[analysis_df_2.inferred == 0]
print(f'Stated: {len(stated)}; {round((len(stated)/len(analysis_df_2)) * 100, 2)}%')

# + trusted=true
#How many of the inferred ones had results anywhere?
inferred_res_sw = len(inferred[(inferred.euctr_results_inc == 1) | (inferred.ctgov_results_inc == 1) | (inferred.isrctn_results_inc == 1) | (inferred.journal_results_inc == 1)])
print(f'Inferred Dates with any results: {inferred_res_sw}')
print(f'Total inferred dates: {len(inferred)}')
ci_calc(inferred_res_sw, len(inferred))

# + trusted=true
#How many of the extracted ones had results anywhere?
stated_res_sw = len(stated[(stated.euctr_results_inc == 1) | (stated.ctgov_results_inc == 1) | (stated.isrctn_results_inc == 1) | (stated.journal_results_inc == 1)])
print(f'Extracted with any results: {stated_res_sw}')
print(f'Total extracted dates: {len(stated)}')
ci_calc(stated_res_sw, len(stated))

# + trusted=true
#a is the number of trials with results
#b is the total number of trials

a = [inferred_res_sw, stated_res_sw]
b = [len(inferred),len(stated)]

stat, pval = proportions_ztest(a, b)
print(pval)

# + trusted=true
#How many of the inferred ones had results somewhere else?
inferred_res_swe = len(inferred[(inferred.ctgov_results_inc == 1) | (inferred.isrctn_results_inc == 1) | (inferred.journal_results_inc == 1)])
print(f'Inferred with results outside the EUCTR: {inferred_res_swe}')
print(f'Total Inferred: {len(inferred)}')
ci_calc(inferred_res_swe, len(inferred))

# + trusted=true
#How many of the extracted ones had results somewhere else?
stated_res_swe = len(stated[(stated.ctgov_results_inc == 1) | (stated.isrctn_results_inc == 1) | (stated.journal_results_inc == 1)])
print(f'Extracted with results outside the EUCTR: {stated_res_swe}')
print(f'Total Extracted: {len(stated)}')
ci_calc(stated_res_swe, len(stated))

# + trusted=true
a = [inferred_res_swe, stated_res_swe]
b = [len(inferred),len(stated)]

stat, pval = proportions_ztest(a, b)
print(pval)
# -

# ## Now we have to do this for each registry

# + trusted=true
#EUCTR

#Results posted to EUCTR by date of search - stated
stated_results_euctr = stated[(stated.euctr_results_inc == 1)]
print(f'Extracted with EUCTR results: {len(stated_results_euctr)}')
print(f'Total extracted: {len(stated)}')
ci_calc(len(stated_results_euctr), len(stated))

print('\n')

#Results posted to EUCTR by date of search - inferred
inferred_results_euctr = inferred[(inferred.euctr_results_inc == 1)]
print(f'Inferred with EUCTR results: {len(inferred_results_euctr)}')
print(f'Total inferred: {len(inferred)}')
ci_calc(len(inferred_results_euctr), len(inferred))

# + trusted=true
a = [len(inferred_results_euctr), len(stated_results_euctr)]
b = [len(inferred),len(stated)]

stat, pval = proportions_ztest(a, b)
print(pval)

# + trusted=true
#CTG extracted dates
stated_ctg = stated[stated.nct_id.notnull()]
stated_ctg_results = stated_ctg[(stated_ctg.ctgov_results_inc == 1)]
print(f'Extracted with CTG results: {len(stated_ctg_results)}')
print(f'Total CTG extracted: {len(stated_ctg)}')
ci_calc(len(stated_ctg_results), len(stated_ctg))

print('\n')

#CTG inferred dates
inferred_ctg = inferred[inferred.nct_id.notnull()]
inferred_ctg_results = inferred_ctg[(inferred_ctg.ctgov_results_inc == 1)]
print(f'Inferred with CTG results: {len(inferred_ctg_results)}')
print(f'Total CTG inferred: {len(inferred_ctg)}')
ci_calc(len(inferred_ctg_results), len(inferred_ctg))

# + trusted=true
a = [len(inferred_ctg_results), len(stated_ctg_results)]
b = [len(inferred_ctg),len(stated_ctg)]

stat, pval = proportions_ztest(a, b)
print(pval)

# + trusted=true
#isrctn extracted dates
stated_isrctn = stated[stated.isrctn_id.notnull()]
stated_isrctn_results = stated_isrctn[(stated_isrctn.isrctn_results_inc == 1)]
print(f'Extracted with ISRCTN results: {len(stated_isrctn_results)}')
print(f'Total ISRCTN extracted: {len(stated_isrctn)}')
ci_calc(len(stated_isrctn_results), len(stated_isrctn))

print('\n')

#isrctn inferred dates
inferred_isrctn = inferred[inferred.isrctn_id.notnull()]
inferred_isrctn_results = inferred_isrctn[(inferred_isrctn.isrctn_results_inc == 1)]
print(f'Inferred with ISRCTN results:{len(inferred_isrctn_results)}')
print(f'Total ISRCTN extracted: {len(inferred_isrctn)}')
ci_calc(len(inferred_isrctn_results), len(inferred_isrctn))

# + trusted=true
a = [len(inferred_isrctn_results), len(stated_isrctn_results)]
b = [len(inferred_isrctn),len(stated_isrctn)]

stat, pval = proportions_ztest(a, b)
print(pval)

# + trusted=true
#journal extracted dates
stated_journal = stated[(stated.journal_results_inc == 1)]
print(f'Extracted with results in a Journal: {len(stated_journal)}')
print(f'Total Extracted: {len(stated)}')
ci_calc(len(stated_journal), len(stated))

print('\n')

#journal inferred dates
inferred_journal = inferred[(inferred.journal_results_inc == 1)]
print(f'Inferred with results in a Journal: {len(inferred_journal)}')
print(f'Total Inferred: {len(inferred)}')
ci_calc(len(inferred_journal), len(inferred))

# + trusted=true
a = [len(inferred_journal), len(stated_journal)]
b = [len(inferred),len(stated)]

stat, pval = proportions_ztest(a, b)
print(pval)
# -

# # Publication Date Analysis

# + trusted=true
date_df = analysis_df[['euctr_id', 'euctr_results', 'euctr_results_date', 'nct_id', 'ctgov_results', 'ctgov_results_date', 
             'isrctn_id', 'isrctn_results', 'isrctn_results_date', 'journal_result', 'journal_pub_date']].reset_index(drop=True)

earliest_results_date = dec_results.first_version_date.min()

# + trusted=true
#Sense checking to make sure there are no duplicate values
just_dates = date_df[['euctr_results_date','ctgov_results_date', 'isrctn_results_date', 'journal_pub_date']].reset_index(drop=True)
just_dates['test'] = just_dates.apply(check_dupes, axis=1)
just_dates.test.value_counts()

#There are no repeat dates so no need to worry about that.

# + trusted=true
#Getting rid of results dates from after we started searching
date_df['euctr_results_date'] = np.where(date_df['euctr_results_date'] > search_start_date, pd.NaT, date_df['euctr_results_date'])
date_df['euctr_results_date'] = pd.to_datetime(date_df['euctr_results_date'])

date_df['ctgov_results_date'] = np.where(date_df['ctgov_results_date'] > search_start_date, pd.NaT, date_df['ctgov_results_date'])
date_df['ctgov_results_date'] = pd.to_datetime(date_df['ctgov_results_date'])

date_df['isrctn_results_date'] = np.where(date_df['isrctn_results_date'] > search_start_date, pd.NaT, date_df['isrctn_results_date'])
date_df['isrctn_results_date'] = pd.to_datetime(date_df['isrctn_results_date'])

date_df['journal_pub_date'] = np.where(date_df['journal_pub_date'] > search_start_date, pd.NaT, date_df['journal_pub_date'])
date_df['journal_pub_date'] = pd.to_datetime(date_df['journal_pub_date'])

# + trusted=true
#Getting the earliest publication date for each trial
date_df['min_date'] = date_df[['euctr_results_date',
                               'ctgov_results_date', 
                               'isrctn_results_date', 
                               'journal_pub_date']].min(axis=1)

# + trusted=true
#Getting the total number of results available
date_df['results_counts'] = (date_df == 'Yes').T.sum()

# + [markdown] tags=[]
# ## Pre-EUCTR Results Section trials

# + trusted=true
#Trials that had a result of some kind before the EUCTR results section launched
pre_euctr = date_df[(date_df.min_date < earliest_results_date)].reset_index(drop=True)

print(len(pre_euctr))

# + trusted=true
#How many of these went on the publish a result on the EUCTR

print(len(pre_euctr[pre_euctr.euctr_results == 'Yes']))

ci_calc(95,135)

# + trusted=true
#Here we can extract where the earliest result was extracted for a given trial

conds = [pre_euctr.euctr_results_date == pre_euctr.min_date, 
         pre_euctr.ctgov_results_date == pre_euctr.min_date, 
         pre_euctr.isrctn_results_date == pre_euctr.min_date, 
         pre_euctr.journal_pub_date == pre_euctr.min_date]

out = ['EUCTR', 'CTgov', 'ISRCTN', 'Journal']

pre_euctr['earliest_results'] = np.select(conds, out, 'No Result')

# + trusted=true
#Lets now look at the distribution of where trials were first to report prior to the EUCTR
#This has to be limited to only trials that were also cross-registered on ClinicalTrials.gov to compare
#like with like
first_report_pre = pre_euctr[pre_euctr.nct_id.notnull()].earliest_results.value_counts()
first_report_pre

# + trusted=true
#Can use this to get the CIs for those
#Journals
ci_calc(first_report_pre[0],first_report_pre.sum())

# + trusted=true
#CT gov
ci_calc(first_report_pre[1],first_report_pre.sum())

# + [markdown] tags=[]
# ## Post-EUCTR Results Section Trials

# + trusted=true
#Make the sample
post_euctr = date_df[(date_df.min_date >= earliest_results_date)].reset_index(drop=True)

#Trials with any result after the launch of the EUCTR results section
print(len(post_euctr))

# + trusted=true
#How many of these ended up on the EUCTR at all
len(post_euctr[post_euctr.euctr_results == 'Yes'])

# + trusted=true
#And the CI for that
ci_calc(len(post_euctr[post_euctr.euctr_results == 'Yes']),len(post_euctr))

# + trusted=true
#Adding the earliest dissemination route

conds = [post_euctr.euctr_results_date == post_euctr.min_date, 
         post_euctr.ctgov_results_date == post_euctr.min_date, 
         post_euctr.isrctn_results_date == post_euctr.min_date, 
         post_euctr.journal_pub_date == post_euctr.min_date]

out = ['EUCTR', 'CTgov', 'ISRCTN', 'Journal']

post_euctr['earliest_results'] = np.select(conds, out, 'No Result')

# + trusted=true
first_report_post = post_euctr[post_euctr.nct_id.notnull()].earliest_results.value_counts()
first_report_post

# + trusted=true
first_report_post.sum()

# + trusted=true
#Journal CIs
ci_calc(first_report_post[0], first_report_post.sum())

# + trusted=true
#EUCTR CIs
ci_calc(first_report_post[1], first_report_post.sum())

# + trusted=true
#CTG CIs
ci_calc(first_report_post[2], first_report_post.sum())

# + trusted=true
#What about trials not on ClinicalTrials.gov.
#We can ignore the trial with the earliest ISRCTN result here
first_pub_no_ctg = post_euctr[(post_euctr.nct_id.isna())].earliest_results.value_counts()
first_pub_no_ctg

# + trusted=true
#CI for journal
ci_calc(first_pub_no_ctg[0],first_pub_no_ctg.sum() - 1)

# + trusted=true
#CI for EUCTR
ci_calc(first_pub_no_ctg[1],first_pub_no_ctg.sum()- 1)

# + trusted=true
#CI for ISRCTN
ci_calc(first_pub_no_ctg[2],first_pub_no_ctg.sum())
# -

# ## Data for Start Year Figure
#
# Here we just get the data we would need and export it. Figures are made in a separate notebook.

# + trusted=true
graphing_df = analysis_df[['euctr_id', 
                           'euctr_results_inc', 
                           'any_results_inc']].merge(regression[['Trial ID', 
                                                                 'Trial Start Year']], 
                                                    how='left', left_on='euctr_id', right_on='Trial ID').drop('Trial ID', axis=1)

graphing_df.to_csv(parent + '/data/graphing_data/start_year_data.csv')
# -

# # Reporting of Trial IDs
#
# Might need to re-adjust this so that only things eligible to have that ID (i.e. registered there) are in the denom

# + trusted=true
trial_id_df = analysis_df[['euctr_id', 'nct_id', 'isrctn_id', 'journal_results_inc', 'journal_reg_numbers']].reset_index(drop=True)

# + trusted=true
reg_id_df = trial_id_df[trial_id_df.journal_results_inc == 1].journal_reg_numbers.value_counts(dropna=False).to_frame().reset_index()

# + trusted=true
#How many EUCTR/Publication pairs had an EUCTR ID

euctr_pub_ids = trial_id_df[(trial_id_df.journal_results_inc == 1) & (trial_id_df.euctr_id.notnull())]
print(f'There are {len(euctr_pub_ids)} trials with an EUCTR registration and a matched publication')
print(f'Below are the ones with a Trial ID excluding the {euctr_pub_ids.journal_reg_numbers.value_counts()["None"]} with no ID')
euctr_id_match = euctr_pub_ids[euctr_pub_ids.journal_reg_numbers != 'None'].journal_reg_numbers.value_counts()
euctr_id_match

# + trusted=true
#Stats on number containing an EUCTR ID
summarizer(euctr_id_match.filter(like='EUCTR/EudraCT').sum(), len(euctr_pub_ids))

# + trusted=true
#How many CTG/Publication pairs had an NCT ID

ctg_pub_ids = trial_id_df[(trial_id_df.journal_results_inc == 1) & (trial_id_df.nct_id.notnull())]
print(f'There are {len(ctg_pub_ids)} trials with a ClinicalTrials.gov registration and a matched publication')
print(f'Below are the ones with a Trial ID excluding the {ctg_pub_ids.journal_reg_numbers.value_counts()["None"]} with no ID')
ctg_id_match = ctg_pub_ids[ctg_pub_ids.journal_reg_numbers != 'None'].journal_reg_numbers.value_counts()
ctg_id_match

# + trusted=true
#Stats on number containing an NCT ID
summarizer(ctg_id_match.filter(like='ClinicalTrials.gov').sum(), len(ctg_pub_ids))

# + trusted=true
#How many EUCTR/Publication pairs had an ISRCTN ID

isrctn_pub_ids = trial_id_df[(trial_id_df.journal_results_inc == 1) & (trial_id_df.isrctn_id.notnull())]
print(f'There are {len(isrctn_pub_ids)} trials with an ISRCTN registration and a matched publication')
print(f'Below are the ones with a Trial ID excluding the {isrctn_pub_ids.journal_reg_numbers.value_counts()["None"]} with no ID')
isrctn_id_match = isrctn_pub_ids[isrctn_pub_ids.journal_reg_numbers != 'None'].journal_reg_numbers.value_counts()
isrctn_id_match

# + trusted=true
#Stats on number containing an ISRCTN ID
summarizer(isrctn_id_match.filter(like='ISRCTN').sum(), len(isrctn_pub_ids))
# -

# # Exploratory Analayses

# + trusted=true
#Creating the exploratory analysis dataset through merging a few different DFs 
#and aligning the columns for ease of use.

exploratory_final = analysis_df[['euctr_id', 'euctr_results_inc', 'ctgov_results_inc', 'isrctn_results_inc', 
                                 'journal_results_inc', 'any_results_inc', 'nct_id', 'isrctn_id', 
                                 'journal_result']].merge(full_sample[['eudract_number', 
                                                                  'inferred']], 
                                                          how='left', 
                                                          left_on='euctr_id', 
                                                          right_on='eudract_number')

exploratory_final = exploratory_final.merge(regression, 
                                            how='left', 
                                            left_on='euctr_id', 
                                            right_on='Trial ID').drop(['eudract_number', 
                                                                       'Timestamp', 
                                                                       'Notes', 
                                                                       'Trial ID'], axis=1)

exploratory_final = exploratory_final.merge(other_reg_data, 
                                            how='left', 
                                            left_on='euctr_id', 
                                            right_on='trial_id').drop(['Unnamed: 0', 'trial_id'], axis=1)

exploratory_final.columns = ['euctr_id', 'euctr_results_inc', 'ctgov_results_inc', 'isrctn_results_inc', 
                             'journal_results_inc', 'any_results_inc', 'nct_id', 'isrctn_id', 'journal_result', 
                             'inferred', 'trial_start_yr', 'enrollment', 'location', 'sponsor_status', 
                             'protocol_country', 'sponsor_country']

# + trusted=true
exploratory_final.head()

# + trusted=true
exploratory_final[exploratory_final.enrollment.isna()]
# -

# Run the next two cells on the relevant variables in `exploratory_final` to get data for Table 1 of the paper.
#
# #We will run `.describe()` on `enrollment` and `protocol_country`
#
# #We will run `.value_counts()` on `sponsor_status`,`location`, and `trial_start_yr`

# + trusted=true
exploratory_final.protocol_country.describe()

# + trusted=true
exploratory_final.trial_start_yr.value_counts().sort_index()
# -

# ## Analysis 1: Regression

# + trusted=true
#Taking only what we need:
regression_final = exploratory_final[['euctr_id', 'euctr_results_inc', 'any_results_inc', 'inferred', 
                                      'trial_start_yr', 'enrollment', 'location', 'sponsor_status', 
                                      'protocol_country']].reset_index(drop=True)

regression_final = regression_final[regression_final.any_results_inc == 1].reset_index(drop=True)

regression_final = regression_final.join(pd.get_dummies(regression_final[['location', 'sponsor_status']]), how='left')

# + trusted=true
regression_final.location.value_counts()

# + trusted=true
y_reg = regression_final['euctr_results_inc'].reset_index(drop=True)
x_reg = regression_final[['inferred', 'trial_start_yr', 'enrollment',
                         'protocol_country', 'location_EEA and Non-EEA', 'location_Non-EEA', 
                         'sponsor_status_Commercial']].reset_index(drop=True)

# + trusted=true
simple_logistic_regression(y_reg, x_reg)
# -

# If we run the regression per protocol it will not converge because, as shown earlier, no trials with inferred completion dates have a result on the EUCTR making that a perfect predictor. I will therefore remove this from the regression as it is a derived variable anyway.

# + trusted=true
#Re-running the regression without the "inferred" variable
y_reg1 = regression_final['euctr_results_inc'].reset_index(drop=True)
x_reg1 = regression_final[['trial_start_yr', 'enrollment',
                         'protocol_country', 'location_EEA and Non-EEA', 'location_Non-EEA', 
                         'sponsor_status_Commercial']].reset_index(drop=True)

# + trusted=true
simple_logistic_regression(y_reg1, x_reg1)
# -

# Check univariable ORs here with any of these variables:
#
# `trial_start_yr`, `enrollment`, `protocol_country`, `location_EEA and Non-EEA`, `location_Non-EEA`, `sponsor_status_Commercial`

# + trusted=true
x_regu = regression_final[['location_EEA and Non-EEA', 'location_Non-EEA']].reset_index(drop=True)

simple_logistic_regression(y_reg1, x_regu)

# + trusted=true
#Holm-Bonferroni corrected thresholds
print(.05 / (7 - 1 + 1))
print(.05 / (7 - 2 + 1))
print(.05 / (7 - 3 + 1))
print(.05 / (7 - 4 + 1))
print(.05 / (7 - 5 + 1))
# -

# # Analysis 2: Sponsor Country
# Each trial will be assigned a “sponsor country” based on the most frequent sponsor country assigned in the EUCTR country protocols. A protocol of a specific country need not contain a sponsor from that country. If no single country appears most frequently, the trial will be coded as having “multi-country” sponsorship. The percent of trials reported to the EUCTR, other registries, and the literature will be reported for each unique sponsor country in the sample.

# + trusted=true
spon_country = exploratory_final[['euctr_id', 'nct_id', 'isrctn_id', 'journal_result', 'euctr_results_inc', 
                                  'ctgov_results_inc', 'isrctn_results_inc', 'journal_results_inc', 
                                  'any_results_inc', 'sponsor_country']].reset_index(drop=True)

# + trusted=true
#First for the EUCTR
spon_country_reporting = crosstab(spon_country, 'euctr_results_inc', 'sponsor_country').reset_index()
spon_country_reporting.columns = ['sponsor_country', 'not_reported', 'reported', 'all']
spon_country_reporting['prct_reported'] = round((spon_country_reporting.reported / spon_country_reporting['all'])*100,2)
spon_country_reporting.sort_values(by='all', ascending=False)

# + trusted=true
#Now for the other dissemination routes

#CTG
ct_gov_trials = spon_country[spon_country.nct_id.notnull()].reset_index(drop=True)
ctg_reporting = crosstab(ct_gov_trials, 'ctgov_results_inc', 'sponsor_country').reset_index()
ctg_reporting.columns = ['sponsor_country', 'not_reported', 'reported', 'all']
ctg_reporting['prct_reported'] = round((ctg_reporting.reported / ctg_reporting['all'])*100,2)
ctg_reporting.sort_values(by='all', ascending=False)

# + trusted=true
#ISRCTN
isrctn_trials = spon_country[spon_country.isrctn_id.notnull()].reset_index(drop=True)
isrctn_reporting = crosstab(isrctn_trials, 'isrctn_results_inc', 'sponsor_country').reset_index()
isrctn_reporting.columns = ['sponsor_country', 'not_reported', 'reported', 'all']
isrctn_reporting['prct_reported'] = (isrctn_reporting.reported / isrctn_reporting['all']) * 100
isrctn_reporting.sort_values(by='all', ascending=False)

# + trusted=true
#Journal Reporting
journal_reporting = crosstab(spon_country, 'journal_results_inc', 'sponsor_country').reset_index()
journal_reporting.columns = ['sponsor_country', 'not_reported', 'reported', 'all']
journal_reporting['prct_reported'] = round((journal_reporting.reported / journal_reporting['all'])*100,2)
journal_reporting.sort_values(by='all', ascending=False)

# + trusted=true
#Any Reporting
any_reporting = crosstab(spon_country, 'any_results_inc', 'sponsor_country').reset_index()
any_reporting.columns = ['sponsor_country', 'not_reported', 'reported', 'all']
any_reporting['prct_reported'] = round((any_reporting.reported / any_reporting['all'])*100,2)
any_reporting.sort_values(by='all', ascending=False)
# -








