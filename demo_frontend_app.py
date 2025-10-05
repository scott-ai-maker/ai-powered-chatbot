"""
Demo version of the AI Career Mentor Chatbot frontend.
This version uses mock responses to demonstrate functionality.
"""

import streamlit as st
import json
import uuid
from datetime import datetime
import time

# Mock client import
import sys
import os
sys.path.append('.')
from demo_frontend import MockChatbotClient

# Page configuration
st.set_page_config(
    page_title="AI Career Mentor (Demo)",
    page_icon="🤖",
    layout="wide"
)

# Demo notice
st.info("🎭 **Demo Mode**: This is a demonstration using simulated AI responses. The full version integrates with Azure OpenAI for real AI-powered career advice!")

# Initialize session state
if 'demo_client' not in st.session_state:
    st.session_state.demo_client = MockChatbotClient()

if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'conversation_id' not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())

# Header
st.markdown("""
<div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 10px; color: white; text-align: center; margin-bottom: 2rem;">
    <h1>🤖 AI Career Mentor</h1>
    <p>Your intelligent guide to AI engineering careers</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 🎯 Try These Questions")
    
    sample_questions = [
        "How do I transition from web development to AI engineering?",
        "What skills are most important for AI engineering roles?", 
        "What's the typical salary for AI engineers?",
        "Should I get a PhD for AI positions?",
        "What portfolio projects should I build?",
        "How do I prepare for AI engineering interviews?"
    ]
    
    for i, question in enumerate(sample_questions):
        if st.button(f"💬 {question[:40]}...", key=f"q_{i}"):
            st.session_state.messages.append({
                "role": "user",
                "content": question,
                "timestamp": datetime.now().isoformat()
            })
            st.rerun()
    
    st.markdown("---")
    st.markdown("### 🔄 Actions")
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.session_state.conversation_id = str(uuid.uuid4())
        st.rerun()

# Main chat interface
st.markdown("### 💬 Chat with AI Career Mentor")

# Display messages
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 0.75rem 1rem; border-radius: 18px 18px 5px 18px; margin: 0.5rem 0; margin-left: 20%;">
            <strong>You:</strong> {message["content"]}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background: #f1f3f4; padding: 0.75rem 1rem; border-radius: 18px 18px 18px 5px; margin: 0.5rem 0; margin-right: 20%; border-left: 4px solid #667eea;">
            <strong>🤖 AI Mentor:</strong><br>{message["content"]}
        </div>
        """, unsafe_allow_html=True)

# Input form
with st.form("chat_form", clear_on_submit=True):
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_input(
            "Ask me anything about AI engineering careers...",
            placeholder="e.g., How do I get started in AI engineering?",
            label_visibility="collapsed"
        )
    
    with col2:
        submit = st.form_submit_button("Send 🚀", use_container_width=True)

# Process input
if submit and user_input.strip():
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "timestamp": datetime.now().isoformat()
    })
    
    # Show loading and get response
    with st.spinner("🤖 AI Mentor is thinking..."):
        response = st.session_state.demo_client.send_message(
            message=user_input,
            conversation_id=st.session_state.conversation_id,
            user_id="demo_user"
        )
        
        # Add AI response
        st.session_state.messages.append({
            "role": "assistant",
            "content": response["message"],
            "timestamp": datetime.now().isoformat()
        })
    
    st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    <p>🚀 Built with FastAPI, Azure OpenAI, and Streamlit | 
    <a href="https://github.com/scott-ai-maker/ai-powered-chatbot">View on GitHub</a></p>
</div>
""", unsafe_allow_html=True)
