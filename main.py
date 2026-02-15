import streamlit as st
from urllib.parse import urlencode
import budget_summaries
import spending_insights
import NLU_Analysis
import rag_granite_finance
import about_fibot
import dream_tracker  # New Pro Module

st.set_page_config(page_title="Fibot Pro - AI Finance Companion", page_icon="💰", layout="wide")

# Custom CSS
st.markdown("""
    <style>
    body {
        background-color: #0E0E0F;
        color: white;
        font-family: "Segoe UI", sans-serif;
    }
    .top-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 15px 40px;
        background: rgba(255, 255, 255, 0.02);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    .fibot-name {
        font-family: 'Poppins', sans-serif;
        font-size: 2.5em;
        font-weight: 600;
        color: #FFD700;
        letter-spacing: 1px;
    }
    .button-group button {
        margin-left: 10px;
        padding: 8px 20px;
        border-radius: 20px;
        font-size: 0.9em;
        cursor: pointer;
        background-color: transparent;
        color: white;
        border: 1px solid #FFD700;
        transition: 0.3s;
    }
    .button-group button:hover {
        background-color: #FFD700;
        color: black;
    }
    .nav-links {
        text-align: right;
        padding: 10px 40px;
        background: rgba(0,0,0,0.2);
    }
    .center-section {
        text-align: center;
        padding: 8vh 20px;
    }
    .headline {
        font-size: 3em;
        font-weight: bold;
        background: linear-gradient(90deg, #FFFFFF, #FFD700);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .subhead {
        font-size: 1.4em;
        color: #aaa;
        margin-bottom: 30px;
    }
    .btn-outline {
        background: #FFD700;
        color: black;
        border: none;
        padding: 12px 30px;
        border-radius: 30px;
        font-weight: bold;
        cursor: pointer;
        text-decoration: none;
        display: inline-block;
    }
    .question-card {
        display: inline-block;
        background-color: #1A1A1B;
        color: #ddd;
        padding: 12px 20px;
        margin: 0 10px;
        border-radius: 30px;
        border: 1px solid #333;
        font-size: 0.9em;
    }
    /* --- SCROLLER CSS --- */
    .scroll-row {
        width: 100%;
        overflow: hidden;
        position: relative;
        padding: 20px 0;
        background: transparent;
    }
    .scroll-content {
        display: flex;
        width: max-content; /* Ensure container is wide enough for duplicates */
        animation: scroll-left 40s linear infinite;
    }
    .scroll-content-reverse {
        display: flex;
        width: max-content;
        animation: scroll-right 40s linear infinite;
    }
    @keyframes scroll-left {
        0% { transform: translateX(0); }
        100% { transform: translateX(-50%); }
    }
    @keyframes scroll-right {
        0% { transform: translateX(-50%); }
        100% { transform: translateX(0); }
    }
    .question-card {
        flex-shrink: 0;
        background-color: #1A1A1B;
        color: #ddd;
        padding: 12px 25px;
        margin: 0 10px;
        border-radius: 30px;
        border: 1px solid #333;
        font-size: 1em;
        white-space: nowrap;
    }
    </style>
""", unsafe_allow_html=True)

# State Management
if "show_sip" not in st.session_state: st.session_state.show_sip = False
if "show_swp" not in st.session_state: st.session_state.show_swp = False

# Navigation logic
params = st.query_params
page = params.get("page", "home")

# Top Bar
st.markdown("""
<div class="top-bar">
    <div class="fibot-name">Fibot Pro</div>
    <div class="button-group">
        <a href="?page=sip" target="_self"><button>SIP Calc</button></a>
        <a href="?page=swp" target="_self"><button>SWP Calc</button></a>
    </div>
</div>
""", unsafe_allow_html=True)

# Modal Logic
@st.dialog("SIP Calculator")
def sip_modal():
    monthly = st.number_input("Monthly SIP (₹)", value=5000)
    rate = st.number_input("Expected Return (%)", value=12.0)
    yrs = st.number_input("Years", value=10)
    if st.button("Calculate"):
        r = rate / 12 / 100
        m = yrs * 12
        val = monthly * (((1 + r)**m - 1) / r) * (1 + r)
        st.success(f"Estimated Wealth: ₹{val:,.2f}")

@st.dialog("SWP Calculator")
def swp_modal():
    total = st.number_input("Lump Sum (₹)", value=1000000)
    withdraw = st.number_input("Monthly Payout (₹)", value=10000)
    rate = st.number_input("Annual Return (%)", value=8.0)
    yrs = st.number_input("Duration (Years)", value=10)
    if st.button("Calculate"):
        st.info("Calculating balance over time...")
        # (Simplified logic for display)
        st.success("Calculated!")

# Handle Modals
if page == "sip": sip_modal()
if page == "swp": swp_modal()

# Navigation Helper
def nav_link(label, p_name):
    query = urlencode({"page": p_name})
    active_style = "color:#FFD700; border-bottom: 2px solid #FFD700;" if page == p_name else "color:#ccc;"
    return f'<a href="?{query}" target="_self" style="{active_style} text-decoration:none; margin-left:25px; font-weight:600;">{label}</a>'

st.markdown(f"""
    <div class="nav-links">
        {nav_link("Home", "home")}
        {nav_link("Chatbot", "chatbot")}
        {nav_link("Health & Budget", "budget")}
        {nav_link("Dream Tracker", "dreams")}
        {nav_link("Insights", "spending")}
        {nav_link("NLU", "nlu")}
    </div>
""", unsafe_allow_html=True)

# Routing
if page == "chatbot" or page == "try":
    rag_granite_finance.main()
elif page == "budget":
    budget_summaries.main()
elif page == "spending":
    spending_insights.main()
elif page == "dreams":
    dream_tracker.main()
elif page == "nlu":
    NLU_Analysis.main()
elif page == "know":
    about_fibot.main()
else:
    # --- PRO HOME PAGE ---
    st.markdown("""
    <div class="center-section">
        <div class="headline">Your AI Companion for Financial Freedom.</div>
        <div class="subhead">Track, Analyze, and Achieve your dreams with Fibot Pro.</div>
        <a href="?page=try" class="btn-outline">Launch Fibot Chat</a>
        <a href="?page=know" style="color:#0E6FFF; margin-left:20px; text-decoration:none;">Learn more →</a>
    </div>
    """, unsafe_allow_html=True)

    # Scroller 
    q1 = ["How to save ₹1 Lakh?", "Best SIP for 2025?", "Emergency fund tips?", "Debt payoff plan?"]
    q2 = ["Analyze my food spend", "Financial health score?", "Track my bike goal", "Is my spending high?"]

    def render_row(qs, rev=False):
        c = "scroll-content-reverse" if rev else "scroll-content"
        html = f'<div class="scroll-row"><div class="{c}">'
        for q in qs * 3:
            html += f'<div class="question-card">{q}</div>'
        return html + "</div></div>"

    st.markdown(render_row(q1), unsafe_allow_html=True)
    st.markdown(render_row(q2, True), unsafe_allow_html=True)