import solara

# Reactive variables 
input_mode = solara.reactive("manual") # Toggle between "manual" and "rss"
sidebar_open = solara.reactive(True) 

# Manual fields
news_title = solara.reactive("")
news_description = solara.reactive("")
news_date = solara.reactive("")
news_source = solara.reactive("")

# RSS field
rss_link = solara.reactive("")

@solara.component
def Page():
    solara.Style("""
        @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@300;400;500&display=swap');
                 
        /* Font Classes */
        .space-mono-bold {
            font-family: "Space Mono", monospace;
            font-weight: 700;
        }
        .roboto-mono-medium {
            font-family: "Roboto Mono", monospace;
            font-weight: 500;
        }
        .roboto-mono-regular {
            font-family: "Roboto Mono", monospace;
            font-weight: 400;
        }
                
        @keyframes slideUp {
            0% { transform: translateY(100vh); }
            100% { transform: translateY(0); }
        }

        /* Base Layout */
        .dashboard-container {
            display: flex;
            height: 100vh;
            width: 100vw;
            margin: 0;
            overflow: hidden; 
            animation: slideUp 0.8s cubic-bezier(0.16, 1, 0.3, 1);
        }
        
        /* Custom Sidebar CSS*/
        .sidebar {
            background-color: #1C6EA4; 
            color: white;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: width 0.3s ease, padding 0.3s ease; 
            overflow: hidden;
            white-space: nowrap; /* Keep text from wrapping when shrinking */
        }
        /* Dynamic classes controlled by Python */
        .sidebar-open {
            width: 250px;
            padding: 30px 20px;
        }
        .sidebar-closed {
            width: 0px;
            padding: 0px; 
        }

        
        /* Right Workspace */
        .workspace {
            background-color: #FADA7A; 
            flex-grow: 1;
            padding: 40px 60px;
            display: flex;
            flex-direction: column;
            align-items: center;
            overflow-y: auto;
        }

        .form-container {
            width: 60%;
            min-width: 450px;
            display: flex;
            flex-direction: column;
            gap: 15px;
            margin-top: 20px;
        }
        
        .push-button {
            border: none !important;
            border-radius: 8px !important;
            padding: 10px 20px !important;
            transition: none !important;
            text-transform: none !important;
            cursor: pointer;
            position: relative;
            top: 0;
        }
        .push-button:active {
            transform: translateY(6px) !important;
            box-shadow: none !important;
        }  
        
        /* Dashboard Button Colors */
        .action-btn {
            background-color: #1C6EA4 !important; /* Your dark blue */
            color: #FFFFFF !important;
            box-shadow: 0px 6px 0px 0px #134B70 !important; /* Darker shadow */
            border: 1px solid #134B70 !important;
        }
        .toggle-btn {
            background-color: #FFFFFF !important;
            color: #444444 !important;
            box-shadow: 0px 6px 0px 0px #DDDDDD !important; 
            border: 1px solid #DDDDDD !important;
        }

        /* Hamburger Menu Icon Button */
        .menu-btn {
            position: absolute !important;
            top: 30px;
            left: 30px;
            background-color: transparent !important;
            color: #1C6EA4 !important;
            font-size: 24px !important;
            min-width: 0 !important;
            padding: 0 !important;
            box-shadow: none !important;
        }
        .menu-btn:hover {
            color: #578FCA !important;
        }
    """)

    with solara.Div(classes=["dashboard-container"]):
        
        # Left Sidebar
        # Python conditionally applies open or closed CSS class
        sidebar_class = "sidebar-open" if sidebar_open.value else "sidebar-closed"
        
        with solara.Div(classes=["sidebar", sidebar_class]):
            with solara.Column(style={"background-color": "white", "padding": "10px"}):
                solara.Text("Saved Articles", classes=["roboto-mono-medium"], style={"font-size": "20px", "border-bottom": "2px solid #1C6EA4", "padding-bottom": "15px", "margin-bottom": "15px"})
                solara.Text("> No articles yet", classes=["roboto-mono-regular"], style={"font-size": "14px", "opacity": "0.8"})
            
            solara.Button("Log out", text=True, classes=["roboto-mono-medium"], style={"color": "white"})

        # Right Workspace
        with solara.Div(classes=["workspace"], style={"position": "relative"}):
    
            # Hamburger Button
            solara.Button(
                icon_name="mdi-menu", 
                classes=["menu-btn"],
                on_click=lambda: sidebar_open.set(not sidebar_open.value)
            )

            # Header 
            solara.HTML(unsafe_innerHTML="""
                <div style="text-align: center; width: 100%; margin-bottom: 20px;">
                    <span class='space-mono-bold' style="color:#1C6EA4; font-size:48px;">Enti</span><span class='space-mono-bold' style="color:#578FCA; font-size:48px;">Lytics</span>
                    <p class='roboto-mono-medium' style="color: #666; margin-top: -10px; font-size: 18px;">Workspace</p>
                </div>
            """)

            # Input Form Container
            with solara.Div(classes=["form-container"]):
                if input_mode.value == "manual":
                    solara.InputText("News Title", value=news_title)
                    solara.InputText("Description (Article Content)", value=news_description)
                    solara.InputText("Date Published", value=news_date)
                    solara.InputText("Source URL", value=news_source)
                else:
                    solara.InputText("Paste RSS Feed URL", value=rss_link)

                # Action Buttons Row
                with solara.Row(justify="center", style={"margin-top": "30px", "gap": "20px", "background-color": "transparent"}):
                    solara.Button(
                        "Run Analysis", 
                        classes=["push-button", "action-btn", "roboto-mono-medium"], 
                        on_click=lambda: print("Initiating BiLSTM...")
                    )
                    
                    if input_mode.value == "manual":
                        solara.Button(
                            "Switch to RSS", 
                            classes=["push-button", "toggle-btn", "roboto-mono-medium"], 
                            on_click=lambda: input_mode.set("rss")
                        )
                    else:
                        solara.Button(
                            "Switch to Manual Input", 
                            classes=["push-button", "toggle-btn", "roboto-mono-medium"], 
                            on_click=lambda: input_mode.set("manual")
                        )