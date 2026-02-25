import solara

@solara.component
def Page():
    solara.Style("""
        @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@300;400;500&display=swap');
                 
        .space-mono-regular {
            font-family: "Space Mono", monospace;
            font-weight: 400;
            font-style: normal;
        }

        .space-mono-bold {
            font-family: "Space Mono", monospace;
            font-weight: 700;
            font-style: normal;
        }

        
        .roboto-mono-light {
            font-family: "Roboto Mono", monospace;
            font-optical-sizing: auto;
            font-weight: 300;
            font-style: normal;
        }
                 
        .roboto-mono-regular {
            font-family: "Roboto Mono", monospace;
            font-optical-sizing: auto;
            font-weight: 400;
            font-style: normal;
        }
                 
        .roboto-mono-medium {
            font-family: "Roboto Mono", monospace;
            font-optical-sizing: auto;
            font-weight: 500;
            font-style: normal;
        }


        # Button
        .v-btn, 
        .v-btn:hover, 
        .v-btn:focus {
            box-shadow: none !important;
            elevation: 0 !important;
            transition: none !important;
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
        
        .google-auth {
            background-color: #FFFFFF !important;
            color: #444444 !important;
            box-shadow: 0px 6px 0px 0px #DDDDDD !important; 
            border: 1px solid #DDDDDD !important;
        }
    
    """)
    with solara.Column(
        style={
            "min-height": "100vh",
            "display": "flex",
            "justify-content": "center",
            "align-items": "center",
            "background-color": "#FADA7A",
        }
    ):
        with solara.Div(
            style={
                "width": "30%",
                "min-width": "300px",
                "height": "auto",
                "background-color": "#FADA7A",
                "display": "flex",
                "flex-direction": "column",
                "align-items": "center",
                "gap": "30px",
            }
        ):
            # Logo Section
            solara.HTML(
                unsafe_innerHTML="""
                <div style="text-align: center;">
                    <span class='space-mono-bold' style="color:#1C6EA4; font-size:72px;">Enti</span><span class='space-mono-bold' style="color:#578FCA; font-size:72px;">Lytics</span>
                    <p class='roboto-mono-medium' style="color: #666; margin-top: -10px; font-size: 18px;">News Information Management System</p>
                </div>
                """
            )
            solara.Button(
                label="Continue with Google",
                icon_name="mdi-google", 
                on_click=lambda: print("Trigger Google OAuth Flow"),
                classes=["push-button", "google-auth"]
            )
            solara.HTML(
                unsafe_innerHTML="""
                <div class='roboto-mono-regular' style="text-align: center; color: #777; font-size: 12px; margin-top: 10px;">
                    By continuing, you agree to EntiLytics' terms. <br>
                    Secure passwordless authentication powered by Google OAuth 2.0.
                </div>
                """
            )