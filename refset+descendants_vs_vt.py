import pandas as pd
import requests
from tqdm import tqdm
import os
from os import listdir
from os.path import isfile, join
from datetime import datetime

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
snowstorm_url = "http://ec2-3-123-35-169.eu-central-1.compute.amazonaws.com:8080/"
snomed_branch = 'MAIN'
snomed_versie = 'prerelease'

# Dataframes VT creëren
files_in_folder = [f for f in listdir("./resources") if isfile(join("./resources", f))]
i=0
print("Bestanden in map:")
print("-"*80)
file_1 = False
file_2 = False
file_3 = False
for file in files_in_folder:
    file_type = file.split("_")[-1:]
    if file_type[0] == "ThesaurusConceptRol.csv":
        thesaurusConceptRollen = pd.read_csv("./resources/"+file)
        file_1 = file
    if file_type[0] == "ThesaurusConcept.csv":
        thesaurusConcepten = pd.read_csv("./resources/"+file)
        file_2 = file
    if file_type[0] == "ThesaurusTerm.csv":
        thesaurusTermen = pd.read_csv("./resources/"+file)
        file_3 = file
if file_1 and file_2 and file_3:
    print("Bronbestanden gevonden.")
else:
    exit("Niet alle bronbestanden aanwezig.")

print("-"*80)
print("-"*80)
print(file_1)
print(thesaurusConceptRollen.head())
print("-"*80)
print(file_2)
print(thesaurusConcepten.head())
print("-"*80)
print(file_3)
print(thesaurusTermen.head())
print("-"*80)
print("-"*80)

# Ophalen refset members
def fetchEcl(ecl):
    concepts = []
    url = f"{snowstorm_url}{snomed_branch}/concepts?ecl={ecl}&limit=10000&returnIdOnly=true"
    # print(url)
    req = requests.get(url)
    response = req.json()
    total = response.get('total',0)
    while len(concepts) < total:
        concepts += response.get('items',[])
        url = f"{snowstorm_url}{snomed_branch}/concepts?ecl={ecl}&limit=10000&searchAfter={response.get('searchAfter')}&returnIdOnly=true"
        # print(url)
        req = requests.get(url)
        response = req.json()
    return concepts
conceptID_list = fetchEcl("^146481000146103")

print(f"{len(conceptID_list)} refsetleden opgehaald. Nu de descendants.")

# Descendants van refsetleden ophalen, en toevoegen aan lijst
deduplicated_list_ecl           = conceptID_list.copy()
deduplicated_list_descendants   = []
for concept in tqdm(deduplicated_list_ecl):
    deduplicated_list_descendants += fetchEcl(f"<{concept}")

# Lijsten dedupliceren
deduplicated_list_ecl = list(set(deduplicated_list_ecl))
print(len(deduplicated_list_ecl), "concepten in refset.")

deduplicated_list_descendants = list(set(deduplicated_list_descendants))
print(len(deduplicated_list_descendants), "concepten in descendants.")



# Lijst met thesaurusconcept ID's na filter creeren
thesaurusIDs = thesaurusConceptRollen['ConceptID'].values

# Iterate over kolom met Thesaurus ID's
output = []
for thesaurusID in list(set(thesaurusIDs)):
    thesaurusConcept = thesaurusConcepten[
        (thesaurusConcepten['ConceptID'] == thesaurusID) & (thesaurusConcepten['Einddatum'] == 20991231)
        ]

    thesaurusTerm = thesaurusTermen[
        (thesaurusTermen['ConceptID'] == thesaurusID) &
        (thesaurusTermen['Einddatum'] == 20991231) &
        (thesaurusTermen['TypeTerm'] == 'voorkeursterm')
    ]

    try:
        SCTID = int(thesaurusConcept['SnomedID'])
    except:
        SCTID = False

    try:
        term = thesaurusTerm['Omschrijving'].values[0]
    except:
        term = False

    groepCode = thesaurusConceptRollen[
                    thesaurusConceptRollen['ConceptID'] == thesaurusID
                ]['SpecialismeGroepCode'].values[0]

    in_ecl          = (SCTID in deduplicated_list_ecl)
    in_descendants  = (SCTID in deduplicated_list_descendants)

    output.append({
        'ThesaurusID' : str(thesaurusID),
        'Snomed ID' : str(SCTID),
        'Voorkeursterm' : term,
        'SpecialismeGroepCode' : str(groepCode),
        'SCTID in refset': in_ecl,
        'SCTID in descendants van refsetleden': in_descendants,
    })

# Iterate over refset members
output2 = []
for SCTID in deduplicated_list_ecl:
    present = False
    thesaurusTerm = False
    vt_concept = False
    for ConceptID in thesaurusConcepten[(thesaurusConcepten['SnomedID'] == SCTID) & (thesaurusConcepten['Einddatum'] == 20991231)]['ConceptID']:
        present = True
        vt_concept = ConceptID
        try:
            thesaurusTerm = thesaurusTermen[
                (thesaurusTermen['ConceptID'] == ConceptID) &
                (thesaurusTermen['Einddatum'] == 20991231) &
                (thesaurusTermen['TypeTerm'] == 'voorkeursterm')
            ]['Omschrijving'].values[0]
        except:
            continue


    output2.append({
        'Snomed ID' : str(SCTID),
        'ThesaurusID' : str(vt_concept),
        'Voorkeursterm DT' : thesaurusTerm,
        'SNOMED Concept in VT': present,
    })


# Exporteren naar Excel
now = datetime.now()
date_time = now.strftime("%m-%d-%Y_%H:%M:%S")
writer = pd.ExcelWriter(f"output_{date_time}.xlsx", engine='xlsxwriter')

# Sheet 1 met metadata
metadata_df = pd.DataFrame([
    {'key' : 'Scriptnaam', 'value' : os.path.basename(__file__)},
    {'key' : 'Export time', 'value' : date_time},
    {'key' : 'SNOMED versie', 'value' : snomed_versie},
    {'key' : 'Snowstorm URL', 'value' : snowstorm_url},
    {'key' : 'VT bronbestand[0]', 'value' : file_1},
    {'key' : 'VT bronbestand[1]', 'value' : file_2},
    {'key' : 'VT bronbestand[2]', 'value' : file_3},
    {'key' : 'Opmerkingen', 'value' : input("Opmerkingen voor in het output-bestand? ")},
])
metadata_df.to_excel(writer, 'Sheet1')

# Sheet 2 met resultaten - VT vs ECL
output_df = pd.DataFrame(output)
output_df.to_excel(writer, 'Sheet2')

# Sheet 3 met resultaten - ECL vs VT
output_df = pd.DataFrame(output2)
output_df.to_excel(writer, 'Sheet3')

writer.save()
print(f"Klaar - download output_{date_time}.xlsx voor resultaten.")