"""Streamlit interface for the LLM-powered software engineering assistant."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Allow running with: streamlit run app/streamlit_app.py
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from app.assistant_core import (
    generate_requirements,
    generate_test_cases,
    review_requirements,
    suggest_architecture,
)
from app.corpus import corpus_status, retrieve_context

st.set_page_config(page_title="LLM SE Assistant", page_icon="🤖", layout="wide")

st.title("LLM-Powered Virtual Assistant for Software Engineering")
st.caption("Human-machine cooperation prototype for requirements, review, tests, and architecture.")

provider = os.getenv("LLM_PROVIDER", "mock")
status = corpus_status()

with st.sidebar:
    st.header("Runtime settings")
    st.info(f"LLM provider: `{provider}`")
    use_context = st.checkbox(
        "Use local dataset context",
        value=False,
        help="Uses the processed local corpus created from downloaded online datasets. This is optional and reproducible.",
    )
    st.metric("Local corpus documents", status["documents"])
    if not status["available"]:
        st.warning("No processed corpus found. Run the data download and preparation scripts first, or use mock mode without context.")
    st.code("python data_sources/download_datasets.py\npython data_sources/prepare_benchmark.py", language="bash")

example_description = """Build a web application that helps students plan study schedules. Users can enter courses, deadlines, available study hours, and preferred study times. The system suggests a weekly study plan and lets the student revise it."""

project_description = st.text_area(
    "Project description",
    value=example_description,
    height=150,
    help="Describe the software system that the assistant should analyze.",
)

if use_context:
    with st.expander("Preview retrieved local context"):
        context_preview = retrieve_context(project_description, top_k=2, max_chars=1600)
        st.text(context_preview or "No context available yet.")

if "requirements_json" not in st.session_state:
    st.session_state.requirements_json = None
if "requirements_text" not in st.session_state:
    st.session_state.requirements_text = ""

tab1, tab2, tab3, tab4 = st.tabs([
    "1. Generate requirements",
    "2. Review requirements",
    "3. Generate test cases",
    "4. Suggest architecture",
])

with tab1:
    if st.button("Generate requirements", type="primary"):
        with st.spinner("Generating requirements..."):
            result = generate_requirements(project_description, use_context=use_context)
            st.session_state.requirements_json = result
            st.session_state.requirements_text = json.dumps(result, indent=2)
    if st.session_state.requirements_json:
        st.json(st.session_state.requirements_json)

with tab2:
    requirements_text = st.text_area(
        "Requirements to review",
        value=st.session_state.requirements_text,
        height=300,
        key="review_requirements_text",
    )
    if st.button("Review requirements"):
        with st.spinner("Reviewing requirements..."):
            st.json(review_requirements(requirements_text, use_context=use_context))

with tab3:
    test_requirements_text = st.text_area(
        "Requirements for test generation",
        value=st.session_state.requirements_text,
        height=300,
        key="test_requirements_text",
    )
    if st.button("Generate test cases"):
        with st.spinner("Generating test cases..."):
            st.json(generate_test_cases(test_requirements_text, use_context=use_context))

with tab4:
    arch_requirements_text = st.text_area(
        "Requirements for architecture suggestion",
        value=st.session_state.requirements_text,
        height=300,
        key="arch_requirements_text",
    )
    if st.button("Suggest architecture"):
        with st.spinner("Suggesting architecture..."):
            st.json(suggest_architecture(project_description, arch_requirements_text, use_context=use_context))
