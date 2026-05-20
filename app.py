import streamlit as st
import fitz
import ollama
import json
import os
import base64

st.set_page_config(layout="wide")

st.title("AI Legal - Warrant Form Auto Fill")

# ----------------------------------------
# Upload PDF
# ----------------------------------------

top_col1, top_col2 = st.columns([3, 1])

with top_col1:
    uploaded_file = st.file_uploader(
        "Upload Judgment PDF",
        type=["pdf"]
    )

with top_col2:
    st.write("")
    st.write("")
    if st.button("Process Demo Data", use_container_width=True):
        st.session_state.data = {
            "prisoner_name": "Sarjug Rai",
            "case_number": "123/1957",
            "conviction_date": "28 October 1957",
            "judge_name": "Justice ABC",
            "offence": "Murder",
            "section": "302 IPC",
            "sentence": "Life Imprisonment",
            "jail_name": "Patna Central Jail"
        }
        st.session_state.demo_mode = True

if uploaded_file or st.session_state.get("demo_mode"):

    os.makedirs("temp", exist_ok=True)

    if uploaded_file:
        input_path = f"temp/{uploaded_file.name}"

        with open(input_path, "wb") as f:
            f.write(uploaded_file.read())

        # ----------------------------------------
        # Extract Judgment Text
        # ----------------------------------------

        doc = fitz.open(input_path)

        text = ""

        for page in doc:
            text += page.get_text()

        # ----------------------------------------
        # AI Extraction
        # ----------------------------------------

        if "data" not in st.session_state or st.session_state.get("last_uploaded") != uploaded_file.name:

            with st.spinner("Extracting details..."):

                prompt = f"""
                Extract the following details.

                Return ONLY valid JSON.

                Fields:
                - prisoner_name
                - case_number
                - conviction_date
                - judge_name
                - offence
                - section
                - sentence
                - jail_name

                Judgment:
                {text[:12000]}
                """

                response = ollama.chat(
                    model='qwen3:8b',
                    messages=[
                        {
                            'role': 'user',
                            'content': prompt
                        }
                    ]
                )

                raw = response['message']['content']

                raw = raw.replace("```json", "")
                raw = raw.replace("```", "")
                raw = raw.strip()

                st.session_state.data = json.loads(raw)
                st.session_state.last_uploaded = uploaded_file.name

    data = st.session_state.data

    # ----------------------------------------
    # Two Column Layout
    # ----------------------------------------

    left, right = st.columns([1, 1])

    # ========================================
    # LEFT SIDE → Editable Fields
    # ========================================

    with left:

        st.header("Edit Fields")

        data["jail_name"] = st.text_input(
            "Jail Name",
            data.get("jail_name", "")
        )

        data["conviction_date"] = st.text_input(
            "Conviction Date",
            data.get("conviction_date", "")
        )

        data["prisoner_name"] = st.text_input(
            "Prisoner Name",
            data.get("prisoner_name", "")
        )

        data["case_number"] = st.text_input(
            "Case Number",
            data.get("case_number", "")
        )

        data["judge_name"] = st.text_input(
            "Judge Name",
            data.get("judge_name", "")
        )

        data["offence"] = st.text_area(
            "Offence",
            data.get("offence", "")
        )

        data["section"] = st.text_input(
            "Section",
            data.get("section", "")
        )

        data["sentence"] = st.text_area(
            "Sentence",
            data.get("sentence", "")
        )

    # ========================================
    # GENERATE LIVE PDF
    # ========================================

    form_doc = fitz.open("form35.pdf")

    page = form_doc[0]

    page.insert_text((250, 155), data["jail_name"], fontsize=8)

    page.insert_text((220, 172), data["conviction_date"], fontsize=8)

    page.insert_text((360, 172), data["prisoner_name"], fontsize=8)

    page.insert_text((240, 198), data["case_number"], fontsize=8)

    page.insert_text((240, 210), data["judge_name"], fontsize=8)

    page.insert_text((180, 222), data["offence"], fontsize=8)

    page.insert_text((190, 234), data["section"], fontsize=8)

    page.insert_text((360, 245), data["sentence"], fontsize=8)

    output_pdf = "temp/live_preview.pdf"

    form_doc.save(output_pdf)

    # ========================================
    # RIGHT SIDE → LIVE PDF
    # ========================================

    with right:

        st.header("Preview")

        with open(output_pdf, "rb") as pdf_file:
            base64_pdf = base64.b64encode(
                pdf_file.read()
            ).decode('utf-8')

        pdf_display = f"""
        <iframe
            src="data:application/pdf;base64,{base64_pdf}"
            width="100%"
            height="900"
            type="application/pdf">
        </iframe>
        """

        st.markdown(pdf_display, unsafe_allow_html=True)

        # Download Button

        with open(output_pdf, "rb") as pdf_file:
            st.download_button(
                "Download PDF",
                pdf_file,
                file_name="filled_form35.pdf",
                mime="application/pdf"
            )