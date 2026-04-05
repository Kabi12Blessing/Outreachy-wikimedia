"""
refchecker.py - Wikipedia Duplicate Reference Checker

Author: Eileen Blessing Mbong Kabi (EileenBlessing)
GitHub: https://github.com/Kabi12Blessing/
Project: Outreachy Round 32 - Wikimedia Foundation
Wish: Lusophone Technological Wishlist - Wish 3

PROTOTYPE NOTICE:
This script demonstrates the core duplicate detection logic for Wish 3.
It is not a production tool. The actual internship implementation would
integrate directly into the Visual Editor codebase following MediaWiki
development standards.

How it works:
  1. Fetch article wikitext from the public Wikipedia API
  2. Extract every <ref>...</ref> block from the wikitext
  3. Normalize identifiers (URLs, DOIs, ISBNs) so two refs citing
     the same source always produce the same string regardless of
     how they wrote it (http vs https, hyphens in ISBNs, etc)
  4. Build a map of identifier -> refs using it, then flag any
     identifier that appears in more than one ref

No user data is collected or stored.
All requests go to the public Wikipedia API.
"""

import requests
import re
from collections import defaultdict


def fetch_article(title):
    """
    Fetches the raw wikitext of a Wikipedia article by title.
    Uses the public MediaWiki parse API.
    Returns the wikitext string.
    """
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "parse",
        "page": title,
        "prop": "wikitext",   # we only need the raw source, not rendered HTML
        "format": "json",
        "redirects": True     # follow redirects e.g. "COVID-19" -> "Covid 19"
    }
    # Wikipedia API policy requires a descriptive User-Agent for all requests
    headers = {
        "User-Agent": "EileenBlessing/RefCheckPrototype/1.0 (https://github.com/Kabi12Blessing/)"
    }

    response = requests.get(url, params=params, headers=headers, timeout=10)

    if response.status_code != 200:
        raise Exception(f"API request failed with status code: {response.status_code}")

    if not response.text:
        raise Exception("API returned an empty response")

    data = response.json()

    if "error" in data:
        raise Exception(f"Article not found: {data['error']['info']}")

    return data["parse"]["wikitext"]["*"]


def extract_references(wikitext):
    """
    Extracts every full <ref>...</ref> definition from the wikitext.
    Self-closing tags like <ref name="foo" /> are skipped — they
    reuse an existing ref and have no content to check.

    Returns a list of dicts with keys: index, name, content.
    """
    # group 1 = name attribute (optional), group 2 = ref content
    pattern = r'<ref(?:\s+name\s*=\s*["\']?([^"\'/>]+)["\']?)?\s*>([\s\S]*?)<\/ref>'
    matches = re.finditer(pattern, wikitext, re.IGNORECASE)

    refs = []
    for i, match in enumerate(matches, 1):
        refs.append({
            "index": i,
            "name": match.group(1).strip() if match.group(1) else None,
            "content": match.group(2).strip()
        })

    return refs


def normalize_url(url):
    """
    Strips protocol, www prefix and trailing slash so two URLs
    pointing to the same page compare as equal strings.
    e.g. http://www.bbc.com/news/ -> bbc.com/news
    """
    url = url.strip().lower()
    url = re.sub(r'^https?://', '', url)  # drop http:// or https://
    url = re.sub(r'^www\.', '', url)       # drop www prefix
    url = url.rstrip('/')                  # drop trailing slash
    return url


def normalize_doi(doi):
    """
    Strips the doi.org URL prefix and doi: prefix so all DOI
    formats compare equal.
    e.g. https://doi.org/10.1000/xyz -> 10.1000/xyz
    """
    doi = doi.strip().lower()
    doi = re.sub(r'^https?://doi\.org/', '', doi)  # URL form -> bare DOI
    doi = re.sub(r'^doi:', '', doi)                 # drop doi: prefix
    return doi


def normalize_isbn(isbn):
    """
    Strips hyphens and spaces so ISBN-10 and ISBN-13 with or
    without hyphens compare equal.
    e.g. 978-3-16-148410-0 -> 9783161484100
    """
    return re.sub(r'[\s\-]', '', isbn).upper()


