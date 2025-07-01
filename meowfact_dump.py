import requests
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import os

def fetch_fact(fact_id, lang_code, lang_name, date_added):
    """
    Fetch a single fact using the meowfacts API
    """
    try:
        url = f"https://meowfacts.herokuapp.com/?id={fact_id}&lang={lang_code}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        # Check if the data is valid
        if 'data' in data and data['data']:
            fact_text = data.get("data")[0]
            
            if fact_text and fact_text.strip() and fact_text.strip().lower() != 'none':
                # Establish fields for data analysis on meowfacts
                return {
                    'id': f"{lang_code}_{fact_id}",
                    'fact_id': fact_id,
                    'fact': fact_text.strip(),
                    'language': lang_name,
                    'date_added': date_added,
                    'character_count': len(fact_text.strip())
                }
    except Exception as e:
        print(f"Error fetching fact {fact_id}: {e}")
    
    return None

def collect_language_facts(lang_code, lang_name, date_added, max_workers=25):
    """
    Collect all facts for a given language
    """
    print(f"Collecting {lang_name} facts...")
    
    all_data = []
    fact_id = 0
    empty_batch = 0
    batch_size = 25
    
    while empty_batch < 1:
        # Create list of fact IDs for this batch
        batch_ids = list(range(fact_id, fact_id + batch_size))
        
        # Submit API requests concurrently, then collect results as they complete
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            pending_requests = {
                executor.submit(fetch_fact, fid, lang_code, lang_name, date_added): fid 
                for fid in batch_ids
            }
            
            batch_facts = []
            for request in as_completed(pending_requests):
                result = request.result()
                if result:
                    batch_facts.append(result)
        
        # If we got facts in this batch, add them and continue
        batch_start = fact_id
        batch_end = fact_id + batch_size - 1
        if batch_facts:
            all_data.extend(batch_facts)
            empty_batch = 0
            print(f"Found {len(batch_facts)} facts in batch {batch_start}-{batch_end}")
        else:
            empty_batch += 1
            print(f"No facts found in batch {batch_start}-{batch_end}")
        
        fact_id += batch_size
    
    print(f"Completed {lang_name}: {len(all_data)} facts")
    return all_data

def main():
    """
    Main entry point for meowfacts collection script
    """
    
    # Language mapping
    languages = {
        'eng': 'English',
        'esp': 'Spanish', 
        'ger': 'German',
        'rus': 'Russian',
        'por': 'Portuguese',
        'ita': 'Italian',
        'ces': 'Czech',
        'ben': 'Bengali',
        'fil': 'Filipino',
        'ukr': 'Ukrainian',
        'urd': 'Urdu',
        'zho': 'Chinese',
        'kor': 'Korean'
    }
    
    print("Starting meowfacts fact collection...")
    start_time = time.time()
    date_added = datetime.now().strftime('%Y-%m-%d')
    
    all_data = []
    
    # Collect data for each language
    for lang_code, lang_name in languages.items():
        language_facts = collect_language_facts(lang_code, lang_name, date_added)
        all_data.extend(language_facts)
    
    output_dir = "daily_meowfact_data"
    os.makedirs(output_dir, exist_ok = True)

    # Create output filename
    timestamp = datetime.now().strftime("%Y%m%d")
    filename = os.path.join(output_dir, f"meowfacts_complete_{timestamp}.json")
    
    # Save table to JSON
    print(f"Saving {len(all_data)} facts to {filename}...")
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    
    end_time = time.time()
    duration = round(end_time - start_time, 2)
    
    print(f"Collection complete. {len(all_data)} total facts saved to {filename}")
    print(f"Total time: {duration} seconds")


if __name__ == "__main__":
    main()