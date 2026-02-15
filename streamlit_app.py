# streamlit_app.py
import streamlit as st
#from rag_granite_finance import build_or_load_index, load_finance_corpus, load_granite_llm, answer_question
def main():
    """
    st.set_page_config(page_title="Financial Q&A (Granite + FAISS)", layout="centered")
    st.title("💬 Financial Q&A (IBM Granite + FAISS)")

    @st.cache_resource
    def _boot():
        corpus = load_finance_corpus()
        vs, _ = build_or_load_index(corpus)
        llm = load_granite_llm()
        return vs, llm

    vectorstore, llm = _boot()

    q = st.text_area("Ask a financial question:", height=120, placeholder="e.g., What is SIP? How to start a budget?")
    if st.button("Get Answer") and q.strip():
        with st.spinner("Thinking..."):
            answer, sources = answer_question(llm, vectorstore, q.strip())
        st.subheader("Answer")
        st.write(answer)
        with st.expander("Sources (retrieved context)"):
            for i, s in enumerate(sources, 1):
                st.markdown(f"**{i}.** {s[:600]}{'...' if len(s)>600 else ''}")
    """
    return 0
if __name__ == "__main__":
    main()
