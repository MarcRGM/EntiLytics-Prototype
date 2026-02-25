"""
Entity Analysis Module: Transformer-based Entity Ranking and Summarization

This module implements distance-based threshold filtering for both entity
importance ranking and extractive summarization, following the findings
from recent research on transformer semantic similarity.

References:
    "Transformer Models for Paraphrase Detection: A Comprehensive Semantic 
    Similarity Study" (2025). Evaluation on Microsoft Research Paraphrase 
    Corpus (MRPC) dataset.
    
    Key Finding: BERT-based models achieve superior performance using distance 
    metrics (Manhattan, Euclidean) compared to cosine similarity, with optimal 
    thresholds in the range of 0.45-0.60 for semantic matching tasks.
"""

from sentence_transformers import SentenceTransformer, util
import nltk
from nltk.tokenize import sent_tokenize # Split articles by sentence rather than using split('.')
import sys
sys.dont_write_bytecode = True
import numpy as np
# Used for calculating the manhattan distance from BERT vectors
import torch 
import torch.nn.functional as vector_math 

# Load a pre-trained BERT model (all-MiniLM-L6-v2 is fast and accurate)
model = SentenceTransformer('all-MiniLM-L6-v2')

# nltk requirement
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab', quiet=True)

DISTANCE_THRESHOLD = 0.50
"""
Rationale:
    Based on "Transformer Models for Paraphrase Detection" (2025), which 
    identified optimal thresholds of 0.45-0.60 for distance-based semantic 
    matching with BERT models on the MRPC dataset. The value 0.50 represents 
    the mid-point
Reference:
    Paper Section: "Results + Discussion" 
    Specific finding: "Mid-range thresholds (around 0.4-0.6) show better balance"
    Peak performance values: Euclidean ~0.458-0.568, Manhattan ~0.455-0.596
"""

def entity_ranking(article_description, entity_list):
    """
    Rank entities using Manhattan distance with threshold filtering.

    Args:
        article_description: Full article text
        top_entities: Top-ranked entity names from ranking
        threshold: Max distance (default 0.50, range 0.45-0.60)
    
    Returns a list of dictionaries with name and score values (entities meeting distance threshold)              
    """

    # Check if there are entities to rank
    if not entity_list:
        return []
    
    # Extract just the 'text' string from each Flair dictionary and remove repeated entities
    entity_names = []
    for entity in entity_list:
        # Extract the string from the Flair dict and strip trailing/leading punctuation and whitespace
        name = entity['text'].strip(".,!?'\" ")

        if name not in entity_names:
            entity_names.append(name)

    # Encode the article and all entities into BERT vectors
    # BERT can only compare with vectors
    article_vector = model.encode(article_description, convert_to_tensor=True)
    entity_vectors = model.encode(entity_names, convert_to_tensor=True)

    # Scales BERT vectors to unit length 
    # This ensures distances remain consistent across different article lengths
    article_vector = vector_math.normalize(article_vector.unsqueeze(0), p=2, dim=1)
    entity_vectors = vector_math.normalize(entity_vectors, p=2, dim=1)

    # Score using Manhattan distance
    final_rankings = []
    for index, entity_name in enumerate(entity_names):
        # Calculate the Manhattan Distance between BERT vectors
        raw_dist = torch.dist(entity_vectors[index], article_vector, p=1).item()

        # This is the standard Geometric Scaling for Manhattan distance in BERT research
        # Max Manhattan distance between L2-normalized vectors is 2 * sqrt(d)
        # 384 is the dimension of the all-MiniLM-L6-v2 model
        scaling_factor = 2 * np.sqrt(384) # This is ~19.6
        # Scaling: Divide to get a 0.0-1.0 Distance Score
        normalized_dist = raw_dist / scaling_factor

        final_rankings.append({
            "name": entity_name,
            "distance": round(normalized_dist, 4) # lower is better
        })

    # Sort entities by distance in ascending order (closest first)
    final_rankings.sort(key=lambda x: x['distance'])

    # Apply threshold filter: keep only entities within distance threshold
    filtered_rankings = [ent for ent in final_rankings if ent['distance'] <= DISTANCE_THRESHOLD]

    # Make sure at least one entity is returned if any exist
    if not filtered_rankings and final_rankings:
        filtered_rankings = [final_rankings[0]]

    return filtered_rankings

