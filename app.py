from flask import Flask, request, render_template_string, session
import requests
import secrets
import re

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

GOOGLE_API_KEY = "AIzaSyAI3hc54P2uVDKeVzZrbyWXSiTlQ_0S8Hs"
SEARCH_ENGINE_ID = "57e27a61842084170"

def get_live_search_data_and_images(query):
    text_snippets = []
    image_urls = []
    
    # 1. Google Custom Search (Text)
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {'q': query, 'key': GOOGLE_API_KEY, 'cx': SEARCH_ENGINE_ID, 'num': 4}
        res = requests.get(url, params=params, timeout=5).json()
        for item in res.get('items', []):
            snippet = item.get('snippet', '')
            if snippet:
                text_snippets.append(snippet)
    except Exception:
        pass

    # Backup: DuckDuckGo Search (अगर Google खाली रहे)
    if not text_snippets:
        try:
            ddg_url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            html_res = requests.get(ddg_url, headers=headers, timeout=5).text
            matches = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', html_res, re.DOTALL)
            for m in matches[:4]:
                clean_txt = re.sub(r'<[^>]+>', '', m).strip()
                if clean_txt:
                    text_snippets.append(clean_txt)
        except Exception:
            pass

    # 2. Google Images
    try:
        img_url = "https://www.googleapis.com/customsearch/v1"
        img_params = {'q': query, 'key': GOOGLE_API_KEY, 'cx': SEARCH_ENGINE_ID, 'searchType': 'image', 'num': 6}
        img_res = requests.get(img_url, params=img_params, timeout=5).json()
        for item in img_res.get('items', []):
            link = item.get('link')
            if link and (link.startswith('http://') or link.startswith('https://')):
                image_urls.append(link)
    except Exception:
        pass

    return "\n".join(text_snippets), image_urls

