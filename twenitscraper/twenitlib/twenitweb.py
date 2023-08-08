import pandas as pd
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
import json, csv
import os, re
from pathlib import Path


def get_selectors() -> list:
    selectors = [
        {
            "id":"paginator",
            "parentSelectors":["_root","paginator"],
            "paginationType":"clickOnce",
            "selector":"button.f9c5690c58",
            "type":"SelectorPagination"
        },
        {
            "id":"element",
            "parentSelectors":["_root","paginator"],
            "type":"SelectorElement",
            "selector":"div.fe821aea6c:nth-of-type(n+2)",
            "multiple":True
        },
        {
            "id":"nom",            
            "multiple": False,
            "parentSelectors":["element"],
            "regex":"",
            "selector": "div.fcab3ed991",
            "type": "SelectorText"
        }, 
        {
            "id":"localite",
            "multiple": False,
            "parentSelectors":["element"],
            "regex":"",
            "selector": "span.f4bd0794db[data-testid]",
            "type": "SelectorText"
        },
        {
            "id":"prix_init",
            "multiple":False,
            "parentSelectors":["element"],
            "regex":"",
            "selector":"span.c5888af24f",
            "type":"SelectorText"
        },
        {
            "id":"prix_actuel",
            "multiple":False,
            "parentSelectors":["element"],
            "regex":"",
            "selector":"span.fcab3ed991",
            "type":"SelectorText"
        },
        {
            "id":"note",
            "multiple":False,
            "parentSelectors":["element"],
            "regex":"",
            "selector":"div.d10a6220b4",
            "type":"SelectorText"
        },
        {
            "id":"typo",
            "multiple":False,
            "parentSelectors":["element"],
            "regex":"",
            "selector":"span.df597226dd",
            "type":"SelectorText"
        },
        {
            "id":"type_de_lit",
            "multiple":False,
            "parentSelectors":["element"],
            "regex":"",
            "selector":".cb5b4b68a4 div",
            "type":"SelectorText"
        },
        {
            "id":"taxes",
            "multiple":False,
            "parentSelectors":["element"],
            "regex":"",
            "selector":"div[data-testid='taxes-and-charges']",
            "type":"SelectorText"
        },
        {
            "id":"nuite",
            "multiple":False,
            "parentSelectors":["element"],
            "regex":"",
            "selector":"div[data-testid='price-for-x-nights']",
            "type":"SelectorText"
        },
        {
            "id":"experience_vecu",
            "multiple":False,
            "parentSelectors":["element"],
            "regex":"",
            "selector":"div.db63693c62",
            "type":"SelectorText"
        },
        {
            "id":"reduction",
            "multiple":False,
            "parentSelectors":["element"],
            "regex":"",
            "selector":"span.e2f34d59b1",
            "type":"SelectorText"
        },
        {
            "id":"genius",
            "multiple":False,
            "parentSelectors":["element"],
            "regex":"",
            "selector":".b2fe1a41c3.a1f3ecff04 div.b1e6dd8416",
            "type":"SelectorText"
        }
    ]
    return selectors

def generate_url(checkin:str, checkout:str, dest_id:int) -> str:
    return f"https://www.booking.com/searchresults.fr.html?label=gog235jc-1DCAYoTUIGc2F2b2llSA1YA2hNiAEBmAENuAEXyAEM2AED6AEB-AECiAIBqAIDuAK37uOQBsACAdICJDJjMjgxMmVhLTIyM2MtNDI1Mi1iYTM4LTA3MmE4MjI3MWFkMdgCBOACAQ&sid=086e078aef1832684e5d5671c99a12b1&aid=356980&dest_id={dest_id}&dest_type=region&nflt=ht_id%3D204%3Brpt%3D1&shw_aparth=0&checkin={checkin}&checkout={checkout}&selected_currency=EUR"

def get_dates(url:str) -> object:
    url_params = parse_qs(urlparse(url).query)
    date_fin, date_debut = url_params['checkin'][0], url_params['checkout'][0]
    sep = '-'
    return sep.join(date_debut.split('-')[::-1]), sep.join(date_fin.split('-')[::-1])

