# ==============================================================================
# STREAMLIT ANALYTICS APPLICATION
#
# Purpose:
# Provide a simple web interface for exploring synthetic patient data
# and validating transcript redaction results.
#
# Architecture:
# User -> Streamlit UI -> BigQuery -> Display Results
# ==============================================================================

# Streamlit powers the web application.
import pandas as pd
import streamlit as st

# BigQuery client used to retrieve data.
from google.cloud import bigquery


# ==============================================================================
# BIGQUERY TABLE CONFIGURATION
# ==============================================================================

# Keep project and dataset names in one place so table references are easier
# to update if the BigQuery project or dataset changes later.
PROJECT_ID = "mental-health-llm-pip"
DATASET_ID = "patient_insights"

# Fully-qualified BigQuery table names used by the Streamlit pages.
DIM_PATIENTS_TABLE = f"{PROJECT_ID}.{DATASET_ID}.dim_patients"
FACT_SESSIONS_TABLE = f"{PROJECT_ID}.{DATASET_ID}.fact_sessions"
FACT_SESSIONS_REDACTED_TABLE = f"{PROJECT_ID}.{DATASET_ID}.fact_sessions_redacted"

# The symptom extraction code has used two possible column names in different
# iterations of the project. The UI checks both so it can work with either
# BigQuery schema without requiring code changes.
SYMPTOM_COLUMN_CANDIDATES = [
    "extracted_symptoms",
    "symptoms"
]


def get_symptom_column(client):
    """Find the symptom array column currently available in BigQuery."""

    # Read the BigQuery table schema instead of assuming a fixed column name.
    # This avoids breaking the app if the table was created from an older
    # notebook that used "symptoms" instead of "extracted_symptoms".
    table = client.get_table(FACT_SESSIONS_REDACTED_TABLE)

    column_names = {
        field.name
        for field in table.schema
    }

    # Return the first supported symptom column found in the table schema.
    for column_name in SYMPTOM_COLUMN_CANDIDATES:

        if column_name in column_names:
            return column_name

    # Returning None lets the page show a helpful Streamlit error instead of
    # failing with a BigQuery "column not found" exception.
    return None


def format_symptoms(symptoms):
    """Normalize BigQuery repeated-field values into a plain Python list."""

    # BigQuery repeated fields can come back as lists or array-like objects.
    # This helper makes the display code simpler and handles empty/null values.
    if symptoms is None:
        return []

    if isinstance(symptoms, list):
        return symptoms

    try:
        if len(symptoms) == 0:
            return []
    except TypeError:
        return []

    return list(symptoms)


def get_table_columns(client, table_name):
    """Return the column names available in a BigQuery table."""

    table = client.get_table(table_name)
    return {field.name for field in table.schema}


def classify_diagnosis(diagnosis):
    """Map a DSM diagnosis string back to the synthetic profile labels."""

    if diagnosis is None:
        return "Unknown"

    diagnosis_text = str(diagnosis).lower()

    if "bipolar" in diagnosis_text or "cyclothym" in diagnosis_text:
        return "Bipolar"

    if "depress" in diagnosis_text or "dysthym" in diagnosis_text:
        return "Depressive"

    if "anxiety" in diagnosis_text or "panic" in diagnosis_text or "phobia" in diagnosis_text:
        return "Anxiety"

    return "Unknown"


# ==============================================================================
# PAGE CONFIGURATION
# ==============================================================================

# Configure browser tab title and layout.
st.set_page_config(

    # Browser tab title.
    page_title="Mental Health Analytics",

    # Use full browser width.
    layout="wide"
)


# ==============================================================================
# NAVIGATION MENU
# ==============================================================================

# Create a dropdown menu in the left sidebar.
page = st.sidebar.selectbox(

    "Navigation",

    [
        "Dashboard",
        "PHI Validation",
        "RAG Diagnosis",
        "RAG Accuracy Summary",
        "Symptom Redaction"
    ]
)


# ==============================================================================
# DASHBOARD PAGE
# ==============================================================================

