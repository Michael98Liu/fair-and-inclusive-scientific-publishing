# Traces of editors impeding a fair and inclusive scientific publishing

As per our agreement with Elsevier, the anonymity of the editors and journals included in our analysis should be preserved (see the file "NYU Abu Dhabi Elsevier Agreement"). As such, we cannot share the full dataset analyzed in the manuscript. We are nonetheless willing to share the code we used to collect and analyze data, along with a step-by-step guide focusing on an arbitrary journal as an example. Additionally, we include the data (anonymized) and code necessary to reproduce the figures.

This code repository is organized in the following way:

- Utility functions and complicated objects can be found in `src/`
- Code related to data collection and data cleaning can be found in `data_collection/`
- Code related to each figure can be found in directories `figure_1/` to `figure_4/`. For each of these, code is divided into three stages:
    - Analysis: The code we use to process and aggregate data; can be executed on the **sample set** of editors;
    - Anonymizing: anonymize the aggregated data on **all** editors analyzed from the previous step;
    - Plot: generate plots using the aggregated data;
- Raw and processed data, as well as [data schema](data/readme.md), are stored in `data/`;
- Figures are stored in `figure/`.

The code to anonymize the actual data is shared for transparency, but this code cannot be executed since its input consists of de-anonymized data that we cannot share due to our agreement with Elsevier. All other notebooks can be executed given that all prerequisites are met. More specifically, this code repository includes:

1. A sample of editorial information pages from an arbitrary journal published by Elsevier;
2. Code to extract and identify editorial board members in Microsoft Academic Graph (MAG); for your convenience, we provided a sample of MAG related to the sample of editors we provide; the full MAG data can be downloaded [here](https://docs.microsoft.com/en-us/academic-services/graph/get-started-receive-data);
3. Code to retrieve the publication, citation, discipline, etc. of identified editors;
4. Code to find matched scientists comparable to editors;
5. Code to classify normal, questionable, and suspicious editors;
6. Code to run the randomized baseline model;
7. A subset of MAG that is necessary for the aforementioned tasks;

## Reproducing results
In order to reproduce our results, the following is needed:
1. A subscription to Elsevier;
2. Formal permission from Elsevier before proceeding with any form of data collection (see our letter of terms and agreement from Elsevier).

## System requirements
The project was created and executed on the NYU High Performance Computing (HPC) cluster [Greene](https://sites.google.com/a/nyu.edu/nyu-hpc/systems/greene-cluster) with computing jobs utilizing at most 499GB of memory. The code in this repo can run on any commercial laptop with at least 8GB of memory, and is tested on a 2017 MacBook Air (macOS Catalina).

## Environment
- Python 3.8.5

Python libraries:
- pandas 1.2.0
- numpy 1.19.2
- scipy 1.7.4
- matplotlib 3.3.2
- scikit-learn 0.24.2
- pycountry 20.7.3
- fuzzywuzzy 0.18.0
- beautifulsoup4 4.9.3
- Unidecode 1.3.1

Install all libraries with `pip`: `pip install -r requirements.txt`.
