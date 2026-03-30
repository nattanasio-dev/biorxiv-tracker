import requests
import csv
from datetime import datetime, timedelta
import time

def search_biorxiv():
    # Calculate dates for the last 30 days
    end_date = datetime.today()
    start_date = end_date - timedelta(days=30)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    matches = []
    cursor = 0

    print(f"Searching bioRxiv from {start_str} to {end_str}...")

    # A "fake ID" that tells the website we are a normal web browser, not a bot
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # Loop through the bioRxiv API pages
    while True:
        url = f"https://api.biorxiv.org/details/biorxiv/{start_str}/{end_str}/{cursor}"
        print(f"Fetching page at cursor {cursor}...")
        
        # --- NEW RETRY LOGIC ---
        success = False
        for attempt in range(5): # The robot will try up to 5 times per page
            try:
                # We give it a generous 30-second timeout
                response = requests.get(url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    success = True
                    break # It worked! Break out of the retry loop and move on
                else:
                    print(f"Attempt {attempt + 1} failed with status {response.status_code}. Retrying in 5 seconds...")
                    time.sleep(5)
                    
            except Exception as e:
                # If it times out, it prints this and tries again
                print(f"Attempt {attempt + 1} timed out. Retrying in 5 seconds... (Error: {e})")
                time.sleep(5)
        
        # If it failed 5 times in a row, we stop the whole search to be safe
        if not success:
            print("Failed after 5 attempts. The server is too busy. Stopping here to save what we found so far.")
            break
        # -----------------------
        
        # Extract the list of papers
        collection = data.get('collection', [])
        
        # If the page is empty, we've reached the end
        if not collection:
            print("No more papers to check.")
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
        
        # Pause for 2 seconds between pages to be extra polite to the server
        time.sleep(2) 

    # Always save a CSV (even if empty)
    with open('car_t_ihc_papers.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Title', 'URL']) # Create headers
        writer.writerows(matches) # Add the papers

    print(f"Found {len(matches)} matching papers. Saved to CSV.")

if __name__ == "__main__":
    search_biorxiv()