if page == "Dashboard":

    # Main page title.
    st.title("Mental Health Analytics")

    # Create BigQuery connection.
    client = bigquery.Client()

    # Allow users to filter by profile type.
    profile = st.selectbox(

        "Profile",

        [
            "All",
            "Anxiety",
            "Depressive",
            "Bipolar"
        ]
    )

    # --------------------------------------------------------------------------
    # QUERY BUILDING
    # --------------------------------------------------------------------------

    # If user selects "All", return all profiles.
    if profile == "All":

        query = """
        SELECT *
        FROM `mental-health-llm-pip.patient_insights.dim_patients`
        LIMIT 20
        """

    # Otherwise filter by selected profile.
    else:

        query = f"""
        SELECT *
        FROM `mental-health-llm-pip.patient_insights.dim_patients`
        WHERE profile = '{profile}'
        LIMIT 20
        """

    # Execute query and convert results to DataFrame.
    df = client.query(query).to_dataframe()

    # --------------------------------------------------------------------------
    # SUMMARY METRIC
    # --------------------------------------------------------------------------

    # Display number of records returned.
    st.metric(

        "Patients Displayed",

        len(df)
    )

    # Display DataFrame as interactive table.
    st.dataframe(df)


# ==============================================================================
# PHI VALIDATION PAGE
# ==============================================================================

elif page == "PHI Validation":

    st.title("PHI Validation")

    # Explain purpose of page.
    st.info(
        "Review redacted transcripts and session metadata."
    )

    # Create BigQuery connection.
    client = bigquery.Client()

    # Detect which symptom extraction column exists so this page can show
    # symptoms beside the redacted transcript when available.
    symptom_column = get_symptom_column(client)

    # BigQuery query text is built differently depending on whether symptoms
    # exist in the table. If no symptom column exists yet, return an empty
    # string array so the rest of the Streamlit display code can still run.
    if symptom_column:

        symptom_select = f"r.{symptom_column} AS extracted_symptoms,"

    else:

        symptom_select = "ARRAY<STRING>[] AS extracted_symptoms,"

    # --------------------------------------------------------------------------
    # DATA QUALITY VALIDATION QUERY
    # --------------------------------------------------------------------------

    # Join three tables:
    #
    # fact_sessions_redacted
    #     ↓
    # fact_sessions
    #     ↓
    # dim_patients
    #
    # This allows us to see:
    # - Redacted transcript
    # - Extracted symptoms, if the symptom column exists
    # - Session details
    # - Patient demographics
    query = f"""
    SELECT

        r.session_id,

        r.transcript_redacted,
        {symptom_select}

        p.age,
        p.gender,
        p.profile,

        s.session_date,
        s.medication_name,
        s.dosage_mg

    FROM `{FACT_SESSIONS_REDACTED_TABLE}` r

    JOIN `{FACT_SESSIONS_TABLE}` s
        ON r.session_id = s.session_id

    JOIN `{DIM_PATIENTS_TABLE}` p
        ON s.patient_id = p.patient_id

    LIMIT 20
    """

    # Load query results into Pandas.
    df = client.query(query).to_dataframe()

    # --------------------------------------------------------------------------
    # SESSION SELECTOR
    # --------------------------------------------------------------------------

    # Let user choose a specific session.
    session_id = st.selectbox(

        "Session",

        df["session_id"]
    )

    # Retrieve selected row.
    record = df[
        df["session_id"] == session_id
    ].iloc[0]

    # --------------------------------------------------------------------------
    # SESSION METADATA
    # --------------------------------------------------------------------------

    st.subheader("Session Information")

    # Create three-column layout.
    col1, col2, col3 = st.columns(3)

    with col1:

        st.write("**Age:**", record["age"])

        st.write("**Gender:**", record["gender"])

    with col2:

        st.write("**Profile:**", record["profile"])

        st.write("**Date:**", record["session_date"])

    with col3:

        st.write("**Medication:**", record["medication_name"])

        st.write(
            "**Dosage:**",
            f"{record['dosage_mg']} mg"
        )

    # Horizontal divider.
    st.divider()

    # --------------------------------------------------------------------------
    # EXTRACTED SYMPTOMS
    # --------------------------------------------------------------------------

    st.subheader("Extracted Symptoms")

    # Normalize the repeated BigQuery field before rendering it.
    symptoms = format_symptoms(
        record["extracted_symptoms"]
    )

    # Show extracted symptoms when the symptom redaction pipeline has populated
    # them for the selected session.
    if symptoms:

        st.write(
            ", ".join(symptoms)
        )

    # If the column exists but this row is empty, the extraction job likely has
    # not processed this particular session yet.
    elif symptom_column:

        st.warning(
            "No symptoms have been extracted for this session yet."
        )

    # If no supported column exists, the BigQuery table needs to be updated by
    # the symptom extraction workflow before this section can show results.
    else:

        st.warning(
            "No symptom column was found in fact_sessions_redacted."
        )

    # Horizontal divider.
    st.divider()

    # --------------------------------------------------------------------------
    # REDACTED TRANSCRIPT VIEWER
    # --------------------------------------------------------------------------

    st.subheader("Redacted Transcript")

    # Display transcript in a large scrollable text box.
    st.text_area(

        "Transcript",

        record["transcript_redacted"],

        height=500
    )


