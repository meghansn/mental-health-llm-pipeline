import os
import math
import re
from google.cloud import bigquery
import pandas as pd
from transformers import pipeline

def main():
    # 1. ORCHESTRATION & ENVIRONMENT VARIABLES
    task_index = int(os.environ.get("CLOUD_RUN_TASK_INDEX", 0))
    task_count = int(os.environ.get("CLOUD_RUN_TASK_COUNT", 1))
    
    client = bigquery.Client()
    project_id = "mental-health-llm-pip"
    dataset_id = "patient_insights"
    
    print(f"🚀 Task {task_index}/{task_count} initializing pipeline process...")

    # 2. DYNAMIC WORKLOAD CALCULATION
    count_query = f"SELECT COUNT(*) as total FROM `{project_id}.{dataset_id}.fact_sessions`"
    try:
        count_job = client.query(count_query)
        total_rows = list(count_job.result())[0]['total']
        print(f"📊 Database Metrics: Found {total_rows} total rows to process.")
    except Exception as e:
        print(f"❌ Failed to fetch table metrics: {e}")
        return

    # Mathematically slice the dataset segments for parallel execution
    rows_per_task = math.ceil(total_rows / task_count)
    offset = task_index * rows_per_task
    
    print(f"📦 Task {task_index} assigned {rows_per_task} rows starting at offset {offset}.")

    # 3. DATA INGESTION
    query = f"""
        SELECT session_id, raw_transcript_unredacted 
        FROM `{project_id}.{dataset_id}.fact_sessions`
        ORDER BY session_id
        LIMIT {rows_per_task} OFFSET {offset}
    """
    
    try:
        print("⏳ Querying BigQuery data warehouse...")
        df = client.query(query).to_dataframe()
    except Exception as e:
        print(f"❌ Failed to query BigQuery: {e}")
        return

    if df.empty:
        print(f"ℹ️ Task {task_index} found no records in its offset range. Exiting.")
        return

    print(f"✅ Loaded {len(df)} rows successfully into memory.")

    # 4. TRANSFORMER MODEL LOADING
    print("⏳ Initializing Hugging Face token classification pipeline...")
    try:
        nlp = pipeline("ner", model="dslim/bert-base-NER", aggregation_strategy="simple")
        print("🧠 Model matrices loaded successfully!")
    except Exception as e:
        print(f"❌ Hugging Face model failed to load: {e}")
        return

    # 5. BACK-TO-FRONT REDACTION ENGINE
    def redact_text(text):
        if not isinstance(text, str) or not text.strip():
            return text
            
        # --- GUARDRAIL: Catch structural speaker tags at the start of lines ---
        text = re.sub(r'(?m)^([A-Z][a-zA-Z\s\.\d]+):', r'[\1]:', text)

        # --- ML TRANSFORMATIONS ---
        entities = nlp(text)
        
        for ent in sorted(entities, key=lambda x: x['start'], reverse=True):
            if ent['word'].lower() in ['anxiety', 'depression', 'therapy', 'ptsd', 'cbt', 'session']:
                continue
            text = text[:ent['start']] + f"[{ent['entity_group']}]" + text[ent['end']:]
        return text

    # 6. PIPELINE EXECUTION & DATASTREAM BACK TO WAREHOUSE
    print("🧠 Crunching text transformations via BERT...")
    df['transcript_redacted'] = df['raw_transcript_unredacted'].apply(redact_text)
    
    table_id = f"{project_id}.{dataset_id}.fact_sessions_redacted"
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND" 
    )
    
    print(f"📤 Streaming {len(df)} processed records back to BigQuery...")
    try:
        load_job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        load_job.result() 
        print(f"✅ Task {task_index} pipeline run completely successful!")
    except Exception as e:
        print(f"❌ Failed to load processed data to BigQuery: {e}")

if __name__ == "__main__":
    main()
