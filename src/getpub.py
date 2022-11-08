import os
import pandas as pd
import numpy as np
from tqdm import tqdm_notebook as tqdm
from matplotlib import pyplot as plt
import seaborn as sns

import helper
import matcher

class GetPub:
    def __init__(self, L, M, outcome):
        self.L = L
        self.M = M
        self.LOG = self.L.LOG
        self.debug = self.L.debug
        self.dir = '/scratch/fl1092/capstone/matching/'+outcome+'/'

        if not os.path.exists(self.dir):
            os.makedirs(self.dir)
            print(self.dir, "created")
        else:
            print(self.dir, "exists")

        self.matched = None
        self.comparables = None
        self.matched_span = None
        self.full_range = None

        self.papers = None
        self.citations = None
        self.cites = None

        # if first time being executed, save the "group" file
        if self.M.groups is not None:
            self.M.groups.to_csv(self.dir+"sampled_groupes.csv",sep='\t',index=False)
            self.groups = self.M.groups
        else:
            self.groups = pd.read_csv(self.dir+"sampled_groupes.csv", sep='\t',
            dtype={'EditorsNewId':int,'issn':str,'AuthorsNewId':int,'seed':int})
        self.groups = self.groups.rename(columns={'AuthorsNewId':'NewAuthorId'})

    def getFullRange(self, df, start, end, year0):
        full_range_list = []
        min_year = df[start].min()

        for year in tqdm(range(min_year, 2019)): # maximum 2018
            subset = df[ (df[start] <= year) & (df[end] >= year) ]
            subset = subset.assign(Year = year)
            subset = subset.assign(EditorYear = subset.Year-subset[year0])
            subset = subset.drop([start, end, year0], axis=1)

            full_range_list.append(subset)
        full_range = pd.concat(full_range_list, ignore_index=True, sort=False)

        return full_range

    def getBothFullRange(self):
        # AuthorsNewId	EditorsNewId	issn	AuthorYear0	Ecount	Acount	Ayfp	Aylp	EditorYear0	Eyfp	Eylp	Eprior	Aprior	seed
        authors = self.matched[['AuthorsNewId','EditorsNewId','issn','AuthorYear0','Ayfp','Aylp']].drop_duplicates()
        editors = self.matched[['EditorsNewId','issn','EditorYear0','Eyfp','Eylp']].drop_duplicates()

        aut_range = self.getFullRange(authors, 'Ayfp', 'Aylp', 'AuthorYear0')
        edi_range = self.getFullRange(editors, 'Eyfp', 'Eylp', 'EditorYear0')

        edi_range = edi_range.assign(NewAuthorId = edi_range.EditorsNewId)
        aut_range = aut_range.rename(columns={'AuthorsNewId':'NewAuthorId'})
        assert(aut_range.shape[1] == edi_range.shape[1])
        print(f"Editor and author range: {edi_range.shape} {aut_range.shape}")

        self.full_range = pd.concat([edi_range, aut_range], ignore_index=True, sort=False)

    def getSeedBadness(self, window = None):
        # find the intersection of EditorYears that an editor has a comparable author
        # find the seed for each comparison group
        # for each editor whehter normal or sus or ques
        edi_range = self.full_range[ self.full_range.NewAuthorId == self.full_range.EditorsNewId ]
        aut_range = self.full_range[ self.full_range.NewAuthorId != self.full_range.EditorsNewId ]
        print(f"Editor and author range: {edi_range.shape} {aut_range.shape} (same as before)")

        edi_range = edi_range.rename(columns={'Count':'EdiCount'}).drop('NewAuthorId',axis=1)
        aut_range = aut_range.rename(columns={'Count':'AutCount'})

        full_range = self.groups.merge(
            edi_range, on=['EditorsNewId','issn']).merge(
            aut_range, on=['EditorsNewId','NewAuthorId','issn','EditorYear'])

        self.n_count = full_range.merge(self.normal, on=['EditorsNewId','issn'])
        self.q_count = full_range.merge(self.q, on=['EditorsNewId','issn'])
        self.s_count = full_range.merge(self.bad_apples, on=['EditorsNewId','issn'])
        
        self.n_count.to_csv(self.dir+f'NormalCount_{window}.csv', sep='\t', index=False)
        self.q_count.to_csv(self.dir+f'QuestionableCount_{window}.csv', sep='\t', index=False)
        self.s_count.to_csv(self.dir+f'SuspiciousCount_{window}.csv', sep='\t', index=False)

    def getBadPetter(self, filename, Aq=2/3, Bq=2, As=2, Bs=2):
        jpub_count = pd.read_csv(filename, sep='\t',
                        usecols=['NewAuthorId','issn','BeAvg','AfAvg'],
                        dtype={'NewAuthorId':int,'issn':str,'BeAvg':float,'AfAvg':float})
        print(jpub_count.shape)

        normal = jpub_count[jpub_count.apply(lambda row: row.AfAvg < max(row.BeAvg * Bq, Aq), axis=1)]
        Q = jpub_count[jpub_count.apply(lambda row: row.AfAvg >= max(row.BeAvg * Bq, Aq), axis=1)]
        S = jpub_count[jpub_count.apply(lambda row: row.AfAvg >= max(row.BeAvg * Bs, As), axis=1)]

        self.normal = normal[['NewAuthorId','issn']].drop_duplicates().rename(columns={'NewAuthorId':'EditorsNewId'})
        self.bad_apples = S[['NewAuthorId','issn']].drop_duplicates().rename(columns={'NewAuthorId':'EditorsNewId'})
        self.q = Q[['NewAuthorId','issn']].drop_duplicates().rename(columns={'NewAuthorId':'EditorsNewId'})
        
        self.all_editors = jpub_count[['NewAuthorId','issn']].drop_duplicates()

        print(f'# Population: {self.all_editors.shape[0]} Aq: {Aq}, Bq {Bq}, As: {As}, Bs: {Bs} | ',
              f'questionable: {round(Q.shape[0]/jpub_count.shape[0]*100, 2)}',
              f'suspicious: {round(S.shape[0]/jpub_count.shape[0]*100, 2)}%')
        
    def getBadAlt(Aq=1, Bq=2, As=2, Bs=3):
        
        jpub_count = pd.read_csv('/scratch/fl1092/capstone/temp/EditorJournalCountOthersAvgAlt.csv', sep='\t',
                       usecols=['NewAuthorId','issn','SelfAvg','OtherAverage'],
                       dtype={'NewAuthorId':int,'issn':str,'SelfAvg':float,'OtherAverage':float})
        print(jpub_count.shape)
    
        normal = jpub_count[jpub_count.apply(lambda row: row.SelfAvg < max(row.OtherAverage * Bq, Aq), axis=1)]
        Q = jpub_count[jpub_count.apply(lambda row: row.SelfAvg >= max(row.OtherAverage * Bq, Aq), axis=1)]
        S = jpub_count[jpub_count.apply(lambda row: row.SelfAvg >= max(row.OtherAverage * Bs, As), axis=1)]

        print(f'# Aq: {Aq}, Bq {Bq}, As: {As}, Bs: {Bs} | ',
              f'questionable: {round(Q.shape[0]/jpub_count.shape[0]*100, 2)}%,suspicious: {round(S.shape[0]/jpub_count.shape[0]*100, 2)}%')

        return normal, Q, S

    def get_lines(self, category, agg=False): # editor year range
        # params: agg -> whether to aggregate all author counts for one editor

        if self.full_range is None:
            self.load_full_range()

        full_range = self.full_range.copy()

        if category == 'citation':
            full_range = full_range.merge(self.L.citation_year, on=['NewAuthorId','Year'], how='left')
        elif category == 'citation_cum':
            merged = []
            for year in tqdm(range(full_range.Year.min(), full_range.Year.max() + 1)):
                subset = full_range[full_range.Year == year]
                subset = subset.merge(self.L.prior_impact[year], how='left')
                subset = subset.rename(columns={'Prior':'Count'})
                merged.append(subset)
            full_range = pd.concat(merged, ignore_index=True, sort=False)
        elif category == 'paper':
            full_range = full_range.merge(self.L.paper_count, on=['NewAuthorId','Year'], how='left')
        elif category == 'self_citation':
            full_range = full_range.merge(self.L.self_citation, on=['NewAuthorId','Year'], how='left')
        elif category == 'journal_citation':
            full_range = full_range.merge(self.L.journal_citation, on=['NewAuthorId','Year','issn'], how='left')
        elif category == 'journal_paper':
            full_range = full_range.merge(self.L.journal_paper, on=['NewAuthorId','Year','issn'], how='left')
        elif category == 'network_size':
            full_range = full_range.merge(self.L.network_size, on=['NewAuthorId','Year'],how='left')
        elif category == 'selfcite_rate':
            full_range = full_range.merge(self.L.selfcite_rate, on=['NewAuthorId','Year'], how='left')
        elif category == 'journal_paper_cum':
            merged = []
            for year in tqdm(range(max(1900, full_range.Year.min()), full_range.Year.max() + 1)):
                subset = full_range[full_range.Year == year]
                subset = subset.merge(self.L.prior_journal_paper[year], on=['NewAuthorId','issn'], how='left')
                subset = subset.rename(columns={'Prior':'Count'})
                merged.append(subset)
            full_range = pd.concat(merged, ignore_index=True, sort=False)
        else:
            self.LOG.log(f'{category} error.')
            return None
        full_range = full_range.fillna(0)

        self.full_range = full_range

    def load_lines(self, window=5):
        
        cols = ['EditorsNewId', 'issn', 'NewAuthorId', 'EditorYear', 'EdiCount', 'AutCount', 'seed', 'Year_y', 'Year_x']
        # year_x is the year for editors
        types = {x: (int if x!='issn' else str) for x in cols}

        self.n_count = pd.read_csv(self.dir+f'NormalCount_{window}.csv', sep='\t', usecols=cols, dtype=types)
        self.q_count = pd.read_csv(self.dir+f'QuestionableCount_{window}.csv', sep='\t', usecols=cols, dtype=types)
        self.s_count = pd.read_csv(self.dir+f'SuspiciousCount_{window}.csv', sep='\t', usecols=cols, dtype=types)
