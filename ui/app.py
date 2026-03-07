import solara
import urllib.parse
import json
import uuid
from features.auth_handler import get_google_login_url, exchange_code_for_user_info
from features.simple_ner import identify_entities
from features.rss_handler import fetch_rss_articles
from features.ranking_and_summarization import entity_ranking, generate_summary
from features.relationship_mapping import mapping
from bs4 import BeautifulSoup 
from features.database import SessionLocal, Article, Summary, Account, Annotation, AnalysisResult, UserSession
from datetime import datetime, timedelta

COOKIE_NAME = "entil_session"

# Global app state
current_view = solara.reactive("login") 
current_user = solara.reactive(None)
current_session_id   = solara.reactive(None)
show_logout_confirm = solara.reactive(False)

# Dashboard state
input_mode = solara.reactive("manual") 
sidebar_open = solara.reactive(True) 
show_help_modal = solara.reactive(False)
rss_link = solara.reactive("")
is_loading = solara.reactive(False)
current_page = solara.reactive(0)
items_per_page = 10
error_message = solara.reactive("")
# UI state for results
display_mode = solara.reactive("summary")  # "summary" or "original"
notes_input = solara.reactive("")
save_status = solara.reactive("")

# Manual input fields
news_title = solara.reactive("")
news_description = solara.reactive("")

# Data storage
selected_article_data = solara.reactive(None)
rss_feed_results = solara.reactive([]) # Stores the list of titles/dates

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

def display_help_button():
    # Help Button 
    solara.Button(icon_name="mdi-help-circle-outline", classes=["help-btn"], on_click=lambda: show_help_modal.set(True))

    # Pop-Up Modal
    if show_help_modal.value:
        with solara.Div(classes=["modal-overlay"]):
            with solara.Div(classes=["modal-content"]):
                solara.Text("About EntiLytics", classes=["space-mono-bold"], style={"font-size": "1.75rem", "color": "#1C6EA4", "border-bottom": "2px solid #FADA7A", "padding-bottom": "10px"})
                
                solara.Text("EntiLytics is a web-based news information management system that helps users understand English online news articles by automatically extracting entities, ranking their importance, mapping relationships, and generating entity‑focused extractive summaries using a pretrained BiLSTM NER model and a transformer-based ranking module.", classes=["roboto-mono-regular"], style={"color": "#444", "line-height": "1.6", "font-size": "1rem"})
                
                solara.Text("Terms of Use", classes=["space-mono-bold"], style={"font-size": "1.25rem", "color": "#578FCA", "margin-top": "10px"})
                solara.Text("By using this workspace, you agree that data processed on this platform is for academic and analytical purposes. User sessions are authenticated securely via Google OAuth 2.0.", classes=["roboto-mono-regular"], style={"color": "#666", "font-size": "0.875rem", "line-height": "1.5"})
                
                # Close Button
                with solara.Row(justify="flex-end", style={"margin-top": "20px"}):
                    solara.Button("Close", classes=["push-button", "action-btn", "roboto-mono-medium"], on_click=lambda: show_help_modal.set(False))

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

@solara.component
def SessionRestorer():
    bridged_sid, set_bridged_sid = solara.use_state("")

    # Use a raw script tag inside HTML to ensure it runs in the browser immediately
    solara.HTML(tag="script", unsafe_innerHTML="""
        (function() {
            function getCookie(name) {
                let v = document.cookie.match('(^|;) ?' + name + '=([^;]*)(;|$)');
                return v ? v[2] : null;
            }
            
            let attempts = 0;
            const checkExist = setInterval(function() {
                const el = document.querySelector("#sid_bridge input");
                attempts++;
                if (el) {
                    const sid = getCookie("entil_sid");
                    el.value = sid ? sid : "NO_COOKIE";
                    // This triggers the Python on_value
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    clearInterval(checkExist);
                } else if (attempts > 50) { // Stop after 5 seconds
                    clearInterval(checkExist);
                }
            }, 100); 
        })();
    """)

    # Put the bridge in a container but keep it hidden
    with solara.Column(style={"display": "none"}):
        solara.InputText(
            label="bridge", 
            value=bridged_sid, 
            on_value=set_bridged_sid,
            attributes={"id": "sid_bridge"}
        )

    def recover():
        if not bridged_sid:
            return 

        print(f"--- BRIDGE HANDSHAKE: Received '{bridged_sid}' ---")

        if bridged_sid == "NO_COOKIE":
            print("No cookie found in browser.")
            is_checking_session.set(False)
        else:
            # THIS IS WHERE YOUR PRINT STARTS
            user_info = resolve_session(bridged_sid) 
            if user_info:
                current_user.set(user_info)
                current_session_id.set(bridged_sid)
                print(f"User {user_info['email']} restored successfully.")
            is_checking_session.set(False)

    solara.use_effect(recover, [bridged_sid])
    return solara.Div(style={"display": "none"})