def generate_summary(article_description, top_entities):

    """
    Generate summary using Manhattan distance with threshold filtering.

    Args:
        article_description: Full article text
        top_entities: Top-ranked entity names from ranking
    
    Returns the summary and sentence count
    """

    # Split into sentences
    sentences = sent_tokenize(article_description)

    # If already short, return as is
    if len(sentences) <= 3:
        return {
            'summary': article_description,
            'sentence_count': len(sentences),
        }
    
    # Create a single string of the top entity names
    entity_focus_string = ", ".join([ent['name'] for ent in top_entities])

    # Encode the entity string into BERT vectors (Text to Numbers)
    entities_embedding = model.encode(entity_focus_string, convert_to_tensor=True)
    entities_embedding = vector_math.normalize(entities_embedding.unsqueeze(0), p=2, dim=1)

    # Store results
    scored = []

    # Loop through each sentence with its position
    for i, sentence in enumerate(sentences):
        # Encode the sentence
        sentence_embedding = model.encode(sentence, convert_to_tensor=True)
        sentence_embedding = vector_math.normalize(sentence_embedding.unsqueeze(0), p=2, dim=1)

        # Calculate the Manhattan Distance between BERT vectors
        raw_dist = torch.dist(sentence_embedding, entities_embedding, p=1).item()

        # This is the standard Geometric Scaling for Manhattan distance in BERT research
        # Max Manhattan distance between L2-normalized vectors is 2 * sqrt(d)
        # 384 is the dimension of the all-MiniLM-L6-v2 model
        scaling_factor = 2 * np.sqrt(384) # This is ~19.6
        # Scaling: Divide to get a 0.0-1.0 Distance Score
        normalized_dist = raw_dist / scaling_factor

        scored.append({
            'text': sentence,          
            'index': i, # Keep the position in the article
            'distance': normalized_dist    
        })

    print("SENTENCES:")
    for sen in scored:
        print(sen['text'])
    
    # Apply threshold filter: keep only sentence within distance threshold
    filtered_sentences = [s for s in scored if s['distance'] <= DISTANCE_THRESHOLD]

    # Make sure at least one entity is returned if any exist
    if not filtered_sentences and scored:
        filtered_sentences = [scored[0]]

    # Sort by original position 
    filtered_sentences.sort(key=lambda x: x['index'])

    print("")
    print("")

    print("FILTERED SENTENCE:")
    for sen in filtered_sentences:
        print(sen['text'])

    return {
        'summary': ' '.join([s['text'] for s in filtered_sentences]),
        'sentence_count': len(filtered_sentences),
    }

# Testing
if __name__ == "__main__":
    article_text = """TOKYO, Japan — In a historic move that could reshape the global semiconductor industry, the Japanese government announced a $15 billion subsidy package on Thursday to support the construction of a massive new chip manufacturing plant in Hokkaido. The facility will be jointly operated by Taiwan Semiconductor Manufacturing Company (TSMC) and local tech conglomerate Sony Group. Prime Minister Fumio Kishida hailed the agreement as a critical step toward securing Japan's technological independence. During a press conference in Tokyo, Kishida emphasized that global supply chain disruptions over the past three years made this domestic initiative an absolute necessity. The new plant, expected to begin full operations by 2028, will focus on producing advanced 12-nanometer logic chips used in electric vehicles and artificial intelligence servers. TSMC Chairman Mark Liu expressed his deep gratitude for the swift approval process and highlighted the strong engineering talent pool available in the northern island of Hokkaido. However, the ambitious project has not been without its critics. Environmental groups, including the Tokyo-based Green Earth Alliance, have raised concerns about the enormous water and electricity requirements of the proposed facility. In response, Sony Group CEO Kenichiro Yoshida assured the public that the plant would run entirely on renewable energy sources, primarily sourced from nearby offshore wind farms. The economic impact of this joint venture is expected to be staggering. Local officials project the creation of over 8,000 direct high-tech jobs, with tens of thousands of additional positions generated in supporting industries across the region. Financial markets reacted positively to the news, with shares of both TSMC and Sony surging on the Nikkei index shortly after the announcement. Meanwhile, geopolitical analysts view the collaboration as a strategic counterweight to China's growing dominance in the microchip sector. United States Secretary of Commerce Gina Raimondo issued a statement from Washington praising the alliance, noting that it aligns perfectly with America's own CHIPS Act goals. As construction crews prepare to break ground next month, the world will be watching closely to see if this multi-billion dollar gamble pays off."""

    mock_top_entities = [
        {'name': 'Taiwan Semiconductor Manufacturing Company', 'distance': 0.3120},
        {'name': 'TSMC', 'distance': 0.3205},
        {'name': 'Sony Group', 'distance': 0.3411},
        {'name': 'Japan', 'distance': 0.3650},
        {'name': 'Hokkaido', 'distance': 0.3892},
        {'name': 'Fumio Kishida', 'distance': 0.4105}
    ]

    generate_summary(article_text, mock_top_entities)