import solara

user = solara.reactive("")
passwr = solara.reactive("")

@solara.component
def Page():
    solara.Style("""
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
        
        .login {
            background-color: #578FCA !important;
            color: white !important;
            box-shadow: 0px 6px 0px 0px #3674B5 !important; 
        }
                 
        .sign-up {
            background-color: #F5F0CD !important;
            box-shadow: 0px 6px 0px 0px #e1c46d !important; 
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
                "height": "auto",
            }
        ):
            with solara.Column(
                style={
                    "gap": "16px",
                    "background-color": "#FADA7A",
                    }
                ):
                solara.HTML(
                    unsafe_innerHTML="""
                    <div style="text-align: center;">
                        <span style="color:#1C6EA4; font-size:72px; font-weight:bold; font-family: 'Arial', 'Helvetica', sans-serif;">Enti</span>
                        <span style="color:#578FCA; font-size:72px; font-weight:bold; font-family: 'Arial', 'Helvetica', sans-serif;">Lytics</span>
                    </div>
                    """
                )
                # Username
                solara.InputText(
                    label="Username",
                    value=user,
                )
                # Password
                solara.InputText(
                    label="Password",
                    value=passwr,
                    password=True,
                )
                solara.Button(
                    "Login",
                    on_click=lambda: print("Login clicked"),
                    classes=["push-button", "login"]
                )
                solara.Button(
                    "Sign Up",
                    on_click=lambda: print("Sign Up clicked"),
                    classes=["push-button", "sign-up"]
                )
