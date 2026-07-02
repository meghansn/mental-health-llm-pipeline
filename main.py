import json
from textwrap import dedent

from google.cloud import bigquery
from sklearn.metrics.pairwise import cosine_similarity

import vertexai
from vertexai.generative_models import GenerativeModel
from vertexai.language_models import TextEmbeddingModel

from config import (
    PROJECT_ID,
    LOCATION,
    PATIENT_DATASET,
    EMBEDDING_MODEL,
    LLM_MODEL,
)

# Initialize Vertex AI.
vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
)

# Initialize clients and models.
client = bigquery.Client(project=PROJECT_ID)
embedding_model = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL)
llm = GenerativeModel(LLM_MODEL)


def clean_json_response(text):
    text = text.strip()
    if text.startswith("```json"):
        text = text.removeprefix("```json").strip()
    elif text.startswith("```"):
        text = text.removeprefix("```").strip()
    if text.endswith("```"):
        text = text.removesuffix("```").strip()
    return text


def load_diagnosis(response_text, patient_id):
    cleaned = clean_json_response(response_text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON for patient {patient_id}:")
        print(cleaned)
        raise exc

# Load all disorder embeddings.
disorder_query = """
SELECT
    de.disorder_id,
    dd.disorder_name,
    dd.icd10_code,
    de.retrieval_text,
    de.embedding
FROM `mental-health-llm-pip.mental_health.disorder_embeddings` de
JOIN `mental-health-llm-pip.mental_health.dim_disorders` dd
    ON de.disorder_id = dd.disorder_id
"""

disorders_df = client.query(disorder_query).to_dataframe()

# Fetch patients with session data.
patient_query = f"""
SELECT
    dp.*,
    fs.session_date,
    fsr.*
FROM `{PROJECT_ID}.{PATIENT_DATASET}.dim_patients` dp
JOIN `{PROJECT_ID}.{PATIENT_DATASET}.fact_sessions` fs
    ON dp.patient_id = fs.patient_id
JOIN `{PROJECT_ID}.{PATIENT_DATASET}.fact_sessions_redacted` fsr
    ON fs.session_id = fsr.session_id
WHERE dp.dsm5_diagnosis IS NULL
ORDER BY dp.patient_id, fs.session_date
"""

df = client.query(patient_query).to_dataframe()
print(f"Rows: {len(df)}")
print(f"Unique patients: {df['patient_id'].nunique()}")

for count, patient_id in enumerate(df["patient_id"].unique(), start=1):
    patient_df = df[df["patient_id"] == patient_id]
    longitudinal_symptoms = []

    for _, row in patient_df.iterrows():
        longitudinal_symptoms.append(f"Session Date: {row['session_date']}")
        longitudinal_symptoms.append(f"Symptoms: {row['extracted_symptoms']}")

    patient_history = "\n\n".join(longitudinal_symptoms)
    query_embedding = embedding_model.get_embeddings([patient_history])[0].values

    disorders_df["similarity"] = disorders_df["embedding"].apply(
        lambda x: cosine_similarity([query_embedding], [x])[0][0]
    )
    top_disorders = disorders_df.sort_values("similarity", ascending=False).head(1)

    rag_context = "".join(
        f"Disorder: {row['disorder_name']}\n{row['retrieval_text']}\n\n"
        for _, row in top_disorders.iterrows()
    )

    prompt = dedent(f"""
        Use only the RAG table context below. Do not use outside knowledge.

        Patient: {patient_history}

        RAG table context: {rag_context}

        Return valid JSON only. Arrays must contain strings.
        {{
          "primary_diagnosis": "",
          "supporting_symptoms": [],
          "differential_diagnoses": []
        }}
    """).strip()

    response = llm.generate_content(prompt)
    diagnosis = load_diagnosis(response.text, patient_id)
    dsm5 = diagnosis["primary_diagnosis"]

    icd_query = f"""
    SELECT icd10_code
    FROM `{PROJECT_ID}.mental_health.dim_disorders`
    WHERE disorder_name = @diagnosis
    LIMIT 1
    """

    icd_job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("diagnosis", "STRING", dsm5)
        ]
    )

    icd_df = client.query(icd_query, job_config=icd_job_config).to_dataframe()
    icd10 = icd_df.iloc[0]["icd10_code"] if not icd_df.empty else None

    update_query = f"""
    UPDATE `{PROJECT_ID}.{PATIENT_DATASET}.dim_patients`
    SET
        dsm5_diagnosis = @diagnosis,
        icd10_code = @icd10
    WHERE patient_id = @patient_id
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("diagnosis", "STRING", dsm5),
            bigquery.ScalarQueryParameter("icd10", "STRING", icd10),
            bigquery.ScalarQueryParameter("patient_id", "STRING", patient_id),
        ]
    )

    update_job = client.query(update_query, job_config=job_config)
    update_job.result()
    print(
        f"Patient {count}/{df['patient_id'].nunique()} "
        f"updated rows: {update_job.num_dml_affected_rows} "
        f"diagnosis: {dsm5}"
    )
