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
import schemdraw
from schemdraw import flow
import matplotlib.pyplot as plt
from upsetplot import from_indicators, plot
import pandas as pd
import numpy as np
from matplotlib.patches import Patch
from lifelines import KaplanMeierFitter
from lifelines.plotting import add_at_risk_counts
from lifelines.utils import median_survival_times

# + trusted=true
import sys
from pathlib import Path
import os
cwd = os.getcwd()
parent = str(Path(cwd).parents[0])
sys.path.append(parent)
# -

# # Flow Chart for Sample

# Flowchart describing the processs to get from raw data to our sample for analysis. Numbers are from a dictionary called `flowchart_dict` in the `Data Processing and Handling` notebook and the 'Analysis Prep' of the `Analysis` notebook.

# + trusted=true
with schemdraw.Drawing() as d:
    d += flow.Box(w=10, h=1.5).label('Registered Trials on the EUCTR\n(N=38,566)')
    d += flow.Arrow('down', l=4).at((5,-.75))
    d += flow.Arrow('right').at((5,-2.75))
    d += flow.Box(w=6, h=2).label('Not Authorised \n(n=20)\nMissing Date Info\n(n=729)')
    d += flow.Box(w=5, h=1).label('n=37,817').at((2.5,-5.2))
    d += flow.Line('down', l=1).at((5, -5.7))
    d += flow.Arrow(l=3).theta(-45).at((5,-6.7))
    d += flow.Box(w=6, h=2).label('Inferred Completion Date\n(n=16,051)').at((5.8,-8.8))
    d += flow.Arrow(l=3).theta(225).at((5,-6.7))
    d += flow.Box(w=6, h=2).label('Extracted Completion Date\n(n=21,766)').at((4.2,-8.8))
    d += flow.Line('down', l=2).at((1.3, -10.8))
    d += flow.Arrow('left', l=1)
    d += flow.Box(w=5.5, h=1.5).label('Completed <24 Months\n(n=2,584)')
    d += flow.Line('down', l=2).at((9, -10.8))
    d += flow.Arrow('right', l=1)
    d += flow.Box(w=5.5, h=1.5).label('Completed <24 Months\n(n=7,992)')
    
    d += flow.Arrow('left', l=1).at((1.3, -16))
    d += flow.Box(w=5.5, h=3).label('Not Sampled\n(n=18,813)\n\nReplaced\n(n=15)')
    
    d += flow.Arrow('right', l=1).at((9, -16))
    d += flow.Box(w=5.5, h=3).label('Not Sampled\n(n=7,906)\n\nReplaced\n(n=7)')
    
    d += flow.Arrow('down', l=6).at((9, -12.8))
    d += flow.Box(w=4.5, h=1.5).label('Inferred Included\n(n=146)')
    d += flow.Arrow('down', l=6).at((1.3, -12.8))
    d += flow.Box(w=4.5, h=1.5).label('Extracted Included\n(n=354)')
    
    #Final
    d += flow.Arrow(l=3).theta(-45).at((1.3,-20.3))
    d += flow.Arrow(l=3).theta(225).at((9,-20.3))
    d += flow.Box(w=5, h=1.5).label('Final Sample\n(n=500)').at((7.7,-22.5))

#d.save(parent + '/data/Figures/flowchart.jpg')
# -
# # Upset Plot for Results

# + trusted=true
upset_df = pd.read_csv(parent + '/data/graphing_data/upset_data.csv').drop('Unnamed: 0', axis=1)
upset_df.columns = ['EUCTR', 'ClinicalTrials.gov', 'ISRCTN', 'Journal Publication']

upset_df = upset_df.replace(1,True)
upset_df = upset_df.replace(0,False)

# + trusted=true
fig = plt.figure(figsize=(12, 7), dpi=300)
plot(from_indicators(["EUCTR", "ClinicalTrials.gov", "ISRCTN", "Journal Publication"],
                      data=upset_df), 
     sort_by='degree', 
     show_counts=True, 
     fig=fig, 
     element_size=None, 
     totals_plot_elements=3,
     include_empty_subsets=True
    )

plt.show()

#fig.savefig(parent + '/data/Figures/upset_chart.jpg')
# -

# # Upset Plot for Registrations

# + trusted=true
upset_reg_df = pd.read_csv(parent + '/data/graphing_data/upset_reg_data.csv').drop('Unnamed: 0', axis=1)

# + trusted=true
upset_reg_df['EUCTR Registration'] = True
upset_reg_df['ClinicalTrials.gov Registration'] = np.where(upset_reg_df['nct_id'].notnull(), True, False)
upset_reg_df['ISRCTN Registration'] = np.where(upset_reg_df['isrctn_id'].notnull(), True, False)

# + trusted=true
fig = plt.figure(figsize=(12, 7), dpi=300)
plot(from_indicators(['EUCTR Registration', 'ClinicalTrials.gov Registration', 'ISRCTN Registration'],
                      data=upset_reg_df), 
     sort_by='degree', 
     show_counts=True, 
     fig=fig, 
     element_size=None, 
     totals_plot_elements=3
    )

plt.show()

#fig.savefig(parent + '/data/Figures/upset_chart_reg.jpg')

# + [markdown] tags=[]
# # Start Year Graphs

# + trusted=true
graphing_df = pd.read_csv(parent + '/data/graphing_data/start_year_data.csv')

data = graphing_df[graphing_df.any_results_inc == 0][['Trial Start Year']]

