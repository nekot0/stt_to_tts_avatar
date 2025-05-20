import os
import time
import queue
import threading
import sounddevice as sd
from flask import Flask, jsonify, Response
from flask_cors import CORS
from mem0 import Memory
from openai import AzureOpenAI
import azure.cognitiveservices.speech as speechsdk
import logging


# === Global Constants ===
class CFG:
    # Mem0
    memory_n_items = 3
    # LLM
    llm_temperature = 0.7
    llm_max_tokens = 200
    # TTS
    voice_character = "ja-JP-AoiNeural"

cfg = CFG()

# Azure Speech Services
AZURE_SPEECH_KEY="Azure Speech Service API KEY"
AZURE_REGION="Azure Speech Service Region"
# Azure OpenAI LLM
OPENAI_API_BASE="Azure OpenAI API Base"
OPENAI_API_VERSION="Azure OpenAI API Version"
OPENAI_DEPLOY_NAME ="Azure OpenAI Deployment Name"
OPENAI_API_KEY="Azure OpenAI API Key"
# OpenAI Embedding
OPENAI_EMBED_API_KEY="OpenAI API Key"
# Mem0 user management
DEFAULT_USER_ID="user1"


# === Global Instances ===
#load_dotenv()
memory = None
llm = None
speech_config = None
audio_config = None

event_queue = queue.Queue()
latest_reply = {"text": ""}
app = Flask(__name__)
CORS(app)
# Set LogLevel
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


# === Initialize ===
def initialize_models():
    """Initialize Memory, LLM (Azure OpenAI), and Azure TTS configuration."""
    global memory, llm, speech_config, audio_config

    # Configure Azure TTS
    speech_config = speechsdk.SpeechConfig(
        subscription=AZURE_SPEECH_KEY,
        region=AZURE_REGION
    )
    speech_config.speech_synthesis_voice_name = cfg.voice_character
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    print(f"Device {sd.default.device} listening")

    # Initialize Azure OpenAI LLM
    llm = AzureOpenAI(
        api_key=OPENAI_API_KEY,
        api_version=OPENAI_API_VERSION,
        azure_endpoint=OPENAI_API_BASE
    )

    # Initialize OpenAI Embedding
    os.environ["OPENAI_API_KEY"] = OPENAI_EMBED_API_KEY

    # Initialize memory
    memory = Memory()


# === Speech Recognition ===
def recognize_speech_from_mic() -> str:
    """Capture audio from mic and convert to text using Azure STT."""
    speech_recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config,
        language="ja-JP"
    )

    print(f"🎤 Please speak into mic...")
    result = speech_recognizer.recognize_once()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        #print(f"[Recognized] {result.text}")
        return result.text
    elif result.reason == speechsdk.ResultReason.NoMatch:
        #print("[STT] No speech could be recognized.")
        return ""
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation = result.cancellation_details
        print(f"[STT] Canceled: {cancellation.reason}")
        if cancellation.reason == speechsdk.CancellationReason.Error:
            print(f"[STT] Error details: {cancellation.error_details}")
    return ""


# === Generate text message ===
def generate_reply(user_input: str, user_id: str = DEFAULT_USER_ID) -> str:
    """Generate a full response using Azure OpenAI (no streaming)."""
    # Fetch memory context
    related_memories = memory.search(query=user_input, user_id=user_id, limit=cfg.memory_n_items)
    memories_text = "\n".join([f"- {m['memory']}" for m in related_memories["results"]])

    # Construct message payload
    system_prompt = (
        "システムプロンプトを入力する。"
        f"MEMORIES:\n{memories_text}"
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]

    response = llm.chat.completions.create(
        model=OPENAI_DEPLOY_NAME,
        messages=messages,
        temperature=cfg.llm_temperature,
        max_tokens=cfg.llm_max_tokens,
        stream=False
    )

    response_text = response.choices[0].message.content
    
    memory.add([
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": response_text}
    ], user_id=user_id)

    return response_text


# === Start chatting ===
@app.route("/api/speak", methods=["GET"])
def get_speak():
    text = latest_reply.get("text", "")
    latest_reply["text"] = ""
    return jsonify({"text": text})


@app.route("/api/stream")
def stream():
    def event_stream():
        while True:
            text = event_queue.get()
            yield f"data: {text}\n\n"
    return Response(event_stream(), content_type='text/event-stream')


def run_chat():
    """Voice-based interactive chat loop."""
    print("Say '終了' or '終わり' to quit.\n")
    while True:
        user_input = recognize_speech_from_mic().strip()
        if user_input in {"終了", "終わり", "おわり", "しゅうりょう"}:
            print("👋 Goodbye!")
            break
        if not user_input:
            continue
        
        print(f"User: {user_input}")
        reply = generate_reply(user_input)
        latest_reply["text"] = reply
        event_queue.put(reply)
        print(f"AI: {reply}")


if __name__ == "__main__":
    initialize_models()

    flask_thread = threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False),
        daemon=True
    )
    flask_thread.start()

    try:
        run_chat()
    except KeyboardInterrupt:
        print("Exit the programme.")
