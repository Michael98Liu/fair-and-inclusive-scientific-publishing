# Data schema

### Data collection

We demonstrate how we download Editorial Board pages and parse editors from them using a sample issue (Volume 15) from an arbitrary journal (Comparative Biochemistry and Physiology Part D: Genomics and Proteomics).

Next, we identify the collected editorial board members in MAG using the first and last name (or first and middle initial and last name), affiliation, and year(s) of the affiliation of each editor.

As this is only a demonstrative example, the start and end of all editor's editorial career, in this particular example, is 2015. If the same procedure is applied on the entired set of editorial pages, you can end up with the complete set of editors and their accurate start and end of editorial career.

From the set of editors that we have obtained accordingly, we sample 10 editors from the aforementioned journal (for demonstrative purposes), stored at `../data/SampleEditors.csv`, and use them to demonstrate susbsequent analysis.

The schema of all table related to data colleciton are described in details below:

- `EditorialPageLinks.csv`: a sample of one manually curated link to the PDF files of Editorial Board pages.
    - title: journal title
    - issn: journal issn
    - issue
    - volume
    - date: date in the format of 'yyyymmdd'
    - date_text: date in the format of 'month yyyy'
    - pdf_link: link to the PDF file of editorial page
    - supplement_text: the volume and issue in text
    - exist: whether a PDF file of editorial board page exists
    
- `editorial_board_info/`: contains a sample of xml files containing editorial board information.

- `EditorTitles.csv`: the list of all possible editorial titles an Elsevier journal editor may have. 
    - original: the original spelling of an editorial title
    - normalized: editorial titles after removing non-alphabetical characters
    
- `SampleEditorsVol15.csv`: list of editors parsed from editorial information page of Volume 15 of journal "Comparative Biochemistry and Physiology Part D: Genomics and Proteomics".
    - title: journal title
    - issn: journal issn
    - issue: volume and issue as text
    - editorName: name of editor as shown on the editorial page
    - editorAff: affiliation of editor as shown on the editorial page
    - date: date when the issue, where name and affiliation data is collected, is published
    - Year: year when the issue, where name and affiliation data is collected, is published

- `SampleEditors.csv`: 10 editors randomly sampled from an arbitary journal.
    - NewAuthorId: identifier of authors
    - issn: issn of the journal one edits
    - start_year: the year one becomes an editor
    - end_year: the year one stops being an editor
    
- `EditorPapers.csv`: set of papers the 10 editors published.
    - NewAuthorId: identifier of authors
    - PaperId: identifier of a paper authored by the author
    - Year
    - JournalId: identifier for the journal the paper is published in
    
- `EditorCitations.csv`: citations the 10 editors received.
    - NewAuthorId: identifier of authors
    - CitesFrom: the papers that cite one of the 10 editors
    - BeingCited: the papers that the 10 editors publish
    - Year: when the citation was made
    
- `EditorGender.csv`: the gender of the 10 editors.
    - NewAuthorId: identifier of authors
    - gender: male or female

- `ElsevierJournals.csv`: set of journals published by Elsevier.  
    - DisplayName: journal title
    - JournalId: identifier of journal
    - issn: journal issn

- `EditorCareerDiscipline.csv`: the field of research, year of first publication, and year of last publication of an editor.
    - NewAuthorId: identifier of authors
    - Yfp: year of first publication
    - Ylp: year of last publication
    - Parent: identifier of field of research
    
- `Editorials.csv`: set of editorials that is written by one of the 10 editors.
    - PaperId: paper identifier
    - Editorial: whether the paper is an editorial
    
- `manual_labeled_different.csv` and `manual_labeled_same.csv`: pairs of affiliation names manually labeled to be same/different.

### Data cleaning

Due to the shear size of the MAG dataset, we only provide the subset of scientists that is necessary to performe the aforementioned identification process for the sample of editors from the selected journal (Volume 15 of Comparative Biochemistry and Physiology Part D: Genomics and Proteomics).

- `mag/AuthorNames.csv`: subset of authors in MAG that is used to identify each editor in MAG.
    - NewAuthorId: identifier of authors
    - first: first name
    - middle: middle name
    - last: last name
    - f_ini: first name initial
    - m_ini: middle name initial
    
- `mag/AuthorAffYear.csv`: when and what each author's affiliation is when they publish each paper; the same subset of authors as in `mag/AuthorNames.csv`.
    - NewAuthorId: identifier of authors
    - AffiliationId: identifier of affiliations
    - Year: year(s) when the author is associated with the affiliation
    
