import pandas as pd
from openai import OpenAI
from tqdm import tqdm  # For progress bars
import time
import logging


# --- Configuration ---
logging.basicConfig(filename='translation.log', level=logging.INFO)

client = OpenAI(api_key="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")
INPUT_CSV = 'CMF_alumni_survey_spanish1.csv'
OUTPUT_CSV = 'CMF_alumni_survey_english.csv'


#Translation Testing
'''
response = client.chat.completions.create(
    model= "gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "Translate the following Spanish text to English while preserving numbers, dates, and proper nouns. Return only the translation."},
        {"role": "user", "content": "Sí, tengo un negocio."}
    ],
    temperature=0.1
)
translated_text = response.choices[0].message.content
print(translated_text)
'''
# Translation Function with Caching 
translation_cache = {}

def translate_to_english(text, context="text"):
    """Translate Spanish text to English using OpenAI once, with caching."""
    if pd.isna(text) or str(text).strip() == "":
        return text
    
    if text in translation_cache:
        return translation_cache[text]
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Translate Spanish to English. Preserve numbers/dates. Return ONLY the translation."},
                {"role": "user", "content": text}
            ],
            temperature=0.1
        )
        translated = response.choices[0].message.content.strip()
        translation_cache[text] = translated
        time.sleep(0.2)  # Avoid rate limits    
        logging.info(f"Translated: '{text}' → '{translated}'")
        return translated
    except Exception as e:
        print(f"Failed to translate: '{text[:50]}...'. Error: {e}")
        return text  # Return original if translation fails

#Clean Headers
def clean_header(header):
    """Extracts the actual question from header string"""
    try:
        return header.split("|")[-1].strip()
    except:
        return header

#Identify Text Columns
def is_text_column(series):
    non_null = series.dropna()
    if non_null.empty:
        return False
    sample = non_null.sample(min(5, len(non_null)))
    return any(isinstance(x, str) and any(char.isalpha() for char in str(x)) for x in sample)


#Main Processing
def main():
    # Load data
    df = pd.read_csv(INPUT_CSV)
    
    # 1. Clean column names first
    #df.columns = [col.split("|")[-1].strip() for col in df.columns]

    #Translate Headers
    new_headers = []
    for header in df.columns:
        if header.lower() in ['respondentid', 'answeredat']:
            new_headers.append(header)
            continue
        
        try:
            clean_hdr = clean_header(header)
            translated = translate_to_english(clean_hdr, context="header")
            new_headers.append(translated)
            logging.info(f"Header translated: '{header}' → '{translated}'")
        except Exception as e:
            new_headers.append(header)
            logging.error(f"Header translation failed for '{header}': {str(e)}")
    
    df.columns = new_headers
    logging.info(f"New headers: {list(df.columns)}")
    
    # 2. Identify text columns (excluding metadata/timestamps)
    text_cols = [col for col in df.columns 
                if col not in ['respondentId', 'answeredAt'] 
                and is_text_column(df[col])]
    
    #print(f"Columns to translate: {text_cols}")
    
    # 3. Process translations with progress bar
    for col in tqdm(text_cols, desc="Translating columns"):
        df[col] = df[col].apply(lambda x: translate_to_english(x) if pd.notna(x) else x)
    
    # 4. Save results
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Saved translated data to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()