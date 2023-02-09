import pandas as pd
import numpy as np
from math import sqrt
from statsmodels.stats.proportion import proportions_ztest

def status_exclude(x):
    d = {}
    d['number_of_countries'] = x.eudract_number_with_country.nunique()
    d['completed'] = np.where(x.end_of_trial_status == 'Completed', 1, 0).sum()
    d['ongoing'] =  np.where((x.end_of_trial_status == 'Ongoing') | (x.end_of_trial_status == 'Restarted'), 1, 0).sum()
    d['terminated'] = np.where(x.end_of_trial_status == 'Prematurely Ended', 1, 0).sum()
    d['suspended'] = np.where((x.end_of_trial_status == 'Temporarily Halted') | (x.end_of_trial_status == 'Suspended by CA'), 1, 0).sum()
    d['other_status'] = np.where((x.end_of_trial_status == 'Not Authorised') | (x.end_of_trial_status == 'Prohibited by CA'), 1, 0).sum()
    d['no_status'] = np.where(pd.isnull(x.end_of_trial_status),1,0).sum()
    d['results'] = np.where(x.trial_results.notnull(), 1, 0).sum()
    return pd.Series(d)

def group_dates(x):
    d = {}
    d['latest_completion_p'] = x.protocol_completion.max()
    d['latest_completion_r'] = x.results_completion.max()
    return pd.Series(d)


def date_fix(x):
    if x < pd.to_datetime('2004-01-01') or x > pd.to_datetime('2020-12-31'):
        return pd.NaT
    else:
        return x
    
def ci_calc(num, denom, z=1.96, printer=True):
    p = num/denom
    se_num = p * (1-p)
    se = sqrt(se_num/denom)
    p_m = z * se
    if printer:
        print(f'Proportion: {round(p * 100,2)}%')
        print(f'95% CI: {round((p - p_m) * 100,2)}-{round((p + p_m) * 100,2)}')
    return (p - p_m, p, p + p_m)

def z_test(count, nobs):
    stat, pval = proportions_ztest(count, nobs)
    return stat, pval

def summarizer(num, denom):
    print(f'Total: {denom}')
    print(f'Results found: {num}')
    ci_out = ci_calc(num, denom)
    return ci_out

def check_dupes(x):
    x1 = [value for value in list(x) if value is not pd.NaT]
    return len(tuple(x1)) != len(set(tuple(x1)))