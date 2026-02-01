import solara
from features.simple_ner import identify_entities
from features.rss_handler import fetch_rss_articles
from features.transformer_ranking import entity_ranking

text = solara.reactive("")
continuous_update = solara.reactive(True)
results = solara.reactive([])
is_loading = solara.reactive(False) 

def getArticles(rss_url):
    fetched_articles = fetch_rss_articles(rss_url)

    # Avoid flicker problems from using reactive variable
    temp_results = []

    # Using [:3] for quick testing
    for article in fetched_articles[:3]:
        temp_results.append({
            "title" : article['title'],
            "description" : article['description'],
            "entities" : identify_entities(article['description'])
        })

    # Check entity ranking of the first article for quick testing
    entity_ranking(temp_results[0]['description'], temp_results[0]['entities'])
    
    results.set(temp_results)
    is_loading.set(False)

def reset():
    text.set("")
    results.set([]) # Clear the cards
    is_loading.set(False)


# UI Components
@solara.component
def ArticleListings():
    # This component only renders if results.value is not empty
    if results.value:
        for i, article in enumerate(results.value, 1):
            with solara.Card(
                style={
                    "padding": "3rem",
                    "gap": "1rem",
                    "background-color": "#34699A",
                },
                title=f"{i}. {article['title']}", 
                elevation=5
            ):
                solara.Markdown(f"Description: {article['description'][:300]}...")
                solara.Markdown(f"Entities:")
                # Nested loop for entities
                with solara.Column(
                    style={
                        "gap": "1rem",
                        "background-color": "#34699A",
                    }
                ):
                    for ent in article['entities']:
                        solara.Markdown(f"Entity: {ent['text']},        Label: {ent['label']},      CF: {ent['confidence']}")


@solara.component
def Page():
    solara.lab.theme.dark = True
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
                
        # Show loading status if active
        if is_loading.value:
            solara.ProgressLinear() # horizontal progress bar
            solara.Info("Fetching and analyzing articles...")

        # Display the articles
        ArticleListings()