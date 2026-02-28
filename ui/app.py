import solara
import urllib.parse
from features.auth_handler import get_google_login_url, exchange_code_for_user_info

# Global app state
current_view = solara.reactive("login") 
current_user = solara.reactive(None)

# Dashboard state
input_mode = solara.reactive("manual") 
sidebar_open = solara.reactive(True) 
news_title = solara.reactive("")
news_description = solara.reactive("")
news_date = solara.reactive("")
news_source = solara.reactive("")
rss_link = solara.reactive("")


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
            solara.Button(icon_name="mdi-menu", classes=["menu-btn"], on_click=lambda: sidebar_open.set(not sidebar_open.value))

            solara.HTML(unsafe_innerHTML="""
                <div style="text-align: center; width: 100%; margin-bottom: 20px;">
                    <span class='space-mono-bold' style="color:#1C6EA4; font-size:48px;">Enti</span><span class='space-mono-bold' style="color:#578FCA; font-size:48px;">Lytics</span>
                    <p class='roboto-mono-medium' style="color: #666; margin-top: -10px; font-size: 18px;">Workspace</p>
                </div>
            """)

            with solara.Div(classes=["form-container"]):
                if input_mode.value == "manual":
                    solara.InputText("News Title", value=news_title)
                    solara.InputText("Description (Article Content)", value=news_description)
                    solara.InputText("Date Published", value=news_date)
                    solara.InputText("Source URL", value=news_source)
                else:
                    solara.InputText("Paste RSS Feed URL", value=rss_link)

                with solara.Row(justify="center", style={"margin-top": "30px", "gap": "20px", "background-color": "transparent"}):
                    solara.Button("Run Analysis", classes=["push-button", "action-btn", "roboto-mono-medium"], on_click=lambda: print("Initiating BiLSTM..."))
                    
                    if input_mode.value == "manual":
                        solara.Button("Switch to RSS", classes=["push-button", "toggle-btn", "roboto-mono-medium"], on_click=lambda: input_mode.set("rss"))
                    else:
                        solara.Button("Switch to Manual Input", classes=["push-button", "toggle-btn", "roboto-mono-medium"], on_click=lambda: input_mode.set("manual"))

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
    """)

    # Traffic Controller
    if current_view.value == "login":
        LoginScreen()
    elif current_view.value == "dashboard":
        DashboardScreen()