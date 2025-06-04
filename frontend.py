import streamlit as st
import pandas as pd
from datetime import datetime
from processor import Processor
import os

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


def get_files():
    files = os.listdir("CleanedData")
    files_list = []
    for file in files:
        if file.endswith(".csv"):
            files_list.append(file[:-4])
    return files_list


st.title("Survey Bot")



processor = Processor("kc_house_data.csv")


def get_response_and_data(user_input):
    response = processor.create_query(user_input)
    #print(response)
    data = processor.execute_query(response)
    
    return response, data

# Main chat interface
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.container():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if "data" in message:
                st.dataframe(message["data"], use_container_width=True)
            if "graph" in message:
                st.plotly_chart(message["graph"], use_container_width=True, key=f"graph_{message['role']}_{len(st.session_state.messages)}")

    if prompt := st.chat_input("What would you like to know?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        response_text, response_data = get_response_and_data(prompt)
        graphs = processor.get_graph(response_text)
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "Here's the response:",
            "data": response_data,
            "graph": graphs[0] if graphs else None  # Store first graph for backward compatibility
        })
        with st.chat_message("assistant"):
            st.write(response_text)
            st.dataframe(response_data, use_container_width=True)
            # Display all graphs with unique keys
            for i, graph in enumerate(graphs):
                st.plotly_chart(graph, use_container_width=True, key=f"graph_assistant_{len(st.session_state.messages)}_{i}")
