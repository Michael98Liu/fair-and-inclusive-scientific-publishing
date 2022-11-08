import datetime
import os
import pandas as pd
from tqdm import tqdm_notebook as tqdm

seq = None

if seq == None:
    log_file = "LOG_{}.log"
    info_file = "LOG_info_{}.log"
    debug_file = "LOG_debug_{}.log"
else:
    log_file = f"LOG_{seq}" + "_{}.log"
    info_file = f"LOG_info_{seq}" + "_{}.log"
    debug_file = f"LOG_debug_{seq}" + "_{}.log"


class Log:
    def __init__(self, dir_name, verbose = True, fname = log_file):
        self.fname = dir_name+fname
        self.verbose = verbose

    def log(self, s):
        time = datetime.datetime.now().strftime("%Y-%m-%d")
        self.f_log = open(self.fname.format(time), "a+")
        time = datetime.datetime.now().strftime("%I:%M%p")

        self.f_log.write(time)
        self.f_log.write("|")
        self.f_log.write(s)
        self.f_log.write("\n")

        self.f_log.close()

        if self.verbose:
            print(s)

class Loader:

    def __init__(self, dir_name = None, verbose = True):
        now = datetime.datetime.now()
        y, m, d = now.year, now.month, now.day

        if dir_name == None:
            dir_name = f"/scratch/fl1092/capstone/matching/{y}_{m}_{d}/"

        self.update_directory(dir_name)

    def update_directory(self, new_dir):
        self.directory = new_dir

        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
            print(self.directory, "created")
        else:
            print(self.directory, "exists")

        self.LOG = Log(self.directory, fname = log_file, verbose = True)
        self.debug = Log(self.directory, fname = debug_file, verbose = False)
        self.LOG.log("Done initializing")

    def load_editors(self):
        self.editors = pd.read_csv("/scratch/fl1092/capstone/elsevier/editors.csv", sep='\t',
                     usecols=["NewAuthorId", "issn", "start_year", "end_year"],
                     dtype={"NewAuthorId":int, "issn":str, "start_year":int, "end_year":int})
        self.editors = self.editors.rename(columns={'NewAuthorId':'EditorsNewId'})

        assert(self.editors.issn.apply(lambda x: len(x) ==8).all())
        assert(self.editors[(self.editors.start_year >= 2018) | (self.editors.start_year < 1950)].shape[0]==0)
        self.LOG.log(f"editors: {self.editors.shape} unique: {self.editors.EditorsNewId.nunique()}")

    def load_career(self):
        self.author_career = pd.read_csv('/scratch/fl1092/capstone/conflated/AuthorEraDisp.csv',
            sep='\t', memory_map=True,
            usecols=['NewAuthorId', 'Yfp', 'Ylp', 'Parent'],
            dtype={'NewAuthorId':int, 'Yfp':int, 'Ylp':int, 'Parent':int})

    def load_field(self):

        self.parent_of_fields = pd.read_csv("/scratch/fl1092/capstone/FieldOfStudyParent.csv", sep='\t',
                                           usecols=['Field', 'Parent'],
                                           dtype={'Field': int, 'Parent': int}) # all level-0

        self.field_parent = pd.read_csv("/scratch/fl1092/capstone/conflated/AuthorFields.csv",sep='\t',
        usecols=['NewAuthorId', 'Parent'], dtype={'NewAuthorId':int, 'Parent':int})
        assert(self.field_parent.Parent.nunique() == 19)

        self.LOG.log(f"fields shape: {self.field_parent.shape}")

    def load_impact(self):
        self.prior_impact = {}
        for year in tqdm(range(1900, 2019)):
            prior_impact = pd.read_csv(f'/scratch/fl1092/capstone/conflated/prior_impact/{year}.csv',
                                                  sep='\t', memory_map=True,
                                                  usecols=['NewAuthorId', 'CitationCount'])
            prior_impact = prior_impact.rename(columns={'CitationCount':'Prior'})
            self.prior_impact[year] = prior_impact
        self.LOG.log(f"prior_impact loaded")

        self.citation_year = pd.read_csv("/scratch/fl1092/capstone/conflated/AuthorCitationYear.csv",
                     sep='\t', memory_map=True,
                    usecols=['NewAuthorId', 'Year', 'CitationCount'],
                    dtype={'NewAuthorId': int, 'Year': int, 'CitationCount': int})
        self.citation_year = self.citation_year.rename(columns={"CitationCount": 'Count'})
        self.LOG.log(f"citation per year: {self.citation_year.shape}")

    def load_self_citation(self):
        self.selfcite_rate = pd.read_csv("/scratch/fl1092/capstone/conflated/SelfCitationRate.csv",
            sep='\t',memory_map=True,usecols=['NewAuthorId','Year','SelfciteRate'],
            dtype={'NewAuthorId':int,'Year':int,'SelfciteRate':float})
        self.selfcite_rate = self.selfcite_rate.rename(columns={"SelfciteRate": 'Count'})

        self.self_citation = pd.read_csv("/scratch/fl1092/capstone/conflated/SelfCitation.csv",
            sep='\t',memory_map=True,usecols=['NewAuthorId','Year','CitationCount'],
            dtype={'NewAuthorId':int,'Year':int,'CitationCount':int})
        self.self_citation = self.self_citation.rename(columns={"CitationCount": 'Count'})

        self.prior_selfcite = {}
        for year in tqdm(range(1900, 2019)):
            df = pd.read_csv(f'/scratch/fl1092/capstone/conflated/prior_selfcite/{year}.csv', memory_map=True,
                             usecols=['NewAuthorId', 'CitationCount'],
                             dtype={'NewAuthorId':int, 'CitationCount':int})
            df = df.rename(columns={'CitationCount':'Prior'})
            self.prior_selfcite[year] = df

        self.LOG.log(f'selfcite rate: {self.selfcite_rate.shape} self citation: {self.self_citation.shape}')

    def load_journal_citation(self):
        
        self.prior_journal_citation = {}

        for year in tqdm(range(1900, 2019)):
            j_cite = pd.read_csv(f'/scratch/fl1092/capstone/conflated/prior_journal_citation/{year}.csv',
                sep='\t', memory_map=True,usecols=['NewAuthorId', 'issn', 'CitationCount'],
                dtype={'NewAuthorId':int,'issn':str,'CitationCount':int})

            j_cite = j_cite.rename(columns={'CitationCount':'Prior'})
            self.prior_journal_citation[year] = j_cite

        self.journal_citation = pd.read_csv("/scratch/fl1092/capstone/conflated/JournalCitationYear.csv",
            sep='\t', memory_map=True, usecols=['NewAuthorId', 'issn', 'Year', 'CitationCount'],
            dtype={'NewAuthorId':int, 'issn':str, 'CitationCount':int, 'Year':int})
        self.journal_citation = self.journal_citation.rename(columns={'CitationCount':'Count'})

        self.LOG.log("Journal citation loaded")

    def load_paper_count(self):
        self.prior_paper = {}
        for year in tqdm(range(1900, 2019)):
            prior_paper = pd.read_csv(f'/scratch/fl1092/capstone/conflated/prior_paper/{year}.csv',
                                                  sep='\t', memory_map=True,
                                                  usecols=['NewAuthorId', 'PaperCount'])
            prior_paper = prior_paper.rename(columns={'PaperCount':'Prior'})
            self.prior_paper[year] = prior_paper
        self.LOG.log(f'prior paper loaded')

        self.paper_count = pd.read_csv("/scratch/fl1092/capstone/conflated/AuthorPaperCount.csv", sep='\t',memory_map=True,
        usecols = ['NewAuthorId','Year','PaperCount'],dtype={'NewAuthorId':int,'Year':int,'PaperCount':int})
        self.paper_count = self.paper_count.rename(columns={"PaperCount": 'Count'})

        self.LOG.log(f'paper count: {self.paper_count.shape}')

    def load_journal_publication(self):
        # the ones who have published in journal at least once
        self.prior_journal_paper = {}
        for year in tqdm(range(1900, 2019)):
            prior_paper = pd.read_csv(f"/scratch/fl1092/capstone/conflated/prior_journal_paper/{year}.csv",
                                      sep='\t',memory_map=True,usecols=['NewAuthorId','issn','PaperCount'],
                                     dtype={'NewAuthorId':int,'issn':str,'PaperCount':int})
            prior_paper = prior_paper.rename(columns={'PaperCount':'Prior'})
            self.prior_journal_paper[year] = prior_paper

        self.journal_paper = pd.read_csv("/scratch/fl1092/capstone/conflated/JournalPaperYear.csv",
            sep='\t', memory_map=True,
            usecols=['NewAuthorId','issn','Year','PaperCount'],
            dtype={'NewAuthorId':int,'issn':str,'Year':int,'PaperCount':int})
        self.journal_paper = self.journal_paper.rename(columns={"PaperCount": 'Count'})

        self.LOG.log(f'prior journal paper loaded. journal paper count: {self.journal_paper.shape}')

    def load_journal_career(self):
        self.journal_career = pd.read_csv("/scratch/fl1092/capstone/conflated/AuthorJournalCareer.csv",
            sep='\t', memory_map=True, usecols=['NewAuthorId','Yfp','Ylp','Parent','issn'],
            dtype={'NewAuthorId':int,'Yfp':int,'Ylp':int,'Parent':int,'issn':str})
        self.LOG.log(f'journal career loaded')

    def load_network_size(self):
        network = pd.read_csv('/scratch/fl1092/capstone/conflated/AID_Network_ND.csv', sep=',',
                             usecols=['newAID','num_coAIDs','PubYear'],
                             dtype={'newAID':int,'num_coAIDs':int,'PubYear':int})
        self.network_size = network.rename(columns={'newAID':'NewAuthorId','PubYear':'Year','num_coAIDs':'Count'})
        self.LOG.log(f'network size loaded {self.network_size.shape}')

    def load_df(self):

        self.paper_year = pd.read_csv("/scratch/fl1092/capstone/mag/PaperAuthorYear.csv",
                                      dtype={'PaperId': int, 'Year': int, 'EntityId': int},
                                      usecols = ['PaperId', 'Year', 'EntityId'], sep='\t')

        self.paper_year = self.paper_year[self.paper_year.Year < 2019]


        self.paper_author = pd.read_csv("/scratch/fl1092/capstone/bigmem/Paper_EntityId.csv",
                                        dtype={'PaperId': int, 'EntityId': int},
                                        usecols=['PaperId', 'EntityId'], sep='\t')

        self.paper_journals = pd.read_csv("/scratch/fl1092/capstone/mag/Paper_journals.csv", sep = '\t',
                                     dtype={'PaperId': int, 'JournalId': int},
                                     usecols = ['PaperId', 'JournalId'], memory_map=True)

        self.reference = pd.read_csv(f"/scratch/fl1092/capstone/mag/PaperReferences.txt", sep="\t",
                                     dtype={'CitesFrom': int, 'BeingCited': int},
                               names = ['CitesFrom', 'BeingCited'], memory_map=True)

        self.LOG.log(f"paper author: {self.paper_author.shape}\npaper_year: {self.paper_year.shape}")
        self.LOG.log(f"paper journals: {self.paper_journals.shape}\nreferences: {self.reference.shape}")
