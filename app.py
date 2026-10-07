from flask import Flask, jsonify, render_template, request
import json
from pathlib import Path
from analyzer import EnglishStructureAnalyzer

app = Flask(__name__)
analyzer = EnglishStructureAnalyzer()

@app.get('/')
def index():
    tests = json.loads((Path(__file__).parent / 'test_sentences.json').read_text(encoding='utf-8'))
    return render_template('index.html', tests=tests)

@app.post('/api/analyze')
def analyze():
    payload = request.get_json(silent=True) or {}
    text = (payload.get('text') or '').strip()
    if not text:
        return jsonify({'error': '英文を入力してください。'}), 400
    if len(text) > 30000:
        return jsonify({'error': 'v1では一度に30,000文字までです。'}), 400
    try:
        return jsonify(analyzer.analyze(text))
    except Exception as e:
        return jsonify({'error': f'解析に失敗しました: {e}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
