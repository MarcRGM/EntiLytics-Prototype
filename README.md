# EntiLytics

**News Information Management System with BiLSTM-Based Entity Extraction and Summarization**

> A web-based platform that automatically identifies, ranks, and visualizes named entities in news articles to support efficient news comprehension.

Live site: [https://entilytics.tech](https://entilytics.tech)

---

## What It Does

Reading news articles often means sorting through large amounts of text to find the people, organizations, and locations that actually matter to the story. EntiLytics automates this process.

Given a news article, the system will:

1. **Extract entities** (persons, organizations, locations, and miscellaneous) using a pretrained BiLSTM Named Entity Recognition model via the Flair NLP library
2. **Rank entities by importance** using a pretrained transformer model that weighs each entity's position in the text, mention frequency, and contextual relevance
3. **Map relationships** between entities by detecting which entities appear together within the same sentence, then visualizing the result as an interactive network graph
4. **Generate a summary** using extractive summarization, selecting the sentences most relevant to the top-ranked entities
5. **Store and annotate** articles and analysis results per user account, with personal notes saved to a database

---

## Tech Stack

| Layer                | Technology                                                                 |
| -------------------- | -------------------------------------------------------------------------- |
| UI Framework         | [Solara](https://solara.dev) (Python-based reactive web UI)                |
| NER Model            | [Flair](https://github.com/flairNLP/flair) (BiLSTM, trained on CoNLL-2003) |
| Importance Ranking   | Pretrained transformer model (Hugging Face Transformers)                   |
| Relationship Mapping | NetworkX + Pyvis                                                           |
| Database             | PostgreSQL (Azure Flexible Server)                                         |
| ORM                  | SQLAlchemy                                                                 |
| Authentication       | Google OAuth 2.0                                                           |
| Containerization     | Docker                                                                     |
| Container Registry   | Azure Container Registry                                                   |
| Hosting              | Azure App Service for Containers                                           |
| CI/CD                | GitHub Actions                                                             |
| Domain               | Custom domain with Azure Managed SSL Certificate                           |

---

## Project Structure

```
entilytics/
├── app.py
├── features/
│   ├── auth_handler.py
│   ├── database.py
│   ├── flair_ner.py
│   ├── entity_ranking_and_summarization.py
│   ├── relationship_mapping.py
│   └── rss_handler.py
├── public/
│   └── entilytics_icon.png
├── Dockerfile
├── requirements.txt
├── .github/
│   └── workflows/
│       └── main.yml
└── docs/
    ├── database_guide.ipynb
    └── deployment_guide.ipynb
```

---

## Running Locally

### Prerequisites

- Python 3.11 or higher
- A `.env` file in the project root with the following variables:

```env
DB_HOST=<your-postgresql-host>
DB_NAME=<your-database-name>
DB_USER=<your-database-username>
DB_PASS=<your-database-password>
GOOGLE_CLIENT_ID=<your-google-oauth-client-id>
GOOGLE_CLIENT_SECRET=<your-google-oauth-client-secret>
REDIRECT_URI=http://localhost:8080/
```

### Setup

```bash
# Clone the repository
git clone https://github.com/<your-username>/entilytics.git
cd entilytics

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate       # On Windows: venv\Scripts\activate

# Set the Python path (required for Solara to resolve imports)
export PYTHONPATH=.

# Install dependencies
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

# Run the application
solara run app.py --host 0.0.0.0 --port 8080
```

The application will be available at `http://localhost:8080`.

### Running with Docker

```bash
# Build the image
docker build -t entilytics .

# Run the container with environment variables
docker run -p 8080:8080 \
  -e DB_HOST=<your-host> \
  -e DB_NAME=<your-db> \
  -e DB_USER=<your-user> \
  -e DB_PASS=<your-pass> \
  -e GOOGLE_CLIENT_ID=<your-client-id> \
  -e GOOGLE_CLIENT_SECRET=<your-client-secret> \
  -e REDIRECT_URI=http://localhost:8080/ \
  entilytics
```

---

## Database Schema

The system uses a PostgreSQL database with the following core tables:

| Table             | Description                                               |
| ----------------- | --------------------------------------------------------- |
| `account`         | Registered users (Google OAuth)                           |
| `user_sessions`   | Active login sessions with expiry timestamps              |
| `article`         | Stored news article titles and content                    |
| `summary`         | NLP-generated extractive summaries per article            |
| `analysis_result` | Entity rankings, relationship graph HTML, and JSON output |
| `annotation`      | User-written notes linked to articles                     |

For full schema documentation, see [`docs/database_guide.ipynb`](docs/database_guide.ipynb).

---

## Deployment

The application is deployed to Azure App Service using GitHub Actions. Every push to the `main` branch triggers an automated build and deployment pipeline:

1. Docker image is built and tagged with the commit SHA
2. Image is pushed to Azure Container Registry
3. Azure App Service pulls the new image and restarts the container

For full deployment documentation, see [`docs/deployment_guide.ipynb`](docs/deployment_guide.ipynb).

---

## Data Sources

Entity extraction is powered by a BiLSTM model pretrained on the **CoNLL-2003** English newswire corpus, which covers four entity types: person, organization, location, and miscellaneous.

Test articles are collected from the following RSS feeds:

| Source         | Feed URL                                           |
| -------------- | -------------------------------------------------- |
| Manila Times   | `https://www.manilatimes.net/news/feed/`           |
| Mindanao Times | `https://www.mindanaotimes.com.ph/feed/`           |
| ProPublica     | `https://www.propublica.org/feeds/propublica/main` |

---

## Evaluation

The system is evaluated using the following methods:

- **F1 Score** for entity extraction accuracy, entity ranking correlation, relationship mapping, and summarization (ROUGE)
- **Black-box testing** for functional verification
- **ISO 25010** standard for reliability and usability assessment

---

## Academic Context

This system was developed as a thesis project for the degree of **Bachelor of Science in Computer Science** at **Tarlac State University**, College of Computer Studies.

---

## Known Limitations

- Analysis is limited to English-language articles only
- Some RSS feeds provide partial article content rather than full text, which may affect analysis quality
- Session persistence on page refresh is under active development
- The system does not perform fact-checking or verify the credibility of news sources
- Internet connectivity is required for pretrained model access and RSS feed retrieval
