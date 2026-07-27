
import streamlit as st
import pdfplumber
import json
import re
import os
import textwrap
from io import BytesIO

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ClauseGuard — AI Financial Document Risk Analyzer",
    page_icon="shield",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown(textwrap.dedent("""
<style>
    @import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap");

    html, body, [class*="css"] {
        font-family: "Inter", sans-serif;
    }

    .main-header {
        text-align: center;
        padding: 1.5rem 0 0.5rem 0;
    }
    .main-header h1 {
        font-size: 2.8rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 0.2rem;
        letter-spacing: -0.5px;
    }
    .main-header p {
        font-size: 1.1rem;
        color: #6b7280;
        margin-top: 0;
    }

    .card {
        background: #ffffff;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.06);
        border: 1px solid #f0f0f5;
        margin-bottom: 1.2rem;
    }

    .risk-gauge-container {
        text-align: center;
        padding: 1rem;
    }
    .risk-score-number {
        font-size: 3.5rem;
        font-weight: 700;
        line-height: 1;
    }
    .risk-label {
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 0.5rem;
    }

    .severity-high {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }
    .severity-medium {
        background-color: #fef3c7;
        color: #92400e;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }
    .severity-low {
        background-color: #d1fae5;
        color: #065f46;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }

    .recommendation-item {
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        padding: 0.75rem 0;
        border-bottom: 1px solid #f3f4f6;
    }
    .recommendation-item:last-child {
        border-bottom: none;
    }

    .stButton>button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    .icon-inline {
        display: inline-flex;
        align-items: center;
        vertical-align: middle;
        margin-right: 6px;
    }

    div[data-testid="stSidebarUserContent"] {
        padding-top: 1rem;
    }
</style>
"""), unsafe_allow_html=True)

# ── Line Art Icons (SVG) ─────────────────────────────────────────────────────
ICONS = {
    "shield": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    "file_text": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><line x1="10" y1="9" x2="8" y2="9"/></svg>',
    "alert_triangle": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    "check_circle": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
    "clipboard": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg>',
    "key": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/></svg>',
    "search": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
    "upload": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>',
    "lock": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
    "check": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
    "activity": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
    "code": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>',
    "info": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
    "flag": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/></svg>',
}

# ── Sample Documents ─────────────────────────────────────────────────────────
SAMPLE_RISKY_INVOICE = """
INVOICE #INV-2024-8847

Vendor: Apex Global Solutions Ltd.
Date: July 15, 2024
Amount Due: $147,500.00

Payment Terms:
- Full payment due within 3 business days of invoice date.
- Late fees: 15% per week compounded weekly.
- Payment must be made via wire transfer to an offshore account (IBAN: XK8932...).
- No refunds, chargebacks, or disputes permitted under any circumstances.
- Vendor reserves the right to unilaterally modify terms without notice.
- Goods are "as-is" with no warranty, express or implied.
- Jurisdiction: Courts of [Undisclosed Offshore Territory].

Description:
Consulting services — Strategic advisory (vague scope, no deliverables defined).
"""

SAMPLE_CLEAN_CONTRACT = """
SERVICE AGREEMENT #SA-2024-1122

Between: TechFlow Inc. (Client) and CloudSecure LLC (Provider)
Effective Date: August 1, 2024

Scope of Services:
CloudSecure shall provide managed cloud infrastructure services, including:
- 24/7 monitoring and alerting
- Monthly security patch management
- Quarterly performance reports
- 99.9% uptime SLA with pro-rata credits for downtime

Payment Terms:
- Monthly fee: $4,500, invoiced on the 1st of each month
- Net-30 payment terms
- Late fee: 1.5% per month on overdue balances (capped at 5%)

Termination:
Either party may terminate with 60 days written notice. Upon termination,
CloudSecure shall return all client data within 14 business days.

Liability:
Provider's liability is limited to 12 months of fees paid. Both parties maintain
appropriate insurance coverage.

Governing Law: State of California, USA.
"""

# ── Helper Functions ─────────────────────────────────────────────────────────

def extract_text_from_pdf(uploaded_file):
    """Extract text from an uploaded PDF file using pdfplumber."""
    text = ""
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        st.error(f"Failed to extract PDF text: {e}")
        return None
    return text.strip()