- `mag/Affiliations.txt`: the original affiliations data from MAG, schema see [here](https://docs.microsoft.com/en-us/academic-services/graph/reference-data-schema#affiliations).

### Figure 1

The original data used for figure 1 are organized such that each row represents an editor and a comparable author. But since the dataframe contains identifying information of editors such as paper count, citation count, rank of first affiliation etc. that, once combined, may be able to identify an editor, we **remove the ID of each row and shuffle data within each group of Year0 and field-of-study**, such that you can no longer identify scientists from the data we use, while preserving the overall distribution of attributes of the population.

Below are the schema of the two tables representing the distribution of the different fields used for both editors and authors, respectively.

- `figure_1/EditorStats.csv`: the data related to editors in figure 1, shuffled.
    - Year0: the year before one becomes an editor
    - Parent: the FieldOfStudyId of the editor's scientific field of research
    - age: academic age of an editor in year0 
    - EPriorPaperCount: cumulative paper count by the end of year0
    - EPriorCitationCount: cumulative citation count by the end of year0
    - EHindex: H-index by the end of year0
    - EColabCount: total number of collaborators by the end of year0
    - ETop: whether the editor is affiliated with a top-100 affiliation in year0
    
- `figure_1/AuthorStats.csv`: the data related to authors matched to editors in figure 1, shuffled.
    - Year0: the Year0 of the author's matched editor
    - Parent: the FieldOfStudyId of the author's matched editor
    - APriorPaperCount: the average cumulative paper count by the end of year0 of all authors matched to one editor
    - APriorCitationCount: the average cumulative citation count by the end of year0 of all authors matched to one editor
    - AHindex: the average H-index by the end of year0 of all authors matched to one editor
    - AColabCount: the average total number of collaborators by the end of year0 of all authors matched to one editor
    - ATop: the precentage of authors who is affiliated with a top-100 affiliation in year0
    
    
We also demonstrate the process of finding a match for an editor. For each editor, we sample a set of authors whose year-of-first-publication matches that of the editor. For the sake of demonstration, we picked a subset of authors to match against so that the code could finish in a reasonable amount of time. The following two files contain information on the subset of authors. 

- `figure_1/FirstYearWithKnownAff.csv`: the first year with a known affiliation of a subset of authors.
    - NewAuthorId: identifier of authors
    - FirstYear: the first year an author publishes with a known affiliation
    
- `figure_1/AuthorEraDisp.csv`: the field of research, year of first publication, and year of last publication of a subset of authors.
    - NewAuthorId: identifier of authors
    - Yfp: year of first publication
    - Ylp: year of last publication
    - Parent: identifier of field of research
    
### Figure 2

We first calculate the percentage of male and female authors, editors, and editors-in-chief (EICs) in each year.

Then, we use a randomized baseline model that randomly replaces editors (or EICs) with a randomly selected scientist who may have a different gender but is identical in terms of discipline and academic age, and similar in terms of productivity and impact (both binned into deciles).

- The following 3 files stores the count of male and female authors/editors/editors-in-chief in each discipline in each year: `AuthorGenderCount.csv`, `EditorGenderCount.csv`, and `ChiefGenderCount.csv`.
    - Year
    - gender: male or female
    - Field: discipline
    - Count: number of authors/editors/editors-in-chief
    
- `figure_4/EditorCareerLength.csv`: the gender and career length of each editor.
    - gender: male or female
    - Field: discpiline
    - length: length of editorship in years
    
- `figure_4/Fields.csv`: the list of fields sorted alphabetically.

- `figure_4/randomBaseline/Editors.csv`: each row represents an editor.
    - gender: the gender of this editor
    - Field: the discipline of this editor
    - Year: he/she is serving as an editor in this year

- `figure_4/randomBaseline/EICs.csv`: each row represents an editor-in-chief.
    - gender: the gender of this editor-in-chief
    - Field: the discipline of this editor-in-chief
    - Year: he/she is serving as an editor-in-chief in this year
    
- `figure_4/randomBaseline/editorSampleAgeCitePub/`: each row represents a randomly selected scientist replacing editors as described; sampling repeated 50 times, each stored in a different file.
    - gender: the gender of this randomly selected scientist
    - Field: the discipline of this randomly selected scientist (same as the editor he/she replaces)
    - Year: the replaced editor is serving as an editor in this year

- `figure_4/randomBaseline/eicSampleAgeCitePub/`: each row represents a randomly selected scientist as described; sampling repeated 50 times, each stored in a different file.
    - gender: the gender of a randomly selected scientist
    - Field: the discipline of a randomly selected scientist (same as the editor-in-chief he/she replaces)
    - Year: the replaced editor-in-chief is serving as an editor-in-chief in this year
    
### Figure 3

When matching, first match editors and authors on their discipline, gender, rank of first affiliation, and year of first publication. Then, find out the year in author's career (call it AuthorYear0) when the author's paper/citation count in that year, and the author's cummulative paper/citaion count by the end of that year, are comparable to those of an editor and in the editor's EditorYear0. Two additional criteria: AuthorYear0 does not differ from EditorYear0 by more than 3 years; the academic age of the editor and author does not differ by more than 10% when they are being compared.

- `figure_3/AuthorsMatch.csv`: Authors matched to editors and the percentage of their papers that go to the editor's journal.
    - EditorYear: The number of years since the matched editor starts editorship.
    - AutPercent: The percentage of papers got published in the editor's journal each year.
    - Cohort: Divided editors into cohorts based on their self-publication rate.
    
- `figure_3/EICandBoard.csv`: Percentage of self-publication of editors-in-chief and their corresponding editorial board.
    - ChiefPercent: The self-publication rate of an editor-in-chief.
    - BoardAvg: The average self-publication rate of his/her editorial board.

- `figure_3/EditorPercentageGender.csv`: Self-publication rate and gender of each editor.
    - AfAvg: The self-publication rate (i.e., the percentage of papers got published in the editor's journal during the five-year period after becoming an editor).
    - gender: gender of the editor.

- `figure_3/EditorsMatch.csv`: The editors who are matched to scientists and their annual self-publication rate.
    - EditorYear: The number of years since the matched editor starts editorship.
    - EdiPercent: The percentage of self-published papers each year.
    - Cohort: Divided editors into cohorts based on their self-publication rate.

- `figure_3/EditorsPeer.csv`: All editors and their annual self-publication rate.
    - EditorYear: The number of years since the start of editorship.
    - EdiPercent: The percentage of self-published papers each year.
    - Cohort: Divided editors into cohorts based on their self-publication rate.

- `figure_3/PeerTrend.csv`: The average annual self-publication rate of all editors on the same editorial board in the same year for each editor.
    - EditorYear: The number of years since the start of editorship.
    - EdiPercent: The average percentage of self-published papers of all editors on the same editorial board.
    - Cohort: Divided editors into cohorts based on their self-publication rate.

- `figure_3/cumulative.csv`: The self-publication rate and the discipline of each editor.
    - Percentage: Self-publication rate.
    - FieldOfStudyId: The ID of the field of study of the editor.
    - Field: The field of the editor.
    
For the sake of demonstration, we picked a subset of authors to match against so that the code could finish in a reasonable amount of time. The following three files contain information on the subset of authors.

- `figure_2/AuthorCareer.csv`: the field-of-study, year-of-first-publicaiton, and year-of-last-publication of the set of authors to be matched against.
    - NewAuthorId: identifier of authors
    - Yfp: year of first publication
    - Ylp: year of last publication
    - Parent: identifier of field of research

- `figure_2/AuthorFirstAffRank.csv`: the rank of first affiliation of a subset of authors; same subset of authors as in `figure_2/AuthorCareer.csv`.
    - NewAuthorId: identifier of authors
    - Rank: rank of first affiliation

- `figure_2/AuthorGender.csv`: the gender of a subset of authors; same subset of authors as in `figure_2/AuthorCareer.csv`.
    - NewAuthorId: identifier of authors
    - gender: male or female

### Figure 4

For each editor, we calculate what's the total percentage of one's paper that is published in the journal(s) that one edits during editorship; notice that one may edit multiple journals throughout one's publishing career. For each journal, we calculate the percentage of papers that are authored by its editorial board. This data is not publicly shared.

- `EditorPapers.csv`: paper count by three editors shown in figure 3
    - EditorId: Anonymized identifier of editors
    - IssnId: Anonymized identifier of journals
    - AnoPaperId: Anonymized identifier of papers
    - Year
    - edit: whether the paper is published in a journal that the editor edits
    - during: whether the paper is published during the time when the editor is editting that journal
    
- `Editors.csv`: three editors shown in figure 3.
    - EditorId: anonymized identifier of editors
    - IssnId: anonymized identifier of the journal one edits
    - start_year: the year one becomes an editor
    - end_year: the year one stops being an editor
    
- `EditorPapersInJournal.csv`: the number of papers in each of the three Elsevier journals that is authored by its editors in each year.
    - Year
    - IssnId: anonymized identifier of the journal one edits
    - Count: number of papers

- `TotalPapersInJournal.csv`: the total number of papers in each of the three Elsevier journal in each year.
    - Year
    - IssnId: anonymized identifier of the journal one edits
    - Total: number of papers

