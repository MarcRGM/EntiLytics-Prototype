from flair.data import Sentence
from flair.nn import Classifier
from nltk.stem import WordNetLemmatizer
import nltk
import sys
sys.dont_write_bytecode = True

# Download WordNet data if not already present on the current environment.
# This check runs once and is skipped on subsequent startups.
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet', quiet=True)

# Load the ner-fast model: a BiLSTM NER model with a Softmax output layer.
# This is the non-CRF alternative provided by Flair, suited for environments
# where raw BiLSTM feature output is preferred over global sequence smoothing.
tagger = Classifier.load('ner-fast')

# Initialize the WordNet Lemmatizer for morphological normalization.
lemmatizer = WordNetLemmatizer()


def normalize_entity(text: str) -> str:
    """
    Converts an extracted entity string to a standardized base form.

    Lowercases each token, applies WordNet lemmatization to reduce
    inflected forms (e.g. plurals) to their base form, then applies
    title casing for consistent display.

    Args:
        text: The raw entity string as extracted by the NER model.

    Returns:
        A title-cased string with each word reduced to its base form.
    """
    words = text.split()
    lemmatized = [lemmatizer.lemmatize(word.lower()) for word in words]
    return " ".join(lemmatized).title()


def identify_entities(text: str) -> list:
    """
    Extracts named entities from the given text using the Flair NER model.

    Applies morphological normalization and deduplication to the raw
    model output before returning results.

    Args:
        text: The full article text to analyze.

    Returns:
        A list of dicts with keys: 'text', 'label', 'confidence'.
        Returns an empty list if no entities are found.
    """
    sentence = Sentence(text)
    tagger.predict(sentence)

    results = []
    seen_normalized = []

    if not sentence.get_spans('ner'):
        print("No entities found.")
        return results

    for entity in sentence.get_spans('ner'):
        label = entity.get_label('ner')
        norm_name = normalize_entity(entity.text)

        # Skip if a normalized form of this entity was already added.
        # This prevents duplicate entries from morphological variants.
        if norm_name not in seen_normalized:
            results.append({
                "text": norm_name,
                "label": label.value,
                "confidence": round(label.score, 2)
            })
            seen_normalized.append(norm_name)

    return results