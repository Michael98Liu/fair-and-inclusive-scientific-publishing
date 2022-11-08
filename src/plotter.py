import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
from scipy import stats
import numpy as np

import helper
import getpub

class Plotter:
    def __init__(self, G):

        self.bad_editors = G.bad_editors.copy()
        self.bad_authors = G.bad_authors.copy()
        self.q_editors = G.q_editors.copy()
        self.q_authors = G.q_authors.copy()
        self.normal_authors = G.normal_authors.copy()
        self.normal_editors = G.normal_editors.copy()

        self.bad_editors = self.bad_editors.assign(EditorYear = self.bad_editors.EditorYear + 1)
        self.bad_authors = self.bad_authors.assign(EditorYear = self.bad_authors.EditorYear + 1)
        self.q_editors = self.q_editors.assign(EditorYear = self.q_editors.EditorYear + 1)
        self.q_authors = self.q_authors.assign(EditorYear = self.q_authors.EditorYear + 1)
        self.normal_authors = self.normal_authors.assign(EditorYear = self.normal_authors.EditorYear + 1)
        self.normal_editors = self.normal_editors.assign(EditorYear = self.normal_editors.EditorYear + 1)

        self.colors = {'normal': '#4daf4a', 'bad': '#e41a1c', 'q':'#f9ba17'}

        self.field_name = pd.read_csv("/scratch/fl1092/capstone/advanced/FieldsOfStudy.txt", sep="\t",
                        names = ["FieldOfStudyId", "Rank", "NormalizedName", "DisplayName",
                                 "MainType", "Level", "PaperCount", "CitationCount", "CreatedDate"],
                       usecols=['FieldOfStudyId','DisplayName'])

        self.__editor_attributes()
        self.__count_by_field()

    def __editor_attributes(self):
        self.editors = pd.read_csv("/scratch/fl1092/capstone/matching/editors.csv", sep='\t',
                     usecols=["EditorsNewId","issn","start_year",'Yfp','Ylp','Parent'],
                     dtype={"EditorsNewId":int, "issn":str, "start_year":int,'Yfp':int,'Ylp':int,'Parent':int})

        self.editors = self.editors.drop_duplicates()
        assert(self.editors.shape[0] == self.editors[["EditorsNewId","issn"]].shape[0])
        self.editors = self.editors.assign(post_span = self.editors.Ylp - self.editors.start_year)
        self.editors = self.editors.assign(prior_span = self.editors.start_year - self.editors.Yfp)

    def __count_by_field(self):
        count_by_field = self.editors.groupby('Parent').issn.count().reset_index()
        count_by_field = count_by_field.rename(columns={'Parent':'FieldOfStudyId','issn':'EditorCount'})
        count_by_field = count_by_field.merge(self.field_name, on='FieldOfStudyId')

        self.count_by_field = count_by_field.sort_values(by='EditorCount', ascending=False).reset_index(drop=True)

    def fill_area(self, xr, yr, ax, text=True, color=False):
        
        ax.fill([xr[0], (xr[0]+xr[1])/2, (xr[0]+xr[1])/2, xr[0]], [yr[0], yr[0], yr[1], yr[1]], alpha=0.2, color='#BDC0BA')
        ax.fill([(xr[0]+xr[1])/2, xr[1], xr[1], (xr[0]+xr[1])/2], [yr[0], yr[0], yr[1], yr[1]], alpha=0.2, color='#FEDFE1')
        
        if text:
            ax.text(-9.5, yr[1]/9*8, 'before becoming editor', fontsize=10)
            ax.text(1, yr[1]/9*8, 'after becoming editor', fontsize=10)

    def mean_confidence_interval(self, a, conf=0.95):
        mean, sem, m = np.mean(a), stats.sem(a), stats.t.ppf((1+conf)/2., len(a)-1)
        return mean, mean - m*sem, mean + m*sem

    def ci_diff(self, year, merged, ci=0.95):

        sample1 = merged[merged.EditorYear == year].Edi.values
        sample2 = merged[merged.EditorYear == year].Aut.values

        n1, n2 = sample1.size, sample2.size
        s1, s2 = np.std(sample1), np.std(sample2)

        sp = np.sqrt(((n1-1)*s1**2 + (n2-1)*s2**2)/(n1+n2-2))
        se = sp*np.sqrt(1/n1 + 1/n2)

        degrees_freedom = n1+n2-2
        sample_mean = np.mean(sample1)-np.mean(sample2)
        confidence_interval = stats.t.interval(ci, degrees_freedom, sample_mean, se)

        assert(round((confidence_interval[0]+confidence_interval[1])/2, 4) == round(sample_mean, 4))

        return sample_mean - confidence_interval[0] # +/- value on mean

    def mean_diff(self, year, merged):
        sample1 = merged[merged.EditorYear == year].Edi.values
        sample2 = merged[merged.EditorYear == year].Aut.values
        return np.mean(sample1)-np.mean(sample2)

    def plot_curve(self, df, y, role, typ, y_min, y_max, x_min, x_max, ax, window):
        df.fillna(0, inplace=True)
        meandf = pd.DataFrame()

        for year in range(x_min, x_max+1):
            data = df[ df['EditorYear'] == year ][y].tolist()
            mid, lo, hi = self.mean_confidence_interval(data)
            meandf = meandf.append({'EditorYear': year, 'mean': mid, 'lo': lo, 'hi': hi}, ignore_index=True)

        meandf.fillna(0, inplace=True)

        meandf['hi'] = meandf.hi.rolling(window, center=False, min_periods=1).mean()
        meandf['lo'] = meandf.lo.rolling(window, center=False, min_periods=1).mean()
        meandf['mean'] = meandf['mean'].rolling(window, center=False, min_periods=1).mean()

        meandf = meandf[(meandf.EditorYear >= x_min) & (meandf.EditorYear <= x_max)]

        if role == 'editors':
            line, = ax.plot(meandf['EditorYear'], meandf['mean'], alpha=1, color=self.colors[typ], linewidth=2.)
        elif role == 'authors':
            line, = ax.plot(meandf['EditorYear'], meandf['mean'], '--', alpha=1, color=self.colors[typ], linewidth=2.)

        ax.fill_between(meandf['EditorYear'], meandf['lo'], meandf['hi'], alpha = 0.1, color=self.colors[typ])
        ax.set_ylim([y_min, y_max])
        ax.set_xlim([x_min, x_max])
        ax.set_xticks([x for x in range(-10, 11, 2)])

        return line

    def plot(self, plot_type, min_x=-10, max_x=10, ymax=600, disp=0, ax=None,
        start_min = 0, start_max = 2020, bad=True, smoothed=True, window=5, color=False):

        assert(plot_type in ['normal', 'bad', 'q'])

        editors = self.editors.copy()
        editors = editors[editors.post_span > 0]
        editors = editors[editors.start_year >= start_min]
        editors = editors[editors.start_year <= start_max]

        if disp > 0:
            editors = editors[editors.Parent == disp]
            dispname = self.field_name[self.field_name.FieldOfStudyId == disp].DisplayName.values[0]
        else:
            dispname = ''

        editors = editors[['EditorsNewId','issn']].drop_duplicates()

        if plot_type == 'normal':
            editor_line = self.normal_editors.copy()
            author_line = self.normal_authors.copy()
        elif plot_type == 'q':
            editor_line = self.q_editors.copy()
            author_line = self.q_authors.copy()
        elif plot_type == 'bad':
            editor_line = self.bad_editors.copy()
            author_line = self.bad_authors.copy()

        editor_line = editor_line[(editor_line.EditorYear >=min_x-window) & (editor_line.EditorYear<=max_x) ]
        author_line = author_line[(author_line.EditorYear >=min_x-window) & (author_line.EditorYear<=max_x) ]

        editor_line = editor_line.merge(editors, on=['EditorsNewId','issn'])
        author_line = author_line.merge(editors, on=['EditorsNewId','issn'])

        editor_count = editor_line[['EditorsNewId','issn']].drop_duplicates().shape[0] # TODO: why is there dup
        print('editors: ', editor_count)
        self.editor_line = editor_line
        self.author_line = author_line

        if ax is None:
            ax = plt.gca()
        self.fill_area([min_x, max_x], [0, ymax], ax, color)

        e_line = self.plot_curve(editor_line, 'Count', 'editors', plot_type, y_min=0, y_max=ymax,
        x_min = min_x, x_max = max_x, ax=ax, window=window)
        a_line = self.plot_curve(author_line, 'Count', 'authors', plot_type, y_min=0, y_max=ymax,
        x_min = min_x, x_max = max_x, ax=ax, window=window)

        ax.set_ylim(ymin=0)
        ax.set_ylim(ymax=ymax)

        return e_line, a_line, editor_count

    def plot_line(self, plot_type, ax=None, ymax=100, min_x=-10, max_x=10, color=False, window=5):
        if plot_type == 'normal':
            editor_line = self.normal_editors.copy()
            author_line = self.normal_authors.copy()
        elif plot_type == 'q':
            editor_line = self.q_editors.copy()
            author_line = self.q_authors.copy()
        elif plot_type == 'bad':
            editor_line = self.bad_editors.copy()
            author_line = self.bad_authors.copy()

        editor_line = editor_line[(editor_line.EditorYear >=min_x-window) & (editor_line.EditorYear<=max_x) ]
        author_line = author_line[(author_line.EditorYear >=min_x-window) & (author_line.EditorYear<=max_x) ]

        self.editor_line = editor_line
        self.author_line = author_line

        editor_count = editor_line[['EditorsNewId','issn']].drop_duplicates().shape[0]
        print('editors: ', editor_count)

        if ax is None:
            ax = plt.gca()
        self.fill_area([min_x, max_x], [0, ymax], ax, color)

        e_line = self.plot_curve(editor_line, 'Count', 'editors', plot_type, y_min=0, y_max=ymax,
        x_min = min_x, x_max = max_x, ax=ax, window=window)
        a_line = self.plot_curve(author_line, 'Count', 'authors', plot_type, y_min=0, y_max=ymax,
        x_min = min_x, x_max = max_x, ax=ax, window=window)

        ax.set_ylim(ymin=0)
        ax.set_ylim(ymax=ymax)

        return e_line, a_line, editor_count

    def plot_by_field(self, plot_type, post_length=0, min_x=-11, max_x=9, ymax=600, disp=0, ax=None,
        start_min = 0, start_max = 2020, bad=True, smoothed=True, window=5):

        plt.figure(figsize=(18, 12))
        plt.subplots_adjust(hspace = 0.3)

        for ind, row in self.count_by_field.iterrows():

            if ind > 8: break
            ax=plt.subplot(3, 3, ind+1)

            disp = row['FieldOfStudyId']

            self.plot(plot_type, min_x, max_x, ymax, disp, ax, start_min, start_max, bad)

    def t_test(self, type='normal'):
        editor_line, author_line = self.editor_line, self.author_line

        print(f'{type} editors and authors')
        df = pd.DataFrame(columns=['year', 't-statistic', 'p-value'])

        for year in range(-9, 11):
            edit = editor_line[editor_line.EditorYear == year].Count
            auth = author_line[author_line.EditorYear == year].Count
            ttest =  stats.ttest_ind(auth, edit)
            df = df.append({'year':year, 't-statistic': round(ttest.statistic, 3), 'p-value': round(ttest.pvalue, 3)},
                           ignore_index=True)

        return df

    def plot_diff(self, typ, min_x=-9, max_x=10, ax=None, max_y=11):
        self.fill_area([-0.5, 19.5], [-max_y*0.1, max_y], ax, False)
        assert(typ in ['normal', 'bad', 'q'])

        merged = self.editor_line.rename(columns={'Count':'Edi'}).merge(
            self.author_line.rename(columns={'Count':'Aut'}), on=['EditorsNewId','issn','EditorYear'], how='left')

        merged = merged[(merged.EditorYear>=min_x) & (merged.EditorYear<=max_x)]
        errbar = [self.ci_diff(year, merged) for year in range(min_x, max_x+1)]
        mean_diff = [self.mean_diff(year, merged) for year in range(min_x, max_x+1)]

        x_range = [year+9 for year in range(min_x, max_x+1)]
        g = ax.bar(x=x_range, height=mean_diff, data=merged, color=self.colors[typ], yerr=errbar, error_kw={'elinewidth':0.8})

        df = self.t_test(typ)
        df = df[(df.year >= min_x) & (df.year <= max_x)]

        for ind, row in df.iterrows():
            if row['p-value'] >= 0.05:
                stars = ''
            elif row['p-value'] < 0.05 and row['p-value'] >= 0.01:
                stars = '*'
            elif row['p-value'] < 0.01 and row['p-value'] >= 0.001:
                stars = '*\n*'
            elif row['p-value'] < 0.001:
                stars = '*\n*\n*'
            ax.text(row.year+9, mean_diff[ind]+errbar[ind], stars, color='black', ha="center", fontsize=10, linespacing=0.3)

        self.diff_df = df.copy()
        self.meandiff = mean_diff
        self.errbar = errbar

        ax.set_xticks([4, 9, 14, 19])
        ax.set_xticklabels(['-5','0','5','10'])
        ax.set_ylim([-max_y*0.1, max_y])
        ax.set_xlim([-0.5, 19.5])
        ax.set_ylabel('')
        ax.set_xlabel('')

        return df

    def plot_box(self, typ, min_x=-9, max_x=10, ax=None, max_y=11):
        self.fill_area([-0.5, 19.5], [-max_y, max_y], ax, False)

        if typ == 'normal':
            merged = self.normal_editors.rename(columns={'Count':'Edi'}).merge(
                self.normal_authors.rename(columns={'Count':'Aut'}), on=['EditorsNewId','issn','EditorYear'], how='left')
        elif typ == 'bad':
            merged = self.bad_editors.rename(columns={'Count':'Edi'}).merge(
                self.bad_authors.rename(columns={'Count':'Aut'}), on=['EditorsNewId','issn','EditorYear'], how='left')
        elif typ == 'q':
            merged = self.q_editors.rename(columns={'Count':'Edi'}).merge(
                self.q_authors.rename(columns={'Count':'Aut'}), on=['EditorsNewId','issn','EditorYear'], how='left')

        merged = merged[(merged.EditorYear>=min_x) & (merged.EditorYear<=max_x)]
        merged = merged.assign(difference = merged.Edi - merged.Aut)
        sns.boxplot(x='EditorYear', y='difference', data=merged, showfliers=False, color=self.colors[typ])

        ax.set_xticks([4, 9, 14, 19])
        ax.set_xticklabels(['-5','0','5','10'])
        ax.set_ylim([-max_y*0.8, max_y])
        ax.set_xlim([-0.5, 19.5])
        ax.set_xlabel('')
        ax.set_ylabel('')