HTML = '''
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Umang Raj AI</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f0f2f5; height: 100vh; display: flex; flex-direction: column; }
        .header { background: #fff; padding: 14px 20px; border-bottom: 1px solid #ddd; display: flex; justify-content: space-between; align-items: center; font-weight: bold; font-size: 18px; color: #1a73e8; }
        .chat-box { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 14px; }
        .welcome-box { margin: auto; text-align: center; max-width: 400px; padding: 20px; }
        .welcome-title { font-size: 26px; font-weight: bold; color: #1a73e8; margin-bottom: 10px; }
        .welcome-sub { font-size: 16px; color: #5f6368; line-height: 1.5; }
        .msg { max-width: 85%; padding: 12px 16px; border-radius: 16px; line-height: 1.5; font-size: 15px; word-wrap: break-word; white-space: pre-wrap; }
        .user-msg { background: #1a73e8; color: #fff; align-self: flex-end; border-bottom-right-radius: 2px; }
        .ai-msg { background: #fff; color: #202124; align-self: flex-start; border-bottom-left-radius: 2px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); width: 85%; }
        .gallery-title { font-size: 13px; font-weight: bold; color: #1a73e8; margin-top: 12px; margin-bottom: 6px; }
        .gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(110px, 1fr)); gap: 8px; margin-top: 5px; }
        .img-card { height: 100px; border-radius: 8px; overflow: hidden; background: #eee; border: 1px solid #e0e0e0; }
        .img-card img { width: 100%; height: 100%; object-fit: cover; display: block; }
        .footer { background: #fff; padding: 12px 16px; border-top: 1px solid #ddd; display: flex; gap: 10px; }
        .footer input { flex: 1; padding: 12px 18px; border: 1px solid #ccc; border-radius: 25px; outline: none; font-size: 15px; }
        .footer button { background: #1a73e8; color: #fff; border: none; border-radius: 25px; padding: 12px 22px; cursor: pointer; font-weight: bold; }
        .clear-btn { background: #f1f3f4; color: #5f6368; border: none; border-radius: 15px; padding: 6px 12px; font-size: 12px; cursor: pointer; text-decoration: none; font-weight: normal; }
    </style>
</head>
<body>
    <div class="header">
        <span>Umang Raj AI</span>
        <a href="/clear" class="clear-btn">Reset Chat</a>
    </div>

    <div class="chat-box" id="chatBox">
        {% if not messages %}
            <div class="welcome-box">
                <div class="welcome-title">नमस्ते, मैं गौरव हूँ! 👋</div>
                <div class="welcome-sub">मैं <strong>Umang Raj AI</strong> का साथी हूँ। मुझसे कोई भी सवाल पूछें या बातचीत शुरू करें...</div>
            </div>
        {% endif %}
        {% for m in messages %}
            {% if m.role == 'user' %}
                <div class="msg user-msg">{{ m.text }}</div>
            {% else %}
                <div class="msg ai-msg">
                    <div>{{ m.text }}</div>
                    {% if m.images and m.images|length > 0 %}
                        <div class="gallery-title">🖼️ तस्वीरें:</div>
                        <div class="gallery">
                            {% for img in m.images %}
                                <div class="img-card">
                                    <a href="{{ img }}" target="_blank">
                                        <img src="{{ img }}" loading="lazy" onerror="this.parentElement.parentElement.style.display='none'">
                                    </a>
                                </div>
                            {% endfor %}
                        </div>
                    {% endif %}
                </div>
            {% endif %}
        {% endfor %}
    </div>

    <form method="POST" action="/" class="footer">
        <input type="text" name="q" placeholder="यहाँ मैसेज लिखें..." autocomplete="off" autofocus required>
        <button type="submit">भेजें</button>
    </form>

    <script>
        const box = document.getElementById('chatBox');
        box.scrollTop = box.scrollHeight;
    </script>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def home():
    if 'messages' not in session:
        session['messages'] = []

    if request.method == 'POST':
        user_query = request.form.get('q', '').strip()
        if user_query:
            session['messages'].append({'role': 'user', 'text': user_query})
            live_data, images = get_live_search_data_and_images(user_query)
            
            history_text = "\n".join([f"{m['role']}: {m['text']}" for m in session['messages'][-4:]])
            
            prompt = (
                f"You are 'Umang Raj AI'.\n"
                f"Rules:\n"
                f"1. Only tell creator info if asked who made/developed you: 'मुझे उमंग राज (Umang Raj) ने बनाया है, जो रामपुर चौरम गांव, जिला अरवल, बिहार के रहने वाले हैं।'\n"
                f"2. Never say 'I don't have real-time or latest information' or 'visit other sites'. Use the provided web search data to give the factual answer.\n"
                f"3. Never refuse pictures; they load below automatically.\n\n"
                f"Web Search Results:\n{live_data}\n\n"
                f"Chat History:\n{history_text}\n\n"
                f"User Question: {user_query}\n"
                f"Give a clear, direct, and helpful answer in Hindi."
            )

            ai_reply = ""
            try:
                post_res = requests.post(
                    "https://text.pollinations.ai/",
                    json={"messages": [{"role": "user", "content": prompt}], "model": "openai"},
                    timeout=20
                )
                if post_res.status_code == 200 and post_res.text.strip():
                    ai_reply = post_res.text.strip()
            except Exception:
                pass

            if not ai_reply:
                try:
                    get_res = requests.get(f"https://text.pollinations.ai/{requests.utils.quote(prompt)}", timeout=15)
                    if get_res.status_code == 200:
                        ai_reply = get_res.text.strip()
                except Exception:
                    ai_reply = "माफ़ कीजिए, उत्तर प्राप्त नहीं हो सका। कृपया पुनः प्रयास करें।"

            session['messages'].append({'role': 'ai', 'text': ai_reply, 'images': images})
            session.modified = True

    return render_template_string(HTML, messages=session.get('messages', []))

@app.route('/clear')
def clear():
    session.pop('messages', None)
    return render_template_string('<script>window.location.href="/";</script>')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
            
