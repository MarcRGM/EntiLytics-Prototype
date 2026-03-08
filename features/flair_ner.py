from flair.data import Sentence
from flair.nn import Classifier
import nltk
from nltk.stem import WordNetLemmatizer

import sys
sys.dont_write_bytecode = True

# Load the standard English NER model 
# 'ner-fast' for a smaller, faster BiLSTM model if preferred
tagger = Classifier.load('ner-fast')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet', quiet=True)

# Initialize Lemmatizer for singular/plural handling
lemmatizer = WordNetLemmatizer()

def normalize_entity(text):
    """
    Converts entities to a standard singular form to prevent 
    duplicates like 'Apple' and 'Apples'.
    """
    words = text.split()
    # Lemmatize each word in the entity and rejoin
    return " ".join([lemmatizer.lemmatize(word.lower()) for word in words]).title()

def identify_entities(input):
    # Create a Flair Sentence object
    sentence = Sentence(input)

    # Predict entities
    tagger.predict(sentence)

    results = []
    
    # Track normalized names to avoid duplicates in the final list
    seen_normalized = []

    # Extract results
    if not sentence.get_spans('ner'):
        print("No entities found.")
    else:
        for entity in sentence.get_spans('ner'):
            label = entity.get_label('ner')
            original_text = entity.text
            
            # Create normalized version for checking duplicates
            norm_name = normalize_entity(original_text)
            
            # Only add to results if entity is not seen (in any form) yet
            if norm_name not in seen_normalized:
                results.append({
                    "text": norm_name, # Use normalized text for the final output
                    "label": label.value,
                    "confidence": round(label.score, 2)
                })
                seen_normalized.append(norm_name)
                
    return results

if __name__ == "__main__":
    identify_entities()
