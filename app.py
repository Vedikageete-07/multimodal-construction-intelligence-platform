import json
import re
from datetime import datetime
from typing import Any, Dict

import pandas as pd
import streamlit as st
from PIL import Image

try:
    from google import genai
    from google.genai import types
except Exception:
    genai = None
    types = None


st.set_page_config(
    page_title="BuildIntel AI | Construction Intelligence",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main {background: #f7f9fc;}
    .block-container {padding-top: 1.5rem; max-width: 1400px;}
    .hero {
        padding: 1.5rem 1.8rem; border-radius: 18px;
        background: linear-gradient(120deg,#10243a,#205b75);
        color: white; margin-bottom: 1.2rem;
    }
    .hero h1 {color:white; margin:0;}
    .hero p {color:#dceaf2; margin:.4rem 0 0 0;}
    .small-note {color:#64748b; font-size:.85rem;}
    div[data-testid="stMetric"] {
        background:white; padding:14px; border:1px solid #e6ebf2;
        border-radius:12px;
    }
</style>
""", unsafe_allow_html=True)


def safe_json_download(data: Dict[str, Any], filename: str):
    return st.download_button(
        "⬇️ Download JSON report",
        data=json.dumps(data, indent=2, ensure_ascii=False),
        file_name=filename,
        mime="application/json",
        use_container_width=False,
    )


def parse_json_response(text: str) -> Dict[str, Any]:
    """Parse JSON even if a model wraps it in Markdown fences."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("The AI did not return a JSON object.")
    return json.loads(cleaned[start:end + 1])


def gemini_json(prompt: str, image: Image.Image = None) -> Dict[str, Any]:
    api_key = st.session_state.get("gemini_api_key", "").strip()
    if not api_key or genai is None:
        raise RuntimeError("Gemini is not configured. Use Demo Mode or add a valid API key.")
    client = genai.Client(api_key=api_key)
    contents = [prompt]
    if image is not None:
        contents.append(image)
    response = client.models.generate_content(
        model=st.session_state.get("gemini_model", "gemini-2.5-flash"),
        contents=contents,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    return parse_json_response(response.text or "")


def use_ai_or_demo(prompt: str, demo: Dict[str, Any], image: Image.Image = None):
    if st.session_state.get("demo_mode", True):
        return demo, "Demonstration mode"
    try:
        result = gemini_json(prompt, image)
        return result, "Gemini AI"
    except Exception as exc:
        st.warning(f"AI request could not be completed: {exc}. Showing demonstration result instead.")
        return demo, "Demonstration fallback"


def show_image_uploader(key: str, label: str):
    uploaded = st.file_uploader(label, type=["jpg", "jpeg", "png"], key=key)
    if uploaded:
        try:
            image = Image.open(uploaded).convert("RGB")
            st.image(image, caption="Uploaded construction-site image", use_container_width=True)
            return image
        except Exception as exc:
            st.error(f"Unable to read image: {exc}")
    return None


def show_safety_report(report: Dict[str, Any], source: str):
    score = int(max(0, min(100, report.get("safety_score", 0))))
    c1, c2, c3 = st.columns(3)
    c1.metric("Safety score", f"{score}/100")
    c2.metric("Overall status", str(report.get("overall_status", "Needs review")))
    hazards = report.get("hazards", [])
    c3.metric("Hazards identified", len(hazards))
    st.caption(f"Analysis source: {source}")
    checklist = report.get("ppe_detection", [])
    if checklist:
        st.subheader("PPE compliance checklist")
        if isinstance(checklist, dict):
            checklist = [{"item": k, "status": v} for k, v in checklist.items()]
        st.dataframe(pd.DataFrame(checklist), use_container_width=True, hide_index=True)
    st.subheader("Site hazards and corrective actions")
    if hazards:
        st.dataframe(pd.DataFrame(hazards), use_container_width=True, hide_index=True)
    else:
        st.info("No hazards were returned in this report.")
    safe_json_download(report, "site_safety_report.json")


def demo_safety():
    return {
        "safety_score": 72,
        "overall_status": "Needs improvement",
        "ppe_detection": [
            {"item": "Safety helmets", "status": "Partially observed", "notes": "Verify every worker is wearing a secured helmet."},
            {"item": "High-visibility vests", "status": "Observed", "notes": "Visible on some workers; inspect the full site."},
            {"item": "Steel-toe boots", "status": "Not verifiable", "notes": "Footwear cannot be reliably confirmed from this view."},
            {"item": "Safety harnesses", "status": "Not verifiable", "notes": "Required when working at height; inspect directly."},
        ],
        "hazards": [
            {"hazard": "Unprotected work-at-height area", "severity": "High", "remedy": "Install guardrails and require inspected fall-arrest systems."},
            {"hazard": "Material storage near walkway", "severity": "Medium", "remedy": "Clear access routes and secure stored materials."},
        ],
        "limitations": "Illustrative demonstration output; verify all findings through a qualified site safety inspection."
    }


def demo_crack():
    return {
        "defect_type": "Hairline (illustrative classification)",
        "estimated_width_mm": 0.3,
        "severity": "Low",
        "possible_root_causes": ["Drying shrinkage", "Surface finish movement"],
        "recommended_repairs": ["Record and monitor crack progression", "Ask a qualified engineer to inspect if it widens or reappears"],
        "urgency": "Routine inspection",
        "limitations": "Image-only estimates are not structural diagnoses. Width requires a scale reference and on-site measurement."
    }


def main():
    st.sidebar.title("🏗️ BuildIntel AI")
    st.sidebar.caption("Multimodal Construction Intelligence Platform")
    st.sidebar.divider()
    st.sidebar.subheader("AI Configuration")
    st.session_state["gemini_api_key"] = st.sidebar.text_input(
        "Google Gemini API key", type="password",
        value=st.session_state.get("gemini_api_key", ""),
        help="Optional. Keep your API key private; do not commit it to GitHub."
    )
    st.session_state["gemini_model"] = st.sidebar.selectbox(
        "Gemini model", ["gemini-2.5-flash", "gemini-2.0-flash"],
        index=0
    )
    st.session_state["demo_mode"] = st.sidebar.toggle(
        "Demonstration mode", value=st.session_state.get("demo_mode", True),
        help="Demo mode works without an API key and uses clearly labelled sample results."
    )
    st.sidebar.divider()
    st.sidebar.subheader("Platform architecture")
    st.sidebar.markdown(
        "- Streamlit interface\n"
        "- Python analysis layer\n"
        "- Gemini multimodal vision (optional)\n"
        "- JSON reports\n"
        "- No external database"
    )
    st.sidebar.info("AI output is decision support only. It does not replace a licensed structural or safety professional.")

    st.markdown("""
    <div class="hero">
      <h1>🏗️ Multimodal Construction Intelligence</h1>
      <p>AI-assisted site safety, structural defect review, project estimation and daily site guidance.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("Use the modules below to analyze site images, estimate project requirements and get practical construction guidance.")
    safety_tab, crack_tab, planning_tab, assistant_tab = st.tabs([
        "🦺 Site Safety & PPE", "🧱 Crack Diagnostics",
        "📊 Planning & Valuation", "🌦️ Site Assistant"
    ])

    with safety_tab:
        st.header("Site Safety & PPE Audit")
        st.write("Upload a construction-site photo to review visible PPE indicators and potential hazards.")
        image = show_image_uploader("safety_image", "Upload site photo (JPG/PNG)")
        if st.button("Analyze site safety", type="primary", key="safety_analyze"):
            if image is None:
                st.error("Please upload a construction-site image first.")
            else:
                prompt = """
Analyze this construction site image for visible occupational safety indicators.
Return ONLY JSON with:
safety_score (integer 0-100), overall_status (string),
ppe_detection (array of objects with item,status,notes),
hazards (array of objects with hazard,severity,remedy),
limitations (string).
Check helmets, high-visibility vests, steel-toe boots and safety harnesses.
Hazard severity must be Low, Medium, High, or Critical.
Do not claim an item is absent if it is not visible; use Not verifiable.
Mention that image analysis is preliminary and standards compliance requires a qualified inspection.
"""
                with st.spinner("Reviewing image..."):
                    report, source = use_ai_or_demo(prompt, demo_safety(), image)
                st.session_state["safety_report"] = report
                st.session_state["safety_source"] = source
        if "safety_report" in st.session_state:
            show_safety_report(st.session_state["safety_report"], st.session_state.get("safety_source", "Demo"))

    with crack_tab:
        st.header("Crack Diagnostics & Structural Integrity")
        st.write("Upload a concrete or wall-surface photo for a preliminary visual review.")
        image = show_image_uploader("crack_image", "Upload concrete/wall image (JPG/PNG)")
        scale_note = st.text_input("Optional scale/reference information", placeholder="e.g. ruler visible; 1 cm markings")
        if st.button("Analyze crack / defect", type="primary", key="crack_analyze"):
            if image is None:
                st.error("Please upload a surface image first.")
            else:
                prompt = f"""
Review this concrete/wall image for visible defects. Reference information: {scale_note or 'No scale supplied'}.
Return ONLY JSON with:
defect_type (one of Hairline, Settlement, Structural Shear, Thermal Expansion, Spalling, Unclear),
estimated_width_mm (number or null), severity (Low, Medium, High, Critical, Unclear),
possible_root_causes (array of strings), recommended_repairs (array of strings),
urgency (string), limitations (string).
Do not overstate certainty. If no scale is available, clearly say width is a rough visual estimate or null.
Do not provide a definitive structural diagnosis; recommend a qualified structural engineer for concerning cracks.
"""
                with st.spinner("Analyzing visible surface characteristics..."):
                    report, source = use_ai_or_demo(prompt, demo_crack(), image)
                st.session_state["crack_report"] = report
                st.session_state["crack_source"] = source
        if "crack_report" in st.session_state:
            report = st.session_state["crack_report"]
            a, b, c = st.columns(3)
            a.metric("Defect type", str(report.get("defect_type", "Unclear")))
            width = report.get("estimated_width_mm")
            b.metric("Estimated width", f"{width} mm" if width is not None else "Not available")
            c.metric("Severity", str(report.get("severity", "Unclear")))
            st.caption(f"Analysis source: {st.session_state.get('crack_source', 'Demo')}")
            st.subheader("Possible root causes")
            for item in report.get("possible_root_causes", []):
                st.write(f"• {item}")
            st.subheader("Recommended next steps")
            for item in report.get("recommended_repairs", []):
                st.write(f"• {item}")
            st.info(f"Urgency: {report.get('urgency', 'Professional review recommended')}")
            st.warning(report.get("limitations", "This is preliminary image-based guidance, not an engineering certification."))
            safe_json_download(report, "crack_diagnostics_report.json")

    with planning_tab:
        st.header("Project Planning & Real Estate Valuation")
        st.write("Enter project details to calculate an indicative budget, expenditure, material quantities and asset value.")
        left, right = st.columns(2)
        with left:
            structure = st.selectbox("Structure type", ["Residential", "Commercial", "Industrial"])
            area = st.number_input("Built-up area (sq ft)", min_value=100, max_value=1000000, value=1500, step=100)
            city_tier = st.selectbox("Location tier", ["Tier 1", "Tier 2", "Tier 3"])
            completion = st.slider("Project completion (%)", 0, 100, 35)
        with right:
            base_cost = st.number_input("Base construction cost (₹ / sq ft)", min_value=500, max_value=10000, value=1800, step=50)
            market_rate = st.number_input("Estimated market value (₹ / sq ft)", min_value=500, max_value=50000, value=3500, step=100)
            contingency = st.slider("Contingency (%)", 0, 25, 10)
        tier_factor = {"Tier 1": 1.20, "Tier 2": 1.00, "Tier 3": 0.85}[city_tier]
        structure_factor = {"Residential": 1.0, "Commercial": 1.15, "Industrial": 1.10}[structure]
        estimated_budget = area * base_cost * tier_factor * structure_factor * (1 + contingency / 100)
        incurred = estimated_budget * completion / 100
        asset_value = area * market_rate * tier_factor
        cement_bags = area * 0.40
        steel_kg = area * 4.0
        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("Estimated project budget", f"₹{estimated_budget:,.0f}")
        m2.metric("Expenditure incurred", f"₹{incurred:,.0f}")
        m3.metric("Indicative asset valuation", f"₹{asset_value:,.0f}")
        st.progress(completion / 100, text=f"Milestone progress: {completion}%")
        st.subheader("Indicative material requirements")
        material_df = pd.DataFrame([
            {"Material": "Cement", "Estimated quantity": f"{cement_bags:,.0f} bags", "Basis": "0.40 bags per sq ft (planning assumption)"},
            {"Material": "Steel", "Estimated quantity": f"{steel_kg:,.0f} kg", "Basis": "4.0 kg per sq ft (planning assumption)"},
        ])
        st.dataframe(material_df, use_container_width=True, hide_index=True)
        st.caption("All values are indicative planning assumptions, not a bill of quantities, contractor quotation, appraisal or engineering design.")
        plan_report = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "inputs": {"structure_type": structure, "built_up_sqft": area, "location_tier": city_tier,
                       "completion_percent": completion, "base_cost_inr_per_sqft": base_cost,
                       "market_rate_inr_per_sqft": market_rate, "contingency_percent": contingency},
            "estimates_inr": {"total_project_budget": round(estimated_budget, 2),
                              "capital_expenditure_incurred": round(incurred, 2),
                              "indicative_asset_valuation": round(asset_value, 2)},
            "materials": {"cement_bags": round(cement_bags), "steel_kg": round(steel_kg)},
            "assumptions": ["Tier and structure multipliers are illustrative.", "Material quantities use simplified per-square-foot assumptions.", "Obtain a local engineer/quantity surveyor estimate before procurement."]
        }
        safe_json_download(plan_report, "construction_planning_report.json")
        st.subheader("Conceptual architectural visualization prompt")
        st.write(f"Generate a conceptual {structure.lower()} building of approximately {area:,} sq ft, in an Indian urban context, with practical circulation, daylighting and climate-responsive design. This is a concept prompt, not a construction drawing.")
        st.code(f"Conceptual architectural rendering of a {structure.lower()} building, built-up area {area:,} square feet, contemporary Indian architecture, climate-responsive design, realistic materials, professional architectural visualization.", language="text")

    with assistant_tab:
        st.header("Daily Site Assistant & Weather-Aware Advisory")
        weather = st.selectbox("Current / expected weather", ["Normal", "High Wind", "Heavy Rain", "Extreme Heat"])
        advisories = {
            "Normal": ["Continue work under the approved site safety plan.", "Maintain housekeeping, PPE checks and routine equipment inspections."],
            "High Wind": ["Pause crane and hoisting operations when wind exceeds equipment/site limits.", "Secure loose materials, sheets and temporary structures.", "Follow the lift supervisor and equipment manufacturer's wind limits."],
            "Heavy Rain": ["Protect electrical systems and avoid work in waterlogged areas.", "Inspect excavations, scaffolding and access routes after rainfall.", "Protect fresh concrete and follow the approved curing and pour plan."],
            "Extreme Heat": ["Schedule hydration and shaded rest breaks.", "Monitor workers for heat stress and adjust strenuous work timing.", "Protect concrete placement and curing according to the engineer-approved method."]
        }
        st.subheader(f"Advisory for: {weather}")
        for item in advisories[weather]:
            st.warning(item) if weather != "Normal" else st.info(item)

        st.divider()
        st.subheader("Ask the Construction Assistant")
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        question = st.chat_input("Ask about concrete, site planning, materials or safety...")
        if question:
            st.session_state.chat_history.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)
            with st.chat_message("assistant"):
                if st.session_state.get("demo_mode", True):
                    answer = (
                        "Demo assistant response: Start by checking the approved drawings, method statement, "
                        "site conditions and applicable local codes. For safety-critical or structural decisions, "
                        "consult the responsible qualified engineer. Add a Gemini API key and turn off Demonstration "
                        "mode for AI-generated answers."
                    )
                else:
                    try:
                        client = genai.Client(api_key=st.session_state["gemini_api_key"])
                        context = "\n".join(
                            f'{m["role"]}: {m["content"]}' for m in st.session_state.chat_history[-8:]
                        )
                        response = client.models.generate_content(
                            model=st.session_state.get("gemini_model", "gemini-2.5-flash"),
                            contents=("You are a cautious construction site information assistant. "
                                      "Give practical general guidance, state assumptions, never certify structural safety, "
                                      "and recommend qualified professionals for high-risk decisions.\n\n" + context)
                        )
                        answer = response.text or "I could not generate a response. Please try again."
                    except Exception as exc:
                        answer = f"AI assistant unavailable: {exc}. Please check the API key or enable Demonstration mode."
                st.markdown(answer)
            st.session_state.chat_history.append({"role": "assistant", "content": answer})

    st.divider()
    st.caption("BuildIntel AI • Academic capstone prototype • AI outputs and estimates require professional verification.")


if __name__ == "__main__":
    main()
