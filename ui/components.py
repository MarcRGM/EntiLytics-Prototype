import sys
sys.dont_write_bytecode = True

import urllib.parse
import solara

from features.auth_handler import get_google_login_url, exchange_code_for_user_info
from features.database import SessionLocal, Account, UserSession

from theme import COLORS, FONTS, SPACING, RADIUS, SHADOWS, SIZES, CARD_STYLES, LAYOUT_STYLES, MODAL_OVERLAY_STYLE, SIZES

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
    fetch_articles, AnalysisWorker, analyze_article, handle_manual_analysis, handle_rss_fetch,
    RSSWorker, get_saved_titles, display_historical_analysis, save_to_azure,
    delete_current_article, delete_user_from_db, get_user_activity
)


def display_help_button():
    """Display help button and modal with system information"""
    solara.Button(
        icon_name="mdi-help-circle-outline", 
        classes=["help-btn", "action-btn", "push-button"], 
        on_click=lambda: show_help_modal.set(True)
    )

    # Pop-Up Modal
    if show_help_modal.value:
        with solara.Div(classes=["modal-overlay"]):
            with solara.Div(classes=["modal-content"]):
                solara.Text(
                    "About EntiLytics", 
                    classes=["space-mono-bold"], 
                    style={
                        "font-size": SIZES["heading_lg"], 
                        "color": COLORS["primary"],
                        "border-bottom": f"2px solid {COLORS['secondary']}", 
                        "padding-bottom": "10px"
                    }
                )
                
                solara.Text(
                    "EntiLytics is a web-based news information management system that helps users understand English online news articles by automatically extracting entities, ranking their importance, mapping relationships, and generating entity‑focused extractive summaries using a pretrained BiLSTM NER model and a transformer-based ranking module.", 
                    classes=["roboto-mono-regular"], 
                    style={
                        "color": COLORS["text_primary"],
                        "line-height": "1.6", 
                        "font-size": FONTS["body_default"]
                    }
                )
                
                solara.Text(
                    "Terms of Use", 
                    classes=["space-mono-bold"], 
                    style={
                        "font-size": SIZES["heading_md"], 
                        "color": COLORS["primary_light"],
                        "margin-top": "10px"
                    }
                )
                solara.Text(
                    "By using this workspace, you agree that data processed on this platform is for academic and analytical purposes. User sessions are authenticated securely via Google OAuth 2.0.", 
                    classes=["roboto-mono-regular"], 
                    style={
                        "color": COLORS["text_secondary"],
                        "font-size": FONTS["body_small"],
                        "line-height": "1.5"
                    }
                )
                
                # Close Button
                with solara.Row(justify="flex-end", style={"margin-top": "20px"}):
                    solara.Button(
                        "Close", 
                        classes=["push-button", "action-btn", "roboto-mono-medium"], 
                        on_click=lambda: show_help_modal.set(False)
                    )


@solara.component
def SessionRestorer():
    """Restore user session on page refresh using Solara's session ID"""
    sid = solara.get_session_id()

    def recover():
        # If already logged in, skip recovery
        if current_user.value is not None:
            is_checking_session.set(False)
            return

        # Try to resolve session from database
        user_info = resolve_session(sid)
        if user_info:
            current_user.set(user_info)
            current_session_id.set(sid)
            # Store in localStorage as backup
            solara.HTML(tag="script", unsafe_innerHTML=f"""
                localStorage.setItem('entil_session_id', '{sid}');
            """)
        else:
            # Try localStorage backup
            solara.HTML(tag="script", unsafe_innerHTML="""
                var savedSid = localStorage.getItem('entil_session_id');
                if (savedSid) {
                    fetch('/__solara/api/session/set/' + savedSid, {method: 'POST'})
                    .then(() => window.location.reload());
                }
            """)
        
        is_checking_session.set(False)

    solara.use_effect(recover, [])
    return solara.Div(style={"display": "none"})