def generate_sitemap(dest_folder:str, name:str, dest_ids:str, start_date:str, end_date:str, freq:str) -> None:
    data = {}
    start_url = []
    frequencies = []
    
    match freq:
        case 'all': frequencies = [1, 3, 7]
        case _: frequencies.append(int(freq))

    df = pd.read_csv(dest_ids)
    dest_ids = df['dest_id']

    for freq in frequencies:
        checkin_date = datetime.strptime(start_date, "%Y-%m-%d")
        checkout_date = datetime.strptime(end_date, "%Y-%m-%d")
        date_space = int((checkout_date - checkin_date).days) + 1

        checkin = datetime.strptime(start_date, "%Y-%m-%d")
        checkout = checkin + timedelta(days=freq)

        for i in range(date_space):
            for dest_id in dest_ids:
                start_url.append(generate_url(checkin.strftime("%Y-%m-%d"), checkout.strftime("%Y-%m-%d"), dest_id))
            checkin += timedelta(days=1) 
            checkout += timedelta(days=1)

        start_url.reverse()
            
        data['_id'] = f"booking_{freq}j" + f"{checkin_date}"
        data['startUrl'] = start_url
        data['selectors'] = get_selectors()

        json_data = json.dumps(data, indent=4)
        
        with open(f'{dest_folder}/{name}_{freq}j_{datetime.strptime(start_date, "%Y-%m-%d").date()}-{datetime.strptime(end_date, "%Y-%m-%d").date()}.json', "w") as file:
            file.write(json_data)

def clean_result(src:str, dest:str, file_type:str):

    df = pd.read_csv(src)

    checkin_date = []
    checkout_date = []
    prix_init = []
    prix_actuel = []
    reduction = []
    genius = []
    taxes = []

    nom = df['nom'].to_list()
    localite = df['localite'].to_list()
    typo = df['typo'].to_list()
    type_de_lit = df['type_de_lit'].to_list()
    experiences = [x.split('ex')[0] if str(x) != 'nan' else 0 for x in df['experience_vecu'].to_list()]

    prix_actuels = df['prix_actuel'].to_list()
    for ol in range(len(prix_actuels)):
        if str(prix_actuels[ol]) != 'nan':
            if df['taxes'].loc[ol].lower() != 'taxes et frais compris':
                prix = int(str(prix_actuels[ol].split('€')[1][1:].replace(' ', ''))) + int(df['taxes'].loc[ol].split('€')[1][1:].replace(' ', ''))
                prix_actuel.append(prix)
            else:
                prix_actuel.append(str(prix_actuels[ol])[1:])
        else:
            prix_actuel.append(0)


    prix_inits = df['prix_init'].to_list()
    for k in range(len(prix_inits)):
        prix_init.append(str(prix_inits[k])[1:] if str(prix_inits[k]) != 'nan' else prix_actuel[k])

    for i in df['web-scraper-start-url'].to_list():
        outdate, indate = get_dates(i)
        checkin_date.append(indate)
        checkout_date.append(outdate)

    for m in df['reduction'].to_list():
        reduction.append(m if str(m) != 'nan' else '0%')

    for n in df['genius'].to_list():
        genius.append(1 if str(n) != 'nan' else 0)

    for j in df['taxes'].to_list():
        taxes.append(j)
        
    date_price = []
    for i in prix_actuel:
        date_p = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime('%d/%m/%y')
        date_price.append(date_p)

    typologie = []
    for i in prix_actuel:
        typologie.append('')
        
    n_offre = []
    for i in prix_actuel:
        n_offre.append('')
        
    date_debut_jour = []
    for i in prix_actuel:
        date_debut_jour.append('')
        
    nb_semaine = []
    for i in checkin_date:
        nb_semaine.append(datetime.strptime(i, '%d-%m-%Y').isocalendar()[1])
        
    checkin_date = list(map(lambda x: datetime.strptime(x, '%d-%m-%Y').strftime('%d/%m/%Y'), checkin_date))
    checkout_date = list(map(lambda x: datetime.strptime(x, '%d-%m-%Y').strftime('%d/%m/%Y'), checkout_date))
        
    data = pd.DataFrame(
        {
            'web-scraper-order': df['web-scraper-order'].to_list(),
            'date_price': date_price,
            'date_debut': checkin_date,
            'date_fin': checkout_date,
            'prix_init': prix_init,
            'prix_actuel': prix_actuel,
            'typologie': df['typo'].to_list(),
            'n_offre': n_offre,
            # 'genius': genius,
            'nom': nom,
            'localite': localite,
            'date_debut-jour': date_debut_jour,
            'Nb semaines':nb_semaine
        }
    )

    data = data.drop_duplicates(subset=['date_price',  'date_debut', 'date_fin', 'prix_init', 'prix_actuel', 'typologie', 'n_offre', 'nom', 'localite', 'date_debut-jour','Nb semaines'])

    date_index = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime('%d_%m_%y')
    # items = data[data['genius'] == 1]
    filename = Path(src).stem
    dest_filename = f'{dest}/{filename}_cleaned_{date_index}.csv' if file_type == 'csv' else f'{dest}/{filename}_cleaned_{date_index}.xlsx'

    # if len(items) > 0:
    #     if file_type == 'csv':
    #         data.to_csv(dest_filename, index=False)
    #     else:
    #         data.to_excel(dest_filename, index=False)

    # else:
    # data = data.drop(columns=['genius'])
    if file_type == 'csv':
        data.to_csv(dest_filename, index=False)
    else:
        data.to_excel(dest_filename, index=False)
    
    return True
