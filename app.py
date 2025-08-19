import streamlit as st
import os
import requests
import base64
import json
import re

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("GEMINI_API_KEY not found in environment variables. Please set it.")
    st.stop()

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

def encode_image(image_file):
    return base64.b64encode(image_file.read()).decode("utf-8")

def clean_json_string(text):
    text = re.sub(r'```json\s*|\s*```', '', text, flags=re.MULTILINE)
    text = text.strip().replace("'", '"')
    match = re.search(r'\{[\s\S]*\}', text)
    return match.group(0) if match else text

st.title("Business Card Scanner")
st.write("Upload multiple business card images to extract name, company, and phone number.")

uploaded_files = st.file_uploader("Choose business card images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    results = []
    contents = []
    for file in uploaded_files:
        image_data = encode_image(file)
        contents.append({
            "parts": [
                {"inlineData": {"mimeType": f"image/{file.type.split('/')[-1]}", "data": image_data}},
                {"text": """Extract the name, company, and phone number from this business card. 
                            Return only valid JSON like {'name': str, 'company': str, 'phone': str}, 
                            using 'N/A' for missing fields. Do not include markdown, code blocks, or extra text."""}
            ]
        })

    headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}
    payload = {"contents": contents}
    response = requests.post(API_URL, headers=headers, json=payload).json()

    for idx, candidate in enumerate(response.get("candidates", [])):
        content = candidate.get("content", {}).get("parts", [{}])[0].get("text", "{}")
        cleaned_content = clean_json_string(content)
        extracted_data = json.loads(cleaned_content)
        results.append(
            f"**Image {idx + 1}:** "
            f"**Name:** {extracted_data.get('name', 'N/A')}, "
            f"**Company:** {extracted_data.get('company', 'N/A')}, "
            f"**Phone:** {extracted_data.get('phone', 'N/A')}"
        )

    st.subheader("Extracted Details")
    for result in results:
        st.markdown(result)

    output_text = "\n".join([re.sub(r'\*\*([^*]+)\*\*', r'\1', line) for line in results])
    st.download_button("Download Results", output_text, "business_card_data.txt", "text/plain")
else:
    st.info("Please upload one or more business card images to start the OCR process.")
