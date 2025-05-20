# 🎤 Azure AI Avatar Interactive System

This repository demonstrates a real-time, voice-interactive system that integrates Azure OpenAI, Azure Speech Services, and the Azure TTS Avatar SDK.  
A user can speak into the microphone, receive a GPT-generated response, and watch an avatar read it aloud in a web browser.

---

## 📁 Project Structure
```bash
stt_to_tts_avatar/
├── interact_llm.py # Python backend (speech input + GPT response generation)
├── index.html # Frontend (browser-based avatar rendering and speech playback)
└── README.md # This file
```


---

## 🧠 Key Technologies

| Feature                  | Technology                                      |
|--------------------------|--------------------------------------------------|
| Speech-to-Text (STT)     | Azure Speech SDK (Python)                        |
| Response generation      | Azure OpenAI GPT-4o                              |
| Memory/context handling  | `mem0` custom module                             |
| Text-to-Speech (TTS)     | Azure Speech SDK (JavaScript)                   |
| Avatar rendering         | Azure TTS Avatar SDK via WebRTC                 |
| Backend communication    | Flask + Server-Sent Events (SSE) for streaming  |



---

## 🚀 Getting Started

### 1. Set up Azure Resources

- **Azure OpenAI resource** (GPT-4o model recommended)
- **Azure Speech resource** with *Standard S0* tier
- Avatar SDK requires supported regions (e.g., `westus2`)

🔐 Set the API keys and region in `interact_llm.py`:

```python
AZURE_SPEECH_KEY = "your-speech-key"
AZURE_REGION = "your-region"
OPENAI_API_KEY = "your-openai-api-key"
```


### 🔐 Environment Variable Notice

This project uses **both Azure OpenAI and OpenAI (official) APIs**:

- `interact_llm.py` uses `AzureOpenAI` for GPT responses
- `mem0` uses `OpenAI` Embeddings (`text-embedding-ada-002`) for semantic memory search

⚠️ **Important:** Both libraries refer to the environment variable `OPENAI_API_KEY`.  
This can cause a conflict if you use a single `.env` file for both Azure and OpenAI services.

✅ Recommendations:

| Purpose              | Variable to Set           | Notes                                 |
|----------------------|---------------------------|----------------------------------------|
| Azure OpenAI (GPT)   | Use `AzureOpenAI(...)`    | Do NOT set `OPENAI_API_KEY` globally  |
| OpenAI Embedding     | Set `os.environ["OPENAI_API_KEY"]` before calling `Memory()` |

✅ In `interact_llm.py`, this is already handled:
```python
os.environ["OPENAI_API_KEY"] = OPENAI_EMBED_API_KEY  # for mem0
```


### 2. Launch the Backend

```bash
# Install required packages
pip install flask flask-cors openai sounddevice azure-cognitiveservices-speech

# Start the server
python interact_llm.py
```

interactllm.py
- Captures speech from microphone
- Transcribes it via Azure STT
- Generates a reply via GPT
- Stores the reply in /api/speak and also pushes it via /api/stream

### 3. Open the Frontend

- Open index.html in Chrome or Edge
- Avatar will load and speak replies automatically via streaming events

🔈 If you don’t hear audio, check your browser’s autoplay policy or verify the ICE token.


## 🎨 Customization
| Feature | How to Customize |
| ---------------- | --------------------------------------------------- |
| Avatar character | AvatarConfig("lisa", "casual-sitting")              |
| Voice profile    | speechSynthesisVoiceName, e.g., ja-JP-NanamiNeural     |
| Character personality | Edit system_prompt in interact_llm.py          |
| Speech speed     | Use speakSsmlAsync() with <prosody rate="+25%"> in SSML |


