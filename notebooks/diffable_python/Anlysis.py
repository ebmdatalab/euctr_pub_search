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
from scipy.stats import median_test
import matplotlib.pyplot as plt

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
#summarizer returns a nice output of proportions and CIs
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
last_search_any = pd.to_datetime('2023-08-16')
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
             'Notice of no analysis']
summarizer(results_types[results_types.results_type.isin(doc_types)].euctr_results_format.sum(), total_found_euctr)

# + trusted=true
for doc in doc_types:
    print(doc)
    summarizer(results_types[results_types.results_type == doc].euctr_results_format.sum(), total_found_euctr)
    print('\n')

# + trusted=true
#Reports

ci_calc(10,266)

# + trusted=true
#Tab and Document

ci_calc(16,266)

# + trusted=true
#Tab and CSR and Tab and Report

ci_calc(5,266)

# + trusted=true
#Total with both Tabular and Document results
summarizer(results_types[~results_types.results_type.isin(doc_types + ['Tabular'])].euctr_results_format.sum(), total_found_euctr)
# -

# ## Cross-Registration and results availability on other registries

# + trusted=true
#First we looks at unique registrations to the EUCTR
euctr_only_reg = analysis_df[analysis_df.nct_id.isna() & analysis_df.isrctn_id.isna()]
print(f'Out of {len(analysis_df)} trials {len(euctr_only_reg)} were only on the EUCTR')
ci_calc(len(euctr_only_reg), len(analysis_df))

# + trusted=true
#Now we'll look at cross-registration on ClinicalTrials.gov
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
summarizer(just_euctr, has_some_result)

# + trusted=true
#What did the distribution of documents look like for unique results

just_euctr_ids = euctr_results_ids - ctg_results_ids - isrctn_results_ids - journal_results_ids
euctr_results[euctr_results.euctr_id.isin(just_euctr_ids)].euctr_results_format.value_counts()

# + trusted=true
euctr_results[euctr_results.euctr_id.isin(just_euctr_ids)].euctr_results_format.value_counts().sum()

# + tags=[] trusted=true
# Values for appendix table

summarizer(1,55)

# + trusted=true
#How many had results on just on ClinicalTrials.gov?
just_ctg = len(ctg_results_ids - euctr_results_ids - isrctn_results_ids - journal_results_ids)
print(f'{just_ctg} trials had results on just ClinicalTrials.gov')
summarizer(just_ctg,has_some_result)

# + trusted=true
#How many had results on just on the ISRCTN?
just_isrctn = len(isrctn_results_ids - euctr_results_ids - ctg_results_ids - journal_results_ids)
print(f'{just_isrctn} trials had results on just the ISRCTN')

# + trusted=true
#How many had results just in the literature?
just_pub = len(journal_results_ids - euctr_results_ids - ctg_results_ids - isrctn_results_ids)
print(f'{just_pub} trials had results only in a journal publication')
summarizer(just_pub,has_some_result)

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

# + trusted=true
#How many trials had results somewhere that wasn't the EUCTR
outside_euctr = analysis_df[((analysis_df.ctgov_results_inc == 1) | 
                             (analysis_df.isrctn_results_inc == 1) | 
                             (analysis_df.journal_results_inc == 1))]
print(f'{len(outside_euctr)} had a result outside the EUCTR')
ci_calc(len(outside_euctr), len(analysis_df))
# -

# ## Getting data on combinations of results availability
#
# We will visualise these in an upset chart in the paper

# + trusted=true
upset_plot_data = analysis_df[['euctr_results_inc', 'ctgov_results_inc', 'isrctn_results_inc', 'journal_results_inc']]

#upset_plot_data.to_csv(parent + '/data/graphing_data/upset_data.csv')

cross_reg_upset = analysis_df[['euctr_id', 'nct_id', 'isrctn_id']]

#cross_reg_upset.to_csv(parent + '/data/graphing_data/upset_reg_data.csv')
# -

