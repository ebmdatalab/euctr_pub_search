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
#The denominators here are out of 241 after exclusions. 
len(df)

# + trusted=true
#Did we extract the same information about EUCTR results?

# + trusted=true
reco_checker(df, 'euctr_res_nd', 'euctr_res_2nd')

# + trusted=true
#Percent Agreement

1 - (len(reco_checker(df, 'euctr_res_nd', 'euctr_res_2nd'))/len(df))

# + trusted=true
#Now did we find a ClinicalTrials.gov cross registration?

# + trusted=true
reco_checker(df, 'nct_nd', 'nct_2nd')[['trial_id', 'nct_nd', 'nct_2nd', 'nct_id']] 

# + trusted=true
1 - (len(reco_checker(df, 'nct_nd', 'nct_2nd'))/len(df))

# + trusted=true
#When we did both find a ClinicalTrials.gov registration, did we find the same one

# + trusted=true
df[(df.nct_nd == 1) & (df.nct_2nd == 1)].nct_match.value_counts()

# + trusted=true
1 - (9/(158+2))

# +
#What about finding the same ISRCTN registration

# + trusted=true
reco_checker(df, 'isrctn_nd', 'isrctn_2nd')
# +



# + trusted=true

# -


# +

# -


df.to_csv(parent + '/data/dual_coding/' + 'df_temp.csv')









# + trusted=true
#First lets look at any where we didn't agree on EUCTR results.

df[((df.euctr_res_nd == 1) & (df.euctr_res_2nd == 0)) | ((df.euctr_res_nd == 0) & (df.euctr_res_2nd == 1))]

# + trusted=true
1/241

# + trusted=true
1 - (7/241)

# + trusted=true
#Then anywhere we didn't both find a matched CTGov reg

df[((df.nct_nd == 1) & (df.nct_2nd == 0)) | ((df.nct_nd == 0) & (df.nct_2nd == 1))]

# + trusted=true
#Now lets see whether we found the same NCT ID
#1 means we matched
#2 is N/A meaning there was nothing to match
#0 is we found different things that needed to be resolved

df.nct_match.value_counts()

# + trusted=true
1 - (9/(157+9))

# + trusted=true
#Then anywhere we didn't both find a matched isrctn reg

df[((df.isrctn_nd == 1) & (df.isrctn_2nd == 0)) | ((df.isrctn_nd == 0) & (df.isrctn_2nd == 1))]

# + trusted=true
#How many did either of us find a publication:

len(df[(df.pub_nd == 1) | (df.pub_2nd == 1)])

# + trusted=true
len(df[(df.pub_nd == 0) | (df.pub_2nd == 0)])

# + trusted=true
#Then we check publications

len(df[((df.pub_nd == 1) & (df.pub_2nd == 0)) | ((df.pub_nd == 0) & (df.pub_2nd == 1))])

# + trusted=true
1 - (37/250)

# + trusted=true
#Then did we match?

df.pub_match.value_counts()

# + trusted=true
98 / (98+49)

# + trusted=true
df.head(2)

# + trusted=true
#Did the publication date we extracted match?

df.pub_date_match.value_counts()

# + trusted=true
1 - (80/(80+67))

# + trusted=true
80+67

# + trusted=true
df[((df.pub_reg_nd == 1) & (df.pub_reg_2nd == 0)) | ((df.pub_reg_nd == 0) & (df.pub_reg_2nd == 1))]

# + trusted=true
df.pub_reg_match.value_counts()

# + trusted=true
93+16

# + trusted=true
16 / (93+16)
# +


