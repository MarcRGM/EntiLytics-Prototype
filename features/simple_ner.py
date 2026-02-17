from flair.data import Sentence
from flair.nn import Classifier

import sys
sys.dont_write_bytecode = True

# Load the standard English NER model 
# 'ner-fast' for a smaller, faster BiLSTM model if preferred
tagger = Classifier.load('ner')

def identify_entities(input):
    # Create a Flair Sentence object
    sentence = Sentence(input)

    # Predict entities
    tagger.predict(sentence)

    results =[]

    # Extract results
    if not sentence.get_spans('ner'):
        print("No entities found.")
    else:
        for entity in sentence.get_spans('ner'):
            label = entity.get_label('ner')
            results.append({
            "text": entity.text,
            "label": label.value,
            "confidence": f"{label.score:.2f}"
        })
    return results

if __name__ == "__main__":
    identify_entities()
