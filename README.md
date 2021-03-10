# terminologiecentrum_toolkit
>docker-compose build --no-cache runner

>docker-compose run runner

Dit dropt je in een bash sessie, waarbij je toegang hebt tot alle bestanden in de repository. De bestanden worden gespiegeld met de root directory van de repository.

# Scripts
## DHD
### Verrichtingenthesaurus
- refset+descendants_vs_vt.py
    
    Vergelijkt leden van een SNOMED refset en descendants van deze leden met de VT. Exporteert kolommen voor specalismecode, lidmaatschap van refset, match met descendants van refsetleden