# # Data Quality, Completion Status, and Reporting
#
# For overall population numbers, see the `Data Processing` notebook

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

# + [markdown] tags=[]
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
#
# Due to the very low number of results, all but 1 of which was never the earliest, we are excluding ISRCTN from this analysis. You can verify this fact below using the original date_df dataframe.

# + trusted=true
date_df = analysis_df[['euctr_id', 'euctr_results_inc', 'euctr_results_date', 'nct_id', 'ctgov_results_inc', 'ctgov_results_date', 
             'isrctn_id', 'isrctn_results_inc', 'isrctn_results_date', 'journal_results_inc', 'journal_pub_date']].reset_index(drop=True)


#This is the earliest results available on the EUCTR
earliest_euctr_results_date = dec_results.first_version_date.min()
print(earliest_euctr_results_date)

# + trusted=true
#It's probably easiest to just blank out any dates of results that are excluded to make life easier
#We'll also remove ISRCTN
#Making a fresh copy so we can compare for sanity checks

date_df2 = date_df.drop(['isrctn_id', 'isrctn_results_inc', 'isrctn_results_date'], axis=1).reset_index(drop=True)

date_df2['euctr_results_date'] = pd.to_datetime(np.where((date_df2.euctr_results_inc == 0) & date_df2.euctr_results_date.notnull(), pd.NaT, date_df2.euctr_results_date))

date_df2['ctgov_results_date'] = pd.to_datetime(np.where((date_df2.ctgov_results_inc == 0) & date_df2.ctgov_results_date.notnull(), pd.NaT, date_df2.ctgov_results_date))

date_df2['journal_pub_date'] = pd.to_datetime(np.where((date_df2.journal_results_inc == 0) & date_df2.journal_pub_date.notnull(), pd.NaT, date_df2.journal_pub_date))

# + trusted=true
#Sense checking to make sure there are no duplicate date values for when we take mins and maxes
just_dates = date_df2[['euctr_results_date','ctgov_results_date', 'journal_pub_date']].reset_index(drop=True)
just_dates['test'] = just_dates.apply(check_dupes, axis=1)
just_dates.test.value_counts()

#There are no repeat dates so no need to worry about that.

# + trusted=true
#Getting the earliest and latest publication dates
date_df2['min_date'] = date_df2[['euctr_results_date',
                               'ctgov_results_date', 
                               'journal_pub_date']].min(axis=1)

date_df2['max_date'] = date_df2[['euctr_results_date',
                               'ctgov_results_date', 
                               'journal_pub_date']].max(axis=1)

# + trusted=true
#Getting the total number of results available 
date_df2['results_counts'] = (date_df2[['euctr_results_inc', 'ctgov_results_inc', 'journal_results_inc']].T.sum())
# -

# # Time to Reporting

# + trusted=true
conds = [date_df2.euctr_results_date == date_df2.min_date, 
         date_df2.ctgov_results_date == date_df2.min_date, 
         date_df2.journal_pub_date == date_df2.min_date]

out = ['EUCTR', 'CTgov', 'Journal']

date_df2['earliest_results'] = np.select(conds, out, 'No Result')

# + trusted=true
# All Trials

date_df2[date_df2.nct_id.notnull()].earliest_results.value_counts()

# + trusted=true
summarizer(156,291)

# + trusted=true
#Those with a first results

date_df2[(date_df2.nct_id.notnull()) & (date_df2.min_date < earliest_euctr_results_date) & (date_df2.journal_pub_date > pd.to_datetime('2008-09-30'))].earliest_results.value_counts()

# + trusted=true
summarizer(23,87)

# + trusted=true
date_df2[(date_df2.nct_id.notnull()) & (date_df2.min_date >= earliest_euctr_results_date)].earliest_results.value_counts()

# + trusted=true
summarizer(89,193)
# -

