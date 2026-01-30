import solara
from features.simple_ner import identify_entities
from features.rss_handler import fetch_rss_articles

text = solara.reactive("")
continuous_update = solara.reactive(True)
results = solara.reactive([])

def getArticles(rss_url):
    fetched_articles = fetch_rss_articles(rss_url)

    # Avoid flicker problems from using reactive variable
    temp_results = []

    for article in fetched_articles[:3]:
        temp_results.append({
            "title" : article['title'],
            "description" : article['description'],
            "entities" : identify_entities(article['description'])
        })
    results.set(temp_results)

    for result in results.value:
        print(f"Title: {result['title']}")
        print(f"Description: {result['description']}")
        print("Entities: ")
        for ent in result['entities']:
            print(f"{ent['text']}, {ent['label']}")

def reset():
    text.set("")


@solara.component
def Page():
    solara.lab.theme.dark = True
    solara.Style("""
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
        solara.HTML(
            unsafe_innerHTML="""
            <div 
                style="text-align: center;
                background-color: transparent;
            ">
                <span style="color:#1C6EA4; font-size:72px; font-weight:bold; font-family: 'Arial', 'Helvetica', sans-serif;">Enti</span>
                <span style="color:#578FCA; font-size:72px; font-weight:bold; font-family: 'Arial', 'Helvetica', sans-serif;">Lytics</span>
            </div>
            """
        )
        with solara.Card(
                style={
                    "padding": "3rem",
                    "min-width": "400px",
                    "gap": "1rem",
                },
                elevation=10,
            ):
            with solara.Column(style={"gap": "1.5rem"}):
                solara.InputText("RSS feed link", value=text, continuous_update=continuous_update.value)
                with solara.Row():
                    solara.Button("Enter", on_click=lambda: getArticles(text.value), color="#75B06F",)
                    solara.Button("Clear", on_click=lambda: reset(), color="#CD5656",)
                