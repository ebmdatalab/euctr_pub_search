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
from sklearn.metrics import cohen_kappa_score

# + trusted=true
import sys
from pathlib import Path
import os
cwd = os.getcwd()
parent = str(Path(cwd).parents[0])
sys.path.append(parent)


# + trusted=true
def reco_checker(df, field1, field2):
    return df[((df[field1] == 1) & (df[field2] == 0)) | ((df[field1] == 0) & (df[field2] == 1))]


# + trusted=true
reco_data = pd.read_csv(parent + '/data/dual_coding/' + 'dual_coding.csv')
study_data = pd.read_csv(parent + '/data/final_dataset/' + 'analysis_df.csv')

# + trusted=true
#These were all the trials that were assigned for dual coding and were excluded. Uncomment to view.
#We will exclude these from the rest of the analysis

#reco_data[reco_data.euctr_res_nd.isna()]

# + trusted=true
#Combining the reconcilliation data with the final data

df = reco_data[reco_data.euctr_res_nd.notnull()].merge(study_data[['euctr_id', 'euctr_results', 'nct_id', 'isrctn_id', 'journal_results_inc']], how='left', left_on='trial_id', right_on='euctr_id').reset_index(drop=True)

# + trusted=true
#The denominators here are out of 239 after exclusions. 
len(df)

# + trusted=true
df.columns

# + trusted=true
#Did we extract the same information about EUCTR results?

# + trusted=true
reco_checker(df, 'euctr_res_nd', 'euctr_res_2nd')

# + trusted=true
#Percent Agreement

1 - (len(reco_checker(df, 'euctr_res_nd', 'euctr_res_2nd'))/len(df))

# + trusted=true
#cohen's kappa

cohen_kappa_score(df.euctr_res_nd, df.euctr_res_2nd)

# + trusted=true
#Now did we find a ClinicalTrials.gov cross registration?

# + trusted=true
reco_checker(df, 'nct_nd', 'nct_2nd')[['trial_id', 'nct_nd', 'nct_2nd', 'nct_id']] 

# + trusted=true
1 - (len(reco_checker(df, 'nct_nd', 'nct_2nd'))/len(df))

# + trusted=true
cohen_kappa_score(df.nct_nd, df.nct_2nd)

# + trusted=true
#When we did both find a ClinicalTrials.gov registration, did we find the same one

# + trusted=true
df[(df.nct_nd == 1) & (df.nct_2nd == 1)].nct_match.value_counts()

# + trusted=true
158/160

# + trusted=true
#What about finding the same ISRCTN registration

# + trusted=true
reco_checker(df, 'isrctn_nd', 'isrctn_2nd')
# + trusted=true
1 - (len(reco_checker(df, 'isrctn_nd', 'isrctn_2nd'))/len(df))


# + trusted=true
cohen_kappa_score(df.isrctn_nd, df.isrctn_2nd)


# + trusted=true
#Now for publications

# + trusted=true
reco_checker(df, 'pub_nd', 'pub_2nd')

# + trusted=true
1 - (len(reco_checker(df, 'pub_nd', 'pub_2nd'))/len(df))

# + trusted=true
cohen_kappa_score(df.pub_nd, df.pub_2nd)

# + trusted=true
#Did we find the same publication?

# + trusted=true
df[(df.pub_nd == 1) & (df.pub_2nd == 1)].pub_match.value_counts()

# + trusted=true
98/110

# + trusted=true
#When we both found the same pub, did the extracted publication date match

# + trusted=true
df[(df.pub_match == 1)].pub_date_match.value_counts()

# + trusted=true
67/98

# + trusted=true
#When we both found the same pub, did the extracted trial ID match

# + trusted=true
df[(df.pub_match == 1)].pub_reg_match.value_counts()

# + trusted=true
86/(12+86)
# -



