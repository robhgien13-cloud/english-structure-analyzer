# English Structure Analyzer v1

Stanza (Universal Dependencies) + an educational conversion layer for visualising English sentence structure.

## Run

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python setup_models.py
python app.py
```

Open http://127.0.0.1:5000

## What v1 does
- long-text input and Stanza sentence segmentation
- UD token/dependency data
- recursive clause nodes
- S / V / O / C / M candidates
- noun/adjective/PP/to-infinitive/gerund/participle phrase nodes
- modification, coordination, complement, reference and omitted-element relations (where detectable)
- grammar tags such as relative clauses, coordination, negation, comparison, existential there, inversion candidates
- stable IDs for future question generation
- three views: Skeleton / Structure / Original
- warnings rather than forced certainty for ambiguous conversions

The educational S/V/O/C conversion is deliberately rule-based and conservative. Stanza's UD parse is the source analysis; the school-grammar layer is an interpretation and should be validated before using nodes as diagnostic answer keys.

## v1.1 実験データ
- `test_sentences.json` に T01〜T30 の検証英文を収録。
- 画面上部の「実験データ」から1文を選択、または「30文すべて」で一括入力できます。
- T01〜T30は SV → SVO → SVC → SVOC → 修飾 → 節 → 関係詞 → 並列 → 特殊構文 → 多重入れ子の順で難しくなります。
- Android上でZIPを開くだけではStanzaは実行されません。実解析にはPythonサーバーとStanza英語モデルが必要です。


## Render deployment
1. Upload this folder to a GitHub repository.
2. In Render, create a Web Service from that repository.
3. `render.yaml` contains the build/start settings.
4. Select the Free plan for testing.
5. The first build downloads the Stanza English models, so it takes longer than later starts.

Build: `pip install -r requirements.txt && python setup_models.py`
Start: `gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120`
