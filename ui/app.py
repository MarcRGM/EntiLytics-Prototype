import solara
import urllib.parse
from features.auth_handler import get_google_login_url, exchange_code_for_user_info
from features.simple_ner import identify_entities
from features.rss_handler import fetch_rss_articles
from features.ranking_and_summarization import entity_ranking, generate_summary
from features.relationship_mapping import mapping
from bs4 import BeautifulSoup 


# Global app state
current_view = solara.reactive("login") 
current_user = solara.reactive(None)

# Dashboard state
input_mode = solara.reactive("manual") 
sidebar_open = solara.reactive(True) 
show_help_modal = solara.reactive(False)
rss_link = solara.reactive("")
is_loading = solara.reactive(False)

# Manual input fields
news_title = solara.reactive("")
news_description = solara.reactive("")
news_date = solara.reactive("")
news_source = solara.reactive("")

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

# LOGIN SCREEN COMPONENT
@solara.component
def LoginScreen():
    router = solara.use_router()
    raw_search = router.search or ""
    query_params = urllib.parse.parse_qs(raw_search)
    auth_code_list = query_params.get("code")
    auth_code = auth_code_list[0] if auth_code_list else None

    # OAUTH LOGIC
    if auth_code and current_user.value is None:
        user_info = exchange_code_for_user_info(auth_code)
        if "error" not in user_info:
            current_user.set(user_info)
            router.push("/") # clear code from URL

    # View when logged in
    if current_user.value is not None:
        return solara.Column(
            align="center",
            style={"min-height": "100vh", "justify-content": "center", "background-color": "#FADA7A"},
            children=[
                solara.Text(f"Welcome, {current_user.value['name']}!", style={"font-size": "32px", "font-weight": "bold", "color": "#1C6EA4", "font-family": "'Space Mono', monospace"}),
                solara.Text(f"Email: {current_user.value['email']}", style={"color": "#666", "font-family": "'Roboto Mono', monospace"}),
                
                # Trigger dashboard
                solara.Button(
                    "Go to Dashboard", 
                    classes=["push-button", "roboto-mono-medium"],
                    style={"margin-top": "20px", "background-color": "#1C6EA4", "color": "white", "box-shadow": "0px 6px 0px 0px #134B70"}, 
                    on_click=lambda: current_view.set("dashboard")
                ) 
            ]
        )

    # View when logged out
    with solara.Column(style={"min-height": "100vh", "display": "flex", "justify-content": "center", "align-items": "center", "background-color": "#FADA7A"}):
        with solara.Div(style={"width": "30%", "min-width": "300px", "height": "auto", "background-color": "#FADA7A", "display": "flex", "flex-direction": "column", "align-items": "center", "gap": "30px"}):
            solara.HTML(unsafe_innerHTML="""
                <div style="text-align: center;">
                    <span class='space-mono-bold' style="color:#1C6EA4; font-size:72px;">Enti</span><span class='space-mono-bold' style="color:#578FCA; font-size:72px;">Lytics</span>
                    <p class='roboto-mono-medium' style="color: #666; margin-top: -10px; font-size: 18px;">News Information Management System</p>
                </div>
            """)
            solara.Button(label="Continue with Google", icon_name="mdi-google", href=get_google_login_url(), classes=["push-button", "google-auth"])
            solara.HTML(unsafe_innerHTML="""
                <div class='roboto-mono-regular' style="text-align: center; color: #777; font-size: 12px; margin-top: 10px;">
                    By continuing, you agree to EntiLytics' terms. <br>
                    Secure passwordless authentication powered by Google OAuth 2.0.
                </div>
            """)


