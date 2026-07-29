# ClauseGuard

![App Logo]([assets/screenshot.png](https://github.com/D-Groot/ClauseGaurd/blob/main/logo.png))

AI-powered financial document risk analyzer. Upload a contract or invoice — get an instant risk score, plain-English summary, flagged red flags, and actionable recommendations.

Built for **Dev Season of Code — Summer Edition 2026**.



## What it does

- Upload a PDF or paste document text (invoices, contracts, service agreements)
- AI analysis returns:
  - **Risk score** (0–100) with a color-coded gauge
  - **Plain-English summary**
  - **Key terms** extracted
  - **Red flags** with severity ratings (high / medium / low)
  - **Recommendations** for what to renegotiate or verify
- Two built-in sample documents (risky invoice, clean contract) for instant demo, no upload required

## Tech Stack

- **Streamlit** — UI and app framework
- **pdfplumber** — PDF text extraction
- **Google Gemini API** (`google-generativeai`) — document risk analysis, structured JSON output

## Setup

### 1. Clone and install dependencies

```bash
git clone <your-repo-url>
cd clauseguard
pip install streamlit pdfplumber google-generativeai
```

### 2. Set your Gemini API key

```bash
export GEMINI_API_KEY="your-api-key-here"
```

Or paste it directly into the sidebar of the running app (session-only, not stored).

### 3. Run the app

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

## Usage

1. Upload a PDF, or paste document text into the text area
2. Click **Analyze Document**
3. Review the risk score, summary, key terms, red flags, and recommendations
4. Or click **Risky Invoice** / **Clean Contract** in the sidebar for an instant demo

## Project Structure

```
clauseguard/
├── app.py          # Full application (UI + logic, single file)
└── README.md
```

## How It Works

1. `pdfplumber` extracts raw text from an uploaded PDF (or the user pastes text directly)
2. The text is sent to the Gemini API with a system prompt enforcing a strict JSON schema:
   ```json
   {
     "risk_score": 0-100,
     "summary": "...",
     "key_terms": ["..."],
     "red_flags": [{"issue": "...", "severity": "high|medium|low"}],
     "recommendations": ["..."]
   }
   ```
3. The response is sanitized (markdown fences stripped) and parsed
4. Results render as styled cards: gauge, summary, key terms, red flags table, recommendations checklist

## What's Next

- Multi-document comparison against standard terms
- Exportable PDF/markdown risk reports
- Follow-up Q&A mode on uploaded documents
- Batch analysis of multiple documents
- Jurisdiction-aware compliance checks

## License

Built for Dev Season of Code — Summer Edition 2026.
