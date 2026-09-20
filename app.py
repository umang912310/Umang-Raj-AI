import os
import urllib.parse
from typing import List, Dict

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

HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Umang AI</title>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }

        body {
            background-color: #0f172a;
            color: #ffffff;
            display: flex;
            height: 100vh;
            overflow: hidden;
        }

        /* Sidebar Drawer */
        #sidebar {
            width: 280px;
            background-color: #1e293b;
            border-right: 1px solid #334155;
            display: flex;
            flex-direction: column;
            transition: transform 0.3s ease;
            position: absolute;
            top: 0;
            bottom: 0;
            left: 0;
            height: 100%;
            z-index: 20;
            transform: translateX(-100%);
        }

        #sidebar.open {
            transform: translateX(0);
        }

        .sidebar-header {
            padding: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #334155;
        }

        .sidebar-header h2 {
            font-size: 16px;
            font-weight: 600;
            color: #38bdf8;
        }

        .close-btn {
            background: none;
            border: none;
            color: #94a3b8;
            font-size: 20px;
            cursor: pointer;
        }

        .close-btn:hover {
            color: #ffffff;
        }

        #history-list {
            flex: 1;
            overflow-y: auto;
            padding: 12px;
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .history-item {
            background-color: #334155;
            padding: 10px 12px;
            border-radius: 6px;
            font-size: 13px;
            cursor: pointer;
            word-break: break-word;
            transition: background 0.2s ease;
        }

        .history-item:hover {
            background-color: #475569;
        }

        /* Main Container */
        #main-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            height: 100vh;
            width: 100%;
            position: relative;
        }

        header {
            padding: 12px 16px;
            background-color: #1e293b;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #334155;
            z-index: 5;
        }

        .header-left, .header-right {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .menu-btn, .voice-toggle-btn {
            background-color: #334155;
            border: none;
            color: #ffffff;
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
        }

        h1 {
            font-size: 18px;
            font-weight: bold;
            color: #38bdf8;
        }

        button#reset {
            background-color: #ef4444;
            border: none;
            padding: 6px 12px;
            color: #ffffff;
            border-radius: 6px;
            font-size: 13px;
            cursor: pointer;
        }

        /* Hero Welcome Screen */
        #welcome-section {
            position: absolute;
            top: 45%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 12px;
            padding: 20px;
            width: 90%;
            max-width: 450px;
            z-index: 2;
            pointer-events: none;
        }

        .logo-circle {
            width: 70px;
            height: 70px;
            background: linear-gradient(135deg, #0284c7, #38bdf8);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 32px;
            box-shadow: 0 0 20px rgba(56, 189, 248, 0.4);
        }

        .welcome-title {
            font-size: 26px;
            font-weight: bold;
            color: #38bdf8;
            letter-spacing: 1px;
        }

        .welcome-desc {
            font-size: 15px;
            color: #94a3b8;
            line-height: 1.6;
            background-color: rgba(30, 41, 59, 0.7);
            padding: 12px 18px;
            border-radius: 10px;
            border: 1px solid #334155;
        }

        /* Chat Output */
        #chat-box {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            z-index: 3;
        }

        .msg {
            max-width: 85%;
            padding: 12px 16px;
            border-radius: 12px;
            line-height: 1.5;
            word-break: break-word;
            font-size: 15px;
        }

        .user {
            align-self: flex-end;
            background-color: #2563eb;
            color: #ffffff;
            border-bottom-right-radius: 2px;
        }

        .ai {
            align-self: flex-start;
            background-color: #334155;
            color: #f1f5f9;
            border-bottom-left-radius: 2px;
        }

        .ai p { margin-bottom: 8px; }
        .ai p:last-child { margin-bottom: 0; }
        .ai img { max-width: 100%; border-radius: 8px; margin-top: 6px; }

        /* Input Footer */
        footer {
            padding: 12px 16px;
            background-color: #1e293b;
            display: flex;
            gap: 8px;
            align-items: center;
            border-top: 1px solid #334155;
            z-index: 5;
        }

        input {
            flex: 1;
            padding: 12px 14px;
            border-radius: 8px;
            border: 1px solid #475569;
            outline: none;
            background-color: #0f172a;
            color: #ffffff;
            font-size: 15px;
        }

        input:focus { border-color: #38bdf8; }

        .mic-btn {
            background-color: #0284c7;
            border: none;
            width: 44px;
            height: 44px;
            border-radius: 8px;
            color: #ffffff;
            font-size: 18px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .mic-btn.listening {
            background-color: #ef4444;
            animation: pulse 1s infinite;
        }

        button#send {
            background-color: #38bdf8;
            border: none;
            padding: 0 18px;
            height: 44px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 14px;
            cursor: pointer;
            color: #0f172a;
        }

        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.08); }
            100% { transform: scale(1); }
        }
    </style>
