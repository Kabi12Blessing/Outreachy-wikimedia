import csv
import requests

results = []

with open('Task 2 - Intern.csv', 'r') as file:
    reader = csv.reader(file)
    # skip the header row
    next(reader)
    for row in reader:
        url = row[0].strip()
        if url:
            try:
                response = requests.head(url, timeout=(5, 10))
                line = f"({response.status_code}) {url}"
                print(line)
                results.append(line)
            except requests.exceptions.Timeout:
                line = f"(TIMEOUT) {url}"
                print(line)
                results.append(line)
            except requests.exceptions.ConnectionError:
                line = f"(CONNECTION ERROR) {url}"
                print(line)
                results.append(line)
            except Exception as e:
                line = f"(ERROR) {url}"
                print(line)
                results.append(line)

with open('task2_results.txt', 'w') as output_file:
    output_file.write('\n'.join(results))

print("\nDone! Results saved to task2_results.txt")
