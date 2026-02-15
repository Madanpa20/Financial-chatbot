import streamlit as st
import google.generativeai as genai
import json,io,os
import tempfile
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
from dotenv import load_dotenv
def main():
    # ------------------------
    # Configure Gemini API
    # ------------------------
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY2")  # Replace with your key
    genai.configure(api_key=api_key) # Replace with your key

    if "context" not in st.session_state:
        st.session_state.context = ""  # For multi-turn context
    if "voice_text" not in st.session_state:
        st.session_state.voice_text = ""
    st.set_page_config(page_title="Financial NLU Analyzer", page_icon="💬", layout="centered")

    # Inject CSS for styling
    st.markdown("""
    <style>
    .intent-badge {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 20px;
        background-color: #3498DB;
        color: white;
        font-weight: bold;
        font-size: 16px;
    }
    .sentiment-positive {background-color: #2ECC71; color: white; padding: 5px; border-radius: 8px;}
    .sentiment-negative {background-color: #E74C3C; color: white; padding: 5px; border-radius: 8px;}
    .sentiment-neutral {background-color: #95A5A6; color: white; padding: 5px; border-radius: 8px;}
    .category-pill {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 20px;
        background-color: #f1c40f;
        color: black;
        font-weight: 500;
        font-size: 12px;
    }
    .glass-card {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 9px;
        padding: 9px;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .date-tag {
        display: inline-block;
        background-color: #3498DB;
        color: white;
        padding: 6px 12px;
        border-radius: 20px;
        margin: 5px;
        font-size: 14px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("💬 Financial NLU Analyzer")
    st.markdown("Enter a financial query below. The NLU will detect intent, entities, sentiment, categories, amounts, dates, and more.")
    # 🎤 Voice Recorder
    st.markdown("#### 🎙 Speak your query:")
    audio_data = mic_recorder(
        start_prompt="🎙 Start Recording",
        stop_prompt="⏹ Stop Recording",
        just_once=True,
        use_container_width=True,
        format="wav"  # <— record as WAV instead of WebM
    )

    if audio_data:
       try:
        wav_bytes = io.BytesIO(audio_data["bytes"])
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_bytes) as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio)
        st.session_state.voice_text = text
        st.success(f"Recognized Speech: {text}")


       except Exception as e:
            st.error(f"Speech recognition error: {e}")
    # ------------------------
    # User Input
    # ------------------------
    user_query = st.text_area("Enter your query:", placeholder="e.g., Show my expenses for last month",value=st.session_state.voice_text)

    if st.button("Analyze"):
        if user_query.strip() == "":
            st.warning("Please enter a query before analyzing.")
        else:
            with st.spinner("Analyzing..."):
                prompt = f"""
    You are a financial Natural Language Understanding (NLU) assistant.
    Analyze the user's input and return ONLY valid JSON with the following keys:

    - intent: string
    - entities: list of {{type: string, value: string}}
    - sentiment: one of ["positive", "negative", "neutral"]
    - categories: list of spending categories (e.g., Food, Rent, Investments)
    - amounts: list of {{value: float, currency: string}}
    - dates: list of temporal expressions
    - notes: any finance-specific terms (ROI, mutual funds, interest rate, etc.)

    Also use this conversation history for context:
    {st.session_state.context}

    User query: "{user_query}"

    Important:
    - Output must be ONLY valid JSON
    - No markdown, no explanation, no code fences
    """

                try:
                    model = genai.GenerativeModel("gemini-2.5-flash")  # Or latest model
                    response = model.generate_content(prompt)

                    result_text = response.candidates[0].content.parts[0].text.strip()

                    if result_text.startswith("```"):
                        result_text = result_text.strip("`").strip()
                        if result_text.lower().startswith("json"):
                            result_text = result_text[4:].strip()

                    data = json.loads(result_text)

                    # -------- Structured Display --------
                    st.markdown(f"<div class='intent-badge'>Intent: {data.get('intent', 'N/A')}</div>", unsafe_allow_html=True)

                    # Sentiment color
                    sentiment = data.get("sentiment", "neutral").lower()
                    sentiment_class = f"sentiment-{sentiment}"
                    st.markdown(f"<div class='{sentiment_class}'>Sentiment: {sentiment.capitalize()}</div>", unsafe_allow_html=True)

                    # Entities Table
                    st.subheader("📌 Extracted Entities")
                    if data.get("entities"):
                        st.table(data["entities"])
                    else:
                        st.info("No entities detected.")

                    # Spending Categories as pills
                    st.subheader("🏷 Spending Categories")
                    if data.get("categories"):
                        cat_html = " ".join([f"<span class='category-pill'>{c}</span>" for c in data["categories"]])
                        st.markdown(cat_html, unsafe_allow_html=True)
                    else:
                        st.info("No categories found.")

                    # Amounts Table
                    st.subheader("💰 Amounts")
                    if data.get("amounts"):
                        st.table(data["amounts"])
                    else:
                        st.info("No amounts found.")

                    # Dates
                    st.subheader("📅 Dates / Time References")
                    if data.get("dates"):
                        if isinstance(data["dates"], list):
                            tags_html = "".join([f"<span class='date-tag'>{date}</span>" for date in data["dates"]])
                        else:
                            tags_html = f"<span class='date-tag'>{data['dates']}</span>"
                        
                        # ✅ Always display after building
                        st.markdown(tags_html, unsafe_allow_html=True)
                    else:
                        st.info("No date references found.")

                    # Notes in glass card
                    st.subheader("📓 Financial Notes")
                    if data.get("notes"):
                        st.markdown(f"<div class='glass-card'>{', '.join(data['notes'])}</div>", unsafe_allow_html=True)
                    else:
                        st.info("No special financial terms detected.")

                    st.session_state.context += f"\nUser: {user_query}\nNLU: {json.dumps(data)}"

                except json.JSONDecodeError:
                    st.error("AI did not return valid JSON. See raw output below:")
                    st.code(result_text)

                except Exception as e:
                    st.error(f"Error: {e}")

    # Footer
    st.markdown("---")
    st.caption("💡 Tip: Try queries like 'I spent ₹500 on groceries last week' or 'Show my investment returns this year'")

if __name__ == "__main__":
    main()