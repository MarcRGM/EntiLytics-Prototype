import nltk
import sys
from flair.data import Sentence
from flair.nn import Classifier
from nltk.stem import WordNetLemmatizer
from nltk import pos_tag, word_tokenize
from nltk.corpus import wordnet

sys.dont_write_bytecode = True

# Download WordNet data if not already present on the current environment.
# This check runs once and is skipped on subsequent startups.
try:
    nltk.data.find('corpora/wordnet')
    nltk.data.find('taggers/averaged_perceptron_tagger_eng')
except LookupError:
    nltk.download('wordnet', quiet=True)
    nltk.download('averaged_perceptron_tagger_eng', quiet=True)

# Load the ner-fast model: a BiLSTM NER model with a Softmax output layer.
# This is the non-CRF alternative provided by Flair, suited for environments
# where raw BiLSTM feature output is preferred over global sequence smoothing.
tagger = Classifier.load('ner-fast')

# Initialize the WordNet Lemmatizer for morphological normalization.
lemmatizer = WordNetLemmatizer()

def get_wordnet_pos(nltk_pos_tag):
    """
    Convert NLTK POS tag to WordNet POS tag for accurate lemmatization.
    
    Maps NLTK tags to WordNet format:
    - NN/NNS/NNP/NNPS -> NOUN
    - VB/VBD/VBG/VBN/VBP/VBZ -> VERB
    - JJ/JJR/JJS -> ADJ
    - RB/RBR/RBS -> ADV
    """
    if nltk_pos_tag.startswith('NN'):
        return wordnet.NOUN
    elif nltk_pos_tag.startswith('VB'):
        return wordnet.VERB
    elif nltk_pos_tag.startswith('JJ'):
        return wordnet.ADJ
    elif nltk_pos_tag.startswith('RB'):
        return wordnet.ADV
    else:
        return wordnet.NOUN  # Default to noun


def normalize_entity(text: str) -> str:
    """
    Converts an extracted entity string to a standardized base form.

    Applies POS-aware lemmatization to reduce inflected forms to base form.
    Proper nouns (NNP/NNPS) are preserved as-is to keep entity names intact.

    Args:
        text: The raw entity string as extracted by the NER model.

    Returns:
        A string with each word reduced to its base form using POS tags.
    """
    tokens = word_tokenize(text)
    tagged_tokens = pos_tag(tokens)

    normalized_words = []
    for word, pos_tag_value in tagged_tokens:
        # Preserve proper nouns (entity names like Philippines, John, etc.)
        if pos_tag_value in ['NNP', 'NNPS']:
            normalized_words.append(word)
        else:
            # Use POS-aware lemmatization for accurate base form
            wordnet_pos = get_wordnet_pos(pos_tag_value)
            lemmatized_word = lemmatizer.lemmatize(word, pos=wordnet_pos)
            normalized_words.append(lemmatized_word)

    return " ".join(normalized_words)


def is_morphological_variant(candidate_entity_name, seen_entity_list):
    """
    Check if candidate entity is a morphological variant of a seen entity.
    (Words with the same structural base)
    
    Args:
        candidate_entity_name: New entity to check.
        seen_entity_list: List of already-accepted entities.
        
    Returns:
        True if candidate is a variant of a seen entity, False otherwise.
    """
    candidate_lower = candidate_entity_name.lower().strip()
    
    for seen_entity in seen_entity_list:
        seen_lower = seen_entity.lower().strip()
        
        # Skip if lengths differ too much
        length_difference = abs(len(candidate_lower) - len(seen_lower))
        if length_difference > 3:
            continue
        
        # Check substring containment
        if candidate_lower in seen_lower or seen_lower in candidate_lower:
            # Verify they share significant overlap (80%+ character match)
            longer = max(candidate_lower, seen_lower, key=len)
            shorter = min(candidate_lower, seen_lower, key=len)
            
            # Count how many characters from the shorter string appear in the longer.
            matching_chars = 0
            for char in shorter:
                if char in longer:
                    matching_chars += 1
            
            overlap_ratio = matching_chars / len(longer)
            if overlap_ratio >= 0.80:
                return True
    
    return False


def identify_entities(text: str) -> list:
    """
    Extracts named entities from the given text using the Flair NER model.

    Applies morphological normalization and deduplication to prevent 
    variant entities from being counted separately.

    Args:
        text: The full article text to analyze.

    Returns:
        A list of dicts with keys: 'text', 'label', 'confidence'.
        Deduplicated by morphological variant matching.
    """
    sentence = Sentence(text)
    tagger.predict(sentence)

    entity_results = []
    seen_entity_names = []

    if not sentence.get_spans('ner'):
        return entity_results

    for entity_span in sentence.get_spans('ner'):
        entity_label = entity_span.get_label('ner')
        normalized_entity_name = normalize_entity(entity_span.text)

        # Skip if this entity or a morphological variant was already added
        if not is_morphological_variant(normalized_entity_name, seen_entity_names):
            entity_results.append({
                "text": normalized_entity_name,
                "label": entity_label.value,
                "confidence": round(entity_label.score, 2)
            })
            seen_entity_names.append(normalized_entity_name)

    return entity_results