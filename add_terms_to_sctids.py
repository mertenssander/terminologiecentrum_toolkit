import pandas as pd
import tqdm
import os
import logging
import requests
import json
from datetime import datetime
from functools import cache

"""

"""
### Config ###
# Snowstorm URL - include trailing forward slash
snowstorm_url = "https://snowstorm.test-nictiz.nl/"
snomed_branch = 'MAIN/SNOMEDCT-NL'
snomed_versie = 'live-20210331'
language_snowstorm = 'nl'
language_refsets = [
    '31000146106',      # NL
    '15551000146102',   # NL PT-Friendly
]

############################################################################

# Set up logger
logging.basicConfig(
    format='[%(levelname)8s] %(asctime)s | [%(module)20.20s] | %(message)s', 
    datefmt='%m/%d/%Y %I:%M:%S %p', 
    level = logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"Initialized {__name__}")

# Define function to retrieve terms
@cache
def fetchTerms(conceptid):
    url = f"{snowstorm_url}{snomed_branch}/concepts/{conceptid}/descriptions/"
    req = requests.get(url, headers={'Accept-Language':language_snowstorm})
    response = req.json()
    if req.status_code == 200:
        return response
    else:
        return {}
@cache
def fetchFSN_PT(conceptid):
    url = f"{snowstorm_url}{snomed_branch}/concepts/{conceptid}/"
    req = requests.get(url, headers={'Accept-Language':language_snowstorm})
    response = req.json()
    if req.status_code == 200:
        return response
    else:
        return {}

# Read source file
filename = input("Wat is de bestandsnaam? ")
logger.info(f"Filename: {filename}")
try:
    df = pd.read_excel(filename)
except Exception as e:
    logger.exception(f"Kon bestand niet openen. Foutmelding:")
    exit()
print(df.head())

# Select column
print("In welke kolom staat het SNOMED ID?")
for key, column in enumerate(df.columns):
    print(f"{key}: {column}")
column_id = int(input("Kolom ID: "))
column_name = df.columns[column_id]

logger.info(f"Gekozen kolom: {column_name}")

print("-"*80)

# Toevoegen termen
for row, value in tqdm.tqdm(df.iterrows(), total=df.shape[0]):
    terms = fetchTerms(value[column_name])['conceptDescriptions']
    fsn_pt = fetchFSN_PT(value[column_name])

    # Voeg FSN/PT toe
    df.at[row,'SNOMED-FSN'] = fsn_pt.get('fsn',{}).get('term',None)
    df.at[row,'SNOMED-PT']  = fsn_pt.get('pt',{}).get('term',None)

    # Voeg SYN toe
    syns = list()
    for syn in terms:
        desired_syn = False
        for key, acceptability in syn['acceptabilityMap'].items():
            if key in language_refsets:
                if acceptability in [
                    # 'PREFERRED',      # PREFERRED SYN staat al in kolom PT
                    'ACCEPTABLE',
                    ]:
                    desired_syn = True
        
        if desired_syn and syn['type'] == 'SYNONYM':
            syns.append(syn)
    
    for key, syn in enumerate(syns):
        df.at[row,f'SNOMED-SYN-{key}']  = syn.get('term')



print(df.head())

# Exporteren naar Excel
print("Exporteren naar excel")
export_comment = input("Opmerkingen voor in het output-bestand? ")
now = datetime.now()
date_time = now.strftime("%m-%d-%Y_%H:%M:%S")
writer = pd.ExcelWriter(f"output_{date_time}.xlsx", engine='xlsxwriter')

# # Sheet 1 met metadata
metadata_df = pd.DataFrame([
    {'key' : 'Scriptnaam', 'value' : os.path.basename(__file__)},
    {'key' : 'Export time', 'value' : date_time},
    {'key' : 'SNOMED versie', 'value' : snomed_versie},
    {'key' : 'Snowstorm URL', 'value' : snowstorm_url},
    {'key' : 'Bronbestand', 'value' : filename},
    {'key' : 'Opmerkingen', 'value' : export_comment},
])
metadata_df.to_excel(writer, 'Metadata')

# Sheet 2 met resultaten
df.to_excel(writer, 'Resultaat')
writer.save()
logger.info(f"Klaar - download output_{date_time}.xlsx voor resultaten.")
