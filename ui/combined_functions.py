import solara
from features.simple_ner import identify_entities
from features.rss_handler import fetch_rss_articles
from features.ranking_and_summarization import entity_ranking, generate_summary
from features.relationship_mapping import mapping

import sys
sys.dont_write_bytecode = True

text = solara.reactive("")
continuous_update = solara.reactive(True)
results = solara.reactive([])
is_loading = solara.reactive(False) 

def getArticles(rss_url):
    is_loading.set(True)

    try:
        fetched_articles = fetch_rss_articles(rss_url)

        # Avoid flicker problems from using reactive variable
        temp_results = []

        # Using [:3] for quick testing
        for article in fetched_articles[:3]:
            extracted_entities = identify_entities(article['description'])
            
            ranking = entity_ranking(article['description'], extracted_entities)
            
            summarize = generate_summary(article['description'], ranking)

            entity_names = [ent['name'] for ent in ranking[:10]]
            article_graph = ""
            # Only run it if there are at least 2 entities
            if len(entity_names) > 1:
                article_graph = mapping(article['description'], entity_names)

            temp_results.append({
                "title" : article['title'],
                "description" : article['description'],
                "entities" : extracted_entities,
                "importance" : ranking,
                "graph_html": article_graph,
                "summary" : summarize['summary']
            })
        
        results.set(temp_results)
        is_loading.set(False)

    except Exception as e:
        print(f"Error: {e}")
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
                solara.Markdown(f"### Description:")
                solara.Markdown(article['description'])
                solara.Markdown("")
                solara.Markdown("")

                solara.Markdown(f"### Summary:")
                solara.Markdown(article['summary'])
                solara.Markdown("")
                solara.Markdown("")

                solara.Markdown("### Entities:")
                solara.Markdown("")
                # Nested loop for entities
                for ent in article['entities']:
                    solara.Markdown(f"Entity: {ent['text']},        Label: {ent['label']},      CF: {ent['confidence']}")
                solara.Markdown("")
                solara.Markdown("")
                solara.Markdown("### Top Entities:")
                solara.Markdown("")

                for ent in article['importance']:
                    solara.Markdown(f"Entity: {ent['name']}    |   Importance: {ent['score']:.4f}")

                graph_code = article.get('graph_html')
                
                if graph_code:
                    solara.Markdown("### Relationship Map:")
                    # Graph container
                    with solara.Div(style={  
                        "border-radius": "10px",
                        "height": "60vh",  
                        "min-height": "500px" 
                    }):
                        solara.HTML(
                            tag="iframe",
                            attributes={
                                "srcdoc": graph_code,
                                "style": "width: 100%; height: 100%; border: none; border-radius: 10px;"
                            }
                        )
                else:
                    solara.Info("Not enough entities to map relationships.")


@solara.component
def Page():
    solara.lab.theme.dark = True
    with solara.Column(
        style={
            "min-height": "100vh",
            "display": "flex",
            "justify-content": "center",
            "align-items": "center",
            "padding": "2rem",
            "gap": "1rem",
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
                    "padding": "2rem",
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