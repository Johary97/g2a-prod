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


class AnnonceCamping(Scraping):
    def __init__(self) -> None:
        super().__init__()
        self.data_extension = 'csv'
        self.week_scrap = ''
        self.website_name = 'campings'
        self.website_url = 'www.campings.com'

    def set_week_scrap(self, date: str) -> None:
        self.week_scrap = date

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

            return datetime.strftime(datetime.strptime(f"{date_split[2]}/{months[date_split[3]]}/2023", '%d/%m/%Y'), '%d/%m/%Y') 

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
                date_1 = extract_dates(dates_string)
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
            sys.exit("Arrêt!")


class CampingScraper(Scraper):
    def __init__(self,) -> None:
        super().__init__()
        self.urls = []
        self.storage = ''
        self.log = ''
        self.week_scrap = ''

    def set_destinations(self, filename: str) -> None:
        with open(filename, 'r') as infile:
            self.urls = json.load(infile)

    def set_log(self, log):
        self.log = log

    def set_week_scrap(self, date: str) -> None:
        self.week_scrap = date
    
    def start(self) -> None:
        c = AnnonceCamping()
        c.set_week_scrap(self.week_scrap)
        last_index = self.get_history('last_index')
        c.set_driver_interval(300, 500)
        for index in range(last_index + 1, len(self.urls)):
            try:
                print(index+1, ' / ', len(self.urls))
                c.set_url(self.urls[index])
                c.scrap()
                time.sleep(5)
                c.extract()
                c.save()
                self.set_history('last_index', index)
                # c.increment_counter()
            except Exception as e:
                print(e)
                c.driver.quit()
                break
        
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
        super().__init__()
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
            print()
            nb_page = self.get_page_length(url)
            url_paged = list(self.generate_url_with_page(url, nb_page))
            self.append_urls(url_paged)
    
    def append_urls(self, urls: list) -> None:
        current_list = [item for item in self.urls]
        current_list.extend(urls)
        self.set_urls(list(set(current_list)))

    def extract(self) -> None:

        soupe = BeautifulSoup(self.driver.page_source, 'lxml')
        results = soupe.find('div', class_="dca-results__list").find_all('section', class_='dca-result--product') \
            if soupe.find('div', class_="dca-results__list").find_all('section', class_='dca-result--product') else []

        params_url = parse_qs(urlparse(self.driver.current_url).query)
        url_date = params_url['checkInDate'][0]

        if results:
            for result in results:
                url = 'https://www.campings.com' + result.find('a', href=True)['href'].split('?')[0]
                link = url + f'?checkInDate={url_date}&night=7'
                self.data.append(link)
            
    def save(self) -> None:
        current_data = []

        if os.path.exists(self.storage_file):
            with open(self.storage_file, 'r') as openfile:
                current_data = json.load(openfile)

        current_data.extend(self.data)
        current_data = list(set(current_data))
        json_object = json.dumps(current_data, indent=4)

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
            args, ['-l', '-d'])

        if not len(miss):
            date_scrap = args.date_price
            
            c = CampingScraper()

            log_path = f"{log_folder}/campings/{date_scrap.replace('/', '_')}"

            if not os.path.exists(log_path):
                os.makedirs(log_path)

            c.set_week_scrap(date_scrap)
            c.set_destinations(f"{data_folder}/{args.destinations}")
            c.set_log(f"{log_path}/{args.log}")
            c.start()

        else:
            raise Exception(f"Argument(s) manquant(s): {', '.join(miss)}")
