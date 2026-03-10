import sys
sys.dont_write_bytecode = True

import json
import uuid
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

from features.flair_ner import identify_entities
from features.rss_handler import fetch_rss_articles
from features.entity_ranking_and_summarization import entity_ranking, generate_summary
from features.relationship_mapping import mapping
from features.database import SessionLocal, Article, Summary, Account, Annotation, AnalysisResult, UserSession

from state import (
    current_user, current_role, current_session_id, current_view,
    is_loading, selected_article_data, rss_feed_results,
    error_message, news_title, news_description, rss_link,
    save_status, notes_input, is_checking_session
)


def fetch_articles(rss_url):
    """Fetches the list of articles without analyzing yet"""
    is_loading.set(True)
    try:
        fetched = fetch_rss_articles(rss_url)
        rss_feed_results.set(fetched)
        selected_article_data.set(None) 
    except Exception as e:
        print(f"RSS Error: {e}")
    finally:
        is_loading.set(False)

def analyze_article(article):
    is_loading.set(True)
    try:
        # Clean the text using BeautifulSoup
        soup = BeautifulSoup(article['description'], "html.parser")
        clean_text = soup.get_text(separator=" ")

        # Run NLP Pipeline
        entities = identify_entities(clean_text)
        rankings = entity_ranking(clean_text, entities)
        summary = generate_summary(clean_text, rankings)
        
        # Generate Map
        top_names = [e['name'] for e in rankings]
        graph_html = mapping(clean_text, top_names) if len(top_names) > 1 else ""

        selected_article_data.set({
            "title": article['title'],
            "original-text": clean_text,
            "summary": summary['summary'],
            "graph": graph_html,
            "rankings": rankings
        })
    finally:
        is_loading.set(False)

def handle_manual_analysis():
    # Reset error first
    error_message.set("")
    
    # Requirement check for Title and Description
    if not news_title.value.strip() and not news_description.value.strip():
        error_message.set("News Title and Description (Article Content) are required for manual analysis.")
        return
    elif not news_title.value.strip():
        error_message.set("News Title is required for manual analysis.")
        return
    elif not news_description.value.strip():
        error_message.set("Description (Article Content) is required for analysis.")
        return

    analyze_article({
        'title': news_title.value, 
        'description': news_description.value
    })

def handle_rss_fetch():
    error_message.set("")
    
    if not rss_link.value.strip():
        error_message.set("Please provide a valid RSS Feed URL.")
        return
    
    fetch_articles(rss_link.value)

def sync_user_to_db(email):
    """Ensures the Google user exists in the Azure Account table."""
    db = SessionLocal()
    try:
        user_acc = db.query(Account).filter(Account.gmail == email).first()
        if not user_acc:
            print(f"Registering new user in Azure: {email}")
            user_acc = Account(gmail=email, account_role="user")
            db.add(user_acc)
            db.commit()
        else:
            print(f"User {email} already exists in database.")
        current_role.set(user_acc.account_role)
    except Exception as e:
        print(f"Failed to sync user to database: {e}")
        db.rollback()
    finally:
        db.close()

def save_to_azure(data_dict, user_notes):
    db = SessionLocal()
    try:
        email = current_user.value['email']
        user_acc = db.query(Account).filter(Account.gmail == email).first()
        
        # Article Logic
        existing_article = db.query(Article).filter(Article.title == data_dict['title']).first()
        if existing_article:
            article_id = existing_article.articleid
        else:
            new_art = Article(
                title=data_dict['title'], 
                content=data_dict.get('original-text') or data_dict.get('content')
            )
            db.add(new_art)
            db.flush() 
            article_id = new_art.articleid

        # Summary Logic
        existing_summary = db.query(Summary).filter(Summary.articleid == article_id).first()
        if existing_summary:
            existing_summary.summarytext = data_dict['summary']
        else:
            db.add(Summary(articleid=article_id, accountid=user_acc.accountid, summarytext=data_dict['summary']))
        
        # Note Logic
        if user_notes:
            existing_note = db.query(Annotation).filter(Annotation.articleid == article_id, Annotation.accountid == user_acc.accountid).first()
            if existing_note:
                existing_note.note = user_notes
            else:
                db.add(Annotation(articleid=article_id, accountid=user_acc.accountid, note=user_notes))
        
        rankings_list = data_dict.get('rankings', [])
        # Extract just names for the bubbles section of the UI
        all_entity_names = [e['name'] for e in rankings_list]
        
        existing_result = db.query(AnalysisResult).filter(AnalysisResult.articleid == article_id).first()
        
        if existing_result:
            existing_result.rankings_json = json.dumps(rankings_list)
            existing_result.entities_all_json = json.dumps(all_entity_names)
            existing_result.graph_html = data_dict.get('graph', "")
        else:
            db.add(AnalysisResult(
                articleid=article_id,
                rankings_json=json.dumps(rankings_list),
                entities_all_json=json.dumps(all_entity_names),
                graph_html=data_dict.get('graph', "")
            ))

        db.commit()

        new_data = {**selected_article_data.value} # Copy existing data
        new_data["articleid"] = article_id # Add the ID 
        selected_article_data.set(new_data) # Push update to UI

        save_status.set("success")

    except Exception as e:
        db.rollback()
        print(f"DATABASE ERROR: {e}")
    finally:
        db.close()

