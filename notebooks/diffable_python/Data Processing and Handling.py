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
from datetime import date
from dateutil.relativedelta import relativedelta
from ast import literal_eval

# + trusted=true
import sys
from pathlib import Path
import os
cwd = os.getcwd()
parent = str(Path(cwd).parents[0])
sys.path.append(parent)

# + trusted=true
#importing custom functions for analysis

from lib.functions import status_exclude, group_dates, date_fix

# + trusted=true
#These are our scrapes of the full EUCTR protocol data and the EUCTR results data. 
#This data was scraped between 1 December and 3 December 2020

#Limiting to only the columns we need to save on memory
usecols = ['eudract_number', 
           'eudract_number_with_country', 
           'end_of_trial_status', 
           'trial_results', 
           'date_of_competent_authority_decision', 
           'date_of_ethics_committee_opinion', 
           'trial_in_the_member_state_concerned_years', 
           'trial_in_all_countries_concerned_by_the_trial_years', 
           'trial_in_the_member_state_concerned_months', 
           'trial_in_all_countries_concerned_by_the_trial_months', 
           'trial_in_all_countries_concerned_by_the_trial_days', 
           'trial_in_the_member_state_concerned_days', 
           'date_of_the_global_end_of_the_trial']

dec_results = pd.read_csv(parent + '/data/source_data/' + 'euctr_data_quality_results_scrape_dec_2020.csv.zip')

dec_full = pd.read_csv(parent + '/data/source_data/' + 'euctr_euctr_dump-2020-12-03-095517.csv.zip', low_memory=False, usecols=usecols)
# -

# First, we can quickly exclude all trials that appear to have never started in Europe because they were either "Not Authorised" or "Prohibited by CA" across all trial protocols.

# + trusted=true
#Taking the columns we need
#Applying custom imported function during groupby to combine multiple country protocols into 1 record and exclude trials
#In a status we don't want

trial_status = dec_full[['eudract_number', 
                         'eudract_number_with_country', 
                         'end_of_trial_status', 
                         'trial_results']].groupby('eudract_number').apply(status_exclude)

# + trusted=true
#Doing exclusions of the status

trial_status['never_started'] = np.where(trial_status.other_status == trial_status.number_of_countries, 1, 0)
never_started_exclusions = trial_status[trial_status.never_started == 1].index.to_list()

# + trusted=true
print(f'There are {len(never_started_exclusions)} trials that were never approved in the EU/EEA')

# + trusted=true
#Lets exclude those trial moving forward:

dec_started = dec_full[~dec_full.eudract_number.isin(never_started_exclusions)].reset_index(drop=True)

# + trusted=true
#checks
print(len(dec_full))
print(len(dec_started))
print(dec_full.eudract_number.nunique())
# -

# # Extracted End Dates

# + trusted=true
#First some data loading and housekeeping

#Taking only the columns we need from the protocol scrape and then merging in the results completion information.

dec_short = dec_started[['eudract_number', 'date_of_the_global_end_of_the_trial']]

merged_dates = dec_short.merge(dec_results[['trial_id', 'global_end_of_trial_date']], 
                               how='left', left_on='eudract_number', right_on='trial_id').drop('trial_id', axis=1)

#Renaming the columns and making the dates into dates
merged_dates.columns = ['eudract_number', 'protocol_completion', 'results_completion']

merged_dates['protocol_completion'] = pd.to_datetime(merged_dates['protocol_completion'])
merged_dates['results_completion'] = pd.to_datetime(merged_dates['results_completion'])

# + trusted=true
#Check on the data
merged_dates.head()
# -

# Here we use 2 functions, imported above, to help manage the data.
#
# 1. **group_dates** lets us collapse each trial into a single trial ID. Each row in this initial dataset reprents a country-level protocol, not an entire trial so some IDs are repeated. Even though the protocol completion date should hypothetically be the same across all the protocols, this is not guaranteed. During the groupby we take the latest completion date provided (or the "max"). To keep the dates together, we also take the max of the results_completion but this date will be the same across all entries with results. 
#
#
# 2. **date_fix** gets rid of obvious outlier dates with completion dates either before 2004 (i.e. before the EUCTR was created) or after 2020 (i.e. in the future and therefore should not exist yet since these dates are entered retrospectively). While some of these may not be mistakes, they obviously represent some sort of odd situation we would rather avoid. These are turned into null values where appropriate.

