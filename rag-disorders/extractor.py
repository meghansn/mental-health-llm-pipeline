import json
import time

from vertexai.generative_models import GenerativeModel


class SymptomExtractor:

    def __init__(self, model_name):
        self.model = GenerativeModel(model_name)

    def extract(self, transcript):

        prompt = f"""
Extract clinically relevant mental health symptoms from the therapy transcript.

Requirements:
- Return ONLY a JSON array
- Use concise symptom names
- Do not return diagnoses
- Do not return explanations
- Do not return markdown

Example:
["insomnia","fatigue","hopelessness"]

Transcript:
{transcript}
"""

        for attempt in range(5):

            try:

                response = self.model.generate_content(
                    prompt
                )

                cleaned = (
                    response.text
                    .replace("```json", "")
                    .replace("```", "")
                    .strip()
                )

                return json.loads(cleaned)

            except Exception as e:

                print(
                    f"Retry {attempt + 1}/5: {e}"
                )

                time.sleep(15)

        return []