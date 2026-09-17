from flask import Flask, request, render_template_string
import requests

app = Flask(__name__)

HTML = '''
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Umang Raj AI - Smart Search Engine</title>
    <meta name="description" content="Umang Raj AI is an intelligent search and AI assistant created by Umang Raj.">
    <meta name="keywords" content="Umang Raj AI, Umang AI, Umang Search Engine, Umang Raj">
    <meta name="author" content="Umang Raj">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 20px; background: #fafafa; color: #202124; text-align: center; }
        .box { max-width: 600px; margin: 40px auto 20px auto; }
        h1 { color: #ea4335; font-size: 38px; margin-bottom: 5px; }
        .tagline { color: #5f6368; font-size: 15px; margin-bottom: 25px; }
        .form { display: flex; gap: 8px; justify-content: center; }
        input { flex: 1; padding: 14px 20px; border: 1px solid #dfe1e5; border-radius: 25px; outline: none; font-size: 16px; box-shadow: 0 1px 6px rgba(32,33,36,.1); }
        button { padding: 14px 24px; border: none; background: #1a73e8; color: #fff; border-radius: 25px; font-size: 16px; cursor: pointer; font-weight: bold; }
        .results { max-width: 600px; margin: 30px auto; text-align: left; }
        .ai-card { background: #fff; border: 1px solid #e0e0e0; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); line-height: 1.6; font-size: 16px; white-space: pre-wrap; }
        .label { font-size: 12px; font-weight: bold; color: #1a73e8; margin-bottom: 8px; text-transform: uppercase; }
    </style>
</head>
<body>
    <div class="box">
        <h1>Umang Raj AI</h1>
        <div class="tagline">The Next-Gen Smart AI Search Engine</div>
        <form method="GET" action="/" class="form">
            <input type="text" name="q" placeholder="मुझसे कुछ भी पूछें (Ask anything)..." value="{{ query }}" required>
            <button type="submit">पूछें</button>
        </form>
    </div>
    {% if query %}
    <div class="results">
        <div class="ai-card">
            <div class="label">उमंग राज AI का उत्तर:</div>
            {{ answer }}
        </div>
    </div>
    {% endif %}
</body>
</html>
'''

@app.route('/')
def home():
    query = request.args.get('q', '').strip()
    answer = ""
    if query:
        try:
            prompt = f"आप 'Umang Raj AI' नाम के एक बुद्धिमान AI सहायक हैं, जिसे Umang Raj ने बनाया है। कृपया इस सवाल का सीधा, सरल और सटीक जवाब हिंदी में दें: {query}"
            url = f"https://text.pollinations.ai/{requests.utils.quote(prompt)}"
            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                answer = res.text.strip()
            else:
                answer = "माफ़ कीजिए, उत्तर प्राप्त नहीं हो सका। पुनः प्रयास करें।"
        except Exception:
            answer = "नेटवर्क त्रुटि के कारण उत्तर नहीं मिल सका।"

    return render_template_string(HTML, query=query, answer=answer)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
  
