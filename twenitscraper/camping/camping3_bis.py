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

    def __init__(self, output_name:str, start_date:str, end_date:str):
        self.output_name = output_name
        self.start_date = start_date
        self.end_date = end_date

        self.create_file(self.output_name)
        self.scraping_dates = Queue()
        self.setup_dates()
        self.base_urls = Queue()
        self.base_link_paged = Queue()
        self.base_link_to_scrap = Queue()
        self.scrap_finished = False

        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument('--ignore-certificate-errors')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        # self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--incognito')
        self.current_driver = 'chrome'
        self.drivers = ['chrome', 'chrome']


        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=self.chrome_options)

        self.scrap()


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
        dates = pd.bdate_range(start=self.start_date, end=self.end_date, freq="C", weekmask="Sat")
        # dates = [date.to_pydatetime().strftime("%d/%m/%Y") for date in dates]
        dates = [date.to_pydatetime().strftime("%Y-%m-%d") for date in dates]
        for date in dates:
            self.scraping_dates.put(date)
        print(f"total dates {self.scraping_dates.qsize()}")

    def set_base_urls(self, date) -> None:
        print("setting up base urls")
        with open('./settings.json', 'r') as file:
            urls = json.loads(file.read())['urls']  
            for url in urls:
                self.base_urls.put(url + f"?checkInDate={date}&accommodation_types%5B0%5D=mobile_home&accommodation_types%5B1%5D=bungalow&region=18&type=region")
                # self.base_urls.put(url + f"?checkInDate=2023-11-04&accommodation_types%5B0%5D=mobile_home&accommodation_types%5B1%5D=bungalow&region=18&type=region")
        print(f"base urls length {self.base_urls.qsize()}")

    def get_page(self, url):
        print(f"getting page for {url}")
        try:
            self.driver.get(url)
            return self.driver.page_source
            print("page received")
        except Exception:
            time.sleep(5)
            self.switch_driver()
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
                    params_date = link[-10:]
                    url = link.split('?')[0]
                    if params_date == date:
                        link = url + f'?checkInDate={date}' + '&night=7'
                        self.base_link_to_scrap.put(link)
                    
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
            self.switch_driver()    #changement de driver
            page_data = self.get_page(url)
            data = self.extract_data(page_data, url)
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
    
            for result in results:
                data = {}
                typologie = result.find('h3', class_="result__name").text.strip() \
                    if result.find('h3', class_="result__name") else ''
                adulte = result.find('div', attrs={'data-property':"adults"}).text.strip() \
                    if result.find('div',attrs={'data-property':"adults"}) else ''
                prix_actuel = re.sub(r'[^0-9.]', '', (result.find('div', class_='best-offer__price-value').text.strip()[:-2].replace(',', '.'))).replace(' ', '') \
                    if result.find('div', class_='best-offer__price-value') else ''
                prix_init = re.sub(r'[^0-9.]', '', (result.find('div', class_="best-offer__price-old").text.strip()[:-2].replace(',','.'))).replace(' ', '') \
                    if result.find('div', class_="best-offer__price-old") else prix_actuel
                station_key, date_debut, date_fin = self.get_link_data(url)
                data['url'] = url
                data['web-scrapper-order'] = ''
                data['date_price'] = str((datetime.now() - timedelta(days = datetime.now().weekday())).strftime("%d/%m/%Y"))
                data['date_debut'] = date_debut
                data['date_fin'] = date_fin
                data['prix_init'] = prix_init
                data['prix_actuel'] = prix_actuel
                data['typologie'] = typologie
                data['nom'] = name
                data['Nb personnes'] = adulte
                data['localite'] = localite
                data['n_offres'] = ''
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
                    'url',
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
                    'n_offres',
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
    csv_source.drop_duplicates(subset=['date_price', 'date_debut', 'date_fin', 'prix_init', 'prix_actuel', 'typologie', 'n_offre', 'nom', 'localite', 'date_debut-jour','Nb semaines', 'cle_station', 'nom_station'])
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
        'url',
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
    CampingScrap('./data/test1.csv', "2023/04/01", "2023/04/7")
    
    # for i in range(0, 8):
    #     try:
    #         clean_campings(f"E:/asa/MUnit/save/27_03_2023/campings/n{i}.csv", f"E:/asa/MUnit/save/27_03_2023/campings/n{i}_cleaned.csv")
    #     except Exception as e:
    #         print(e)
    #         pass

    # merge_campings([f"E:/asa/MUnit/save/27_03_2023/campings/n{i}_cleaned.csv" for i in range(0,8)], "E:/asa/MUnit/save/27_03_2023/campings/merged.csv")

    