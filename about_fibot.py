import streamlit as st
def main():
    st.title("About Fibot")
    st.write("""
    ## Who We Are
    Fibot is your **AI-powered personal financial assistant** designed to make money
    management simple, accessible, and intelligent. We combine modern data analysis
    with natural language understanding to give you personalized, actionable insights
    — whether you’re budgeting, investing, or planning for your future.

    ## Our Mission
    To empower individuals and businesses to make **smarter financial decisions**
    through AI-driven tools, clear insights, and easy-to-understand advice.

    ## Our Solution
    Managing finances can be overwhelming — scattered data, confusing reports,
    and lack of clarity often get in the way. Fibot solves this by:
    - **Centralizing Your Financial View** — One place for budgets, expenses, and investments.
    - **Providing AI-Powered Insights** — Turn raw data into clear recommendations.
    - **Understanding Natural Language** — Ask Fibot your questions, just like chatting with a friend.
    - **Making Decisions Simpler** — Our clean interface and powerful analytics
      help you focus on action, not just information.

    ## Key Features
    - **Budget Summary**: Quickly see where your money is going and where you can save.
    - **Spending Insights**: Identify patterns and control overspending.
    - **NLU Analysis**: Understand complex financial queries and provide meaningful answers.
    - **Interactive Chatbot**: Get instant advice, tips, and tailored solutions.

    ## Why Choose Fibot?
    - **Fast & Smart** — Powered by cutting-edge AI.
    - **User-Friendly** — No financial jargon, just clear language.
    - **Secure** — Your data stays private and protected.
    - **Action-Oriented** — We don’t just show you numbers, we help you decide what to do next.

    ---
    _Financial freedom isn’t just a dream — with Fibot, it’s a plan._
    """)

    # Back to Home button
    st.markdown('<a href="?page=home"><button style="background-color:#0E6FFF; color:white; padding:10px 20px; border:none; border-radius:8px; cursor:pointer;">Back to Home</button></a>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
