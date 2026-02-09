import networkx as nx
import nltk
from pyvis.network import Network
from itertools import combinations
from nltk.tokenize import sent_tokenize # Split articles by sentence rather than using split('.')
import uuid

# nltk requirement
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab', quiet=True)

def mapping(article, entities):
    # NetworkX Graph manages the logic and brain of the connections
    graph = nx.Graph()

    # Split by sentences to perform sentence-level analysis
    # nltk handles periods in abbreviations (e.g., Dr. or Inc.)
    sentences = sent_tokenize(article)
    
    for sentence in sentences:
        clean_s = sentence.strip() # Remove extra spaces/newlines
        if not clean_s: continue   # Skip empty strings
        
        # Add the entities that are found from the current sentence
        found = [e for e in entities if e.lower() in clean_s.lower()]
        
        # Create connection if 2 or more entities appear
        if len(found) > 1:
            # combinations() pairs everyone (e.g., A-B, B-C, A-C)
            # sorted() prevent duplicates (e.g., A-B and B-A)
            for pair in combinations(sorted(found), 2):
                u, v = pair # standard placeholder names for nodes
                
                if graph.has_edge(u, v):
                    # Increase the weight if it's already linked
                    # and append the new sentence to the evidence list
                    graph[u][v]['weight'] += 1
                    graph[u][v]['evidence'].append(clean_s)
                else:
                    # Create an edge and
                    # start a new list to store the sentence as evidence
                    # weight = how strong the connection is
                    # anything after u and v are custom attributes
                    graph.add_edge(u, v, weight=1, evidence=[clean_s])

    # Interactive Visualization using PyVis
    net = Network(height="500px", width="100%", bgcolor="#FADA7A", font_color="#1C6EA4", notebook=True)
    # net.from_nx(graph) automatic creation with default style 

    # Force the nodes to spread out neatly
    net.barnes_hut(
        gravity=-8000, # Pushes nodes away from each other
        central_gravity=0.3, # Keeps the cluster centered
        spring_length=250 # Controls the length of the lines
    )

    # Add nodes and the edge connecting them
    # (ID, Visible text, Shows when hovered, Color of the circle)
    for entity in entities:
        net.add_node(entity, label=entity, title=entity, color="white", shape="circle")

    # Iterate through the NetworkX edges to build the Pyvis map
    for u, v, data in graph.edges(data=True): # True gives the custom attributes from graph
        # title is an attribute Pyvis uses for the hover tooltip
        hover_text = "Found in:\n" + "\n".join(data['evidence'])
        
        # (Nodes to connect, line thickness, Shows when hovered, Color of the line)
        net.add_edge(u, v, 
                    value=data['weight'],
                    title=hover_text,      
                    color="#1C6EA4")

    # Generate the html string
    html_string = net.generate_html() 

    # Give unique ID to each graphs
    unique_id = f"graph_{uuid.uuid4().hex[:8]}"
    html_string = html_string.replace('id="mynetwork"', f'id="{unique_id}"')
    html_string = html_string.replace("id='mynetwork'", f"id='{unique_id}'")
    html_string = html_string.replace("getElementById('mynetwork')", f"getElementById('{unique_id}')")
    html_string = html_string.replace('getElementById("mynetwork")', f'getElementById("{unique_id}")')
    net.save_graph(f"graph_{unique_id}.html")

    return html_string

# Simple demo to run the module directly
if __name__ == "__main__":
    article = (
        "Apple was founded by Steve Jobs and Steve Wozniak. "
        "Microsoft was co-founded by Bill Gates and Paul Allen. "
        "Apple and Microsoft compete in the PC market."
    )
    entities = [
        "Apple", "Steve Jobs", "Steve Wozniak",
        "Microsoft", "Bill Gates", "Paul Allen"
    ]
    mapping(article, entities)
