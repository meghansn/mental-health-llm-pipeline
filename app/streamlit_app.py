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
import streamlit as st

# BigQuery client used to retrieve data.
from google.cloud import bigquery


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
        "PHI Validation"
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
    # - Session details
    # - Patient demographics
    query = """
    SELECT

        r.session_id,

        r.transcript_redacted,

        p.age,
        p.gender,
        p.profile,

        s.session_date,
        s.medication_name,
        s.dosage_mg

    FROM `mental-health-llm-pip.patient_insights.fact_sessions_redacted` r

    JOIN `mental-health-llm-pip.patient_insights.fact_sessions` s
        ON r.session_id = s.session_id

    JOIN `mental-health-llm-pip.patient_insights.dim_patients` p
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
    # REDACTED TRANSCRIPT VIEWER
    # --------------------------------------------------------------------------

    st.subheader("Redacted Transcript")

    # Display transcript in a large scrollable text box.
    st.text_area(

        "Transcript",

        record["transcript_redacted"],

        height=500
    )
