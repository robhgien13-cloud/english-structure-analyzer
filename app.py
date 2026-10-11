from flask import Flask, jsonify, render_template, request
import json
from pathlib import Path
from analyzer import EnglishStructureAnalyzer
import sys
sys.path.insert(0, str(Path(__file__).parent / 'tests'))
from gold55_school_grammar_adapter import adapt_main_clause

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

@app.post('/api/diagnose/prepare')
def prepare_diagnosis():
    payload = request.get_json(silent=True) or {}
    text = (payload.get('text') or '').strip()
    if not text or len(text) > 3000:
        return jsonify({'error': '1文（3,000文字以内）を入力してください。'}), 400
    try:
        parsed = analyzer.analyze(text)
        if len(parsed.get('sentences', [])) != 1:
            return jsonify({'error': '診断対象は1文だけ選んでください。'}), 400
        sentence = parsed['sentences'][0]
        roles = adapt_main_clause(parsed)
        tokens = sentence.get('tokens', [])
        return jsonify({
            'tokens': [{'index': t['index'], 'text': t['text'], 'upos': t.get('upos')} for t in tokens],
            'roles': {role: [{'text': e.get('text', ''), 'token_ids': e.get('token_ids', [])} for e in roles[role]]
                      for role in 'SVOC'},
            'experimental': True,
            'warning': '試験版の自動判定です。曖昧な解析は正解として確定しないでください。'
        })
    except Exception:
        return jsonify({'error': 'この文はまだ安全に診断できません。別の文を選択してください。'}), 422

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
