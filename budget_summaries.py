import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import google.generativeai as genai
import io, re, json, os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from textwrap import wrap
from dotenv import load_dotenv
from db_utils import get_db # Centralized MongoDB utility

# --- CRITICAL: CACHED DATA FETCHING ---
# This stops the infinite reload loop by keeping data in memory for 60 seconds.
@st.cache_data(ttl=60)
def fetch_cloud_data_for_analysis():
    """Retrieves all transactions from the cloud and converts to a list for caching."""
    try:
        db = get_db()
        # Convert cursor to list immediately; Streamlit cannot cache lazy cursors.
        data = list(db.transactions.find())
        return data
    except Exception as e:
        return []

def calculate_health_score(summary_data, total_budget):
    """Calculates a financial health score from 0-100 based on cloud analysis."""
    score = 100
    penalties = {
        "needs": 20,       
        "wants": 15,       
        "savings": 25,     
        "investments": 20  
    }
    for category, values in summary_data.items():
        if values['status'] == 'exceeded':
            score -= penalties.get(category, 10)
    return max(score, 0)

def main():
    # --- CONFIG ---
    st.set_page_config(page_title="💰 Fibot Pro | Budget", page_icon="💰", layout="wide")
    load_dotenv()
    
    # --- Database Setup ---
    db = get_db()
    transactions_col = db.transactions

    # --- Gemini API ---
    api_key = os.getenv("GEMINI_API_KEY3")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-3-flash") # Updated to current model

    # --- Load Spending Data from Cloud (Using Cached Function) ---
    data_list = fetch_cloud_data_for_analysis()
    history_df = pd.DataFrame(data_list)

    if history_df.empty:
        st.warning("No transactions found in the cloud. Please add entries in 'Spending Insights' first.")
        st.stop()
    
    # Clean MongoDB internal fields for analysis
    if '_id' in history_df.columns:
        history_df = history_df.drop(columns=['_id'])

    # --- UI ---
    st.title("💰 Budget Summaries & Pro Health Score")
    st.markdown("Fibot Pro evaluates your cloud data to detect anomalies and track financial discipline.")
    
    # --- User Budget Inputs ---
    total_budget = st.number_input("Enter your total monthly budget (₹)", min_value=1000, value=50000, step=500)

    col1, col2, col3, col4 = st.columns(4)
    with col1: n_p = st.slider("Needs (%)", 0, 100, 50)
    with col2: w_p = st.slider("Wants (%)", 0, 100, 30)
    with col3: s_p = st.slider("Savings (%)", 0, 100, 10)
    with col4: i_p = st.slider("Investments (%)", 0, 100, 10)

    allocation_percentages = {"needs": n_p, "wants": w_p, "savings": s_p, "investments": i_p}

    if "parsed_data" not in st.session_state: st.session_state.parsed_data = None
    if "health_score" not in st.session_state: st.session_state.health_score = 0

    # --- Generate Analysis ---
    if st.button("📊 Analyze Cloud Financial Health", use_container_width=True):
        with st.spinner("Analyzing your cloud financial patterns..."):
            # Group cloud data by category
            category_totals = history_df.groupby("category")["amount"].sum().to_dict()

            prompt = f"""
            You are a senior financial advisor AI. Analyze cloud data: {category_totals}
            Budget: {total_budget} | Goals: {allocation_percentages}
            Return ONLY valid JSON with structure:
            {{
              "summary": {{
                "needs": {{"spent": number, "limit": number, "status": "ok/exceeded"}},
                "wants": {{"spent": number, "limit": number, "status": "ok/exceeded"}},
                "savings": {{"spent": number, "limit": number, "status": "ok/exceeded"}},
                "investments": {{"spent": number, "limit": number, "status": "ok/exceeded"}}
              }},
              "anomalies": ["list of unusual cloud spending spikes"],
              "advice": "Actionable budget optimization advice."
            }}
            """

            try:
                response = model.generate_content(prompt)
                data_str = re.search(r"\{[\s\S]*\}", response.text).group()
                parsed_data = json.loads(data_str)
                st.session_state.parsed_data = parsed_data
                
                h_score = calculate_health_score(parsed_data["summary"], total_budget)
                st.session_state.health_score = h_score

                st.divider()
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.subheader("❤️ Health Score")
                    st.title(f"{h_score}/100")
                    if h_score >= 80: st.success("Status: Excellent! 🌟")
                    elif h_score >= 50: st.warning("Status: Monitor Spends. ⚠️")
                    else: st.error("Status: High Stress. 🚨")
                
                with c2:
                    st.subheader("💡 Cloud Insights")
                    st.info(parsed_data["advice"])

                if parsed_data.get("anomalies"):
                    st.subheader("🚩 Anomaly Alerts")
                    for alert in parsed_data["anomalies"]: st.error(alert)

            except Exception as e:
                st.error(f"Cloud Analysis Failed: {e}")
            
    # --- PDF Generation ---
    if st.button("📄 Download Pro PDF Report"):
        if st.session_state.parsed_data is None:
            st.error("⚠️ Run the cloud analysis first.")
        else:
            try:
                pd_dat = st.session_state.parsed_data
                hs = st.session_state.health_score
                pdf_buffer = io.BytesIO()
                can = canvas.Canvas(pdf_buffer, pagesize=letter)
                w, h = letter

                can.setFont("Helvetica-Bold", 18)
                can.drawString(50, h - 50, "Fibot Pro: Cloud Financial Report")
                can.setFont("Helvetica-Bold", 14)
                can.drawString(50, h - 80, f"Health Score: {hs}/100")
                
                curr_y = h - 120
                for sec, val in pd_dat["summary"].items():
                    can.setFont("Helvetica-Bold", 11)
                    can.drawString(60, curr_y, f"{sec.capitalize()}: {val['status'].upper()}")
                    curr_y -= 15
                    can.setFont("Helvetica", 10)
                    can.drawString(70, curr_y, f"Spent: ₹{val['spent']} | Limit: ₹{val['limit']}")
                    curr_y -= 25

                can.save()
                pdf_buffer.seek(0)
                st.download_button("⬇️ Download PDF Report", pdf_buffer, "cloud_health_report.pdf", "application/pdf")
            except Exception as e:
                st.error(f"PDF Generation Error: {e}")

if __name__ == "__main__":
    main()