# + trusted=true
#Running the groupby

latest_dates = merged_dates.groupby('eudract_number', as_index=False).apply(group_dates).reset_index(drop=True)

# + trusted=true
#Lets see how many dates we are exluding with the date_fix

print(f'{len(latest_dates[(latest_dates["latest_completion_p"] < pd.to_datetime("2004-01-01")) | (latest_dates["latest_completion_p"] > pd.to_datetime("2020-12-31"))])}\
 replaced from the protocol dates')

print(f'{len(latest_dates[(latest_dates["latest_completion_r"] < pd.to_datetime("2004-01-01")) | (latest_dates["latest_completion_r"] > pd.to_datetime("2020-12-31"))])}\
 replaced from the results dates')

# + trusted=true
#If you are interested in these dates you can uncomment and run either of the following:

#latest_dates[(latest_dates["latest_completion_p"] < pd.to_datetime("2004-01-01")) | (latest_dates["latest_completion_p"] > pd.to_datetime("2020-12-31"))]

#latest_dates[(latest_dates["latest_completion_r"] < pd.to_datetime("2004-01-01")) | (latest_dates["latest_completion_r"] > pd.to_datetime("2020-12-31"))]

# + trusted=true
#Running the date fix

latest_dates['latest_completion_p'] = latest_dates['latest_completion_p'].apply(date_fix)
latest_dates['latest_completion_r'] = latest_dates['latest_completion_r'].apply(date_fix)

#Now we can take the results completion date when available, and the latest protocol completion date otherwise

latest_dates['available_completion'] = np.where(latest_dates.latest_completion_r.notnull(), 
                                            latest_dates.latest_completion_r, latest_dates.latest_completion_p)

# + trusted=true
latest_dates.head()

# + trusted=true
#Our final data is all of the trials with an "available_completion_date"
#This forms the population of trials in which we could extract a clear end date.

final_dates = latest_dates[latest_dates.available_completion.notnull()].reset_index(drop=True)
# -

# # Secondary Populations - Inferred End Date

# + trusted=true
#here is everything we couldn't infer an end date for.

no_completion = latest_dates[latest_dates.available_completion.isna()].reset_index(drop=True)

# + trusted=true
#We can use that data to create a new dataset, only with those trial IDs, 
#and with the columns we need from the original December protocol dataset.

inf_fields = ['eudract_number', 'eudract_number_with_country', 'date_of_competent_authority_decision', 
              'date_of_ethics_committee_opinion', 'trial_in_the_member_state_concerned_years', 
              'trial_in_all_countries_concerned_by_the_trial_years', 
              'trial_in_the_member_state_concerned_months', 
              'trial_in_all_countries_concerned_by_the_trial_months', 
              'trial_in_all_countries_concerned_by_the_trial_days', 
              'trial_in_the_member_state_concerned_days']

no_comp_inf = dec_full[inf_fields][dec_full[inf_fields].eudract_number.isin(no_completion.eudract_number.to_list())].reset_index(drop=True)

# + trusted=true
#Examining the dataset

no_comp_inf.head()

# + trusted=true
#Turning dates into dates.

no_comp_inf['date_of_competent_authority_decision'] = pd.to_datetime(no_comp_inf['date_of_competent_authority_decision'])
no_comp_inf['date_of_ethics_committee_opinion'] = pd.to_datetime(no_comp_inf['date_of_ethics_committee_opinion'])

#Creating a new column for the latest approval date within a protocol, and then doing a groupby, so we get the
#Latest approval date for the whole trial which we will use later.

no_comp_inf['latest_approval'] = no_comp_inf[['date_of_competent_authority_decision', 'date_of_ethics_committee_opinion']].max(axis=1)

