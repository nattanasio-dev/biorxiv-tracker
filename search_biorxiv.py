import requests
import csv
from datetime import datetime, timedelta
import time

# ==========================================
# 1. BIORXIV SEARCH ROBOT
# ==========================================
def search_biorxiv(headers, start_str, end_str):
    matches = []
    cursor = 0
    print(f"\n--- Searching bioRxiv from {start_str} to {end_str} ---")

    while True:
        url = f"https://api.biorxiv.org/details/biorxiv/{start_str}/{end_str}/{cursor}"
        print(f"Fetching bioRxiv page at cursor {cursor}...")
        
        success = False
        for attempt in range(5):
            try:
                response = requests.get(url, headers=headers, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    success = True
                    break
                else:
                    print(f"Attempt {attempt + 1} failed (status {response.status_code}). Retrying...")
                    time.sleep(5)
            except Exception as e:
                print(f"Attempt {attempt + 1} timed out. Retrying... (Error: {e})")
                time.sleep(5)
        
        if not success:
            print("bioRxiv server is too busy. Stopping bioRxiv search.")
            break
        
        collection = data.get('collection', [])
        if not collection:
            print("No more bioRxiv papers to check.")
            break

        for paper in collection:
            title = paper.get('title', '').lower()
            abstract = paper.get('abstract', '').lower()
            text_to_search = f"{title} {abstract}"

            has_car_t = "car-t" in text_to_search or "car t" in text_to_search
            has_ihc = "ihc" in text_to_search or "immunohistochemistry" in text_to_search

            if has_car_t and has_ihc:
                doi = paper.get('doi', '')
                link = f"https://doi.org/{doi}"
                # Notice the new 'bioRxiv' tag at the end!
                matches.append([paper.get('title', ''), link, 'bioRxiv'])
        
        cursor += 100
        time.sleep(2) 
        
    return matches

# ==========================================
# 2. PUBMED SEARCH ROBOT
# ==========================================
def search_pubmed(headers):
    matches = []
    print("\n--- Searching PubMed for the last 30 days ---")
    
    # We ask PubMed to do the keyword searching for us
    term = '("car-t" OR "car t") AND ("ihc" OR "immunohistochemistry")'
    search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={term}&reldate=30&datetype=pdat&retmode=json&retmax=100"
    
    print("Asking PubMed for matching article IDs...")
    try:
        search_response = requests.get(search_url, headers=headers, timeout=30)
        search_data = search_response.json()
        
        # PubMed returns a list of ID numbers for the matching papers
        id_list = search_data.get('esearchresult', {}).get('idlist', [])
        
        if not id_list:
            print("No matching papers found on PubMed.")
            return matches
            
        print(f"Found {len(id_list)} matching IDs on PubMed. Fetching titles...")
        
        # Now we ask PubMed for the actual titles and links for those specific IDs
        ids_string = ",".join(id_list)
        summary_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={ids_string}&retmode=json"
        
        summary_response = requests.get(summary_url, headers=headers, timeout=30)
        summary_data = summary_response.json()
        
        results = summary_data.get('result', {})
        
        # Match each title with its URL
        for article_id in id_list:
            article_info = results.get(article_id, {})
            title = article_info.get('title', '')
            link = f"https://pubmed.ncbi.nlm.nih.gov/{article_id}/"
            # Notice the new 'PubMed' tag at the end!
            matches.append([title, link, 'PubMed'])
            
    except Exception as e:
        print(f"Failed to reach PubMed. Error: {e}")
        
    return matches

# ==========================================
# 3. MAIN CONTROLLER (BRINGS IT ALL TOGETHER)
# ==========================================
def main():
    end_date = datetime.today()
    start_date = end_date - timedelta(days=30)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # Create an empty master list
    all_papers = []
    
    # Run the bioRxiv search and add to the master list
    biorxiv_papers = search_biorxiv(headers, start_str, end_str)
    all_papers.extend(biorxiv_papers)
    
    # Run the PubMed search and add to the master list
    pubmed_papers = search_pubmed(headers)
    all_papers.extend(pubmed_papers)

    # Save the master list to the CSV file with our NEW header
    with open('car_t_ihc_papers.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Title', 'URL', 'Source']) # Added the 'Source' column
        writer.writerows(all_papers) 

    print(f"\nSUCCESS! Found {len(biorxiv_papers)} from bioRxiv and {len(pubmed_papers)} from PubMed.")
    print(f"Total: {len(all_papers)} papers saved to CSV.")

if __name__ == "__main__":
    main()