# ==============================================================================
# RAG DIAGNOSIS PAGE
# ==============================================================================

elif page == "RAG Diagnosis":

    st.title("RAG Diagnosis")

    st.info(
        "Review the DSM diagnosis written back to the patient table by the RAG pipeline."
    )

    client = bigquery.Client()
    patient_columns = get_table_columns(client, DIM_PATIENTS_TABLE)

    if "dsm5_diagnosis" not in patient_columns:

        st.error(
            "No dsm5_diagnosis column was found in dim_patients. "
            "Run the diagnosis table update before using this page."
        )

        st.stop()

    icd_select = "icd10_code" if "icd10_code" in patient_columns else "NULL AS icd10_code"

    diagnosis_filter = st.selectbox(
        "Diagnosis rows",
        [
            "Diagnosed only",
            "All patients"
        ]
    )

    where_clause = (
        "WHERE dsm5_diagnosis IS NOT NULL"
        if diagnosis_filter == "Diagnosed only"
        else ""
    )

    query = f"""
    SELECT
        patient_id,
        age,
        gender,
        region,
        intake_date,
        profile,
        dsm5_diagnosis,
        {icd_select}
    FROM `{DIM_PATIENTS_TABLE}`
    {where_clause}
    ORDER BY patient_id
    """

    df = client.query(query).to_dataframe()

    if df.empty:

        st.warning("No diagnosis rows were found.")
        st.stop()

    diagnosed_count = df["dsm5_diagnosis"].notna().sum()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Patients Loaded", len(df))

    with col2:
        st.metric("Diagnosed", int(diagnosed_count))

    with col3:
        st.metric("Profiles", df["profile"].nunique())

    st.divider()

    patient_id = st.selectbox(
        "Patient",
        df["patient_id"]
    )

    record = df[df["patient_id"] == patient_id].iloc[0]

    st.subheader("Selected Patient")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("**Profile:**", record["profile"])
        st.write("**Age:**", record["age"])

    with col2:
        st.write("**Gender:**", record["gender"])
        st.write("**Region:**", record["region"])

    with col3:
        st.write("**Intake Date:**", record["intake_date"])
        st.write("**ICD-10:**", record["icd10_code"])

    st.subheader("RAG Diagnosis")
    st.write(record["dsm5_diagnosis"] or "No diagnosis saved yet.")

    st.divider()

    st.subheader("Diagnosis Table")

    st.dataframe(
        df,
        use_container_width=True
    )


# ==============================================================================
# RAG ACCURACY SUMMARY PAGE
# ==============================================================================

