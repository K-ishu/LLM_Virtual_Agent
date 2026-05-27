from __future__ import annotations

import html
import json
import os
from datetime import datetime
from textwrap import dedent

import streamlit as st

try:
    from app.llm_client import LLMClient
except Exception:
    LLMClient = None


# =========================================================
# Page config
# =========================================================
st.set_page_config(
    page_title="LLM-Powered Virtual Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================
# State
# =========================================================
def now_time() -> str:
    return datetime.now().strftime("%I:%M %p").lstrip("0")


if "project_brief" not in st.session_state:
    # Empty on initial load, as requested.
    st.session_state.project_brief = ""

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "login_open" not in st.session_state:
    st.session_state.login_open = False

if "user_name" not in st.session_state:
    st.session_state.user_name = "Alex Morgan"

if "user_email" not in st.session_state:
    st.session_state.user_email = "alex@example.com"

if "chat_messages" not in st.session_state:
    # Empty chat on first app load.
    st.session_state.chat_messages = []

if "chat_history" not in st.session_state:
    # Saved chat history during the current Streamlit session.
    st.session_state.chat_history = []


# =========================================================
# Helpers
# =========================================================
def ui(markup: str) -> None:
    """Render HTML as real HTML, not as Markdown/code."""
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
        "Answer clearly, practically, and concisely. "
        "If the user writes in Persian, answer in Persian. "
        "Do not return raw JSON unless explicitly requested."
    )

    if LLMClient is None:
        return "LLMClient is not available. Check app.llm_client import."

    try:
        client = LLMClient()
        response = client.chat(system_prompt, prompt)
        return clean_ai_text(getattr(response, "text", response))
    except Exception as exc:
        return f"AI request failed: {exc}"


def submit_prompt(prompt: str) -> None:
    prompt = (prompt or "").strip()
    if not prompt:
        return

    user_msg = {"role": "user", "content": prompt, "time": now_time()}
    st.session_state.chat_messages.append(user_msg)

    with st.spinner("Thinking..."):
        answer = ask_ai(prompt)

    assistant_msg = {"role": "assistant", "content": answer, "time": now_time()}
    st.session_state.chat_messages.append(assistant_msg)

    st.session_state.chat_history.append({
        "question": prompt,
        "answer": answer,
        "time": now_time(),
    })


def login_user(email: str, password: str) -> None:
    email = (email or "").strip()
    if not email:
        st.toast("Please enter an email.", icon="⚠️")
        return

    st.session_state.logged_in = True
    st.session_state.user_email = email
    st.session_state.user_name = email.split("@")[0].replace(".", " ").title()
    st.session_state.login_open = False
    st.toast("Logged in successfully.", icon="✅")


