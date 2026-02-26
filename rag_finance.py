import streamlit as st
from pathlib import Path
from datasets import load_dataset
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch, io, csv, os
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr

HISTORY_FILE = "search_history.csv"

# ----------------------------- Save & Load History -----------------------------
def load_history_from_csv():
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:  # Only Q and A
                    q = row[0]
                    a = row[1]
                    history.append((q, a))
    return history

def save_history_to_csv(history):
    with open(HISTORY_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        for q, a in history:
            writer.writerow([q, a])

def main():
    if "voice_text" not in st.session_state:
        st.session_state.voice_text = ""
    if "history" not in st.session_state:
        st.session_state.history = load_history_from_csv()  # Load persisted history
    if "selected_history" not in st.session_state:
        st.session_state.selected_history = None

    INDEX_DIR = "faiss_index"
    EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    GRANITE_MODEL = "ibm-granite/granite-3.3-2b-instruct"
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50
    TOP_K = 2

    @st.cache_resource
    def build_or_load_faiss():
        if Path(INDEX_DIR).exists():
            embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
            return FAISS.load_local(INDEX_DIR, embeddings, allow_dangerous_deserialization=True)

        hf_datasets = [
            "SALT-NLP/FLUE-FiQA",
            "sujet-ai/Sujet-Finance-Instruct-177k",
            "bilalRahib/fiqa-personal-finance-dataset" 
        ]
        all_texts = []
        for ds_name in hf_datasets:
            ds = load_dataset(ds_name)
            train = ds["train"]
            cols = train.column_names
            if "text" in cols:
                all_texts.extend(train["text"])
            elif "sentence" in cols:
                all_texts.extend(train["sentence"])
            elif "question" in cols and "answer" in cols:
                all_texts.extend([f"Q: {q}\nA: {a}" for q, a in zip(train["question"], train["answer"])])
            else:
                all_texts.extend(train[cols[0]])

        splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        chunks = []
        for txt in all_texts:
            chunks.extend(splitter.split_text(str(txt)))

        embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
        vectorstore = FAISS.from_texts(chunks, embeddings)
        vectorstore.save_local(INDEX_DIR)
        return vectorstore

    @st.cache_resource
    def load_granite_llm():
        tokenizer = AutoTokenizer.from_pretrained(GRANITE_MODEL)
        if torch.cuda.is_available():
            model = AutoModelForCausalLM.from_pretrained(
                GRANITE_MODEL,
                torch_dtype=torch.float16,
                device_map=None
            )
            model=model.to("cuda")
        else:
            model = AutoModelForCausalLM.from_pretrained(
                GRANITE_MODEL,
                torch_dtype=torch.float32,
                device_map={"": "cpu"}
            )
        return pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=256,
            temperature=0.2,
            do_sample=False
        )

    def answer_question(granite_pipe, vectorstore, question):
        docs = vectorstore.similarity_search(question, k=TOP_K)
        context = "\n\n---\n\n".join([d.page_content for d in docs]) or "No relevant context found."
        prompt = (
            f"You are a financial assistant. "
            f"Use ONLY the context below to answer the question.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\nAnswer:"
        )
        output = granite_pipe(prompt, max_new_tokens=256, temperature=0.2, do_sample=False, return_full_text=False)
        answer = output[0]['generated_text'].strip()
        return answer, [d.page_content for d in docs]

    st.set_page_config(page_title="Finance Chatbot", layout="wide")
    st.title("💬 Finance Chatbot (IBM Granite )")

    # Sidebar: Show persisted history
    st.sidebar.header("📜 Search History")
    if st.session_state.history:
        for idx, (q, a) in enumerate(st.session_state.history):
            if st.sidebar.button(q[:30] + ("..." if len(q) > 30 else ""), key=f"hist_{idx}"):
                st.session_state.selected_history = (q, a, [])
    else:
        st.sidebar.write("No searches yet.")

    vectorstore = build_or_load_faiss()
    granite_pipe = load_granite_llm()

    st.markdown("#### 🎙 Speak your query:")
    audio_data = mic_recorder(
        start_prompt="🎙 Start Recording",
        stop_prompt="⏹ Stop Recording",
        just_once=True,
        use_container_width=True,
        format="wav"
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

    user_question = st.text_input("Ask your finance question:", placeholder="Ask Fibot?", value=st.session_state.voice_text)

    if user_question.strip() and (not st.session_state.history or st.session_state.history[-1][0] != user_question):
        with st.spinner("Generating answer..."):
            answer, sources = answer_question(granite_pipe, vectorstore, user_question)
        st.session_state.history.append((user_question, answer))
        save_history_to_csv(st.session_state.history)  # Persist immediately
        st.session_state.selected_history = (user_question, answer, sources)
        st.session_state.voice_text = ""

    if st.session_state.selected_history:
        q, a, src = st.session_state.selected_history
        st.subheader(f"🔍 {q}")
        st.write(a)
        if src:
            with st.expander("Sources"):
                for i, s in enumerate(src, 1):
                    st.write(f"{i}. {s[:300]}...")

if __name__ == "__main__":
    main()