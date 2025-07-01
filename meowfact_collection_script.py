import requests
import json
from datetime import datetime
import time
import os
import hashlib

def get_language_info():
    """
    Get language information / fact counts from the /options endpoint
    """
    try:
        response = requests.get("https://meowfacts.herokuapp.com/options", timeout=10)
        data = response.json()
        
        languages = {}
        for lang_data in data.get('lang', []):

            iso_code = lang_data.get('iso_code', lang_data.get('full_code', ''))
            # Handle duplicate esp case
            if iso_code == 'esp':
                iso_code = lang_data.get('full_code', iso_code)
            if iso_code:
                languages[iso_code] = {
                    'language': lang_data.get('english_name', '').title(),
                    'country': lang_data.get('local_name', ''),
                    'full_code': lang_data.get('full_code', ''),
                    'fact_count': lang_data.get('fact_count', 0)
                }
        
        print(f"Found {len(languages)} languages with fact counts")
        return languages
        
    except Exception as e:
        print(f"Error fetching language info: {e}")

def generate_fact_id(fact_text):
    """
    Generate a unique ID for a fact based on its text content
    """
    # Create a hash of the fact text for consistent + unique IDs
    return hashlib.md5(fact_text.encode('utf-8')).hexdigest()[:18]

def collect_all_facts(lang_code, lang_info, date_added):
    """
    Fetch all facts for a language using the count parameter
    """
    try:
        fact_count = lang_info.get('fact_count', 1000)  # Default to 1000 facts if no fact_count

        url = f"https://meowfacts.herokuapp.com/?lang={lang_code}&count={fact_count}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        facts = []
        if 'data' in data and data['data']:
            for fact_text in data['data']:
                if fact_text and fact_text.strip() and fact_text.strip().lower() != 'none':

                    cleaned_text = fact_text.strip()
                    unique_id = generate_fact_id(cleaned_text)

                    # Establish fields for data analysis on meowfacts
                    facts.append({
                        'id_fact': unique_id,
                        'fact': cleaned_text,
                        'country': lang_info['country'].title(),
                        'language': lang_info['language'].title(),
                        'language_code': lang_code,
                        'date_added': date_added,
                        'word_count': len(cleaned_text.split()),
                        'character_count': len(cleaned_text)
                    })
        
        return facts
        
    except Exception as e:
        print(f"Error fetching facts for {lang_code}: {e}")
        return []
    
def collect_language_facts(lang_code, lang_info, date_added):
    """
    Collect all facts at once for a given language using count param
    """
    lang_name = lang_info['language']
    expected_count = lang_info.get('fact_count')
    
    # Collect all facts in one request
    all_data = collect_all_facts(lang_code, lang_info, date_added)
    
    print(f"Collected {len(all_data)} {lang_name}  facts")
    return all_data

def main():
    """
    Main entry point for meowfacts collection script
    """
    
    print("Starting meowfacts fact collection...")
    start_time = time.time()
    date_added = datetime.now().strftime('%Y-%m-%d')
    
    # Get language information from /options endpoint
    languages = get_language_info()
    
    all_data = []
    
    # Collect data for each language
    for lang_code, lang_info in languages.items():
        language_facts = collect_language_facts(lang_code, lang_info, date_added)
        all_data.extend(language_facts)
    
    # Set output directory 
    output_dir = "daily_meowfact_data"
    os.makedirs(output_dir, exist_ok = True)

    # Create output filename
    timestamp = datetime.now().strftime("%Y%m%d")
    filename = os.path.join(output_dir, f"meowfacts_data_{timestamp}.json")
    
    # Save output to file
    print(f"Saving {len(all_data)} facts to {filename}...")
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    
    end_time = time.time()
    duration = round(end_time - start_time, 2)
    
    print(f"Collection complete. {len(all_data)} total facts saved to {filename}")
    print(f"Total time: {duration} seconds")


if __name__ == "__main__":
    main()