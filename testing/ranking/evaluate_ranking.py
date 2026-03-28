"""
Entity Ranking Evaluation: Headline Entity Recovery F1

Evaluates EntiLytics entity ranker against headline entities.

Gold Standard: Named entities extracted from article headlines using Flair NER.
Research shows headline entities are primary article subjects (Singh et al. 2021;
Baraniak & Sydow 2021).

System: entity_ranking() ranks entities from the article body.
Evaluation checks if gold headline entities appear in top-ranked predictions.

Metric: Entity Recovery F1
  Precision = headline entities found in top-ranked / total top-ranked entities
  Recall = headline entities found in top-ranked / total headline entities
  F1 = harmonic mean
"""

import pandas as pd
import sys
from pathlib import Path

base_path = Path(__file__).parent
sys.path.append(str(base_path.parent.parent))

from features.flair_ner import identify_entities
from features.entity_ranking_and_summarization import entity_ranking

# Load dataset (from summarization evaluation)
csv_dataset_path = base_path / "summarization_dataset.csv"
if not csv_dataset_path.exists():
    print(f"ERROR: {csv_dataset_path} not found")
    sys.exit(1)

articles_df = pd.read_csv(csv_dataset_path)
print(f"Loaded {len(articles_df)} articles\n")


def is_acronym_of(short, long):
    """Check if short is an acronym of long"""
    if len(short) < 2:
        return False
    words = [w for w in long.split() if w]
    if len(words) < len(short):
        return False
    return short == "".join(w[0] for w in words)


def is_partial_acronym_of(short, long):
    """Check if short is an acronym ignoring function words"""
    if len(short) < 2:
        return False
    stop_words = {"for", "of", "the", "and", "in", "at", "by", "a", "an"}
    content_words = [w for w in long.split() if w not in stop_words]
    if len(content_words) < len(short):
        return False
    return short == "".join(w[0] for w in content_words)


def is_match(entity_a, entity_b):
    """Check if two entities are the same (handles exact, substring, and acronym variations)"""
    a = entity_a.strip().lower()
    b = entity_b.strip().lower()

    if not a or not b:
        return False

    # Exact match
    if a == b:
        return True

    # Short entities (< 3 chars) only match via acronym to avoid false positives
    if len(a) < 3 or len(b) < 3:
        return (is_acronym_of(a, b) or is_acronym_of(b, a) or
                is_partial_acronym_of(a, b) or is_partial_acronym_of(b, a))

    # Longer entities can match via substring
    if a in b or b in a:
        return True

    # Also check acronym variations for longer entities
    return (is_acronym_of(a, b) or is_acronym_of(b, a) or
            is_partial_acronym_of(a, b) or is_partial_acronym_of(b, a))


def is_valid_gold_entity(text):
    """Filter out NER mistakes - reject very long phrases and clauses that aren't true named entities"""
    words = text.split()
    if len(words) > 5:  # Too long to be a named entity
        return False
    clause_markers = {"to", "would", "did", "have", "said", "says", "want", "wants"}
    if any(w in clause_markers for w in words):  # Contains action verbs, likely not an NE
        return False
    return True


def extract_gold_entities_from_headline(headline_text):
    """Get the named entities from headline, filtered to remove false positives"""
    entities = identify_entities(headline_text)
    return set(
        e["text"].lower() for e in entities
        if is_valid_gold_entity(e["text"].lower())
    )


# Evaluation loop
ranking_precision_list = []
ranking_recall_list = []
ranking_f1_list = []
skipped_count = 0

print("ENTITY RANKING EVALUATION\n")

for _, article_row in articles_df.iterrows():
    # Get gold entities from headline
    gold_headline_entities = extract_gold_entities_from_headline(article_row["headline"])

    # Skip articles with no valid headline entities
    if not gold_headline_entities:
        skipped_count += 1
        continue

    # Rank entities from article body
    body_entities = identify_entities(article_row["full_text"])
    ranked_entities = entity_ranking(article_row["full_text"], body_entities)

    # Get top-K entities where K = number of gold entities (fair comparison)
    top_k = max(1, len(gold_headline_entities))
    system_top_entities = {e["name"].lower() for e in ranked_entities[:top_k]}

    # Check which system predictions match gold entities
    matched_entities = set(
        gold_e for gold_e in gold_headline_entities
        if any(is_match(gold_e, sys_e) for sys_e in system_top_entities)
    )

    # Calculate metrics
    tp = len(matched_entities)
    precision = tp / len(system_top_entities) if system_top_entities else 0
    recall = tp / len(gold_headline_entities) if gold_headline_entities else 0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0

    ranking_precision_list.append(precision)
    ranking_recall_list.append(recall)
    ranking_f1_list.append(f1)

    print(f"[{article_row['source']}] {article_row['headline'][:60]}...")
    print(f"Gold headline entities: {sorted(gold_headline_entities)}")
    print(f"Top-{top_k} ranked entities: {sorted(system_top_entities)}")
    print(f"Matched: {sorted(matched_entities)}")
    print(f"P={precision:.2f}  R={recall:.2f}  F1={f1:.2f}\n")


# Results
total_evaluated = len(ranking_f1_list)
if total_evaluated == 0:
    print("No articles evaluated.")
    sys.exit(0)

avg_precision = sum(ranking_precision_list) / total_evaluated
avg_recall = sum(ranking_recall_list) / total_evaluated
avg_f1 = sum(ranking_f1_list) / total_evaluated

print(f"\nRESULTS ({total_evaluated} articles evaluated, {skipped_count} skipped)\n")
print("ENTITY RANKING - Headline Entity Recovery F1")
print(f"Mean Precision: {avg_precision:.4f}")
print(f"Mean Recall: {avg_recall:.4f}")
print(f"Mean F1: {avg_f1:.4f}")
print(f"\n[Lower-bound baseline: Does not reward valid entities missing from headlines]")