# # Data for Time to Reporting K-M Curves
#
# Code for medians and 95% CIs were done in the `Figures` notebook

# + trusted=true
#Make the sample
post_euctr = date_df2[(date_df2.min_date >= earliest_euctr_results_date)].reset_index(drop=True)

#Trials with a first result only after the launch of the EUCTR results section
print(len(post_euctr))

# + trusted=true
km_df = post_euctr.merge(full_sample, how='left', left_on='euctr_id', right_on='eudract_number')

km_df['final_date'] = pd.to_datetime(km_df['final_date'])

# + trusted=true
km_df['euctr_days'] = (km_df['euctr_results_date'] - km_df['final_date']) / pd.Timedelta(1,"d")

km_df['euctr_days'] = np.where(km_df['euctr_days'].isna(), 
                               (search_start_date - km_df['final_date']) / pd.Timedelta(1,"d"),
                               km_df['euctr_days'])

km_df['ctg_days'] = (km_df['ctgov_results_date'] - km_df['final_date']) / pd.Timedelta(1,"d")

km_df['ctg_days'] = np.where(km_df['ctg_days'].isna(), 
                               (search_start_date - km_df['final_date']) / pd.Timedelta(1,"d"),
                               km_df['ctg_days'])

km_df['pub_days'] = (km_df['journal_pub_date'] - km_df['final_date']) / pd.Timedelta(1,"d")

km_df['pub_days'] = np.where(km_df['pub_days'].isna(), 
                               (search_start_date - km_df['final_date']) / pd.Timedelta(1,"d"),
                               km_df['pub_days'])


# + trusted=true
km_df.to_csv(parent + '/data/graphing_data/time_to_pub.csv')
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

#graphing_df.to_csv(parent + '/data/graphing_data/start_year_data.csv')

# + [markdown] tags=[]
# # Reporting of Trial IDs

# + tags=[] trusted=true
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

# # Exploratory Analyses

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
exploratory_final.enrollment.describe()

# + trusted=true
exploratory_final.location.value_counts().sort_index()
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

# If we run the regression per protocol it leads to some funky results because of only including 1 trial with inferred results, as shown earlier. I will therefore remove this from the regression as it is a derived variable anyway.

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
# -

# p-values uni:
# com spon: <0.00001
# nonEEA: <0.0001
# prot_country: <0.0001
# enrollment: .05
# start_yr: 0.17209
# EEA/NonEEA: .02412
#
#

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
# # Peer Review Additions
#
# Additions to the analysis requested by, or added following, peer review

# ## Breakdown of results by sponsor type

# + trusted=true
full_sample

# + trusted=true
spon_results = analysis_df.merge(other_reg_data[['trial_id', 'sponsor_status']], 
                                 left_on='euctr_id', 
                                 right_on='trial_id', 
                                 how='left').merge(full_sample[['eudract_number', 'inferred']], 
                                                   left_on='euctr_id', 
                                                   right_on='eudract_number', 
                                                   how='left')

# + trusted=true
spon_results.columns

# + trusted=true
#All Results
crosstab(spon_results, 'any_results_inc', 'sponsor_status')

# + trusted=true
summarizer(240,277)
print('\n')
summarizer(143,222)

# + trusted=true
crosstab(spon_results[spon_results.inferred==0], 'any_results_inc', 'sponsor_status')

# + trusted=true
summarizer(233,260)
print('\n')
summarizer(79,94)

# + trusted=true
crosstab(spon_results[spon_results.inferred==1], 'any_results_inc', 'sponsor_status')

# + trusted=true
summarizer(7,17)
print('\n')
summarizer(64,128)

# + trusted=true
#a is the number of trials with results
#b is the total number of trials

a = [233, 7]
b = [260,17]

stat, pval = proportions_ztest(a, b)
print(pval)

# + trusted=true
a = [79, 64]
b = [94,128]