# + trusted=true
fig = plt.figure(figsize=(10, 6), dpi=200)

bins = list(range(int(data.min()[0]),int(data.max()[0]+2)))

#Graph 1
ax1 = plt.subplot(211)

data1 = graphing_df[graphing_df.any_results_inc == 0][['Trial Start Year']]
bins1 = list(range(int(data.min()[0]),int(data.max()[0]+2)))

ax1.hist(graphing_df['Trial Start Year'], bins1, align='left', histtype='stepfilled', color='#ff7f0e', alpha=.3)

ax1.hist(data1, bins1, align='left', color='#1f77b4', rwidth=.98)

ax1.set_axisbelow(True)
ax1.grid(axis='y')
ax1.set_xticks(bins)
ax1.set_yticks(range(0,61,10))
plt.title('a. Distribution of Fully Unreported Trials by Start Year')

#Graph 2
ax2 = plt.subplot(212)

#Making first bin anything from 2004 or earlier because 1 trial is from 1999
data2 = np.clip(graphing_df[graphing_df.euctr_results_inc == 0][['Trial Start Year']], 2004, 2020)
bins2 = list(range(2004,2020))

names = []
for b in bins:
    if b == 2004:
        names.append('≤2004')
    else:
        names.append(str(b))

ax2.hist(graphing_df['Trial Start Year'], bins1, align='left', histtype='stepfilled', color='#ff7f0e', alpha=.3)
        
ax2.hist(data2, bins2, align='left', color='#1f77b4', rwidth=.98)

ax2.set_axisbelow(True)
ax2.grid(axis='y')
ax2.set_xticks(bins)
ax2.set_xticklabels(names)
ax2.set_yticks(range(0,61,10))
plt.title('b. Distribution of Unreported EUCTR Results by Start Year')

legend_elements = [Patch(facecolor='#1f77b4',label='Unreported Trials'), 
                   Patch(facecolor='#ff7f0e',label='Full Sample', alpha=.3)]

fig.legend(handles=legend_elements, loc=1, bbox_to_anchor=(.985,.95))

plt.tight_layout()
plt.subplots_adjust(hspace=.3)
plt.show()

fig.savefig(parent + '/data/Figures/start_year_results.jpg')
# -
# # Time to Searches Graph

# + trusted=true
to_pub = pd.read_csv(parent + '/data/graphing_data/days_to_search.csv')

# + trusted=true
fig = plt.figure(figsize=(10, 6), dpi=300)

group = 'inferred'
column = 'days_to_search'
grouped = to_pub.groupby(group)

names, vals, xs = [], [] ,[]

for i, (name, subdf) in enumerate(grouped):
    names.append(name)
    vals.append(subdf[column].tolist())
    xs.append(np.random.normal(i+1, 0.04, subdf.shape[0]))

plt.boxplot(vals, labels=['Extracted', 'Inferred'])
ngroup = len(vals)

for x, val in zip(xs, vals):
    plt.scatter(x, val, alpha=0.4)

plt.ylabel('Days From Completion to Search',labelpad=10)

plt.show()

# + trusted=true
#fig.savefig(parent + '/data/Figures/time_to_search.jpg')
# -
# # KM for time to pub

# + trusted=true
km_pub = pd.read_csv(parent + '/data/graphing_data/time_to_pub.csv')

# + trusted=true
km_pub.columns

# + trusted=true
time_to_euctr = km_pub[['euctr_results_inc', 'euctr_days', 'inferred']]
time_to_ctg = km_pub[km_pub.nct_id.notnull()][['ctgov_results_inc', 'ctg_days', 'inferred']]
time_to_pub = km_pub[['journal_results_inc', 'pub_days', 'inferred']]

# + trusted=true
fig = plt.figure(dpi=300)
ax = plt.subplot()
yticks = list(np.arange(0,1.1,.1))

euctr = KaplanMeierFitter()
euctr.fit(time_to_euctr[time_to_euctr.inferred == 0].euctr_days, time_to_euctr[time_to_euctr.inferred == 0].euctr_results_inc, label='EUCTR')
ax = euctr.plot_cumulative_density(ci_show=False, figsize=(15,10), grid=True, ax=ax, show_censors=True, yticks=yticks)

ctg = KaplanMeierFitter()
ctg.fit(time_to_ctg[time_to_ctg.inferred == 0].ctg_days, time_to_ctg[time_to_ctg.inferred == 0].ctgov_results_inc,  label='ClinicalTrials.gov')
ax = ctg.plot_cumulative_density(ci_show=False, figsize=(15,10), grid=True, ax=ax, show_censors=True, yticks=yticks)

pub = KaplanMeierFitter()
pub.fit(time_to_pub[time_to_pub.inferred == 0].pub_days, time_to_pub[time_to_pub.inferred == 0].journal_results_inc,  label='Journal Article')
ax = pub.plot_cumulative_density(ci_show=False, figsize=(15,10), grid=True, ax=ax, show_censors=True, yticks=yticks)

add_at_risk_counts(euctr, ctg, pub, rows_to_show = ['At risk'], ax=ax)
plt.tight_layout()

fig.savefig(parent + '/data/Figures/time_to_results.jpg')
# + trusted=true
print(euctr.median_survival_time_)
median_survival_times(euctr.confidence_interval_)

# + trusted=true
print(ctg.median_survival_time_)
median_survival_times(ctg.confidence_interval_)


# + trusted=true
print(pub.median_survival_time_)
median_survival_times(pub.confidence_interval_)
# -





# +

# -