latest_approval = no_comp_inf[['eudract_number', 'latest_approval']].groupby('eudract_number', as_index=False).max()

# + trusted=true
#Here we turn the day/month/year data we have on expected duration in days (assuming a month is 30 days)
#We do this across both the duration expected within country and globally and then take the longest of the two
#For each protocol and then once again we group to get the longest possible duration provided

no_comp_inf['country_days'] = ((no_comp_inf['trial_in_the_member_state_concerned_years'].fillna(0) * 364) + 
                               (no_comp_inf['trial_in_the_member_state_concerned_months'].fillna(0) * 30) + 
                               (no_comp_inf['trial_in_the_member_state_concerned_days'].fillna(0))) 

no_comp_inf['global_days'] = ((no_comp_inf['trial_in_all_countries_concerned_by_the_trial_years'].fillna(0) * 364) + 
                              (no_comp_inf['trial_in_all_countries_concerned_by_the_trial_months'].fillna(0) * 30) + 
                              (no_comp_inf['trial_in_all_countries_concerned_by_the_trial_days'].fillna(0)))

no_comp_inf['max_days'] = no_comp_inf[['country_days', 'global_days']].max(axis=1)

longest_duration = no_comp_inf[['eudract_number', 'max_days']].groupby('eudract_number', as_index=False).max()

# + trusted=true
#Now we can merge in the latest approval date and pick out the trial we can infer an end date for
#So we exclude trials that had 0 duration (meaning no information in these fields) and no approval dates

inferred_df = latest_approval.merge(longest_duration, how='left', on='eudract_number')

can_infer = inferred_df[(inferred_df.max_days != 0) & (inferred_df.latest_approval.notnull())].reset_index(drop=True)

# + trusted=true
#Saving the trials we exluded here to be able to check later

no_inference = inferred_df[(inferred_df.max_days == 0) | (inferred_df.latest_approval.isnull())].eudract_number.to_list()

# + trusted=true
#Now we add the latest approval to the longest trial duration

can_infer['inferred_completion'] = can_infer['latest_approval'] + can_infer.max_days.astype('timedelta64[D]')

#Now we conservatively add another year to the inferred completion date per our methods

can_infer['inferred_completion_adj'] = can_infer['inferred_completion'] + pd.offsets.DateOffset(months=12)

# + trusted=true
can_infer.head()
# -

# # Creating final dataset
#
# Now we need to bring everything together.

# + trusted=true
#Get each trial id only once
all_ids = dec_full.eudract_number.unique()

#turn that into a DataFrame
df = pd.DataFrame(all_ids)
df.columns = ['eudract_number']

# + trusted=true
#Merge in the dates we extracted earlier

df1 = df.merge(final_dates[['eudract_number', 'available_completion']], how='left', on='eudract_number')

df2 = df1.merge(can_infer[['eudract_number', 'inferred_completion_adj']], how='left', on='eudract_number')

df2.head()

# + trusted=true
#Conditions to create the inclusion/exclusion categorical variable

#Trials that were "not authorised" or "prohibited" in all countries
never_start = df2.eudract_number.isin(never_started_exclusions)

#Trials that didn't have an end date, and didn't have sufficient information to infer one
no_inf = df2.eudract_number.isin(no_inference)

#Trials that had some kind of completion date information
avail_comp = df2.available_completion.notnull()

#Trials where we had to infer an end date.
infer_comp = df2.inferred_completion_adj.notnull()

# + trusted=true
#Creating the inclusion/exclusion categorical variable

conds = [never_start, no_inf, avail_comp, infer_comp]

labels = ['No EU Start', 'Cannot Infer', 'Extracted', 'Inferred']

df2['exclusion_status'] = np.select(conds, labels)

# + trusted=true
df2.head()

# + trusted=true
#We can take a look at how frequently each category appears

df2.exclusion_status.value_counts()

# + trusted=true
#Taking the appropriate final date

df2['final_date'] = np.where(df2.available_completion.notnull(), 
                             df2.available_completion, df2.inferred_completion_adj)

#Making a binary variable for inclusion based on being completed for 24 months prior to data extraction

