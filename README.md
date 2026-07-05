Mental Health LLM Pipeline

Overview

The Mental Health LLM Pipeline is an end-to-end generative AI application that simulates longitudinal mental health records and demonstrates how Retrieval-Augmented Generation (RAG) can support diagnostic decision-making.

The project generates synthetic therapy sessions, extracts clinically relevant symptoms using large language models, stores structured data in Google BigQuery, retrieves candidate disorders using vector embeddings, and produces explainable diagnoses through a RAG pipeline. An interactive Streamlit application allows users to explore patient trajectories, review model predictions, and inspect the complete diagnostic workflow.

Note: All patient records are synthetic and generated for research and educational purposes only. No real patient data is included.

⸻

Features

* Synthetic longitudinal mental health dataset generation
* Automated symptom extraction from therapy transcripts
* Google BigQuery data warehouse
* Retrieval-Augmented Generation (RAG) diagnostic pipeline
* Disorder retrieval using vector embeddings
* Explainable LLM-generated diagnoses
* Interactive Streamlit dashboard
* Dockerized application for reproducible deployment

⸻

Architecture

Synthetic Patient Profiles
            │
            ▼
LLM Therapy Transcript Generation
            │
            ▼
Google BigQuery
            │
            ▼
Symptom Extraction
            │
            ▼
Disorder Embeddings
            │
            ▼
Similarity Retrieval (RAG)
            │
            ▼
Gemini Diagnostic Reasoning
            │
            ▼
Streamlit Dashboard

⸻

Repository Structure

.
├── app/
│   └── streamlit_app.py
├── pipeline/
│   ├── Dockerfile
│   └── ...
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
└── ...

⸻

Technology Stack

Languages

* Python

Cloud

* Google Cloud Platform (GCP)
* BigQuery
* Vertex AI

AI & NLP

* Gemini
* Retrieval-Augmented Generation (RAG)
* Text Embeddings
* Transformers

Data

* Pandas

Application

* Streamlit

Deployment

* Docker
* Docker Compose

⸻

RAG Workflow

The diagnostic pipeline follows these steps:

1. Generate synthetic patient therapy sessions.
2. Extract structured symptoms from each transcript.
3. Aggregate patient symptom history.
4. Retrieve the most relevant disorders using vector embeddings.
5. Provide the retrieved clinical context to the language model.
6. Generate an explainable diagnosis with supporting evidence.

This approach improves diagnostic grounding by combining semantic retrieval with LLM reasoning.

⸻

Streamlit Dashboard

The application includes interactive pages for:

* Patient exploration
* Longitudinal therapy sessions
* Extracted symptoms
* RAG-assisted diagnosis
* Model evaluation
* PHI validation

⸻

Running with Docker

Prerequisites

* Docker Desktop
* Google Cloud SDK
* Access to the associated Google Cloud project
* Application Default Credentials configured

Authenticate locally:

gcloud auth application-default login

Build and start the application:

docker compose up --build

Open the application:

http://localhost:8501

Stop the application:

docker compose down

⸻

Running Without Docker

Install dependencies:

pip install -r requirements.txt

Run Streamlit:

streamlit run app/streamlit_app.py

⸻

Future Improvements

Potential future enhancements include:

* Public deployment on Google Cloud Run
* Automated CI/CD with GitHub Actions
* Expanded evaluation metrics
* Enhanced visualization of retrieval results
* Multi-agent clinical workflow experimentation

⸻

Project Goals

This project demonstrates practical experience with:

* Large Language Models (LLMs)
* Retrieval-Augmented Generation (RAG)
* Prompt engineering
* Vector embeddings
* Cloud-based data engineering
* Interactive analytics
* Containerized deployment
* End-to-end AI application development

⸻

Disclaimer

This repository is intended solely for educational, research, and portfolio purposes. All patient records are synthetically generated and do not represent real individuals. The application is not intended for clinical use or medical decision-making.
