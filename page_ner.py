import solara
from flair.data import Sentence
from flair.nn import Classifier

text = solara.reactive("")
continuous_update = solara.reactive(True)
entities = solara.reactive("")

def identify_entities(input):
    # Load the standard English NER model 
    # 'ner-fast' for a smaller, faster BiLSTM model if preferred
    tagger = Classifier.load('ner')

    # Create a Flair Sentence object
    sentence = Sentence(input)

    # Predict entities
    tagger.predict(sentence)

    extract = []

    # Extract and print results
    print("\nIdentified Entities:")
    if not sentence.get_spans('ner'):
        print("No entities found.")
    else:
        for entity in sentence.get_spans('ner'):
            extract.append(f"{entity.text} [{entity.get_label('ner').value}]")

    return extract

def clearText():
    text.set("")
    entities.set("")

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
                solara.InputText("Enter some text", value=text, continuous_update=continuous_update.value)
                with solara.Row():
                    solara.Button("Enter", on_click=lambda: entities.set(identify_entities(text.value)), color="#75B06F",)
                    solara.Button("Clear", on_click=lambda: clearText(), color="#CD5656",)
                solara.Markdown(f"Entities found: {entities.value}")