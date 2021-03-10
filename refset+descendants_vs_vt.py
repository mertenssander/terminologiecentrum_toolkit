import pandas as pd
import requests
from tqdm import tqdm
from os import listdir
from os.path import isfile, join

"""
Test welke van de leden+descendants in een refset er in de VT (totaal en lijst gyn) zitten.
146481000146103 |simpele referentieset met obstetrische verrichtingen (metadata)|

Plaats het VT Excel Release-bestand in ./resources

1) Maakt een lijst van een SNOMED refset en de descendants van die refsetleden.
2) Leest een release-bestand van de Verrichtingenthesaurus in
- Vergelijkt elke rij uit 2 met 1. Toont True/False in het output.xlsx bestand in kolom D.

Run met python3 refset+descendants_vs_vt.py. Kies in de dialoog het juist excel bestand en download output.xlsx.
"""
### Config ###
# Snowstorm URL - include trailing forward slash
snowstorm_url = "http://ec2-18-192-57-190.eu-central-1.compute.amazonaws.com:8080/"


# Bronbestand kiezen
files_in_folder = [f for f in listdir("./resources") if isfile(join("./resources", f))]
i=0
print("Bestanden in map:")
print("-"*80)
for file in files_in_folder:
    i+=1
    print(f"[{i}]\t{file}")

file_no = int(input("Welk bestand bevat de laatste versie van de verrichtingenthesaurus? "))-1
filename = files_in_folder[file_no]
print(f"Gekozen bestand: {filename}")
print("-"*80)

# Dataframe creëren
df = pd.read_excel("./resources/"+filename, header=2, sheet_name=1)

# Ophalen refset members
def fetchEcl(ecl):
    concepts = []
    url = f"{snowstorm_url}MAIN/concepts?ecl={ecl}&limit=10000&returnIdOnly=true"
    # print(url)
    req = requests.get(url)
    response = req.json()
    total = response.get('total',0)
    while len(concepts) < total:
        concepts += response.get('items',[])
        url = f"{snowstorm_url}MAIN/concepts?ecl={ecl}&limit=10000&searchAfter={response.get('searchAfter')}&returnIdOnly=true"
        # print(url)
        req = requests.get(url)
        response = req.json()
    return concepts
conceptID_list = fetchEcl("^146481000146103")

print(f"{len(conceptID_list)} refsetleden opgehaald. Nu de descendants.")

# Descendants van refsetleden ophalen, en toevoegen aan lijst
refset_plus_descendants = conceptID_list.copy()
for concept in tqdm(conceptID_list):
    refset_plus_descendants += fetchEcl(f"<{concept}")

# Lijst dedupliceren
deduplicated_list = list(set(refset_plus_descendants))
print(len(deduplicated_list), "concepten in totaal.")


# Iterate over kolom met SNOMED ID's
output = []
for row, value in df.iterrows():
    try:
        conceptID = value['Snomed ID & Snomed Term'].split(":")[0]
    except:
        conceptID = False
    in_ecl = (int(conceptID) in deduplicated_list)
    # print(row, conceptID, in_ecl)
    output.append({
        'ThesaurusID' : value['ThesaurusID'],
        'Voorkeursterm' : value['Voorkeursterm'],
        'Snomed ID & Snomed Term' : value['Snomed ID & Snomed Term'],
        'SCTID in refset of descendants?': in_ecl,
    })

# Exporteren naar Excel
output_df = pd.DataFrame(output)
output_df.to_excel("output.xlsx")
print(f"Klaar - download output.xlsx voor resultaten.")