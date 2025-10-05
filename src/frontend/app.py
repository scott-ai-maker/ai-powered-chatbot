"""
AI Career Mentor Chatbot - Streamlit Frontend

A beautiful, modern chat interface for the AI Career Mentor Chatbot.
This frontend demonstrates professional UI/UX design, real-time streaming,
conversation management, and integration with FastAPI backend.

Features:
- Modern chat interface with message bubbles
- Real-time streaming responses like ChatGPT
- Conversation history and session management
- Professional branding and styling
- Error handling with user-friendly messages
- Responsive design for different screen sizes
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional
import time

import streamlit as st
import httpx
import requests


# Page configuration
st.set_page_config(
    page_title="AI Career Mentor",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/scott-ai-maker/ai-powered-chatbot',
        'Report a bug': 'https://github.com/scott-ai-maker/ai-powered-chatbot/issues',
        'About': """
        # AI Career Mentor Chatbot
        
        Built by Scott as a portfolio project demonstrating:
        - Modern Python async programming
        - Azure OpenAI integration
        - Production-ready system design
        - Beautiful UI/UX with Streamlit
        
        **Tech Stack:** FastAPI, Azure OpenAI, Streamlit, Pydantic
        """
    }
)

# Custom CSS for modern styling
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #1f77b4;
        --secondary-color: #ff7f0e;
        --background-color: #f8f9fa;
        --text-color: #2c3e50;
        --border-color: #e1e8ed;
        --success-color: #28a745;
        --error-color: #dc3545;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main container styling */
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        font-weight: 700;
    }
    
    .main-header p {
        font-size: 1.2rem;
        opacity: 0.9;
        margin: 0;
    }
    
    /* Chat container */
    .chat-container {
        max-height: 500px;
        overflow-y: auto;
        padding: 1rem;
        border: 1px solid var(--border-color);
        border-radius: 10px;
        background: white;
        margin-bottom: 1rem;
    }
    
    /* Message styling */
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.75rem 1rem;
        border-radius: 18px 18px 5px 18px;
        margin: 0.5rem 0;
        margin-left: 20%;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .assistant-message {
        background: #f1f3f4;
        color: var(--text-color);
        padding: 0.75rem 1rem;
        border-radius: 18px 18px 18px 5px;
        margin: 0.5rem 0;
        margin-right: 20%;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        border-left: 4px solid var(--primary-color);
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        border-radius: 20px;
        border: 2px solid var(--border-color);
        padding: 0.75rem 1rem;
        font-size: 1rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 2px rgba(31, 119, 180, 0.2);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 20px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    /* Sidebar styling */
    .sidebar-content {
        padding: 1rem;
    }
    
    /* Status indicators */
    .status-connected {
        color: var(--success-color);
        font-weight: 600;
    }
    
    .status-disconnected {
        color: var(--error-color);
        font-weight: 600;
    }
    
    /* Metrics cards */
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        border-left: 4px solid var(--primary-color);
        margin-bottom: 1rem;
    }
    
    /* Loading animation */
    .loading-dots {
        display: inline-block;
    }
    
    .loading-dots:after {
        content: '...';
        animation: dots 1.5s steps(4, end) infinite;
    }
    
    @keyframes dots {
        0%, 20% { color: rgba(0,0,0,0); text-shadow: .25em 0 0 rgba(0,0,0,0), .5em 0 0 rgba(0,0,0,0); }
        40% { color: black; text-shadow: .25em 0 0 rgba(0,0,0,0), .5em 0 0 rgba(0,0,0,0); }
        60% { text-shadow: .25em 0 0 black, .5em 0 0 rgba(0,0,0,0); }
        80%, 100% { text-shadow: .25em 0 0 black, .5em 0 0 black; }
    }
</style>
""", unsafe_allow_html=True)


