# Addressing the Lusophone Technological Wishlist Proposals

Outreachy Round 32 - Wikimedia Foundation
Contributor: Eileen Blessing Mbong Kabi (EileenBlessing)
GitHub: https://github.com/Kabi12Blessing

## About This Project

This repository contains my contributions for the Outreachy Round 32 application to the Wikimedia Foundation project: Addressing the Lusophone Technological Wishlist Proposals.

The project aims to implement two wishes from the 2025 Lusophone Technological Wishlist:

- Wish 3 - Automatic duplicate reference detection in the Visual Editor
- Wish 8 - Wikidata scoring support for WikiScore

## Repository Contents
```
Outreachy-wikimedia/
  Task 1 - Intern.html      # Task 1 submission
  Task 2 - Intern.csv       # CSV input file for Task 2
  task2.py                  # Task 2 submission
  task2_results.txt         # Output from running task2.py
  prototype/
    refchecker.html         # Visual demo of duplicate reference detector
    refchecker.py           # Python version of the same logic
  README.md
```

## Task 1 - Intern.html

**Objective of the task:**

Create a JavaScript script to manipulate a JSON object and print it in a human legible format.

**My approach:**

The input data had dates stored as strings in YYYY-MM-DD format. To get a readable date I split each date string on the hyphen to get the year, month and day separately.

The month came out as a number so I created an array of month names and used the month number minus one as the index to look up the correct name. I subtracted one because the array is zero-indexed but months start at 1.

I used `parseInt()` on the day to convert it from a string to a number before inserting it into the sentence.

I then built the formatted sentence for each article using a template literal and displayed everything in the `#results` element using `innerText`. I added comments throughout the code explaining each step.

**How to run:**

Clone the repository and open the file in any browser:
```bash
git clone https://github.com/Kabi12Blessing/Outreachy-wikimedia.git
cd Outreachy-wikimedia
open "Task 1 - Intern.html"
```

## Task 2 - task2.py

**Objective of the task:**

Create a Python script to get and print the status code of the response of a list of URLs from a .csv file.

**My approach:**

The CSV file had a header row with the column name "urls" so I used `next(reader)` to skip it before looping through the actual URLs.

I used the `requests` library with a split timeout of `(5, 10)` — 5 seconds to connect and 10 seconds to receive the response. I chose a split timeout rather than a single value because a server can accept a connection quickly but still take a long time to actually respond, and a single timeout value would not catch that difference.

I handled three error cases separately rather than catching everything in one block. Timeout and connection errors are common when checking URLs at scale so they deserved their own clear labels in the output. A general exception catch handled anything else unexpected.

I also saved all results to `task2_results.txt` after the script finishes. The task only asked to print the results but saving them means you can review everything later without re-running the script.

**How to run:**

Clone the repository then run:
```bash
git clone https://github.com/Kabi12Blessing/Outreachy-wikimedia.git
cd Outreachy-wikimedia
pip install requests
python task2.py
```

## Prototype - prototype/

**Objective:**

Build a working demonstration of the core logic behind Wish 3 — detecting duplicate references in Wikipedia articles.

**Background:**

Wish 3 from the Lusophone Technological Wishlist asks for a feature in the Visual Editor that detects when an editor is about to add a reference that already exists in the article. When editing a long Wikipedia article it is genuinely difficult to know whether a URL, DOI or ISBN has already been cited somewhere earlier in the same article. Editors accidentally create duplicates all the time, especially on articles with hundreds of references.

**My approach:**

The first problem to solve was that two references can cite the same source but write it differently. For example `http://www.bbc.com/news/` and `https://bbc.com/news` are the same URL but a simple string comparison would say they are different. So before comparing anything I normalize each identifier — strip the protocol, www prefix and trailing slash from URLs, strip the doi.org prefix from DOIs, and strip hyphens and spaces from ISBNs. After normalization two references citing the same source will always produce the same string regardless of how they wrote it.

I handled URLs, DOIs and ISBNs separately in the extraction because they appear in different formats inside wikitext. A URL appears as a plain link, a DOI can appear as `doi=`, `doi:` or `https://doi.org/`, and an ISBN appears as `isbn=` inside a template. Each one needed its own regex pattern to find it reliably.

For the detection itself I built a map of normalized identifier to the list of references using it. After processing all references, any identifier with more than one entry in its list is a duplicate. This way I only go through the references once rather than comparing every reference against every other reference.

The same logic is implemented in both Python (`refchecker.py`) and JavaScript (`refchecker.html`) to demonstrate proficiency in both languages the project requires.

**The HTML demo has two tabs:**

- Article Scanner — fetches any real Wikipedia article via the MediaWiki API and reports all duplicate reference groups found
- Editor Simulation — simulates what the experience would look like inside the Visual Editor. When you load an article, click Cite and enter a URL that already exists in the article, the duplicate alert appears giving you the option to reuse the existing reference or add a new one anyway

**How to run the Python script:**

Clone the repository and run:
```bash
git clone https://github.com/Kabi12Blessing/Outreachy-wikimedia.git
cd Outreachy-wikimedia/prototype
pip install requests
python refchecker.py
```

**How to open the HTML demo:**

Clone the repository and open the file in any browser:
```bash
git clone https://github.com/Kabi12Blessing/Outreachy-wikimedia.git
cd Outreachy-wikimedia/prototype
open refchecker.html
```

Or download `prototype/refchecker.html` and open it directly in your browser. No server or installation needed.

## Demo Video

A walkthrough of the prototype showing the duplicate reference detector working on real Wikipedia articles.

[Watch the demo video](#)

## Microtasks

- T418285 - https://phabricator.wikimedia.org/T418285
- T418286 - https://phabricator.wikimedia.org/T418286

## Proposal

- https://phabricator.wikimedia.org/T422301

## Contact

- Outreachy username: EileenBlessing
- Wikimedia username: EileenBlessing
