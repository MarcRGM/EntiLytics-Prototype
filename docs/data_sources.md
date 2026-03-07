# Data Sources

This document describes all data sources used in EntiLytics for model training, system testing, and live article input. It is intended to support reproducibility and to clarify the provenance of all data used in development and evaluation.

---

## 1. Pretrained Model: CoNLL-2003 Corpus

**Used for:** BiLSTM Named Entity Recognition (NER) model training

The entity extraction component uses a BiLSTM NER model pretrained on the **CoNLL-2003** English newswire corpus. This corpus is a standard benchmark dataset for named entity recognition tasks and is widely used in NLP research.

| Property | Value |
|---|---|
| Corpus Name | CoNLL-2003 |
| Language | English |
| Domain | Newswire (Reuters) |
| Source URL | `https://www.clips.uantwerpen.be/conll2003/ner/` |
| Annotation Format | BIO tagging (Begin, Inside, Outside) |
| Entity Types | Person (`PER`), Organization (`ORG`), Location (`LOC`), Miscellaneous (`MISC`) |
| Accessed Via | Flair NLP library (pretrained model) |

The model is not trained from scratch in this project. The pretrained Flair BiLSTM NER model is loaded directly from the Flair model hub. The CoNLL-2003 corpus is referenced here because it is the dataset on which the pretrained model was trained, which determines the entity types the system can recognize and the domains where it performs reliably.

**Relevance to this project:** CoNLL-2003 is sourced from English newswire text, making it well-suited for news-domain entity detection. The four entity types it covers (person, organization, location, miscellaneous) are the same four types used throughout EntiLytics for extraction, ranking, and evaluation.

---

## 2. RSS Feed Sources

**Used for:** Article collection during development, testing, and live system use

Users can input news articles either by pasting text manually or by providing an RSS feed URL. During development and evaluation, the following three RSS feeds were used as the primary sources of test articles. All feeds are publicly accessible, updated regularly, and return articles in standard XML format.

Each RSS entry contains the following fields:

- `title` — article headline
- `description` — article body or excerpt
- `pubDate` — publication date and time
- `link` — URL to the full article on the source website

### 2.1 Manila Times

| Property | Value |
|---|---|
| Publication | Manila Times |
| Coverage | Philippine national news |
| Feed URL | `https://www.manilatimes.net/news/feed/` |
| Format | XML (RSS 2.0) |
| Articles per update | Approximately 15 to 20 |
| Language | English |

The Manila Times feed was selected for its broad coverage of Philippine national news, including politics, business, and society. It provides consistent English-language content relevant to the target user base of Filipino students, researchers, and professionals.

### 2.2 Mindanao Times

| Property | Value |
|---|---|
| Publication | Mindanao Times |
| Coverage | Mindanao regional news |
| Feed URL | `https://www.mindanaotimes.com.ph/feed/` |
| Format | XML (RSS 2.0) |
| Articles per update | Approximately 10 to 20 |
| Language | English |

The Mindanao Times feed provides regional Philippine news. Including this source alongside the Manila Times allows the system to be tested on articles with a narrower geographic focus and a different writing style, which helps assess the model's generalizability across local news domains.

### 2.3 ProPublica

| Property | Value |
|---|---|
| Publication | ProPublica |
| Coverage | Investigative journalism (United States and international) |
| Feed URL | `https://www.propublica.org/feeds/propublica/main` |
| Format | XML (RSS 2.0) |
| Articles per update | Approximately 10 to 20 |
| Language | English |

ProPublica was included to provide international context and a different genre of English-language journalism. Investigative articles tend to be longer, involve more named entities, and have denser entity relationships than standard news reports. Testing on ProPublica articles helps evaluate system performance on more complex inputs.

---

## 3. Evaluation Dataset

**Used for:** Baseline accuracy testing of the NER model

For formal evaluation of entity extraction accuracy, the system is tested in two ways:

**Baseline testing** uses the standard CoNLL-2003 test split, which provides pre-labeled ground truth annotations. This allows F1 score calculation against a known benchmark and supports comparison with published results from other NER systems.

**Real-world testing** uses a manually labeled sample of articles collected from the three RSS feeds listed above. Entities in these articles are annotated by hand to create ground truth labels, which are then compared against the system's output. This tests how well the pretrained model transfers to the specific news domains used by the system.

The combination of both evaluation approaches supports both reliable baseline comparison and practical, domain-specific performance assessment.

---

## 4. Notes on Data Limitations

The following limitations apply to the data sources used in this project and should be considered when interpreting evaluation results.

**Partial RSS content:** Some RSS feeds return only a short excerpt of each article rather than the full text. When this occurs, the system analyzes only the excerpt available, which may reduce the completeness of entity extraction and relationship mapping.

**Feed availability:** RSS feeds are maintained by third-party publishers. If a feed becomes unavailable or changes its structure, article retrieval will fail until the feed URL is updated by the user.

**Domain coverage:** The CoNLL-2003 pretrained model performs reliably on standard English newswire text. Its accuracy may be lower on highly technical, specialized, or non-standard news content outside the domains represented in its training data.

**No fact-checking:** The system does not verify the factual accuracy or source credibility of any article. Users are responsible for assessing the reliability of their input sources independently.
