# features/rss_handler.py

import feedparser
from datetime import datetime

def fetch_rss_articles(rss_url):
    """
    Fetch articles from an RSS feed.
    
    Args:
        rss_url: The RSS feed URL
        
    Returns:
        List of dictionaries with article info
    """
    
    print(f"Fetching RSS feed from: {rss_url}")
    
    try:
        # Parse the RSS feed
        feed = feedparser.parse(rss_url)
        
        # Check if feed loaded successfully
        if feed.bozo:  # bozo = feed has errors
            print("Warning: Feed may have issues")
        
        articles = []
        
        # Get articles
        for entry in feed.entries:
            
            # Extract article info
            article = {
                'title': entry.get('title', 'No Title'),
                'description': entry.get('description', ''),
                'link': entry.get('link', ''),
                'published': entry.get('published', 'Unknown date'),
                'source': rss_url
            }
            
            articles.append(article)
        
        print(f"Fetched {len(articles)} articles")
        return articles
        
    except Exception as e:
        print(f"Error fetching RSS feed: {e}")
        return []


# Test function
if __name__ == "__main__":
    
    # Get URL
    url = input("Enter a sentence to identify entities: ")
    articles = fetch_rss_articles(url)
    
    print("\n=== ARTICLES ===")
    for i, article in enumerate(articles, 1):
        print(f"\n{i}. {article['title']}")
        print(f"   Link: {article['link']}")
        print(f"   Published: {article['published']}")
        print(f"   Preview: {article['description'][:100]}...")