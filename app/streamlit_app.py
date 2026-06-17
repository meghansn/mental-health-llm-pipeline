import streamlit as st
from google.cloud import bigquery

st.set_page_config(
    page_title="Mental Health Analytics",
    layout="wide"
)

page = st.sidebar.selectbox(
    "Navigation",
    [
        "Dashboard",
        "PHI Validation"
    ]
)

if page == "Dashboard":

    st.title("Mental Health Analytics")

    client = bigquery.Client()

    profile = st.selectbox(
        "Profile",
        ["All", "Anxiety", "Depressive", "Bipolar"]
    )

    if profile == "All":

        query = """
        SELECT *
        FROM `mental-health-llm-pip.patient_insights.dim_patients`
        LIMIT 20
        """

    else:

        query = f"""
        SELECT *
        FROM `mental-health-llm-pip.patient_insights.dim_patients`
        WHERE profile = '{profile}'
        LIMIT 20
        """

    df = client.query(query).to_dataframe()

    st.metric(
        "Patients Displayed",
        len(df)
    )

    st.dataframe(df)
elif page == "PHI Validation":

    st.title("PHI Validation")

    st.info(
        "Review redacted transcripts and session metadata."
    )

    client = bigquery.Client()

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

    df = client.query(query).to_dataframe()

    session_id = st.selectbox(
        "Session",
        df["session_id"]
    )

    record = df[df["session_id"] == session_id].iloc[0]

    st.subheader("Session Information")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("**Age:**", record["age"])
        st.write("**Gender:**", record["gender"])

    with col2:
        st.write("**Profile:**", record["profile"])
        st.write("**Date:**", record["session_date"])

    with col3:
        st.write("**Medication:**", record["medication_name"])
        st.write("**Dosage:**", f"{record['dosage_mg']} mg")

    st.divider()

    st.subheader("Redacted Transcript")

    st.text_area(
        "Transcript",
        record["transcript_redacted"],
        height=500
    )