elif page == "RAG Accuracy Summary":

    st.title("RAG Accuracy Summary")

    st.info(
        "Compare the RAG diagnosis against the synthetic patient profile label."
    )

    client = bigquery.Client()
    patient_columns = get_table_columns(client, DIM_PATIENTS_TABLE)

    if "dsm5_diagnosis" not in patient_columns:

        st.error(
            "No dsm5_diagnosis column was found in dim_patients. "
            "Run the diagnosis pipeline first."
        )

        st.stop()

    query = f"""
    SELECT
        patient_id,
        profile,
        dsm5_diagnosis
    FROM `{DIM_PATIENTS_TABLE}`
    WHERE dsm5_diagnosis IS NOT NULL
    """

    df = client.query(query).to_dataframe()

    if df.empty:

        st.warning("No saved RAG diagnoses were found.")
        st.stop()

    df["rag_profile"] = df["dsm5_diagnosis"].apply(classify_diagnosis)
    df["is_correct"] = df["profile"] == df["rag_profile"]

    accuracy = df["is_correct"].mean()
    correct_count = int(df["is_correct"].sum())

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Diagnosed Patients", len(df))

    with col2:
        st.metric("Correct", correct_count)

    with col3:
        st.metric("Accuracy", f"{accuracy:.1%}")

    st.divider()

    st.subheader("Accuracy by Profile")

    profile_summary = (
        df.groupby("profile")
        .agg(
            patients=("patient_id", "count"),
            correct=("is_correct", "sum"),
            accuracy=("is_correct", "mean"),
        )
        .reset_index()
    )
    profile_summary["accuracy"] = profile_summary["accuracy"].map(lambda value: f"{value:.1%}")

    st.dataframe(
        profile_summary,
        use_container_width=True
    )

    st.subheader("Expected vs RAG Category")

    confusion = pd.crosstab(
        df["profile"],
        df["rag_profile"],
        rownames=["Expected profile"],
        colnames=["RAG category"],
    )

    st.dataframe(
        confusion,
        use_container_width=True
    )

    st.subheader("Patient-Level Results")

    st.dataframe(
        df[
            [
                "patient_id",
                "profile",
                "dsm5_diagnosis",
                "rag_profile",
                "is_correct",
            ]
        ],
        use_container_width=True,
    )


# ==============================================================================
# SYMPTOM REDACTION PAGE
# ==============================================================================

