import streamlit as st
import pandas as pd
import os
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
from db_utils import get_db  # Import your central utility

# --- CRITICAL: CACHED AGGREGATION ---
# This function calculates total savings in the cloud and caches the result for 60 seconds.
@st.cache_data(ttl=60)
def get_cloud_savings_total():
    try:
        db = get_db()
        pipeline = [
            {"$match": {"category": {"$in": ["Savings", "Investments", "Investment"]}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        aggregation_result = list(db.transactions.aggregate(pipeline))
        return aggregation_result[0]['total'] if aggregation_result else 0
    except Exception as e:
        return 0

# --- CRITICAL: CACHED GOALS LIST ---
@st.cache_data(ttl=60)
def fetch_cloud_goals():
    try:
        db = get_db()
        # MongoDB cursors must be converted to a list to be cached
        return list(db.user_goals.find().sort("created_at", 1))
    except Exception as e:
        st.error(f"Error fetching goals: {e}")
        return []

def main():
    st.title("🎯 Dream Tracker Pro (Cloud)")
    st.markdown("Set your sights on financial freedom and track your progress in real-time.")

    # --- Database Initialization ---
    try:
        db = get_db()
        goals_col = db.user_goals
    except Exception as e:
        st.error(f"Cloud Connection Failed: {e}")
        st.stop()

    # --- 1. Add New Goal Section ---
    with st.expander("✨ Define a New Dream"):
        col1, col2 = st.columns([2, 1])
        with col1:
            g_name = st.text_input("What is your dream?", placeholder="e.g. Emergency Fund")
        with col2:
            g_target = st.number_input("Target Amount (₹)", min_value=100, step=500)
            
        if st.button("Add to My Cloud Dreams", use_container_width=True):
            if g_name and g_target > 0:
                # Cloud Insert
                goals_col.insert_one({
                    "name": g_name,
                    "target": g_target,
                    "created_at": datetime.now()
                })
                # Clear cache so new data shows immediately
                st.cache_data.clear()
                st.success(f"Dream '{g_name}' synced to cloud!")
                st.rerun()
            else:
                st.error("Please enter a valid name and target.")

    # --- 2. Progress Calculation (Using Cached Functions) ---
    st.divider()
    st.subheader("🚀 Your Financial Journey")

    # Fetch live total from cached cloud aggregation
    total_saved = get_cloud_savings_total()

    # Retrieve Goals from cached cloud fetch
    goals_list = fetch_cloud_goals()
    
    if not goals_list:
        st.info("You haven't set any cloud dreams yet. Add one above to get started!")
    else:
        for goal in goals_list:
            name = goal.get("name", "Unnamed Goal")
            target = goal.get("target", 0)
            
            st.markdown(f"### {name}")
            
            # Progress calculation
            progress_val = min(total_saved / target, 1.0) if target > 0 else 0.0
            
            # Display UI Components
            c1, c2 = st.columns([3, 1])
            with c1:
                st.progress(progress_val)
            with c2:
                st.metric("Total Saved", f"₹{total_saved:,.0f}", f"{progress_val*100:.1f}%")
            
            st.caption(f"Status: ₹{total_saved:,.0f} saved of ₹{target:,.0f} target")
            
            # Delete Feature
            if st.button(f"Remove {name}", key=f"del_{goal['_id']}"):
                goals_col.delete_one({"_id": goal["_id"]})
                # Clear cache to reflect deletion
                st.cache_data.clear()
                st.rerun()

            # Celebrate Completion
            if progress_val >= 1.0:
                st.balloons()
                st.success(f"🏆 **Goal Achieved!** You've reached your target for {name}!")
            
            st.markdown("<br>", unsafe_allow_html=True)

    # --- 3. Sidebar Gamification ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("🏅 Cloud Milestone")
    if goals_list:
        next_goal = goals_list[0]['name']
        st.sidebar.write(f"Keep tracking to reach your **{next_goal}**!")
    else:
        st.sidebar.write("Set a cloud goal to earn the **Dreamer** badge!")

if __name__ == "__main__":
    main()