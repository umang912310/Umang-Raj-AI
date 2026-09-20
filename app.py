import os
import sys
import subprocess
import urllib.parse
from typing import List, Dict

# Auto package installer
for pkg in ["fastapi", "uvicorn", "requests", "pydantic"]:
    try:
        __import__(pkg)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

import requests
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Umang AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

chat_memory: List[Dict[str, str]] = []
search_history: List[str] = []
MAX_MEMORY = 10

class ChatPayload(BaseModel):
    message: str

HTML_CONTENT = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Umang AI</title>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: sans-serif; }
        body { background: #0f172a; color: white; display: flex; height: 100vh; overflow: hidden; }
        
        /* Sidebar History */
        #sidebar {
            width: 260px;
            background: #1e293b;
            border-right: 1px solid #334155;
            display: flex;
            flex-direction: column;
            transition: transform 0.3s ease;
            position: absolute;
            height: 100%;
            z-index: 10;
            transform: translateX(-100%);
        }
        #sidebar.open { transform: translateX(0); }
        .sidebar-header {
            padding: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #334155;
        }
        .sidebar-header h2 { font-size: 16px; color: #38bdf8; }
        .close-btn { background: none; border: none; color: white; font-size: 18px; cursor: pointer; }
        #history-list { flex: 1; overflow-y: auto; padding: 10px; list-style: none; display: flex; flex-direction: column; gap: 8px; }
        .history-item {
            background: #334155;
            padding: 10px;
            border-radius: 6px;
            font-size: 13px;
            cursor: pointer;
            word-break: break-word;
        }
        .history-item:hover { background: #475569; }

        /* Main Container */
        #main-container { flex: 1; display: flex; flex-direction: column; height: 100vh; width: 100%; }
        header { padding: 15px; background: #1e293b; display: flex; justify-content: space-between; align-items: center; }
        .header-left { display: flex; align-items: center; gap: 10px; }
        .header-right { display: flex; align-items: center; gap: 8px; }
        .menu-btn { background: #334155; border: none; color: white; padding: 6px 10px; border-radius: 5px; cursor: pointer; }
        .voice-toggle-btn { background: #334155; border: none; color: white; padding: 6px 10px; border-radius: 5px; cursor: pointer; font-size: 13px; }
        h1 { font-size: 18px; color: #38bdf8; }
        button#reset { background: #ef4444; border: none; padding: 6px 12px; color: white; border-radius: 5px; cursor: pointer; }
        
        #chat-box { flex: 1; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; gap: 12px; }
        .msg { max-width: 85%; padding: 12px 16px; border-radius: 12px; line-height: 1.5; word-break: break-word; font-size: 15px; }
        .user { align-self: flex-end; background: #2563eb; }
        .ai { align-self: flex-start; background: #334155; }
        
        .ai p { margin-bottom: 8px; }
        .ai p:last-child { margin-bottom: 0; }
        .ai ul, .ai ol { margin-left: 20px; margin-bottom: 8px; }
        .ai code { background: #1e293b; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 13px; }
        .ai pre { background: #1e293b; padding: 10px; border-radius: 6px; overflow-x: auto; margin: 8px 0; }
        .ai pre code { background: none; padding: 0; }
        .ai img { max-width: 100%; border-radius: 8px; margin-top: 5px; }

        footer { padding: 12px; background: #1e293b; display: flex; gap: 8px; align-items: center; }
        input { flex: 1; padding: 12px; border-radius: 8px; border: none; outline: none; background: #334155; color: white; font-size: 15px; }
        .mic-btn { background: #0284c7; border: none; width: 44px; height: 44px; border-radius: 8px; color: white; font-size: 18px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
        .mic-btn.listening { background: #ef4444; animation: pulse 1s infinite; }
        button#send { background: #38bdf8; border: none; padding: 0 16px; height: 44px; border-radius: 8px; font-weight: bold; cursor: pointer; color: #0f172a; }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.08); }
            100% { transform: scale(1); }
        }
    </style>
</head>
<body>

    <div id="sidebar">
        <div class="sidebar-header">
            <h2>History</h2>
            <button class="close-btn" onclick="toggleSidebar()">✕</button>
        </div>
        <ul id="history-list"></ul>
    </div>

    <div id="main-container">
        <header>
            <div class="header-left">
                <button class="menu-btn" onclick="toggleSidebar()">☰ History</button>
                <h1>Umang Raj AI</h1>
            </div>
            <div class="header-right">
                <button id="voiceToggle" class="voice-toggle-btn" onclick="toggleVoiceReply()">🔊 Voice: ON</button>
                <button id="reset" onclick="resetChat()">Reset</button>
            </div>
        </header>
        <div id="chat-box"></div>
        <footer>
            <button id="micBtn" class="mic-btn" onclick="toggleListening()" title="Speak">🎙️</button>
            <input type="text" id="userInput" placeholder="Type or click mic to speak..." onkeydown="if(event.key==='Enter') sendMsg()">
            <button id="send" onclick="sendMsg()">Send</button>
        </footer>
    </div>

    <script>
        let isVoiceReplyEnabled = true;
        let recognition = null;
        let isListening = false;

        // Speech-to-Text Setup
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'hi-IN';

            recognition.onstart = function() {
                isListening = true;
                document.getElementById("micBtn").classList.add("listening");
            };

            recognition.onresult = function(event) {
                const speechText = event.results[0][0].transcript;
                document.getElementById("userInput").value = speechText;
                sendMsg();
            };

            recognition.onerror = function(event) {
                stopListening();
            };

            recognition.onend = function() {
                stopListening();
            };
        }

        function toggleListening() {
            if (!recognition) {
                alert("Microphone not supported on this browser/app view.");
                return;
            }
            if (isListening) {
                recognition.stop();
                stopListening();
            } else {
                try {
                    recognition.start();
                } catch(e) {
                    recognition.stop();
                }
            }
        }

        function stopListening() {
            isListening = false;
            document.getElementById("micBtn").classList.remove("listening");
        }

        // Text-to-Speech Output
        function speakText(text) {
            if (!isVoiceReplyEnabled || !('speechSynthesis' in window)) return;
            const cleanText = text.replace(/[*#_`]/g, '').replace(/\[.*?\]\(.*?\)/g, '');
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(cleanText);
            utterance.lang = 'hi-IN';
            utterance.rate = 1.0;
            window.speechSynthesis.speak(utterance);
        }

        function toggleVoiceReply() {
            isVoiceReplyEnabled = !isVoiceReplyEnabled;
            const btn = document.getElementById("voiceToggle");
            if (isVoiceReplyEnabled) {
                btn.innerText = "🔊 Voice: ON";
            } else {
                window.speechSynthesis.cancel();
                btn.innerText = "🔇 Voice: OFF";
            }
        }

        function toggleSidebar() {
            document.getElementById("sidebar").classList.toggle("open");
            loadHistory();
        }

        async function loadHistory() {
            try {
                const res = await fetch("/history");
                const data = await res.json();
                const list = document.getElementById("history-list");
                list.innerHTML = "";
                if (data.history.length === 0) {
                    list.innerHTML = "<li style='color:#94a3b8; font-size:12px; padding:10px;'>No history found.</li>";
                    return;
                }
                data.history.forEach(item => {
                    const li = document.createElement("li");
                    li.className = "history-item";
                    li.innerText = item;
                    li.onclick = () => {
                        document.getElementById("userInput").value = item;
                        toggleSidebar();
                    };
                    list.appendChild(li);
                });
            } catch (err) {}
        }

        async function sendMsg() {
            const input = document.getElementById("userInput");
            const text = input.value.trim();
            if (!text) return;

            addBubble(text, "user", false);
            input.value = "";

            try {
                const res = await fetch("/chat", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ message: text })
                });
                const data = await res.json();
                if (data.type === "image") {
                    addBubble('<img src="' + data.reply + '" alt="Generated">', "ai", true);
                    speakText("मैंने आपके लिए यह तस्वीर बना दी है।");
                } else {
                    const formattedHtml = marked.parse(data.reply);
                    addBubble(formattedHtml, "ai", true);
                    speakText(data.reply);
                }
            } catch (err) {
                addBubble("Server error. Please try again.", "ai", false);
            }
        }

        function addBubble(content, role, isHtml = false) {
            const box = document.getElementById("chat-box");
            const div = document.createElement("div");
            div.className = "msg " + role;
            if (isHtml) {
                div.innerHTML = content;
            } else {
                div.innerText = content;
            }
            box.appendChild(div);
            box.scrollTop = box.scrollHeight;
        }

        async function resetChat() {
            window.speechSynthesis.cancel();
            await fetch("/reset", { method: "POST" });
            document.getElementById("chat-box").innerHTML = "";
            document.getElementById("history-list").innerHTML = "";
            addBubble("Chat history cleared.", "ai", false);
        }
    </script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_CONTENT

@app.get("/history")
def get_history():
    return {"history": list(reversed(search_history))}

@app.post("/chat")
def chat_handler(req: ChatPayload):
    global chat_memory, search_history
    raw_text = req.message.strip()
    if not raw_text:
        return {"reply": "Message cannot be empty.", "type": "text"}

    search_history.append(raw_text)

    img_keywords = ["image", "photo", "draw", "generate", "तस्वीर", "फोटो", "बनाओ"]
    if any(k in raw_text.lower() for k in img_keywords):
        clean = raw_text
        for k in img_keywords:
            clean = clean.lower().replace(k, "").strip()
        encoded = urllib.parse.quote(clean or raw_text)
        img_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true"
        chat_memory.append({"role": "user", "content": raw_text})
        chat_memory.append({"role": "ai", "content": img_url})
        return {"reply": img_url, "type": "image"}

    system_instruction = (
        "You are Umang Raj AI, a warm, intelligent, and natural conversational AI assistant for Umang Raj. "
        "Talk naturally in a polite, human-like tone using Hindi/Hinglish or English depending on user input. "
        "DO NOT write code or programming syntax unless the user explicitly asks for code. "
        "Provide helpful, direct, and conversational responses.\n\n"
    )

    history = system_instruction + "Conversation History:\n"
    for turn in chat_memory[-MAX_MEMORY:]:
        history += f"{turn['role'].upper()}: {turn['content']}\n"
    history += f"USER: {raw_text}\nAI:"

    url = f"https://text.pollinations.ai/{urllib.parse.quote(history)}?model=mistral"
    try:
        res = requests.get(url, timeout=30)
        bot_response = res.text.strip() if res.status_code == 200 else "Server busy. Please try again."
    except Exception as e:
        bot_response = f"Error: {str(e)}"

    chat_memory.append({"role": "user", "content": raw_text})
    chat_memory.append({"role": "ai", "content": bot_response})
    if len(chat_memory) > (MAX_MEMORY * 2):
        chat_memory = chat_memory[-(MAX_MEMORY * 2):]

    return {"reply": bot_response, "type": "text"}

@app.post("/reset")
def reset_handler():
    global chat_memory, search_history
    chat_memory.clear()
    search_history.clear()
    return {"status": "cleared"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
    
