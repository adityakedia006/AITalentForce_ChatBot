"""
Streamlit Frontend for Voice-Enabled Chatbot
Modern UI with dark/light theme toggle, audio input, and chat history
"""

import streamlit as st
import requests
import json
from datetime import datetime
import base64
from pathlib import Path
from audio_recorder_streamlit import audio_recorder
import time

# Page configuration
st.set_page_config(
    page_title="AI Voice Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = ""
if "thinking" not in st.session_state:
    st.session_state.thinking = False


def apply_custom_css():
    """Apply custom CSS based on theme"""
    theme = st.session_state.theme
    
    if theme == "dark":
        primary_bg = "#0E1117"
        secondary_bg = "#262730"
        text_color = "#FAFAFA"
        accent_color = "#FF4B4B"
        user_msg_bg = "#1E3A5F"
        bot_msg_bg = "#2D2D2D"
        border_color = "#3D3D3D"
    else:
        primary_bg = "#FFFFFF"
        secondary_bg = "#F0F2F6"
        text_color = "#262730"
        accent_color = "#FF4B4B"
        user_msg_bg = "#E3F2FD"
        bot_msg_bg = "#F5F5F5"
        border_color = "#E0E0E0"
    
    st.markdown(f"""
    <style>
        /* Main container */
        .main {{
            background-color: {primary_bg};
            color: {text_color};
        }}
        
        /* Chat message styling */
        .chat-message {{
            padding: 1.5rem;
            border-radius: 1rem;
            margin-bottom: 1rem;
            display: flex;
            flex-direction: column;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            animation: fadeIn 0.3s ease-in;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .user-message {{
            background: linear-gradient(135deg, {user_msg_bg} 0%, {user_msg_bg}dd 100%);
            border-left: 4px solid {accent_color};
        }}
        
        .bot-message {{
            background: linear-gradient(135deg, {bot_msg_bg} 0%, {bot_msg_bg}dd 100%);
            border-left: 4px solid #4CAF50;
        }}
        
        .message-header {{
            display: flex;
            align-items: center;
            margin-bottom: 0.5rem;
            font-weight: 600;
            font-size: 0.9rem;
        }}
        
        .message-icon {{
            margin-right: 0.5rem;
            font-size: 1.2rem;
        }}
        
        .message-content {{
            padding-left: 2rem;
            line-height: 1.6;
            font-size: 1rem;
        }}
        
        .message-time {{
            font-size: 0.75rem;
            color: #888;
            margin-top: 0.5rem;
            text-align: right;
        }}
        
        /* Thinking animation */
        .thinking-container {{
            display: flex;
            align-items: center;
            padding: 1rem;
            background: {bot_msg_bg};
            border-radius: 1rem;
            margin-bottom: 1rem;
        }}
        
        .thinking-dots {{
            display: flex;
            gap: 0.5rem;
            margin-left: 1rem;
        }}
        
        .dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: {accent_color};
            animation: bounce 1.4s infinite ease-in-out both;
        }}
        
        .dot:nth-child(1) {{ animation-delay: -0.32s; }}
        .dot:nth-child(2) {{ animation-delay: -0.16s; }}
        
        @keyframes bounce {{
            0%, 80%, 100% {{ transform: scale(0); }}
            40% {{ transform: scale(1); }}
        }}
        
        /* Sidebar styling */
        .sidebar .sidebar-content {{
            background-color: {secondary_bg};
        }}
        
        /* Button styling */
        .stButton > button {{
            border-radius: 0.5rem;
            transition: all 0.3s ease;
        }}
        
        .stButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }}
        
        /* Input styling */
        .stTextInput > div > div > input {{
            border-radius: 0.5rem;
            border: 2px solid {border_color};
        }}
        
        /* Header styling */
        .app-header {{
            padding: 1.5rem;
            background: linear-gradient(135deg, {accent_color} 0%, #FF6B6B 100%);
            border-radius: 1rem;
            margin-bottom: 2rem;
            text-align: center;
            color: white;
            box-shadow: 0 4px 12px rgba(255,75,75,0.3);
        }}
        
        .app-title {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }}
        
        .app-subtitle {{
            font-size: 1rem;
            opacity: 0.9;
        }}
        
        /* Stats cards */
        .stat-card {{
            background: {secondary_bg};
            padding: 1rem;
            border-radius: 0.5rem;
            border: 1px solid {border_color};
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 2rem;
            font-weight: 700;
            color: {accent_color};
        }}
        
        .stat-label {{
            font-size: 0.9rem;
            color: #888;
            margin-top: 0.25rem;
        }}
        
        /* Hide Streamlit branding */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        
        /* Scrollbar styling */
        ::-webkit-scrollbar {{
            width: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: {secondary_bg};
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: {accent_color};
            border-radius: 4px;
        }}
    </style>
    """, unsafe_allow_html=True)


def toggle_theme():
    """Toggle between dark and light theme"""
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"


def clear_chat():
    """Clear chat history"""
    st.session_state.messages = []
    st.session_state.conversation_history = []
    st.success("✨ Chat cleared!")


def send_message(message: str, audio_data: bytes = None):
    """Send message to the API"""
    try:
        st.session_state.thinking = True
        
        # Prepare the request
        files = {}
        data = {}
        
        if audio_data:
            files['audio_file'] = ('audio.wav', audio_data, 'audio/wav')
        
        if message:
            data['message'] = message
        
        if st.session_state.conversation_history:
            data['conversation_history'] = json.dumps([
                {"role": msg["role"], "content": msg["content"]}
                for msg in st.session_state.conversation_history
            ])
        
        if st.session_state.system_prompt:
            data['system_prompt'] = st.session_state.system_prompt
        
        # Make API request
        response = requests.post(
            f"{API_BASE_URL}/api/assist",
            files=files if files else None,
            data=data,
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        
        # Extract response
        user_text = result.get('transcribed_text') or message
        bot_response = result['response']
        
        # Update conversation history
        st.session_state.conversation_history = result['conversation_history']
        
        # Add messages to display
        st.session_state.messages.append({
            "role": "user",
            "content": user_text,
            "timestamp": datetime.now().strftime("%I:%M %p"),
            "type": "audio" if audio_data else "text"
        })
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": bot_response,
            "timestamp": datetime.now().strftime("%I:%M %p")
        })
        
        st.session_state.thinking = False
        return True
        
    except requests.exceptions.RequestException as e:
        st.session_state.thinking = False
        st.error(f"❌ Error: {str(e)}")
        return False
    except Exception as e:
        st.session_state.thinking = False
        st.error(f"❌ Unexpected error: {str(e)}")
        return False