# LOGIN SCREEN COMPONENT
@solara.component
def LoginScreen():
    router = solara.use_router()
    query_params = urllib.parse.parse_qs(router.search or "")
    auth_code = query_params.get("code", [None])[0]

    def handle_oauth():
        # If we have a code but we are already logged in (via Restorer), ignore it!
        if current_user.value is not None and auth_code:
            router.push("/")
            return

        if auth_code and current_user.value is None:
            user_info = exchange_code_for_user_info(auth_code)
            
            if user_info and "error" in user_info:
                print("Bad code detected. Cleaning URL via redirect...")
                # HARD REDIRECT to wipe the ?code=
                solara.HTML(tag="script", unsafe_innerHTML="window.location.href = window.location.origin + window.location.pathname;")
                return

            if user_info and "error" not in user_info:
                sync_user_to_db(user_info['email'])
                sid = create_session(user_info)
                if sid:
                    current_user.set(user_info)
                    current_view.set("dashboard")
                    # Write cookie AND clean URL
                    solara.HTML(tag="script", unsafe_innerHTML=f"""
                        document.cookie = 'entil_sid={sid}; max-age=604800; path=/; SameSite=Lax';
                        window.location.href = '/';
                    """)

    solara.use_effect(handle_oauth, [auth_code])
    
    # View when logged in
    if current_user.value is not None:
        current_view.set("dashboard")

    # View when logged out
    else:
        with solara.Column(style={"min-height": "100vh", "display": "flex", "justify-content": "center", "align-items": "center", "background-color": "#FADA7A"}):
            with solara.Div(style={"width": "30%", "min-width": "300px", "height": "auto", "background-color": "#FADA7A", "display": "flex", "flex-direction": "column", "align-items": "center", "gap": "30px"}):
                display_help_button()
                solara.HTML(unsafe_innerHTML="""
                    <div style="text-align: center;">
                        <span class='space-mono-bold' style="color:#1C6EA4; font-size:72px;">Enti</span><span class='space-mono-bold' style="color:#578FCA; font-size:72px;">Lytics</span>
                        <p class='roboto-mono-medium' style="color: #666; margin-top: -10px; font-size: 18px;">News Information Management System</p>
                    </div>
                """)
                solara.Button(label="Continue with Google", icon_name="mdi-google", href=get_google_login_url(), classes=["push-button", "google-auth"])
                solara.HTML(unsafe_innerHTML="""
                    <div class='roboto-mono-regular' style="text-align: center; color: #777; font-size: 12px; margin-top: 10px;">
                        By continuing, you agree to EntiLytics' terms. 
                    </div>
                """)


