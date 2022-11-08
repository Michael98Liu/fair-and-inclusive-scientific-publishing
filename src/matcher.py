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
            
        self.matched = (
            self.matched.drop(['Ayfp_x','Aylp_x','Eyfp_x','Eylp_x','EditorYear0_x'], axis=1)
            .rename(
                columns={'Eylp_y':'Eylp','Aylp_y':'Aylp','Eyfp_y':'Eyfp','Ayfp_y':'Ayfp','EditorYear0_y':'EditorYear0'}
            ).drop_duplicates(subset=['AuthorsNewId','EditorsNewId','issn'])
        )
        
        self.log_stats('Dropped duplicates')
    
    def filter_journal_editor(self):
        
        editors = pd.read_csv("/scratch/fl1092/capstone/elsevier/editors.csv", sep='\t',
                     usecols=["NewAuthorId", "issn"],
                     dtype={"NewAuthorId":int, "issn":str, "start_year":int, "end_year":int})
        
        # filter 
        self.matched = (
            self.matched.merge(
                editors.rename(columns={'NewAuthorId':'AuthorsNewId'}).assign(isEdi=1),
                on=['AuthorsNewId','issn'], how='left').fillna(0)
            .query('isEdi == 0')
            .drop('isEdi', axis=1)
        )
        
        self.log_stats('Editors from the same journal filtered out')

    def sample(self, n_seed=50):

        all_sampled = []

        for seed in tqdm(range(n_seed)):
            np.random.seed(seed)

            sampled = self.matched.groupby(['EditorsNewId','issn']).apply(
                lambda x: x.filter([np.random.choice(x.index, replace=True)], axis=0)).reset_index(drop=True)
            self.debug.log(f'sample editors seed {seed} sampled {sampled.shape}')

            sampled = sampled.assign(seed=seed)
            all_sampled.append(sampled)

        all_sampled = pd.concat(all_sampled, ignore_index=True, sort=False)
        self.matched = all_sampled
        self.log_stats('combined all sampled')

        self.groups = self.matched[['EditorsNewId','issn','AuthorsNewId','seed']].drop_duplicates()
