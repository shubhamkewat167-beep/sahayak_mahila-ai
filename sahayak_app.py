import streamlit as st
from google import genai
from google.genai import types

# =========================================================
# SAHAYAK AI — VOICE-FIRST MULTILINGUAL GOVERNMENT GUIDE
# =========================================================

st.set_page_config(
    page_title="Sahayak AI",
    page_icon="🎙️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# -------------------------
# Styling
# -------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

header, footer {visibility:hidden;}
.stApp {
    background:
      radial-gradient(circle at 50% 0%, rgba(255,255,255,.95), transparent 38%),
      linear-gradient(145deg,#fbf7f1 0%,#f4e9dd 55%,#eee0d2 100%);
    color:#24211f;
    font-family:'Plus Jakarta Sans',sans-serif;
}
.block-container {
    max-width: 760px;
    padding-top: 2.5rem;
    padding-bottom: 3rem;
}
.brand {text-align:center;margin-bottom:1.5rem;}
.logo {
    width:68px;height:68px;border-radius:50%;margin:0 auto 1rem;
    display:flex;align-items:center;justify-content:center;
    font-size:2rem;
    background:linear-gradient(145deg,#ff7657,#e9583a);
    box-shadow:0 12px 28px rgba(220,83,52,.24);
}
.title {font-size:2rem;font-weight:700;letter-spacing:-.04em;}
.subtitle {color:#77706a;font-size:.92rem;margin-top:.35rem;}

.sahayak-card {
    background:rgba(255,255,255,.78);
    border:1px solid rgba(255,255,255,.95);
    border-radius:26px;
    padding:1.25rem 1.35rem;
    box-shadow:0 14px 35px rgba(88,58,40,.07);
    margin:1rem 0;
}
.sahayak-label {
    font-size:.78rem;font-weight:700;color:#6d665f;
    margin-bottom:.55rem;
}
.sahayak-text {font-size:1.05rem;line-height:1.65;}
.user-bubble {
    background:#27252d;color:white;border-radius:22px 22px 7px 22px;
    padding:1rem 1.1rem;margin:.8rem 0 1rem auto;
    max-width:85%;font-size:.95rem;
}
.progress-wrap {margin:1.2rem 0;}
.progress-label {
    display:flex;justify-content:space-between;
    color:#746d67;font-size:.78rem;margin-bottom:.45rem;
}
.progress {
    height:7px;background:#e7ddd3;border-radius:99px;overflow:hidden;
}
.progress > div {
    height:100%;border-radius:99px;
    background:linear-gradient(90deg,#ff7657,#e9583a);
}
.small-note {color:#817971;font-size:.78rem;text-align:center;margin-top:.7rem;}
.stButton > button {
    border-radius:16px !important;
    border:1px solid #e3d8ce !important;
    background:rgba(255,255,255,.9) !important;
    color:#292522 !important;
    min-height:48px;
    font-weight:600 !important;
}
.stButton > button:hover {
    border-color:#ed6848 !important;
    color:#d95437 !important;
}
.primary-btn > button {
    background:linear-gradient(135deg,#ff7657,#e9583a) !important;
    color:white !important;border:0 !important;
}
div[data-testid="stAudioInput"] {
    background:rgba(255,255,255,.72);
    border-radius:20px;padding:.5rem;
}
hr {border-color:#e8ddd3;}
</style>
""", unsafe_allow_html=True)

# -------------------------
# Session state
# -------------------------
defaults = {
    "stage": "language",
    "lang": None,
    "service": None,
    "messages": [],
    "answers": {},
    "eligibility_index": 0,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# -------------------------
# Gemini client
# -------------------------
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except Exception:
    api_key = ""

if not api_key:
    st.error("Add GOOGLE_API_KEY to Streamlit Secrets before running the app.")
    st.stop()

client = genai.Client(api_key=api_key)
MODEL = "gemini-3.8-flash"

LANGUAGES = {
    "Tamil": "தமிழ்",
    "Telugu": "తెలుగు",
    "Hindi": "हिंदी",
    "English": "English",
    "Bengali": "বাংলা",
    "Marathi": "मराठी",
}

# -------------------------
# Helpers
# -------------------------
def ask_gemini(prompt, audio=None):
    """Use Gemini to understand either text or recorded speech."""
    try:
        contents = [prompt]
        if audio is not None:
            contents.append(
                types.Part.from_bytes(
                    data=audio.getvalue(),
                    mime_type=audio.type or "audio/wav",
                )
            )
        response = client.models.generate_content(
            model=MODEL,
            contents=contents,
        )
        return response.text.strip()
    except Exception as e:
        return f"ERROR: {e}"

def detect_language_from_audio(audio):
    prompt = """Listen to this short recording.
Identify the language the speaker is using or the language they are
requesting.

Return ONLY one of:
Tamil, Telugu, Hindi, English, Bengali, Marathi

If the speaker says something like "I prefer Telugu", return Telugu.
Do not explain anything."""
    result = ask_gemini(prompt, audio)
    for lang in LANGUAGES:
        if lang.lower() in result.lower():
            return lang
    return None

def understand_intent(audio, text=None):
    prompt = """You are the intent detector for Sahayak AI.
The user is a first-time digital user in India.
Classify the user's request into ONE of:
UJJWALA, OTHER, UNCLEAR

UJJWALA means the user wants an LPG/gas connection, cooking gas,
Ujjwala scheme, or help getting a gas cylinder connection.

Return ONLY the category name."""
    if text:
        prompt += f"\nUser text: {text}"
        result = ask_gemini(prompt)
    else:
        result = ask_gemini(prompt, audio)
    if "UJJWALA" in result.upper():
        return "UJJWALA"
    if "OTHER" in result.upper():
        return "OTHER"
    return "UNCLEAR"

def answer_in_language(question, audio):
    prompt = f"""You are Sahayak AI.
The user speaks {st.session_state.lang}.
Understand her answer to this question:

QUESTION:
{question}

Return a VERY SHORT English interpretation of the answer.
Do not add explanations. Do not invent information."""
    return ask_gemini(prompt, audio)

def reset():
    for k, v in defaults.items():
        st.session_state[k] = v
    st.rerun()

# -------------------------
# Header
# -------------------------
st.markdown("""
<div class="brand">
  <div class="logo">🎙️</div>
  <div class="title">Sahayak AI <span style="font-weight:500;">(सहायक)</span></div>
  <div class="subtitle">Your voice · Your language · Your guide</div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# STAGE 1 — LANGUAGE
# =========================================================
if st.session_state.stage == "language":

    st.markdown("""
    <div class="sahayak-card">
      <div class="sahayak-label">👋 Sahayak says</div>
      <div class="sahayak-text">
        Hello! I can help you in your own language.<br><br>
        Are you comfortable with <b>Tamil</b>?<br>
        If you prefer another language, simply say its name.
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🎙️ Speak naturally")
    st.caption('Try saying: “I prefer Telugu” · “Hindi” · “தமிழ் வேண்டும்”')

    audio = st.audio_input("Tap the microphone and speak")

    if audio:
        with st.spinner("Sahayak is listening…"):
            detected = detect_language_from_audio(audio)

        if detected:
            st.session_state.lang = detected
            st.session_state.messages.append({
                "role": "user",
                "content": f"Language selected: {detected}"
            })
            st.session_state.stage = "intent"
            st.rerun()
        else:
            st.warning("I couldn't identify the language. Please try again.")

    st.markdown('<div class="small-note">Or choose your language</div>',
                unsafe_allow_html=True)

    cols = st.columns(3)
    for i, lang in enumerate(LANGUAGES):
        with cols[i % 3]:
            if st.button(f"{LANGUAGES[lang]}  {lang}", key=f"lang_{lang}"):
                st.session_state.lang = lang
                st.session_state.stage = "intent"
                st.rerun()

# =========================================================
# STAGE 2 — WHAT DO YOU NEED?
# =========================================================
elif st.session_state.stage == "intent":

    st.markdown(f"""
    <div class="sahayak-card">
      <div class="sahayak-label">🌿 Sahayak · {st.session_state.lang}</div>
      <div class="sahayak-text">
        How can I help you today?<br><br>
        <span style="color:#77706a;font-size:.9rem;">
        You can simply tell me what you need. You don't need to know
        the name of a government scheme.
        </span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    audio = st.audio_input("🎙️ Tell Sahayak what you need", key="intent_audio")

    if audio:
        with st.spinner("Understanding…"):
            intent = understand_intent(audio=audio)

        if intent == "UJJWALA":
            st.session_state.service = "PM Ujjwala Yojana"
            st.session_state.stage = "confirm"
            st.rerun()
        elif intent == "OTHER":
            st.info("For this prototype, I currently have one complete service flow: LPG connection assistance through PM Ujjwala Yojana.")
        else:
            st.warning("I couldn't understand that clearly. Please try saying what help you need.")

    st.markdown('<div class="small-note">Example: “I need help getting a gas connection.”</div>',
                unsafe_allow_html=True)

# =========================================================
# STAGE 3 — CONFIRM SERVICE
# =========================================================
elif st.session_state.stage == "confirm":

    st.markdown(f"""
    <div class="sahayak-card">
      <div class="sahayak-label">🎯 I understood</div>
      <div class="sahayak-text">
        You want help with <b>{st.session_state.service}</b>.
        <br><br>
        I'll ask a few simple questions to check whether you appear
        to meet the eligibility conditions. Is that okay?
      </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Yes, continue", key="yes", type="primary"):
            st.session_state.stage = "eligibility"
            st.session_state.eligibility_index = 0
            st.rerun()
    with c2:
        if st.button("Start over", key="restart"):
            reset()

# =========================================================
# STAGE 4 — ELIGIBILITY
# =========================================================
elif st.session_state.stage == "eligibility":

    questions = [
        ("age", "What is your age?"),
        ("lpg", "Does anyone in your household already have an LPG gas connection?"),
        ("poor", "Would your household be considered a poor or deprived household under the scheme's applicable criteria?"),
    ]

    idx = st.session_state.eligibility_index
    total = len(questions)
    key, question = questions[idx]

    pct = int((idx / total) * 100)

    st.markdown(f"""
    <div class="progress-wrap">
      <div class="progress-label">
        <span>Eligibility check</span>
        <span>{idx + 1} of {total}</span>
      </div>
      <div class="progress"><div style="width:{max(pct,8)}%"></div></div>
    </div>

    <div class="sahayak-card">
      <div class="sahayak-label">🌿 Sahayak · {st.session_state.lang}</div>
      <div class="sahayak-text">{question}</div>
    </div>
    """, unsafe_allow_html=True)

    audio = st.audio_input("🎙️ Tap and answer naturally", key=f"elig_{key}")

    if audio:
        with st.spinner("Understanding your answer…"):
            interpretation = answer_in_language(question, audio)

        # Keep the raw interpretation so the demo can display it.
        st.session_state.answers[key] = interpretation
        st.session_state.messages.append({
            "role": "user",
            "content": interpretation
        })

        if idx + 1 < total:
            st.session_state.eligibility_index += 1
        else:
            st.session_state.stage = "result"
        st.rerun()

    if st.session_state.answers:
        st.markdown("**Information you've shared**")
        for k, v in st.session_state.answers.items():
            st.markdown(f"- `{k}` · {v}")

# =========================================================
# STAGE 5 — RESULT
# =========================================================
elif st.session_state.stage == "result":

    # Simple demo logic. Final government eligibility is always subject
    # to official verification.
    age_text = st.session_state.answers.get("age", "")
    lpg_text = st.session_state.answers.get("lpg", "").lower()
    poor_text = st.session_state.answers.get("poor", "").lower()

    import re
    nums = re.findall(r"\b(\d{1,3})\b", age_text)
    age = int(nums[0]) if nums else None

    age_ok = age is not None and age >= 18
    no_lpg = any(x in lpg_text for x in ["no", "not", "none", "nobody", "doesn't"])
    poor_ok = any(x in poor_text for x in ["yes", "poor", "deprived", "eligible"])

    appears_eligible = age_ok and no_lpg and poor_ok

    if appears_eligible:
        title = "You appear to meet the basic conditions"
        body = ("Based on the information you provided, you appear to meet "
                "the basic eligibility conditions used in this prototype.")
    else:
        title = "Let's review your information"
        body = ("One or more answers may not match the basic conditions "
                "used in this prototype. The official authority will make "
                "the final eligibility decision.")

    st.markdown(f"""
    <div class="sahayak-card" style="text-align:center;padding:2rem 1.3rem;">
      <div style="font-size:2.4rem;">{"🎉" if appears_eligible else "🔎"}</div>
      <div style="font-size:1.25rem;font-weight:700;margin:.7rem 0;">
        {title}
      </div>
      <div style="color:#716a64;line-height:1.6;">{body}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Your answers")
    for k, v in st.session_state.answers.items():
        st.markdown(f"**{k.title()}** · {v}")

    if appears_eligible:
        if st.button("Continue to application help", type="primary"):
            st.session_state.stage = "application"
            st.rerun()

    if st.button("Start again"):
        reset()

# =========================================================
# STAGE 6 — APPLICATION ASSISTANCE
# =========================================================
elif st.session_state.stage == "application":

    st.markdown("""
    <div class="sahayak-card">
      <div class="sahayak-label">📝 Next step</div>
      <div class="sahayak-text">
        Great. I can now help you prepare for the application.
        <br><br>
        For the real government application, you may need documents
        such as identity/KYC information, household details and bank
        details depending on the official requirements.
      </div>
    </div>
    """, unsafe_allow_html=True)

    steps = [
        ("✓", "Eligibility check", "Completed"),
        ("2", "Documents", "Prepare required documents"),
        ("3", "Application", "Continue through the official service"),
        ("4", "Review", "Check everything before submission"),
    ]

    for num, name, desc in steps:
        st.markdown(f"""
        <div class="sahayak-card" style="padding:.9rem 1rem;margin:.55rem 0;">
          <div style="display:flex;gap:12px;align-items:center;">
            <div style="width:34px;height:34px;border-radius:50%;
                        background:#f3e8df;display:flex;align-items:center;
                        justify-content:center;font-weight:700;">{num}</div>
            <div>
              <b>{name}</b>
              <div style="font-size:.78rem;color:#817971;">{desc}</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### Official next step")
    st.info("For a real submission, continue through the official PM Ujjwala Yojana portal. This prototype does not pretend to submit a government application.")

    if st.button("Restart Sahayak"):
        reset()

# -------------------------
# Small footer
# -------------------------
st.markdown(
    '<div class="small-note">Sahayak AI · Voice-first access to essential services</div>',
    unsafe_allow_html=True
)
