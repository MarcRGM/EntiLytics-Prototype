from sentence_transformers import SentenceTransformer, util
import nltk
from nltk.tokenize import sent_tokenize # Split articles by sentence rather than using split('.')
import sys
sys.dont_write_bytecode = True

# Load a pre-trained BERT model (all-MiniLM-L6-v2 is fast and accurate)
model = SentenceTransformer('all-MiniLM-L6-v2')

# nltk requirement
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab', quiet=True)

def entity_ranking(article_description, entity_list, threshold=0.7):
    """
    Following research on semantic similarity thresholds (Martes et al., 2024),
    which found optimal cosine similarity thresholds for transformer models
    fall within the range 0.6-0.8, with peak performance around 0.7.

    Args:
        article_description: Full article text
        top_entities: Top-ranked entity names from ranking
        threshold: Cosine similarity threshold (default: 0.7)
                   Range: 0.6-0.8 per Jiang et al. (2024)
    
    Returns a list of dictionaries with name and score values                      
    """

    # Check if there are entities to rank
    if not entity_list:
        return []
    
    # Extract just the 'text' string from each Flair dictionary and remove repeated entities
    entity_names = []
    for entity in entity_list:
        # Extract the string from the Flair dict
        name = entity['text']
        if name not in entity_names:
            entity_names.append(name)

    # Encode the article and all entities into BERT vectors
    # BERT can only compare with vectors
    article_vector = model.encode(article_description, convert_to_tensor=True)
    entity_vectors = model.encode(entity_names, convert_to_tensor=True)

    # Compare each entity to the full article
    # Measures how relevant an entity is by giving it a score from 0.0 (Irrelevant) to 1.0 (relevant)
    cosine_scores = util.cos_sim(entity_vectors, article_vector)

    # Build the list of results
    final_rankings = []
    for index, entity_name in enumerate(entity_names):
        # The order in cosine_scores exactly matches the order in entity_names
        importance_score = cosine_scores[index].item() # get single number with .item

        if importance_score >= threshold:
            final_rankings.append({
                "name": entity_name,
                "score": importance_score
            })

    # Sort by highest score 
    final_rankings.sort(key=lambda x: x['score'], reverse=True)

    # Print results for checking
    # for entity in final_rankings:
        # print(f"Entity: {entity['name']} | Importance: {entity['score']:.4f}")

    return final_rankings

def generate_summary(article_description, top_entities, threshold=0.7):

    """
    Following research on semantic similarity thresholds (Martes et al., 2024),
    which found optimal cosine similarity thresholds for transformer models
    fall within the range 0.6-0.8, with peak performance around 0.7.

    Args:
        article_description: Full article text
        top_entities: Top-ranked entity names from ranking
        threshold: Cosine similarity threshold (default: 0.7)
                   Range: 0.6-0.8 per Jiang et al. (2024)
    
    Returns a list of dictionaries 
    """

    # Split into sentences
    sentences = sent_tokenize(article_description)

    # If already short, return as is
    if len(sentences) <= 3:
        return {
            'summary': article_description,
            'sentence_count': len(sentences),
            'scores': []
        }
    
    # Create a single string of the top entity names
    entity_focus_string = ", ".join([ent['name'] for ent in top_entities])

    # Encode the entity string into BERT vectors (Text to Numbers)
    entities_embedding = model.encode(entity_focus_string, convert_to_tensor=True)

    # Store results
    scored = []

    # Loop through each sentence with its position
    for i, sentence in enumerate(sentences):
        # Encode the sentence
        sentence_embedding = model.encode(sentence, convert_to_tensor=True)

        # Model calculate cosine similarity
        # Compares two vectors and returns a number from 0.0 to 1.0:
        similarity = util.cos_sim(sentence_embedding, entities_embedding).item() # get single number with .item

        scored.append({
            'text': sentence,          
            'index': i, # Keep the position in the article
            'score': similarity    
        })
    
    # Select sentences with similarity >= threshold
    selected = [s for s in scored if s['score'] >= threshold]
    
    # Fallback: If no sentences meet threshold, lower it slightly
    if not selected:
        threshold = 0.6
        selected = [s for s in scored if s['score'] >= threshold]
    
    # Fallback: If still empty, take best sentence
    if not selected:
        scored.sort(key=lambda x: x['score'], reverse=True)
        selected = [scored[0]]
        threshold = selected[0]['score']
    
    # Sort by original position 
    selected.sort(key=lambda x: x['index'])
    
    return {
        'summary': ' '.join([s['text'] for s in selected]),
        'sentence_count': len(selected),
        'threshold_used': threshold,
        'selected_scores': [round(s['score'], 3) for s in selected] # cosine similarity scores of each selected sentence
    }

