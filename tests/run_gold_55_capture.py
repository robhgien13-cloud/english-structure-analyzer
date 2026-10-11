"""Capture actual parser output for 55 approved sentences. No accuracy claim."""
import json
from pathlib import Path
from analyzer import EnglishStructureAnalyzer
from gold55_school_grammar_adapter import adapt_main_clause
from score_gold55_accuracy import score
SENTENCES = [
  "She is happy.",
  "The tall boy runs fast.",
  "I read a book.",
  "She gave me a book.",
  "I found the book useful.",
  "The dog barked loudly.",
  "My father is a doctor.",
  "We watched the movie.",
  "They elected him president.",
  "The teacher showed us a picture.",
  "The man who smiled left.",
  "The boy who lives here runs fast.",
  "The book that I bought yesterday was expensive.",
  "The woman whom we met yesterday is a scientist.",
  "The house where I grew up has disappeared.",
  "When I arrived home, my mother was cooking dinner.",
  "Because it was raining, we stayed inside.",
  "If you study hard, you will improve.",
  "Although he was tired, he continued working.",
  "I will call you after I finish my homework.",
  "I think that she is right.",
  "What he said surprised everyone.",
  "I know where she lives.",
  "That he passed the exam is surprising.",
  "She asked whether I was ready.",
  "There are many books on the desk.",
  "There was a problem with the plan.",
  "It is important to learn English.",
  "It seems that he is honest.",
  "It was difficult for me to answer.",
  "She wants to become a doctor.",
  "To read books is enjoyable.",
  "He decided to leave early.",
  "I enjoy playing tennis.",
  "Swimming in the sea is fun.",
  "The girl sitting by the window is my sister.",
  "The letter written in English was difficult.",
  "She opened the door and entered the room.",
  "He is smart but sometimes careless.",
  "The book that my teacher recommended yesterday was surprisingly difficult to understand.",
  "The student who won the prize thanked the teacher who had helped her.",
  "The book I borrowed from the library contains stories that children can easily understand.",
  "What she discovered during the experiment surprised the researchers who were watching her.",
  "Although the road was slippery, the driver stopped the car before it reached the bridge.",
  "It was difficult for the children to understand what the scientist had explained.",
  "Walking through the park, she noticed a boy sitting alone under a tree.",
  "She opened the window, picked up her bag, and left the room without saying goodbye.",
  "The documents that had been sent yesterday were carefully examined by the manager.",
  "The teacher considered the explanation that the student had given surprisingly clear.",
  "When the boy who had lost his wallet realized that someone had found it, he decided to call the police.",
  "Not until the final results were announced did the researchers realize how serious the problem had become.",
  "Had the engineer checked the equipment more carefully before the experiment, the unexpected failure might have been prevented.",
  "It was the report submitted by the assistant last Friday that the committee discussed during the meeting in the main conference room.",
  "The professor with whom the students had discussed the theory in detail published an article about its limitations in an international journal.",
  "The more carefully the students examined the evidence, the less certain they became about the conclusion proposed by the researcher."
]
def main():
    parser = EnglishStructureAnalyzer()
    outputs, errors, predictions = {}, {}, {}
    for i, sentence in enumerate(SENTENCES, 1):
        cid = f"G{i:03d}"
        try:
            outputs[cid] = parser.analyze(sentence)
            roles = adapt_main_clause(outputs[cid])
            predictions[cid] = {role: [item.get('text', '') for item in roles[role]] for role in 'SVOCM'}
            print(cid, "OK", flush=True)
        except Exception as exc:
            errors[cid] = repr(exc)
            print(cid, "ERROR", repr(exc), flush=True)
    Path("artifacts").mkdir(exist_ok=True)
    accuracy = score(predictions) if not errors else {"not_scored": True, "errors": errors}
    print("GOLD55 ANNOTATED SCORE", accuracy.get("passed"), "/", accuracy.get("total"), flush=True)
    for failure in accuracy.get("failed", []):
        print("GOLD MISMATCH", failure["id"], failure["differences"], flush=True)
    Path("artifacts/g001-g055-actual.json").write_text(
        json.dumps({"outputs":outputs,"errors":errors,"total":len(SENTENCES),
                    "predictions":predictions,"gold_accuracy":accuracy},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL",len(SENTENCES),"SUCCESS",len(outputs),"ERRORS",len(errors),flush=True)
    if errors: raise SystemExit(1)
if __name__ == "__main__": main()
