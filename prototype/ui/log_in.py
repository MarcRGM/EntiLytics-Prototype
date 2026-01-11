import solara


user = solara.reactive("")
passwr = solara.reactive("")
continuous_update = solara.reactive(True)

@solara.component
def Page():
    solara.Style("""
    html, body {
        margin: 0;
        padding: 0;
        height: 100%;
    }
    """)

    # Outer container fills viewport
    with solara.Div(
        style={
            "height": "100vh",
            "width": "100vw",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "center",
            "alignItems": "center",
            "backgroundColor": "#FADA7A",
        }
    ):
        solara.Markdown("""
        <span style="color:#1C6EA4; font-size:72px; font-weight:bold; font-family: 'Arial', 'Helvetica', sans-serif;">Enti</span>
        <span style="color:#578FCA; font-size:72px; font-weight:bold; font-family: 'Arial', 'Helvetica', sans-serif;">Lytics</span>
        """)
        solara.InputText(
            label="Username",
            value=user,
            continuous_update=continuous_update.value,
        )
        solara.InputText(
            label="Password",
            value=passwr,
            continuous_update=continuous_update.value,
        )

        with solara.Row():
            solara.Button("Clear", on_click=lambda: (user.set(""), passwr.set("")))