# =========================================================
# CSS
# =========================================================
st.markdown(
    """
<style>
:root {
  --bg: #050914;
  --rail: #07111f;
  --panel: #0b1424;
  --panel2: #0e192c;
  --stroke: rgba(117,142,200,.18);
  --stroke2: rgba(117,142,200,.30);
  --text: #edf4ff;
  --muted: #91a2c0;
  --muted2: #667794;
  --red: #ff4f5f;
  --red2: #b23248;
  --purple: #8c5cff;
  --blue: #3f8cff;
  --cyan: #2dd4bf;
  --green: #22c55e;
  --amber: #f59e0b;
}

html, body, [class*="css"], .stApp {
  font-family: Inter, "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp {
  background:
    radial-gradient(circle at 18% 10%, rgba(27,58,132,0.25), transparent 25%),
    radial-gradient(circle at 76% 8%, rgba(117,58,255,0.13), transparent 24%),
    radial-gradient(circle at 52% 85%, rgba(0,120,255,0.08), transparent 32%),
    linear-gradient(180deg, #060b15 0%, #050913 36%, #05070e 100%);
  color: var(--text);
}

header[data-testid="stHeader"] { background: transparent !important; }
#MainMenu, footer { visibility: hidden; }
[data-testid="stSidebar"], section[data-testid="stSidebar"] { display: none !important; }

.block-container {
  max-width: 1700px !important;
  padding: 14px 18px 34px 18px !important;
}

div[data-testid="column"] {
  min-width: 0;
}

/* Native widgets */
.stTextArea textarea,
.stTextInput input,
.stTextInput textarea {
  background: rgba(8,14,26,.94) !important;
  color: #edf2ff !important;
  border-radius: 12px !important;
  border: 1px solid rgba(120,140,200,.22) !important;
  font-size: 14px !important;
  padding: 14px 16px !important;
  box-shadow: none !important;
}

.stTextArea textarea::placeholder,
.stTextInput input::placeholder {
  color: #7f90b2 !important;
  opacity: 1 !important;
}

.stButton > button,
.stFormSubmitButton > button {
  border-radius: 12px !important;
  border: 1px solid rgba(120,140,200,.20) !important;
  background: linear-gradient(180deg, rgba(12,19,36,.96), rgba(8,14,26,.98)) !important;
  color: #eef4ff !important;
  font-weight: 800 !important;
  min-height: 40px !important;
  box-shadow: none !important;
}

.stButton > button:hover,
.stFormSubmitButton > button:hover {
  border-color: rgba(255,95,110,.55) !important;
  color: white !important;
}

textarea:focus,
input:focus {
  border-color: rgba(255,95,110,.42) !important;
  box-shadow: 0 0 0 1px rgba(255,95,110,.15) !important;
}

/* Sidebar */
.left-rail {
  border-right: 1px solid rgba(255,255,255,.08);
  padding: 18px 16px 20px 4px;
  min-height: calc(100vh - 40px);
}

.brand {
  display: flex;
  gap: 12px;
  align-items: center;
  margin: 8px 0 24px 0;
}

.logo {
  width: 48px;
  height: 48px;
  border-radius: 15px;
  display: grid;
  place-items: center;
  font-size: 25px;
  color: #ff6f7d;
  background: linear-gradient(180deg, rgba(255,95,95,.22), rgba(255,95,95,.05));
  border: 1px solid rgba(255,120,120,.35);
  box-shadow: 0 0 28px rgba(255,80,120,.15);
}

.brand-title {
  font-size: 16px;
  font-weight: 900;
  line-height: 1.1;
}

.brand-sub {
  font-size: 12px;
  color: #b7c3dd;
  margin-top: 3px;
}

.nav {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 13px 15px;
  border-radius: 14px;
  border: 1px solid rgba(255,110,120,.42);
  background: linear-gradient(90deg, rgba(255,90,90,.14), rgba(255,90,90,.04));
  font-weight: 800;
  margin-bottom: 24px;
}

.section {
  font-size: 11px;
  letter-spacing: .11em;
  color: #7e8aa8;
  text-transform: uppercase;
  font-weight: 900;
  margin: 18px 0 10px;
}

.module,
.history,
.profile,
.login-card {
  border: 1px solid rgba(120,140,200,.18);
  background: linear-gradient(180deg, rgba(11,19,38,.85), rgba(8,15,30,.92));
  border-radius: 12px;
  padding: 10px 12px;
  margin-bottom: 10px;
  color: #dfe8ff;
}

.module-title {
  display: flex;
  align-items: center;
  font-size: 13px;
  color: white;
  font-weight: 850;
}

.num {
  display: inline-grid;
  place-items: center;
  width: 22px;
  height: 22px;
  margin-right: 8px;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 900;
  background: rgba(95,120,255,.15);
  color: #c9d3ff;
  border: 1px solid rgba(120,140,255,.35);
}

.module-sub,
.history span,
.profile-mail {
  font-size: 11px;
  color: #8ea0c6;
}

.search {
  border: 1px solid rgba(120,140,200,.18);
  background: rgba(10,17,31,.90);
  border-radius: 12px;
  padding: 10px 12px;
  color: #8292b7;
  font-size: 12px;
  margin-bottom: 12px;
}

.history.active {
  border-color: rgba(255,95,95,.40);
  background: linear-gradient(180deg, rgba(120,25,35,.28), rgba(15,18,35,.95));
}

.history-title {
  font-size: 13px;
  color: white;
  font-weight: 700;
  margin-bottom: 3px;
}

.profile {
  margin-top: 18px;
  border-radius: 14px;
  display: flex;
  gap: 10px;
  align-items: center;
}

.avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #6e85ff, #ff6f8f);
  color: white;
  font-weight: 900;
}

.profile-name {
  font-size: 13px;
  font-weight: 800;
}

/* Hero */
.hero {
  border-radius: 24px;
  border: 1px solid rgba(120,140,200,.16);
  overflow: hidden;
  display: grid;
  grid-template-columns: 42% 58%;
  min-height: 292px;
  background:
    radial-gradient(circle at 30% 30%, rgba(40,90,255,.18), transparent 28%),
    radial-gradient(circle at 70% 30%, rgba(255,60,120,.08), transparent 22%),
    linear-gradient(180deg, rgba(10,19,38,.96), rgba(8,13,26,.98));
  box-shadow: 0 10px 50px rgba(0,0,0,.25), inset 0 0 0 1px rgba(255,255,255,.02);
}

.hero-left {
  position: relative;
  display: grid;
  place-items: center;
  min-height: 292px;
  border-right: 1px solid rgba(255,255,255,.05);
  background:
    radial-gradient(circle at 50% 43%, rgba(255,91,126,.30), transparent 14%),
    radial-gradient(circle at 50% 43%, rgba(111,92,255,.28), transparent 25%),
    radial-gradient(circle at center, rgba(80,130,255,.20), transparent 30%),
    linear-gradient(180deg, rgba(8,16,34,.90), rgba(8,16,34,.98));
}

.hero-left::after {
  content: "";
  position: absolute;
  bottom: 31px;
  width: 210px;
  height: 40px;
  background: radial-gradient(circle, rgba(141,72,255,.50), rgba(70,60,255,.10), transparent 75%);
  filter: blur(10px);
}

.hero-left::before {
  content: "";
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,.025) 1px, transparent 1px);
  background-size: 34px 34px;
  opacity: .55;
}

.brain-glow {
  position: relative;
  width: 240px;
  height: 190px;
  display: grid;
  place-items: center;
  z-index: 2;
}

.brain-glow::before {
  content: "";
  position: absolute;
  width: 245px;
  height: 170px;
  border-radius: 50%;
  background:
    radial-gradient(circle, rgba(255,92,132,.20), transparent 62%),
    radial-gradient(circle, rgba(125,92,255,.26), transparent 70%);
  filter: blur(12px);
}

.brain {
  position: relative;
  font-size: 116px;
  z-index: 3;
  filter:
    drop-shadow(0 0 20px rgba(255,90,130,.32))
    drop-shadow(0 0 34px rgba(120,95,255,.22));
}

.hero-right {
  position: relative;
  padding: 34px 38px;
}

.hero-icons {
  position: absolute;
  top: 25px;
  right: 25px;
  display: flex;
  gap: 18px;
  font-size: 22px;
}

.new-project {
  position: absolute;
  top: 20px;
  right: 92px;
  background: linear-gradient(180deg, #ff6f61, #ff5a4f);
  color: white;
  padding: 11px 16px;
  border-radius: 14px;
  font-size: 14px;
  font-weight: 900;
  box-shadow: 0 10px 28px rgba(255,90,90,.22);
}

.hero-title {
  margin-top: 40px;
  font-size: 35px;
  line-height: 1.08;
  font-weight: 950;
}

.hero-title .accent {
  color: #ff5972;
}

.hero-desc {
  margin-top: 12px;
  max-width: 590px;
  font-size: 14px;
  line-height: 1.65;
  color: #b7c4df;
}

.badges {
  margin-top: 24px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.badge {
  border: 1px solid rgba(120,140,200,.22);
  background: rgba(8,14,28,.72);
  border-radius: 999px;
  padding: 10px 14px;
  font-size: 13px;
}

/* Workflow */
.workflow {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 14px;
}

.card {
  border: 1px solid rgba(120,140,200,.18);
  background: linear-gradient(180deg, rgba(13,20,38,.92), rgba(9,15,28,.98));
  border-radius: 18px;
  min-height: 104px;
  padding: 16px 18px;
}

.card-num {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: inline-grid;
  place-items: center;
  font-weight: 900;
  margin-bottom: 10px;
  border: 1px solid rgba(255,255,255,.16);
}

.c1 { background: rgba(255,104,76,.22); color: #ff8d74; }
.c2 { background: rgba(180,85,255,.22); color: #c58cff; }
.c3 { background: rgba(158,85,255,.22); color: #bf98ff; }
.c4 { background: rgba(90,140,255,.22); color: #83adff; }
.c5 { background: rgba(255,180,70,.22); color: #ffcf7f; }
.c6 { background: rgba(80,210,200,.22); color: #7de8dc; }

.card-title {
  font-size: 14px;
  font-weight: 900;
  margin-bottom: 5px;
}

.card-sub {
  font-size: 12px;
  color: #93a5cb;
  line-height: 1.45;
}

/* Brief */
.brief-card {
  margin-top: 18px;
  border: 1px solid rgba(120,140,200,.16);
  border-radius: 18px 18px 0 0;
  background: linear-gradient(180deg, rgba(11,19,38,.88), rgba(8,14,26,.98));
  padding: 18px 18px 10px;
}

.brief-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.brief-title {
  font-size: 18px;
  font-weight: 900;
}

.brief-sub {
  font-size: 13px;
  color: #a3b2d0;
  margin-top: 2px;
}

.brief-btn {
  border: 1px solid rgba(255,110,120,.38);
  color: #ff8f98;
  background: rgba(255,75,75,.06);
  border-radius: 14px;
  padding: 10px 14px;
  font-weight: 800;
  font-size: 13px;
}

/* Tabs */
.tabs {
  margin-top: 14px;
  display: flex;
  gap: 26px;
  border-bottom: 1px solid rgba(255,255,255,.08);
  padding-bottom: 10px;
}

.tab {
  color: #c8d4ef;
  font-size: 13px;
  font-weight: 800;
  position: relative;
}

.tab.active {
  color: white;
}

.tab.active::after {
  content: "";
  position: absolute;
  left: 0;
  bottom: -11px;
  width: 100%;
  height: 2px;
  border-radius: 999px;
  background: #ff586a;
}

/* Chat */
.chat-layout {
  margin-top: 16px;
  display: grid;
  grid-template-columns: 1fr 330px;
  gap: 18px;
}

.chat {
  border: 1px solid rgba(120,140,200,.16);
  border-radius: 22px;
  background:
    radial-gradient(circle at 70% 60%, rgba(255,85,130,.06), transparent 26%),
    radial-gradient(circle at 35% 15%, rgba(60,120,255,.10), transparent 28%),
    linear-gradient(180deg, rgba(12,20,40,.94), rgba(8,14,26,.98));
  padding: 16px 18px;
  min-height: 360px;
}

.chat-title {
  font-size: 14px;
  font-weight: 900;
  margin-bottom: 4px;
}

.chat-desc {
  font-size: 12px;
  color: #96a8cd;
  margin-bottom: 18px;
}

.messages {
  min-height: 0;
  max-height: 320px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.msg-row {
  display: flex;
  width: 100%;
}

.msg-row.user {
  justify-content: flex-end;
}

.bubble {
  max-width: 64%;
  padding: 16px 18px;
  border-radius: 20px;
  font-size: 14px;
  line-height: 1.7;
  box-shadow: 0 10px 25px rgba(0,0,0,.18);
}

.bubble.user {
  background: linear-gradient(180deg, rgba(172,56,78,.96), rgba(150,45,65,.96));
  border: 1px solid rgba(255,110,130,.25);
  color: #fff5f6;
  border-top-right-radius: 10px;
}

.bubble.assistant {
  background:
    radial-gradient(circle at 80% 20%, rgba(155,90,255,.10), transparent 30%),
    linear-gradient(180deg, rgba(18,28,52,.96), rgba(12,20,36,.98));
  border: 1px solid rgba(120,140,200,.20);
  color: #eff5ff;
  border-top-left-radius: 10px;
}

.assistant-wrap {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.mini-brain {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: rgba(255,70,110,.12);
  color: #ff708a;
  border: 1px solid rgba(255,120,150,.25);
  flex-shrink: 0;
  margin-top: 4px;
}

.msg-time {
  font-size: 11px;
  color: #7f92bc;
  margin-top: 7px;
}

.msg-time.right {
  text-align: right;
}

.actions {
  margin-top: 10px;
  color: #9fb0d6;
  display: flex;
  gap: 14px;
  font-size: 12px;
}

.composer {
  margin-top: 10px;
  border: 1px solid rgba(120,140,200,.18);
  border-radius: 18px;
  background: rgba(9,16,31,.92);
  padding: 10px 12px;
}

.composer-tip {
  margin-top: 8px;
  display: flex;
  justify-content: space-between;
  color: #798db5;
  font-size: 11px;
}

/* Right side */
.side {
  border: 1px solid rgba(120,140,200,.16);
  border-radius: 22px;
  background: linear-gradient(180deg, rgba(12,19,36,.94), rgba(8,14,26,.98));
  padding: 16px;
  min-height: 470px;
}

.side-title {
  font-size: 14px;
  font-weight: 900;
  margin-bottom: 14px;
}

.recent {
  margin-top: 8px;
  border-top: 1px solid rgba(255,255,255,.06);
  padding-top: 10px;
}

.recent-row {
  display: flex;
  justify-content: space-between;
  color: #d7e2ff;
  font-size: 12px;
  padding: 10px 2px;
}

.recent-time {
  color: #7f93bc;
  white-space: nowrap;
  margin-left: 10px;
}

@media (max-width: 1400px) {
  .workflow { grid-template-columns: repeat(3, 1fr); }
  .chat-layout { grid-template-columns: 1fr; }
}

@media (max-width: 1100px) {
  .left-rail { display: none; }
  .hero { grid-template-columns: 1fr; }
}
</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# Layout
# =========================================================
left, main = st.columns([0.18, 0.82], gap="large")


# -------------------------
# Left rail: real login/profile controls
# -------------------------
with left:
    ui("""
    <div class="left-rail">
      <div class="brand">
        <div class="logo">🧠</div>
        <div>
          <div class="brand-title">LLM ASSISTANT</div>
          <div class="brand-sub">for Software Engineering</div>
        </div>
      </div>

      <div class="nav">⌘ Dashboard</div>

      <div class="section">Workflow Modules</div>
      <div class="module"><div class="module-title"><span class="num">1</span>Requirements</div><div class="module-sub">Generate FR/NFR</div></div>
      <div class="module"><div class="module-title"><span class="num">2</span>Review</div><div class="module-sub">Find ambiguity</div></div>
      <div class="module"><div class="module-title"><span class="num">3</span>Tests</div><div class="module-sub">Create test cases</div></div>
      <div class="module"><div class="module-title"><span class="num">4</span>Architecture</div><div class="module-sub">Suggest components</div></div>
      <div class="module"><div class="module-title"><span class="num">5</span>Code</div><div class="module-sub">Review quality</div></div>
      <div class="module"><div class="module-title"><span class="num">6</span>Security</div><div class="module-sub">Defensive risks</div></div>

      <div class="section">History</div>
      <div class="search">Search conversations 🔎</div>
      <div class="history active"><div class="history-title">Alzheimer's Safety App</div><span>2m ago</span></div>
      <div class="history"><div class="history-title">Medication Reminder System</div><span>1d ago</span></div>
      <div class="history"><div class="history-title">Telehealth Platform</div><span>2d ago</span></div>
      <div class="history"><div class="history-title">E-Commerce Checkout</div><span>3d ago</span></div>
      <div class="history"><div class="history-title">IoT Device Monitor</div><span>4d ago</span></div>
    </div>
    """)

    if st.session_state.logged_in:
        ui(f"""
        <div class="profile">
          <div class="avatar">{html.escape(st.session_state.user_name[:1].upper())}</div>
          <div>
            <div class="profile-name">{html.escape(st.session_state.user_name)}</div>
            <div class="profile-mail">{html.escape(st.session_state.user_email)}</div>
          </div>
        </div>
        """)
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
    else:
        ui("""
        <div class="profile">
          <div class="avatar">?</div>
          <div>
            <div class="profile-name">Guest User</div>
            <div class="profile-mail">Not logged in</div>
          </div>
        </div>
        """)
        if st.button("Login", use_container_width=True):
            st.session_state.login_open = not st.session_state.login_open

        if st.session_state.login_open:
            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("Email", placeholder="alex@example.com")
                password = st.text_input("Password", placeholder="password", type="password")
                login = st.form_submit_button("Sign in", use_container_width=True)
                if login:
                    login_user(email, password)
                    st.rerun()


# -------------------------
# Main area
# -------------------------
with main:
    provider = html.escape(os.getenv("LLM_PROVIDER", "OpenAI"))
    model = html.escape(os.getenv("OPENAI_MODEL", "DeepSeek-V3.1"))

    ui(f"""
    <section class="hero">
      <div class="hero-left">
        <div class="brain-glow"><div class="brain">🧠</div></div>
      </div>
      <div class="hero-right">
        <div class="hero-icons">☼ 🔔</div>
        <div class="new-project">⊕ New Project</div>
        <div class="hero-title"><span class="accent">LLM-Powered</span><br>Virtual Assistant for<br>Software Engineering</div>
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

    <section class="workflow">
      <div class="card"><div class="card-num c1">1</div><div class="card-title">Requirements</div><div class="card-sub">Generate FR/NFR</div></div>
      <div class="card"><div class="card-num c2">2</div><div class="card-title">Review</div><div class="card-sub">Find ambiguity & missing criteria</div></div>
      <div class="card"><div class="card-num c3">3</div><div class="card-title">Tests</div><div class="card-sub">Create structured test cases</div></div>
      <div class="card"><div class="card-num c4">4</div><div class="card-title">Architecture</div><div class="card-sub">Suggest components & data flow</div></div>
      <div class="card"><div class="card-num c5">5</div><div class="card-title">Code</div><div class="card-sub">Review code quality and security</div></div>
      <div class="card"><div class="card-num c6">6</div><div class="card-title">Security</div><div class="card-sub">Generate defensive risk scenarios</div></div>
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
    """)

    st.text_area(
        "Project Brief",
        key="project_brief",
        height=86,
        placeholder="Describe your software project here...",
        label_visibility="collapsed",
    )




    st.markdown("### AI Workflow")

    action = st.radio(
        "Choose action",
        [
            "General Chat",
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

    if st.button("Run AI workflow", use_container_width=True):
        brief = st.session_state.get("project_brief", "").strip()

        if action != "General Chat" and not brief:
            st.warning("Write a project brief first.")
        else:
            if action == "Requirements":
                prompt = f"""Generate professional software requirements for this project brief:

{brief}

Return:
- Assumptions
- Clarification questions
- Functional requirements
- Non-functional requirements
- Risks"""

            elif action == "Review":
                prompt = f"""Review this project brief or requirements:

{brief}

Find:
- Ambiguity
- Missing acceptance criteria
- Security/privacy gaps
- Contradictions
- Unverifiable statements

Return:
- Review summary
- Issues
- Recommendations
- Improved requirements"""

            elif action == "Test Cases":
                prompt = f"""Generate professional test cases for this project:

{brief}

Return:
- Test case ID
- Priority
- Preconditions
- Steps
- Expected result
- Requirement covered"""

            elif action == "Architecture":
                prompt = f"""Suggest a high-level software architecture for this project:

{brief}

Return:
- Architecture style
- Components
- Data flow
- Technology stack
- Deployment view
- Security considerations"""

            elif action == "Code Analysis":
                prompt = f"""Analyze this code or technical description:

{brief}

Return:
- Summary
- Detected language/technology
- Quality findings
- Security findings
- Recommended improvements"""

            elif action == "Security":
                prompt = f"""Generate defensive security and unsafe scenario analysis for this project:

{brief}

Return:
- Potential abuse cases
- Security risks
- Privacy risks
- Mitigations
- Validation tests"""

            else:
                prompt = brief or "How can I improve this software engineering project?"

            submit_prompt(prompt)
            st.rerun()


    chat_col, side_col = st.columns([0.74, 0.26], gap="large")

    with chat_col:
        message_blocks = []

        if not st.session_state.chat_messages:
            message_blocks.append("""
            <div style="height: 230px; display: flex; align-items: center; justify-content: center; color: #7f90b2; text-align: center;">
              <div>
                <div style="font-size: 34px; margin-bottom: 10px;">??</div>
                <div style="font-size: 16px; font-weight: 800; color: #dce7ff;">Start a new AI conversation</div>
                <div style="font-size: 13px; margin-top: 6px;">Ask about requirements, testing, architecture, code review, or project documentation.</div>
              </div>
            </div>
            """)

        for msg in st.session_state.chat_messages[-8:]:
            role = msg.get("role", "assistant")
            content = html.escape(msg.get("content", "")).replace("\\n", "<br>")
            t = html.escape(msg.get("time", ""))

            if role == "user":
                message_blocks.append(f"""
                <div class="msg-row user">
                  <div>
                    <div class="bubble user">{content}</div>
                    <div class="msg-time right">{t} ??</div>
                  </div>
                </div>
                """)
            else:
                message_blocks.append(f"""
                <div class="msg-row assistant">
                  <div class="assistant-wrap">
                    <div class="mini-brain">??</div>
                    <div>
                      <div class="bubble assistant">
                        {content}
                        <div class="actions">?? ?? ??</div>
                      </div>
                      <div class="msg-time">{t}</div>
                    </div>
                  </div>
                </div>
                """)

        ui(f"""
        <section class="chat">
          <div class="chat-title">General AI Chat</div>
          <div class="chat-desc">Ask general questions, request explanations, translations, or SE guidance.</div>
          <div class="messages">
            {''.join(message_blocks)}
          </div>
        </section>
        """)

        ui('<div class="composer">')
        with st.form("chat_form", clear_on_submit=True):
            prompt = st.text_input(
                "Ask",
                placeholder="Ask anything about the project or software engineering...",
                label_visibility="collapsed",
            )

            send = st.form_submit_button("Send", use_container_width=True)

            if send and prompt.strip():
                submit_prompt(prompt)
                st.rerun()

        ui("""
          <div class="composer-tip">
            <div>Tip: write your message and press Send</div>
            <div>Real AI chat connected here</div>
          </div>
        </div>
        """)

    with side_col:
        ui("""
        <aside class="side">
          <div class="side-title">✨ Suggestions</div>
        """)

        suggestions = [
            "List the functional requirements",
            "Identify potential risks",
            "Suggest system architecture",
            "Create test cases for login",
            "Review data privacy concerns",
        ]
        for idx, suggestion in enumerate(suggestions):
            if st.button(f"{suggestion}  →", key=f"suggestion_{idx}", use_container_width=True):
                submit_prompt(suggestion)
                st.rerun()

        ui("""
          <div class="side-title" style="margin-top:18px;">◔ Recent actions</div>
          <div class="recent">
            <div class="recent-row"><span>Explain authentication flow</span><span class="recent-time">2m ago</span></div>
            <div class="recent-row"><span>Translate feature spec</span><span class="recent-time">1h ago</span></div>
            <div class="recent-row"><span>Generate test cases for API</span><span class="recent-time">Yesterday</span></div>
          </div>
        </aside>
        """)
