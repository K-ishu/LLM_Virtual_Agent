"""Professional Streamlit UI for the LLM-Powered Software Engineering Assistant.

Drop-in replacement for: app/streamlit_app.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from app.assistant_core import (
    analyze_code,
    generate_attack_scenarios,
    generate_requirements,
    generate_test_cases,
    review_requirements,
    suggest_architecture,
)
from app.llm_client import LLMClient


st.set_page_config(
    page_title="LLM SE Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 3rem;
    max-width: 1280px;
}
section[data-testid="stSidebar"] {
    background: #0b1220;
    border-right: 1px solid #1f2937;
}
.hero-card {
    background: linear-gradient(135deg, #111827 0%, #1f2937 62%, #374151 100%);
    color: white;
    border-radius: 22px;
    padding: 28px 32px;
    margin-bottom: 22px;
    box-shadow: 0 10px 30px rgba(17, 24, 39, 0.18);
}
.hero-title {
    font-size: 2.15rem;
    font-weight: 850;
    letter-spacing: -0.03em;
    margin: 0 0 8px 0;
}
.hero-subtitle {
    color: #d1d5db;
    font-size: 1rem;
    line-height: 1.55;
    max-width: 920px;
}
.card {
    background: #121826;
    border: 1px solid #283447;
    border-radius: 18px;
    padding: 18px 20px;
    margin-bottom: 16px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.22);
}
.compact-card {
    background: #0e1523;
    border: 1px solid #283447;
    border-radius: 14px;
    padding: 14px 16px;
    margin-bottom: 12px;
}
.section-title {
    font-size: 1.08rem;
    font-weight: 750;
    color: #f8fafc;
    margin-bottom: 10px;
}
.muted {
    color: #94a3b8;
    font-size: 0.92rem;
}
.badge {
    display: inline-block;
    padding: 5px 11px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 700;
    background: #eef2ff;
    color: #3730a3;
    margin-right: 7px;
    margin-bottom: 7px;
}
.badge-green { background: #dcfce7; color: #166534; }
.badge-yellow { background: #fef3c7; color: #92400e; }
.badge-red { background: #fee2e2; color: #991b1b; }
.badge-gray { background: #f3f4f6; color: #374151; }
.req-card { border-left: 5px solid #ef4444; }
.nfr-card { border-left: 5px solid #2563eb; }
.issue-high { border-left: 5px solid #dc2626; }
.issue-medium { border-left: 5px solid #f59e0b; }
.issue-low { border-left: 5px solid #2563eb; }
.workflow-step {
    padding: 14px 16px;
    border-radius: 16px;
    border: 1px solid #283447;
    background: #121826;
    min-height: 106px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.18);
}
.workflow-number {
    width: 28px;
    height: 28px;
    border-radius: 999px;
    background: #ef4444;
    color: white;
    font-weight: 800;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-right: 8px;
}
.footer-meta {
    border-top: 1px solid #e5e7eb;
    margin-top: 12px;
    padding-top: 10px;
    color: #6b7280;
    font-size: 0.85rem;
}

.info-box {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 14px;
    padding: 14px 16px;
    margin: 12px 0 16px 0;
    color: #cbd5e1;
}
.good-box {
    background: #052e1a;
    border: 1px solid #166534;
    color: #bbf7d0;
    border-radius: 12px;
    padding: 10px 14px;
    display: inline-block;
}
.warn-box {
    background: #422006;
    border: 1px solid #92400e;
    color: #fde68a;
    border-radius: 12px;
    padding: 10px 14px;
    display: inline-block;
}
.stTextArea textarea {
    background-color: #0f172a !important;
    color: #f8fafc !important;
    border: 1px solid #334155 !important;
    border-radius: 14px !important;
}
p, li, label { color: #e5e7eb; }
</style>
""",
    unsafe_allow_html=True,
)


EXAMPLE_PROJECT = (
    "Build a clinic appointment booking system for patients, doctors, and clinic administrators. "
    "Patients can create an account, search doctors by specialty, book appointments, cancel or reschedule appointments, "
    "receive email reminders, and view their appointment history. Doctors can define weekly availability slots, "
    "approve or reject appointment requests, and view their upcoming schedule. Clinic administrators can manage doctor profiles, "
    "specialties, and appointment policies. The system stores patient personal data, doctor availability, appointment records, "
    "reminder preferences, and audit logs. The system must enforce role-based access control, prevent unauthorized access to records, "
    "encrypt sensitive data, and keep an audit trail of booking changes."
)

