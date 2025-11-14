# 🎨 Streamlit Frontend - AI Voice Assistant

Beautiful, modern UI for the AI Voice Assistant with dark/light theme toggle, voice input, and chat history.

## ✨ Features

### Core Features
- 🎤 **Voice Input**: Record audio directly in browser or upload audio files
- 💬 **Text Chat**: Traditional text-based messaging
- 🌓 **Theme Toggle**: Switch between dark and light themes
- 🗑️ **Clear Chat**: Reset conversation anytime
- 📊 **Statistics**: Track message count and activity
- 🎯 **Custom Context**: Set AI behavior with system prompts
- ⚡ **Quick Actions**: Pre-defined message shortcuts
- 🔄 **Real-time Updates**: Live thinking animation during AI processing

### UI/UX Highlights
- Modern gradient design with smooth animations
- Responsive layout that works on all screen sizes
- Message timestamps for better context
- Visual indicators for audio vs text messages
- API health status monitoring
- Smooth fade-in animations for messages
- Custom scrollbar styling
- Professional typing indicators

## 🚀 Quick Start

### 1. Install Dependencies

```powershell
pip install streamlit audio-recorder-streamlit requests
```

Or install from requirements.txt:

```powershell
pip install -r requirements.txt
```

### 2. Start the Backend API

Make sure your FastAPI backend is running first:

```powershell
python main.py
```

The API should be available at `http://localhost:8000`

### 3. Launch Streamlit App

```powershell
streamlit run streamlit_app.py
```

The app will open automatically in your browser at `http://localhost:8501`

## 🎯 How to Use

### Text Chat
1. Go to the **💬 Text Input** tab
2. Type your message in the input box
3. Click **Send 📤** or press Enter

### Voice Chat
1. Go to the **🎤 Voice Input** tab
2. **Option A - Record**: Click "Click to record" and speak
3. **Option B - Upload**: Upload an audio file (WAV, MP3, OGG, M4A)
4. Click **Send Recording** or **Send File**

### Setting AI Context
1. Open the sidebar (⚙️ Settings)
2. Scroll to **🎯 AI Context**
3. Enter your custom system prompt
4. The AI will follow this context in responses

Example contexts:
- "You are a helpful assistant who speaks concisely"
- "You are a teacher explaining complex topics simply"
- "You translate all responses to English"

### Theme Toggle
- Click the theme button in sidebar (🌙/☀️)
- Instantly switches between dark and light mode

### Quick Actions
Use pre-defined shortcuts at the bottom:
- **👋 Greet**: Say hello
- **🌤️ Weather**: Ask about weather
- **💡 Idea**: Get creative suggestions
- **📚 Explain**: Request explanations

## 🎨 Customization

### Change Colors

Edit the `apply_custom_css()` function in `streamlit_app.py`:

```python
# Dark theme colors
accent_color = "#FF4B4B"  # Change to your brand color
user_msg_bg = "#1E3A5F"   # User message background
bot_msg_bg = "#2D2D2D"    # Bot message background
```

### Add More Quick Actions

Add to the quick actions section:

```python
with quick_col5:
    if st.button("🎵 Music", use_container_width=True):
        if send_message("Recommend some music"):
            st.rerun()
```

### Modify API Endpoint

Change the base URL in `streamlit_app.py`:

```python
API_BASE_URL = "http://your-api-url:8000"
```

## 📱 Mobile Support

The app is fully responsive and works on:
- Desktop browsers
- Tablets
- Mobile phones (note: audio recording may vary by browser)

## 🔧 Troubleshooting

### "Server Offline" in sidebar
- Make sure FastAPI backend is running on port 8000
- Check that `.env` has valid API keys
- Verify no firewall blocking localhost:8000

### Audio recording not working
- Grant microphone permissions in your browser
- Try using Chrome/Edge (best support)
- Alternative: Upload audio file instead

### Theme not applying
- Clear browser cache
- Refresh the page (Ctrl+R or Cmd+R)
- Check browser console for errors

### Messages not sending
- Check API status in sidebar
- Verify backend logs for errors
- Ensure proper API key configuration

## 🎯 Keyboard Shortcuts

- **Enter**: Send text message (in text input)
- **Ctrl + R**: Refresh page
- **Ctrl + K**: Focus text input (browser default)

## 📊 Performance Tips

1. **Clear old conversations**: Use "Clear Chat" to reset
2. **Limit system prompt length**: Keep it under 200 words
3. **Optimize audio files**: Use WAV or MP3 for best results
4. **Monitor API status**: Check sidebar for connection issues

## 🌟 Advanced Features

### Conversation Export (Coming Soon)
Save your chat history to file

### Multi-language Support (Coming Soon)
Automatic language detection and translation

### Voice Output (Coming Soon)
AI responses with text-to-speech

## 📝 Technical Details

### Session State Management
The app uses Streamlit session state to persist:
- Message history
- Conversation context
- Theme preference
- System prompt
- Thinking state

### API Integration
All requests go through the `/api/assist` endpoint which handles:
- Text messages
- Audio transcription
- Conversation history
- Custom system prompts

### Audio Handling
- Browser recording via `audio-recorder-streamlit`
- File upload support for multiple formats
- Automatic conversion to API-compatible format

## 🤝 Contributing

Feel free to customize the UI:
1. Modify CSS in `apply_custom_css()`
2. Add new tabs for different input methods
3. Enhance message display formatting
4. Add emoji or GIF support

## 📄 License

MIT License - feel free to use and modify!

---

**Enjoy chatting with your AI assistant! 🚀**