# LOGIN SCREEN COMPONENT
@solara.component
def LoginScreen():
    """Login screen with Google OAuth integration"""
    router = solara.use_router()
    query_params = urllib.parse.parse_qs(router.search or "")
    auth_code = query_params.get("code", [None])[0]

    def handle_oauth():
        # If we have a code but we are already logged in (via Restorer), ignore it
        if current_user.value is not None and auth_code:
            router.push("/")
            return

        if auth_code and current_user.value is None:
            # Exchange auth code for user info
            user_info = exchange_code_for_user_info(auth_code)
            
            # Handle bad codes
            if user_info and "error" in user_info:
                print("Bad code detected. Cleaning URL via redirect...")
                solara.HTML(tag="script", unsafe_innerHTML="window.location.href = window.location.origin + window.location.pathname;")
                return

            # Successfully got user info
            if user_info and "error" not in user_info:
                sync_user_to_db(user_info['email'])
                sid = solara.get_session_id() # Get the Solara SID
                created_sid = create_session(user_info, sid) # Store it in DB
                
                if created_sid:
                    current_user.set(user_info)
                    current_session_id.set(sid)
                    # Save to localStorage for session persistence across refreshes
                    solara.HTML(tag="script", unsafe_innerHTML=f"""
                        localStorage.setItem('entil_saved_sid', '{sid}');
                        window.location.href = '/';
                    """)

    solara.use_effect(handle_oauth, [auth_code])
    
    # View when logged in
    if current_user.value is not None:
        current_view.set("dashboard")

    # View when logged out
    else:
        with solara.Column(style={
            "min-height": "100vh", 
            "display": "flex", 
            "justify-content": "center", 
            "align-items": "center", 
            "background-color": COLORS["bg_workspace"]
        }):
            with solara.Div(style={
                "width": "30%", 
                "min-width": "300px", 
                "height": "auto", 
                "background-color": COLORS["bg_workspace"], 
                "display": "flex", 
                "flex-direction": "column", 
                "align-items": "center", 
                "gap": "30px"
            }):
                display_help_button()
                solara.HTML(unsafe_innerHTML=f"""
                    <div style="text-align: center;">
                        <span class='space-mono-bold login-title' style="font-size: {SIZES['display_lg']}; color:{COLORS['primary']};">Enti</span><span class='space-mono-bold login-title' style="font-size: {SIZES['display_lg']}; color:{COLORS['primary_light']};">Lytics</span>
                        <p class='roboto-mono-medium login-subtitle' style="font-size: {SIZES['subtitle']}; color: {COLORS['text_secondary']}; margin-top: -10px;">News Information Management System</p>
                    </div>
                """)
                solara.Button(
                    label="Continue with Google", 
                    icon_name="mdi-google", 
                    href=get_google_login_url(), 
                    classes=["push-button", "google-auth", "login-btn"]
                )
                with solara.Column(
                    classes=['roboto-mono-regular', 'login-terms'], 
                    style={
                        "background-color": "transparent", 
                        "text-align": "center", 
                        "color": COLORS["text_light"],
                        "margin-top": "10px", 
                        "gap": "4px", 
                        "padding": "0 20px", 
                        "line-height": "1.5",
                        "font-size": FONTS["body_small"]
                    }
                ):
                    solara.Text("By continuing, you agree to EntiLytics'", style={"display": "inline"})
                    solara.Button(
                        label="terms", 
                        on_click=lambda: show_help_modal.set(True),
                        text=True, 
                        style={
                            "color": COLORS["primary"], 
                            "text-decoration": "underline", 
                            "padding": "0", 
                            "margin": "0",
                            "min-width": "unset", 
                            "height": "auto",
                            "text-transform": "none",
                            "vertical-align": "baseline",
                            "display": "inline-block",
                            "font-size": "inherit",
                            "font-family": "inherit"
                        }
                    )


