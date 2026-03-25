"""
Summarization Evaluation: Entity Coverage F1

Evaluates EntiLytics summarization against a gold standard derived from 
article headlines.

Gold Standard: Named entities extracted from headlines using Flair NER.
Research shows headline entities are primary content subjects, making them 
a valid automated proxy for central entity identification Singh et al. (2021) 
and Baraniak and Sydow (2021).

System: generate_summary() produces an extractive summary. Evaluation checks 
if gold headline entities appear in the generated summary.

Metric: Entity Coverage F1 referenced to Hofmann-Coyle et al.
(2022) who establish F1 as the appropriate metric for entity-centric extractive
summarization evaluated at the sentence level.
  Precision = gold entities found in summary / all ranked entities in summary
  Recall = gold entities found in summary / total gold entities
  F1 = harmonic mean of precision and recall
"""

import pandas as pd
import sys
from pathlib import Path

base_path = Path(__file__).parent
sys.path.append(str(base_path.parent))

from features.flair_ner import identify_entities
from features.entity_ranking_and_summarization import entity_ranking, generate_summary


# Load CSV dataset
csv_dataset_path = base_path / "summarization_dataset.csv"
if not csv_dataset_path.exists():
    print("ERROR: summarization_dataset.csv not found. Run article_collection.py first.")
    sys.exit(1)

articles_dataframe = pd.read_csv(csv_dataset_path)
print(f"Loaded {len(articles_dataframe)} articles from {csv_dataset_path}")

# Filter stub articles (RSS placeholders with no real content)
initial_article_count = len(articles_dataframe)
articles_dataframe = articles_dataframe[
    ~articles_dataframe["full_text"].str.strip().str.match(r"^The post .+ appeared first on .+\.$")
]
print(f"Filtered {initial_article_count - len(articles_dataframe)} stub articles, "
      f"{len(articles_dataframe)} remaining\n")


def extract_gold_entities_from_headline(headline_text):
    """Extract named entities from headline as gold standard."""
    extracted_entities = identify_entities(headline_text)
    return set(
        entity["text"].lower() for entity in extracted_entities
    )


# Evaluation loop
summary_precision_list = []
summary_recall_list = []
summary_f1_list = []
skipped_article_count = 0

print("SUMMARIZATION EVALUATION -- ENTITY COVERAGE F1\n")

for _, article_row in articles_dataframe.iterrows():
    # Extract gold entities from headline
    gold_headline_entities = extract_gold_entities_from_headline(article_row["headline"])

    if not gold_headline_entities:
        skipped_article_count += 1
        continue

    # Set top-K equal to number of gold entities
    article_top_k = max(1, len(gold_headline_entities))

    # Run summarization pipeline: extract entities -> rank -> generate summary
    body_flair_entities = identify_entities(article_row["full_text"])
    ranked_entities_list = entity_ranking(article_row["full_text"], body_flair_entities)
    generated_summary = generate_summary(article_row["full_text"], ranked_entities_list[:article_top_k])

    summary_text_lowercase = generated_summary["summary"].lower()

    # Find gold entities that appear in the summary
    gold_entities_in_summary = set(
        entity for entity in gold_headline_entities
        if any(word_token in summary_text_lowercase for word_token in entity.split())
    )

    # Find all ranked entities that appear in the summary
    all_ranked_entities_lowercase = set(
        entity["name"].lower() for entity in ranked_entities_list
    )
    all_ranked_entities_in_summary = set(
        entity for entity in all_ranked_entities_lowercase
        if any(word_token in summary_text_lowercase for word_token in entity.split())
    )

    # Calculate entity coverage metrics
    entity_true_positives = len(gold_entities_in_summary)
    
    entity_precision = (
        entity_true_positives / len(all_ranked_entities_in_summary)
        if all_ranked_entities_in_summary else 0
    )
    entity_recall = (
        entity_true_positives / len(gold_headline_entities)
        if gold_headline_entities else 0
    )
    entity_f1 = (
        (2 * entity_precision * entity_recall / (entity_precision + entity_recall))
        if (entity_precision + entity_recall) > 0 else 0
    )

    summary_precision_list.append(entity_precision)
    summary_recall_list.append(entity_recall)
    summary_f1_list.append(entity_f1)

    # Print per-article results
    print(f"[{article_row['source']}] {article_row['headline'][:65]}...")
    print(f"  Gold entities     : {gold_headline_entities}")
    print(f"  Found in summary  : {gold_entities_in_summary}")
    print(f"  P={entity_precision:.2f}  R={entity_recall:.2f}  F1={entity_f1:.2f}")
    print(f"  Summary ({generated_summary['sentence_count']} sentences): "
          f"{generated_summary['summary'][:120]}...\n")


# Print aggregate results
total_evaluated_articles = len(summary_f1_list)
if total_evaluated_articles == 0:
    print("No articles evaluated.")
    sys.exit(0)

average_precision = sum(summary_precision_list) / total_evaluated_articles
average_recall = sum(summary_recall_list) / total_evaluated_articles
average_f1 = sum(summary_f1_list) / total_evaluated_articles

print(f"RESULTS ({total_evaluated_articles} articles evaluated, "
      f"{skipped_article_count} skipped)\n")
print("SUMMARIZATION -- Entity Coverage F1")
print(f"  Mean Precision : {average_precision:.4f}")
print(f"  Mean Recall    : {average_recall:.4f}")
print(f"  Mean F1        : {average_f1:.4f}")