EXAMPLE_CODE = """def login(username, password):
    if username == "admin" and password == "admin":
        return True
    return False
"""


def safe_json(data: Any) -> str:
    try:
        return json.dumps(data, indent=2, ensure_ascii=False)
    except TypeError:
        return str(data)

def escape_text(value) -> str:
    """Escape text before rendering it inside custom HTML."""
    import html
    return html.escape(str(value or ""))
def is_short_or_generic(text: str) -> bool:
    cleaned = (text or "").strip().lower()
    generic = {"hi", "hello", "test", "ok", "yes", "no", "ciao", "salam", "سلام"}
    words = [w for w in cleaned.replace("\n", " ").split(" ") if w.strip()]
    return cleaned in generic or len(words) < 8
def input_quality_label(text: str) -> tuple[str, str]:
    """Return a professional input-quality label for the project brief."""
    words = len((text or "").split())

    if words < 8:
        return "Needs more detail", "warn"

    if words < 35:
        return "Usable project brief", "good"

    return "Detailed project brief", "good"

def get_client() -> LLMClient:
    return LLMClient()


def general_ai_response(user_message: str) -> dict[str, Any]:
    """General-purpose assistant for non-workflow questions."""
    system_prompt = """
You are a helpful AI assistant inside a Software Engineering Assistant app.
Answer clearly and directly.
If the user asks about software engineering, provide practical engineering guidance.
If the user asks something general, answer normally.
Do not return JSON. Return readable plain text.
"""
    client = LLMClient()
    response = client.chat(system_prompt, user_message)
    return {
        "answer": response.text,
        "metadata": {
            "provider": response.provider,
            "model": response.model,
            "task": "general_ai_chat",
            "used_local_context": False,
        },
    }


def show_metadata(data: dict[str, Any]) -> None:
    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        return
    st.markdown(
        f"""
<div class="footer-meta">
    <span class="badge badge-gray">Provider: {metadata.get('provider', 'unknown')}</span>
    <span class="badge badge-gray">Model: {metadata.get('model', 'unknown')}</span>
    <span class="badge badge-gray">Task: {metadata.get('task', 'unknown')}</span>
    <span class="badge badge-gray">Local context: {metadata.get('used_local_context', False)}</span>
</div>
""",
        unsafe_allow_html=True,
    )


def render_list(title: str, items: list[Any], icon: str = "•") -> None:
    if not items:
        return
    st.markdown(f'<div class="card"><div class="section-title">{title}</div>', unsafe_allow_html=True)
    for item in items:
        st.markdown(f"{icon} {item}")
    st.markdown("</div>", unsafe_allow_html=True)