# DASHBOARD SCREEN COMPONENT
@solara.component
def DashboardScreen():
    """Main dashboard with sidebar, workspace, and analysis view"""
    solara.use_router().push("/")
    # Create both workers at the top
    AnalysisWorker()
    RSSWorker()

    with solara.Div(classes=["dashboard-container"]):
        # Left Sidebar - Saved articles list
        sidebar_class = "sidebar-open" if sidebar_open.value else "sidebar-closed"
        with solara.Div(classes=["sidebar", sidebar_class]):
            with solara.Column(style={
                "background-color": "transparent", 
                "padding": "10px", 
                "padding-bottom": "30px", 
                "height": "100vh", 
                "width": "100%", 
                "display": "flex", 
                "flex-direction": "column"
            }):
                # Mobile close button
                with solara.Row(justify="end", style={
                    "width": "100%", 
                    "background-color": COLORS["primary_dark"]
                }):
                    solara.Button(
                        icon_name="mdi-close", 
                        on_click=lambda: sidebar_open.set(False),
                        classes=["mobile-close-btn", "toggle-btn", "push-button"],
                        text=True,
                        style={
                            "color": COLORS["text_white"], 
                            "margin-bottom": "auto", 
                            "display": "inline-flex", 
                            "font-size": SIZES["heading_md"],
                            "background-color": "transparent"
                        }
                    )
                
                # Sidebar title
                solara.Text(
                    "Saved Articles", 
                    classes=["roboto-mono-medium", "sidebar-title"], 
                    style={
                        "color": COLORS["text_white"], 
                        "border-bottom": f"2px solid {COLORS['text_white']}", 
                        "padding-bottom": "15px", 
                        "margin-bottom": "15px"
                    }
                )
                
                # Search bar
                with solara.Div(style={"background-color": "transparent"}):
                    solara.InputText(
                        label="Search articles...", 
                        value=sidebar_search, 
                        continuous_update=True,
                        classes=["roboto-mono-light", "input"],
                    )

                # Fetch titles using current_user and refresh on save_status change
                email_val = current_user.value['email'] if current_user.value else None
                saved_list = solara.use_memo(lambda: get_saved_titles(email_val), [email_val, save_status.value])

                # Filter the list based on the search term
                filtered_list = [
                    article for article in saved_list 
                    if sidebar_search.value.lower() in article.title.lower()
                ] if saved_list else []

                # Display filtered articles
                with solara.Div(style={
                    "flex-grow": "1", 
                    "display": "flex", 
                    "flex-direction": "column", 
                    "background-color": "transparent", 
                    "overflow-y": "auto"
                }):
                    if not saved_list:
                        solara.Text(
                            "> No articles yet", 
                            classes=["roboto-mono-medium", "sidebar-info"], 
                            style={
                                "color": COLORS["text_white"], 
                                "opacity": "0.8"
                            }
                        )
                    elif not filtered_list:
                        solara.Text(
                            "No matches found", 
                            classes=["roboto-mono-medium", "sidebar-info"], 
                            style={
                                "color": COLORS["text_white"], 
                                "padding": "10px"
                            }
                        )
                    else:
                        with solara.Column(style={"gap": "5px", "background-color": "transparent"}):
                            for article in filtered_list:
                                # Check if this article is currently being viewed
                                is_current = (
                                    selected_article_data.value and 
                                    "articleid" in selected_article_data.value and 
                                    selected_article_data.value["articleid"] == article.articleid 
                                )
                                
                                # Highlight background if this is the current article
                                highlight_style = {
                                    "color": COLORS["text_white"], 
                                    "background": COLORS["primary_darker"] if is_current else COLORS["primary_dark"],
                                    "justify-content": "flex-start", 
                                    "text-transform": "none", 
                                    "border-radius": "0", 
                                    "width": "100%", 
                                    "overflow": "hidden",
                                    "border-left": f"4px solid {COLORS['secondary']}" if is_current else f"4px solid transparent",
                                    "transition": "all 0.2s ease"
                                }

                                solara.Button(
                                    f"{article.title}", 
                                    on_click=lambda a=article: [display_historical_analysis(a.articleid), sidebar_open.set(False)],
                                    text=True, 
                                    classes=["roboto-mono-medium", "article-btn-text"],
                                    style=highlight_style
                                )
                
                # Logout logic
                def handle_logout():    
                    """Handle user logout and session cleanup"""
                    sid = current_session_id.value
                    if sid:
                        db = SessionLocal()
                        try:
                            # Remove the session from database
                            db.query(UserSession).filter(UserSession.session_id == sid).delete()
                            db.commit()
                        finally:
                            db.close()

                    # Wipe Python App State
                    current_user.set(None)
                    current_session_id.set(None)
                    current_role.set("user")
                    selected_article_data.set(None)
                    
                    # Redirect and Clear
                    current_view.set("login")
                    solara.routing.router.push("/")
                    # Solara session reset
                    solara.HTML(tag="script", unsafe_innerHTML="window.location.href = '/';")

                # Logout button
                with solara.Column(style={
                    "margin-top": "auto", 
                    "padding": "10px", 
                    "background-color": "transparent"
                }):
                    if not show_logout_confirm.value:
                        solara.Button(
                            "Log out", 
                            text=True, 
                            icon_name="mdi-logout",
                            classes=["roboto-mono-medium", "sidebar-logout", "toggle-btn", "push-button"], 
                            style={
                                "color": COLORS["text_white"], 
                                "justify-content": "flex-start", 
                                "gap": "8px"
                            }, 
                            on_click=lambda: show_logout_confirm.set(True)
                        )
                    else:
                        with solara.Div(classes=["logout-confirm-container"]):
                            solara.Text(
                                "Are you sure?", 
                                classes=["roboto-mono-medium", "sidebar-logout"], 
                                style={
                                    "color": COLORS["text_white"], 
                                    "font-family": FONTS["mono"]
                                }
                            )
                            with solara.Row(style={"gap": "10px", "background-color": "transparent", "padding": "0"}):
                                solara.Button(
                                    "Yes", 
                                    on_click=handle_logout, 
                                    classes=["push-button", "red-btn", "sidebar-logout", "sidebar-logout-pad"],
                                    style={
                                        "background-color": COLORS["error_light"], 
                                        "color": COLORS["text_white"]
                                    }
                                )
                                solara.Button(
                                    "No", 
                                    on_click=lambda: show_logout_confirm.set(False), 
                                    text=True,
                                    classes=["push-button", "toggle-btn", "sidebar-logout", "sidebar-logout-pad"],
                                    style={"color": COLORS["text_white"]}
                                )

        # Right Workspace
        with solara.Div(classes=["workspace"], style={"position": "relative"}):
            # Menu toggle button
            solara.Button(
                icon_name="mdi-menu", 
                classes=["menu-btn", "toggle-btn", "push-button"], 
                on_click=lambda: sidebar_open.set(not sidebar_open.value)
            )

            display_help_button()

            # Workspace header
            solara.HTML(unsafe_innerHTML=f"""
                <div class='workspace-title-container' style="text-align: center; width: 100%; margin-bottom: 20px;">
                    <span class='space-mono-bold workspace-title'>Enti</span><span class='space-mono-bold workspace-title' style="color:{COLORS['primary_light']};">Lytics</span>
                    <p class='roboto-mono-medium workspace-subtitle' style="margin-top: -10px;">Workspace</p>
                </div>
            """)

            # Loading state
            if is_loading.value:
                solara.ProgressLinear(color=COLORS["primary"])
                solara.Text("Processing...", style={"margin-top":"10px", "color": COLORS["primary"]})

            # Results view (selected article)
            elif selected_article_data.value:
                data = selected_article_data.value
                
                with solara.Column(style={
                    "background": COLORS["bg_white"], 
                    "width": "100%", 
                    "gap": SPACING["xl"]
                }):
                    
                    # Back button and display mode toggle
                    with solara.Div(classes=["results-top-container"]):
                        solara.Button(
                            "Back", 
                            icon_name="mdi-arrow-left", 
                            on_click=lambda: [selected_article_data.set(None), notes_input.set(""), save_status.set("")],  
                            text=True, 
                            classes=["roboto-mono-regular", "back-btn", "push-button"]
                        )
                        with solara.Div(classes=["segmented-control"]):
                            with solara.ToggleButtonsSingle(value=display_mode, mandatory=True):
                                solara.Button("Summary", value="summary")
                                solara.Button("Original Text", value="original")

                    # Main analysis layout
                    with solara.Row(classes=["analysis-grid"], style={
                        "padding": "10px", 
                        "justify-content": "space-between", 
                        "flex-wrap": "wrap"
                    }):
                        
                        # Left column - Article content
                        with solara.Column(classes=["left-column-results"], style={"gap": SPACING["xl"]}):
                            with solara.Div(style={
                                "background": COLORS["bg_white"], 
                                "padding": "1.5rem", 
                                "border-radius": RADIUS["md"], 
                                "box-shadow": SHADOWS["md"]
                            }):
                                solara.Text(
                                    data['title'], 
                                    classes=["roboto-mono-regular"], 
                                    style={
                                        "font-size": SIZES["heading_lg"],
                                        "font-weight": "bold", 
                                        "margin-bottom": "1rem", 
                                        "display": "block"
                                    }
                                )
                                
                                # Show summary or original text based on toggle
                                if display_mode.value == "summary":
                                    # Manhattan-distance based extractive summary
                                    solara.Text(
                                        data['summary'], 
                                        classes=["roboto-mono-light"], 
                                        style={
                                            "text-align": "justify", 
                                            "display": "block", 
                                            "white-space": "pre-wrap", 
                                            "line-height": "1.6", 
                                            "font-size": FONTS["body_default"],
                                            "color": COLORS["text_primary"]
                                        }
                                    ) 
                                else:
                                    solara.Text(
                                        data['original-text'], 
                                        classes=["roboto-mono-light"], 
                                        style={
                                            "text-align": "justify", 
                                            "display": "block", 
                                            "white-space": "pre-wrap", 
                                            "line-height": "1.6", 
                                            "font-size": FONTS["body_default"],
                                            "color": COLORS["text_primary"]
                                        }
                                    )

                        # Right column - Analytics
                        with solara.Column(classes=["right-column-analytics"], style={"gap": SPACING["xl"]}):
                            # Top Entities Card (Manhattan Distance Ranking)
                            with solara.Div(style={
                                "background": COLORS["bg_white"], 
                                "padding": SPACING["xl"], 
                                "border-radius": RADIUS["md"]
                            }):
                                solara.Text(
                                    "Top Entities (Ranked)", 
                                    classes=["roboto-mono-medium"], 
                                    style={
                                        "color": COLORS["primary"], 
                                        "margin-bottom": "1rem", 
                                        "display": "block", 
                                        "font-size": FONTS["section_title"]
                                    }
                                )
                                
                                # Display top 8 entities with importance scores
                                for item in data['rankings'][:8]: 
                                    # Calculation: Lower distance = higher importance (1.0 - dist)
                                    importance_percent = (1 - item['distance']) * 100
                                    
                                    with solara.Column(style={"margin-bottom": "0.75rem"}):
                                        with solara.Row(justify="space-between", style={"align-items": "center"}):
                                            solara.Text(
                                                item['name'], 
                                                classes=["roboto-mono-regular"], 
                                                style={
                                                    "font-size": FONTS["body_small"],
                                                    "color": COLORS["text_primary"]
                                                }
                                            )
                                            solara.Text(
                                                f"Dist: {item['distance']:.2f}", 
                                                style={
                                                    "color": COLORS["primary_light"], 
                                                    "font-size": FONTS["body_xs"]
                                                }
                                            )
                                        
                                        solara.ProgressLinear(
                                            value=importance_percent, 
                                            color=COLORS["primary_light"], 
                                            style={"height": "0.25rem"} 
                                        )

                            # Extracted Entities Card (Raw BiLSTM list)
                            with solara.Div(style={
                                "background": COLORS["bg_white"], 
                                "padding": SPACING["xl"], 
                                "border-radius": RADIUS["md"]
                            }):
                                solara.Text(
                                    "Extracted Entities", 
                                    classes=["roboto-mono-medium"], 
                                    style={
                                        "color": COLORS["primary"], 
                                        "margin-bottom": SPACING["md"], 
                                        "display": "block", 
                                        "font-size": FONTS["body_default"]
                                    }
                                )
                                all_names = [e['text'] for e in data['all_entities']]
                                with solara.Row(style={"flex-wrap": "wrap", "gap": SPACING["sm"]}):
                                    for name in all_names:
                                        solara.Div(
                                            name, 
                                            classes=["roboto-mono-regular"], 
                                            style={
                                                "padding": f"{SPACING['sm']} {SPACING['md']}", 
                                                "border": f"1px solid {COLORS['border_light']}", 
                                                "border-radius": RADIUS["full"], 
                                                "font-size": FONTS["body_xs"],
                                                "background": COLORS["bg_pale"],
                                                "color": COLORS["text_primary"]
                                            }
                                        )
                                        
                # Relationship map and notes section (Outside the Grid)
                with solara.Column(style={
                    "gap": SPACING["xl"], 
                    "padding": SPACING["xl"], 
                    "width": "100%"
                }):
                    # Entity Relationship Network
                    with solara.Div(classes=["relationship-map-container"]):
                        solara.Text(
                            "Entity Relationship Network", 
                            classes=["roboto-mono-medium"], 
                            style={
                                "margin-bottom": SPACING["md"], 
                                "display": "block", 
                                "font-size": FONTS["section_title"],
                                "color": COLORS["text_primary"]
                            }
                        )
                        
                        solara.Text(
                            "Click connection lines to view shared context between entities (if applicable).", 
                            style={
                                "font-size": FONTS["body_small"],
                                "color": COLORS["text_secondary"],
                                "font-family": FONTS["mono"],
                                "display": "block"
                            }
                        )
                        
                        if data['graph']:
                            solara.HTML(tag="iframe", attributes={
                                "srcdoc": data['graph'], 
                                "style": f"width:100%; height:35rem; border:1px solid {COLORS['border_light']}; border-radius:{RADIUS['md']}; background: {COLORS['bg_white']};"
                            })
                            
                    # Notes section
                    with solara.Div(classes=["notes-section-container"]):
                        solara.Text(
                            "Notes", 
                            classes=["roboto-mono-medium"], 
                            style={
                                "color": COLORS["primary"], 
                                "margin-bottom": SPACING["md"], 
                                "display": "block", 
                                "font-size": FONTS["body_default"]
                            }
                        )
                        with solara.Div(style={
                            "font-size": FONTS["body_small"]
                        }, classes=["roboto-mono-light"]):
                            solara.InputTextArea(
                                label="Add annotations...", 
                                value=notes_input, 
                                rows=5, 
                                continuous_update=True,
                            )
                        with solara.Row(justify="end"):
                            solara.Button(
                                "Save Analysis", 
                                classes=["push-button", "action-btn", "roboto-mono-regular"], 
                                style={
                                    "margin-top": "1rem", 
                                    "margin-bottom": "1rem", 
                                    "font-size": FONTS["button_text"],
                                    "align-item": "center"
                                },
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
                                            style={
                                                "font-size": FONTS["button_text"], 
                                                "margin-bottom": "1rem"
                                            },
                                        )
                                else:
                                    with solara.Div(classes=["logout-confirm-container"]):
                                        with solara.Row(style={
                                            "gap": SPACING["lg"], 
                                            "background-color": "transparent", 
                                            "justify-content": "flex-end"
                                        }):
                                            solara.Button(
                                                "Delete now", 
                                                on_click=lambda: [delete_current_article(), show_delete_confirm.set(False)], 
                                                classes=["push-button", "red-btn", "roboto-mono-regular"],
                                                style={
                                                    "background-color": COLORS["error_light"], 
                                                    "color": COLORS["text_white"]
                                                }
                                            )
                                            solara.Button(
                                                "Cancel", 
                                                on_click=lambda: show_delete_confirm.set(False), 
                                                text=True,
                                                classes=["push-button", "toggle-btn", "roboto-mono-regular"],
                                                style={
                                                    "font-size": FONTS["button_text"],
                                                    "margin-bottom": "1rem"
                                                }
                                            )
                        with solara.Row(justify="end"):
                            solara.Button(
                                "Back", 
                                icon_name="mdi-arrow-left", 
                                on_click=lambda: [selected_article_data.set(None), notes_input.set(""), save_status.set("")],  
                                text=True, 
                                classes=["roboto-mono-medium", "back-btn", "push-button"]
                            )
                        
                        # Save status messages
                        if save_status.value == "success":
                            with solara.Row(justify="end", style={"padding-top": SPACING["xl"]}):
                                solara.Success("Analysis Saved", on_close=lambda: save_status.set(""))
                        elif "error" in save_status.value:
                            solara.Error(f"Cloud Save Failed: {save_status.value}", on_close=lambda: save_status.set(""))

            # Input View (Manual or RSS)
            else:
                with solara.Div(classes=["form-container"]):
                    
                    if error_message.value:
                        solara.Error(error_message.value)

                    # Manual input form
                    if input_mode.value == "manual":
                        solara.InputText(
                            "News Title", 
                            value=news_title, 
                            style={"width": "100%"}, 
                            classes=["roboto-mono-light", "input"]
                        )
                        with solara.Div(style={"width": "100%"}, classes=["roboto-mono-light", "input"]):
                            solara.InputTextArea(
                                label="Description (Article Content)", 
                                value=news_description,
                                rows=10, 
                                continuous_update=True,
                            )
                    # RSS input form
                    else:
                        solara.InputText(
                            "RSS Feed URL", 
                            value=rss_link, 
                            style={"width": "100%"}, 
                            classes=["roboto-mono-light", "input"]
                        )
                        
                        # RSS help section
                        with solara.Div(classes=["input"]):
                            with solara.Row(gap=SPACING["md"], style={"align-items": "start", "flex-wrap": "nowrap"}):
                                solara.v.Icon(
                                    children=["mdi-rss-box"], 
                                    style_=f"color: {COLORS['primary']}; font-size: 25px; margin-top: -2px;"
                                )
                                
                                with solara.Div(style={"width": "100%"}):
                                    solara.Text(
                                        "Understanding RSS Feeds", 
                                        classes=["rss-info-header", "roboto-mono-medium"],
                                        style={"color": COLORS["primary_dark"]}
                                    )
                                    solara.HTML(
                                        tag="div", 
                                        classes=["rss-info-body", "roboto-mono-regular"], 
                                        unsafe_innerHTML=f"""
                                            <b>What is it?</b> RSS is a standardized web feed that allows news websites to 
                                            broadcast their latest articles in a machine-readable format.
                                            <br><br>
                                            <b>How to get it:</b> News sites typically provide an RSS link in their footer or 
                                            navigation. When you click it, you will likely see a page of <b>XML code</b> 
                                            (raw text). To use it here, simply <b>copy the URL</b> from your browser's 
                                            address bar and paste it into the field above.
                                            <br><br>
                                            <b>Find RSS Feeds:</b> Browse available feeds at 
                                            <a href="https://rss.feedspot.com/world_news_rss_feeds/" target="_blank" style="color: {COLORS['primary']}; text-decoration: underline;">World News RSS Feeds</a> 
                                            or 
                                            <a href="https://rss.feedspot.com/philippines_news_rss_feeds/" target="_blank" style="color: {COLORS['primary']}; text-decoration: underline;">Philippines News RSS Feeds</a>
                                            <br><br>
                                            <i style="color: {COLORS['text_primary']}; font-size: 0.9em;">Note: Availability depends on the publisher. 
                                            Some feeds may only provide short summaries rather than the full article text.</i>
                                            <br><br>
                                        """
                                    )
                                    # Quick fetch buttons
                                    solara.Text(
                                        "Quick Fetch Popular Feeds", 
                                        classes=["rss-info-header", "roboto-mono-medium"], 
                                        style={
                                            "color": COLORS["primary"], 
                                            "text-align": "center"
                                        }
                                    )
                                    
                                    with solara.Row(justify='center', style={
                                        "padding-bottom": "10px", 
                                        "gap": SPACING["lg"], 
                                        "flex-wrap": "wrap", 
                                        "background-color": "transparent"
                                    }):
                                        solara.Button(
                                            "Manila Times",
                                            classes=["push-button", "back-btn", "roboto-mono-regular"],
                                            on_click=lambda: [rss_link.set("https://www.manilatimes.net/news/feed/"), handle_rss_fetch()]
                                        )
                                        solara.Button(
                                            "Tech Pinas",
                                            classes=["push-button", "back-btn", "roboto-mono-regular"],
                                            on_click=lambda: [rss_link.set("http://feeds.feedburner.com/Techpinas"), handle_rss_fetch()]
                                        )
                                        solara.Button(
                                            "The Guardian",
                                            classes=["push-button", "back-btn", "roboto-mono-regular"],
                                            on_click=lambda: [rss_link.set("https://www.theguardian.com/international/rss"), handle_rss_fetch()]
                                        )

                    # Action buttons
                    with solara.Row(classes=["form-action-row"], style={
                        "background-color": "transparent", 
                        "justify-content": "center"
                    }):
                        if input_mode.value == "manual":
                            solara.Button(
                                "Run Analysis", 
                                classes=["push-button", "action-btn", "roboto-mono-medium", "form-btn-text"], 
                                on_click=lambda: [handle_manual_analysis(), news_title.set(""), news_description.set("")]
                            )
                            
                            solara.Button(
                                "Switch to RSS", 
                                classes=["push-button", "toggle-btn", "roboto-mono-medium", "form-btn-text"], 
                                on_click=lambda: [
                                    news_title.set(""),
                                    news_description.set(""),
                                    rss_feed_results.set([]), 
                                    selected_article_data.set(None), 
                                    error_message.set(""),
                                    input_mode.set("rss"),
                                ]
                            )
                        
                        else:
                            # Fetches the RSS list metadata
                            solara.Button(
                                "Fetch Articles", 
                                classes=["push-button", "action-btn", "roboto-mono-medium", "form-btn-text"], 
                                on_click=lambda: handle_rss_fetch()
                            )
                            
                            solara.Button(
                                "Switch to Manual Input", 
                                classes=["push-button", "toggle-btn", "roboto-mono-medium", "form-btn-text"], 
                                on_click=lambda: [
                                    rss_link.set(""),
                                    rss_feed_results.set([]), 
                                    selected_article_data.set(None), 
                                    error_message.set(""),
                                    input_mode.set("manual")
                                ]
                            )
                            
                # RSS article list results with pagination
                if input_mode.value == "rss" and rss_feed_results.value:
                    # Calculate start and end indices
                    start = current_page.value * items_per_page
                    end = start + items_per_page
                    paginated_articles = rss_feed_results.value[start:end]
                    # Manual spacing
                    solara.HTML(unsafe_innerHTML=f'<div style="height: 40px; width: 100%;"></div>')
                    # Render the list
                    with solara.Column(style={"width": "100%", "padding": "0", "border-radius": RADIUS["lg"]}):
                        for article in paginated_articles:
                            with solara.Div(classes=["rss-item-row"], style={
                                "padding": SPACING["lg"],
                                "display":"flex", 
                                "justify-content":"space-between", 
                                "align-items":"center"
                            }):
                                with solara.Column(style={"background-color": "transparent"}):
                                    solara.Text(
                                        article['title'], 
                                        classes=["roboto-mono-medium"], 
                                        style={
                                            "font-size": FONTS["rss_title"],
                                            "color": COLORS["text_primary"]
                                        }
                                    )
                                    solara.Text(
                                        article['published'], 
                                        style={
                                            "font-size": FONTS["rss_date"], 
                                            "color": COLORS["text_secondary"]
                                        }
                                    )
                                solara.Button(
                                    "Analyze Now", 
                                    classes=["push-button", "action-btn", "analyze-btn"], 
                                    style={
                                        "font-size": FONTS["button_text"], 
                                        "width": "fit-content"
                                    }, 
                                    on_click=lambda a=article: analyze_article(a)
                                )
                    # Manual spacing
                    solara.HTML(unsafe_innerHTML=f'<div style="height: 20px; width: 100%;"></div>')
                    
                    # Pagination controls
                    with solara.Row(justify="center", style={"background-color": "transparent", "padding-bottom": "25px"}):
                        solara.Button(
                            "Previous", 
                            classes=["push-button", "toggle-btn", "roboto-mono-regular"],
                            disabled=current_page.value == 0, 
                            on_click=lambda: current_page.set(current_page.value - 1)
                        )
                        
                        solara.Text(
                            f"Page {current_page.value + 1}", 
                            classes=["roboto-mono-regular"], 
                            style={
                                "margin-top": "5px", 
                                "color": COLORS["text_secondary"]
                            }
                        )

                        solara.Button(
                            "Next", 
                            classes=["push-button", "toggle-btn", "roboto-mono-regular"],
                            disabled=end >= len(rss_feed_results.value), 
                            on_click=lambda: current_page.set(current_page.value + 1)
                        )
                # System information and disclaimer when no articles
                else:  
                    with solara.Div(style={
                        "width": "100%", 
                        "max-width": "850px", 
                        "margin": "20px auto", 
                        "padding": "0 15px"
                    }):
                        
                        # System info container
                        with solara.Div(classes=["info-container"]):
                            solara.Text(
                                "System Information", 
                                classes=["roboto-mono-medium"], 
                                style={
                                    "display": "block", 
                                    "margin-bottom": SPACING["lg"], 
                                    "color": COLORS["primary"], 
                                    "font-size": FONTS["info_header"], 
                                    "text-transform": "uppercase", 
                                    "border-bottom": f"2px solid {COLORS['secondary']}"
                                }
                            )
                            
                            with solara.Div(classes=["info-clamp-text"], style={"color": COLORS["text_primary"]}):
                                solara.HTML(unsafe_innerHTML=f"""
                                    <b>Entities:</b> Entities are names of people, organizations, and locations detected in the article. If none appear, the content may not contain recognizable proper nouns, or the text is too short for the model to process confidently.<br><br>
                                    <b>Ranked Entities:</b> Not all detected entities are equally important. The system scores each entity by how closely it relates to the article as a whole. Only entities that pass the relevance threshold are ranked and displayed. The distance score indicates importance: the closer the value is to 0, the more central and important the entity is to the content.<br><br>
                                    <b>Relationship Network:</b> The network map shows connections between the top-ranked entities based on how often they appear together in the same context. It will not generate if fewer than two important entities are found. Note that some entities may appear in the map without any connections, as they are still considered important to the article but do not share enough context with other entities to form a relationship.<br><br>
                                    <b>Summarization:</b> Not all sentences are equally important to the story. The system scores each sentence by how closely it relates to the top-ranked entities. Only sentences that pass the relevance threshold are selected for the summary. If the system determines that all sentences are important to the top entities, the summary may be similar to the original or still relatively long.
                                """)

                        # Disclaimer container
                        with solara.Div(classes=["disclaimer-container"]):
                            with solara.Row(style={
                                "align-items": "center", 
                                "margin-bottom": "8px", 
                                "background-color": "transparent", 
                                "gap": SPACING["md"]
                            }):
                                solara.v.Icon(
                                    children=["mdi-alert-circle-outline"], 
                                    style_=f"color: {COLORS['secondary']}; font-size: 14px; margin-bottom: {SPACING['lg']};"
                                )
                                solara.Text(
                                    "Content Disclaimer", 
                                    classes=["roboto-mono-medium"], 
                                    style={
                                        "color": COLORS["secondary"],
                                        "font-size": FONTS["info_header"], 
                                        "margin-bottom": SPACING["lg"], 
                                        "text-transform": "uppercase"
                                    }
                                )
                            
                            with solara.Div(classes=["disclaimer-text"], style={"color": COLORS["bg_white"]}):
                                solara.HTML(unsafe_innerHTML=f"""
                                    <b>No Fact-Checking:</b> The system identifies entities but does not verify the factual accuracy of the content, nor does it detect misinformation or fake news.<br><br>
                                    <b>Extraction Redundancy:</b> Due to current model limitations, some entities may appear multiple times as fragments. Users should review the Relationship Network with this in mind.<br><br>
                                    <b>Domain Specificity:</b> The system is optimized for factual, entity-rich news articles. Results for non-news content, such as opinions, fiction, or social media posts, may be less meaningful as they often lack the formal structure the system is built around.
                                """)

                # Only show if the user is an Admin
                with solara.Row(style={
                    "align-items": "center", 
                    "background-color": "transparent", 
                    "flex-wrap": "wrap"
                }):
                    if current_role.value == "admin":
                        solara.Button(
                            "Admin Console", 
                            on_click=lambda: current_view.set("admin"), 
                            icon_name="mdi-shield-account",
                            classes=["push-button", "toggle-btn", "roboto-mono-regular"],
                            style={
                                "font-size": FONTS["button_small"],
                                "border": f"1px solid {COLORS['primary']}"
                            }
                        )


