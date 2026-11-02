# Multimodal Construction Intelligence Platform

An academic Generative AI capstone prototype for construction-site decision support.

## Features

1. **Site Safety & PPE Audit** – Upload a construction image and review visible PPE indicators (helmets, high-visibility vests, boots and harnesses), hazards, severity and corrective actions.
2. **Crack Diagnostics** – Upload a concrete/wall image for a preliminary defect classification, possible causes, estimated width (when possible), urgency and suggested next steps.
3. **Planning & Real Estate Valuation** – Calculate indicative project budget, expenditure based on completion percentage, indicative asset valuation, and simplified cement/steel quantities.
4. **Daily Site Assistant** – Weather-aware site advisories and a multi-turn construction Q&A assistant.

## Technology

- Python
- Streamlit
- Google Gemini multimodal API (optional)
- Pillow
- Pandas
- JSON reports

## Run locally

Python 3.9+ is recommended.

```bash
# 1. Create and activate a virtual environment
python -m venv venv

# Windows PowerShell
.\venv\Scripts\Activate.ps1

# macOS/Linux
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the app
streamlit run app.py
```

Open the local URL printed by Streamlit (usually http://localhost:8501).

## AI mode and demo mode

The app starts in **Demonstration mode**, so all modules can be explored without an API key. Demo results are illustrative and are clearly labelled.

To use Gemini:
1. Obtain a Gemini API key from Google AI Studio.
2. Enter it in the sidebar's password field.
3. Turn off Demonstration mode.
4. Upload an image and run an analysis.

Never commit API keys to GitHub. For a deployed app, configure secrets in Streamlit Community Cloud.

Example Streamlit secret:

```toml
GEMINI_API_KEY = "your-key"
```

For this academic version, enter the key in the sidebar at runtime. Do not place it in source code.

## Deploy on Streamlit Community Cloud

1. Push this repository to a **public GitHub repository**.
2. Sign in at https://share.streamlit.io/
3. Choose **New app**.
4. Select the repository, branch `main`, and main file `app.py`.
5. Deploy and wait for the build to finish.
6. Open the generated HTTPS URL and test all four modules.
7. Add your Gemini API key through the app sidebar if you want live Gemini analysis.

## Repository structure

```text
construction_intelligence_platform/
├── app.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Important limitations

- Image-based PPE review can miss objects due to angle, lighting, occlusion or image quality. It is not an OSHA/IS 456 compliance certificate.
- Crack width cannot be measured accurately from an image without a known scale and suitable image calibration. This tool does not diagnose structural safety.
- Planning rates, location multipliers and material quantities are simplified academic assumptions. Replace them with local BOQ, supplier rates, drawings and quantity-surveyor inputs for real projects.
- Weather advisories are general reminders. Follow site-specific method statements, equipment limits, local weather alerts and the responsible safety officer.
- Gemini responses may be incorrect. A qualified construction professional must verify safety-critical decisions.

## Academic project scope

This project is designed as a decision-support prototype aligned with the Skill Wallet Project 1 brief. It is not a replacement for professional engineering, valuation, inspection or legal compliance services.
