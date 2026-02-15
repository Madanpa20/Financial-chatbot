import streamlit as st
import io, os, time
from datetime import datetime
from dotenv import load_dotenv
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
from google import genai
from db_utils import get_db

# --- CACHED DATA FETCHING ---
@st.cache_data(ttl=300) 
def fetch_cloud_history_cached():
    try:
        db = get_db()
        return list(db.search_history.find().sort("timestamp", -1).limit(12))
    except Exception:
        return []

def main():
    load_dotenv()
    db = get_db()
    history_col = db.search_history

    # --- State Initialization ---
    if "user_query" not in st.session_state: st.session_state.user_query = ""
    if "selected_history" not in st.session_state: st.session_state.selected_history = None
    if "last_request_time" not in st.session_state: st.session_state.last_request_time = 0

    GEMINI_API_KEY4 = os.getenv("GEMINI_API_KEY4", "")
    client = genai.Client(api_key=GEMINI_API_KEY4)

    def answer_question(question):
        try:
            # Active 2025 AI Models
            models_to_try = ["gemini-3-flash", "gemini-2.5-flash", "gemini-2.0-flash"]
            for model_name in models_to_try:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=f"You are a professional financial advisor. Answer this clearly: {question}"
                    )
                    return response.text.strip()
                except Exception:
                    continue
            return "⚠️ No available models found. Check cloud API permissions."
        except Exception as e:
            return f"⚠️ Response Error: {str(e)}"
    st.title("💬 Finance Chatbot")

    # --- Sidebar: History Selection ---
    st.sidebar.header("📜 Cloud Search History")
    cloud_history = fetch_cloud_history_cached()
    
    if cloud_history:
        for idx, doc in enumerate(cloud_history):
            q = doc.get("question", "No query")
            a = doc.get("answer", "No answer")
            # When history button is clicked, we set the state and STOP the script 
            # to prevent it from reaching the AI generation logic below.
            if st.sidebar.button(q[:30] + "...", key=f"hist_{idx}"):
                st.session_state.selected_history = (q, a)
                st.session_state.user_query = "" # Clear input to prevent auto-search
                st.rerun() 
    else:
        st.sidebar.write("No searches yet.")

    # 🎙 Speech Section
    audio_data = mic_recorder(start_prompt="🎙 Speak", stop_prompt="⏹ Stop", just_once=True, format="wav")
    if audio_data:
        try:
            wav_bytes = io.BytesIO(audio_data["bytes"])
            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_bytes) as source:
                audio = recognizer.record(source)
            st.session_state.user_query = recognizer.recognize_google(audio)
            st.rerun() 
        except Exception: pass

    # ✍️ Manual Query Input
    user_question = st.text_input("Ask a question:", value=st.session_state.user_query)

    # --- Search Logic (Only runs for NEW queries) ---
    if st.button("Search"):
        query = user_question.strip()
        if query:
            # Throttle to prevent "No available models" error from API spamming
            if time.time() - st.session_state.last_request_time < 2:
                st.warning("Please wait 2 seconds...")
            else:
                with st.spinner("Fibot is generating a new answer..."):
                    answer = answer_question(query)
                    st.session_state.last_request_time = time.time()
                
                # Cloud Storage
                history_col.insert_one({"question": query, "answer": answer, "timestamp": datetime.now()})
                
                # Update state and clear cache
                st.cache_data.clear()
                st.session_state.selected_history = (query, answer)
                st.session_state.user_query = ""
                st.rerun()

    # --- RESULTS DISPLAY ---
    if st.session_state.selected_history:
        q_show, a_show = st.session_state.selected_history
        st.markdown("---")
        st.subheader(f"🔍 {q_show}")
        st.info(a_show)

if __name__ == "__main__":
    main()