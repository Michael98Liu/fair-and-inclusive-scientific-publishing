import pandas as pd
import numpy as np
from tqdm.notebook import tqdm
from scipy.stats import ttest_ind

def loadText(file):
    text = ''
    
    with open(file, 'r') as f:
        for line in f:
            text += line
    return text


def priorCount(df):
    # given a dataframe containing the (citation or publication) count of each scientist in each year
    # calculate the total count up until each year
    prior = {}
    
    for year in tqdm(range(df.Year.min(), df.Year.max()+1)):
        
        sub = df[df.Year <= year].groupby('NewAuthorId').Count.sum().reset_index()
        prior[year] = sub
        
    return prior

def getCount(df, col, count_dict, count_col=None):
    # df: dataframe that contains scientists and years to be calculated
    # col: name of column that contains years
    # count_dict: a dictionary of prior values
    # count_col: name of value column
    
    if count_col is None:
        count_col = col+'_count'
    
    merged = []
    for year in range(1900,2019):
        subset = df[df[col] == year]
        if subset.shape[0] == 0:
            continue
        if year in count_dict.keys():
            # in the actual code we use, also need to match on 'issn'
            # but since in the test data, only one journal is considered
            # we use this simplified version
            subset = subset.merge(count_dict[year], on=['NewAuthorId'], how='left')
            subset = subset.fillna(0)
        else:
            subset = subset.assign(Count=0)
        
        merged.append(subset)
        
    merged = pd.concat(merged,sort=False,ignore_index=True)
    merged = merged.rename(columns={'Count':count_col})
    
    return merged

def bootstrapTTest(df, outcome, indep, v1, v2, ite=1000):
    # outcome: name of the column of dependent variables
    # indep: name of the column of independent variables
    # v1, v2: the two values of independed variable
    
    ### standardize outcome ###
    df[outcome] = (df[outcome] - df[outcome].mean())/df[outcome].std()
    ### standardize outcome ###
    
    betas = []
    
    df1 = df[df[indep] == v1]
    df2 = df[df[indep] == v2]
    
    ttest = ttest_ind(df2[outcome], df1[outcome], permutations=ite)
    pval = ttest.pvalue
    pval = f'$P$ = {round(pval, 3)}' if pval >= 0.001 else '$P < 0.001$'
    
    for i in range(ite):
        
        s_df1 = df1.sample(replace=True, frac=1)
        s_df2 = df2.sample(replace=True, frac=1)
        
        a = s_df1[outcome]
        b = s_df2[outcome]
                       
        betas.append(np.mean(b)-np.mean(a))
        
    b = np.mean(betas)
    lo = round(np.percentile(np.array(betas), q=2.5), 2)
    hi = round(np.percentile(np.array(betas), q=97.5), 2)
    
    print("$t_{" + f"{df1.shape[0]+df2.shape[0]-2}" +"}$" + f" = {round(ttest.statistic, 2)},", end=' ')
    print(f"{pval},", end=' ')
    print(f"$\\beta$ = {round(b, 2)},", end=' ')
    print(f"95\% CI = {lo} -- {hi}")    