# Data Dictionary: Mental Health Synthetic Dataset

## 1. Table: `dim_patients`
| Column | Data Type | Description |
| :--- | :--- | :--- |
| `patient_id` | STRING | Unique UUID assigned to each patient. |
| `age` | INT64 | Patient age (18–75). |
| `gender` | STRING | Gender identity. |
| `region` | STRING | GTA location. |
| `intake_date` | DATE | Onboarding date. |
| `profile` | STRING | Clinical category (Depressive, Anxiety, or Bipolar). |

## 2. Table: `fact_sessions`
| Column | Data Type | Description |
| :--- | :--- | :--- |
| `session_id` | STRING | Unique UUID for the session. |
| `patient_id` | STRING | Foreign key to `dim_patients`. |
| `session_date` | DATE | Date of session. |
| `raw_transcript_unredacted` | STRING | 50+ line therapy dialogue. |
| `medication_name` | STRING | Name of medication. |
| `medication_rxnorm_code` | STRING | Standard RxNorm code. |
| `dosage_mg` | INT64 | Dosage in milligrams. |

fact_sessions_redacted

Stores original and de-identified versions of session transcripts to support PHI redaction validation and downstream analytics.

Column	Type	Description
session_id	STRING	Unique identifier for each session
raw_transcript_unredacted	STRING	Original transcript prior to PHI redaction
transcript_redacted	STRING	Transcript after PHI redaction and de-identification