stat, pval = proportions_ztest(a, b)
print(pval)

# + trusted=true
#EUCTR
crosstab(spon_results, 'euctr_results_inc', 'sponsor_status')

# + trusted=true
summarizer(214,277)
print('\n')
summarizer(52,222)

# + trusted=true
#How many had results on just the EUCTR?
j_e = spon_results[spon_results.euctr_id.isin(euctr_results_ids - ctg_results_ids - isrctn_results_ids - journal_results_ids)]
crosstab(j_e, 'euctr_results_inc', 'sponsor_status')

# + trusted=true
summarizer(41,240)
print('\n')
summarizer(14,143)

# + trusted=true
crosstab(spon_results[spon_results.inferred==0], 'euctr_results_inc', 'sponsor_status')

# + trusted=true
summarizer(214,260)
print('\n')
summarizer(51,94)

# + trusted=true
crosstab(spon_results[spon_results.inferred==1], 'euctr_results_inc', 'sponsor_status')

# + trusted=true
summarizer(0,17)
print('\n')
summarizer(1,128)

# + trusted=true
#a is the number of trials with results
#b is the total number of trials

a = [214, 0]
b = [260,17]

stat, pval = proportions_ztest(a, b)
print(pval)

# + trusted=true
a = [51, 1]
b = [94,127]

stat, pval = proportions_ztest(a, b)
print(pval)

# + trusted=true
#ClinicalTrials.gov
crosstab(spon_results[spon_results.nct_id.notnull()], 'ctgov_results_inc', 'sponsor_status')

# + trusted=true
summarizer(129,235)
print('\n')
summarizer(4,104)

# + trusted=true
#How many had results on just CTgov?
j_c = spon_results[spon_results.euctr_id.isin(ctg_results_ids - euctr_results_ids - isrctn_results_ids - journal_results_ids)]
crosstab(j_c, 'ctgov_results_inc', 'sponsor_status')

# + trusted=true
summarizer(2,240)
print('\n')
summarizer(1,143)

# + trusted=true
crosstab(spon_results[(spon_results.inferred==0) & spon_results.nct_id.notnull()], 'ctgov_results_inc', 'sponsor_status')

# + trusted=true
summarizer(128,227)
print('\n')
summarizer(3,44)

# + trusted=true
crosstab(spon_results[(spon_results.inferred==1) & spon_results.nct_id.notnull()], 'ctgov_results_inc', 'sponsor_status')

# + trusted=true
summarizer(1,8)
print('\n')
summarizer(1,60)

# + trusted=true
#a is the number of trials with results
#b is the total number of trials

a = [128, 1]
b = [227,8]

stat, pval = proportions_ztest(a, b)
print(pval)

# + trusted=true
a = [3, 1]
b = [44, 60]

stat, pval = proportions_ztest(a, b)
print(pval)

# + trusted=true
#ISRCTN
crosstab(spon_results[spon_results.isrctn_id.notnull()], 'isrctn_results_inc', 'sponsor_status')

# + trusted=true
summarizer(0,2)
print('\n')
summarizer(2,30)

# + trusted=true
#The ISRCTN has no unique results

# + trusted=true
crosstab(spon_results[(spon_results.inferred==0) & spon_results.isrctn_id.notnull()], 'isrctn_results_inc', 'sponsor_status')

# + trusted=true
summarizer(0,2)
print('\n')
summarizer(2,27)

# + trusted=true
crosstab(spon_results[(spon_results.inferred==1) & spon_results.isrctn_id.notnull()], 'isrctn_results_inc', 'sponsor_status')

# + trusted=true
#a is the number of trials with results
#b is the total number of trials

a = [0,0]
b = [2,0]

stat, pval = proportions_ztest(a, b)
print(pval)

# + trusted=true
a = [2,0]
b = [27,3]

stat, pval = proportions_ztest(a, b)
print(pval)

