import os
import glob

import pandas as pd
import numpy as np
from tqdm.notebook import tqdm

import helper

class Matcher:
    def __init__(self, L, prior_dir=None, count_dir=None, matched=None):
        self.prior_dir = prior_dir
        self.count_dir = count_dir

        self.L = L
        self.info = self.L.LOG
        self.debug = self.L.debug

        self.fields = list(self.L.parent_of_fields.Parent.unique())
        assert(len(self.fields) == 19)

        if matched is None:
            self.load_matched()
        else:
            self.matched = matched.copy()
            self.log_stats('')

    def log_stats(self, msg):
        self.info.log(f'{self.matched.shape} {self.matched.EditorsNewId.nunique()} {self.matched[["EditorsNewId","issn"]].drop_duplicates().shape} {msg}')

    def load_matched(self):
        self.all_matched = []
        for field in tqdm(self.fields):

            try:
                matched_count, matched_prior = pd.DataFrame(), pd.DataFrame()

                if self.count_dir:
                    matched_count = pd.read_csv(self.count_dir+f'{field}.csv',memory_map=True,sep='\t',
                                         usecols=['EditorsNewId','issn','AuthorsNewId','Ecount','Acount',
                                                           'EditorYear0','Eyfp','Eylp','Ayfp','Aylp','AuthorYear0'],
                                        dtype={'EditorsNewId':int,'issn':str,'AuthorsNewId':int,'Ecount':float,'Acount':float,
                                               'EditorYear0':int,'Eyfp':int,'Eylp':int,'Ayfp':int,'Aylp':int,'AuthorYear0':int})
                if self.prior_dir:
                    matched_prior = pd.read_csv(self.prior_dir+f'{field}.csv',memory_map=True,sep='\t',
                                         usecols=['EditorsNewId','issn','AuthorsNewId','Eprior','Aprior',
                                                           'EditorYear0','Eyfp','Eylp','Ayfp','Aylp','AuthorYear0'],
                                        dtype={'EditorsNewId':int,'issn':str,'AuthorsNewId':int,'Eprior':float,'Aprior':float,
                                               'EditorYear0':int,'Eyfp':int,'Eylp':int,'Ayfp':int,'Aylp':int,'AuthorYear0':int})
                if self.count_dir and self.prior_dir:
                    if matched_count.shape[0] == 0 or matched_prior.shape[0] == 0: continue

                    matched = matched_count.merge(matched_prior, on=['EditorsNewId','AuthorsNewId','issn','AuthorYear0'])
                else:
                    if self.count_dir: matched = matched_count
                    if self.prior_dir: matched = matched_prior

                self.all_matched.append(matched)

            except Exception as e:
                self.info.log(str(e))

        self.matched = pd.concat(self.all_matched, ignore_index=True, sort=False)
        self.log_stats('')

    def __map_rank(self, tiers):
        rank_mapping = []
        t = 0
        for i in range(1001):
            if i > tiers[t]:
                t+= 1
            rank_mapping.append({'Rank':i,'Tier':tiers[t]})
        rank_mapping.append({'Rank':1001,'Tier':1001})
        rank_mapping = pd.DataFrame(rank_mapping)

        return rank_mapping

    def filter_count(self, prior_threshold=0.5, count_threshold=0.5):
        if self.prior_dir:
            matched = self.matched.assign(Ec=self.matched.apply(lambda row: row['Eprior']+1 if row['Eprior']==0 else row['Eprior'], axis=1))
            matched = matched.assign(Ac = matched.apply(lambda row: row['Aprior']+1 if row['Eprior']==0 else row['Aprior'], axis=1))
            # filter
            matched['diff'] = matched.apply(lambda row:abs(row['Ec']-row['Ac'])/row['Ec'], axis=1)
            filtered = matched[(matched['diff'] <= prior_threshold)]
            self.matched = filtered.drop(['diff','Ac','Ec'], axis=1)
            self.log_stats('prior')
        if self.count_dir:
            matched = self.matched.assign(Ec=self.matched.apply(lambda row: row['Ecount']+1 if row['Ecount']==0 else row['Ecount'], axis=1))
            matched = matched.assign(Ac = matched.apply(lambda row: row['Acount']+1 if row['Ecount']==0 else row['Acount'], axis=1))
            # filter
            matched['diff'] = matched.apply(lambda row:abs(row['Ec']-row['Ac'])/row['Ec'], axis=1)
            filtered = matched[(matched['diff'] <= count_threshold) | (abs(matched['Ec']-matched['Ac']) == 1)]
            self.matched = filtered.drop(['diff','Ac','Ec'], axis=1)
            self.log_stats('count')

    def filter_gender(self):
        self.matched = self.matched.merge(self.L.author_gender.rename(
            columns={'NewAuthorId':'EditorsNewId','gender':'Egender'}), on='EditorsNewId')
        self.log_stats('')
        self.matched = self.matched.merge(self.L.author_gender.rename(
            columns={'NewAuthorId':'AuthorsNewId','gender':'Agender'}), on='AuthorsNewId')
        self.log_stats('')
        self.matched = self.matched[self.matched.Egender == self.matched.Agender]
        self.matched = self.matched.drop(['Egender','Agender'],axis=1)
        self.log_stats('gender')
        self.matched = self.matched.drop_duplicates()
        self.log_stats('drop dup')

    def filter_race(self):
        self.matched = self.matched.merge(self.L.author_race.rename(
            columns={'NewAuthorId':'EditorsNewId','Race':'Erace'}), on='EditorsNewId')
        self.log_stats('')
        self.matched = self.matched.merge(self.L.author_race.rename(
            columns={'NewAuthorId':'AuthorsNewId','Race':'Arace'}), on='AuthorsNewId')
        self.log_stats('')

        self.matched = self.matched[self.matched.Erace == self.matched.Arace]
        self.matched = self.matched.drop(['Erace','Arace'],axis=1)
        self.log_stats('race')
        self.matched = self.matched.drop_duplicates()
        self.log_stats('drop dup (same as before)')

    def sample(self, n_seed=50):
        
        all_sampled = []

        for seed in tqdm(range(n_seed)):
            np.random.seed(seed)

            sampled = self.matched.groupby(['EditorsNewId','issn']).apply(
                lambda x: x.filter([np.random.choice(x.index, replace=True)], axis=0)).reset_index(drop=True)

            sampled = sampled.assign(seed=seed)
            all_sampled.append(sampled)

        all_sampled = pd.concat(all_sampled, ignore_index=True, sort=False)
        self.matched = all_sampled
        self.log_stats('combined all sampled')

        self.groups = self.matched[['EditorsNewId','issn','AuthorsNewId','seed']].drop_duplicates()
