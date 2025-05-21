import pandas as pd
import re

# Load the dataset
df = pd.read_csv('CMF_alumni_survey_english.csv')

# --- STEP 1: Clean Headers ---
def clean_header(header):
    # Remove special chars, extra spaces, and make lowercase
    header = re.sub(r'[^\w\s]', '', header)  # Remove symbols
    header = header.strip().lower().replace(' ', '_')  # Format
    return header

# Rename columns
df.columns = [clean_header(col) for col in df.columns]

# --- STEP 2: Clean Numerical Data ---
def clean_numeric(value):
    if pd.isna(value) or value == '':
        return None
    # Remove all non-numeric chars except digits, '.', and '-'
    cleaned = re.sub(r'[^\d.-]', '', str(value))
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None

# Columns to clean (now using cleaned headers)
numeric_columns = [
    'during_the_past_year_how_much_revenue_salesturnover_did_your_company_generate_per_month_if_you_have_a_business_but_have_not_generated_any_revenue_yet_please_write_0_use_the_local_currency',
    'if_you_answered_increased_or_decreased_can_you_estimate_by_how_much_it_increased_or_decreased',
    'calculate_the_exact_accumulated_investment_in_local_currency_do_not_include_your_own_savings_an_estimate_is_fine'
]

for col in numeric_columns:
    if col in df.columns:
        df[col] = df[col].apply(clean_numeric)

# Save cleaned data
df.to_csv('cleaned_CMF_alumni_survey_english.csv', index=False)
print("✅ Data cleaned and saved!")