# + trusted=true
#Journal Articles
crosstab(spon_results, 'journal_results_inc', 'sponsor_status')

# + trusted=true
summarizer(167,277)
print('\n')
summarizer(126,222)

# + trusted=true
#How many had results just in a journal?
j_e = spon_results[spon_results.euctr_id.isin(journal_results_ids - euctr_results_ids - isrctn_results_ids - ctg_results_ids)]
crosstab(j_e, 'journal_results_inc', 'sponsor_status')

# + trusted=true
summarizer(18,277)
print('\n')
summarizer(90,222)

# + trusted=true
crosstab(spon_results[(spon_results.inferred==0)], 'journal_results_inc', 'sponsor_status')

# + trusted=true
summarizer(160,260)
print('\n')
summarizer(64,94)

# + trusted=true
crosstab(spon_results[(spon_results.inferred==1)], 'journal_results_inc', 'sponsor_status')

# + trusted=true
summarizer(7,17)
print('\n')
summarizer(62,128)

# + trusted=true
#a is the number of trials with results
#b is the total number of trials

a = [160, 7]
b = [260,17]

stat, pval = proportions_ztest(a, b)
print(pval)

# + trusted=true
a = [64, 62]
b = [94,128]

stat, pval = proportions_ztest(a, b)
print(pval)

# + trusted=true
#Non-EUCTR
spon_results['non_euctr_results'] = np.where((spon_results.ctgov_results_inc==1) | 
                                             (spon_results.isrctn_results_inc==1) | 
                                             (spon_results.journal_results_inc==1), 1,0)

# + trusted=true
crosstab(spon_results, 'non_euctr_results', 'sponsor_status')

# + trusted=true
summarizer(199,277)
print('\n')
summarizer(129,222)

# + trusted=true
crosstab(spon_results[(spon_results.inferred==0)], 'non_euctr_results', 'sponsor_status')

# + trusted=true
summarizer(192,260)
print('\n')
summarizer(66,94)

# + trusted=true
crosstab(spon_results[(spon_results.inferred==1)], 'non_euctr_results', 'sponsor_status')

# + trusted=true
summarizer(7,17)
print('\n')
summarizer(63,128)

# + trusted=true
#a is the number of trials with results
#b is the total number of trials

a = [192, 7]
b = [260,17]

stat, pval = proportions_ztest(a, b)
print(pval)

# + trusted=true
a = [66, 63]
b = [94,128]

stat, pval = proportions_ztest(a, b)
print(pval)

# + trusted=true
print(.05 / (11 - 1 + 1))
print(.05 / (11 - 2 + 1))
print(.05 / (11 - 3 + 1))
print(.05 / (11 - 4 + 1))
print(.05 / (11 - 5 + 1))
print(.05 / (11 - 6 + 1))
print(.05 / (11 - 7 + 1))
print(.05 / (11 - 8 + 1))
# -

# ## Time to Searches
#
# Categorize the follow-up trials had.

# + trusted=true
#Lets make a copy of the sample data

sample2 = full_sample[full_sample.eudract_number.isin(analysis_df.euctr_id.to_list())].copy()

# + trusted=true
sample2['final_date'] = pd.to_datetime(sample2['final_date'])
sample2['days_to_search'] = (search_start_date - sample2['final_date']) / pd.Timedelta(1,"d")

# + trusted=true
sample2[sample2.inferred == 0].days_to_search.describe()

# + trusted=true
sample2[sample2.inferred == 1].days_to_search.describe()

# + trusted=true
#Moods test for independent medians

inferred_data = sample2[sample2.inferred == 1].days_to_search

extracted_data = sample2[sample2.inferred == 0].days_to_search

stat, p, med, tbl = median_test(inferred_data, extracted_data)
print(p)

# + trusted=true
#Data for plotting
#sample2[['inferred', 'days_to_search']].to_csv(parent + '/data/graphing_data/days_to_search.csv')
# -