# DASHBOARD SCREEN COMPONENT
@solara.component
def DashboardScreen():
    router = solara.use_router()
    with solara.Div(classes=["dashboard-container"]):
        # Left Sidebar 
        sidebar_class = "sidebar-open" if sidebar_open.value else "sidebar-closed"
        with solara.Div(classes=["sidebar", sidebar_class]):
            with solara.Column(style={"background-color": "transparent", "padding": "10px", "padding-bottom": "30px", "height": "100vh", "width": "100%", "display": "flex", "flex-direction": "column"}):
                with solara.Row(justify="end", style={"width": "100%", "background-color": "#113F67"}):
                    solara.Button(
                        icon_name="mdi-close", 
                        on_click=lambda: sidebar_open.set(False),
                        classes=["mobile-close-btn"], # We will style this in CSS
                        text=True,
                        style={"color": "white", "font-size": "1.5rem", "background-color": "transparent"}
                    )
                
                solara.Text("Saved Articles", classes=["roboto-mono-medium"], style={"color": "white", "font-size": "1.2rem", "border-bottom": "2px solid white", "padding-bottom": "15px", "margin-bottom": "15px"})
                
                # Fetch titles using current_user and refresh on save_status change
                email_val = current_user.value['email'] if current_user.value else None
                saved_list = solara.use_memo(lambda: get_saved_titles(email_val), [email_val, save_status.value])

                if not saved_list:
                    solara.Text("> No articles yet", classes=["roboto-mono-medium"], style={"color": "white","font-size": "1rem", "opacity": "0.8"})
                else:
                    with solara.Column(style={"gap": "5px", "background-color": "transparent", "overflow-y": "auto", "flex-grow": "1"}):
                        for article in saved_list:
                            solara.Button(
                                f"{article.title}", 
                                on_click=lambda a=article: display_historical_analysis(a.articleid),
                                text=True, 
                                classes=["roboto-mono-medium", "article-btn-text"],
                                style={"color": "white", "background": "#113F67", "justify-content": "flex-start", "text-transform": "none", "border-radius": "0", "width": "100%", "overflow": "hidden"}
                            )
                
                # Logout logic
                def handle_logout():    
                    if current_session_id.value:
                        db = SessionLocal()
                        try:
                            db.query(UserSession).filter(UserSession.session_id == current_session_id.value).delete()
                            db.commit()
                        finally:
                            db.close()

                    
                    # Wipe Python App State
                    current_user.set(None)
                    current_session_id.set(None)
                    selected_article_data.set(None)
                    
                    # Redirect to the login screen
                    current_view.set("login")
                    show_logout_confirm.set(False)
                    
                    # Force a clean URL
                    router.push("/")

                with solara.Column(style={"margin-top": "auto", "padding": "10px", "background-color": "transparent"}):
                    if not show_logout_confirm.value:
                        solara.Button(
                            "Log out", 
                            text=True, 
                            classes=["roboto-mono-medium"], 
                            style={"color": "white", "justify-content": "flex-start", "font-size": "1rem"}, 
                            on_click=lambda: show_logout_confirm.set(True)
                        )
                    else:
                        with solara.Row(style={"gap": "10px", "align-items": "center", "background-color": "transparent"}):
                            solara.Text("Are you sure?", classes=["roboto-mono-medium"], style={"color": "white", "font-family": "'Roboto Mono', monospace"})
                            solara.Button(
                                "Yes", 
                                on_click=handle_logout, 
                                classes=["push-button", "red-btn"],
                                style={"background-color": "#d9534f", "color": "white", "padding": "2px 10px"}
                            )
                            solara.Button(
                                "No", 
                                on_click=lambda: show_logout_confirm.set(False), 
                                text=True,
                                classes=["push-button", "toggle-btn"],
                                style={"color": "white"}
                            )

        # Right Workspace
        with solara.Div(classes=["workspace"], style={"position": "relative"}):
            # Hamburger Menu
            solara.Button(icon_name="mdi-menu", classes=["menu-btn"], on_click=lambda: sidebar_open.set(not sidebar_open.value))

            display_help_button()

            # Header
            solara.HTML(unsafe_innerHTML="""
                <div style="text-align: center; width: 100%; margin-bottom: 20px;">
                    <span class='space-mono-bold' style="color:#1C6EA4; font-size:48px;">Enti</span><span class='space-mono-bold' style="color:#578FCA; font-size:48px;">Lytics</span>
                    <p class='roboto-mono-medium' style="color: #666; margin-top: -10px; font-size: 18px;">Workspace</p>
                </div>
            """)

            # Loading Indicator
            if is_loading.value:
                solara.ProgressLinear(color="#1C6EA4")
                solara.Text("Processing...", style={"margin-top":"10px"})

            # Result View 
            elif selected_article_data.value:
                data = selected_article_data.value
                
                with solara.Column(style={"background": "white", "width": "100%", "gap": "1.25rem"}):
                    
                    # Header Row 
                    with solara.Row(justify="space-between", style={"padding": "10px", "align-items": "center"}):
                        solara.Button("← Back", on_click=lambda: [selected_article_data.set(None), notes_input.set(""), save_status.set("")],  text=True, classes=["roboto-mono-medium"])
                        with solara.Div(classes=["segmented-control"]):
                            with solara.ToggleButtonsSingle(value=display_mode, mandatory=True):
                                solara.Button("Summary", value="summary")
                                solara.Button("Original Text", value="original")

                    # Main Layout Grid
                    with solara.Columns([8, 4], style={"gap": "1.25rem", "padding": "10px"}):
                        
                        # LEFT COLUMN: Content and Relationship Map
                        with solara.Column(style={"gap": "1.25rem"}):
                            with solara.Div(style={"background": "white", "padding": "1.5rem", "border-radius": "0.12px", "box-shadow": "0 4px 6px rgba(0,0,0,0.05)"}):
                                solara.Text(data['title'], classes=["roboto-mono-regular"], style={"font-size": "1.5rem", "font-weight": "bold", "margin-bottom": "1rem", "display": "block"})
                                
                                if display_mode.value == "summary":
                                    # Manhattan-distance based extractive summary
                                    solara.Text(data['summary'], classes=["roboto-mono-light"], style={"text-align": "justify", "display": "block", "white-space": "pre-wrap", "line-height": "1.6", "font-size": "1rem"}) 
                                else:
                                    solara.Text(data['original-text'], classes=["roboto-mono-light"], style={"text-align": "justify", "display": "block", "white-space": "pre-wrap", "line-height": "1.6", "font-size": "1rem"})

                            # Relationship Map
                            with solara.Div():
                                solara.Text("Entity Relationship Network", classes=["roboto-mono-medium"], style={"margin-bottom": "0.6rem", "display": "block", "font-size": "1.1rem"})
                                if data['graph']:
                                    solara.HTML(tag="iframe", attributes={
                                        "srcdoc": data['graph'], 
                                        "style": "width:100%; height:35rem; border:1px solid #DDD; border-radius:0.12px; background: white;"
                                    })

                        # RIGHT COLUMN: Analytics & Annotation
                        with solara.Column(style={"gap": "1.25rem"}):
                            # Top Entities (Manhattan Distance Ranking)
                            with solara.Div(style={"background": "white", "padding": "1.25rem", "border-radius": "0.12px"}):
                                solara.Text("Top Entities (Ranked)", classes=["roboto-mono-medium"], style={"color": "#1C6EA4", "margin-bottom": "1rem", "display": "block", "font-size": "1.1rem"})
                                
                                for item in data['rankings'][:8]: 
                                    # Calculation: Lower distance = higher importance (1.0 - dist)
                                    importance_percent = (1 - item['distance']) * 100
                                    
                                    with solara.Column(style={"margin-bottom": "0.75rem"}):
                                        with solara.Row(justify="space-between", style={"align-items": "center"}):
                                            solara.Text(item['name'], classes=["roboto-mono-regular"], style={"font-size": "0.875rem"})
                                            solara.Text(f"Dist: {item['distance']:.2f}", style={"color": "#578FCA", "font-size": "0.75rem"})
                                        
                                        solara.ProgressLinear(
                                            value=importance_percent, 
                                            color="#578FCA", 
                                            style={"height": "0.25rem"} 
                                        )

                            # Extracted Entities (Raw BiLSTM list)
                            with solara.Div(style={"background": "white", "padding": "1.25rem", "border-radius": "0.12px"}):
                                solara.Text("Extracted Entities", classes=["roboto-mono-medium"], style={"color": "#1C6EA4", "margin-bottom": "0.75rem", "display": "block", "font-size": "1rem"})
                                all_names = [e['name'] for e in data['rankings']]
                                with solara.Row(style={"flex-wrap": "wrap", "gap": "0.5rem"}):
                                    for name in all_names:
                                        solara.Div(name, classes=["roboto-mono-regular"], style={"padding": "0.25rem 0.6rem", "border": "1px solid #DDD", "border-radius": "1rem", "font-size": "0.75rem", "background": "#F9F9F9"})

                            # Annotation Section 
                            with solara.Div(style={"background": "white", "padding": "1.25rem", "border-radius": "0.12px"}):
                                solara.Text("Notes", classes=["roboto-mono-medium"], style={"color": "#1C6EA4", "margin-bottom": "0.6rem", "display": "block", "font-size": "1rem"})
                                with solara.Div(style={"font-size": "0.875rem"}):
                                    solara.InputTextArea(
                                        label="Add annotations...", 
                                        value=notes_input, 
                                        rows=5, 
                                        continuous_update=True
                                    )
                                solara.Button(
                                    "Save Analysis", 
                                    classes=["push-button", "action-btn", "roboto-mono-regular"], 
                                    style={"width": "100%", "margin-top": "1rem", "margin-bottom": "1rem", "font-size": "1rem"},
                                    on_click=lambda: save_to_azure(selected_article_data.value, notes_input.value),
                                )
                                with solara.Column():
                                    # Only show if article is stored 
                                    if selected_article_data.value and "articleid" in selected_article_data.value:
                                        with solara.Row(justify="end"):
                                            solara.Button(
                                                icon_name="delete",
                                                on_click=delete_current_article,
                                                classes=["push-button", "red-btn", "roboto-mono-regular"],
                                                 style={"font-size": "1rem", "margin-bottom": "1rem"},
                                            )
                                # Save status
                                if save_status.value == "success":
                                    solara.Success("Analysis Saved", on_close=lambda: save_status.set(""))
                                elif "error" in save_status.value:
                                    solara.Error(f"Cloud Save Failed: {save_status.value}", on_close=lambda: save_status.set(""))

            # Input View (Manual or RSS)
            else:
                with solara.Div(classes=["form-container"]):
                    
                    if error_message.value:
                        solara.Error(error_message.value)

                    if input_mode.value == "manual":
                        solara.InputText("News Title", value=news_title)
                        solara.InputText("Description (Article Content)", value=news_description)
                    else:
                        # RSS Input field
                        solara.InputText("Paste RSS Feed URL", value=rss_link)

                    # Action Buttons Row
                    with solara.Row(justify="center", style={"margin-top": "30px", "gap": "20px", "background-color": "transparent"}):
                        if input_mode.value == "manual":
                            # Run NLP analysis
                            solara.Button("Run Analysis", classes=["push-button", "action-btn", "roboto-mono-medium"], 
                                          on_click=lambda: [handle_manual_analysis(), news_title.set(""), news_description.set("")])
                            
                            solara.Button("Switch to RSS", classes=["push-button", "toggle-btn", "roboto-mono-medium"], 
                                        on_click=lambda: [
                                            news_title.set(""),
                                            news_description.set(""),
                                            rss_feed_results.set([]), 
                                            selected_article_data.set(None), 
                                            error_message.set(""),
                                            input_mode.set("rss"),
                                            news_title.set(""), 
                                            news_description.set("")
                                        ])
                        
                        else:
                            # Fetches the RSS list metadata
                            solara.Button("Fetch Articles", classes=["push-button", "action-btn", "roboto-mono-medium"], 
                                          on_click=lambda: handle_rss_fetch())
                            
                            solara.Button("Switch to Manual Input", classes=["push-button", "toggle-btn", "roboto-mono-medium"], 
                                        on_click=lambda: [
                                            rss_link.set(""),
                                            rss_feed_results.set([]), 
                                            selected_article_data.set(None), 
                                            error_message.set(""),
                                            input_mode.set("manual")
                                        ])
                            
                # RSS Article List Results (Only shows if articles were fetched)
                if input_mode.value == "rss" and rss_feed_results.value:
                    # Calculate start and end indices
                    start = current_page.value * items_per_page
                    end = start + items_per_page
                    paginated_articles = rss_feed_results.value[start:end]
                    # Manual spacing
                    solara.HTML(unsafe_innerHTML='<div style="height: 40px; width: 100%;"></div>')
                    # Render the list
                    with solara.Column(style={"width": "100%", "padding": "0", "border-radius": "12px"}):
                        for article in paginated_articles:
                            with solara.Div(classes=["rss-item-row"], style={"padding":"15px", "display":"flex", "justify-content":"space-between", "align-items":"center"}):
                                with solara.Column(style={"background-color": "transparent"}):
                                    solara.Text(article['title'], classes=["roboto-mono-medium"])
                                    solara.Text(article['published'], style={"font-size":"12px", "color":"#666"})
                                
                                solara.Button("Analyze Now", classes=["push-button", "action-btn", "analyze-btn"], 
                                            on_click=lambda a=article: analyze_article(a))
                    # Manual spacing
                    solara.HTML(unsafe_innerHTML='<div style="height: 20px; width: 100%;"></div>')
                    # Navigation Buttons
                    with solara.Row(justify="center", style={"background-color": "transparent"}):
                        solara.Button("Previous", 
                                    classes=["push-button", "toggle-btn", "roboto-mono-regular"],
                                    disabled=current_page.value == 0, 
                                    on_click=lambda: current_page.set(current_page.value - 1))
                        
                        solara.Text(f"Page {current_page.value + 1}", classes=["roboto-mono-regular"], style={"margin-top": "5px", "color": "#666"})

                        solara.Button("Next", 
                                    classes=["push-button", "toggle-btn", "roboto-mono-regular"],
                                    disabled=end >= len(rss_feed_results.value), 
                                    on_click=lambda: current_page.set(current_page.value + 1))

