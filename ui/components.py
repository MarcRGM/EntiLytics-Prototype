import sys
sys.dont_write_bytecode = True

import urllib.parse
import solara

from features.auth_handler import get_google_login_url, exchange_code_for_user_info
from features.database import SessionLocal, Account, UserSession

from state import (
    current_view, current_user, current_role, current_session_id,
    show_logout_confirm, show_delete_confirm, input_mode, sidebar_open, show_help_modal,
    rss_link, is_loading, current_page, items_per_page, error_message,
    display_mode, notes_input, save_status, sidebar_search,
    news_title, news_description, selected_article_data, rss_feed_results,
    is_checking_session
)
from logic import (
    sync_user_to_db, create_session, resolve_session,
    fetch_articles, analyze_article, handle_manual_analysis, handle_rss_fetch,
    get_saved_titles, display_historical_analysis, save_to_azure,
    delete_current_article, delete_user_from_db, get_user_activity
)


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
        # If we have a code but we are already logged in (via Restorer), ignore it
        if current_user.value is not None and auth_code:
            router.push("/")
            return

        if auth_code and current_user.value is None:
            user_info = exchange_code_for_user_info(auth_code)
            
            if user_info and "error" in user_info:
                print("Bad code detected. Cleaning URL via redirect...")
                # Hard redirect to wipe the ?code=
                solara.HTML(tag="script", unsafe_innerHTML="window.location.href = window.location.origin + window.location.pathname;")
                return

            if user_info and "error" not in user_info:
                sync_user_to_db(user_info['email'])
                sid = create_session(user_info)
                if sid:
                    current_user.set(user_info)
                    if current_role.value == "admin":
                        current_view.set("admin") 
                    else:
                        current_view.set("dashboard")
                    # Write cookie and clean URL
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
                        <span class='space-mono-bold login-title' style="color:#1C6EA4;">Enti</span><span class='space-mono-bold login-title' style="color:#578FCA;">Lytics</span>
                        <p class='roboto-mono-medium login-subtitle' style="color: #666; margin-top: -10px;">News Information Management System</p>
                    </div>
                """)
                solara.Button(label="Continue with Google", icon_name="mdi-google", href=get_google_login_url(), classes=["push-button", "google-auth", "login-btn"])
                solara.HTML(unsafe_innerHTML="""
                    <div class='roboto-mono-regular login-terms' style="text-align: center; color: #777; margin-top: 10px;">
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
                        classes=["mobile-close-btn"],
                        text=True,
                        style={"color": "white", "font-size": "1.5rem", "background-color": "transparent"}
                    )
                
                solara.Text("Saved Articles", classes=["roboto-mono-medium", "sidebar-title"], style={"color": "white", "border-bottom": "2px solid white", "padding-bottom": "15px", "margin-bottom": "15px"})
                
                # Search Bar
                with solara.Div(style={"background-color": "transparent"}):
                    solara.InputText(
                        label="Search articles...", 
                        value=sidebar_search, 
                        continuous_update=True,
                        classes=["roboto-mono-regular"],
                        style={
                            "background-color": "white", 
                            "border-radius": "4px",
                            "padding": "15px",
                            "color": "white"
                        }
                    )

                # Fetch titles using current_user and refresh on save_status change
                email_val = current_user.value['email'] if current_user.value else None
                saved_list = solara.use_memo(lambda: get_saved_titles(email_val), [email_val, save_status.value])

                # Filter the list based on the search term
                filtered_list = [
                    article for article in saved_list 
                    if sidebar_search.value.lower() in article.title.lower()
                ] if saved_list else []

                if not saved_list:
                    solara.Text("> No articles yet", classes=["roboto-mono-medium", "sidebar-info"], style={"color": "white", "opacity": "0.8"})
                elif not filtered_list:
                    solara.Text("No matches found", classes=["roboto-mono-medium", "sidebar-info"], style={"color": "white", "padding": "10px"})
                else:
                    with solara.Column(style={"gap": "5px", "background-color": "transparent", "overflow-y": "auto", "flex-grow": "1"}):
                        for article in filtered_list:
                            solara.Button(
                                f"{article.title}", 
                                on_click=lambda a=article: [display_historical_analysis(a.articleid), sidebar_open.set(False)],
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
                    show_delete_confirm.set(False)
                    
                    # Force a clean URL
                    router.push("/")

                with solara.Column(style={"margin-top": "auto", "padding": "10px", "background-color": "transparent"}):
                    if not show_logout_confirm.value:
                        solara.Button(
                            "Log out", 
                            text=True, 
                            classes=["roboto-mono-medium", "sidebar-logout"], 
                            style={"color": "white", "justify-content": "flex-start"}, 
                            on_click=lambda: show_logout_confirm.set(True)
                        )
                    else:
                        with solara.Div(classes=["logout-confirm-container"]):
                            solara.Text("Are you sure?", classes=["roboto-mono-medium", "sidebar-logout"], style={"color": "white", "font-family": "'Roboto Mono', monospace"})
                            with solara.Row(style={"gap": "10px", "background-color": "transparent", "padding": "0"}):
                                solara.Button(
                                    "Yes", 
                                    on_click=handle_logout, 
                                    classes=["push-button", "red-btn", "sidebar-logout", "sidebar-logout-pad"],
                                    style={"background-color": "#d9534f", "color": "white"}
                                )
                                solara.Button(
                                    "No", 
                                    on_click=lambda: show_logout_confirm.set(False), 
                                    text=True,
                                    classes=["push-button", "toggle-btn", "sidebar-logout", "sidebar-logout-pad"],
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
                    <span class='space-mono-bold workspace-title' style="color:#1C6EA4;">Enti</span><span class='space-mono-bold workspace-title' style="color:#578FCA;">Lytics</span>
                    <p class='roboto-mono-medium workspace-subtitle' style="color: #666; margin-top: -10px;">Workspace</p>
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
                    with solara.Row(classes=["analysis-grid"], style={"padding": "10px", "justify-content": "space-between", "flex-wrap": "wrap", "padding": "20px"}):
                        
                        # Content
                        with solara.Column(classes=["left-column-results"], style={"gap": "1.25rem"}):
                            with solara.Div(style={"background": "white", "padding": "1.5rem", "border-radius": "0.12px", "box-shadow": "0 4px 6px rgba(0,0,0,0.05)"}):
                                solara.Text(data['title'], classes=["roboto-mono-regular"], style={"font-size": "1.5rem", "font-weight": "bold", "margin-bottom": "1rem", "display": "block"})
                                
                                if display_mode.value == "summary":
                                    # Manhattan-distance based extractive summary
                                    solara.Text(data['summary'], classes=["roboto-mono-light"], style={"text-align": "justify", "display": "block", "white-space": "pre-wrap", "line-height": "1.6", "font-size": "1rem"}) 
                                else:
                                    solara.Text(data['original-text'], classes=["roboto-mono-light"], style={"text-align": "justify", "display": "block", "white-space": "pre-wrap", "line-height": "1.6", "font-size": "1rem"})

                        # Analytics
                        with solara.Column(classes=["right-column-analytics"], style={"gap": "1.25rem"}):
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
                                        
                # Relationship Map and Notes (Outside the Grid)
                with solara.Column(style={"gap": "1.25rem", "padding": "20px", "width": "100%"}):
                    # Relationship Map
                    with solara.Div(classes=["relationship-map-container"]):
                        solara.Text("Entity Relationship Network", classes=["roboto-mono-medium"], style={"margin-bottom": "0.6rem", "display": "block", "font-size": "1.1rem"})
                        
                        solara.Text(
                            "Click connection lines to view shared context between entities (if applicable).", 
                            style={
                                "font-size": "clamp(10px, 1vw, 12px)", 
                                "color": "#666", 
                                "font-family": "'Roboto Mono', monospace",
                                "display": "block"
                            }
                        )
                        
                        if data['graph']:
                            solara.HTML(tag="iframe", attributes={
                                "srcdoc": data['graph'], 
                                "style": "width:100%; height:35rem; border:1px solid #DDD; border-radius:0.12px; background: white;"
                            })
                            
                    # Annotation Section 
                    with solara.Div(classes=["notes-section-container"]):
                        solara.Text("Notes", classes=["roboto-mono-medium"], style={"color": "#1C6EA4", "margin-bottom": "0.6rem", "display": "block", "font-size": "1rem"})
                        with solara.Div(style={"font-size": "0.875rem"}):
                            solara.InputTextArea(
                                label="Add annotations...", 
                                value=notes_input, 
                                rows=5, 
                                continuous_update=True
                            )
                        with solara.Row(justify="end"):
                            solara.Button(
                                "Save Analysis", 
                                classes=["push-button", "action-btn", "roboto-mono-regular"], 
                                style={"margin-top": "1rem", "margin-bottom": "1rem", "font-size": "1rem", "align-item": "center"},
                                on_click=lambda: save_to_azure(selected_article_data.value, notes_input.value),
                            )
                        with solara.Row(justify="end"):
                            # Only show if article is stored
                            if selected_article_data.value and "articleid" in selected_article_data.value:
                                if not show_delete_confirm.value:
                                    with solara.Row(justify="end"):
                                        solara.Button(
                                            icon_name="mdi-delete",
                                            on_click=lambda: show_delete_confirm.set(True),
                                            classes=["push-button", "red-btn", "roboto-mono-regular"],
                                            style={"font-size": "1rem", "margin-bottom": "1rem"},
                                        )
                                else:
                                    with solara.Div(classes=["logout-confirm-container"]):
                                        with solara.Row(style={"gap": "10px", "background-color": "transparent", "justify-content": "flex-end"}):
                                            solara.Button(
                                                "Delete now", 
                                                on_click=lambda: [delete_current_article(), show_delete_confirm.set(False)], 
                                                classes=["push-button", "red-btn", "roboto-mono-regular"],
                                                style={"background-color": "#d9534f", "color": "white"}
                                            )
                                            solara.Button(
                                                "Cancel", 
                                                on_click=lambda: show_delete_confirm.set(False), 
                                                text=True,
                                                classes=["push-button", "toggle-btn", "roboto-mono-regular"],
                                                style={"font-size": "1rem", "margin-bottom": "1rem"}
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
                        solara.InputText("News Title", value=news_title, style={"width": "100%"})
                        solara.InputText("Description (Article Content)", value=news_description, style={"width": "100%"})
                    else:
                        # RSS Input field
                        solara.InputText("Paste RSS Feed URL", value=rss_link, style={"width": "100%"})

                    # Action Buttons Row
                    with solara.Row(classes=["form-action-row"], style={"background-color": "transparent", "justify-content": "center"}):
                        if input_mode.value == "manual":
                            # Run NLP analysis
                            solara.Button("Run Analysis", classes=["push-button", "action-btn", "roboto-mono-medium", "form-btn-text"], 
                                          on_click=lambda: [handle_manual_analysis(), news_title.set(""), news_description.set("")])
                            
                            solara.Button("Switch to RSS", classes=["push-button", "toggle-btn", "roboto-mono-medium", "form-btn-text"], 
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
                            solara.Button("Fetch Articles", classes=["push-button", "action-btn", "roboto-mono-medium", "form-btn-text"], 
                                          on_click=lambda: handle_rss_fetch())
                            
                            solara.Button("Switch to Manual Input", classes=["push-button", "toggle-btn", "roboto-mono-medium", "form-btn-text"], 
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
                else:  
                    # System Information & Disclaimer Section
                    with solara.Div(style={"width": "100%", "max-width": "850px", "margin": "20px auto", "padding": "0 15px"}):
                        
                        # Usage
                        with solara.Div(style={
                            "background": "#fbfbfb", 
                            "border-left": "3px solid #1C6EA4", 
                            "padding": "15px", 
                            "margin-bottom": "15px",
                            "border-radius": "2px"
                        }):
                            solara.Text("System Information & Usage Guide", classes=["roboto-mono-medium"], 
                                        style={"display": "block", "margin-bottom": "10px", "color": "#1C6EA4", "font-size": "12px", "text-transform": "uppercase"})
                            
                            with solara.Div(classes=["info-clamp-text"], style={"color": "#444"}):
                                solara.HTML(unsafe_innerHTML="""
                                    <b>Entities:</b> Entities are names of people, organizations, and locations detected in the article. If none appear, the content may not contain recognizable proper nouns, or the text is too short for the model to process confidently.<br><br>
                                    <b>Ranked Entities:</b> Not all detected entities are equally important. The system scores each entity by how closely it relates to the article as a whole. Only entities that pass the relevance threshold are ranked and displayed.<br><br>
                                    <b>Relationship Network:</b> The network map shows connections between the top-ranked entities based on how often they appear together in the same context. It will not generate if fewer than two important entities are found. Note that some entities may appear in the map without any connections, as they are still considered important to the article but do not share enough context with other entities to form a relationship.<br><br>
                                    <b>RSS Feed URL:</b> An RSS feed is a link that news websites provide to share their latest articles automatically. Paste one here and the system will fetch and list the available articles for you to analyze.
                                """)

                        # Disclaimer
                        with solara.Div(style={
                            "background": "#fdfdfd", 
                            "border-left": "3px solid #94a3b8", 
                            "padding": "12px 15px", 
                            "border-radius": "2px"
                        }):
                            with solara.Row(style={"align-items": "center", "margin-bottom": "8px", "background-color": "transparent", "gap": "8px"}):
                                solara.v.Icon(children=["mdi-alert-circle-outline"], style_="color: #64748b; font-size: 12px;")
                                solara.Text("Content Disclaimer", classes=["roboto-mono-medium"], 
                                            style={"color": "#475569","font-size": "12px", "text-transform": "uppercase"})
                            
                            with solara.Div(classes=["disclaimer-text"], style={"color": "#64748b"}):
                                solara.HTML(unsafe_innerHTML="""
                                    EntiLytics analyzes the structure and entities of the text provided. It does not verify the accuracy of the content or detect misinformation and fake news. The system is designed for use with news articles and performs best on factual, entity-rich content. While the system will still process any text submitted, results may be less meaningful for non-news content such as opinions, fiction, or social media posts, as these may lack the named entities and structure the system is built around.
                                """)

                # Only show if the user is an admin
                with solara.Row(style={"align-items": "center", "background-color": "transparent", "flex-wrap": "wrap"}):
                    if current_role.value == "admin":
                        solara.Button(
                            "Admin Console", 
                            on_click=lambda: current_view.set("admin"), 
                            icon_name="mdi-shield-account",
                            classes=["push-button", "toggle-btn", "roboto-mono-regular"],
                            style={
                                "font-size": "clamp(0.75rem, 1.2vw, 0.9rem)",
                                "border": "1px solid #1C6EA4" 
                            }
                        )
@solara.component
def AdminPage():
    # Centralized Style Dictionary
    s = {
        "page_container": {
            "padding": "clamp(15px, 3vw, 40px)", 
            "background-color": "#FADA7A", 
            "min-height": "100vh"
        },
        "main_card": {
            "background": "white", 
            "padding": "clamp(15px, 2vw, 25px)", 
            "border-radius": "15px", 
            "box-shadow": "0 4px 6px rgba(0,0,0,0.1)"
        },
        "activity_box": {
            "margin": "10px 0 0 10px", 
            "padding": "15px", 
            "background": "#fdfdfd", 
            "border-left": "4px solid #FADA7A"
        },
        "user_row": {
            "border-bottom": "1px solid #EEE", 
            "padding": "15px 0"
        },
        "search_input": {
            "margin-bottom": "20px", 
            "width": "100%"
        }
    }

    # Reactive states (keep your existing logic)
    users, set_users = solara.use_state([])
    search_term = solara.use_reactive("") 
    refresh_counter = solara.use_reactive(0)
    selected_user_id = solara.use_reactive(None)
    delete_confirm_id = solara.use_reactive(None)
    show_logout_confirm = solara.use_reactive(False)

    def load_users():
        db = SessionLocal()
        try:
            set_users(db.query(Account).all())
        finally:
            db.close()

    solara.use_effect(load_users, [refresh_counter.value])

    # Filtered user list based on search term
    filtered_users = [
        u for u in users 
        if search_term.value.lower() in u.gmail.lower()
    ]

    def handle_delete(uid, email):
        if delete_user_from_db(uid, email):
            refresh_counter.value += 1
            delete_confirm_id.set(None)

    def handle_logout():
        current_user.set(None)
        current_role.set("user")
        solara.HTML(tag="script", unsafe_innerHTML="document.cookie = 'entil_sid=; max-age=0; path=/;'; window.location.href = '/';")

    # UI LAYOUT
    with solara.Column(style=s["page_container"]):
        # Header Section 
        with solara.Row(justify="space-between", style={"background-color": "transparent", "align-items": "center", "margin-bottom": "30px", "gap": "20px"}):
            solara.Text("EntiLytics Admin Console", classes=["space-mono-bold"], 
                        style={"font-size": "clamp(1.5rem, 5vw, 2.5rem)", "color": "#3674B5"})
            
            with solara.Row(style={"gap": "10px", "align-items": "center", "background-color": "transparent", "flex-wrap": "wrap"}):
                solara.Button("View Dashboard", on_click=lambda: current_view.set("dashboard"), classes=["push-button", "toggle-btn", "roboto-mono-regular"])
                
                if not show_logout_confirm.value:
                    solara.Button("Logout", on_click=lambda: show_logout_confirm.set(True), classes=["push-button", "red-btn", "roboto-mono-regular"])
                else:
                    with solara.Row(style={"gap": "10px", "align-items": "center", "background-color": "transparent"}):
                        solara.Text("Confirm?", classes=["roboto-mono-medium"], style={"color": "#3674B5", "font-size": "0.9rem"})
                        solara.Button("Yes", on_click=handle_logout, classes=["push-button", "red-btn"])
                        solara.Button("No", on_click=lambda: show_logout_confirm.set(False), text=True, classes=["push-button", "toggle-btn"], style={"color": "#3674B5"})

        # Main Management Container
        with solara.Div(style=s["main_card"]):
            solara.Text("User Management & Activity Audit", classes=["roboto-mono-medium"], 
                        style={"font-size": "clamp(1rem, 2.5vw, 1.2rem)", "margin-bottom": "15px", "display": "block"})
            
            solara.InputText(label="Search by Gmail...", value=search_term, continuous_update=True, style=s["search_input"])

            for user in filtered_users:
                is_admin = user.account_role == "admin"
                is_pending = delete_confirm_id.value == user.accountid
                
                with solara.Column(style=s["user_row"]):
                    with solara.Row(style={"align-items": "center", "flex-wrap": "wrap", "gap": "10px"}):
                        solara.Text(user.gmail, classes=["roboto-mono-regular"], 
                                    style={
                                        "flex": "1 1 200px", 
                                        "font-size": "clamp(0.85rem, 1.5vw, 1rem)",
                                        "font-weight": "bold" if is_admin else "normal",
                                        "word-break": "break-all"
                                    })
                        
                        # Role Badge
                        solara.Text(user.account_role.upper(), classes=["roboto-mono-regular"], 
                                    style={"width": "80px", "color": "#3674B5" if is_admin else "#666", "font-size": "0.75rem"})
                        
                        solara.Button("Activity", 
                                      on_click=lambda uid=user.accountid: selected_user_id.set(uid if selected_user_id.value != uid else None), 
                                      text=True, style={"color": "#3674B5", "font-size": "0.8rem"})
                        
                        solara.Div(style={"flex-grow": "1"})
                        
                        # Delete Section
                        if not is_pending:
                            solara.Button(icon_name="mdi-delete", 
                                          on_click=lambda uid=user.accountid: delete_confirm_id.set(uid),
                                          disabled=is_admin,
                                          classes=["push-button", "red-btn"] if not is_admin else [],
                                          style={"color": "white" if not is_admin else "#ccc"})
                        else:
                            with solara.Row(style={"gap": "5px"}):
                                solara.Button("Del", on_click=lambda uid=user.accountid: handle_delete(uid, user.gmail), classes=["push-button", "red-btn"])
                                solara.Button("X", on_click=lambda: delete_confirm_id.set(None), text=True)

                    # Activity Dropdown
                    if selected_user_id.value == user.accountid:
                        titles = get_user_activity(user.accountid)
                        with solara.Column(style=s["activity_box"]):
                            if not titles:
                                solara.Text("No history found.", style={"font-size": "0.8rem", "font-style": "italic"})
                            else:
                                for title in titles:
                                    solara.Text(f"• {title}", style={"font-size": "0.85rem", "margin-bottom": "4px"})