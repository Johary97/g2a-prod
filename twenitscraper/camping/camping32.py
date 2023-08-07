import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from bs4 import BeautifulSoup
from datetime import datetime
from csv import DictWriter, writer
from queue import Queue
from datetime import timedelta
import pandas as pd
import threading
import json
import os
import time
import requests
from random import randint
from unidecode import unidecode
import re
from urllib.parse import urlparse, parse_qs


class CampingScrap(object):

    def __init__(self, day:str,output_name:str, start_date:str, end_date:str):
        monday = str((datetime.now() - timedelta(days = datetime.now().weekday())).strftime("%d_%m_%Y"))
        file_dir = f'C:/Files/tmp/results/campings/{monday}'

        if not os.path.isdir(file_dir):
            os.mkdir(file_dir)

        self.output_name = f'{file_dir}/{output_name}'
        self.start_date = start_date
        self.end_date = end_date
        self.days = day

        self.create_file(self.output_name)
        self.scraping_dates = Queue()
        self.setup_dates()
        self.base_urls = Queue()
        self.base_link_paged = Queue()
        self.base_link_to_scrap = Queue()
        self.base_link_to_scrap_set = set()
        self.scrap_finished = False

        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument('--ignore-certificate-errors')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        # self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--incognito')
        self.chrome_options.add_argument('start-maximized')
        self.current_driver = 'chrome'
        self.drivers = ['chrome', 'chrome']

        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=self.chrome_options)

        # self.scrap()

        thread = threading.Thread(target=self.scrap)

        # starting thread 1
        thread.start()

        # # wait until thread 1 is completely executed
        # thread.join()

    def scrap(self):
        print("scraping start...")
        while not self.scraping_dates.empty():
            date = self.scraping_dates.get()
            print(f"scrapping on date {date}")
            self.set_base_urls(date)
            self.set_urls_with_page()
            self.scrap_station_link_details(date)
            self.scrap_detail_pages()
        print("scraping finished ('_')")

    def switch_driver(self) -> None:
        """ function to make switch driver """
        self.drivers = self.drivers[1:] + self.drivers[0:1]
        self.driver.quit()
        self.current_driver = self.drivers[0]
        match self.current_driver:
            case 'chrome': 
                self.driver = webdriver.Chrome(options=self.chrome_options)

    def setup_dates(self) -> object:
        print("setup dates")
        # self.days must be "Sat" or "Sun"
        dates = [date.to_pydatetime().strftime("%Y-%m-%d") for date in pd.bdate_range(start=self.start_date, end=self.end_date, freq="C", weekmask=self.days)]
        print(f"Date between: {dates[0]} and {dates[len(dates)-1]}")
        
        for date in dates:
            self.scraping_dates.put(date)

        print(f"total dates {self.scraping_dates.qsize()}")

    def set_base_urls(self, date) -> None:
        print("setting up base urls")
        with open('C:/src/programs/twenitscraper/camping/config2.json', 'r') as file:
            urls = json.loads(file.read())['urls']  
            for url in urls:
                self.base_urls.put(url + f"?checkInDate={date}&accommodation_types%5B0%5D=mobile_home&accommodation_types%5B1%5D=bungalow&region=18&type=region")
            
        print(f"base urls length {self.base_urls.qsize()}")

    def get_page(self, url):
        print(f"getting page for {url}")
        self.switch_driver()

        try:
            self.driver.get(url)
            return self.driver.page_source
        except Exception:
            return self.get_page(url)

    def get_page_length(self, url:str) -> int:
        print("getting page length")
        page = self.get_page(url)
        soupe = BeautifulSoup(page, 'lxml')
        page_length = len(soupe.find_all('li', class_='dca-pagination__page-item')) \
            if soupe.find_all('li', class_='dca-pagination__page-item') else 1
        print(f"page length for url {url} is {page_length}")
        return page_length

    def set_urls_with_page(self) -> None:
        print("setting up urls with page")
        while not self.base_urls.empty():
            url = self.base_urls.get()
            page = self.get_page_length(url)
            url_paged = list(self.generate_url_with_page(url, page))
            for url_page in url_paged:
                self.base_link_paged.put(url_page)
        print(f"urls with page length {self.base_link_paged.qsize()}")

    def scrap_station_link_details(self, date:str) -> None:
        while not self.base_link_paged.empty():
            link = self.base_link_paged.get()
            page = self.get_page(link)
            soupe = BeautifulSoup(page, 'lxml')
            results = soupe.find('div', class_="dca-results__list").find_all('section', class_='dca-result--product') \
                if soupe.find('div', class_="dca-results__list").find_all('section', class_='dca-result--product') else []
            if results:
                for result in results:
                    link = 'https://www.campings.com' + result.find('a', href=True)['href']
                    url = link.split('?')[0]
                    link = url + f'?checkInDate={date}&night=7'

                    if link not in self.base_link_to_scrap_set:
                        self.base_link_to_scrap.put(link)
                        self.base_link_to_scrap_set.add(link)
                    else:
                        print("Url existant !!!")
                    
        print(f"link for data scraping length {self.base_link_to_scrap.qsize()}")

                
    def generate_url_with_page(self, url:str, page:int) -> object:
        print("generating url with page ...")
        for i in range(1, (page + 1)):
            yield url + f"&page={i}"

    def scrap_detail_pages(self):
        print("scrapping detail pages")
        while not self.base_link_to_scrap.empty():
            print("Rest to scrap: ", self.base_link_to_scrap.qsize())
            url = self.base_link_to_scrap.get()
            page_data = self.get_page(url)
            data = self.extract_data(page_data, url)

            if data:
                self.save_data(data, self.output_name)
                
        print("scrapping done ('_')")

    def get_link_data(self, url:str) -> tuple:
        """ function to get dates in url """
        data = url.replace("https://www.campings.com/fr/camping/", '').split('?')
        station_key = data[0][:-1]
        checkin_date = (datetime.strptime(data[1][12:22].replace('-', '/'), "%Y/%m/%d")).strftime("%d/%m/%Y")
        checkout_date = (datetime.strptime(checkin_date, "%d/%m/%Y") + timedelta(days=7)).strftime("%d/%m/%Y")
        return station_key, checkin_date, checkout_date
    
    def extract_data(self, page:str, url:object) -> list:
        def extract_dates(string_date):
            months = {'jan.': 1, 'fév.': 2, 'mars': 3, 'avr.': 4, 'mai': 5, 'juin': 6, 'juil.': 7, 'août': 8, 'sept.': 9, 'oct.': 10, 'nov.': 11, 'déc.': 12}
            date_split = []
            i = 0

            for s in string_date.split('\n'):
                if i==2:
                    s = s.strip().split(' ')
                    day = s[0]
                    month = s[1]
                    date_split.append(day)
                    date_split.append(month)

                elif s != ' ':
                    date_split.append(s.strip())
                
                i += 1

            print(date_split)
            return datetime.strftime(datetime.strptime(f"{date_split[2]}/{months[date_split[3]]}/2023", '%d/%m/%Y'), '%d/%m/%Y') 

        try:
            print("extracting data ....")
            soupe = BeautifulSoup(page, 'lxml')
            name = ''.join(soupe.find('h1', class_='product__name').text.strip().split('\n')[:-1]) \
                if soupe.find('h1', class_='product__name') else ''
            localite = ''

            try:
                localite = ''.join(soupe.find('div', class_='product__localisation').text.strip().split('\n')[0].split('-')[1]).replace(", FRANCE", "") \
                    if soupe.find('div', class_='product__localisation') else ''
            except IndexError:
                localite = soupe.find('div', class_='product__localisation').text.strip().replace("- Voir sur la carte", "") \
                    if soupe.find('div', class_='product__localisation') else ''
                
            results = soupe.find('div', class_='dca-results__list').find_all('div', class_='dca-result--accommodation') \
                if soupe.find('div', class_='dca-results__list').find_all('div', class_='dca-result--accommodation') else []

            datas = []
            station_key, date_debut, date_fin = self.get_link_data(url)
            final_results = []

            print("Liste trouvée: ",len(results))

            for result in results:
                dates_string = result.find('div', class_="dates__values").text.strip()
                date_1 = extract_dates(dates_string)
                print("Date found:", date_1)
                if date_1 == date_debut:
                    final_results.append(result)

            print(f"Valid results: {len(final_results)}/{len(results)}")

            for result in final_results:
                data = {}
                typologie = result.find('h3', class_="result__name").text.strip() \
                    if result.find('h3', class_="result__name") else ''
                adulte = result.find('div', attrs={'data-property':"adults"}).text.strip() \
                    if result.find('div',attrs={'data-property':"adults"}) else ''
                prix_actuel = re.sub(r'[^0-9.]', '', (result.find('div', class_='best-offer__price-value').text.strip()[:-2].replace(',', '.'))).replace(' ', '') \
                    if result.find('div', class_='best-offer__price-value') else ''
                prix_init = re.sub(r'[^0-9.]', '', (result.find('div', class_="best-offer__price-old").text.strip()[:-2].replace(',','.'))).replace(' ', '') \
                    if result.find('div', class_="best-offer__price-old") else prix_actuel
                # station_key, date_debut, date_fin = self.get_link_data(url)
                # data['url'] = url
                data['web-scrapper-order'] = ''
                data['date_price'] = str((datetime.now() - timedelta(days = datetime.now().weekday())).strftime("%d/%m/%Y"))
                data['date_debut'] = date_debut
                data['date_fin'] = date_fin
                data['prix_init'] = prix_init
                data['prix_actuel'] = prix_actuel
                data['typologie'] = typologie.replace('\n', ' ')
                data['nom'] = name.replace('\n', ' ')
                data['Nb personnes'] = adulte.replace('\n', ' ')
                data['localite'] = localite.replace('\n', ' ')
                data['n_offre'] = ''
                data['date_debut-jour'] = ''
                data['Nb semaines'] = datetime.strptime(date_debut, '%d/%m/%Y').isocalendar()[1]
                data['cle_station'] = station_key
                data['nom_station'] = ''
                datas.append(data)
            print("extracting done ...")
            return datas

        except Exception as e:
            with open('errors.txt', 'w') as errorfile:
                errorfile.write(f'{e}\n')
            with open('debug.txt', 'w') as debugfiel:
                debugfiel.write(f'{url}\n')
            pass
    
    def save_data(self, data:list, filename:str) -> bool:
        print("saving data")
        df = pd.DataFrame(data)
        try:
            df.to_csv(filename, mode='a', index=False, header=False)
            print("data saved successfully ... ")
            return True
        except Exception as e:
            print(e)
            return False

    def create_file(self, filename:str) -> None:
        print("creating file")
        if not os.path.exists(f"{filename}"):
            with open(f"{filename}", 'w') as file:
                fields_name = [
                    # 'url',
                    'web-scrapper-order',
                    'date_price',
                    'date_debut', 
                    'date_fin',
                    'prix_init',
                    'prix_actuel',
                    'typologie',
                    'nom',
                    'Nb Personnes',
                    'localite',
                    'n_offre',
                    'date_debut-jour',
                    'Nb semaines',
                    'cle_station',
                    'nom_station'
                ]
                writers = writer(file)
                writers.writerow(fields_name)

