import networkx as nx
import nltk
from pyvis.network import Network
from itertools import combinations
from nltk.tokenize import sent_tokenize # Split articles by sentence rather than using split('.')
import uuid
import re # regex
import sys
import textwrap
sys.dont_write_bytecode = True
from bs4 import BeautifulSoup

# nltk requirement
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab', quiet=True)

def mapping(article, entities):
    # NetworkX Graph manages the logic and brain of the connections
    graph = nx.Graph()

    # BeautifulSoup strips tags and fix spacing
    # separator=" " let <p> tags get replaced by a space
    soup = BeautifulSoup(article, "html.parser")
    clean_text = soup.get_text(separator=" ")

    # Split into sentences
    sentences = sent_tokenize(clean_text)


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
                    # Append the new sentence to the evidence list
                    graph[u][v]['evidence'].append(clean_s)
                else:
                    # Create an edge and
                    # start a new list to store the sentence as evidence
                    # weight = how strong the connection is
                    # anything after u and v are custom attributes
                    graph.add_edge(u, v, weight=1, evidence=[clean_s])

    # Interactive Visualization using PyVis
    net = Network(height="100%", width="100%", bgcolor="white", font_color="#1C6EA4", notebook=True, cdn_resources='remote')
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
        net.add_node(entity, label=entity, title=entity, color="#FADA7A", shape="box", font={'size': 25, 'face': 'Roboto Mono', 'color': '#1C6EA4'})

    # Iterate through the NetworkX edges to build the Pyvis map
    for u, v, data in graph.edges(data=True): # True gives the custom attributes from graph
        # Wrap evidence text so it doesn't get cut off horizontally
        # Break lines every 10 characters and replace newlines with HTML <br>
        wrapped_evidence = []
        for s in data['evidence']:
            words = s.split()
            chunks = [" ".join(words[i:i+10]) for i in range(0, len(words), 10)]
            wrapped_evidence.append("\n".join(chunks))

        # title is an attribute Pyvis uses for the hover tooltip
        hover_text = "Found in:\n" + "\n".join(data['evidence'])
        
        # (Nodes to connect, line thickness, Shows when hovered, Color of the line)
        net.add_edge(u, v, 
                    value=2,
                    title=hover_text,      
                    color="#1C6EA4")

    # Generate the html string
    html_string = net.generate_html() 

    modal_html = """
    <div id="customModal" style="display:none; position:fixed; z-index:9999; left:0; top:0; width:100%; height:100%; background-color:rgba(0,0,0,0.7); font-family: 'Roboto Mono', monospace; backdrop-filter: blur(2px);">
      <div style="background-color:white; margin:8% auto; padding:30px; border-radius:2px; width:65%; max-height:75%; overflow-y:auto; position:relative; box-shadow: 0 20px 40px rgba(0,0,0,0.4); border-left: 5px solid #1C6EA4;">
        <span id="closeModal" style="position:absolute; right:25px; top:15px; cursor:pointer; font-size:30px; color:#1C6EA4; font-weight:bold;">&times;</span>
        
        <h3 id="modalTitle" style="color:#1C6EA4; border-bottom:1px solid #eee; padding-bottom:15px; margin-top:0; font-size: 1.4rem; letter-spacing: -0.5px;">Details</h3>
        
        <div id="modalContentWrapper" style="padding: 10px 0;">
            <pre id="modalContent" style="
                white-space: pre-wrap; 
                word-wrap: break-word; 
                font-size: 14px; 
                line-height: 1.8; 
                color: #333; 
                text-align: justify; 
                margin: 0;
                font-family: 'Roboto Mono', monospace;
            "></pre>
        </div>
      </div>
    </div>

    <script type="text/javascript">
      network.on("click", function (params) {
        if (params.nodes.length > 0 || params.edges.length > 0) {
          var content = "";
          var title = "";
          
          if (params.nodes.length > 0) {
            var nodeData = nodes.get(params.nodes[0]);
            title = "Entity: " + nodeData.label;
            content = "Detailed analysis for this entity is stored in the relationship connections. Click on the lines between nodes to see specific evidence.";
          } else if (params.edges.length > 0) {
            var edgeData = edges.get(params.edges[0]);
            var connection = nodes.get(edgeData.from).label + " & " + nodes.get(edgeData.to).label;
            title = "Relationship: " + connection;
            content = edgeData.title; 
          }
          
          document.getElementById('modalTitle').innerText = title;
          document.getElementById('modalContent').innerText = content;
          document.getElementById('customModal').style.display = "block";
        }
      });

      document.getElementById('closeModal').onclick = function() {
        document.getElementById('customModal').style.display = "none";
      }
      
      window.onclick = function(event) {
        if (event.target == document.getElementById('customModal')) {
          document.getElementById('customModal').style.display = "none";
        }
      }
    </script>
    """
    # Inject before </body>
    html_string = html_string.replace('</body>', modal_html + '</body>')

    # Give unique ID to each graphs
    unique_id = f"graph_{uuid.uuid4().hex[:8]}"
    html_string = re.sub(r'\bmynetwork\b', unique_id, html_string)

    # Remove white space at the top of the graph
    html_string = re.sub(r'<center>\s*<h1></h1>\s*</center>', '', html_string)
    # Replace the height in the CSS style block
    html_string = html_string.replace(
        'height: 500px;',
        'height: 100%;'
    )
    html_string = html_string.replace(
        '<body>',
        '<body style="margin: 0; padding: 0; height: 100%;">'
    )
    html_string = html_string.replace(
        '<html>',
        '<html style="height: 100%;">'
    )
    html_string = html_string.replace(
        '<div class="card" style="width: 100%">',
        '<div class="card" style="width: 100%; height: 100%;">'
    )

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
