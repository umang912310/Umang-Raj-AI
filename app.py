import os
import base64
import urllib.parse
from typing import List, Dict, Optional

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
    image_data: Optional[str] = None  # Base64 इमेज सपोर्ट

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
            -webkit-tap-highlight-color: transparent;
        }

        body {
            background-color: #0f172a;
            color: #ffffff;
            display: flex;
            height: 100vh;
            overflow: hidden;
        }

        /* History Sidebar */
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

        /* Welcome Center */
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
        .msg img {
            max-width: 100%;
            max-height: 250px;
            border-radius: 8px;
            margin-top: 6px;
            display: block;
        }

        /* Image Preview Box before Sending */
        #preview-container {
            display: none;
            padding: 8px 16px;
            background-color: #1e293b;
            border-top: 1px solid #334155;
            align-items: center;
            gap: 10px;
            z-index: 5;
        }

        #preview-img {
            width: 48px;
            height: 48px;
            object-fit: cover;
            border-radius: 6px;
            border: 1px solid #38bdf8;
        }

        #cancel-img-btn {
            background: #ef4444;
            color: white;
            border: none;
            border-radius: 50%;
            width: 22px;
            height: 22px;
            cursor: pointer;
            font-size: 12px;
        }

        /* Footer */
        footer {
            padding: 10px 12px;
            background-color: #1e293b;
            display: flex;
            gap: 8px;
            align-items: center;
            border-top: 1px solid #334155;
            z-index: 5;
        }

        .icon-btn {
            background-color: #334155;
            border: none;
            width: 42px;
            height: 42px;
            border-radius: 8px;
            color: #ffffff;
            font-size: 20px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            touch-action: manipulation;
        }

        .icon-btn.active {
            background-color: #ef4444;
            animation: pulse 1s infinite;
        }

        input[type="text"] {
            flex: 1;
            padding: 11px 14px;
            border-radius: 8px;
            border: 1px solid #475569;
            outline: none;
            background-color: #0f172a;
            color: #ffffff;
            font-size: 15px;
        }

        input[type="text"]:focus {
            border-color: #38bdf8;
        }

        button#send {
            background-color: #38bdf8;
            border: none;
            padding: 0 16px;
            height: 42px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 14px;
            cursor: pointer;
            color: #0f172a;
            flex-shrink: 0;
        }

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
                <h1>Umang AI</h1>
            </div>
            <div class="header-right">
                <button id="voiceToggle" class="voice-toggle-btn" onclick="toggleVoiceReply()">🔊 Voice: ON</button>
                <button id="reset" onclick="resetChat()">Reset</button>
            </div>
        </header>

        <!-- Welcome Card -->
        <div id="welcome-section">
            <div class="logo-circle">⚡</div>
            <div class="welcome-title">Umang AI</div>
            <div class="welcome-desc">
                नमस्ते! मेरा नाम <strong>गौरव</strong> है। मैं <strong>उमंग राज</strong> (रामपुर चौरम, अरवल) का पर्सनल एआई असिस्टेंट हूँ। मुझसे बात करें, सवाल पूछें या फोटो अपलोड करें!
            </div>
        </div>

        <div id="chat-box"></div>

        <!-- Selected Image Preview -->
        <div id="preview-container">
            <img id="preview-img" src="" alt="preview">
            <span style="font-size: 12px; color: #94a3b8; flex: 1;">फोटो चुनी गई</span>
            <button id="cancel-img-btn" onclick="clearSelectedImage()">✕</button>
        </div>

        <footer>
            <!-- Hidden File Input -->
            <input type="file" id="fileInput" accept="image/*" style="display: none;" onchange="handleImageSelection(event)">
            
            <!-- + Photo Button -->
            <button class="icon-btn" onclick="document.getElementById('fileInput').click()" title="फोटो जोड़ें">➕</button>
            
            <!-- Mic Button with Tap and Long Press -->
            <button id="micBtn" class="icon-btn" title="बोलने के लिए दबाएँ">🎙️</button>
            
            <input type="text" id="userInput" placeholder="संदेश लिखें या फोटो जोड़ें..." onkeydown="if(event.key==='Enter') sendMsg()">
            <button id="send" onclick="sendMsg()">Send</button>
        </footer>
    </div>

    <script>
        let isVoiceReplyEnabled = true;
        let recognition = null;
        let isListening = false;
        let attachedImageBase64 = null;

        // 1. Image Upload Logic
        function handleImageSelection(event) {
            const file = event.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = function(e) {
                attachedImageBase64 = e.target.result;
                document.getElementById("preview-img").src = attachedImageBase64;
                document.getElementById("preview-container").style.display = "flex";
            };
            reader.readAsDataURL(file);
        }

        function clearSelectedImage() {
            attachedImageBase64 = null;
            document.getElementById("fileInput").value = "";
            document.getElementById("preview-container").style.display = "none";
        }

        // 2. High-Compatibility Speech Recognition
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRec) {
            recognition = new SpeechRec();
            recognition.continuous = false;
            recognition.interimResults = true;
            recognition.lang = 'hi-IN';

            recognition.onstart = function() {
                isListening = true;
                const mic = document.getElementById("micBtn");
                mic.classList.add("active");
                mic.innerText = "🛑";
                document.getElementById("userInput").placeholder = "सुन रहा हूँ, बोलिए...";
            };

            recognition.onresult = function(event) {
                let current = '';
                for (let i = 0; i < event.results.length; i++) {
                    current += event.results[i][0].transcript;
                }
                document.getElementById("userInput").value = current;
            };

            recognition.onerror = function(event) {
                console.error("Mic error:", event.error);
                stopListening();
            };

            recognition.onend = function() {
                stopListening();
                const text = document.getElementById("userInput").value.trim();
                if (text) sendMsg();
            };
        }

        const micBtn = document.getElementById("micBtn");
        
        // Click to Toggle Mic
        micBtn.addEventListener("click", function(e) {
            e.preventDefault();
            if (!recognition) {
                alert("माइक सपोर्ट नहीं मिला। कृपया Google Speech Services परमिशन चेक करें।");
                return;
            }
            if (isListening) {
                recognition.stop();
                stopListening();
            } else {
                startListeningSafe();
            }
        });

        function startListeningSafe() {
            try {
                if ('speechSynthesis' in window) window.speechSynthesis.cancel();
                recognition.start();
            } catch(err) {
                recognition.stop();
            }
        }

        function stopListening() {
            isListening = false;
            micBtn.classList.remove("active");
            micBtn.innerText = "🎙️";
            document.getElementById("userInput").placeholder = "संदेश लिखें या फोटो जोड़ें...";
        }

        // 3. Text to Speech
        function speakText(text) {
            if (!isVoiceReplyEnabled || !('speechSynthesis' in window)) return;
            const clean = text.replace(/[*#_`]/g, '').replace(/\[.*?\]\(.*?\)/g, '');
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(clean);
            utterance.lang = 'hi-IN';
            utterance.rate = 1.0;
            window.speechSynthesis.speak(utterance);
        }

        function toggleVoiceReply() {
            isVoiceReplyEnabled = !isVoiceReplyEnabled;
            const btn = document.getElementById("voiceToggle");
            btn.innerText = isVoiceReplyEnabled ? "🔊 Voice: ON" : "🔇 Voice: OFF";
            if (!isVoiceReplyEnabled) window.speechSynthesis.cancel();
        }

        // 4. Sidebar & History
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

        // 5. Send Message & Handle Image
        async function sendMsg() {
            const input = document.getElementById("userInput");
            const text = input.value.trim();
            const currentImg = attachedImageBase64;

            if (!text && !currentImg) return;

            document.getElementById("welcome-section").style.display = "none";
            
            // Show User Bubble
            let userHtml = "";
            if (currentImg) {
                userHtml += `<img src="${currentImg}"><br>`;
            }
            if (text) {
                userHtml += `<span>${text}</span>`;
            }
            addBubble(userHtml, "user", true);

            // Clear Inputs
            input.value = "";
            clearSelectedImage();

            try {
                const res = await fetch("/chat", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ 
                        message: text || "इस फोटो के बारे में बताओ", 
                        image_data: currentImg 
                    })
                });
                const data = await res.json();
                if (data.type === "image") {
                    addBubble('<img src="' + data.reply + '" alt="Generated">', "ai", true);
                    speakText("मैंने यह तस्वीर तैयार कर दी है।");
                } else {
                    addBubble(marked.parse(data.reply), "ai", true);
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
            isHtml ? div.innerHTML = content : div.innerText = content;
            box.appendChild(div);
            box.scrollTop = box.scrollHeight;
        }

        async function resetChat() {
            window.speechSynthesis.cancel();
            await fetch("/reset", { method: "POST" });
            document.getElementById("chat-box").innerHTML = "";
            document.getElementById("history-list").innerHTML = "";
            document.getElementById("welcome-section").style.display = "flex";
            clearSelectedImage();
            addBubble("चैट साफ़ कर दी गई है।", "ai", false);
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
        img_payload = req.image_data

        if not raw_text and not img_payload:
            return {"reply": "संदेश खाली नहीं हो सकता।", "type": "text"}

        search_history.append(raw_text if raw_text else "Photo shared")

        # इमेज बनाने की रिक्वेस्ट पहचानना
        img_keywords = ["image", "photo", "draw", "generate", "तस्वीर", "फोटो बनाओ", "बनाओ"]
        if any(k in raw_text.lower() for k in img_keywords) and not img_payload:
            clean = raw_text
            for k in img_keywords:
                clean = clean.lower().replace(k, "").strip()
            encoded = urllib.pa