is_checking_session = solara.reactive(True)

# MASTER PAGE (INJECTS CSS ONCE)
@solara.component
def Page():
    solara.Title("Entilytics")
    with solara.Div(style={"display": "none"}):
        solara.HTML(tag="script", unsafe_innerHTML="""
            document.querySelectorAll("link[rel*='icon']").forEach(el => el.remove());
            var link = document.createElement('link');
            link.rel = 'icon';
            link.type = 'image/png';
            link.href = 'data:image/png;base64,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';
            document.head.appendChild(link);
        """)
    solara.Style("""
        @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@300;400;500&display=swap');
                 
        .space-mono-regular { font-family: "Space Mono", monospace; font-weight: 400; }
        .space-mono-bold { font-family: "Space Mono", monospace; font-weight: 700; }
        .roboto-mono-light { font-family: "Roboto Mono", monospace; font-weight: 300; }
        .roboto-mono-regular { font-family: "Roboto Mono", monospace; font-weight: 400; }
        .roboto-mono-medium { font-family: "Roboto Mono", monospace; font-weight: 500; }

        @keyframes slideUp { 0% { transform: translateY(100vh); } 100% { transform: translateY(0); } }

        .dashboard-container { display: flex; height: 100vh; width: 100vw; margin: 0; overflow: hidden; animation: slideUp 0.8s cubic-bezier(0.16, 1, 0.3, 1); }
        .sidebar { background-color: #113F67; color: white; display: flex; flex-direction: column; justify-content: space-between; transition: width 0.3s ease, padding 0.3s ease; overflow: hidden; white-space: nowrap; z-index: 1000;}
        .sidebar-open { width: 25%; padding: 20px 20px; }
        .sidebar-closed { width: 0%; padding: 0px; }
        .sidebar ::-webkit-scrollbar { width: 5px; }
        .sidebar ::-webkit-scrollbar-track { background: transparent; }
        .sidebar ::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.2); border-radius: 10px; }
        .sidebar ::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.4); }         

        .workspace { width: 75%; height: 100vh; background-color: #FADA7A; flex-grow: 1; padding: 40px 60px; display: flex; flex-direction: column; align-items: center; overflow-y: auto; }
        .form-container { width: 60%; min-width: 450px; display: flex; flex-direction: column; gap: 15px; margin-top: 20px; }
        
        .push-button { border: none !important; border-radius: 8px !important; padding: 10px 20px !important; transition: none !important; text-transform: none !important; cursor: pointer; position: relative; top: 0; }
        .push-button:active { transform: translateY(6px) !important; box-shadow: none !important; } 
        
        .action-btn { background-color: #1C6EA4 !important; color: #FFFFFF !important; box-shadow: 0px 6px 0px 0px #113F67 !important; border: 1px solid #113F67 !important; }
        .toggle-btn, .google-auth { background-color: #FFFFFF !important; color: #444444 !important; box-shadow: 0px 6px 0px 0px #DDDDDD !important; border: 1px solid #DDDDDD !important; }
        
        .red-btn { background-color: #CD5656 !important; color: #FFFFFF !important; box-shadow: 0px 6px 0px 0px #AF3E3E !important; border: 1px solid #AF3E3E !important; }

        .menu-btn { position: absolute !important; top: 30px; left: 30px; background-color: transparent !important; color: #1C6EA4 !important; font-size: 1.75rem !important; min-width: 0 !important; padding: 0 !important; box-shadow: none !important; }
        .menu-btn:hover { color: #578FCA !important; }
                 
        .help-btn { position: absolute !important; top: 30px; right: 30px; background-color: transparent !important; color: #1C6EA4 !important; font-size: 1.75rem !important; min-width: 0 !important; padding: 0 !important; box-shadow: none !important; }
        .help-btn:hover { color: #578FCA !important; }

        /* Saved articles */
        .article-btn-text { white-space: nowrap; overflow: hidden !important; }
        .article-btn-text .v-btn__content { width: 100%; display: block !important; white-space: nowrap !important; overflow: hidden !important; text-overflow: ellipsis !important; text-align: left !important; }
        
        .mobile-close-btn { display: none !important; }   
                       
        /* Toggle Button */
        .segmented-control .v-btn-toggle { background-color: #f0f0f0 !important; border-radius: 12px !important; padding: 4px !important; border: none !important; }

        .segmented-control .v-btn { border-radius: 12px !important; text-transform: none !important; font-family: 'Roboto Mono', monospace !important; letter-spacing: 0 !important; border: none !important; color: #666 !important; }

        .segmented-control .v-btn--active { background-color: #3674B5 !important; color: white !important; box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important; }
                 
        /* Custom Modal CSS */
        .modal-overlay { position: fixed;top: 0; left: 0; width: 100vw; height: 100vh;background-color: rgba(28, 110, 164, 0.4); /* dark blue with transparency */z-index: 9999; /* Force to the front */display: flex;justify-content: center;align-items: center;backdrop-filter: blur(4px); /* frosted glass effect */}
        .modal-content { background-color: #FFFFFF; padding: 40px;border-radius: 12px; width: 50%; min-width: 400px; max-width: 600px; border: 2px solid #1C6EA4; box-shadow: 0px 10px 30px rgba(0,0,0,0.2); display: flex; flex-direction: column; gap: 20px; max-height: 80vh; overflow-y: auto;}
                 
        /* RSS List Hover Effects */
        .rss-item-row { transition: background-color 0.2s; border-radius: 12px; margin-bottom: 5px; } .rss-item-row:hover { background-color: rgba(28, 110, 164, 0.1) !important; }
        .analyze-btn { opacity: 0; transition: opacity 0.2s; }
        .rss-item-row:hover .analyze-btn { opacity: 1; }
                 
        /* Remove solara footer*/
        div[style*="bottom: 0px"][style*="position: absolute"] { display: none !important; }
                 
        /* MOBILE BEHAVIOR */
        @media (max-width: 600px) {
            .mobile-close-btn {
                display: block !important;
                margin-bottom: 10px;
            }
                 
            .sidebar {
                position: fixed; 
                top: 0;
                left: 0;
                height: 100vh;
                width: 100vw;
                background-color: #113F67; 
                z-index: 2000;
            }
            
            .sidebar-closed {
                transform: translateX(-100vw); 
            }
            
            .sidebar-open {
                transform: translateX(0); 
            }
            
            .workspace {
                width: 100vw;
            }
        }
                 
    """)

    SessionRestorer()
    
    print(f"DEBUG: checking={is_checking_session.value}, user={'LOGGED_IN' if current_user.value else 'NONE'}")
    
    # TRAFFIC CONTROLLER WITH LOADING GATE
    if current_user.value is None:
        LoginScreen()
    else:
        DashboardScreen()