def strip_markdown_fences(text):
    """Remove markdown code fences from JSON response."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def call_gemini_api(document_text):
    """Send document text to Gemini API and return parsed JSON."""
    try:
        import google.generativeai as genai
    except ImportError:
        st.error("The `google-generativeai` package is not installed. Run: `pip install google-generativeai`")
        return None

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        st.error("GEMINI_API_KEY environment variable is not set. Please set it before running the app, or paste it in the sidebar.")
        return None

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-3.5-flash")

    system_prompt = (
        "You are ClauseGuard, an expert AI financial document risk analyzer. "
        "Analyze the provided document and return ONLY a valid JSON object with no markdown formatting, "
        "no explanations, and no extra text. The JSON must strictly follow this schema:\n"
        "{\n"
        '  "risk_score": <integer 0-100, where higher means riskier>,\n'
        '  "summary": "<2-3 sentence plain English summary>",\n'
        '  "key_terms": ["<important term>", "<another term>", ...],\n'
        '  "red_flags": [\n'
        '    {"issue": "<description>", "severity": "high|medium|low"},\n'
        '    ...\n'
        '  ],\n'
        '  "recommendations": ["<actionable recommendation>", "<another recommendation>", ...]\n'
        "}\n"
        "Be thorough, objective, and focus on financial and legal risks."
    )

    try:
        response = model.generate_content(
            contents=[
                {"role": "user", "parts": [system_prompt + "\n\nAnalyze this document:\n\n" + document_text]}
            ],
            generation_config={ "temperature": 0.1, "max_output_tokens": 4096, "response_mime_type": "application/json",},
        )
        raw_text = response.text
        clean_json = strip_markdown_fences(raw_text)
        parsed = json.loads(clean_json)
        return parsed
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse Gemini response as JSON: {e}\n\nRaw response:\n{raw_text[:500]}")
        return None
    except Exception as e:
        st.error(f"Gemini API call failed: {e}")
        return None


def get_risk_color(score):
    """Return a color hex and label based on risk score."""
    if score <= 33:
        return "#10b981", "Low Risk", "#d1fae5"
    elif score <= 66:
        return "#f59e0b", "Moderate Risk", "#fef3c7"
    else:
        return "#ef4444", "High Risk", "#fee2e2"


def render_gauge(score):
    """Render a custom HTML/CSS gauge for the risk score."""
    color, label, bg = get_risk_color(score)
    html = textwrap.dedent(f'''
    <div class="card">
        <div class="risk-gauge-container">
            <div class="risk-score-number" style="color: {color};">{score}</div>
            <div class="risk-label" style="color: {color};">{label}</div>
            <div style="margin-top: 1rem;">
                <div style="width: 100%; height: 12px; background: #e5e7eb; border-radius: 999px; overflow: hidden;">
                    <div style="width: {score}%; height: 100%; background: {color}; border-radius: 999px; transition: width 0.8s ease;"></div>
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: 4px; font-size: 0.7rem; color: #9ca3af;">
                    <span>Safe</span>
                    <span>Caution</span>
                    <span>Critical</span>
                </div>
            </div>
        </div>
    </div>
    ''')
    st.markdown(html, unsafe_allow_html=True)


def render_summary(summary_text):
    """Render the summary in a styled card."""
    icon = ICONS["clipboard"]
    html = textwrap.dedent(f'''
    <div class="card">
        <h4 style="margin-top: 0; color: #1a1a2e; font-size: 1.1rem;">
            <span class="icon-inline">{icon}</span>Summary
        </h4>
        <p style="color: #4b5563; line-height: 1.6; margin-bottom: 0;">{summary_text}</p>
    </div>
    ''')
    st.markdown(html, unsafe_allow_html=True)


def render_red_flags(red_flags):
    """Render red flags as a styled table with severity badges."""
    icon = ICONS["flag"]
    if not red_flags:
        html = textwrap.dedent(f'''
        <div class="card">
            <h4 style="margin-top: 0; color: #1a1a2e; font-size: 1.1rem;">
                <span class="icon-inline">{icon}</span>Red Flags
            </h4>
            <p style="color: #6b7280;">No red flags detected. This document appears clean.</p>
        </div>
        ''')
        st.markdown(html, unsafe_allow_html=True)
        return

    rows = ""
    for flag in red_flags:
        severity = flag.get("severity", "medium").lower()
        issue = flag.get("issue", "Unnamed issue")
        badge_class = f"severity-{severity}"
        rows += f'<tr style="border-bottom: 1px solid #f3f4f6;"><td style="padding: 0.75rem 0; color: #374151;">{issue}</td><td style="padding: 0.75rem 0; text-align: right;"><span class="{badge_class}">{severity.upper()}</span></td></tr>'

    html = textwrap.dedent(f'''
    <div class="card">
        <h4 style="margin-top: 0; color: #1a1a2e; font-size: 1.1rem;">
            <span class="icon-inline">{icon}</span>Red Flags ({len(red_flags)})
        </h4>
        <table style="width: 100%; border-collapse: collapse;">
            {rows}
        </table>
    </div>
    ''')
    st.markdown(html, unsafe_allow_html=True)


def render_recommendations(recommendations):
    """Render recommendations as a styled checklist."""
    icon = ICONS["check_circle"]
    if not recommendations:
        html = textwrap.dedent(f'''
        <div class="card">
            <h4 style="margin-top: 0; color: #1a1a2e; font-size: 1.1rem;">
                <span class="icon-inline">{icon}</span>Recommendations
            </h4>
            <p style="color: #6b7280;">No specific recommendations at this time.</p>
        </div>
        ''')
        st.markdown(html, unsafe_allow_html=True)
        return

    items = ""
    check_icon = ICONS["check"]
    for rec in recommendations:
        items += f'<div class="recommendation-item"><span style="flex-shrink: 0; margin-top: 2px;">{check_icon}</span><span style="color: #374151;">{rec}</span></div>'

    html = textwrap.dedent(f'''
    <div class="card">
        <h4 style="margin-top: 0; color: #1a1a2e; font-size: 1.1rem;">
            <span class="icon-inline">{icon}</span>Recommendations
        </h4>
        {items}
    </div>
    ''')
    st.markdown(html, unsafe_allow_html=True)


def render_key_terms(key_terms):
    """Render key terms as tags."""
    if not key_terms:
        return
    icon = ICONS["key"]
    tags = ""
    for term in key_terms:
        tags += f'<span style="display: inline-block; background: #f3f4f6; color: #374151; padding: 4px 12px; border-radius: 999px; font-size: 0.8rem; margin: 4px 4px 4px 0;">{term}</span>'

    html = textwrap.dedent(f'''
    <div class="card">
        <h4 style="margin-top: 0; color: #1a1a2e; font-size: 1.1rem;">
            <span class="icon-inline">{icon}</span>Key Terms
        </h4>
        <div>{tags}</div>
    </div>
    ''')
    st.markdown(html, unsafe_allow_html=True)


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    shield_icon = ICONS["shield"]
    st.markdown(textwrap.dedent(f'''
    <div style="text-align: center; margin-bottom: 1.5rem;">
        <div style="display: inline-flex; align-items: center; justify-content: center; width: 48px; height: 48px; background: #f3f4f6; border-radius: 12px; margin-bottom: 0.5rem;">
            {shield_icon.replace('width="20"', 'width="28"').replace('height="20"', 'height="28"')}
        </div>
        <h2 style="color: #1a1a2e; margin-bottom: 0.2rem; font-size: 1.4rem;">ClauseGuard</h2>
        <p style="color: #6b7280; font-size: 0.85rem;">AI Financial Document Risk Analyzer</p>
    </div>
    '''), unsafe_allow_html=True)

    st.markdown("---")
    file_icon = ICONS["file_text"]
    st.markdown(f'<h4 style="font-size: 1rem; margin-bottom: 0.5rem;"><span class="icon-inline">{file_icon}</span>Sample Documents</h4>', unsafe_allow_html=True)
    st.caption("Click a button below to load a pre-built demo document for instant analysis.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Risky Invoice", use_container_width=True, key="btn_risky"):
            st.session_state["doc_text"] = SAMPLE_RISKY_INVOICE
            st.session_state["doc_source"] = "sample_risky"
            st.rerun()
    with col2:
        if st.button("Clean Contract", use_container_width=True, key="btn_clean"):
            st.session_state["doc_text"] = SAMPLE_CLEAN_CONTRACT
            st.session_state["doc_source"] = "sample_clean"
            st.rerun()

    st.markdown("---")
    lock_icon = ICONS["lock"]
    st.markdown(f'<h4 style="font-size: 1rem; margin-bottom: 0.5rem;"><span class="icon-inline">{lock_icon}</span>API Setup</h4>', unsafe_allow_html=True)
    st.caption("Set your GEMINI_API_KEY environment variable, or paste it below.")
    api_key_input = st.text_input("Paste API key (session only):", type="password", key="api_key_input")
    if api_key_input:
        os.environ["GEMINI_API_KEY"] = api_key_input

    st.markdown("---")
    info_icon = ICONS["info"]
    st.markdown(f'<p style="color: #9ca3af; font-size: 0.75rem;"><span class="icon-inline">{info_icon}</span>ClauseGuard v1.0 &middot; Single-page demo app</p>', unsafe_allow_html=True)

# ── Main Header ──────────────────────────────────────────────────────────────
shield_icon = ICONS["shield"]
st.markdown(textwrap.dedent(f'''
<div class="main-header">
    <h1><span style="display: inline-flex; align-items: center; vertical-align: middle; margin-right: 10px;">{shield_icon.replace('width="20"', 'width="36"').replace('height="20"', 'height="36"')}</span>ClauseGuard</h1>
    <p>Upload a financial document or contract and let AI spot the risks before you sign.</p>
</div>
'''), unsafe_allow_html=True)

# ── Input Section ────────────────────────────────────────────────────────────
st.markdown('<div style="max-width: 800px; margin: 0 auto;">', unsafe_allow_html=True)

upload_icon = ICONS["upload"]
st.markdown(f'<p style="color: #6b7280; font-size: 0.9rem; margin-bottom: 0.3rem;"><span class="icon-inline">{upload_icon}</span>Upload a PDF or paste text below</p>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Upload PDF",
    type=["pdf"],
    label_visibility="collapsed",
)

pasted_text = st.text_area(
    "Paste document text",
    height=180,
    placeholder="Paste contract clauses, invoice terms, or any financial document text here...",
    label_visibility="collapsed",
)

analyze_col, _ = st.columns([1, 3])
with analyze_col:
    analyze_clicked = st.button("Analyze Document", use_container_width=True, type="primary")

st.markdown("</div>", unsafe_allow_html=True)

# ── Determine Document Text ──────────────────────────────────────────────────
doc_text = None
source = None

if uploaded_file is not None:
    doc_text = extract_text_from_pdf(uploaded_file)
    source = "upload"
    if doc_text:
        st.success(f"Extracted {len(doc_text)} characters from PDF.")
    else:
        st.error("Could not extract text from the uploaded PDF.")
elif pasted_text.strip():
    doc_text = pasted_text.strip()
    source = "paste"
elif "doc_text" in st.session_state:
    doc_text = st.session_state["doc_text"]
    source = st.session_state.get("doc_source", "sample")

# ── Analysis ─────────────────────────────────────────────────────────────────
if analyze_clicked or (source in ("sample_risky", "sample_clean") and "analysis_result" not in st.session_state):
    if not doc_text:
        st.warning("Please upload a PDF, paste text, or select a sample document from the sidebar.")
    else:
        with st.spinner("ClauseGuard is analyzing your document..."):
            result = call_gemini_api(doc_text)
            if result:
                st.session_state["analysis_result"] = result
                st.session_state["analyzed_source"] = source
            else:
                if "analysis_result" in st.session_state:
                    del st.session_state["analysis_result"]

# ── Display Results ──────────────────────────────────────────────────────────
if "analysis_result" in st.session_state:
    result = st.session_state["analysis_result"]

    st.markdown("<hr style='border: none; border-top: 1px solid #e5e7eb; margin: 2rem 0;'>", unsafe_allow_html=True)

    score = result.get("risk_score", 50)
    summary = result.get("summary", "No summary provided.")
    key_terms = result.get("key_terms", [])
    red_flags = result.get("red_flags", [])
    recommendations = result.get("recommendations", [])

    gauge_col, summary_col = st.columns([1, 2])
    with gauge_col:
        render_gauge(score)
    with summary_col:
        render_summary(summary)

    if key_terms:
        render_key_terms(key_terms)

    flags_col, recs_col = st.columns(2)
    with flags_col:
        render_red_flags(red_flags)
    with recs_col:
        render_recommendations(recommendations)

    code_icon = ICONS["code"]
    with st.expander("View Raw JSON Response"):
        st.markdown(f'<p style="color: #6b7280; font-size: 0.85rem; margin-bottom: 0.5rem;"><span class="icon-inline">{code_icon}</span>Full parsed response from the model:</p>', unsafe_allow_html=True)
        st.json(result)
