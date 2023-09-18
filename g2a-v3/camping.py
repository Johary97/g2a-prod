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
from scraping import Scraping, Scraper
from tools.args import main_arguments, ARGS_INFO, check_arguments
import dotenv
from tools.g2a import CSVUploader
from tools.changeip import refresh_connection


class AnnonceCamping(Scraping):
    def __init__(self, in_background:bool=False) -> None:
        super().__init__(in_background=in_background)
        self.data_extension = 'csv'
        self.week_scrap = ''
        self.website_name = 'campings'
        self.website_url = 'www.campings.com'

    def set_week_scrap(self, date: str) -> None:
        self.week_scrap = date

    def set_to_principal(self):
        self.principal = True

    def get_link_data(self) -> tuple:
        """ function to get dates in url """
        url = self.driver.current_url
        data = url.replace("https://www.campings.com/fr/camping/", '').split('?')
        station_key = data[0][:-1]

        try:
            checkin_date = (datetime.strptime(data[1][23:33].replace('-', '/'), "%Y/%m/%d")).strftime("%d/%m/%Y")
        except:
            checkin_date = (datetime.strptime(data[1][12:22].replace('-', '/'), "%Y/%m/%d")).strftime("%d/%m/%Y")

        checkout_date = (datetime.strptime(checkin_date, "%d/%m/%Y") + timedelta(days=7)).strftime("%d/%m/%Y")
        
        return station_key, checkin_date, checkout_date

    def extract(self) -> None:
        def extract_dates(string_date,year):
            months = {'janv.': 1, 'févr.': 2, 'mars': 3, 'avr.': 4, 'mai': 5, 'juin': 6, 'juil.': 7, 'août': 8, 'sept.': 9, 'oct.': 10, 'nov.': 11, 'déc.': 12}
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

            return datetime.strftime(datetime.strptime(f"{date_split[2]}/{months[date_split[3]]}/{year}", '%d/%m/%Y'), '%d/%m/%Y') 

        try:
            soupe = BeautifulSoup(self.driver.page_source, 'lxml')
            name = ''.join(soupe.find('h1', class_='product__name').text.strip().split('\n')[:-1]) \
                if soupe.find('h1', class_='product__name') else ''
            localite = ''

            try:
                localite = ''.join(soupe.find('div', class_='product__localisation').text.strip().split('\n')[0].split('-')[1]).replace(", FRANCE", "") \
                    if soupe.find('div', class_='product__localisation') else ''
            except IndexError:
                localite = soupe.find('div', class_='product__localisation').text.strip().replace("- Voir sur la carte", "") \
                    if soupe.find('div', class_='product__localisation') else ''
            except Exception as e:
                print(e)
                
            try:
                results = soupe.find('div', class_='dca-results__list').find_all('div', class_='dca-result--accommodation') \
                    if soupe.find('div', class_='dca-results__list').find_all('div', class_='dca-result--accommodation') else []
            except Exception as e:
                print(e)

            datas = []
            station_key, date_debut, date_fin = self.get_link_data()
            final_results = []

            for result in results:
                dates_string = result.find('div', class_="dates__values").text.strip()
                date_1 = extract_dates(dates_string, year=date_debut.split('/')[2])
                if date_1 == date_debut:
                    final_results.append(result)

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

                data['web-scrapper-order'] = ''
                data['date_price'] = self.week_scrap
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
                data['url'] = self.driver.current_url
                datas.append(data)
            self.data = datas

        except Exception as e:
            print(e)
            self.driver.quit()
            raise Exception(e)

    def create_file(self) -> None:
        if not os.path.exists(f"{self.storage_file}"):
            with open(f"{self.storage_file}", 'w') as file:
                fields_name = [
                    'web-scrapper-order',
                    'date_price',
                    'date_debut',
                    'date_fin',
                    'prix_init',
                    'prix_actuel',
                    'typologie',
                    'n_offre',
                    'nom',
                    'Nb personnes',
                    'localite',
                    'date_debut-jour',
                    'Nb semaines',
                    'cle_station',
                    'nom_station'
                ]
                writers = writer(file)
                writers.writerow(fields_name)
    
    def save_data(self) -> bool:
        
        """ function to append data at the excel file """
        # return True
        # print(self.data)
        if len(self.data):
            try:
                field_names = [
                    'web-scrapper-order',
                    'date_price',
                    'date_debut', 
                    'date_fin',
                    'prix_init',
                    'prix_actuel',
                    'typologie',
                    'n_offre',
                    'nom',
                    'Nb personnes',
                    'localite',
                    'date_debut-jour',
                    'Nb semaines',
                    'cle_station',
                    'nom_station'
                ]

                with open(self.storage_file, 'a', newline='') as f_object:
                    dictwriter_object = csv.DictWriter(f_object, fieldnames=field_names)
                    dictwriter_object.writerows(self.data)
                    return True
            except Exception as e:
                print(e)
                with open('SaveDataError.txt', 'a') as file:
                    file.write(f"{e}")
                    return False  


