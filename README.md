Mental Health LLM Pipeline

Overview

This project explores the development of an end-to-end pipeline for generating, de-identifying, classifying, and analyzing synthetic mental health conversations using NLP and cloud-based data tools.

The project simulates a healthcare analytics workflow, from synthetic data generation and PHI redaction to structured storage and future clinical classification.

Project Objectives

* Generate synthetic mental health conversations
* Detect and remove Protected Health Information (PHI)
* Apply Named Entity Recognition (NER) for entity extraction and de-identification
* Store processed data in Google BigQuery
* Explore DSM-5 and ICD-10 classification approaches
* Engineer features for downstream analytics and machine learning

Current Workflow

1. Synthetic Data Generation

Synthetic patient-provider conversations are generated for experimentation and model development without using real patient data.

2. PHI Redaction

A Python-based redaction pipeline removes common identifiers such as:

* Names
* Dates
* Phone numbers
* Email addresses
* Addresses
* Other sensitive information

3. Named Entity Recognition (NER)

Google Colab notebooks were used to prototype and evaluate NER-based de-identification workflows.

NER successfully identified many common entities, but performance was not perfect. To improve results, NER was supplemented with rule-based and regex approaches for PHI detection and redaction.

This project highlights practical challenges in healthcare NLP, including false positives, false negatives, and entity ambiguity.

4. BigQuery Integration

Processed conversations are loaded into Google BigQuery for scalable storage, querying, and future analytics.

Repository Structure

.
├── Clean_PHI.ipynb
├── Synthetic_Data_Generator.ipynb
├── data_dictionary.md
├── pipeline/
│   ├── redact_pipeline.py
│   ├── requirements.txt
│   └── Dockerfile
└── README.md

Technology Stack

* Python
* Google Colab
* Pandas
* Regular Expressions (Regex)
* Named Entity Recognition (NER)
* Google BigQuery
* Jupyter Notebooks
* Git/GitHub

Lessons Learned

* NER alone is often insufficient for complete PHI removal.
* Combining machine learning and rule-based methods improves de-identification performance.
* Healthcare text contains many edge cases that challenge automated entity recognition.
* BigQuery provides a scalable platform for storing and analyzing processed conversation data.

Roadmap

Completed

* Synthetic conversation generation
* Initial PHI redaction pipeline
* NER experimentation and evaluation
* BigQuery ingestion
* GitHub project setup

Planned

* DSM-5 classification support
* ICD-10 code mapping
* Retrieval-Augmented Generation (RAG)
* Feature engineering
* Descriptive analytics
* Predictive analytics
* Prescriptive analytics

Disclaimer

This project uses synthetic data for educational and research purposes only. It is not intended for clinical diagnosis or medical decision-making.
