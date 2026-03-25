import requests
import csv
from datetime import datetime, timedelta

def search_biorxiv():
    # Calculate dates for the last 30 days
    end_date = datetime.today()
    start_date = end_date - timedelta(days=30)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    # We will store matching papers here
    matches = []
    cursor = 0

    print(f"Searching bioRxiv from {start_str} to {end_str}...")

    # Loop through the bioRxiv API pages
    while True:
        url = f"https://api.biorxiv.org/details/biorxiv/{start_str}/{end_str}/{cursor}"
        response = requests.get(url)
        data = response.json()
        
        # Extract the list of papers
        collection = data.get('collection', [])
        
        # If the page is empty, we've reached the end
        if not collection:
            break

        # Check each paper for your keywords
        for paper in collection:
            title = paper.get('title', '').lower()
            abstract = paper.get('abstract', '').lower()
            text_to_search = f"{title} {abstract}"

            # Keyword Logic
            has_car_t = "car-t" in text_to_search or "car t" in text_to_search
            has_ihc = "ihc" in text_to_search or "immunohistochemistry" in text_to_search

            if has_car_t and has_ihc:
                doi = paper.get('doi', '')
                link = f"https://doi.org/{doi}"
                matches.append([paper.get('title', ''), link])
        
        # Move to the next page of 100 results
        cursor += 100

    # Save the results to a CSV file
    with open('car_t_ihc_papers.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Title', 'URL']) # Create headers
        writer.writerows(matches) # Add the papers

    print(f"Found {len(matches)} papers. Saved to CSV.")

if __name__ == "__main__":
    search_biorxiv()
