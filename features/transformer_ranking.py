from sentence_transformers import SentenceTransformer, util

import sys
sys.dont_write_bytecode = True

# Load a pre-trained BERT model (all-MiniLM-L6-v2 is fast and accurate)
model = SentenceTransformer('all-MiniLM-L6-v2')

def entity_ranking(article_description, entity_list):
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
        importance_score = cosine_scores[index].item()
        final_rankings.append({
            "name": entity_name,
            "score": importance_score
        })

    # Sort by highest score first and keep the top 5
    final_rankings.sort(key=lambda x: x['score'], reverse=True)

    # Print results for checking
    # for entity in final_rankings[:5]:
        # print(f"Entity: {entity['name']} | Importance: {entity['score']:.4f}")

    return final_rankings[:5]

    # return final_rankings[:5]

    