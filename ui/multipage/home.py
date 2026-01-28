import solara
from _utils.shared import SharedComponent


@solara.component
def Page():
    solara.Style("""
        .v-content__wrap {
            background: repeating-linear-gradient(
                 to right,
                 #F8DF95E4 -1%,
                 #F8DF95E4 0%,
                 #FADA7A 0%,
                 #FADA7A 1%
            );
        }
                 
        .theme--light.v-sheet {
            background-color: transparent;
        }
                 
        .v-navigation-drawer__content {
            background-color: #578FCA;
        }
        
    """)
    SharedComponent()
    with solara.Sidebar():
        solara.Markdown("Sidebar")
    with solara.Card(
            style={
                "background-color": "#578FCA",
            },
        ):
            solara.Markdown("This is the home page")
        