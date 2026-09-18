from flask import Flask, request, render_template_string, session
import requests
import secrets
import json

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

def get_live_data_and_images(query):
    text_info = []
    image_urls = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    # 1. DuckDuckGo Instant API (करंट न्यूज़ और पदों के लिए)
    try:
        ddg_url = f"https://api.duckduckgo.com/?q={requests.utils.quote(query)}&format=json&no_html=1&skip_disambig=1"
        res = requests.get(ddg_url, headers=headers, timeout=5).json()
        if res.get('AbstractText'):
            text_info.append(res.get('AbstractText'))
        for topic in res.get('RelatedTopics', [])[:2]:
            if isinstance(topic, dict) and topic.get('Text'):
                text_info.append(topic.get('Text'))
        if res.get('Image'):
            img = res.get('Image')
            if img.startswith('/'):
                img = "https://duckduckgo.com" + img
            image_urls.append(img)
    except Exception:
        pass

    # 2. Wikipedia Live Search (अगर DDG खाली रहे)
    try:
        wiki_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={requests.utils.quote(query)}&utf8=&format=json"
        sr = requests.get(wiki_url, headers=headers, timeout=5).json()
        items = sr.get('query', {}).get('search', [])
        for item in items[:2]:
            clean_snippet = item.get('snippet', '').replace('<span class="searchmatch">', '').replace('</span>', '')
            text_info.append(f"{item.get('title')}: {clean_snippet}")
        
        if items and not image_urls:
            top_title = items[0].get('title')
            sum_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(top_title)}"
            sum_res = requests.get(sum_url, headers=headers, timeout=5).json()
            if 'thumbnail' in sum_res:
                image_urls.append(sum_res['thumbnail']['source'])
    except Exception:
        pass

    return "\n".join(text_info), image_urls

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
        .gallery { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 6px; }
        .img-card { height: 130px; width: 130px; border-radius: 10px; overflow: hidden; background: #eee; border: 1px solid #ddd; }
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
            live_data, images = get_live_data_and_images(user_query)
            
            prompt = (
                f"You are Umang Raj AI.\n"
                f"STRICT INSTRUCTIONS:\n"
                f"1. Only introduce creator if user asks 'who created/made/developed you': 'मुझे उमंग राज (Umang Raj) ने बनाया है, जो रामपुर चौरम गांव, जिला अरवल, बिहार के रहने वाले हैं।'\n"
                f"2. You MUST use this real-time web context to answer factual/current questions. Do NOT use outdated training data:\n"
                f"--- LIVE WEB DATA ---\n{live_data}\n---------------------\n"
                f"Question: {user_query}\n"
                f"Give direct, factual, correct Hindi response:"
            )

            ai_reply = ""
            try:
                post_res = requests.post(
                    "https://text.pollinations.ai/",
                    json={"messages": [{"role": "user", "content": prompt}], "model": "mistral"},
                    timeout=20
                )
                if post_res.status_code == 200 and post_res.text.strip():
                    ai_reply = post_res.text.strip()
            except Exception:
                pass

            if not ai_reply and live_data:
                ai_reply = f"ताज़ा जानकारी के अनुसार:\n{live_data}"
            elif not ai_reply:
                ai_reply = "माफ़ कीजिए, उत्तर प्राप्त नहीं हो सका।"

            session['messages'].append({'role': 'ai', 'text': ai_reply, 'images': images})
            session.modified = True

    return render_template_string(HTML, messages=session.get('messages', []))

@app.route('/clear')
def clear():
    session.pop('messages', None)
    return render_template_string('<script>window.location.href="/";</script>')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
