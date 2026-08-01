# ⚽ Football Match Memory Enricher

An LLM-powered data enrichment pipeline that turns a personal, manually-kept record of football
matches attended into a structured, source-grounded archive — pulling public match reports,
extracting events (goals, red cards, managers, man of the match) with an LLM.

## What it does

You start with a spreadsheet of matches you've attended (date, teams, ground, score). The pipeline:

1. Cleans that spreadsheet into a single structured table (one row per match).
2. Generates search queries per match and retrieves public match report articles.
3. Feeds the article text to an LLM with a strict extraction prompt, using facts you already
   know (teams, score, goalscorers) to keep the model's job narrow.
4. Verifies every extracted fact against the source text before accepting it.
5. Exports the enriched result to a multi-sheet Excel workbook (match-level + event-level).

## Architecture

```
Raw match log (xlsx)
        │  data_preprocessing.py
        ▼
Clean match table (clean_matches.csv)   ← one row per match: teams, score, ground, goalscorers
        │  article_acquisition.ipynb
        ▼
Article text per match (articles.csv)   ← scraped from public match reports, linked by match_id
        │  rag_layer.py
        ▼
Extraction                              ← LLM extracts new facts, grounded against source text
        │
        ▼
match.json                              ← enriched record
        │  enriched_match_layer.ipynb
        ▼
enriched_matches.xlsx                   ← multi-sheet: match summaries + individual events
```

## Project status

| Stage | File(s) | Status |
|---|---|---|
| Data cleaning & normalisation | `src/data_preprocessing.py` | Implemented |
| Article acquisition | `src/article_acquisition.ipynb` | Implemented (SerpAPI) |
| Extraction (RAG layer) | `src/rag_layer.py` | Implemented  |
| Chunking + embeddings + vector retrieval | — | **Not yet implemented.** Currently the pipeline concatenates full article text into context rather than retrieving relevant passages — see [Known limitations](#known-limitations). |
| Excel export | `src/enriched_match_layer.ipynb` | Implemented |

## Repo structure

```
.
├── data/
│   ├── Live Football matches record raw.xlsx   # original manually-kept log
│   ├── clean_matches.csv                       # output of data_preprocessing.py
│   ├── articles.csv                             # output of article_acquisition.ipynb
│   ├── match.json                               # output of rag_layer.py
│   └── enriched_matches.xlsx                    # output of enriched_match_layer.ipynb
├── src/
│   ├── data_preprocessing.py
│   ├── article_acquisition.ipynb
│   ├── rag_layer.py
│   ├── rag_layer.ipynb        # exploratory notebook version
│   └── enriched_match_layer.ipynb
├── tests/
│   └── test_data_preprocessing.py
├── .env                        # not committed — see Setup
└── .gitignore
```

## Setup

**Requirements** (no `requirements.txt` yet — install directly):

```bash
pip install pandas openpyxl python-dotenv requests beautifulsoup4 trafilatura google-search-results pytest
```

**Environment variables** — create a `.env` file in the project root (already gitignored):

```
SERPAPI_KEY=your_serpapi_key
OPENROUTER_API_KEY=your_openrouter_key
```

- `SERPAPI_KEY` — used by the article acquisition layer to search for match report URLs.
- `OPENROUTER_API_KEY` — used by the extraction layer to call the LLM via OpenRouter.

## Running the pipeline

Run the stages in order — each one reads the previous stage's output:

1. **Clean the raw match log**
   ```bash
   python src/data_preprocessing.py
   ```
   Produces `data/clean_matches.csv`.

2. **Acquire articles** — run `src/article_acquisition.ipynb`. Start with a small sample
   (5–10 matches) before scaling up; it hits SerpAPI and scrapes live pages.
   Produces `data/articles.csv`.

3. **Extract & verify**
   ```bash
   cd src && python rag_layer.py
   ```
   Produces `data/match.json` and `data/extraction_audit.json`. The script prints a summary
   of facts kept vs. dropped and an estimated hallucination rate for the run.

4. **Export to Excel** — run `src/enriched_match_layer.ipynb`.
   Produces `data/enriched_matches.xlsx` (a `matches` sheet and an `events` sheet).

5. **Tests**
   ```bash
   pytest tests/
   ```

## Known limitations

- **Chunking not implemented.** Full article text is concatenated per match rather than chunked,
  embedded, and retrieved by relevance. This works while articles are short, but risks exceeding
  context limits and diluting the model's attention as article count/length grows — chunking +
  embedding retrieval (as originally scoped) is the natural next step.
- **Article acquisition has no error handling** for failed requests, paywalls, or timeouts, and
  the trusted-source domain list is small and hardcoded.
- **Unit testing only implemented in preprocessing** - Needs to be extended to other phases.
- **No formal labelled evaluation set yet** — hallucination rate is currently self-reported, not validated against independently labelled matches.

## Roadmap

- [ ] Add chunking + embeddings + relevance-filtered retrieval
- [ ] Manually label subset of matches as ground truth and build a real precision/recall/hallucination
      evaluation script
- [ ] Add error handling, retries and unit testing to article acquisition
- [ ] Add YouTube highlights link
- [ ] Expand filter for trusted sources
- [ ] Increase quantity of extracted data
- [ ] Exploit evidence extraction for LLM validation and auditing
- [ ] Implement Power Automate for when a match gets added to base Spreadsheet 
