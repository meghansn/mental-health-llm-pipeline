# Synthetic Clinical Longitudinal Dataset

## Project Goal
Generating a high-fidelity, longitudinal synthetic dataset for clinical ML benchmarking.

## Methodology
Uses Gemini 3.1 Flash-Lite via Vertex AI to generate 12-month synthetic therapy trajectories, stored directly in BigQuery.

## Features
- **Checkpointing:** Resumable execution via `generation_checkpoint.json`.
- **Scalability:** Optimized for streaming inserts into BigQuery.

## Future Roadmap
1. PHI Redaction (via Cloud DLP).
2. Sentiment & Topic Modeling (BERTopic).
3. Clinical Mapping (DSM-5/ICD-10 classification).
4. Predictive Regression analysis.