def display_message(message):
    """Display a single message"""
    role = message["role"]
    content = message["content"]
    timestamp = message.get("timestamp", "")
    msg_type = message.get("type", "text")
    
    if role == "user":
        icon = "🎤" if msg_type == "audio" else "👤"
        css_class = "user-message"
        label = "You"
    else:
        icon = "🤖"
        css_class = "bot-message"
        label = "AI Assistant"
    
    st.markdown(f"""
    <div class="chat-message {css_class}">
        <div class="message-header">
            <span class="message-icon">{icon}</span>
            <span>{label}</span>
        </div>
        <div class="message-content">{content}</div>
        <div class="message-time">{timestamp}</div>
    </div>
    """, unsafe_allow_html=True)


def display_thinking():
    """Display thinking animation"""
    st.markdown("""
    <div class="thinking-container">
        <span>🤖 AI is thinking</span>
        <div class="thinking-dots">
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def main():
    """Main application"""
    
    # Apply custom CSS
    apply_custom_css()
    
    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <h2>⚙️ Settings</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Theme toggle
        theme_icon = "🌙" if st.session_state.theme == "dark" else "☀️"
        theme_label = "Light Mode" if st.session_state.theme == "dark" else "Dark Mode"
        
        if st.button(f"{theme_icon} {theme_label}", use_container_width=True):
            toggle_theme()
            st.rerun()
        
        st.divider()
        
        # System prompt
        st.markdown("### 🎯 AI Context")
        st.session_state.system_prompt = st.text_area(
            "System Prompt (Optional)",
            value=st.session_state.system_prompt,
            placeholder="e.g., You are a helpful assistant who speaks concisely...",
            height=100,
            help="Set the AI's behavior and context"
        )
        
        st.divider()
        
        # Statistics
        st.markdown("### 📊 Statistics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{len(st.session_state.messages)}</div>
                <div class="stat-label">Messages</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            user_msgs = sum(1 for m in st.session_state.messages if m["role"] == "user")
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{user_msgs}</div>
                <div class="stat-label">Your Messages</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # Clear chat button
        if st.button("🗑️ Clear Chat", use_container_width=True, type="secondary"):
            clear_chat()
            st.rerun()
        
        st.divider()
        
        # API Status
        st.markdown("### 🔌 API Status")
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                st.success("✅ Connected")
            else:
                st.error("❌ Disconnected")
        except:
            st.error("❌ Server Offline")
        
        st.divider()
        
        # Info
        st.markdown("""
        ### ℹ️ About
        
        This is an AI-powered voice assistant with:
        - 🎤 Voice input support
        - 💬 Text chat
        - 🌍 Multi-language transcription
        - 🧠 Context-aware responses
        
        Built with Groq LLM & ElevenLabs
        """)
    
    # Main content
    # Header
    st.markdown("""
    <div class="app-header">
        <div class="app-title">🤖 AI Voice Assistant</div>
        <div class="app-subtitle">Chat with AI using text or voice • Powered by Groq & ElevenLabs</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        # Display messages
        if st.session_state.messages:
            for message in st.session_state.messages:
                display_message(message)
        else:
            st.markdown("""
            <div style="text-align: center; padding: 3rem; color: #888;">
                <h3>👋 Welcome!</h3>
                <p>Start a conversation by typing a message or recording audio below.</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Display thinking animation
        if st.session_state.thinking:
            display_thinking()
    
    # Input area
    st.markdown("---")
    
    # Tabs for different input methods
    input_tab1, input_tab2 = st.tabs(["💬 Text Input", "🎤 Voice Input"])
    
    with input_tab1:
        col1, col2 = st.columns([5, 1])
        
        with col1:
            text_input = st.text_input(
                "Type your message",
                placeholder="Ask me anything...",
                label_visibility="collapsed",
                key="text_input"
            )
        
        with col2:
            send_btn = st.button("Send 📤", use_container_width=True, type="primary")
        
        if send_btn and text_input:
            if send_message(text_input):
                st.rerun()
    
    with input_tab2:
        st.markdown("### 🎙️ Record Audio")
        
        col1, col2 = st.columns([3, 2])
        
        with col1:
            # Audio recorder
            audio_bytes = audio_recorder(
                text="Click to record",
                recording_color="#FF4B4B",
                neutral_color="#6B6B6B",
                icon_size="2x",
                pause_threshold=3.0
            )
        
        with col2:
            st.markdown("**OR**")
            uploaded_file = st.file_uploader(
                "Upload audio file",
                type=['wav', 'mp3', 'ogg', 'm4a'],
                label_visibility="collapsed"
            )
        
        # Process audio
        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
            if st.button("Send Recording 🎤", use_container_width=True, type="primary"):
                if send_message("", audio_bytes):
                    st.rerun()
        
        if uploaded_file:
            st.audio(uploaded_file, format="audio/wav")
            if st.button("Send File 📁", use_container_width=True, type="primary"):
                audio_data = uploaded_file.read()
                if send_message("", audio_data):
                    st.rerun()
    
    # Quick actions
    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")
    
    quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4)
    
    with quick_col1:
        if st.button("👋 Greet", use_container_width=True):
            if send_message("Hello! How are you?"):
                st.rerun()
    
    with quick_col2:
        if st.button("🌤️ Weather", use_container_width=True):
            if send_message("What's the weather like today?"):
                st.rerun()
    
    with quick_col3:
        if st.button("💡 Idea", use_container_width=True):
            if send_message("Give me a creative idea"):
                st.rerun()
    
    with quick_col4:
        if st.button("📚 Explain", use_container_width=True):
            if send_message("Explain quantum computing simply"):
                st.rerun()


if __name__ == "__main__":
    main()
