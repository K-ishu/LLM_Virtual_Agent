from __future__ import annotations

import html
import json
import os
import re
from datetime import datetime
from textwrap import dedent

import streamlit as st
from pathlib import Path

try:
    from app.llm_client import LLMClient
except Exception:
    LLMClient = None


# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(
    page_title="LLM-Powered Virtual Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# -----------------------------
# State
# -----------------------------
def now_time() -> str:
    return datetime.now().strftime("%I:%M %p").lstrip("0")


defaults = {
    "project_brief": "",
    "workflow_result": "",
    "workflow_title": "",
    "logged_in": False,
    "login_open": False,
    "user_name": "Guest User",
    "user_email": "Not logged in",
    "chat_messages": [],
    "chat_history": [],
    "project_history": [],
    "chat_closed": False,
    "chat_minimized": False,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# Chat header controls from HTML links
chat_action = st.query_params.get("chat_action", None)
if chat_action == "toggle":
    st.session_state.chat_minimized = not st.session_state.get("chat_minimized", False)
    st.query_params.clear()
    st.rerun()
elif chat_action == "close":
    st.session_state.chat_closed = False
    st.query_params.clear()
    st.rerun()
elif chat_action == "open":
    st.session_state.chat_closed = False
    st.session_state.chat_minimized = False
    st.query_params.clear()
    st.rerun()



# -----------------------------
# Helpers
# -----------------------------
def render_html(markup: str) -> None:
    markup = dedent(markup).strip()
    if hasattr(st, "html"):
        st.html(markup)
    else:
        st.markdown(markup, unsafe_allow_html=True)


def clean_ai_text(value) -> str:
    if value is None:
        return "No response returned."

    if isinstance(value, str):
        text = value.strip()
        if not text:
            return "Empty response."
        try:
            return clean_ai_text(json.loads(text))
        except Exception:
            return text

    if isinstance(value, dict):
        for key in ("answer", "content", "text", "message", "response"):
            if key in value:
                return clean_ai_text(value[key])
        return json.dumps(value, ensure_ascii=False, indent=2)

    if isinstance(value, list):
        return "\n".join(clean_ai_text(item) for item in value if item)

    return str(value)


def ask_ai(prompt: str) -> str:
    system_prompt = (
        "You are a professional AI assistant for software engineering. "
        "Answer clearly and practically. "
        "For workflow tasks, use structured presentation headings and bullet points. "
        "Do not return raw JSON unless the user explicitly asks for JSON. "
        "If the user writes in Persian, answer in Persian."
    )

    if LLMClient is None:
        return "LLMClient is not available. Check app.llm_client import."

    try:
        client = LLMClient()
        response = client.chat(system_prompt, prompt)
        return clean_ai_text(getattr(response, "text", response))
    except Exception as exc:
        return f"AI request failed: {exc}"


def submit_chat(prompt: str) -> None:
    prompt = (prompt or "").strip()
    if not prompt:
        return

    user_message = {"role": "user", "content": prompt, "time": now_time()}
    st.session_state.chat_messages.append(user_message)

    with st.spinner("AI is answering..."):
        answer = ask_ai(prompt)

    assistant_message = {"role": "assistant", "content": answer, "time": now_time()}
    st.session_state.chat_messages.append(assistant_message)

    st.session_state.chat_history.append(
        {"question": prompt, "answer": answer, "time": now_time()}
    )



# -----------------------------
# Persistent Project Brief Draft
# -----------------------------
PROJECT_BRIEF_DRAFT_FILE = Path("data/project_brief_draft.json")

def load_project_brief_draft() -> str:
    try:
        if PROJECT_BRIEF_DRAFT_FILE.exists():
            data = json.loads(PROJECT_BRIEF_DRAFT_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return str(data.get("project_brief", ""))
    except Exception:
        pass
    return ""

def save_project_brief_draft() -> None:
    try:
        PROJECT_BRIEF_DRAFT_FILE.parent.mkdir(parents=True, exist_ok=True)
        PROJECT_BRIEF_DRAFT_FILE.write_text(
            json.dumps(
                {"project_brief": st.session_state.get("project_brief", "")},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    except Exception:
        pass


def save_project_history() -> None:
    brief = st.session_state.get("project_brief", "").strip()
    if not brief:
        return

    title = brief[:42].strip()
    if len(brief) > 42:
        title += "..."

    item = {
        "title": title,
        "brief": brief,
        "time": now_time(),
    }

    # Avoid saving exact duplicate briefs repeatedly.
    existing = [
        x for x in st.session_state.project_history
        if x.get("brief", "").strip() != brief
    ]
    st.session_state.project_history = [item] + existing
    st.session_state.project_history = st.session_state.project_history[:6]


def normalize_result_text(text: str) -> str:
    text = clean_ai_text(text)
    text = text.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(text)
        if isinstance(data, dict):
            sections = []
            for key, value in data.items():
                title = str(key).replace("_", " ").title()
                if isinstance(value, list):
                    body = "\n".join(f"• {clean_ai_text(item)}" for item in value)
                elif isinstance(value, dict):
                    body = "\n".join(
                        f"• {str(k).replace('_', ' ').title()}: {clean_ai_text(v)}"
                        for k, v in value.items()
                    )
                else:
                    body = clean_ai_text(value)
                sections.append(f"## {title}\n{body}")
            return "\n\n".join(sections)
    except Exception:
        pass

    return text


def split_result_sections(text: str) -> list[tuple[str, str]]:
    text = normalize_result_text(text)

    known_titles = [
        "Assumptions",
        "Clarification Questions",
        "Functional Requirements",
        "Non-Functional Requirements",
        "Risks",
        "Review Summary",
        "Detected Issues",
        "Recommendations",
        "Improved Requirements",
        "Test Cases",
        "Architecture Style",
        "Main Components",
        "Components",
        "Data Flow",
        "Technology Stack",
        "Deployment View",
        "Security Considerations",
        "Potential Abuse Cases",
        "Security Risks",
        "Privacy Risks",
        "Mitigations",
        "Validation Tests",
        "Summary",
        "Detected Language/Technology",
        "Quality Findings",
        "Security Findings",
        "Recommended Improvements",
    ]

    normalized = text
    for title in known_titles:
        normalized = re.sub(
            rf"(?im)^\s*(?:#+\s*)?{re.escape(title)}\s*:?\s*$",
            f"## {title}",
            normalized,
        )

    matches = list(re.finditer(r"(?m)^##\s+(.+?)\s*$", normalized))
    if not matches:
        return [("AI Output", normalized.strip())]

    sections: list[tuple[str, str]] = []
    for idx, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(normalized)
        body = normalized[start:end].strip()
        if body:
            sections.append((title, body))

    return sections or [("AI Output", normalized.strip())]


def render_workflow_result() -> None:
    if not st.session_state.workflow_result:
        render_html(
            """
            <section class="workflow-result">
              <div class="workflow-result-title">Workflow Result</div>
              <div class="workflow-empty">
                Run Requirements, Review, Test Cases, Architecture, Code Analysis, or Security.
                The structured output will appear here as separate presentation cards.
              </div>
            </section>
            """
        )
        return

    sections = split_result_sections(st.session_state.workflow_result)
    cards = []
    for title, body in sections:
        safe_title = html.escape(title)
        safe_body = html.escape(body).replace("\n", "<br>")
        cards.append(
            f"""
            <div class="result-card">
              <div class="result-card-title">{safe_title}</div>
              <div class="result-card-body">{safe_body}</div>
            </div>
            """
        )

    render_html(
        f"""
        <section class="workflow-result">
          <div class="workflow-result-title">
            Workflow Result: {html.escape(st.session_state.workflow_title or "AI Output")}
          </div>
          <div class="workflow-result-note">
            Presentation-ready view. Each category is separated into its own card.
          </div>
          <div class="result-grid">
            {''.join(cards)}
          </div>
        </section>
        """
    )


def run_workflow(action: str, brief: str) -> None:
    brief = (brief or "").strip()

    if not brief:
        st.warning("Write a project brief first.")
        return

    prompts = {
        "Requirements": f"""Generate professional software requirements for this project brief:

{brief}

Return the answer in clear presentation format with these exact headings:
## Assumptions
## Clarification Questions
## Functional Requirements
## Non-Functional Requirements
## Risks

Do not return raw JSON. Use concise professional bullet points.""",
        "Review": f"""Review this project brief or requirements:

{brief}

Return the answer with these headings:
## Review Summary
## Detected Issues
## Recommendations
## Improved Requirements

Focus on ambiguity, missing acceptance criteria, privacy/security gaps, contradictions, and unverifiable statements. Do not return raw JSON.""",
        "Test Cases": f"""Generate professional test cases for this project:

{brief}

Return the answer with this heading:
## Test Cases

For each test case include ID, priority, preconditions, steps, expected result, and requirement covered. Do not return raw JSON.""",
        "Architecture": f"""Suggest a high-level software architecture for this project:

{brief}

Return the answer with these headings:
## Architecture Style
## Main Components
## Data Flow
## Technology Stack
## Deployment View
## Security Considerations

Do not return raw JSON.""",
        "Code Analysis": f"""Analyze this code or technical description:

{brief}

Return the answer with these headings:
## Summary
## Detected Language/Technology
## Quality Findings
## Security Findings
## Recommended Improvements

Do not return raw JSON.""",
        "Security": f"""Generate defensive security and unsafe scenario analysis for this project:

{brief}

Return the answer with these headings:
## Potential Abuse Cases
## Security Risks
## Privacy Risks
## Mitigations
## Validation Tests

Do not return raw JSON.""",
    }

    prompt = prompts[action]

    with st.spinner("Running workflow..."):
        result = ask_ai(prompt)

    save_project_history()
    st.session_state.workflow_title = action
    st.session_state.workflow_result = result


def login_user(username: str, password: str) -> bool:
    expected_user = os.getenv("APP_USERNAME", "admin")
    expected_password = os.getenv("APP_PASSWORD", "admin")

    if username == expected_user and password == expected_password:
        st.session_state.logged_in = True
        st.session_state.user_name = username
        st.session_state.user_email = f"{username}@local"
        st.toast("Logged in.", icon="✅")
        return True

    st.error("Invalid username or password.")
    return False


# -----------------------------
# CSS
# -----------------------------
st.markdown(
    """
<style>
:root {
  --bg: #050914;
  --rail: #07111f;
  --panel: #0b1424;
  --panel2: #0e192c;
  --stroke: rgba(117,142,200,.18);
  --stroke2: rgba(117,142,200,.32);
  --text: #edf4ff;
  --muted: #91a2c0;
  --red: #ff4f5f;
  --purple: #8c5cff;
  --green: #22c55e;
}

html, body, [class*="css"], .stApp {
  font-family: Inter, "Segoe UI", system-ui, sans-serif;
}

.stApp {
  background:
    radial-gradient(circle at 16% 10%, rgba(27,58,132,0.25), transparent 25%),
    radial-gradient(circle at 75% 10%, rgba(117,58,255,0.14), transparent 24%),
    linear-gradient(180deg, #060b15 0%, #050913 38%, #05070e 100%);
  color: var(--text);
}

header[data-testid="stHeader"] { background: transparent !important; }
#MainMenu, footer { visibility: hidden; }
[data-testid="stSidebar"], section[data-testid="stSidebar"] { display:none !important; }

.block-container {
  max-width: 1700px !important;
  padding: 22px 22px 36px !important;
}

/* Native widgets */
.stTextArea textarea,
.stTextInput input {
  background: rgba(8,14,26,.95) !important;
  color: #edf4ff !important;
  border-radius: 12px !important;
  border: 1px solid rgba(120,140,200,.24) !important;
  font-size: 14px !important;
  box-shadow: none !important;
}

.stTextArea textarea::placeholder,
.stTextInput input::placeholder {
  color: #7890ba !important;
  opacity: 1 !important;
}

.stButton > button,
.stFormSubmitButton > button {
  border-radius: 12px !important;
  border: 1px solid rgba(120,140,200,.22) !important;
  background: linear-gradient(180deg, rgba(12,19,36,.96), rgba(8,14,26,.98)) !important;
  color: #eef4ff !important;
  font-weight: 850 !important;
  min-height: 40px !important;
  box-shadow: none !important;
}

.stButton > button:hover,
.stFormSubmitButton > button:hover {
  border-color: rgba(255,95,110,.55) !important;
  color: white !important;
}

/* Login screen */
.login-screen {
  min-height: 88vh;
  display: grid;
  place-items: center;
}

.login-card-screen {
  width: min(520px, 92vw);
  border: 1px solid rgba(255,80,110,.34);
  border-radius: 26px;
  background:
    radial-gradient(circle at 20% 10%, rgba(255,80,130,.10), transparent 26%),
    radial-gradient(circle at 80% 0%, rgba(120,90,255,.12), transparent 30%),
    linear-gradient(180deg, rgba(12,20,40,.98), rgba(8,14,26,.99));
  box-shadow: 0 26px 90px rgba(0,0,0,.35);
  padding: 34px;
  text-align: center;
}

.login-logo {
  width: 72px;
  height: 72px;
  border-radius: 22px;
  display: grid;
  place-items: center;
  margin: 0 auto 16px;
  font-size: 38px;
  background: linear-gradient(180deg, rgba(255,95,95,.24), rgba(255,95,95,.06));
  border: 1px solid rgba(255,120,120,.35);
}

.login-title {
  font-size: 28px;
  font-weight: 950;
  margin-bottom: 8px;
}

.login-sub {
  color: #9fb0d6;
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 22px;
}

/* Sidebar */
.left-rail {
  border-right: 1px solid rgba(255,255,255,.08);
  padding: 18px 16px 20px 4px;
  min-height: calc(100vh - 45px);
}

.brand {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 28px;
}

.logo {
  width: 48px;
  height: 48px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  font-size: 25px;
  background: linear-gradient(180deg, rgba(255,95,95,.22), rgba(255,95,95,.05));
  border: 1px solid rgba(255,120,120,.35);
}

.brand-title { font-size: 16px; font-weight: 950; }
.brand-sub { font-size: 12px; color: #b7c3dd; margin-top: 3px; }

.nav {
  padding: 14px 16px;
  border-radius: 14px;
  border: 1px solid rgba(255,110,120,.42);
  background: linear-gradient(90deg, rgba(255,90,90,.14), rgba(255,90,90,.04));
  font-weight: 900;
  margin-bottom: 26px;
}

.section {
  font-size: 11px;
  letter-spacing: .11em;
  color: #7e8aa8;
  text-transform: uppercase;
  font-weight: 900;
  margin: 18px 0 10px;
}

.history, .profile {
  border: 1px solid rgba(120,140,200,.18);
  background: linear-gradient(180deg, rgba(11,19,38,.85), rgba(8,15,30,.92));
  border-radius: 13px;
  padding: 12px 14px;
  margin-bottom: 10px;
}

.history.active {
  border-color: rgba(255,95,95,.42);
  background: linear-gradient(180deg, rgba(120,25,35,.28), rgba(15,18,35,.95));
}

.history-title { font-size: 13px; font-weight: 800; color: white; }
.history span, .profile-mail { font-size: 11px; color: #8ea0c6; }

.search {
  border: 1px solid rgba(120,140,200,.18);
  background: rgba(10,17,31,.90);
  border-radius: 12px;
  padding: 11px 12px;
  color: #8292b7;
  font-size: 12px;
  margin-bottom: 12px;
}

.profile {
  margin-top: 22px;
  display: flex;
  gap: 11px;
  align-items: center;
}

.avatar {
  width: 46px;
  height: 46px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #6e85ff, #ff6f8f);
  color: white;
  font-weight: 900;
}

.profile-name { font-size: 13px; font-weight: 850; }

/* Hero */
.hero {
  border-radius: 24px;
  border: 1px solid rgba(120,140,200,.17);
  overflow: hidden;
  display: grid;
  grid-template-columns: 42% 58%;
  min-height: 290px;
  background:
    radial-gradient(circle at 30% 30%, rgba(40,90,255,.18), transparent 28%),
    radial-gradient(circle at 70% 30%, rgba(255,60,120,.08), transparent 22%),
    linear-gradient(180deg, rgba(10,19,38,.96), rgba(8,13,26,.98));
  box-shadow: 0 10px 50px rgba(0,0,0,.24), inset 0 0 0 1px rgba(255,255,255,.02);
}

.hero-left {
  position: relative;
  display: grid;
  place-items: center;
  border-right: 1px solid rgba(255,255,255,.06);
  background:
    radial-gradient(circle at 50% 43%, rgba(255,91,126,.30), transparent 14%),
    radial-gradient(circle at 50% 43%, rgba(111,92,255,.30), transparent 26%),
    linear-gradient(180deg, rgba(8,16,34,.90), rgba(8,16,34,.98));
}

.hero-left::before {
  content:"";
  position:absolute;
  inset:0;
  background-image:
    linear-gradient(rgba(255,255,255,.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,.025) 1px, transparent 1px);
  background-size: 34px 34px;
}

.hero-left::after {
  content:"";
  position:absolute;
  bottom:34px;
  width:210px;
  height:42px;
  background: radial-gradient(circle, rgba(141,72,255,.54), rgba(70,60,255,.10), transparent 75%);
  filter: blur(10px);
}

.brain {
  font-size: 118px;
  z-index: 2;
  filter: drop-shadow(0 0 22px rgba(255,90,130,.35)) drop-shadow(0 0 34px rgba(120,95,255,.22));
}

.hero-right {
  position: relative;
  padding: 34px 38px;
}

.hero-icons {
  position:absolute;
  top:25px;
  right:25px;
  display:flex;
  gap:18px;
  font-size:22px;
}

.hero-title {
  margin-top: 38px;
  font-size: 35px;
  line-height: 1.08;
  font-weight: 950;
}

.hero-title .accent { color: #ff5972; }
.hero-desc {
  margin-top: 12px;
  max-width: 610px;
  font-size: 14px;
  line-height: 1.65;
  color: #b7c4df;
}

.badges {
  margin-top:24px;
  display:flex;
  gap:12px;
  flex-wrap:wrap;
}

.badge {
  border:1px solid rgba(120,140,200,.22);
  background:rgba(8,14,28,.72);
  border-radius:999px;
  padding:10px 14px;
  font-size:13px;
}

/* Workflow cards */
.workflow-cards {
  margin-top:18px;
  display:grid;
  grid-template-columns: repeat(6, 1fr);
  gap:14px;
}

.workflow-card {
  border:1px solid rgba(120,140,200,.18);
  background:linear-gradient(180deg, rgba(13,20,38,.92), rgba(9,15,28,.98));
  border-radius:18px;
  min-height:104px;
  padding:16px 18px;
}

.workflow-num {
  width:36px;
  height:36px;
  border-radius:50%;
  display:inline-grid;
  place-items:center;
  font-weight:900;
  margin-bottom:10px;
  border:1px solid rgba(255,255,255,.16);
}

.c1 { background:rgba(255,104,76,.22); color:#ff8d74; }
.c2 { background:rgba(180,85,255,.22); color:#c58cff; }
.c3 { background:rgba(158,85,255,.22); color:#bf98ff; }
.c4 { background:rgba(90,140,255,.22); color:#83adff; }
.c5 { background:rgba(255,180,70,.22); color:#ffcf7f; }
.c6 { background:rgba(80,210,200,.22); color:#7de8dc; }

.workflow-card-title { font-size:14px; font-weight:900; margin-bottom:5px; }
.workflow-card-sub { font-size:12px; color:#93a5cb; line-height:1.45; }

/* Brief */
.brief-card {
  margin-top:18px;
  border:1px solid rgba(120,140,200,.17);
  border-radius:18px 18px 0 0;
  background:linear-gradient(180deg, rgba(11,19,38,.88), rgba(8,14,26,.98));
  padding:18px 18px 10px;
}

.brief-head {
  display:flex;
  justify-content:space-between;
  align-items:center;
}

.brief-title { font-size:18px; font-weight:900; }
.brief-sub { font-size:13px; color:#a3b2d0; margin-top:2px; }

.brief-btn {
  border:1px solid rgba(255,110,120,.38);
  color:#ff8f98;
  background:rgba(255,75,75,.06);
  border-radius:14px;
  padding:10px 14px;
  font-weight:800;
  font-size:13px;
}

/* Workflow result */
.workflow-panel {
  margin-top: 18px;
  border: 1px solid rgba(120,140,200,.17);
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(11,19,38,.86), rgba(8,14,26,.98));
  padding: 18px;
}

.workflow-title {
  font-size: 22px;
  font-weight: 950;
  margin-bottom: 14px;
}

.workflow-result {
  margin-top: 16px;
  border: 1px solid rgba(120,140,200,.16);
  border-radius: 20px;
  background:
    radial-gradient(circle at 20% 20%, rgba(80,120,255,.10), transparent 28%),
    linear-gradient(180deg, rgba(12,20,40,.96), rgba(8,14,26,.98));
  padding: 18px;
}

.workflow-result-title {
  font-size: 17px;
  font-weight: 950;
  margin-bottom: 8px;
}

.workflow-result-note, .workflow-empty {
  color: #91a2c0;
  font-size: 13px;
  margin-bottom: 12px;
}

.result-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}

.result-card {
  border: 1px solid rgba(120,140,200,.18);
  background: linear-gradient(180deg, rgba(14,24,46,.96), rgba(9,16,31,.98));
  border-radius: 16px;
  padding: 16px 18px;
}

.result-card-title {
  font-size: 15px;
  font-weight: 950;
  color: #ffffff;
  margin-bottom: 10px;
}

.result-card-body {
  color: #dfe8ff;
  font-size: 14px;
  line-height: 1.75;
}

/* Unified online chat */
.online-chat-shell {
  border: 1px solid rgba(255,80,110,.42);
  border-radius: 22px;
  background:
    radial-gradient(circle at 15% 10%, rgba(255,80,130,.08), transparent 24%),
    radial-gradient(circle at 85% 30%, rgba(120,90,255,.10), transparent 28%),
    linear-gradient(180deg, rgba(12,20,40,.97), rgba(8,14,26,.99));
  box-shadow: 0 18px 60px rgba(0,0,0,.32), 0 0 28px rgba(255,70,110,.08);
  overflow: hidden;
  padding: 0 0 12px;
}

.chat-header {
  padding: 16px 18px;
  border-bottom: 1px solid rgba(255,255,255,.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-title {
  font-size: 16px;
  font-weight: 950;
}

.chat-status {
  font-size: 12px;
  color: #9fb0d6;
  margin-top: 4px;
}

.online-dot {
  display:inline-block;
  width:8px;
  height:8px;
  border-radius:50%;
  background:#22c55e;
  margin-right:7px;
  box-shadow:0 0 10px rgba(34,197,94,.55);
}

.chat-window {
  height: 430px;
  overflow-y: auto;
  padding: 18px;
  border-bottom: 1px solid rgba(255,255,255,.08);
}

.empty-chat {
  height: 390px;
  display: grid;
  place-items: center;
  text-align: center;
  color: #8fa2c7;
}

.empty-chat-icon { font-size: 34px; margin-bottom: 10px; }
.empty-chat-title { color:white; font-weight:900; font-size:16px; }
.empty-chat-text { font-size:13px; margin-top:6px; max-width:280px; }

.chat-row {
  display:flex;
  gap:10px;
  margin-bottom:16px;
}

.chat-row.user {
  justify-content:flex-end;
}

.chat-avatar {
  width:32px;
  height:32px;
  border-radius:50%;
  display:grid;
  place-items:center;
  background:rgba(255,80,120,.15);
  border:1px solid rgba(255,120,150,.25);
  flex-shrink:0;
}

.chat-bubble {
  max-width: 78%;
  border-radius: 18px;
  padding: 13px 15px;
  font-size: 13.5px;
  line-height: 1.6;
}

.chat-bubble.assistant {
  background: linear-gradient(180deg, rgba(24,35,63,.97), rgba(15,24,44,.99));
  border: 1px solid rgba(120,140,200,.20);
  border-top-left-radius: 8px;
}

.chat-bubble.user {
  background: linear-gradient(180deg, rgba(172,56,78,.96), rgba(150,45,65,.96));
  border: 1px solid rgba(255,110,130,.25);
  border-top-right-radius: 8px;
}

.chat-time {
  font-size: 10.5px;
  color: #7f92bc;
  margin-top: 5px;
}

@media (max-width: 1400px) {
  .workflow-cards { grid-template-columns: repeat(3, 1fr); }
}

@media (max-width: 1100px) {
  .left-rail { display:none; }
  .hero { grid-template-columns:1fr; }
  .workflow-cards { grid-template-columns: repeat(2, 1fr); }
}

/* Floating Assistant */
.floating-chat-shell {
  position: fixed;
  z-index: 9999;
  width: 380px;
  max-width: calc(100vw - 36px);
  border: 1px solid rgba(255,80,110,.42);
  border-radius: 22px;
  background:
    radial-gradient(circle at 15% 10%, rgba(255,80,130,.08), transparent 24%),
    radial-gradient(circle at 85% 30%, rgba(120,90,255,.10), transparent 28%),
    linear-gradient(180deg, rgba(12,20,40,.98), rgba(8,14,26,.99));
  box-shadow: 0 18px 70px rgba(0,0,0,.42), 0 0 32px rgba(255,70,110,.10);
  overflow: hidden;
}

.floating-chat-shell.bottom-right { right: 24px; bottom: 24px; }
.floating-chat-shell.bottom-left { left: 24px; bottom: 24px; }
.floating-chat-shell.top-right { right: 24px; top: 88px; }
.floating-chat-shell.top-left { left: 24px; top: 88px; }

.floating-chat-shell.minimized .chat-window {
  display: none;
}

.floating-chat-launcher {
  position: fixed;
  z-index: 9999;
  right: 24px;
  bottom: 24px;
  width: 62px;
  height: 62px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-size: 28px;
  background: linear-gradient(135deg, #ff4f5f, #8c5cff);
  border: 1px solid rgba(255,255,255,.22);
  box-shadow: 0 16px 45px rgba(0,0,0,.38);
}

.floating-chat-controls {
  margin-top: 14px;
  border: 1px solid rgba(120,140,200,.16);
  border-radius: 16px;
  padding: 12px;
  background: rgba(8,14,26,.72);
}


/* Professional embedded online assistant */
.assistant-card {
  border: 1px solid rgba(255,80,110,.42);
  border-radius: 22px;
  background:
    radial-gradient(circle at 15% 10%, rgba(255,80,130,.08), transparent 24%),
    radial-gradient(circle at 85% 30%, rgba(120,90,255,.10), transparent 28%),
    linear-gradient(180deg, rgba(12,20,40,.98), rgba(8,14,26,.99));
  box-shadow: 0 18px 70px rgba(0,0,0,.28), 0 0 32px rgba(255,70,110,.08);
  overflow: hidden;
  margin-top: 0;
}

.assistant-card.minimized .chat-window {
  display: none;
}

.assistant-card.minimized {
  min-height: auto;
}

.chat-header {
  padding: 15px 17px;
  border-bottom: 1px solid rgba(255,255,255,.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-title {
  font-size: 16px;
  font-weight: 950;
  color: #ffffff;
}

.chat-status {
  font-size: 12px;
  color: #9fb0d6;
  margin-top: 4px;
}

.online-dot {
  display:inline-block;
  width:8px;
  height:8px;
  border-radius:50%;
  background:#22c55e;
  margin-right:7px;
  box-shadow:0 0 10px rgba(34,197,94,.55);
}

.chat-header-actions {
  color: #c8d3ee;
  font-size: 18px;
  letter-spacing: 8px;
}

.chat-window {
  height: 390px;
  overflow-y: auto;
  padding: 18px;
}

.empty-chat {
  height: 340px;
  display: grid;
  place-items: center;
  text-align: center;
  color: #8fa2c7;
}

.empty-chat-icon { font-size: 34px; margin-bottom: 10px; }
.empty-chat-title { color:white; font-weight:900; font-size:16px; }
.empty-chat-text { font-size:13px; margin-top:6px; max-width:280px; }

.chat-row {
  display:flex;
  gap:10px;
  margin-bottom:16px;
}

.chat-row.user {
  justify-content:flex-end;
}

.chat-avatar {
  width:32px;
  height:32px;
  border-radius:50%;
  display:grid;
  place-items:center;
  background:rgba(255,80,120,.15);
  border:1px solid rgba(255,120,150,.25);
  flex-shrink:0;
}

.chat-bubble {
  max-width: 82%;
  border-radius: 18px;
  padding: 13px 15px;
  font-size: 13.5px;
  line-height: 1.6;
}

.chat-bubble.assistant {
  background: linear-gradient(180deg, rgba(24,35,63,.97), rgba(15,24,44,.99));
  border: 1px solid rgba(120,140,200,.20);
  border-top-left-radius: 8px;
}

.chat-bubble.user {
  background: linear-gradient(180deg, rgba(172,56,78,.96), rgba(150,45,65,.96));
  border: 1px solid rgba(255,110,130,.25);
  border-top-right-radius: 8px;
}

.chat-time {
  font-size: 10.5px;
  color: #7f92bc;
  margin-top: 5px;
}

.chat-closed-card {
  border: 1px solid rgba(255,80,110,.34);
  border-radius: 22px;
  background:
    radial-gradient(circle at 20% 10%, rgba(255,80,130,.12), transparent 28%),
    linear-gradient(180deg, rgba(12,20,40,.98), rgba(8,14,26,.99));
  padding: 22px;
  text-align: center;
  box-shadow: 0 18px 70px rgba(0,0,0,.28);
}

.chat-closed-icon {
  width: 58px;
  height: 58px;
  margin: 0 auto 12px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #ff4f5f, #8c5cff);
  font-size: 26px;
}

.chat-closed-title {
  font-size: 16px;
  font-weight: 950;
  color: #ffffff;
}

.chat-closed-sub {
  color: #9fb0d6;
  font-size: 13px;
  margin-top: 6px;
}


/* Chat header icon buttons like online support widgets */
.chat-header {
  position: relative;
  min-height: 58px;
}

.chat-header-actions {
  position: absolute;
  right: 14px;
  top: 13px;
  display: flex;
  gap: 8px;
  color: #dbe7ff;
  font-size: 18px;
  font-weight: 900;
  letter-spacing: 0;
  pointer-events: none;
}

.chat-header-actions span {
  width: 26px;
  height: 26px;
  border-radius: 9px;
  display: grid;
  place-items: center;
  background: rgba(255,255,255,.06);
  border: 1px solid rgba(255,255,255,.10);
}

/* The real Streamlit buttons are placed over the visual icons */
.chat-control-layer {
  height: 0;
  position: relative;
  z-index: 10000;
}

.chat-control-layer [data-testid="stHorizontalBlock"] {
  position: absolute;
  right: 12px;
  top: -54px;
  width: 64px;
  display: flex;
  gap: 7px;
}

.chat-control-layer .stButton > button {
  width: 27px !important;
  min-width: 27px !important;
  height: 27px !important;
  min-height: 27px !important;
  padding: 0 !important;
  border-radius: 9px !important;
  background: rgba(255,255,255,.001) !important;
  border: 0 !important;
  color: transparent !important;
  box-shadow: none !important;
}

.chat-control-layer .stButton > button:hover {
  background: rgba(255,255,255,.10) !important;
  border: 1px solid rgba(255,255,255,.16) !important;
}

/* Composer closer to real online chat */


div[data-testid="stForm"] .stTextInput input {
  min-height: 42px !important;
  border-radius: 14px !important;
}

div[data-testid="stForm"] .stFormSubmitButton > button {
  background: linear-gradient(135deg, #3158ff, #2348d8) !important;
  border: 1px solid rgba(90,130,255,.45) !important;
  color: white !important;
  border-radius: 14px !important;
  min-height: 42px !important;
}

div[data-testid="stForm"] .stFormSubmitButton > button:hover {
  filter: brightness(1.08);
}


/* Clean online chat widget */
.clean-chat-card {
  border: 1px solid rgba(255,80,110,.42);
  border-radius: 22px;
  background:
    radial-gradient(circle at 15% 10%, rgba(255,80,130,.08), transparent 24%),
    radial-gradient(circle at 85% 30%, rgba(120,90,255,.10), transparent 28%),
    linear-gradient(180deg, rgba(12,20,40,.98), rgba(8,14,26,.99));
  box-shadow: 0 18px 70px rgba(0,0,0,.32), 0 0 32px rgba(255,70,110,.08);
  overflow: hidden;
  margin-top: 0;
}

.clean-chat-header {
  height: 58px;
  padding: 14px 16px;
  border-bottom: 1px solid rgba(255,255,255,.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.clean-chat-title {
  font-size: 16px;
  font-weight: 950;
  color: #fff;
}

.clean-chat-status {
  color: #9fb0d6;
  font-size: 12px;
  margin-top: 4px;
}

.clean-online-dot {
  display:inline-block;
  width:8px;
  height:8px;
  border-radius:50%;
  background:#22c55e;
  margin-right:7px;
  box-shadow:0 0 10px rgba(34,197,94,.55);
}

.clean-chat-actions {
  display:flex;
  gap:8px;
}

.clean-chat-actions a {
  width:28px;
  height:28px;
  display:grid;
  place-items:center;
  border-radius:9px;
  color:#dbe7ff !important;
  text-decoration:none !important;
  background:rgba(255,255,255,.06);
  border:1px solid rgba(255,255,255,.11);
  font-size:18px;
  font-weight:900;
}

.clean-chat-actions a:hover {
  background:rgba(255,255,255,.13);
}

.clean-chat-window {
  height: 390px;
  overflow-y: auto;
  padding: 18px;
}

.clean-chat-card.minimized .clean-chat-window {
  display: none;
}

.clean-empty-chat {
  height: 340px;
  display:grid;
  place-items:center;
  text-align:center;
  color:#8fa2c7;
}

.clean-empty-icon {
  font-size:34px;
  margin-bottom:10px;
}

.clean-empty-title {
  color:#fff;
  font-weight:950;
  font-size:16px;
}

.clean-empty-text {
  font-size:13px;
  margin-top:6px;
  max-width:280px;
}

.clean-chat-row {
  display:flex;
  gap:10px;
  margin-bottom:16px;
}

.clean-chat-row.user {
  justify-content:flex-end;
}

.clean-avatar {
  width:32px;
  height:32px;
  border-radius:50%;
  display:grid;
  place-items:center;
  background:rgba(255,80,120,.15);
  border:1px solid rgba(255,120,150,.25);
  flex-shrink:0;
}

.clean-bubble {
  max-width:82%;
  border-radius:18px;
  padding:13px 15px;
  font-size:13.5px;
  line-height:1.6;
}

.clean-bubble.assistant {
  background:linear-gradient(180deg, rgba(24,35,63,.97), rgba(15,24,44,.99));
  border:1px solid rgba(120,140,200,.20);
  border-top-left-radius:8px;
}

.clean-bubble.user {
  background:linear-gradient(180deg, rgba(42,86,255,.96), rgba(30,67,210,.96));
  border:1px solid rgba(90,130,255,.35);
  border-top-right-radius:8px;
}

.clean-time {
  font-size:10.5px;
  color:#7f92bc;
  margin-top:5px;
}

.clean-closed-card {
  border:1px solid rgba(255,80,110,.34);
  border-radius:22px;
  background:
    radial-gradient(circle at 20% 10%, rgba(255,80,130,.12), transparent 28%),
    linear-gradient(180deg, rgba(12,20,40,.98), rgba(8,14,26,.99));
  padding:24px;
  text-align:center;
}

.clean-closed-icon {
  width:58px;
  height:58px;
  margin:0 auto 12px;
  border-radius:50%;
  display:grid;
  place-items:center;
  background:linear-gradient(135deg, #ff4f5f, #3158ff);
  font-size:26px;
}

.clean-closed-title {
  font-size:16px;
  font-weight:950;
  color:#fff;
}

.clean-closed-sub {
  color:#9fb0d6;
  font-size:13px;
  margin-top:6px;
}

/* Make chat form look connected to the card */


div[data-testid="stForm"] .stTextInput input {
  min-height:42px !important;
  border-radius:14px !important;
}

div[data-testid="stForm"] .stFormSubmitButton > button {
  background:linear-gradient(135deg, #3158ff, #2348d8) !important;
  border:1px solid rgba(90,130,255,.45) !important;
  color:white !important;
  border-radius:14px !important;
  min-height:42px !important;
}

.chat-small-action button {
  min-height:34px !important;
}

</style>
""",
    unsafe_allow_html=True,
)



# final-safe-url-actions
try:
    action = st.query_params.get("chat_action", "")
    ui_action = st.query_params.get("ui_action", "")
except Exception:
    action = ""
    ui_action = ""

if action == "toggle":
    st.session_state.chat_minimized = not st.session_state.get("chat_minimized", False)
    st.query_params.clear()
    st.rerun()

if action == "close":
    st.session_state.chat_closed = False
    st.query_params.clear()
    st.rerun()

if action == "open":
    st.session_state.chat_closed = False
    st.session_state.chat_minimized = False
    st.query_params.clear()
    st.rerun()

if ui_action == "theme":
    st.session_state.light_mode = not st.session_state.get("light_mode", False)
    st.query_params.clear()
    st.rerun()
# end-final-safe-url-actions

# -----------------------------
# Login gate
# -----------------------------
if not st.session_state.logged_in:
    render_html(
        """
        <div class="login-screen">
          <div class="login-card-screen">
            <div class="login-logo">🧠</div>
            <div class="login-title">LLM Assistant Login</div>
            <div class="login-sub">
              Sign in to open the software engineering assistant dashboard.
              Default local credentials are <b>admin / admin</b>.
            </div>
          </div>
        </div>
        """
    )

    a, b, c = st.columns([1, 1.2, 1])
    with b:
        with st.form("main_login_form"):
            username = st.text_input("Username", placeholder="admin")
            password = st.text_input("Password", type="password", placeholder="admin")
            submitted = st.form_submit_button("Login", use_container_width=True)
            if submitted:
                if username.strip() == "admin" and password.strip() == "admin":
                    st.session_state.logged_in = True
                    st.session_state.authenticated = True
                    st.session_state.logged_in = True
                    st.session_state.user_name = "admin"
                    st.session_state.user_email = "admin@local"
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

    st.stop()

    history_blocks = []
    if st.session_state.project_history:
        for idx, item in enumerate(st.session_state.project_history[:6]):
            klass = "history active" if idx == 0 else "history"
            history_blocks.append(
                f"""
                <div class="{klass}">
                  <div class="history-title">{html.escape(item.get("title", "Project Brief"))}</div>
                  <span>{html.escape(item.get("time", ""))}</span>
                </div>
                """
            )
    else:
        history_blocks.append(
            """
            <div class="history active">
              <div class="history-title">No saved project brief yet</div>
              <span>Run a workflow to save one</span>
            </div>
            """
        )

    render_html(
        f"""
        <div class="left-rail">
          <div class="brand">
            <div class="logo">🧠</div>
            <div>
              <div class="brand-title">LLM ASSISTANT</div>
              <div class="brand-sub">for Software Engineering</div>
            </div>
          </div>

          <div class="nav">⌘ Dashboard</div>

          <div class="section">Project Brief History</div>
{''.join(history_blocks)}
        </div>
        """
    )



    if st.button("Save Project Brief", key="save_project_brief_sidebar", use_container_width=True):
        if st.session_state.get("project_brief", "").strip():
            save_project_history()
            st.toast("Project brief saved.", icon="?")
            st.rerun()
        else:
            st.warning("Write a Project Brief first.")




# -----------------------------
# Main UI
# -----------------------------
left, main = st.columns([0.22, 0.78], gap="large")


# final-load-project-brief-draft
if not st.session_state.get("_project_brief_draft_loaded", False):
    saved_project_brief = load_project_brief_draft()
    if saved_project_brief and not st.session_state.get("project_brief"):
        st.session_state.project_brief = saved_project_brief
    st.session_state["_project_brief_draft_loaded"] = True
# end-final-load-project-brief-draft


with left:
    render_html(
        """
        <aside class="left-rail">
            <div class="brand">
                <div class="brand-icon">AI</div>
                <div>
                    <div class="brand-title">LLM ASSISTANT</div>
                    <div class="brand-sub">for Software Engineering</div>
                </div>
            </div>

            <div class="nav nav-active">Dashboard</div>

            <div class="section">PROJECT BRIEF HISTORY</div>
        </aside>
        """
    )

    history_query = st.text_input(
        "Project Brief History Search",
        key="history_search",
        placeholder="Search saved briefs...",
        label_visibility="collapsed",
    )

    history_query_clean = history_query.strip().lower()
    project_history_items = st.session_state.get("project_history", [])

    if history_query_clean:
        project_history_items = [
            item for item in project_history_items
            if history_query_clean in item.get("title", "").lower()
            or history_query_clean in item.get("brief", "").lower()
        ]

    if project_history_items:
        cards_html = ""
        for item in project_history_items[:6]:
            title = html.escape(item.get("title", "Saved Project Brief"))
            brief = html.escape(item.get("brief", ""))
            time_label = html.escape(item.get("time", "recent"))
            preview = brief[:85] + ("..." if len(brief) > 85 else "")
            cards_html += f"""
            <div class="history active">
                <div class="history-title">{title}</div>
                <span>{preview}</span>
                <span>{time_label}</span>
            </div>
            """
    else:
        cards_html = """
        <div class="history active">
            <div class="history-title">No saved project brief yet</div>
            <span>Run a workflow to save one</span>
        </div>
        """

    render_html(f"""<div class="history-wrap">{cards_html}</div>""")

    # final-chat-state-defaults
    if "chat_closed" not in st.session_state:
        st.session_state.chat_closed = False
    if "chat_minimized" not in st.session_state:
        st.session_state.chat_minimized = False
    # end-final-chat-state-defaults

    render_html(
        """
        <a class="chat-reopen-bubble" href="?chat_action=open" title="Open AI Chat"></a>
        """
    )

    if st.session_state.get("chat_closed"):
        render_html(
            """
            <section class="clean-closed-card">
              <div class="clean-closed-icon"></div>
              <div class="clean-closed-title">AI Chat is closed</div>
              <div class="clean-closed-sub">Click below to open the online assistant again.</div>
            </section>
            """
        )
        render_html('<a href="?chat_action=open" style="display:block;margin-top:12px;text-align:center;border:1px solid rgba(120,140,200,.25);border-radius:14px;padding:12px;color:white;text-decoration:none;background:rgba(12,20,40,.92);font-weight:800;">Open AI Chat</a>')

    else:
        message_blocks: list[str] = []

        if not st.session_state.chat_messages:
            message_blocks.append(
                """
                <div class="clean-empty-chat">
                  <div>
                    <div class="clean-empty-icon">&#128172;</div>
                    <div class="clean-empty-title">Online AI Chat</div>
                    <div class="clean-empty-text">
                      Ask quick questions. The chat scrolls inside this panel.
                    </div>
                  </div>
                </div>
                """
            )
        else:
            for msg in st.session_state.chat_messages[-12:]:
                role = msg.get("role", "assistant")
                content = html.escape(msg.get("content", "")).replace("\n", "<br>")
                time_text = html.escape(msg.get("time", ""))

                if role == "user":
                    message_blocks.append(
                        f"""
                        <div class="clean-chat-row user">
                          <div>
                            <div class="clean-bubble user">{content}</div>
                            <div class="clean-time" style="text-align:right;">{time_text} ??</div>
                          </div>
                        </div>
                        """
                    )
                else:
                    message_blocks.append(
                        f"""
                        <div class="clean-chat-row">
                          <div class="clean-avatar">AI</div>
                          <div>
                            <div class="clean-bubble assistant">{content}</div>
                            <div class="clean-time">{time_text}</div>
                          </div>
                        </div>
                        """
                    )

        minimized_class = " minimized" if st.session_state.get("chat_minimized") else ""

        render_html(
            f"""
            <section class="clean-chat-card{minimized_class}">
              <div class="clean-chat-header">
                <div>
                  <div class="clean-chat-title">AI Chat</div>
                  <div class="clean-chat-status"><span class="clean-online-dot"></span>Online</div>
                </div>
                <div class="clean-chat-actions"><a href="?chat_action=toggle" title="Minimize or restore chat">&minus;</a><a href="?chat_action=close" title="Close chat">&times;</a></div>
              </div>
              <div class="clean-chat-window">
                {''.join(message_blocks)}
              </div>
            </section>
            """
        )

        if not st.session_state.get("chat_minimized"):
            with st.form("online_chat_form", clear_on_submit=True):
                chat_prompt = st.text_input(
                    "Online chat",
                    placeholder="Type your message...",
                    label_visibility="collapsed",
                )
                sent = st.form_submit_button("Send", use_container_width=True)

                if sent and chat_prompt.strip():
                    submit_chat(chat_prompt)
                    st.rerun()

    # final-history-search-above-card

    render_html(
        f"""
        <div class="profile">
            <div class="avatar">{html.escape(st.session_state.get("user_name", "A")[:1].upper())}</div>
            <div>
                <div class="profile-name">{html.escape(st.session_state.get("user_name", "admin"))}</div>
                <div class="profile-mail">{html.escape(st.session_state.get("user_email", "admin@local"))}</div>
            </div>
        </div>
        """
    )

    if st.button("Logout", key="sidebar_logout_btn_clean", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.authenticated = False
        st.session_state.user_name = "Guest User"
        st.session_state.user_email = "Not logged in"
        st.rerun()

with main:
    provider = html.escape(os.getenv("LLM_PROVIDER", "openai"))
    model = html.escape(os.getenv("OPENAI_MODEL", "deepseek-ai/DeepSeek-V3.1"))

    theme_cols = st.columns([0.88, 0.12])
    with theme_cols[1]:
        if st.button("Theme", key="real_theme_toggle_btn", use_container_width=True):
            st.session_state.light_mode = not st.session_state.get("light_mode", False)
            st.rerun()


    render_html(
        f"""
        <section class="hero">
          <div class="hero-left">
            <div class="brain">🧠</div>
          </div>
          <div class="hero-right">
            <div class="hero-icons"></div>
            <div class="hero-title">
              <span class="accent">LLM-Powered</span><br>
              Virtual Assistant for<br>
              Software Engineering
            </div>
            <div class="hero-desc">
              Generate requirements, review quality, create test cases, suggest architecture,
              analyze code, and identify defensive security risks using a structured AI workflow.
            </div>
            <div class="badges">
              <div class="badge">🟢 Provider: {provider}</div>
              <div class="badge">🟣 Model: {model}</div>
              <div class="badge">🟠 Workflow: Human-in-the-loop SE</div>
            </div>
          </div>
        </section>

        <section class="workflow-cards">
          <div class="workflow-card"><div class="workflow-num c1">1</div><div class="workflow-card-title">Requirements</div><div class="workflow-card-sub">Generate FR/NFR</div></div>
          <div class="workflow-card"><div class="workflow-num c2">2</div><div class="workflow-card-title">Review</div><div class="workflow-card-sub">Find ambiguity & missing criteria</div></div>
          <div class="workflow-card"><div class="workflow-num c3">3</div><div class="workflow-card-title">Tests</div><div class="workflow-card-sub">Create structured test cases</div></div>
          <div class="workflow-card"><div class="workflow-num c4">4</div><div class="workflow-card-title">Architecture</div><div class="workflow-card-sub">Suggest components & data flow</div></div>
          <div class="workflow-card"><div class="workflow-num c5">5</div><div class="workflow-card-title">Code</div><div class="workflow-card-sub">Review code quality and security</div></div>
          <div class="workflow-card"><div class="workflow-num c6">6</div><div class="workflow-card-title">Security</div><div class="workflow-card-sub">Generate defensive risk scenarios</div></div>
        </section>

        <section class="brief-card">
          <div class="brief-head">
            <div>
              <div class="brief-title">Project Brief ⓘ</div>
              <div class="brief-sub">Describe the software system</div>
            </div>
            <div class="brief-btn">📄 Detailed project brief</div>
          </div>
        </section>
        """
    )

    st.text_area(
        "Project Brief",
        key="project_brief",
        height=88,
        placeholder="Describe your software project here...",
        label_visibility="collapsed",
        on_change=save_project_brief_draft,
    )

    render_html(
        """
        <section class="workflow-panel">
          <div class="workflow-title">AI Workflow</div>
        </section>
        """
    )

    action = st.radio(
        "Choose workflow",
        [
            "Requirements",
            "Review",
            "Test Cases",
            "Architecture",
            "Code Analysis",
            "Security",
        ],
        horizontal=True,
        label_visibility="collapsed",
    )

    run_clicked = st.button(
        "Run AI workflow",
        key="run_ai_workflow_main_button",
        type="primary",
        use_container_width=True,
    )

    if run_clicked:
        brief = st.session_state.get("project_brief", "").strip()
        st.session_state["workflow_last_clicked"] = True
        st.session_state["workflow_last_action"] = action

        if not brief:
            st.session_state.workflow_result = ""
            st.error("Please write a Project Brief before running the workflow.")
        else:
            try:
                with st.spinner(f"Running {action} workflow..."):
                    run_workflow(action, brief)

                if st.session_state.get("workflow_result", "").strip():
                    st.success(f"{action} workflow completed.")
                else:
                    st.warning("Workflow clicked, but no output was returned by the AI/backend.")

            except Exception as e:
                st.session_state.workflow_result = f"Workflow error: {e}"
                st.error(f"Workflow error: {e}")

    if st.session_state.get("workflow_result", "").strip():
        render_workflow_result()
    else:
        render_html(
            """
            <section class="workflow-result">
              <div class="workflow-result-title">Workflow Result</div>
              <div class="workflow-result-sub">
                Select a workflow module, write a Project Brief, then click Run AI workflow.
              </div>
            </section>
            """
        )

    lower_left, chat_col = st.columns([0.68, 0.32], gap="large")

    with lower_left:
        pass

    with chat_col:
        pass

    
st.markdown('\n<style>\n/* final history search position */\ndiv[data-testid="stTextInput"] input[placeholder="Search saved briefs..."] {\n  width: 250px !important;\n  max-width: 250px !important;\n  height: 34px !important;\n  min-height: 34px !important;\n  border-radius: 12px !important;\n  background: rgba(7, 14, 28, .92) !important;\n  border: 1px solid rgba(120,140,200,.25) !important;\n  color: #dce7ff !important;\n  font-size: 12px !important;\n  margin-bottom: 10px !important;\n}\n\ndiv[data-testid="stTextInput"] input[placeholder="Search saved briefs..."]::placeholder {\n  color: #8fa2c7 !important;\n}\n</style>\n', unsafe_allow_html=True)

# final-sidebar-workspace-theme-cleanup
st.markdown('\n<style>\n/* final sidebar cleanup */\n.left-rail {\n  padding-top: 20px !important;\n}\n\n.brand {\n  margin-bottom: 22px !important;\n}\n\n.brand-icon {\n  font-size: 11px !important;\n  font-weight: 900 !important;\n  color: #fff !important;\n}\n\n.nav,\n.nav-active {\n  margin-bottom: 20px !important;\n}\n\n.section {\n  margin-top: 6px !important;\n  margin-bottom: 10px !important;\n  color: #9fb3dc !important;\n  font-size: 11px !important;\n  letter-spacing: 1.6px !important;\n  font-weight: 900 !important;\n}\n\n/* keep history search directly under PROJECT BRIEF HISTORY */\ndiv[data-testid="stTextInput"] input[placeholder="Search saved briefs..."] {\n  width: 250px !important;\n  max-width: 250px !important;\n  height: 34px !important;\n  min-height: 34px !important;\n  border-radius: 12px !important;\n  background: rgba(7,14,28,.92) !important;\n  border: 1px solid rgba(120,140,200,.28) !important;\n  color: #dce7ff !important;\n  font-size: 12px !important;\n  margin-top: 0 !important;\n  margin-bottom: 12px !important;\n}\n\n.history-wrap {\n  margin-top: 0 !important;\n}\n\n.history {\n  width: 250px !important;\n  max-width: 250px !important;\n  margin-bottom: 14px !important;\n}\n\n.profile {\n  width: 250px !important;\n  max-width: 250px !important;\n  margin-top: 18px !important;\n}\n\n/* hide Project Workspace if any old HTML remains */\n.workflow-result-title:has(+ .workflow-empty),\n.workflow-empty {\n  display: none !important;\n}\n\n/* one clean theme button */\n.theme-link {\n  display: inline-flex !important;\n  align-items: center !important;\n  justify-content: center !important;\n  min-width: 72px !important;\n  height: 34px !important;\n  padding: 0 14px !important;\n  border-radius: 12px !important;\n  border: 1px solid rgba(255,255,255,.16) !important;\n  background: rgba(255,255,255,.08) !important;\n  color: #eaf1ff !important;\n  font-size: 12px !important;\n  font-weight: 900 !important;\n}\n\n/* hide extra broken top symbols if still visible */\n.hero-icons span:not(.theme-link),\n.hero-icons a:not(.theme-link) {\n  display: none !important;\n}\n</style>\n', unsafe_allow_html=True)

# final-real-left-sidebar-rebuild
st.markdown('\n<style>\n.left-rail {\n  padding-top: 18px !important;\n}\n\n.brand {\n  margin-bottom: 22px !important;\n}\n\n.brand-icon {\n  width: 34px !important;\n  height: 34px !important;\n  border-radius: 12px !important;\n  display: grid !important;\n  place-items: center !important;\n  background: rgba(255, 80, 110, .18) !important;\n  border: 1px solid rgba(255, 80, 110, .45) !important;\n  color: #fff !important;\n  font-weight: 900 !important;\n  font-size: 11px !important;\n}\n\n.brand-title {\n  font-size: 15px !important;\n  font-weight: 900 !important;\n}\n\n.brand-sub {\n  font-size: 11px !important;\n  color: #9fb0d6 !important;\n}\n\n.nav-active {\n  margin-top: 18px !important;\n  margin-bottom: 22px !important;\n  width: 250px !important;\n}\n\n.section {\n  margin-top: 0 !important;\n  margin-bottom: 10px !important;\n  color: #9fb3dc !important;\n  font-size: 11px !important;\n  letter-spacing: 1.5px !important;\n  font-weight: 900 !important;\n}\n\ndiv[data-testid="stTextInput"] input[placeholder="Search saved briefs..."] {\n  width: 250px !important;\n  max-width: 250px !important;\n  height: 34px !important;\n  min-height: 34px !important;\n  border-radius: 12px !important;\n  background: rgba(7, 14, 28, .92) !important;\n  border: 1px solid rgba(120, 140, 200, .28) !important;\n  color: #dce7ff !important;\n  font-size: 12px !important;\n  margin-bottom: 12px !important;\n}\n\n.history-wrap {\n  margin-top: 0 !important;\n}\n\n.history {\n  width: 250px !important;\n  max-width: 250px !important;\n  margin-bottom: 14px !important;\n}\n\n.profile {\n  width: 250px !important;\n  max-width: 250px !important;\n  margin-top: 22px !important;\n}\n\n.theme-link {\n  display: inline-flex !important;\n  align-items: center !important;\n  justify-content: center !important;\n  min-width: 72px !important;\n  height: 34px !important;\n  padding: 0 14px !important;\n  border-radius: 12px !important;\n  border: 1px solid rgba(255,255,255,.16) !important;\n  background: rgba(255,255,255,.08) !important;\n  color: #eaf1ff !important;\n  font-size: 12px !important;\n  font-weight: 900 !important;\n}\n\n/* hide remaining Project Workspace if any old block survived */\n.workflow-result-title:has(+ .workflow-empty),\n.workflow-empty {\n  display: none !important;\n}\n</style>\n', unsafe_allow_html=True)












# final-workflow-real-button
st.markdown('\n<style>\n/* Make Run AI workflow look and behave like a real button */\nbutton[kind="primary"],\ndiv[data-testid="stButton"] button {\n  cursor: pointer !important;\n  pointer-events: auto !important;\n}\n\ndiv[data-testid="stButton"] button:has(div p),\ndiv[data-testid="stButton"] button:has(p) {\n  min-height: 40px !important;\n  height: 40px !important;\n  border-radius: 12px !important;\n  font-size: 13px !important;\n  font-weight: 900 !important;\n}\n\n/* Stronger visual only for primary workflow button */\nbutton[kind="primary"] {\n  background: linear-gradient(135deg, #3158ff, #ff4f6d) !important;\n  border: 1px solid rgba(255,255,255,.18) !important;\n  color: white !important;\n  box-shadow: 0 10px 28px rgba(49,88,255,.22) !important;\n}\n\nbutton[kind="primary"]:hover {\n  transform: translateY(-1px) !important;\n  filter: brightness(1.08) !important;\n}\n</style>\n', unsafe_allow_html=True)

# final-sidebar-chat-before-profile
st.markdown('\n<style>\n/* Clean sidebar order: history -> AI chat -> admin/logout */\n.clean-chat-card {\n  width: 250px !important;\n  max-width: 250px !important;\n  height: 250px !important;\n  max-height: 250px !important;\n  margin-top: 18px !important;\n  margin-bottom: 10px !important;\n  border-radius: 16px !important;\n  overflow: hidden !important;\n  transform: none !important;\n  position: relative !important;\n  left: auto !important;\n  top: auto !important;\n}\n\n.clean-chat-window {\n  height: 188px !important;\n  max-height: 188px !important;\n  overflow-y: auto !important;\n}\n\n.clean-chat-card.minimized {\n  height: 58px !important;\n  max-height: 58px !important;\n}\n\n.clean-chat-card.minimized .clean-chat-window {\n  display: none !important;\n}\n\n.online-chat-composer,\ndiv[data-testid="stForm"]:has(input[aria-label="Online chat"]) {\n  width: 250px !important;\n  max-width: 250px !important;\n  margin-top: 8px !important;\n  margin-bottom: 18px !important;\n  transform: none !important;\n  position: relative !important;\n  left: auto !important;\n  top: auto !important;\n}\n\ndiv[data-testid="stForm"]:has(input[aria-label="Online chat"]) input {\n  width: 100% !important;\n  height: 30px !important;\n  min-height: 30px !important;\n  font-size: 11px !important;\n}\n\ndiv[data-testid="stForm"]:has(input[aria-label="Online chat"]) button {\n  width: 100% !important;\n  height: 32px !important;\n  min-height: 32px !important;\n  font-size: 11px !important;\n  border-radius: 10px !important;\n}\n\n.profile {\n  width: 250px !important;\n  max-width: 250px !important;\n  margin-top: 20px !important;\n}\n\n.clean-chat-actions a {\n  cursor: pointer !important;\n}\n</style>\n', unsafe_allow_html=True)

# final-move-history-boxes-up-only
st.markdown('\n<style>\n/* FINAL: place only saved-brief search + saved-brief card under PROJECT BRIEF HISTORY */\ndiv[data-testid="stTextInput"]:has(input[placeholder="Search saved briefs..."]) {\n  transform: translateY(-335px) !important;\n  margin-bottom: -325px !important;\n  width: 250px !important;\n  max-width: 250px !important;\n}\n\ndiv[data-testid="stTextInput"] input[placeholder="Search saved briefs..."] {\n  width: 250px !important;\n  max-width: 250px !important;\n  height: 34px !important;\n  min-height: 34px !important;\n}\n\n.history-wrap {\n  transform: translateY(-335px) !important;\n  margin-bottom: -325px !important;\n  width: 250px !important;\n  max-width: 250px !important;\n}\n\n.history {\n  width: 250px !important;\n  max-width: 250px !important;\n}\n</style>\n', unsafe_allow_html=True)

# final-tiny-search-input-up-only
st.markdown('\n<style>\n/* FINAL tiny adjustment: move ONLY saved-brief search input slightly upward */\ndiv[data-testid="stTextInput"]:has(input[placeholder="Search saved briefs..."]) {\n  transform: translateY(-352px) !important;\n  margin-bottom: -342px !important;\n  width: 250px !important;\n  max-width: 250px !important;\n}\n\ndiv[data-testid="stTextInput"] input[placeholder="Search saved briefs..."] {\n  width: 250px !important;\n  max-width: 250px !important;\n  height: 34px !important;\n  min-height: 34px !important;\n}\n</style>\n', unsafe_allow_html=True)

# final-gap-between-search-and-saved-card
st.markdown('\n<style>\n/* FINAL tiny adjustment: add gap between saved-brief search and saved-brief card */\n.history-wrap {\n  transform: translateY(-318px) !important;\n  margin-bottom: -308px !important;\n  width: 250px !important;\n  max-width: 250px !important;\n}\n\n.history {\n  width: 250px !important;\n  max-width: 250px !important;\n}\n</style>\n', unsafe_allow_html=True)

# final-exact-history-under-title
st.markdown('\n<style>\n/* FINAL exact adjustment: move ONLY saved brief search + saved card closer under PROJECT BRIEF HISTORY */\ndiv[data-testid="stTextInput"]:has(input[placeholder="Search saved briefs..."]) {\n  transform: translateY(-430px) !important;\n  margin-bottom: -420px !important;\n  width: 250px !important;\n  max-width: 250px !important;\n}\n\ndiv[data-testid="stTextInput"] input[placeholder="Search saved briefs..."] {\n  width: 250px !important;\n  max-width: 250px !important;\n  height: 34px !important;\n  min-height: 34px !important;\n}\n\n.history-wrap {\n  transform: translateY(-396px) !important;\n  margin-bottom: -386px !important;\n  width: 250px !important;\n  max-width: 250px !important;\n}\n\n.history {\n  width: 250px !important;\n  max-width: 250px !important;\n}\n</style>\n', unsafe_allow_html=True)








# final-real-streamlit-theme-css
if st.session_state.get("light_mode", False):
    st.markdown(
        """
        <style>
        .stApp,
        [data-testid="stAppViewContainer"] {
          background: linear-gradient(135deg, #f7f9ff 0%, #eef3ff 55%, #ffffff 100%) !important;
          color: #0f172a !important;
        }

        .hero,
        .workflow-card,
        .brief-card,
        .workflow-panel,
        .workflow-result,
        .history,
        .profile,
        .clean-chat-card {
          background: rgba(255,255,255,.90) !important;
          border-color: rgba(40,60,100,.22) !important;
        }

        .hero-title,
        .workflow-title,
        .brief-title,
        .workflow-card-title,
        .workflow-result-title,
        .history-title,
        .profile-name,
        .clean-chat-title {
          color: #0f172a !important;
        }

        .hero-desc,
        .workflow-card-sub,
        .brief-sub,
        .workflow-result-sub,
        .history span,
        .profile-mail,
        .clean-chat-status {
          color: #475569 !important;
        }

        textarea,
        input {
          background: rgba(255,255,255,.98) !important;
          color: #0f172a !important;
          border-color: rgba(40,60,100,.28) !important;
        }

        input::placeholder,
        textarea::placeholder {
          color: #64748b !important;
        }

        .accent {
          color: #e11d48 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
# end-final-real-streamlit-theme-css