class CampingScraper(Scraper):
    def __init__(self,) -> None:
        super().__init__()
        self.urls = []
        self.storage = ''
        self.log = ''
        self.week_scrap = ''
        self.principal = False

    def set_destinations(self, filename: str) -> None:
        with open(filename, 'r') as infile:
            self.urls = json.load(infile)

    def set_output(self, name):
        self.output = f'{name}.csv'

    def set_log(self, log):
        self.log = f'{log}.json'

    def set_week_scrap(self, date: str) -> None:
        self.week_scrap = date

    def set_to_principal(self) -> None:
        self.principal = True
    
    def start(self) -> None:
        if self.principal:
            refresh_connection()

        counter = 0

        c = AnnonceCamping(in_background=True)

        if self.principal:
            c.set_to_principal()

        c.set_week_scrap(self.week_scrap)
        last_index = self.get_history('last_index')
        # c.set_driver_interval(300, 500)
        c.set_storage(self.output)
        c.create_file()
        for index in range(last_index + 1, len(self.urls)):
            try:
                print(index+1, ' / ', len(self.urls))
                c.set_url(self.urls[index])
                c.scrap()
                time.sleep(5)
                c.extract()
                c.save()
                c.save_data()
                self.set_history('last_index', index)

                if self.principal:
                    counter += 1
                    if counter == 100:
                        refresh_connection()
                        counter = 0
                # c.increment_counter()
            except Exception as e:
                if self.principal:
                    refresh_connection()
                
                print("Wait and refresh ...")
                time.sleep(5)
                self.start()
        
        c.driver.quit()

    def get_history(self, key: str) -> object:
        logs = {}
        try:
            with open(self.log, 'r') as log_file:
                logs = json.load(log_file)
                return logs[key]
        except:
            return -1

    def set_history(self, key: str, value: object) -> None:
        log = {}
        try:
            if os.path.exists(self.log):
                with open(self.log, 'r') as log_file:
                    log = json.load(log_file)

            log[key] = value

            with open(self.log, 'w') as log_file:
                log_file.write(json.dumps(log, indent=4))
        except:
            return