df2['date_inclusion'] = np.where(df2.final_date < pd.to_datetime('2018-12-01'), 1, 0)

#Making a binary variable for inferred end dates

df2['inferred'] = np.where(df2.exclusion_status == 'Inferred', 1, 0)

# + trusted=true
#Creating the final dataset with only included trials, the end date, and the inferred status

final_df = df2[df2.date_inclusion == 1][['eudract_number', 'final_date', 'inferred']].reset_index(drop=True)

print(f'There are {len(final_df)} trials in the final population we will sample from.')

# + trusted=true
final_df.inferred.value_counts()

# + trusted=true
inc_ids = final_df.eudract_number.to_list()

only_included = dec_full[dec_full.eudract_number.isin(inc_ids)].reset_index(drop=True)

print(len(only_included))

print(only_included.eudract_number.nunique())

# + trusted=true
#When we the sample was taken the following code was run to generate a random seed.

#from random import randint

#print(randint(1,10000))

#This produced 7872

# + trusted=true
sample = final_df.sample(500, random_state=7872)

# + trusted=true
sample.head()

# + trusted=true
#sample.to_csv(parent + '/data/samples/' + 'euctr_search_sample_final.csv')
# -

# # Replacing problematic trials in the dataset
#
# Per protocol, trials that are found to be withdrawn, meaning they never happened, at any time during the project, are to be replaced in the sample and re-searched. I will also replace trials that are clearly still ongoing based on other available information or are no longer available on the public EUCTR to be checked for some reason.
#
# To do this, we will take the sample population, exclude the trials from our original sample of 500, and then take a new sample of the remaining. At the final analysis, following all searches, there were 20 trials that need to be replaced and re-searched.

# + trusted=true
#Getting a new random seed for the new replacement sample

#print(randint(1,10000))

#This produced 6377

# + trusted=true
#Now lets remove the original 500 trial sample so we don't get any duplicates
replacement_pop = final_df[~(final_df.eudract_number.isin(sample.eudract_number.to_list()))]

# + trusted=true
#And take a sample
replacement_sample = replacement_pop.sample(20, random_state=6377)

# + trusted=true
#replacement_sample.to_csv(parent + '/data/samples/' + 'replacement_sample.csv')

# + trusted=true
replacement_sample.head(20)
# -

# # Data for Regression
#
# For the regression dataset we need the following categories: </br>
# Inclusion Category: Taken from above but already in the analysis notebook </br>
# Trial start year: Manually extracted dataset </br>
# Sponsor type: Derived below </br>
# EU country protocols registered: Derived below </br>
# Final Enrollment: Manually extracted dataset </br>
# EU only/Multinational: Manually extracted dataset </br>

# + trusted=true
#First lets load in our sponsor info scrape from Dec 2020
spon_df = pd.read_csv(parent + '/data/source_data/' + 'dec2020_spon_info.csv')

# + trusted=true
#We can limit everything to only the trials considered for our sample
incl_trials = sample.eudract_number.to_list() + replacement_sample.eudract_number.to_list()
spon_df_filt = spon_df[spon_df.trial_id.isin(incl_trials)].reset_index(drop=True).drop('Unnamed: 0', axis=1)

#We don't want to count non-EU/EEA protocols for that variable
spon_df_filt_no3rd = spon_df_filt[spon_df_filt.protocol_country != 'Outside EU/EEA'].reset_index(drop=True)

#We can get the count of unique EU country protocols
prot_counts = spon_df_filt_no3rd[['trial_id', 'protocol_country']].drop_duplicates().groupby('trial_id').count()

# + trusted=true
#Lets cross check trials with "No Data Available"
spon_df_filt[spon_df_filt.sponsor_status == 'No Data Available']

# + trusted=true
#We can manually check variation in the "sponsor_status" column to see which has mixed information
spon_df_filt[['trial_id', 'sponsor_status']].groupby('trial_id').nunique().sort_values(by='sponsor_status', ascending=False).head()

# + trusted=true
#Use this cell to check all these
spon_df_filt[spon_df_filt.trial_id == '2006-000666-37']
# -