@solara.component
def AdminPage():
    """Admin panel for user management and activity audit"""
    solara.use_router().push("/")
    
    # Style dictionary using theme constants
    s = {
        "page_container": {
            "padding": SPACING["4xl"], 
            "background-color": COLORS["bg_workspace"], 
            "min-height": "100vh",
            "animation": "slideDown 0.8s cubic-bezier(0.16, 1, 0.3, 1);"
        },
        "main_card": {
            "background": COLORS["bg_white"], 
            "padding": SPACING["xl"],
            "border-radius": RADIUS["lg"], 
            "box-shadow": SHADOWS["md"]
        },
        "activity_box": {
            "margin": f"{SPACING['lg']} 0 0 {SPACING['lg']}", 
            "padding": SPACING["lg"], 
            "background": COLORS["bg_lighter"], 
            "border-left": f"4px solid {COLORS['secondary']}"
        },
        "user_row": {
            "border-bottom": f"1px solid {COLORS['border_default']}", 
            "padding": SPACING["lg"]
        },
        "search_input": {
            "margin-bottom": SPACING["xl"], 
            "width": "100%"
        }
    }

    # Reactive states 
    users, set_users = solara.use_state([])
    search_term = solara.use_reactive("") 
    refresh_counter = solara.use_reactive(0)
    selected_user_id = solara.use_reactive(None)
    delete_confirm_id = solara.use_reactive(None)
    show_logout_confirm = solara.use_reactive(False)

    def load_users():
        """Load all users from database"""
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
        """Delete user from database"""
        if delete_user_from_db(uid, email):
            refresh_counter.value += 1
            delete_confirm_id.set(None)

    def handle_logout():
        """Handle admin logout"""
        sid = solara.get_session_id()
        db = SessionLocal()
        try:
            db.query(UserSession).filter(UserSession.session_id == sid).delete()
            db.commit()
        finally:
            db.close()

        current_user.set(None)
        current_role.set("user")
        solara.HTML(tag="script", unsafe_innerHTML="window.location.href = '/';")

    # UI LAYOUT
    with solara.Column(style=s["page_container"]):
        # Header Section 
        with solara.Row(style={"background-color": "transparent", "margin-bottom": "30px"}):
            solara.HTML(unsafe_innerHTML=f"""
                    <div style="text-align: center;">
                        <span class='space-mono-bold admin-title' style="font-size: {SIZES['display_md']}; color:{COLORS['primary']};">Enti</span><span class='space-mono-bold admin-title' style="font-size: {SIZES['display_md']}; color:{COLORS['primary_light']};">Lytics</span>
                    </div>
                """)

        # Main Management Container
        with solara.Div(style=s["main_card"]):
            solara.Text(
                "User Management & Activity Audit", 
                classes=["roboto-mono-medium"], 
                style={
                    "font-size": SIZES["heading_md"],
                    "margin-bottom": SPACING["lg"], 
                    "display": "block",
                    "color": COLORS["text_primary"]
                }
            )
            
            solara.InputText(
                label="Search by Gmail...", 
                value=search_term, 
                continuous_update=True, 
                style=s["search_input"]
            )

            for user in filtered_users:
                is_admin = user.account_role == "admin"
                is_pending = delete_confirm_id.value == user.accountid
                
                with solara.Column(style=s["user_row"]):
                    with solara.Row(style={
                        "align-items": "center", 
                        "flex-wrap": "wrap", 
                        "gap": SPACING["lg"]
                    }):
                        solara.Text(
                            user.gmail, 
                            classes=["roboto-mono-regular"], 
                            style={
                                "flex": "1 1 200px", 
                                "font-size": FONTS["body_default"],
                                "font-weight": "bold" if is_admin else "normal",
                                "word-break": "break-all",
                                "color": COLORS["text_primary"]
                            }
                        )

                        # Role Badge
                        solara.Text(
                            user.account_role.upper(), 
                            classes=["roboto-mono-regular"], 
                            style={
                                "width": "80px", 
                                "color": COLORS["primary_light"] if is_admin else COLORS["text_secondary"], 
                                "font-size": FONTS["body_xs"]
                            }
                        )
                        
                        solara.Button(
                            "Activity", 
                            on_click=lambda uid=user.accountid: selected_user_id.set(uid if selected_user_id.value != uid else None), 
                            text=True, 
                            style={
                                "color": COLORS["primary_light"], 
                                "font-size": FONTS["body_xs"]
                            }
                        )
                        
                        solara.Div(style={"flex-grow": "1"})
                        
                        # Delete button
                        if not is_pending:
                            solara.Button(
                                icon_name="mdi-delete", 
                                on_click=lambda uid=user.accountid: delete_confirm_id.set(uid),
                                disabled=is_admin,
                                classes=["push-button", "red-btn"] if not is_admin else [],
                                style={
                                    "color": COLORS["text_white"] if not is_admin else COLORS["border_light"]
                                }
                            )
                        else:
                            # Delete confirmation
                            with solara.Row(style={"gap": SPACING["sm"]}):
                                solara.Button(
                                    "Del", 
                                    on_click=lambda uid=user.accountid: handle_delete(uid, user.gmail), 
                                    classes=["push-button", "red-btn"]
                                )
                                solara.Button(
                                    "X", 
                                    on_click=lambda: delete_confirm_id.set(None), 
                                    text=True
                                )

                    # Activity dropdown
                    if selected_user_id.value == user.accountid:
                        activity_data = get_user_activity(user.accountid)
                        
                        with solara.Column(style=s["activity_box"]):
                            if not activity_data:
                                solara.Text(
                                    "No historical activity found.", 
                                    style={
                                        "font-size": FONTS["body_xs"], 
                                        "font-style": "italic", 
                                        "color": COLORS["text_muted"]
                                    }
                                )
                            else:
                                for title, date_created in activity_data:
                                    display_date = date_created.strftime("%b %d, %Y") if date_created else "---"
                                    with solara.Row(
                                        justify="space-between", 
                                        style={
                                            "width": "100%", 
                                            "align-items": "flex-start", 
                                            "margin-bottom": SPACING["lg"], 
                                            "gap": SPACING["xl"], 
                                            "background-color": "transparent"
                                        }
                                    ):
                                        solara.Text(
                                            f"• \"{title}\"", 
                                            classes=["roboto-mono-regular"], 
                                            style={
                                                "font-size": FONTS["body_default"], 
                                                "color": COLORS["text_primary"],
                                                "flex": "1", 
                                                "line-height": "1.4"
                                            }
                                        )
                                        solara.Text(
                                            display_date, 
                                            style={
                                                "font-size": FONTS["body_small"], 
                                                "color": COLORS["text_secondary"],  
                                                "white-space": "nowrap",
                                                "font-family": FONTS["mono"],
                                                "text-align": "right",
                                                "margin-top": "2px"   
                                            }
                                        )
        
        # Navigation buttons
        with solara.Row(justify="end", style={
            "gap": SPACING["lg"], 
            "align-items": "center", 
            "background-color": "transparent", 
            "margin-top": SPACING["2xl"], 
            "width": "100%"
        }):
            solara.Button(
                "Dashboard", 
                on_click=lambda: current_view.set("dashboard"), 
                classes=["push-button", "toggle-btn", "roboto-mono-regular"]
            )
            
            if not show_logout_confirm.value:
                solara.Button(
                    "Log Out", 
                    icon_name="mdi-logout",
                    on_click=lambda: show_logout_confirm.set(True), 
                    classes=["push-button", "red-btn", "roboto-mono-regular"],
                    style={"gap": SPACING["md"]}
                )
            else:
                # Logout confirmation
                with solara.Row(style={
                    "gap": SPACING["lg"], 
                    "align-items": "center", 
                    "background-color": "transparent"
                }):
                    solara.Text(
                        "Confirm?", 
                        classes=["roboto-mono-medium"], 
                        style={
                            "color": COLORS["primary"], 
                            "font-size": FONTS["body_small"]
                        }
                    )
                    solara.Button("Yes", on_click=handle_logout, classes=["push-button", "red-btn"])
                    solara.Button(
                        "No", 
                        on_click=lambda: show_logout_confirm.set(False), 
                        text=True, 
                        classes=["push-button", "toggle-btn"], 
                        style={"color": COLORS["primary_light"]}
                    )