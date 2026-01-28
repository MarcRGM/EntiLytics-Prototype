import solara

# Folder has _ to let solara treat it as private and to remove it from the navigation tab

# some app state that outlives a single page
app_state = solara.reactive(0)

@solara.component
def SharedComponent():
    with solara.Card(
        style={
                "padding": "1rem",
                "min-height": "30vh",
                "display": "flex",
                "justify-content": "center",
                "align-items": "center",
                "background-color": "transparent",
        },
        elevation=0,
    ):
        solara.HTML(
            unsafe_innerHTML="""
            <div style="text-align: center;">
                <span style="color:#1C6EA4; font-size:72px; font-weight:bold; font-family: 'Arial', 'Helvetica', sans-serif;">Enti</span>
                <span style="color:#578FCA; font-size:72px; font-weight:bold; font-family: 'Arial', 'Helvetica', sans-serif;">Lytics</span>
            </div>
            """
        )
