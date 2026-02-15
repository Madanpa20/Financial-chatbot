import streamlit as st
from pymongo import MongoClient
import os
import certifi
from dotenv import load_dotenv

load_dotenv()

@st.cache_resource
def get_db():
    """Cached connection to MongoDB Atlas."""
    ca = certifi.where()
    client = MongoClient(os.getenv("MONGO_URI"), tlsCAFile=ca)
    return client.fibot_pro_db