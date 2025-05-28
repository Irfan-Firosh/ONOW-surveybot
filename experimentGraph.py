import pandas as pd
from pandas_profiling import ProfileReport

df = pd.read_csv('CleanedData/CMF_alumni_survey_english.csv')
profile = ProfileReport(df)
profile.to_file("report.html")


