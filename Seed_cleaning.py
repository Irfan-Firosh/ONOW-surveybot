#Cleaning the 2 csv files

import pandas as pd
import re

# Load the CSV files
seed = pd.read_csv('EFI_seed_order1.csv')
alumni = pd.read_csv('CMF_alumni_survey_spanish1.csv')

#Cleaning the seed csv file

# New column names
new_columns = [
    'respondentId',
    'answeredAt',
    'order_type',
    'customer_name',
    'full_address',
    'seed_types',
    'maize_kg',
    'sorghum_kg',
    'soyabeans_kg',
    'beans_kg',
    'rice_kg',
    'phone_number',
    'contact_preference',
    'remove_me'  # This is the empty column we'll drop
]

# Rename columns
seed.columns = new_columns

# Drop the empty column
seed = seed.drop(columns=['remove_me'])


# Save cleaned data
#seed.to_csv('EFI_seed_order1.csv', index=False)


#cleaning the kg columns
def clean_quantity(quantity):
    if pd.isna(quantity):
        return 0
    quantity = str(quantity).strip().lower()
    # Remove currency symbols, text, and commas
    quantity = re.sub(r'[^\d.]', '', quantity)
    # Extract first number
    match = re.search(r'(\d+\.?\d*)', quantity)
    return float(match.group(1)) if match else 0

seed['maize_kg'] = seed['maize_kg'].apply(clean_quantity)
seed['sorghum_kg'] = seed['sorghum_kg'].apply(clean_quantity)
seed['soyabeans_kg'] = seed['soyabeans_kg'].apply(clean_quantity)
seed['beans_kg'] = seed['beans_kg'].apply(clean_quantity)
seed['rice_kg'] = seed['rice_kg'].apply(clean_quantity)

seed.to_csv('EFI_seed_cleaned.csv', index=False)  