import solara

user = solara.reactive("")
passwr = solara.reactive("")

@solara.component
def Page():
    solara.lab.theme.dark = True
    solara.Style("""
        .v-btn {
            transition: transform 0.2s ease !important;
        }
        .v-btn:hover {
            transform: translateY(-2px);
        }
        .v-btn:active {
            transform: translateY(0px);
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
        with solara.Card(
            style={
                "padding": "3rem",
                "min-width": "400px",
            },
            elevation=8,
        ):
            with solara.Column(style={"gap": "1.5rem"}):
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
                
                with solara.Column():
                    with solara.Row(
                        justify="center",
                        style={
                        "width": "100%",  # Full width
                        "gap": "1rem",    # Space between buttons
                        }
                    ):
                        solara.Button(
                            "Clear",
                            on_click=lambda: (user.set(""), passwr.set("")),
                            color="#CD5656",
                            raised=True,
                        )
                        solara.Button(
                            "Login",
                            on_click=lambda: print("Login clicked"),
                            color="#75B06F",
                        )

                    with solara.Row(
                        justify="center",  # Centers the buttons horizontally
                        style={
                            "width": "100%",  # Full width 
                        }
                    ):
                        solara.Button(
                        "Register",
                        on_click=lambda: (user.set(""), passwr.set("")),
                        color="#58A0C8",
                    )