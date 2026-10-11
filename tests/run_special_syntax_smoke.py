"""Capture real parser output for approved G051-G055 without fabricating pass rates."""
import json
from pathlib import Path
from analyzer import EnglishStructureAnalyzer

CASES = {
  "G051": "Not until the final results were announced did the researchers realize how serious the problem had become.",
  "G052": "Had the engineer checked the equipment more carefully before the experiment, the unexpected failure might have been prevented.",
  "G053": "It was the report submitted by the assistant last Friday that the committee discussed during the meeting in the main conference room.",
  "G054": "The professor with whom the students had discussed the theory in detail published an article about its limitations in an international journal.",
  "G055": "The more carefully the students examined the evidence, the less certain they became about the conclusion proposed by the researcher."
}
def main():
    parser = EnglishStructureAnalyzer()
    outputs = {}
    errors = {}
    for cid, sentence in CASES.items():
        try:
            result = parser.analyze(sentence)
            outputs[cid] = result
            print(cid, 'sentences:', len(result.get('sentences', [])),
                  'clauses:', sum(len(s.get('clauses', [])) for s in result.get('sentences', [])))
        except Exception as exc:
            errors[cid] = repr(exc)
            print(cid, 'ERROR:', repr(exc))
    Path('artifacts').mkdir(exist_ok=True)
    Path('artifacts/g051-g055-actual.json').write_text(
        json.dumps({'outputs': outputs, 'errors': errors}, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    if errors:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