# DASHBOARD SCREEN COMPONENT
@solara.component
def DashboardScreen():
    with solara.Div(classes=["dashboard-container"]):
        
        # Left Sidebar 
        sidebar_class = "sidebar-open" if sidebar_open.value else "sidebar-closed"
        with solara.Div(classes=["sidebar", sidebar_class]):
            with solara.Column(style={"background-color": "white", "padding": "10px"}):
                solara.Text("Saved Articles", classes=["roboto-mono-medium"], style={"font-size": "20px", "border-bottom": "2px solid #1C6EA4", "padding-bottom": "15px", "margin-bottom": "15px"})
                solara.Text("> No articles yet", classes=["roboto-mono-regular"], style={"font-size": "14px", "opacity": "0.8"})
            
            # Logout logic
            def handle_logout():
                current_user.set(None)
                current_view.set("login")

            solara.Button("Log out", text=True, classes=["roboto-mono-medium"], style={"color": "white"}, on_click=handle_logout)

        # Right Workspace
        with solara.Div(classes=["workspace"], style={"position": "relative"}):
            # Hamburger Menu
            solara.Button(icon_name="mdi-menu", classes=["menu-btn"], on_click=lambda: sidebar_open.set(not sidebar_open.value))

            # Help Button 
            solara.Button(icon_name="mdi-help-circle-outline", classes=["help-btn"], on_click=lambda: show_help_modal.set(True))

            # Pop-Up Modal
            if show_help_modal.value:
                with solara.Div(classes=["modal-overlay"]):
                    with solara.Div(classes=["modal-content"]):
                        solara.Text("About EntiLytics", classes=["space-mono-bold"], style={"font-size": "28px", "color": "#1C6EA4", "border-bottom": "2px solid #FADA7A", "padding-bottom": "10px"})
                        
                        solara.Text("EntiLytics is a web-based news information management system that helps users understand English online news articles by automatically extracting entities, ranking their importance, mapping relationships, and generating entity‑focused extractive summaries using a pretrained BiLSTM NER model and a transformer-based ranking module.", classes=["roboto-mono-regular"], style={"color": "#444", "line-height": "1.6"})
                        
                        solara.Text("Terms of Use", classes=["space-mono-bold"], style={"font-size": "20px", "color": "#578FCA", "margin-top": "10px"})
                        solara.Text("By utilizing this workspace, you agree that data processed on this platform is for academic and analytical purposes. User sessions are authenticated securely via Google OAuth 2.0.", classes=["roboto-mono-regular"], style={"color": "#666", "font-size": "14px", "line-height": "1.5"})
                        
                        # Close Button
                        with solara.Row(justify="flex-end", style={"margin-top": "20px"}):
                            solara.Button("Close", classes=["push-button", "action-btn", "roboto-mono-medium"], on_click=lambda: show_help_modal.set(False))

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

            # Result View (Detailed Analysis)
            elif selected_article_data.value:
                solara.Button("← Back to List", on_click=lambda: selected_article_data.set(None), text=True)
                solara.Text(selected_article_data.value['title'], style={"font-size":"24px", "font-weight":"bold"})
                solara.Markdown(f"### Summary\n{selected_article_data.value['summary']}")
                if selected_article_data.value['graph']:
                    solara.HTML(tag="iframe", attributes={"srcdoc": selected_article_data.value['graph'], "style": "width:100%; height:500px; border:none; border-radius:10px;"})

            # Input View (Manual or RSS)
            else:
                with solara.Div(classes=["form-container"]):
                    if input_mode.value == "manual":
                        solara.InputText("News Title", value=news_title)
                        solara.InputText("Description (Article Content)", value=news_description)
                        solara.InputText("Date Published", value=news_date)
                        solara.InputText("Source URL", value=news_source)
                    else:
                        # RSS Input field
                        solara.InputText("Paste RSS Feed URL", value=rss_link)

                    # Action Buttons Row
                    with solara.Row(justify="center", style={"margin-top": "30px", "gap": "20px", "background-color": "transparent"}):
                        if input_mode.value == "manual":
                            # Run NLP analysis
                            solara.Button("Run Analysis", classes=["push-button", "action-btn", "roboto-mono-medium"], 
                                          on_click=lambda: analyze_article({'title': news_title.value, 'description': news_description.value}))
                            
                            solara.Button("Switch to RSS", classes=["push-button", "toggle-btn", "roboto-mono-medium"], 
                                        on_click=lambda: [
                                            news_title.set(""),
                                            news_description.set(""),
                                            news_date.set(""),
                                            news_source.set(""),
                                            rss_feed_results.set([]), 
                                            selected_article_data.set(None), 
                                            input_mode.set("rss")
                                        ])
                        
                        else:
                            # Fetches the RSS list metadata
                            solara.Button("Fetch Articles", classes=["push-button", "action-btn", "roboto-mono-medium"], 
                                          on_click=lambda: fetch_articles(rss_link.value))
                            
                            solara.Button("Switch to Manual Input", classes=["push-button", "toggle-btn", "roboto-mono-medium"], 
                                        on_click=lambda: [
                                            rss_link.set(""),
                                            rss_feed_results.set([]), 
                                            selected_article_data.set(None), 
                                            input_mode.set("manual")
                                        ])
                            
                # RSS Article List Results (Only shows if articles were fetched)
                if input_mode.value == "rss" and rss_feed_results.value:
                    # Manual spacing
                    solara.HTML(unsafe_innerHTML='<div style="height: 40px; width: 100%;"></div>')
                    with solara.Column(style={"width": "100%", "padding": "0", "border-radius": "8px"}):
                        for article in rss_feed_results.value:
                            with solara.Div(classes=["rss-item-row"], style={"padding":"15px", "display":"flex", "justify-content":"space-between", "align-items":"center"}):
                                with solara.Column(style={"background-color": "transparent"}):
                                    solara.Text(article['title'], classes=["roboto-mono-medium"])
                                    solara.Text(article['published'], style={"font-size":"12px", "color":"#666"})
                                
                                solara.Button("Analyze Now", classes=["push-button", "action-btn", "analyze-btn"], 
                                            on_click=lambda a=article: analyze_article(a))


