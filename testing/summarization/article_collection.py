"""
Article Collection for Summarization Evaluation

Fetches news articles from RSS feeds and saves them to a CSV file for use
in the summarization evaluation script.

Sources: Manila Times, Tech Pinas, The Guardian
"""

import pandas as pd
import sys
from pathlib import Path
from bs4 import BeautifulSoup

base_path = Path(__file__).parent
sys.path.append(str(base_path.parent))

from features.rss_handler import fetch_rss_articles

# RSS feed sources
FEEDS = {
    "manila_times"   : "https://www.manilatimes.net/news/feed/",
    "tech_pinas" : "http://feeds.feedburner.com/Techpinas",
    "the_guardian"   : "https://www.theguardian.com/international/rss",
}

def clean(text):
    """Remove HTML tags and normalize whitespace using BeautifulSoup."""
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator=" ").strip()


# Collect articles from all feeds
collected_article_rows = []
current_article_id = 1

for source_name, feed_url in FEEDS.items():
    # Fetch articles from this feed
    raw_articles_list = fetch_rss_articles(feed_url)
    articles_collected_from_source = 0

    for article_data in raw_articles_list:
        # Extract and clean headline and body text
        article_headline = clean(article_data.get("title", ""))
        article_full_text = clean(article_data.get("description", ""))

        # Skip invalid articles
        if not article_headline or not article_full_text:
            continue
        if len(article_full_text) < 100:  # Skip too short articles
            continue
        if "|" in article_headline:  # Skip articles with pipe 
            continue

        # Add to collection
        collected_article_rows.append({
            "article_id": current_article_id,
            "source": source_name,
            "headline": article_headline,
            "full_text": article_full_text,
        })
        current_article_id += 1
        articles_collected_from_source += 1

    print(f"{source_name}: collected {articles_collected_from_source} articles")

# Save to CSV file
articles_dataframe = pd.DataFrame(collected_article_rows)
csv_output_path = base_path / "summarization_dataset.csv"
articles_dataframe.to_csv(csv_output_path, index=False)

print(f"\nTotal articles saved: {len(articles_dataframe)}")
print(f"Saved to {csv_output_path}")