def get_saved_titles(email):
    db = SessionLocal()
    try:
        user_acc = db.query(Account).filter(Account.gmail == email).first()
        if not user_acc:
            return []
        # Get articles linked to this user's summaries
        articles = db.query(Article).join(Summary).filter(Summary.accountid == user_acc.accountid).all()
        return articles
    finally:
        db.close()

def display_historical_analysis(article_id):
    """Fetches saved NLP results and updates the UI state."""
    db = SessionLocal()
    save_status.set("")
    try:
        # Retrieve data from all relevant tables
        article = db.query(Article).filter(Article.articleid == article_id).first()
        summary = db.query(Summary).filter(Summary.articleid == article_id).first()
        result = db.query(AnalysisResult).filter(AnalysisResult.articleid == article_id).first()
        note = db.query(Annotation).filter(Annotation.articleid == article_id).first()

        if article and summary:
            # Reconstruct the dictionary format for the result view
            historical_dict = {
                "articleid": article.articleid,
                "title": article.title,
                "original-text": article.content,
                "summary": summary.summarytext,
                # Graph HTML and Rankings must be parsed from JSON strings
                "graph": result.graph_html if result else "",
                "rankings": json.loads(result.rankings_json) if result and result.rankings_json else []
            }
            
            # Update Solara state variables to trigger the Result View automatically
            selected_article_data.set(historical_dict)
            notes_input.set(note.note if note else "")
            
    finally:
        db.close()

def delete_current_article():
    if not selected_article_data.value or 'articleid' not in selected_article_data.value:
        return

    db = SessionLocal()
    try:
        article_id = selected_article_data.value['articleid']
        
        # These are the Tables that reference articleid
        db.query(Annotation).filter(Annotation.articleid == article_id).delete()
        db.query(Summary).filter(Summary.articleid == article_id).delete()
        db.query(AnalysisResult).filter(AnalysisResult.articleid == article_id).delete()
        
        db.flush()
        db.query(Article).filter(Article.articleid == article_id).delete()
        db.commit()
        
        # Force Sidebar refresh and clear view
        save_status.set("deleted-{article_id}") 
        selected_article_data.set(None)
        
    except Exception as e:
        db.rollback()
        print(f"DELETE ERROR: {e}")
    finally:
        db.close()

# Admin functions
def delete_user_from_db(account_id, gmail):
    db = SessionLocal()
    try:
        # Don't delete if it's an admin account
        user = db.query(Account).filter(Account.accountid == account_id).first()
        if user and user.account_role == "admin":
            return False

        # Delete dependent data in order
        db.query(Annotation).filter(Annotation.accountid == account_id).delete()
        db.query(Summary).filter(Summary.accountid == account_id).delete()
        db.query(UserSession).filter(UserSession.gmail == gmail).delete()
        db.query(Account).filter(Account.accountid == account_id).delete()
        
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error deleting user: {e}")
        return False
    finally:
        db.close()

def get_user_activity(account_id):
    db = SessionLocal()
    try:
        # Fetch articles that have summaries created by this specific user
        articles = db.query(Article).join(Summary).filter(Summary.accountid == account_id).all()
        return [a.title for a in articles]
    finally:
        db.close()

def resolve_session(sid):
    print(f"--- RESOLVING SESSION ---")
    print(f"Received SID from browser: {sid}")
    
    db = SessionLocal()
    try:
        session = db.query(UserSession).filter(UserSession.session_id == sid).first()
        if session:
            print(f"Match found in DB for: {session.gmail}")
            if datetime.utcnow() < session.expires_at:
                print("Session is VALID.")
                return {
                    "email": session.gmail,
                    "name": session.name,
                    "picture": session.picture
                }
            else:
                print("Session EXPIRED.")
        else:
            print("No matching session found in Azure.")
    except Exception as e:
        print(f"DB Error during resolve: {e}")
    finally:
        db.close()
    return None

def create_session(user_info):
    db = SessionLocal()
    try:
        sid = str(uuid.uuid4())
        print(f"--- ATTEMPTING SESSION CREATE ---")
        print(f"User: {user_info.get('email')}")
        print(f"Generated SID: {sid}")

        new_session = UserSession(
            session_id=sid,
            gmail=user_info["email"],
            name=user_info.get("name", "User"),
            picture=user_info.get("picture", ""),
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        
        db.add(new_session)
        db.commit()
        print(f"SUCCESS: Session stored in Azure DB.")
        return sid
    except Exception as e:
        db.rollback()
        print(f"CRITICAL ERROR creating session: {e}")
        return None
    finally:
        db.close()