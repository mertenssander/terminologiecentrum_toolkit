from urllib.request import urlopen, Request
import requests
import json
import tqdm
import pickle
import time
import sys
from decouple import config
import pandas as pd

# Read file
df = pd.read_excel("CxReg_lijst_Snomed_CORR_ActieveCodes_voor Sander (Nictiz).xlsx")

print("-"*60)
print("INFO:")
print(f"Initialized")
print("-"*60)

# Login request uitvoeren
token_endpoint = "https://terminologieserver.nl/auth/realms/nictiz/protocol/openid-connect/token"
data = {
    "grant_type"    : "password",
    "client_id"     : "cli_client",
    "username"      : config('USERNAME'),
    "password"      : config('PASSWORD'),
}
response = requests.post(token_endpoint, data=data).json()
token = response.get('access_token')

# Set up result list
results = []

########### Set up validation request loop
for row, value in tqdm.tqdm(df.iterrows(), total=df.shape[0]):
    expression = value['Snomed'].strip()
    expression = expression.replace("\n"," ")
    expression = expression.replace("\r"," ")
    expression = requests.utils.quote(expression)
    # print(f"# {row} {'#'*80}")
    response = requests.get(
        f"https://terminologieserver.nl/fhir/CodeSystem/11000146104-20210331/$validate-code?code={expression}",
        headers = {
                "Authorization": "Bearer "+token,
                "Content-Type" : "application/fhir+json",
            },
        )

    response_dict = response.json()

    messages = []

    # Check validation result
    validatie_resultaat = None
    for parameter in response_dict['parameter']:
        if parameter['name'] == 'result':
            # print(f"Resultaat validatie: {parameter['valueBoolean']}")
            validatie_resultaat = parameter['valueBoolean']

    for parameter in response_dict['parameter']:
        if parameter['name'] == 'message':
            # print(parameter['valueString'])
            messages.append(parameter['valueString'])
        elif parameter['name'] == 'component' and validatie_resultaat == False:
            for part in parameter['part']:
                if part['name'] == 'message':
                    # print(part['valueString'])
                    messages.append(part['valueString'])
        
        else:
            # print("\t",parameter)
            continue

    results.append({
        'Code' : value['Code'],
        'CxTekst' : value['CxTekst'],
        'Snomed' : value['Snomed'],
        'ValidatieResultaat' : validatie_resultaat,
        'Meldingen' : messages,
    })

output_df = pd.DataFrame(results, columns=results[0].keys())
print(output_df.head())

output_df.to_excel("Output validatie CxReg.xlsx")