# MASTER PAGE (INJECTS CSS ONCE)
@solara.component
def Page():
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
        .sidebar { background-color: #1C6EA4; color: white; display: flex; flex-direction: column; justify-content: space-between; transition: width 0.3s ease, padding 0.3s ease; overflow: hidden; white-space: nowrap; }
        .sidebar-open { width: 250px; padding: 30px 20px; }
        .sidebar-closed { width: 0px; padding: 0px; }
        .workspace { background-color: #FADA7A; flex-grow: 1; padding: 40px 60px; display: flex; flex-direction: column; align-items: center; overflow-y: auto; }
        .form-container { width: 60%; min-width: 450px; display: flex; flex-direction: column; gap: 15px; margin-top: 20px; }
        
        .push-button { border: none !important; border-radius: 8px !important; padding: 10px 20px !important; transition: none !important; text-transform: none !important; cursor: pointer; position: relative; top: 0; }
        .push-button:active { transform: translateY(6px) !important; box-shadow: none !important; } 
        
        .action-btn { background-color: #1C6EA4 !important; color: #FFFFFF !important; box-shadow: 0px 6px 0px 0px #134B70 !important; border: 1px solid #134B70 !important; }
        .toggle-btn, .google-auth { background-color: #FFFFFF !important; color: #444444 !important; box-shadow: 0px 6px 0px 0px #DDDDDD !important; border: 1px solid #DDDDDD !important; }
        
        .menu-btn { position: absolute !important; top: 30px; left: 30px; background-color: transparent !important; color: #1C6EA4 !important; font-size: 24px !important; min-width: 0 !important; padding: 0 !important; box-shadow: none !important; }
        .menu-btn:hover { color: #578FCA !important; }
                 
        /* Help Button */
        .help-btn { 
            position: absolute !important; top: 30px; right: 30px; background-color: transparent !important; color: #1C6EA4 !important; font-size: 24px !important; min-width: 0 !important; padding: 0 !important; box-shadow: none !important; }
        .help-btn:hover { color: #578FCA !important; }

        /* Custom Modal CSS */
        .modal-overlay { position: fixed;top: 0; left: 0; width: 100vw; height: 100vh;background-color: rgba(28, 110, 164, 0.4); /* dark blue with transparency */z-index: 9999; /* Force to the front */display: flex;justify-content: center;align-items: center;backdrop-filter: blur(4px); /* frosted glass effect */}
        .modal-content { background-color: #FFFFFF; padding: 40px;border-radius: 12px; width: 50%; min-width: 400px; max-width: 600px; border: 2px solid #1C6EA4; box-shadow: 0px 10px 30px rgba(0,0,0,0.2); display: flex; flex-direction: column; gap: 20px; max-height: 80vh; overflow-y: auto;}
                 
        /* RSS List Hover Effects */
        .rss-item-row {
            transition: background-color 0.2s;
            border-radius: 8px;
            margin-bottom: 5px;
        }
        .rss-item-row:hover {
            background-color: rgba(28, 110, 164, 0.1) !important;
        }
        .analyze-btn {
            opacity: 0;
            transition: opacity 0.2s;
        }
        .rss-item-row:hover .analyze-btn {
            opacity: 1;
        }
    """)

    # Traffic Controller
    if current_view.value == "login":
        LoginScreen()
    elif current_view.value == "dashboard":
        DashboardScreen()