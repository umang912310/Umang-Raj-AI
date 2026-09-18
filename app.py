from flask import Flask, request, render_template_string
import requests

app = Flask(__name__)

# आपकी दोनों चाबियाँ (Keys)
GOOGLE_API_KEY = "यहाँ_अपनी_GOOGLE_API_KEY_डालें"
SEARCH_ENGINE_ID = "57e27a61842084170"

def get_live_search_data(query):
    """Google से ताज़ा लाइव डेटा लाने का फ़ंक्शन"""
    if not GOOGLE_API_KEY or "यहाँ_अपनी" in GOOGLE_API_KEY:
        return ""
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'q': query,
            'key': GOOGLE_API_KEY,
            'cx': SEARCH_ENGINE_ID,
            'num': 3
        }
        res = requests.get(url, params=params, timeout=5).json()
        snippets = [item.get('snippet', '') for item in res.get('items', [])]
        return "\n".join(snippets)
    except Exception:
        return ""

HTML = '''
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="google-site-verification" content="uDLAyBFcSPxhK968gYamXFGDCb24yBE5M7e5ABlCFyQ" />
    <title>Umang Raj AI - Live Smart Search Engine</title>
    <meta name="description" content="Umang Raj AI with live internet capabilities.">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 20px; background: #f8f9fa; color: #202124; text-align: center; }
        .box { max-width: 600px; margin: 40px auto 20px auto; }
        h1 { color: #1a73e8; font-size: 36px; margin-bottom: 5px; }
        .tagline { color: #5f6368; font-size: 15px; margin-bottom: 25px; }
        .form { display: flex; gap: 8px; justify-content: center; }
        input { flex: 1; padding: 14px 20px; border: 1px solid #dfe1e5; border-radius: 25px; outline: none; font-size: 16px; box-shadow: 0 1px 6px rgba(32,33,36,.1); }
        button { padding: 14px 24px; border: none; background: #1a73e8; color: #fff; border-radius: 25px; font-size: 16px; cursor: pointer; font-weight: bold; }
        .results { max-width: 650px; margin: 30px auto; text-align: left; }
        .ai-card { background: #fff; border: 1px solid #e0e0e0; border-radius: 12px; padding: 22px; box-shadow: 0 2px 10px rgba(0,0,0,0.06); line-height: 1.7; font-size: 16px; white-space: pre-wrap; }
        .label { font-size: 13px; font-weight: bold; color: #1a73e8; margin-bottom: 12px; border-bottom: 1px solid #eee; padding-bottom: 6px; }
    </style>
</head>
<body>
    <div class="box">
        <h1>Umang Raj AI</h1>
        <div class="tagline">Live Web AI Search Engine</div>
        <form method="GET" action="/" class="form">
            <input type="text" name="q" placeholder="ताज़ा खबर, क्रिकेट या कोई भी सवाल पूछें..." value="{{ query }}" required>
            <button type="submit">पूछें</button>
        </form>
    </div>
    {% if query %}
    <div class="results">
        <div class="ai-card">
            <div class="label">✨ उमंग राज AI का लाइव उत्तर:</div>
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
        # 1. पहले ताज़ा गूगल लाइव जानकारी प्राप्त करना
        live_data = get_live_search_data(query)
        
        # 2. AI को निर्देश देना कि वह ताज़ा इंटरनेट जानकारी पढ़कर उत्तर दे
        context = f"\nताज़ा इंटरनेट सर्च डेटा:\n{live_data}" if live_data else ""
        prompt = (
            f"आप 'Umang Raj AI' नाम के एक आधुनिक और सटीक AI सर्च इंजन हैं, जिसे Umang Raj ने बनाया है। "
            f"नीचे दिए गए ताज़ा इंटरनेट डेटा का उपयोग करके सवाल का बिल्कुल सही, पूर्ण और ताज़ा उत्तर हिंदी में दें। "
            f"खेल या हालिया खबरों में भ्रामक उत्तर न दें और सही स्थिति स्पष्ट करें।\n"
            f"{context}\n\n"
            f"यूज़र का सवाल: {query}"
        )
        
        try:
            url = f"https://text.pollinations.ai/{requests.utils.quote(prompt)}"
            res = requests.get(url, timeout=25)
            if res.status_code == 200:
                answer = res.text.strip()
            else:
                answer = "माफ़ कीजिए, उत्तर प्राप्त नहीं हो सका। कृपया पुनः प्रयास करें।"
        except Exception:
            answer = "नेटवर्क में समस्या के कारण उत्तर नहीं मिल पाया।"

    return render_template_string(HTML, query=query, answer=answer)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
    
