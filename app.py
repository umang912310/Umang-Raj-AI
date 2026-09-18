from flask import Flask, request, render_template_string, session
import requests
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

GOOGLE_API_KEY = "AIzaSyAI3hc54P2uVDKeVzZrbyWXSiTlQ_0S8Hs"
SEARCH_ENGINE_ID = "57e27a61842084170"

def get_live_search_data_and_images(query):
    text_snippets = []
    image_urls = []
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'q': query,
            'key': GOOGLE_API_KEY,
            'cx': SEARCH_ENGINE_ID,
            'num': 3
        }
        res = requests.get(url, params=params, timeout=5).json()
        text_snippets = [item.get('snippet', '') for item in res.get('items', [])]
    except Exception:
        pass

    try:
        img_url = "https://www.googleapis.com/customsearch/v1"
        img_params = {
            'q': query,
            'key': GOOGLE_API_KEY,
            'cx': SEARCH_ENGINE_ID,
            'searchType': 'image',
            'num': 3
        }
        img_res = requests.get(img_url, params=img_params, timeout=5).json()
        image_urls = [item.get('link', '') for item in img_res.get('items', []) if item.get('link')]
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
        .chat-box { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 14px; }
        .msg { max-width: 80%; padding: 12px 16px; border-radius: 16px; line-height: 1.5; font-size: 15px; word-wrap: break-word; white-space: pre-wrap; }
        .user-msg { background: #1a73e8; color: #fff; align-self: flex-end; border-bottom-right-radius: 2px; }
        .ai-msg { background: #fff; color: #202124; align-self: flex-start; border-bottom-left-radius: 2px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
        .gallery { display: flex; gap: 8px; margin-top: 10px; overflow-x: auto; }
        .gallery img { height: 90px; width: 120px; object-fit: cover; border-radius: 8px; }
        .footer { background: #fff; padding: 12px 20px; border-top: 1px solid #ddd; display: flex; gap: 10px; }
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
            <div style="text-align: center; color: #888; margin-top: 40px; font-size: 14px;">
                सर्च करने या बातचीत शुरू करने के लिए नीचे लिखें...
            </div>
        {% endif %}
        {% for m in messages %}
            {% if m.role == 'user' %}
                <div class="msg user-msg">{{ m.text }}</div>
            {% else %}
                <div class="msg ai-msg">
                    <div>{{ m.text }}</div>
                    {% if m.images %}
                        <div class="gallery">
                            {% for img in m.images %}
                                <a href="{{ img }}" target="_blank"><img src="{{ img }}" loading="lazy" onerror="this.style.display='none'"></a>
                            {% endfor %}
                        </div>
                    {% endif %}
                </div>
            {% endif %}
        {% endfor %}
    </div>

    <form method="POST" action="/" class="footer">
        <input type="text" name="q" placeholder="यहाँ लिखें..." autocomplete="off" autofocus required>
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
            context = f"\nWeb Search Data:\n{live_data}" if live_data else ""
            history_text = "\n".join([f"{m['role']}: {m['text']}" for m in session['messages'][-4:]])
            prompt = (
                f"You are 'Umang Raj AI' created by Umang Raj. "
                f"Conversation history:\n{history_text}\n"
                f"{context}\n\n"
                f"User Question: {user_query}\n"
                f"Respond accurately in Hindi using the live search data if available."
            )

            try:
                url = f"https://text.pollinations.ai/{requests.utils.quote(prompt)}"
                res = requests.get(url, timeout=25)
                ai_reply = res.text.strip() if res.status_code == 200 else "उत्तर प्राप्त नहीं हो सका।"
            except Exception:
                ai_reply = "नेटवर्क में समस्या के कारण उत्तर नहीं मिल सका।"

            session['messages'].append({'role': 'ai', 'text': ai_reply, 'images': images})
            session.modified = True

    return render_template_string(HTML, messages=session.get('messages', []))

@app.route('/clear')
def clear():
    session.pop('messages', None)
    return render_template_string('<script>window.location.href="/";</script>')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