</head>
<body>

    <!-- Drawer Sidebar -->
    <div id="sidebar">
        <div class="sidebar-header">
            <h2>History</h2>
            <button class="close-btn" onclick="toggleSidebar()">✕</button>
        </div>
        <ul id="history-list"></ul>
    </div>

    <!-- Main App Container -->
    <div id="main-container">
        <header>
            <div class="header-left">
                <button class="menu-btn" onclick="toggleSidebar()">☰ History</button>
                <h1>Umang AI</h1>
            </div>
            <div class="header-right">
                <button id="voiceToggle" class="voice-toggle-btn" onclick="toggleVoiceReply()">🔊 Voice: ON</button>
                <button id="reset" onclick="resetChat()">Reset</button>
            </div>
        </header>

        <!-- Welcome Hero Section -->
        <div id="welcome-section">
            <div class="logo-circle">⚡</div>
            <div class="welcome-title">Umang AI</div>
            <div class="welcome-desc">
                नमस्ते! मेरा नाम <strong>गौरव</strong> है। मैं उमंग राज का पर्सनल एआई असिस्टेंट हूँ। मुझसे कोई भी सवाल पूछें या फोटो बनाने को कहें!
            </div>
        </div>

        <div id="chat-box"></div>

        <footer>
            <button id="micBtn" class="mic-btn" onclick="toggleListening()" title="बोलकर पूछें">🎙️</button>
            <input type="text" id="userInput" placeholder="संदेश लिखें या माइक दबाकर बोलें..." onkeydown="if(event.key==='Enter') sendMsg()">
            <button id="send" onclick="sendMsg()">Send</button>
        </footer>
    </div>

    <!-- संपूर्ण जावास्क्रिप्ट लॉजिक -->
    <script>
        let isVoiceReplyEnabled = true;
        let recognition = null;
        let isListening = false;
        let finalSpokenText = "";

        // 1. हाई-एक्यूरेसी स्पीच रिकग्निशन
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = true; // बोलते समय स्क्रीन पर लाइव दिखना
            recognition.lang = 'hi-IN';

            recognition.onstart = function() {
                isListening = true;
                finalSpokenText = "";
                const mic = document.getElementById("micBtn");
                mic.classList.add("listening");
                mic.innerText = "🛑";
                document.getElementById("userInput").placeholder = "सुन रहा हूँ, बोलिए...";
            };

            recognition.onresult = function(event) {
                let interim = '';
                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    if (event.results[i].isFinal) {
                        finalSpokenText += event.results[i][0].transcript;
                    } else {
                        interim += event.results[i][0].transcript;
                    }
                }
                const currentText = finalSpokenText || interim;
                document.getElementById("userInput").value = currentText;
            };

            recognition.onerror = function(event) {
                console.error("Speech Recognition Error:", event.error);
                stopListening();
            };

            recognition.onend = function() {
                stopListening();
                // बोलना बंद होते ही अगर कुछ बोला गया है तो खुद सेंड हो जाएगा
                const text = document.getElementById("userInput").value.trim();
                if (text) {
                    sendMsg();
                }
            };
        }

        function toggleListening() {
            if (!recognition) {
                alert("आपके डिवाइस के वेबव्यू में माइक सपोर्ट नहीं है। कृपया ऐप को माइक्रोफ़ोन अनुमति दें।");
                return;
            }
            if (isListening) {
                recognition.stop();
                stopListening();
            } else {
                try {
                    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
                    recognition.start();
                } catch(e) {
                    recognition.stop();
                }
            }
        }

        function stopListening() {
            isListening = false;
            const mic = document.getElementById("micBtn");
            if (mic) {
                mic.classList.remove("listening");
                mic.innerText = "🎙️";
            }
            document.getElementById("userInput").placeholder = "संदेश लिखें या माइक दबाकर बोलें...";
        }

        // 2. टेक्स्ट-टू-स्पीच आउटपुट
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

        // 3. साइडबार एवं चैट हिस्ट्री
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
                if (!data.history || data.history.length === 0) {
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

        function hideWelcomeSection() {
            const welcome = document.getElementById("welcome-section");
            if (welcome) welcome.style.display = "none";
        }

        // 4. मैसेज सेंड करना एवं चैट प्रोसेस
        async function sendMsg() {
            const input = document.getElementById("userInput");
            const text = input.value.trim();
            if (!text) return;

            hideWelcomeSection();
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
                    speakText("मैंने आपके लिए यह तस्वीर तैयार कर दी है।");
                } else {
                    const formattedHtml = marked.parse(data.reply);
                    addBubble(formattedHtml, "ai", true);
                    speakText(data.reply);
                }
            } catch (err) {
                addBubble("त्रुटि: सर्वर से कनेक्ट नहीं हो सका।", "ai", false);
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

        // 5. चैट रीसेट
        async function resetChat() {
            window.speechSynthesis.cancel();
            await fetch("/reset", { method: "POST" });
            document.getElementById("chat-box").innerHTML = "";
            document.getElementById("history-list").innerHTML = "";
            
            const welcome = document.getElementById("welcome-section");
            if (welcome) welcome.style.display = "flex";
            
            addBubble("चैट हिस्ट्री साफ़ कर दी गई है।", "ai", false);
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
    try:
        raw_text = req.message.strip()
        if not raw_text:
            return {"reply": "संदेश खाली नहीं हो सकता।", "type": "text"}

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
            "You are Gaurav, a smart, polite, and natural conversational AI assistant built for Umang Raj in Umang AI. "
            "Whenever asked who you are, introduce yourself as Gaurav, Umang Raj's personal AI. "
            "Talk naturally in Hindi/Hinglish or English depending on user input. "
            "DO NOT output code unless explicitly requested."
        )

        messages = [{"role": "system", "content": system_instruction}]
        for turn in chat_memory[-MAX_MEMORY:]:
            messages.append({"role": "user" if turn["role"] == "user" else "assistant", "content": turn["content"]})
        messages.append({"role": "user", "content": raw_text})

        headers = {"Content-Type": "application/json"}
        payload = {
            "messages": messages,
            "model": "openai",
            "seed": 42
        }

        try:
            res = requests.post("https://text.pollinations.ai/", json=payload, headers=headers, timeout=25)
            if res.status_code == 200 and res.text.strip():
                bot_response = res.text.strip()
            else:
                raise Exception("Primary failed")
        except Exception:
            prompt_encoded = urllib.parse.quote(f"{system_instruction}\nUser: {raw_text}\nGaurav:")
            fallback_res = requests.get(f"https://text.pollinations.ai/{prompt_encoded}?model=search", timeout=15)
            bot_response = fallback_res.text.strip() if fallback_res.status_code == 200 else "माफ़ कीजिए, सर्वर व्यस्त है। कृपया पुनः प्रयास करें।"

        chat_memory.append({"role": "user", "content": raw_text})
        chat_memory.append({"role": "ai", "content": bot_response})
        if len(chat_memory) > (MAX_MEMORY * 2):
            chat_memory = chat_memory[-(MAX_MEMORY * 2):]

        retu
