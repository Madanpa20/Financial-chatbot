import streamlit as st
from datetime import date, datetime
import pandas as pd
import matplotlib.pyplot as plt
import google.generativeai as genai
import os
import numpy as np
from dotenv import load_dotenv
from db_utils import get_db  # Using your central utility file

# --- PRO FEATURE: ANOMALY DETECTION ---
def detect_anomalies_pro(df):
    """Pro Feature: Identifies transactions that are statistically unusual."""
    anomalies = []
    if len(df) < 3:
        return anomalies
        
    for category in df['category'].unique():
        cat_df = df[df['category'] == category]
        if len(cat_df) >= 3:
            mean = cat_df['amount'].mean()
            std = cat_df['amount'].std()
            # Identify spending 2 standard deviations above the mean
            spikes = cat_df[cat_df['amount'] > (mean + 2 * std)]
            for _, row in spikes.iterrows():
                anomalies.append(f"🚩 **Anomaly Detected**: Unusual spike in **{category}** (₹{row['amount']}) on {row['date']}")
    return anomalies

# --- CRITICAL: CACHED DATA FETCHING ---
# This stops the infinite reload loop by keeping data in memory for 60 seconds.
@st.cache_data(ttl=60) 
def fetch_transactions_cached():
    try:
        db = get_db()
        # Convert cursor to list immediately; Streamlit cannot cache lazy cursors.
        data = list(db.transactions.find().sort("date", -1))
        return data
    except Exception as e:
        return []

def main():
    # ---------- CONFIG ----------
    st.set_page_config(page_title="Fibot Pro | Insights", page_icon="📊", layout="wide")
    load_dotenv()
    
    # ---- Database Configuration ----
    db = get_db()
    transactions_col = db.transactions

    # ---- AI Configuration ----
    api_key = os.getenv("GEMINI_API_KEY") 
    genai.configure(api_key=api_key)

    # ---- Pro Custom Styling ----
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 25px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
    }
    h1, h2, h3 { color: #FFD700 !important; }
    </style>
    """, unsafe_allow_html=True)

    # ---- LOAD DATA FROM CLOUD (Using Cached Function) ----
    history_list = fetch_transactions_cached()
    history_df = pd.DataFrame(history_list)
    
    if not history_df.empty:
        if '_id' in history_df.columns:
            history_df = history_df.drop(columns=['_id'])

    st.title("📊 Spending Insights Pro (Cloud)")
    st.markdown("Cloud-synced anomaly detection and AI-driven trend analysis.")

    # ---- Transaction Input (Using st.form to batch inputs) ----
    with st.container():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("➕ Quick Add Transaction")

        with st.form("transaction_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            t_date = col1.date_input("Date", value=date.today())
            t_cat = col2.selectbox("Category", ["Food", "Travel", "Entertainment", "Bills", "Shopping", "Medical", "Education", "Investments", "Insurance", "Savings", "Other"])
            t_amount = col3.number_input("Amount (₹)", min_value=0.0, step=10.0)

            submit_button = st.form_submit_button("Log to Cloud Cluster", use_container_width=True)
            
            if submit_button:
                if t_amount > 0:
                    new_doc = {
                        "date": str(t_date),
                        "category": t_cat,
                        "amount": t_amount,
                        "timestamp": datetime.now()
                    }
                    transactions_col.insert_one(new_doc)
                    # Force cache clear so the UI updates with the new transaction
                    st.cache_data.clear()
                    st.success(f"Successfully synced ₹{t_amount} to {t_cat}!")
                    st.rerun() 
                else:
                    st.warning("Please enter an amount greater than 0.")
        st.markdown('</div>', unsafe_allow_html=True)

    # ---- Data Visualization & AI Analysis ----
    if not history_df.empty:
        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("📌 Category Breakdown")
            
            cat_sum = history_df.groupby("category")["amount"].sum()
            fig, ax = plt.subplots(figsize=(6, 6))
            fig.patch.set_alpha(0) 
            ax.pie(cat_sum, labels=cat_sum.index, autopct='%1.1f%%', startangle=90, textprops={'color':"white"})
            st.pyplot(fig)
            st.markdown('</div>', unsafe_allow_html=True)

        with col_right:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("🤖 AI Trend Analysis")
            
            if st.button("Generate Cloud Insights"):
                anomalies = detect_anomalies_pro(history_df)
                if anomalies:
                    for a in anomalies:
                        st.warning(a)
                else:
                    st.success("✅ No unusual spending spikes detected.")

                prompt = f"""
                Analyze this spending: {history_df.tail(15).to_dict(orient='records')}
                1. Identify trends. 2. Evaluate 'Wants' vs 'Savings'. 3. Predict month-end risk.
                Concise bullet points only.
                """

                try:
                    model = genai.GenerativeModel("gemini-3-flash")
                    response = model.generate_content(prompt)
                    st.info(response.text)
                except Exception as e:
                    st.error(f"AI Analysis Failed: {e}")
            st.markdown('</div>', unsafe_allow_html=True)

    # ---- History View ----
    with st.expander("📜 View Full Cloud Audit Log"):
        if not history_df.empty:
            st.dataframe(history_df.sort_values(by="date", ascending=False), use_container_width=True)
        else:
            st.write("No data found in the cloud yet.")

if __name__ == "__main__":
    main()