# Manual Sponsor Status Check: <br />
# 2007-004805-80: One blank, one commercial. Make commercial. <br />
# 2006-000666-37: Commercial in Germany but non-commercial in GB. On manual check sponsor IATEC B.V. is/was a commercial entity (a CRO).  <br />
# 2012-000347-28: One blank, rest commercial. Make commercial.  <br />
# 2012-001956-20: Commercial all locations except Hungary, however clearly a Commercial entity. <br />
# 2011-000291-34: Truly just a blank sponsor name so unknown <br />
# 2007-003461-41: Deutsches Herzzentrum Berlin is a non-commercial sponsor <br />

# + trusted=true
#Doing the Groupby
spon_status = spon_df_filt[['trial_id', 'sponsor_status']].groupby('trial_id').max()

print(spon_status.sponsor_status.value_counts())

# + trusted=true
#Fixing the manually checked data.

spon_status.loc['2007-004805-80', 'sponsor_status'] = 'Commercial'
spon_status.loc['2006-000666-37', 'sponsor_status'] = 'Commercial'
spon_status.loc['2012-000347-28', 'sponsor_status'] = 'Commercial'
spon_status.loc['2012-001956-20', 'sponsor_status'] = 'Commercial'
spon_status.loc['2011-000291-34', 'sponsor_status'] = 'Unknown'
spon_status.loc['2007-003461-41', 'sponsor_status'] = 'Non-Commercial'

# + trusted=true
print(spon_status.sponsor_status.value_counts())

# + trusted=true
reg_df = spon_status.join(prot_counts).fillna(0).reset_index()

# + trusted=true
#reg_df.to_csv(parent + '/data/additional_data/' + 'reg_spon_info.csv')
# -

# # Sponsor Country
#
# Each trial will be assigned a “sponsor country” based on the most frequent sponsor country assigned in the EUCTR country protocols. A protocol of a specific country need not contain a sponsor from that country. If no single country appears most frequently, the trial will be coded as having “multi-country” sponsorship. The percent of trials reported to the EUCTR, other registries, and the literature will be reported for each unique sponsor country in the sample.

# + trusted=true
grouped = spon_df_filt[['trial_id', 
                        'sponsor_country']].groupby('trial_id')['sponsor_country'].apply(pd.Series.mode).to_frame().reset_index()

multi_country = grouped[grouped.level_1 == 1].trial_id.to_list()

# + trusted=true
#Lets check for any that are tied with "No Data Available"
grouped[grouped.trial_id.isin(multi_country)]
#There is one we need to correct for later: 2007-004805-80 needs to be "United Kingdom"

# + trusted=true
to_join = grouped[~grouped.trial_id.isin(multi_country)]

final_df = reg_df.merge(to_join, on='trial_id', how='left').drop('level_1', axis=1)

# + trusted=true
#Correcting that data from earlier
final_df.loc[final_df[final_df.trial_id == '2007-004805-80'].index[0], 'sponsor_country'] = 'United Kingdom'

# + trusted=true
final_df['sponsor_country'] = final_df['sponsor_country'].fillna('Multi-country')

final_df = final_df.replace('France, Metropolitan', 'France')

# + trusted=true
final_df[final_df.sponsor_country == 'No Data Available']
# -

# Manual changes:<br />
# 2010-020521-40: Sponsor is "EPIFARMA S.R.L." which is clearly Italian<br />
# 2011-000291-34: Has no sponsor<br />
# 2013-001103-36: Sponsor is "Tayside Medical Sciences Centre on behalf of University of Dundee & NHS Tayside" which is a UK sponsor

# + trusted=true
final_df.loc[final_df[final_df.trial_id == '2010-020521-40'].index[0], 'sponsor_country'] = 'Italy'
final_df.loc[final_df[final_df.trial_id == '2013-001103-36'].index[0], 'sponsor_country'] = 'United Kingdom'

# + trusted=true
final_df.head()

# + trusted=true
#final_df.to_csv(parent + '/data/additional_data/' + 'spon_country_data.csv')
# -












# +


