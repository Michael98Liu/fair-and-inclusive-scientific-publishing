import pandas as pd
from tqdm.notebook import tqdm

def loadText(file):
    text = ''
    
    with open(file, 'r') as f:
        for line in f:
            text += line
    return text

def getBad(Aq, Bq, As, Bs, jpub_count):
    
    normal = jpub_count[jpub_count.apply(lambda row: row.AfAvg < max(row.BeAvg * Bq, Aq), axis=1)]
    Q = jpub_count[jpub_count.apply(lambda row: row.AfAvg >= max(row.BeAvg * Bq, Aq), axis=1)]
    S = jpub_count[jpub_count.apply(lambda row: row.AfAvg >= max(row.BeAvg * Bs, As), axis=1)]
    
    print(f'# Aq: {Aq}, Bq {Bq}, As: {As}, Bs: {Bs} | ',
          f'questionable: {round(Q.shape[0]/jpub_count.shape[0]*100, 2)}%,suspicious: {round(S.shape[0]/jpub_count.shape[0]*100, 2)}%')
    
    return normal, Q, S


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