class CampingInitializer(Scraping):

    def __init__(self, start_date: str, end_date: str) -> None:
        super().__init__(is_json=True, in_background=True)
        self.start_date = datetime.strptime(start_date, "%d/%m/%Y")
        self.end_date = datetime.strptime(end_date, "%d/%m/%Y")
        self.base_urls = []
        self.data = []
    
    def prepare(self, url) -> None:
        print("Préparation ...")
        dates_saturday = [date.to_pydatetime().strftime("%Y-%m-%d") for date in pd.bdate_range(start=self.start_date, end=self.end_date, freq="C", weekmask='Sat')]
        dates_sunday = [date.to_pydatetime().strftime("%Y-%m-%d") for date in pd.bdate_range(start=self.start_date, end=self.end_date, freq="C", weekmask='Sun')]
        dates = dates_saturday + dates_sunday

        for date in dates:
            self.base_urls.append(url + f"?checkInDate={date}&accommodation_types%5B0%5D=mobile_home&accommodation_types%5B1%5D=bungalow&region=18&type=region")
        
    def initialize(self) -> None:
        print("Récupération nombre de pages...")
        for url in self.base_urls:
            nb_page = self.get_page_length(url)
            url_paged = list(self.generate_url_with_page(url, nb_page))
            self.append_urls(url_paged)
    
    def append_urls(self, urls: list) -> None:
        current_list = [item for item in self.urls]
        current_list.extend(urls)
        self.set_urls(list(set(current_list)))

    def extract(self) -> None:

        soupe = BeautifulSoup(self.driver.page_source, 'lxml')

        params_url = parse_qs(urlparse(self.driver.current_url).query)
        url_date = params_url['checkInDate'][0]
        
        results = soupe.find('div', class_="dca-results__list").find_all('section', class_='dca-result--product') \
            if soupe.find('div', class_="dca-results__list").find_all('section', class_='dca-result--product') else []
        
        if not len(results):
            results = soupe.find('div', {'class': 'dca-results__list'}).find_all('div', {'class': 'dca-product-card'}) \
                if soupe.find('div', {'class': 'dca-results__list'}) and soupe.find('div', {'class': 'dca-results__list'}).find_all('div', {'class': 'dca-product-card'}) else []
    
        print(len(results))

        for result in results:
            url = 'https://www.campings.com' + result.find('a', href=True)['href'].split('?')[0]
            link = url + f'?checkInDate={url_date}&night=7'
            self.data.append(link)
            
    def save(self) -> None:
        current_data = []
        print(len(self.data))

        if os.path.exists(self.storage_file):
            with open(self.storage_file, 'r') as openfile:
                current_data = json.load(openfile)

        current_data.extend(self.data)
        current_data = list(set(current_data))
        json_object = json.dumps(current_data, indent=4)
        print(len(current_data))

        with open(self.storage_file, 'w') as outfile:
            outfile.write(json_object)

    def get_page_length(self, url:str) -> int:
        self.set_url(url)
        self.navigate()
        soupe = BeautifulSoup(self.driver.page_source, 'lxml')
        page_length = len(soupe.find_all('li', class_='dca-pagination__page-item')) \
            if soupe.find_all('li', class_='dca-pagination__page-item') else 1
        return page_length

    def generate_url_with_page(self, url:str, page:int) -> object:
        for i in range(1, (page + 1)):
            yield url + f"&page={i}"


def camping_main():

    dotenv.load_dotenv()

    data_folder = os.environ.get('STATICS_FOLDER')
    log_folder = os.environ.get('LOGS')
    output_folder = os.environ.get('OUTPUT_FOLDER')
    

    args = main_arguments()

    if args.action and args.action == 'init':
        
        miss = check_arguments(args, ['-b', '-e', '-s', '-d'])

        if not len(miss):
            regions = []

            with open(f"{data_folder}/{args.stations}", 'r') as openfile:
                regions = json.load(openfile)

            for region in regions:
                c = CampingInitializer(args.start_date, args.end_date)
                c.prepare(region)
                c.set_storage(f"{data_folder}/{args.destinations}")
                c.initialize()
                print("Récupération des destinations ...")
                c.execute()
            
        else:
            raise Exception(f"Argument(s) manquant(s): {', '.join(miss)}")

    if args.action and args.action == 'start':
        miss = check_arguments(
            args, ['-d', '-n'])

        if not len(miss):
            date_scrap = args.date_price
            
            c = CampingScraper()

            output_path = f"{output_folder}/campings/{date_scrap.replace('/', '_')}"
            log_path = f"{log_folder}/campings/{date_scrap.replace('/', '_')}"

            if not os.path.exists(output_path):
                os.makedirs(output_path)
        
            if not os.path.exists(log_path):
                os.makedirs(log_path)

            c.set_week_scrap(date_scrap)
            c.set_destinations(f"{data_folder}/{args.destinations}")
            c.set_log(f'{log_path}/{args.name}')
            c.set_output(f'{output_path}/{args.name}')

            if args.principal:
                c.set_to_principal()

            c.start()

        else:
            raise Exception(f"Argument(s) manquant(s): {', '.join(miss)}")

    if args.action and args.action == 'uploadcsv':
        miss = check_arguments(args, ['-f','-st', '-l'])

        if not len(miss):
            up = CSVUploader(freq=args.frequency, source=args.storage, log=args.log, site='campings', site_url = 'https://www.campings.com')
            up.upload()

        else:
            raise Exception(f"Argument(s) manquant(s): {', '.join(miss)}")   
