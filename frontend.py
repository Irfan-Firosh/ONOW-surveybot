import streamlit as st
import pandas as pd
from datetime import datetime
from processor import Processor

st.set_page_config(
    page_title="Survey Bot",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Minimal CSS to keep chat input fixed at the bottom, less wide, and with bottom padding
st.markdown("""
    <style>
    .stChatInput {
        position: fixed;
        bottom: 2rem;
        left: 50%;
        transform: translateX(-50%);
        width: 60vw;
        max-width: 600px;
        min-width: 300px;
        z-index: 100;
        padding-bottom: 1rem;
    }
    .main .block-container {
        padding-bottom: 7rem;
    }
    </style>
    """, unsafe_allow_html=True)

processor = Processor()

st.title("Survey Bot")

def get_response_and_data(user_input):
    response = processor.create_query(user_input)
    data = processor.execute_query(response)
    
    return "Here's the response:", data

# Main chat interface
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.container():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if "data" in message:
                st.dataframe(message["data"], use_container_width=True)

    if prompt := st.chat_input("What would you like to know?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        response_text, response_data = get_response_and_data(prompt)
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response_text,
            "data": response_data
        })
        with st.chat_message("assistant"):
            st.write(response_text)
            st.dataframe(response_data, use_container_width=True)

