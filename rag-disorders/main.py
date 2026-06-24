from google.cloud import bigquery
import vertexai
import time
from tqdm import tqdm

from config import *
from extractor import SymptomExtractor


# ---------------------------------
# Initialize
# ---------------------------------

vertexai.init(
    project=PROJECT_ID,
    location=LOCATION
)

client = bigquery.Client(project=PROJECT_ID)

extractor = SymptomExtractor(MODEL_NAME)


# ---------------------------------
# Process batches until complete
# ---------------------------------

while True:

    query = f"""
    SELECT
        session_id,
        transcript_redacted
    FROM `{TABLE_ID}`
    WHERE extracted_symptoms IS NULL
       OR ARRAY_LENGTH(extracted_symptoms) = 0
    LIMIT {BATCH_SIZE}
    """

    df = client.query(query).to_dataframe()

    if len(df) == 0:
        print("No sessions remaining")
        break

    print(f"\nFound {len(df)} sessions")

    progress_query = f"""
    SELECT COUNT(*) AS remaining
    FROM `{TABLE_ID}`
    WHERE extracted_symptoms IS NULL
       OR ARRAY_LENGTH(extracted_symptoms) = 0
    """

    remaining = (
        client.query(progress_query)
        .to_dataframe()
        .iloc[0]["remaining"]
    )

    print(f"Remaining sessions: {remaining:,}")

    for i, row in enumerate(
        tqdm(
            df.iterrows(),
            total=len(df),
            desc="Processing Sessions"
        ),
        start=1
    ):

        _, row = row

        try:

            symptoms = extractor.extract(
                row["transcript_redacted"]
            )


            update_query = f"""
            UPDATE `{TABLE_ID}`
            SET extracted_symptoms = @symptoms
            WHERE session_id = @session_id
            """

            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter(
                        "session_id",
                        "STRING",
                        row["session_id"]
                    ),
                    bigquery.ArrayQueryParameter(
                        "symptoms",
                        "STRING",
                        symptoms
                    )
                ]
            )

            client.query(
                update_query,
                job_config=job_config
            ).result()

            if i % 10 == 0:

                print(
                    f"Processed {i} of {len(df)} "
                    f"in current batch"
                )

                completed_query = f"""
                SELECT COUNT(*) AS completed
                FROM `{TABLE_ID}`
                WHERE ARRAY_LENGTH(extracted_symptoms) > 0
                """

                completed = (
                    client.query(completed_query)
                    .to_dataframe()
                    .iloc[0]["completed"]
                )

                print(
                    f"Completed: {completed:,} / 11,997"
                )

            # Slow down slightly to reduce 429 errors
            time.sleep(2)

        except Exception as e:

            print(
                f"Error processing "
                f"{row['session_id']}: {e}"
            )

            time.sleep(10)

print("Finished processing all sessions")