def clean_campings(src, dest):
    def clean_line(line, references):
        for key in line.keys():
            if str(line[key]) == 'nan':
                line[key] = ''

        line['localite'] = line['localite'].split(',')[0].strip()
        if line['localite'] in references.keys() and type(references[line['localite']]['station']) == str:
            line['nom_station'] = references[line['localite']]['station']

        if type(line['nom_station']) != str:
                line['nom_station'] = ""
        
        line['web-scrapper-order'] = ""
        line['n_offre'] = ""
        line['date_debut-jour'] = ""
        line['localite'] = line['localite'].replace(', ', ' ') if not line['localite'].split(' ')[0].isdigit() else ' '.join(line['localite'].split(' ')[1:]).replace(', ', ' ')
        line['typologie'] = line['typologie'].replace(', ', ' - ')
        line['prix_init'] = str(int(float(line['prix_init']))) if line['prix_init'] != 'prix_init' else 'prix_init'
        line['prix_actuel'] = str(int(float(line['prix_actuel']))) if line['prix_actuel'] != 'prix_actuel' else 'prix_actuel'

        return line

    csv_source = pd.read_csv(src, encoding='utf-8')
    csv_source = csv_source.loc[csv_source['Nb Personnes'].isin(['4 Adultes','6 Adultes', '8 Adultes'])]
    csv_source.drop_duplicates(subset=['date_price', 'date_debut', 'date_fin', 'prix_init', 'prix_actuel', 'typologie', 'nom', 'localite'])
    csv_source.sort_values(inplace=True, ascending = True, by=['Nb semaines', 'date_debut'])
    csv_dict = csv_source.to_dict(orient='records')

    new_dict = []

    all_references_list = pd.read_excel('referencement stations.xlsm', sheet_name='Feuil1').to_dict(orient='records')

    all_references_dict = {}
    for ref in all_references_list:
        if ref['Localite'] not in all_references_dict.keys():
            all_references_dict[ref['Localite'].split(',')[0]] = {'station': ref['Station'], 'dest': ref['Cle station']}

    for line in csv_dict:
        cleaned_line = clean_line(line, all_references_dict)
        new_dict.append(cleaned_line)

    with open(dest, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['web-scrapper-order', 'date_price', 'date_debut', 'date_fin', 'prix_init', 'prix_actuel', 'typologie', 'Nb Personnes','n_offre', 'nom', 'localite', 'date_debut-jour','Nb semaines', 'cle_station', 'nom_station']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for line in new_dict:
            try:
                writer.writerow(line)
            except Exception as e:
                print(e)
                pass

def merge_campings(srcs, dest):
    csv_list = []

    csv_headers = pd.DataFrame(columns=[
        'web-scrapper-order',
        'date_price',
        'date_debut', 
        'date_fin',
        'prix_init',
        'prix_actuel',
        'typologie',
        'n_offre',
        'nom',
        'localite',
        'date_debut-jour',
        'Nb semaines'
        ])

    csv_list.append(csv_headers)

    for file in srcs:
        csv_list.append(pd.read_csv(file, encoding='utf-8'))

    csv_merged = pd.concat(csv_list)
    csv_merged.sort_values(inplace=True, ascending = True, by=['Nb semaines', 'date_debut'])
    csv_merged.drop_duplicates(subset=['date_price', 'date_debut', 'date_fin', 'prix_init', 'prix_actuel', 'typologie', 'n_offre', 'nom', 'localite', 'date_debut-jour','Nb semaines'])
    csv_merged.to_csv(dest, index=False)


if __name__=='__main__':
    instances = []

    with open('C:/src/programs/twenitscraper/camping/config2.json', 'r') as file:
        settings = json.loads(file.read())
        instances = settings['instances']
    
    for instance in instances:
        CampingScrap(instance['dates'], instance['filename'], instance['start_date'], instance['end_date'])
    print("Scrapping done!")
    
    # both threads completely executed

    # CampingScrap('Sun', './data/argeles.csv', "2023/04/25", "2023/11/25")
    
    # for i in range(0, 8):
    #     try:
    #         clean_campings(f"E:/asa/MUnit/save/27_03_2023/campings/n{i}.csv", f"E:/asa/MUnit/save/27_03_2023/campings/n{i}_cleaned.csv")
    #     except Exception as e:
    #         print(e)
    #         pass

    # merge_campings([f"E:/asa/MUnit/save/27_03_2023/campings/n{i}_cleaned.csv" for i in range(0,8)], "E:/asa/MUnit/save/27_03_2023/campings/merged.csv")

    # clean_campings("C:/Files/tmp/results/campings/03_04_2023/languedoc-roussillon-gard.csv", "C:/Files/tmp/results/campings/03_04_2023/languedoc-roussillon-gard_cleaned.csv")
    
    # print("cleaning data done!")