def render_requirements(data: dict[str, Any]) -> None:
    render_list("Assumptions", data.get("assumptions", []), "•")
    render_list("Clarification Questions", data.get("clarification_questions", []), "❓")

    frs = data.get("functional_requirements", [])
    if frs:
        st.markdown('<div class="card"><div class="section-title">Functional Requirements</div>', unsafe_allow_html=True)
        for req in frs:
            st.markdown(
                f"""
<div class="compact-card req-card">
    <span class="badge badge-red">{req.get('id', 'FR')}</span>
    <strong>{req.get('requirement', '')}</strong>
    <div class="muted" style="margin-top:7px;">Rationale: {req.get('rationale', '')}</div>
</div>
""",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    nfrs = data.get("non_functional_requirements", [])
    if nfrs:
        st.markdown('<div class="card"><div class="section-title">Non-Functional Requirements</div>', unsafe_allow_html=True)
        for req in nfrs:
            st.markdown(
                f"""
<div class="compact-card nfr-card">
    <span class="badge">{req.get('id', 'NFR')}</span>
    <span class="badge badge-green">{req.get('quality_attribute', 'quality')}</span>
    <strong>{req.get('requirement', '')}</strong>
    <div class="muted" style="margin-top:7px;">Rationale: {req.get('rationale', '')}</div>
</div>
""",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    render_list("Risks", data.get("risks", []), "⚠️")
    show_metadata(data)


def render_review(data: dict[str, Any]) -> None:
    if data.get("summary"):
        st.markdown(
            f'<div class="card"><div class="section-title">Review Summary</div><p>{data.get("summary")}</p></div>',
            unsafe_allow_html=True,
        )

    issues = data.get("issues", [])
    if issues:
        st.markdown('<div class="card"><div class="section-title">Detected Issues</div>', unsafe_allow_html=True)
        for issue in issues:
            severity = str(issue.get("severity", "medium")).lower()
            cls = "issue-high" if severity == "high" else "issue-low" if severity == "low" else "issue-medium"
            st.markdown(
                f"""
<div class="compact-card {cls}">
    <span class="badge badge-yellow">{issue.get('severity', 'medium')}</span>
    <span class="badge badge-gray">{issue.get('type', 'issue')}</span>
    <strong>{issue.get('id', 'ISSUE')}</strong>
    <p><strong>Evidence:</strong> {issue.get('evidence', '')}</p>
    <p><strong>Recommendation:</strong> {issue.get('recommendation', '')}</p>
</div>
""",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    render_list("Improved Requirements", data.get("improved_requirements", []), "✅")
    render_list("Clarification Questions", data.get("clarification_questions", []), "❓")
    show_metadata(data)


def render_test_cases(data: dict[str, Any]) -> None:
    test_cases = data.get("test_cases", [])
    if test_cases:
        st.markdown('<div class="card"><div class="section-title">Generated Test Cases</div>', unsafe_allow_html=True)
        for tc in test_cases:
            related = ", ".join(tc.get("related_requirement_ids", []))
            preconditions = "; ".join(tc.get("preconditions", []))
            st.markdown(
                f"""
<div class="compact-card">
    <span class="badge badge-red">{tc.get('id', 'TC')}</span>
    <span class="badge">{tc.get('priority', 'medium')} priority</span>
    <span class="badge badge-green">{tc.get('test_type', 'functional')}</span>
    <h4 style="margin: 8px 0 6px 0;">{tc.get('title', 'Test case')}</h4>
    <p><strong>Related requirements:</strong> {related}</p>
    <p><strong>Preconditions:</strong> {preconditions}</p>
</div>
""",
                unsafe_allow_html=True,
            )
            st.markdown("**Steps**")
            for step in tc.get("steps", []):
                st.markdown(f"- {step}")
            st.markdown(f"**Expected result:** {tc.get('expected_result', '')}")
            st.markdown("---")
        st.markdown("</div>", unsafe_allow_html=True)

    render_list("Coverage Notes", data.get("coverage_notes", []), "📌")
    render_list("Missing Information", data.get("missing_information", []), "⚠️")
    show_metadata(data)


def render_architecture(data: dict[str, Any]) -> None:
    if data.get("architecture_style"):
        st.markdown(
            f'<div class="card"><div class="section-title">Architecture Style</div><p>{data.get("architecture_style")}</p></div>',
            unsafe_allow_html=True,
        )

    components = data.get("components", [])
    if components:
        st.markdown('<div class="card"><div class="section-title">System Components</div>', unsafe_allow_html=True)
        for comp in components:
            inputs = ", ".join(comp.get("inputs", []))
            outputs = ", ".join(comp.get("outputs", []))
            st.markdown(
                f"""
<div class="compact-card">
    <span class="badge badge-red">{comp.get('name', 'Component')}</span>
    <p><strong>Responsibility:</strong> {comp.get('responsibility', '')}</p>
    <p><strong>Inputs:</strong> {inputs}</p>
    <p><strong>Outputs:</strong> {outputs}</p>
</div>
""",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    render_list("Data Flow", data.get("data_flow", []), "➡️")
    render_list("Technology Stack", data.get("technology_stack", []), "🧩")
    if data.get("deployment_view"):
        st.markdown(
            f'<div class="card"><div class="section-title">Deployment View</div><p>{data.get("deployment_view")}</p></div>',
            unsafe_allow_html=True,
        )
    render_list("Security and Privacy Considerations", data.get("security_privacy_considerations", []), "🔐")
    render_list("Human-in-the-loop Points", data.get("human_in_the_loop_points", []), "👤")
    show_metadata(data)


def render_code_analysis(data: dict[str, Any]) -> None:
    if data.get("summary"):
        st.markdown(
            f'<div class="card"><div class="section-title">Code Review Summary</div><p>{data.get("summary")}</p></div>',
            unsafe_allow_html=True,
        )
    render_list("Assumptions", data.get("assumptions", []), "•")
    if data.get("detected_language"):
        st.markdown(f'<span class="badge badge-gray">Detected language: {data.get("detected_language")}</span>', unsafe_allow_html=True)

    findings = data.get("quality_findings", [])
    if findings:
        st.markdown('<div class="card"><div class="section-title">Quality and Security Findings</div>', unsafe_allow_html=True)
        for finding in findings:
            severity = str(finding.get("severity", "medium")).lower()
            cls = "issue-high" if severity == "high" else "issue-low" if severity == "low" else "issue-medium"
            st.markdown(
                f"""
<div class="compact-card {cls}">
    <span class="badge badge-yellow">{finding.get('severity', 'medium')}</span>
    <span class="badge badge-gray">{finding.get('category', 'quality')}</span>
    <strong>{finding.get('id', 'QF')}</strong>
    <p><strong>Evidence:</strong> {finding.get('evidence', '')}</p>
    <p><strong>Recommendation:</strong> {finding.get('recommendation', '')}</p>
</div>
""",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    render_list("Refactoring Suggestions", data.get("refactoring_suggestions", []), "🛠️")
    render_list("Safe Test Ideas", data.get("safe_test_ideas", []), "🧪")
    show_metadata(data)


def render_attack_scenarios(data: dict[str, Any]) -> None:
    render_list("Threat Model Assumptions", data.get("threat_model_assumptions", []), "•")

    attacks = data.get("attack_scenarios", [])
    if attacks:
        st.markdown('<div class="card"><div class="section-title">Defensive Attack Scenarios</div>', unsafe_allow_html=True)
        for attack in attacks:
            st.markdown(
                f"""
<div class="compact-card issue-high">
    <span class="badge badge-red">{attack.get('id', 'AS')}</span>
    <span class="badge badge-yellow">Impact: {attack.get('impact', 'medium')}</span>
    <span class="badge">Likelihood: {attack.get('likelihood', 'medium')}</span>
    <h4 style="margin: 8px 0 6px 0;">{attack.get('title', '')}</h4>
    <p><strong>Asset at risk:</strong> {attack.get('asset_at_risk', '')}</p>
    <p><strong>Threat actor:</strong> {attack.get('threat_actor', '')}</p>
    <p><strong>Scenario:</strong> {attack.get('scenario', '')}</p>
</div>
""",
                unsafe_allow_html=True,
            )
            st.markdown("**Mitigations**")
            for mitigation in attack.get("mitigations", []):
                st.markdown(f"- {mitigation}")
            st.markdown("**Validation tests**")
            for test in attack.get("validation_tests", []):
                st.markdown(f"- {test}")
            st.markdown("---")
        st.markdown("</div>", unsafe_allow_html=True)

    unsafe = data.get("unsafe_scenarios", [])
    if unsafe:
        st.markdown('<div class="card"><div class="section-title">Unsafe Scenarios</div>', unsafe_allow_html=True)
        for item in unsafe:
            affected = ", ".join(item.get("affected_users", []))
            st.markdown(
                f"""
<div class="compact-card issue-medium">
    <span class="badge badge-yellow">{item.get('id', 'US')}</span>
    <h4 style="margin: 8px 0 6px 0;">{item.get('title', '')}</h4>
    <p><strong>Scenario:</strong> {item.get('scenario', '')}</p>
    <p><strong>Affected users:</strong> {affected}</p>
    <p><strong>Harm:</strong> {item.get('harm', '')}</p>
</div>
""",
                unsafe_allow_html=True,
            )
            st.markdown("**Mitigations**")
            for mitigation in item.get("mitigations", []):
                st.markdown(f"- {mitigation}")
            st.markdown("**Validation tests**")
            for test in item.get("validation_tests", []):
                st.markdown(f"- {test}")
            st.markdown("---")
        st.markdown("</div>", unsafe_allow_html=True)

    render_list("Residual Risks", data.get("residual_risks", []), "⚠️")
    show_metadata(data)


def render_raw_toggle(data: dict[str, Any], key: str) -> None:
    with st.expander("Advanced: raw JSON output"):
        text = safe_json(data)
        st.code(text, language="json")
        st.download_button(
            label="Download JSON",
            data=text,
            file_name=f"{key}.json",
            mime="application/json",
            use_container_width=True,
        )


def call_backend(func, *args, **kwargs) -> dict[str, Any] | None:
    try:
        with st.spinner("Generating structured software-engineering output..."):
            return func(*args, **kwargs)
    except Exception as exc:
        st.error("The request failed. Check model/provider configuration or input format.")
        st.exception(exc)
        return None


def get_requirements_or_project_text(project_text: str) -> str:
    requirements = st.session_state.get("result_requirements")
    if isinstance(requirements, dict) and requirements:
        return safe_json(requirements)
    return project_text


client = get_client()
provider = client.provider
model = client.model
base_url = client.base_url or "default OpenAI endpoint"

with st.sidebar:
    advanced_mode = st.toggle("Advanced mode", value=False)

    if advanced_mode:
        st.markdown("## Runtime")
        st.markdown(f'<span class="badge badge-green">Provider: {provider}</span>', unsafe_allow_html=True)
        st.markdown(f'<span class="badge">Model: {model}</span>', unsafe_allow_html=True)
        st.caption(f"Endpoint: {base_url}")
        st.metric("Local corpus documents", "6")
        st.divider()

    use_context = st.checkbox("Use local dataset context", value=False)

    st.markdown("## Actions")
    if st.button("Load strong clinic example", use_container_width=True):
        st.session_state["project_description"] = EXAMPLE_PROJECT
        for key in ["review_input", "test_input", "arch_input", "attack_input"]:
            st.session_state.pop(key, None)

    if st.button("Clear generated outputs", use_container_width=True):
        for key in list(st.session_state.keys()):
            if key.startswith("result_") or key in {"review_input", "test_input", "arch_input", "attack_input"}:
                del st.session_state[key]

    if advanced_mode:
        st.divider()
        st.markdown("## Workflow")
        st.caption("Describe → Requirements → Review → Tests → Architecture → Code/Security")


st.markdown(
    f"""
<div class="hero-card">
    <div class="hero-title">LLM-Powered Virtual Assistant for Software Engineering</div>
    <div class="hero-subtitle">
        Generate requirements, review quality, create test cases, suggest architecture,
        analyze code, and identify defensive security risks using a structured AI workflow.
    </div>
    <br>
    <span class="badge badge-green">Provider: {provider}</span>
    <span class="badge">Model: {model}</span>
    <span class="badge badge-gray">Human-in-the-loop SE workflow</span>
</div>
""",
    unsafe_allow_html=True,
)

cols = st.columns(6)
workflow_items = [
    ("1", "Requirements", "Generate FR/NFR from project text."),
    ("2", "Review", "Find ambiguity and missing criteria."),
    ("3", "Tests", "Create structured verification cases."),
    ("4", "Architecture", "Suggest components and data flow."),
    ("5", "Code", "Review code quality and security."),
    ("6", "Security", "Generate defensive risk scenarios."),
]

for col, (num, title, desc) in zip(cols, workflow_items):
    with col:
        st.markdown(
            f"""
<div class="workflow-step">
    <span class="workflow-number">{num}</span>
    <strong>{title}</strong>
    <div class="muted" style="margin-top:8px;">{desc}</div>
</div>
""",
            unsafe_allow_html=True,
        )

st.markdown("### Project Brief")

if "project_description" not in st.session_state:
    st.session_state["project_description"] = EXAMPLE_PROJECT

project_description = st.text_area(
    "Describe the software system",
    key="project_description",
    height=140,
    placeholder=EXAMPLE_PROJECT,
)

quality, quality_type = input_quality_label(project_description)
if quality_type == "warn":
    st.markdown(f'<div class="warn-box">{quality} — add goal, users, features, data, and constraints.</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="good-box">{quality}</div>', unsafe_allow_html=True)


tab_chat, tab_req, tab_review, tab_tests, tab_arch, tab_code, tab_attack = st.tabs(
    [
        "General AI Chat",
        "Requirements",
        "Review",
        "Test Cases",
        "Architecture",
        "Code Analysis",
        "Security / Unsafe Scenarios",
    ]
)

with tab_chat:
    st.markdown("#### General AI Chat")
    st.caption("Ask general questions, request explanations, translations, presentation help, or software-engineering guidance.")

    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = [
            {
                "role": "assistant",
                "content": "Hi. I can help with software engineering, project reports, translations, explanations, and presentation preparation.",
            }
        ]

    chat_top_col, chat_clear_col = st.columns([5, 1])
    with chat_clear_col:
        if st.button("Clear chat", use_container_width=True):
            st.session_state["chat_messages"] = [
                {
                    "role": "assistant",
                    "content": "Chat cleared. How can I help?",
                }
            ]
            st.rerun()

    st.markdown(
        """
<style>
.chat-wrap {
    background: #0f172a;
    border: 1px solid #283447;
    border-radius: 18px;
    padding: 18px;
    margin-bottom: 16px;
    min-height: 360px;
    max-height: 520px;
    overflow-y: auto;
}
.msg-row {
    display: flex;
    margin-bottom: 14px;
}
.msg-user {
    justify-content: flex-end;
}
.msg-assistant {
    justify-content: flex-start;
}
.msg-bubble {
    max-width: 78%;
    padding: 12px 15px;
    border-radius: 16px;
    line-height: 1.55;
    font-size: 0.96rem;
    white-space: pre-wrap;
}
.user-bubble {
    background: linear-gradient(135deg, #ef4444, #f97316);
    color: white;
    border-bottom-right-radius: 4px;
}
.assistant-bubble {
    background: #111827;
    color: #e5e7eb;
    border: 1px solid #334155;
    border-bottom-left-radius: 4px;
}
.msg-label {
    font-size: 0.76rem;
    color: #94a3b8;
    margin-bottom: 4px;
}
</style>
""",
        unsafe_allow_html=True,
    )

    chat_html = ['<div class="chat-wrap">']
    for message in st.session_state["chat_messages"]:
        role = message.get("role", "assistant")
        content = escape_text(message.get("content", ""))

        if role == "user":
            chat_html.append(
                f"""
<div class="msg-row msg-user">
    <div>
        <div class="msg-label" style="text-align:right;">You</div>
        <div class="msg-bubble user-bubble">{content}</div>
    </div>
</div>
"""
            )
        else:
            chat_html.append(
                f"""
<div class="msg-row msg-assistant">
    <div>
        <div class="msg-label">Assistant</div>
        <div class="msg-bubble assistant-bubble">{content}</div>
    </div>
</div>
"""
            )

    chat_html.append("</div>")
    st.markdown("\n".join(chat_html), unsafe_allow_html=True)

    user_prompt = st.chat_input("Write a message...")

    if user_prompt:
        st.session_state["chat_messages"].append(
            {"role": "user", "content": user_prompt}
        )

        with st.spinner("Assistant is thinking..."):
            result = call_backend(general_ai_response, user_prompt)

        if result:
            answer = result.get("answer", "")
            st.session_state["chat_messages"].append(
                {"role": "assistant", "content": answer}
            )
        else:
            st.session_state["chat_messages"].append(
                {
                    "role": "assistant",
                    "content": "I could not generate a response. Please check the provider/model configuration.",
                }
            )

        st.rerun()
with tab_req:
    st.markdown("#### Generate structured software requirements")
    st.caption("Converts a project description into assumptions, clarification questions, FRs, NFRs, and risks.")

    if st.button("Generate requirements", key="btn_req", type="primary"):
        if is_short_or_generic(project_description):
            st.session_state["result_requirements"] = {
                "status": "insufficient_input",
                "message": "The input is too short or too generic to generate meaningful requirements.",
                "required_input": [
                    "Describe the goal of the software system.",
                    "Identify primary users or stakeholders.",
                    "List the main features or workflows.",
                    "Mention important data, constraints, privacy, or security concerns.",
                ],
                "example_input": EXAMPLE_PROJECT,
            }
        else:
            result = call_backend(generate_requirements, project_description, use_context=use_context)
            if result:
                st.session_state["result_requirements"] = result

    result = st.session_state.get("result_requirements")
    if result:
        if result.get("status") == "insufficient_input":
            show_guidance_for_short_input()
            render_list("Required details", result.get("required_input", []), "•")
        else:
            render_requirements(result)
        render_raw_toggle(result, "requirements_output")

with tab_review:
    st.markdown("#### Review requirements quality")
    st.caption("Detects ambiguity, missing acceptance criteria, privacy/security gaps, and unverifiable statements.")

    requirements_text = st.text_area(
        "Requirements to review",
        value=get_requirements_or_project_text(project_description),
        height=180,
        key="review_input",
    )

    if st.button("Review requirements", key="btn_review", type="primary"):
        if is_short_or_generic(requirements_text):
            st.warning("Please generate requirements first or paste a meaningful requirements document.")
        else:
            result = call_backend(review_requirements, requirements_text, use_context=use_context)
            if result:
                st.session_state["result_review"] = result

    result = st.session_state.get("result_review")
    if result:
        render_review(result)
        render_raw_toggle(result, "review_output")

with tab_tests:
    st.markdown("#### Generate test cases")
    st.caption("Transforms requirements into test cases with steps, expected results, priority, and coverage notes.")

    test_input = st.text_area(
        "Requirements for test generation",
        value=get_requirements_or_project_text(project_description),
        height=180,
        key="test_input",
    )

    if st.button("Generate test cases", key="btn_tests", type="primary"):
        if is_short_or_generic(test_input):
            st.warning("Please generate requirements first or paste meaningful requirements.")
        else:
            result = call_backend(generate_test_cases, test_input, use_context=use_context)
            if result:
                st.session_state["result_tests"] = result

    result = st.session_state.get("result_tests")
    if result:
        render_test_cases(result)
        render_raw_toggle(result, "test_cases_output")

with tab_arch:
    st.markdown("#### Suggest high-level architecture")
    st.caption("Generates architecture style, components, data flow, technology stack, deployment view, and HITL points.")

    arch_requirements = st.text_area(
        "Requirements/context for architecture suggestion",
        value=get_requirements_or_project_text(project_description),
        height=180,
        key="arch_input",
    )

    if st.button("Suggest architecture", key="btn_arch", type="primary"):
        if is_short_or_generic(arch_requirements):
            st.warning("Please provide a meaningful project brief or generated requirements.")
        else:
            result = call_backend(suggest_architecture, project_description, arch_requirements, use_context=use_context)
            if result:
                st.session_state["result_architecture"] = result

    result = st.session_state.get("result_architecture")
    if result:
        render_architecture(result)
        render_raw_toggle(result, "architecture_output")

with tab_code:
    st.markdown("#### Analyze code quality and basic security")
    st.caption("Reviews a code snippet for visible bugs, readability, maintainability, reliability, and defensive security issues.")

    if "code_text" not in st.session_state:
        st.session_state["code_text"] = EXAMPLE_CODE

    code_text = st.text_area(
        "Code snippet to analyze",
        key="code_text",
        height=220,
    )

    if st.button("Analyze code", key="btn_code", type="primary"):
        if len(code_text.strip()) < 10:
            st.warning("Please provide a meaningful code snippet.")
        else:
            result = call_backend(analyze_code, code_text, use_context=use_context)
            if result:
                st.session_state["result_code"] = result

    result = st.session_state.get("result_code")
    if result:
        render_code_analysis(result)
        render_raw_toggle(result, "code_analysis_output")

with tab_attack:
    st.markdown("#### Generate defensive attack and unsafe scenarios")
    st.caption("Produces defensive risk scenarios, unsafe cases, mitigations, and validation tests.")

    attack_context = st.text_area(
        "Requirements/context for defensive risk analysis",
        value=get_requirements_or_project_text(project_description),
        height=190,
        key="attack_input",
    )

    if st.button("Generate defensive scenarios", key="btn_attack", type="primary"):
        if is_short_or_generic(attack_context):
            st.warning("Please provide a meaningful project brief or generated requirements.")
        else:
            result = call_backend(
                generate_attack_scenarios,
                project_description,
                attack_context,
                use_context=use_context,
            )
            if result:
                st.session_state["result_attack"] = result

    result = st.session_state.get("result_attack")
    if result:
        render_attack_scenarios(result)
        render_raw_toggle(result, "attack_scenarios_output")
