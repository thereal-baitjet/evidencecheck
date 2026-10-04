"""
PubMed Abstract Retrieval

Fetches abstracts from NCBI PubMed using E-utilities API.
Deduplicates by SHA256 hash and saves with metadata.
"""

import json
import hashlib
from typing import List, Dict
from datetime import datetime
import urllib.request
import urllib.error
import time

# NCBI E-utilities configuration
NCBI_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
NCBI_EMAIL = "research@example.com"  # Required by NCBI
NCBI_API_KEY = ""  # Optional; set for higher rate limits


def compute_hash(text: str) -> str:
    """Compute SHA256 hash of abstract text."""
    return hashlib.sha256(text.encode()).hexdigest()


def fetch_pubmed_articles(query: str, max_results: int = 100) -> List[Dict]:
    """
    Fetch articles from PubMed matching the query.

    Args:
        query: Search query (e.g., "exercise sleep adults")
        max_results: Maximum articles to retrieve

    Returns:
        List of article dictionaries with PMID, title, abstract
    """
    articles = []
    seen_hashes = set()

    # Step 1: Search for article IDs
    search_url = f"{NCBI_BASE_URL}/esearch.fcgi?db=pubmed&term={query.replace(' ', '+')}&retmax={max_results}&rettype=json&email={NCBI_EMAIL}"
    if NCBI_API_KEY:
        search_url += f"&api_key={NCBI_API_KEY}"

    try:
        print(f"Searching PubMed for: {query}")
        with urllib.request.urlopen(search_url, timeout=10) as response:
            search_result = json.loads(response.read().decode())

        pmids = search_result.get("esearchresult", {}).get("idlist", [])
        print(f"Found {len(pmids)} articles. Fetching abstracts...")

        if not pmids:
            print("No results found.")
            return []

        # Step 2: Fetch full records for each PMID
        for i, pmid in enumerate(pmids):
            if len(articles) >= max_results:
                break

            # Rate limiting: NCBI allows 3 requests/sec without API key, 10/sec with
            time.sleep(0.4)

            try:
                fetch_url = f"{NCBI_BASE_URL}/efetch.fcgi?db=pubmed&id={pmid}&rettype=json&email={NCBI_EMAIL}"
                if NCBI_API_KEY:
                    fetch_url += f"&api_key={NCBI_API_KEY}"

                with urllib.request.urlopen(fetch_url, timeout=10) as response:
                    record = json.loads(response.read().decode())

                article_data = record.get("result", {}).get(pmid, {})

                # Extract relevant fields
                title = article_data.get("title", "")
                abstract_text = article_data.get("abstract", "")

                # Skip if no abstract
                if not abstract_text:
                    continue

                # Deduplicate by hash
                abstract_hash = compute_hash(abstract_text)
                if abstract_hash in seen_hashes:
                    print(f"  {pmid}: Duplicate (skipped)")
                    continue

                seen_hashes.add(abstract_hash)

                articles.append({
                    "pmid": pmid,
                    "title": title,
                    "abstract": abstract_text,
                    "abstract_hash": abstract_hash,
                    "retrieval_date": datetime.utcnow().isoformat() + "Z"
                })

                print(f"  {pmid}: OK ({len(articles)}/{max_results})")

            except urllib.error.URLError as e:
                print(f"  {pmid}: Error - {e}")
                continue

        print(f"\nRetrieved {len(articles)} unique abstracts")
        return articles

    except urllib.error.URLError as e:
        print(f"Error connecting to NCBI: {e}")
        return []


def save_corpus(articles: List[Dict], filepath: str) -> None:
    """Save corpus to JSONL file."""
    with open(filepath, 'w') as f:
        for article in articles:
            f.write(json.dumps(article) + '\n')
    print(f"Saved {len(articles)} articles to {filepath}")


def split_dev_heldout(articles: List[Dict], dev_size: int = 10) -> tuple:
    """Split articles into development and held-out sets."""
    dev_set = articles[:dev_size]
    heldout_set = articles[dev_size:dev_size+20]
    return dev_set, heldout_set


if __name__ == "__main__":
    # Retrieve abstracts
    query = "exercise sleep adults"
    articles = fetch_pubmed_articles(query, max_results=30)

    if articles:
        # Save full corpus
        save_corpus(articles, "data/corpus/pubmed_abstracts.jsonl")

        # Split dev/heldout
        dev, heldout = split_dev_heldout(articles)
        save_corpus(dev, "data/corpus/dev_set.jsonl")
        save_corpus(heldout, "data/corpus/heldout_set.jsonl")

        print(f"\nDataset split:")
        print(f"  Development: {len(dev)} abstracts")
        print(f"  Held-out: {len(heldout)} abstracts")
        print(f"  Total: {len(articles)} abstracts")