def extract_identifiers(ref_content):
    """
    Pulls every URL, DOI and ISBN out of a single ref string.
    We run this per ref rather than across the whole article
    because we need to know which ref each identifier came from
    when we report duplicates.

    Returns a list of dicts with keys: type, raw, normalized.
    """
    identifiers = []

    # URLs: stop regex at whitespace and common wikitext delimiters
    # to avoid pulling in surrounding markup like |title= etc
    urls = re.findall(r'https?://[^\s|<>"\'\]]+', ref_content)
    for url in urls:
        normalized = normalize_url(url)
        if len(normalized) > 5:
            identifiers.append({
                "type": "URL",
                "raw": url,
                "normalized": normalized
            })

    # DOIs appear in three formats in wikitext:
    #   |doi=10.1000/xyz   doi:10.1000/xyz   https://doi.org/10.1000/xyz
    dois = re.findall(
        r'(?:doi\s*=\s*|doi:|https?://doi\.org/)([^\s|<>"\'\]]+)',
        ref_content,
        re.IGNORECASE
    )
    for doi in dois:
        normalized = normalize_doi(doi)
        if len(normalized) > 3:
            identifiers.append({
                "type": "DOI",
                "raw": doi,
                "normalized": "doi:" + normalized
            })

    # ISBNs only appear in wikitext template param format: |isbn=978-...
    # length check (9-17 chars) covers ISBN-10 and ISBN-13 with hyphens
    isbns = re.findall(r'isbn\s*=\s*([0-9\-X ]{9,17})', ref_content, re.IGNORECASE)
    for isbn in isbns:
        normalized = normalize_isbn(isbn)
        if len(normalized) >= 10:
            identifiers.append({
                "type": "ISBN",
                "raw": isbn,
                "normalized": "isbn:" + normalized
            })

    return identifiers


def detect_duplicates(refs):
    """
    Builds a map of normalized identifier -> list of refs using it.
    A ref is only added once per identifier even if the same URL
    appears twice in the same ref string.

    Returns only entries where more than one ref uses the identifier.
    """
    identifier_map = defaultdict(list)

    for ref in refs:
        identifiers = extract_identifiers(ref["content"])
        for identifier in identifiers:
            # guard against the same ref being added twice for one identifier
            existing_indices = [r["index"] for r in identifier_map[identifier["normalized"]]]
            if ref["index"] not in existing_indices:
                identifier_map[identifier["normalized"]].append({
                    "index": ref["index"],
                    "name": ref["name"],
                    "content": ref["content"],
                    "type": identifier["type"],
                    "raw": identifier["raw"]
                })

    # keep only identifiers that appear in more than one ref
    duplicates = {
        key: value
        for key, value in identifier_map.items()
        if len(value) > 1
    }

    return duplicates


def print_results(title, refs, duplicates):
    """
    Prints the scan results to the terminal in a readable format.
    Separated from detect_duplicates() to keep detection logic
    independent of how results are displayed.
    """
    print(f"\n{'='*60}")
    print(f"  DUPLICATE REFERENCE CHECKER")
    print(f"  Article: {title}")
    print(f"{'='*60}")
    print(f"  Total references found : {len(refs)}")
    print(f"  Duplicate groups found : {len(duplicates)}")
    print(f"{'='*60}\n")

    if not duplicates:
        print("  No duplicate references found. Article looks clean.\n")
        return

    for identifier, dup_refs in duplicates.items():
        print(f"  DUPLICATE [{dup_refs[0]['type']}]")
        print(f"  Identifier : {identifier}")
        print(f"  Found in   : {len(dup_refs)} references")
        print()
        for ref in dup_refs:
            name_info = f" (name: {ref['name']})" if ref['name'] else ""
            print(f"    Reference #{ref['index']}{name_info}")
            # truncate long refs so terminal output stays readable
            content_preview = ref['content'][:150]
            if len(ref['content']) > 150:
                content_preview += '...'
            print(f"    {content_preview}")
            print()
        print(f"  {'-'*56}\n")


def main():
    """
    Entry point. Reads an article title from the user, runs the
    full pipeline and prints results.
    """
    print("\nWikipedia Duplicate Reference Checker")
    print("Built by Eileen Blessing Mbong Kabi (EileenBlessing)")
    print("Outreachy Round 32 - Wikimedia Foundation\n")

    title = input("Enter Wikipedia article title: ").strip()

    if not title:
        print("Please enter an article title.")
        return

    print(f"\nFetching article: {title}...")

    try:
        wikitext = fetch_article(title)
        print("Article fetched successfully!")

        print("Extracting references...")
        refs = extract_references(wikitext)

        if not refs:
            print("No references found in this article. Try another title.")
            return

        print(f"Found {len(refs)} references.")

        print("Detecting duplicates...")
        duplicates = detect_duplicates(refs)

        print_results(title, refs, duplicates)

    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()