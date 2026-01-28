from flair.data import Sentence
from flair.nn import Classifier

def identify_entities():
    # Load the standard English NER model 
    # 'ner-fast' for a smaller, faster BiLSTM model if preferred
    tagger = Classifier.load('ner')

    # Get user input
    user_input = input("Enter a sentence to identify entities: ")
    
    # Create a Flair Sentence object
    sentence = Sentence(user_input)

    # Predict entities
    tagger.predict(sentence)

    # Extract and print results
    print("\nIdentified Entities:")
    if not sentence.get_spans('ner'):
        print("No entities found.")
    else:
        for entity in sentence.get_spans('ner'):
            label = entity.get_label('ner')
            print(f"- {entity.text} [{label.value}] (Confidence: {label.score:.2f})")

if __name__ == "__main__":
    identify_entities()