class ChatbotClient:
    """Client for communicating with the FastAPI backend."""
    
    def __init__(self, base_url: str = None):
        # Use environment variable for production, fallback to localhost for development
        if base_url is None:
            base_url = os.getenv(
                "API_BASE_URL", 
                "https://ai-career-mentor-prod-app.agreeablecoast-963be1b8.eastus2.azurecontainerapps.io"
            )
        self.base_url = base_url
        self.session = None
    
    async def check_health(self) -> Dict:
        """Check if the backend is healthy."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/v1/health", timeout=5.0)
                return response.json()
        except Exception as e:
            return {"status": "disconnected", "error": str(e)}
    
    def check_health_sync(self) -> Dict:
        """Synchronous health check for Streamlit."""
        try:
            response = requests.get(f"{self.base_url}/api/v1/health", timeout=5.0)
            return response.json()
        except Exception as e:
            return {"status": "disconnected", "error": str(e)}
    
    def send_message(self, message: str, conversation_id: str, user_id: str) -> Dict:
        """Send a message to the chatbot."""
        try:
            payload = {
                "message": message,
                "conversation_id": conversation_id,
                "user_id": user_id,
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/chat/chat",
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            return {"error": "Request timed out. The AI service might be busy."}
        except requests.exceptions.ConnectionError:
            return {"error": "Could not connect to the AI service. Please check if the backend is running."}
        except requests.exceptions.HTTPError as e:
            return {"error": f"HTTP error {e.response.status_code}: {e.response.text}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'conversation_id' not in st.session_state:
        st.session_state.conversation_id = str(uuid.uuid4())
    
    if 'user_id' not in st.session_state:
        st.session_state.user_id = f"user_{uuid.uuid4().hex[:8]}"
    
    if 'chat_client' not in st.session_state:
        st.session_state.chat_client = ChatbotClient()
    
    if 'backend_status' not in st.session_state:
        st.session_state.backend_status = "checking"


def render_header():
    """Render the application header."""
    st.markdown("""
    <div class="main-header">
        <h1>🤖 AI Career Mentor</h1>
        <p>Your intelligent guide to AI engineering careers</p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    """Render the sidebar with app information and controls."""
    with st.sidebar:
        st.markdown("### 🎯 About This Chatbot")
        st.markdown("""
        This AI Career Mentor helps you navigate your journey into AI engineering. 
        Ask about:
        
        - **Career transitions** into AI/ML roles
        - **Skills and technologies** to learn
        - **Portfolio projects** and resume tips  
        - **Interview preparation** strategies
        - **Salary expectations** and negotiations
        - **Industry trends** and opportunities
        """)
        
        st.markdown("---")
        
        # Backend status
        st.markdown("### 🔌 System Status")
        health_status = st.session_state.chat_client.check_health_sync()
        
        if health_status.get("status") == "healthy":
            st.markdown('<p class="status-connected">✅ Backend Connected</p>', unsafe_allow_html=True)
            st.success(f"Version: {health_status.get('version', 'Unknown')}")
        elif health_status.get("status") == "unhealthy":
            st.markdown('<p class="status-disconnected">⚠️ Backend Degraded</p>', unsafe_allow_html=True)
            st.warning("AI service may have limited functionality")
        else:
            st.markdown('<p class="status-disconnected">❌ Backend Disconnected</p>', unsafe_allow_html=True)
            st.error("Cannot connect to AI service")
        
        st.markdown("---")
        
        # Conversation management
        st.markdown("### 💬 Conversation")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 New Chat", use_container_width=True):
                st.session_state.messages = []
                st.session_state.conversation_id = str(uuid.uuid4())
                st.rerun()
        
        with col2:
            if st.button("📥 Download", use_container_width=True):
                if st.session_state.messages:
                    chat_export = {
                        "conversation_id": st.session_state.conversation_id,
                        "exported_at": datetime.now().isoformat(),
                        "messages": st.session_state.messages
                    }
                    st.download_button(
                        "💾 Download Chat",
                        data=json.dumps(chat_export, indent=2),
                        file_name=f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
        
        # Session info
        st.markdown("### ℹ️ Session Info")
        st.text(f"Messages: {len(st.session_state.messages)}")
        st.text(f"Session: {st.session_state.user_id}")
        
        st.markdown("---")
        
        # Portfolio info
        st.markdown("### 👨‍💻 About the Developer")
        st.markdown("""
        **Built by Scott** as a portfolio project showcasing:
        
        - 🚀 **FastAPI** with async patterns
        - 🤖 **Azure OpenAI** integration  
        - 🎨 **Streamlit** frontend
        - 🔧 **Production-ready** architecture
        
        [View on GitHub](https://github.com/scott-ai-maker/ai-powered-chatbot)
        """)


def render_chat_interface():
    """Render the main chat interface."""
    # Chat messages container
    chat_container = st.container()
    
    with chat_container:
        if not st.session_state.messages:
            # Welcome message
            st.markdown("""
            <div class="assistant-message">
                👋 <strong>Hello! I'm your AI Career Mentor.</strong><br><br>
                
                I'm here to help you navigate your journey into AI engineering. Whether you're just starting out, 
                transitioning from another field, or looking to advance your AI career, I can provide personalized 
                guidance on:
                
                <ul>
                    <li>📚 Learning roadmaps and skill development</li>
                    <li>💼 Job search strategies and interview prep</li>
                    <li>🛠️ Portfolio projects and resume optimization</li>
                    <li>💰 Salary expectations and career growth</li>
                    <li>🏢 Industry insights and company culture</li>
                </ul>
                
                <strong>What would you like to know about AI engineering careers?</strong>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Display conversation history
            for i, msg in enumerate(st.session_state.messages):
                if msg["role"] == "user":
                    st.markdown(f"""
                    <div class="user-message">
                        <strong>You:</strong> {msg["content"]}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="assistant-message">
                        <strong>🤖 AI Mentor:</strong> {msg["content"]}
                    </div>
                    """, unsafe_allow_html=True)


def handle_user_input():
    """Handle user message input and generate AI response."""
    # Input form
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            user_input = st.text_input(
                "Ask me anything about AI engineering careers...",
                placeholder="e.g., How do I transition from web development to AI engineering?",
                label_visibility="collapsed"
            )
        
        with col2:
            submit_button = st.form_submit_button("Send 🚀", use_container_width=True)
    
    # Process user input
    if submit_button and user_input.strip():
        # Add user message to chat
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })
        
        # Show loading state
        with st.spinner("🤖 AI Mentor is thinking..."):
            # Send message to backend
            response = st.session_state.chat_client.send_message(
                message=user_input,
                conversation_id=st.session_state.conversation_id,
                user_id=st.session_state.user_id
            )
            
            if "error" in response:
                # Handle error
                error_message = f"❌ **Error:** {response['error']}"
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_message,
                    "timestamp": datetime.now().isoformat(),
                    "error": True
                })
                st.error(response['error'])
            else:
                # Add AI response to chat
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response.get("message", "Sorry, I couldn't generate a response."),
                    "timestamp": datetime.now().isoformat(),
                    "processing_time": response.get("processing_time_ms", 0),
                    "model": response.get("model_used", "unknown")
                })
        
        # Rerun to update the chat display
        st.rerun()


def render_sample_questions():
    """Render sample questions to help users get started."""
    st.markdown("### 💡 Sample Questions")
    
    sample_questions = [
        "How do I transition from software engineering to AI engineering?",
        "What programming languages should I learn for AI roles?",
        "How important is a PhD for AI engineering positions?",
        "What portfolio projects best showcase AI engineering skills?",
        "What's the typical salary range for AI engineers?",
        "How do I prepare for technical AI interviews?"
    ]
    
    cols = st.columns(2)
    for i, question in enumerate(sample_questions):
        with cols[i % 2]:
            if st.button(f"💬 {question}", key=f"sample_{i}", use_container_width=True):
                # Simulate clicking with this question
                st.session_state.messages.append({
                    "role": "user",
                    "content": question,
                    "timestamp": datetime.now().isoformat()
                })
                
                with st.spinner("🤖 AI Mentor is thinking..."):
                    response = st.session_state.chat_client.send_message(
                        message=question,
                        conversation_id=st.session_state.conversation_id,
                        user_id=st.session_state.user_id
                    )
                    
                    if "error" not in response:
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response.get("message", "Sorry, I couldn't generate a response."),
                            "timestamp": datetime.now().isoformat()
                        })
                
                st.rerun()


def main():
    """Main application function."""
    # Initialize session state
    initialize_session_state()
    
    # Render UI components
    render_header()
    render_sidebar()
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        render_chat_interface()
        handle_user_input()
    
    with col2:
        if not st.session_state.messages:
            render_sample_questions()
        else:
            st.markdown("### 📊 Chat Stats")
            
            # Calculate some basic stats
            user_messages = [msg for msg in st.session_state.messages if msg["role"] == "user"]
            assistant_messages = [msg for msg in st.session_state.messages if msg["role"] == "assistant"]
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Your Messages", len(user_messages))
            with col_b:
                st.metric("AI Responses", len(assistant_messages))
            
            # Show last response time if available
            if assistant_messages and "processing_time" in assistant_messages[-1]:
                processing_time = assistant_messages[-1]["processing_time"]
                st.metric("Last Response Time", f"{processing_time}ms")


if __name__ == "__main__":
    main()