elif page == "Symptom Redaction":

    st.title("Symptom Redaction")

    # Explain purpose of page.
    st.info(
        "Review symptoms extracted from PHI-redacted transcripts."
    )

    # Create BigQuery connection.
    client = bigquery.Client()

    # Detect whether the current BigQuery table stores extracted symptoms in
    # "extracted_symptoms" or "symptoms".
    symptom_column = get_symptom_column(client)

    # Stop early with a readable UI message if the symptom extraction schema is
    # not present yet. This is better than allowing the query to fail.
    if symptom_column is None:

        st.error(
            "No symptom column was found in fact_sessions_redacted. "
            "Expected either extracted_symptoms or symptoms."
        )

        st.stop()

    # Let the user choose how many symptom-redaction rows to load from BigQuery.
    # "All" is useful for complete review, but smaller limits keep the app more
    # responsive while exploring.
    row_limit = st.selectbox(

        "Rows to load",

        [
            "50",
            "100",
            "500",
            "1000",
            "All"
        ]
    )

    # BigQuery only needs a LIMIT clause when the user chooses a fixed row count.
    # Leaving this blank for "All" returns every row that has extracted symptoms.
    limit_clause = (
        ""
        if row_limit == "All"
        else f"LIMIT {row_limit}"
    )

    # --------------------------------------------------------------------------
    # SYMPTOM REDACTION QUERY
    # --------------------------------------------------------------------------

    # Join the redacted transcript table back to session and patient metadata so
    # each symptom list can be reviewed with the surrounding clinical context.
    #
    # The WHERE clause only returns rows where symptom extraction has produced
    # at least one symptom, which keeps the review screen focused on completed
    # symptom-redaction results.
    query = f"""
    SELECT

        r.session_id,
        r.transcript_redacted,
        r.{symptom_column} AS extracted_symptoms,

        p.age,
        p.gender,
        p.profile,

        s.session_date,
        s.medication_name,
        s.dosage_mg

    FROM `{FACT_SESSIONS_REDACTED_TABLE}` r

    JOIN `{FACT_SESSIONS_TABLE}` s
        ON r.session_id = s.session_id

    JOIN `{DIM_PATIENTS_TABLE}` p
        ON s.patient_id = p.patient_id

    WHERE ARRAY_LENGTH(r.{symptom_column}) > 0

    ORDER BY s.session_date DESC

    {limit_clause}
    """

    # Load query results into Pandas.
    df = client.query(query).to_dataframe()

    # If the table exists but the extraction job has not populated any rows yet,
    # show a clear empty state instead of an empty selector.
    if df.empty:

        st.warning(
            "No sessions with extracted symptoms were found."
        )

        st.stop()

    # Create a display-friendly string version of the repeated symptom field for
    # the summary table at the bottom of the page.
    df["symptoms_display"] = df["extracted_symptoms"].apply(
        lambda symptoms: ", ".join(format_symptoms(symptoms))
    )

    # --------------------------------------------------------------------------
    # SUMMARY METRICS
    # --------------------------------------------------------------------------

    # The metrics give a quick sanity check that the query is reading symptom
    # extraction output and which table column is being used.
    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Sessions Displayed",
            len(df)
        )

    with col2:

        st.metric(
            "Symptom Field",
            symptom_column
        )

    with col3:

        st.metric(
            "Unique Profiles",
            df["profile"].nunique()
        )

    # Horizontal divider.
    st.divider()

    # --------------------------------------------------------------------------
    # SESSION SELECTOR
    # --------------------------------------------------------------------------

    # Let the user choose a specific session to inspect in detail.
    session_id = st.selectbox(

        "Session",

        df["session_id"]
    )

    # Retrieve selected row.
    record = df[
        df["session_id"] == session_id
    ].iloc[0]

    # --------------------------------------------------------------------------
    # SESSION METADATA
    # --------------------------------------------------------------------------

    st.subheader("Session Information")

    # Create three-column layout.
    col1, col2, col3 = st.columns(3)

    with col1:

        st.write("**Age:**", record["age"])

        st.write("**Gender:**", record["gender"])

    with col2:

        st.write("**Profile:**", record["profile"])

        st.write("**Date:**", record["session_date"])

    with col3:

        st.write("**Medication:**", record["medication_name"])

        st.write(
            "**Dosage:**",
            f"{record['dosage_mg']} mg"
        )

    # Horizontal divider.
    st.divider()

    # --------------------------------------------------------------------------
    # SYMPTOM VIEWER
    # --------------------------------------------------------------------------

    st.subheader("Extracted Symptoms")

    # Normalize the repeated BigQuery field before rendering it as bullets.
    symptoms = format_symptoms(
        record["extracted_symptoms"]
    )

    # Display each extracted symptom on its own line for easier review.
    for symptom in symptoms:

        st.markdown(
            f"- {symptom}"
        )

    # Horizontal divider.
    st.divider()

    # --------------------------------------------------------------------------
    # TABLE VIEW
    # --------------------------------------------------------------------------

    st.subheader("Recent Symptom Redaction Results")

    # Show a compact table of the latest sessions with populated symptoms.
    st.dataframe(

        df[
            [
                "session_id",
                "profile",
                "session_date",
                "symptoms_display"
            ]
        ],

        use_container_width=True
    )

    # Horizontal divider.
    st.divider()

    # --------------------------------------------------------------------------
    # REDACTED TRANSCRIPT VIEWER
    # --------------------------------------------------------------------------

    st.subheader("Redacted Transcript")

    # Display the PHI-redacted transcript used as input to symptom extraction.
    st.text_area(

        "Transcript",

        record["transcript_redacted"],

        height=500
    )
