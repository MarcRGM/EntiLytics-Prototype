import solara

import home


routes = [
    solara.Route(path="/", component=home.Page, label="Home"),
]

@solara.component
def Layout(children=[]):
    return solara.AppLayout(
        children=children,
        navigation=True,  # This will now display the tabs
        title="EntiLytics"
    )
