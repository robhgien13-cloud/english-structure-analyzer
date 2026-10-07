from pathlib import Path
import stanza
model_dir = str(Path(__file__).parent / 'stanza_resources')
stanza.download('en', model_dir=model_dir, processors='tokenize,mwt,pos,lemma,depparse', verbose=True)
print('English Stanza models downloaded to', model_dir)
