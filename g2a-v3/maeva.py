import argparse
from csv import writer
from datetime import datetime, timedelta
from random import randint
import sys
import threading
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import ElementNotVisibleException, ElementNotSelectableException
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import re
from langdetect import detect
from abc import ABC, abstractmethod
import dotenv
import os
import json
from selenium.webdriver.common.keys import Keys
import socket
from selenium.webdriver.remote.command import Command
from scraping import Scraping
from tools.args import main_arguments, check_arguments
from tools.changeip import refresh_connection
from tools.g2a import CSVUploader, G2A

"""DestinationListMaeva: Classe utilisée pour récupérer la liste des destinations d'une station"""


class DestinationListMaeva(Scraping):

    def __init__(self, is_background=False):
        super().__init__(is_background)
        self.data_extension = 'json'
        self.station_key = None
        self.data = []

    def set_station_key(self, station_key):
        self.station_key = station_key

    def generate_url(self, page=1):
        for i in range(1, (page+1)):
            self.urls.append(
                f"https://www.maeva.com/fr-fr/searchlist.php?map=1&acces_direct=1&station_cle={self.station_key}&etendre_min=30&trier_par=zerank&page={i}")

    def get_page_length(self, page):
        soupe = BeautifulSoup(page, 'lxml')

        total = int(soupe.find(
            'div', {'id': 'sl-resultats-tri'}).text.strip().split(' ')[6])

        if total > 30:
            page_nb = (total // 30) if (total %
                                        30 == 0) else ((total // 30) + 1)
            return page_nb

        return 1

    def execute(self):
        try:
            self.generate_url()
            self.set_url(self.urls[0])

            self.navigate()
            page_length = self.get_page_length(self.driver.page_source)
            self.generate_url(page_length)
            self.scrap()
        except Exception as e:
            print(e)
            self.driver.quit()
            sys.exit("Arrêt!!!")

    def scrap(self):
        for index in range(0, len(self.urls)):
            print(f"Page: {index + 1}/{len(self.urls)}")
            try:
                self.driver.get(self.urls[index])
            #     WebDriverWait(self.driver, 10)
                time.sleep(1)
                self.extract()
                self.save()
            except Exception as e:
                print(e)
                self.driver.quit()
                self.alive = False
                self.execute()

    def extract(self):

        soupe = BeautifulSoup(self.driver.page_source, 'lxml')
        toasters = soupe.find('div', {'id': 'sl-toaster-container'}).find_all(
            'div', class_='toaster') if soupe.find('div', {'id': 'sl-toaster-container'}) else []

        for toast in toasters:
            if toast.find('div', class_='toaster-residence-libelle') and toast.find('div', class_='toaster-residence-libelle').find('a', href=True):
                link = toast.find(
                    'div', class_='toaster-residence-libelle').find('a')['href']
                if not link.startswith('/pages'):
                    self.data.append('https://maeva.com' + link)

    def save(self):
        current_list = []

        if os.path.exists(self.storage_file):
            with open(self.storage_file, 'r') as openfile:
                current_list = json.load(openfile)

        current_data = list(set([item for item in current_list + self.data]))

        json_object = json.dumps(current_data, indent=4)

        with open(self.storage_file, 'w') as outfile:
            outfile.write(json_object)


"""AnnonceMaeva: Classe utilisée pour scraper les annonces trouvé avec une url."""


class AnnonceMaeva(Scraping):

    def __init__(self):
        super().__init__(in_background=True)
        self.data = []
        self.data_extension = 'csv'
        self.price_date = ''
        self.website_name = "maeva"
        self.website_url = "https://www.maeva.com"
        self.principal = False
        self.stations = {}
        self.init_station_list()

    def execute(self):
        try:
            self.create_file()
            return self.scrap()
        except Exception as e:
            print(e)
            self.driver.quit()
            self.alive = False
            sys.exit("Arrêt !!!")

    def scrap(self):
        try:
            self.driver.get(self.url)
            WebDriverWait(self.driver, randint(0, 2))
            time.sleep(2)
            while True:
                try:
                    load_btn = self.driver.find_element(
                        By.ID, "toaster-cta-voir-plus")
                    if load_btn:
                        self.driver.execute_script(
                            "arguments[0].click();", load_btn)
                        time.sleep(2)
                except:
                    break

            self.extract()

            print("Saving ...")
            self.save()
            self.save_data()
        except Exception as e:
            print(e)
            if self.principal:
                refresh_connection()
                
            print("Wait and refresh ...")
            time.sleep(5)
            self.scrap()

    def init_station_list(self):
        g2a_instance = G2A(entity="regions")
        print("Initialisation liste stations ...")

        page = 1

        while True:
            g2a_instance.set_page(page)
            results = g2a_instance.execute().json()

            if len(results) == 0:
                break

            for x in results:
                if x['website'] in ['/api/websites/1', '/api/websites/14']:
                    if x['name'] != '' and x['name'] not in self.stations.keys():
                        self.stations[x['name']] = x['region_key']

            page += 1

    def set_price_date(self, price_date):
        self.price_date = price_date

    def set_to_principal(self):
        self.principal = True

    def extract(self):
        def link_params(url):
            url_params = parse_qs(urlparse(url).query)
            sep = '/'
            try:
                n_offre = sep.join(url_params['id'][0].split('-')[::-1])
                start_date = sep.join(
                    url_params['date_debut'][0].split('-')[::-1])
                end_date = sep.join(url_params['date_fin'][0].split('-')[::-1])
                return n_offre, start_date, end_date
            except KeyError as e:
                print(e)
                return

        self.data = []

        soupe = BeautifulSoup(self.driver.page_source, 'lxml')

        if soupe.find('div', class_='fiche-seo-toaster-container'):
            toasters = soupe.find('div', class_='fiche-seo-toaster-container').find_all(
                'div', class_='toaster') if soupe.find('div', class_='fiche-seo-toaster-container') else []
            residence = soupe.find('h1', {"id": "fiche-produit-residence-libelle"}).text.strip() \
                if soupe.find('h1', {"id": "fiche-produit-residence-libelle"}) else ''
            localisation = soupe.find('div', {"id": "fiche-produit-localisation"}).find('span', class_='maeva-black').text.strip() \
                if soupe.find('div', {"id": "fiche-produit-localisation"}) else ''

            breadcrumbs = []
            
            try:
                breadcrumbs = soupe.find(
                    'ol', {'id': 'ui-ariane'}).find_all('li', {'itemprop': 'itemListElement'})
            except:
                breadcrumbs = soupe.find(
                    'nav', {'id': 'ui-ariane'}).find_all('div', {'itemprop': 'itemListElement'})

            station_breadcrumb = breadcrumbs[-2:-1][0].find('a', class_='ariane-item') if breadcrumbs[-2:-1][0].find('a', class_='ariane-item') else ''
            station_name = localisation
            station_key = station_breadcrumb['href'].split(',')[1].replace('.html', '') if station_breadcrumb != '' else ''

            if not station_key:
                station_key = self.stations[station_name.upper()] if station_name.upper() in self.stations.keys() else ''
                print(station_name, ' => ', station_key)

            for toaster in toasters:
                is_disponible = False if toaster.find(
                    'div', {'id': 'toaster-right-date'}).find('div', class_='font-logement-disabled') else True

                if is_disponible:
                    dat = {}
                    date_price = self.price_date

                    typologie = toaster.find('div', class_="toaster-residence-libelle-container").text.strip() \
                        if toaster.find('div', class_='toaster-residence-libelle-container') else ''
                    prix_actuel = toaster.find('div', class_="fiche-produit-prix-item").text.strip()[:-1] \
                        if toaster.find('div', class_="fiche-produit-prix-item") else 0.00
                    prix_init = toaster.find('span', class_="fiche-produit-prix-barre-item").text.strip()[:-1] \
                        if toaster.find('span', class_="fiche-produit-prix-barre-item") else prix_actuel
                    link = 'www.maeva.com' + toaster.find("div", class_="toaster-right-cta").find("a", href=True)['href'] \
                        if toaster.find("div", class_="toaster-right-cta") else ''

                    n_offres, date_debut, date_fin = link_params(link)
                    dat['web-scrapper-order'] = ''
                    dat['date_price'] = date_price
                    dat['date_debut'] = date_debut
                    dat['date_fin'] = date_fin
                    dat['prix_init'] = prix_init
                    dat['prix_actuel'] = prix_actuel
                    dat['typologie'] = typologie
                    dat['n_offre'] = n_offres
                    dat['nom'] = residence
                    dat['localite'] = localisation
                    dat['date_debut-jour'] = ''
                    dat['Nb semaines'] = datetime.strptime(
                        date_debut, '%d/%m/%Y').isocalendar()[1]
                    dat['cle_station'] = station_key
                    dat['nom_station'] = station_name
                    dat['url'] = 'https://www.maeva.com/pages/fiche.php?id=45956&date_debut=2023-07-01&date_fin=2023-07-07&p=fiche-produit-produit'

                    self.data.append(dat)


"""MaevaDestinationScraper: Classe utilisée pour scraper les annonces publiées sur les destinations """


class MaevaDestinationScraper:
    def __init__(self, dest_list_source, date_price):
        self.dests = {}
        self.destination_list = []
        self.principal = False

        if dest_list_source:
            with open(dest_list_source, 'r') as openfile:
                self.destination_list = json.load(openfile)

        self.first_date = None
        self.last_date = None
        self.log = ''
        self.date_price = date_price

    def set_interval(self, f_date, l_date):
        self.first_date = datetime.strptime(f_date, '%d/%m/%Y')
        self.last_date = datetime.strptime(l_date, '%d/%m/%Y')

    def set_log(self, log):
        self.log = f'{log}.json'

    def set_output(self, name):
        self.output = f'{name}.csv'

    def set_to_principal(self):
        self.principal = True

    def generate_urls(self, index=0):

        next_saturday = self.first_date

        urls = []
        base_url = self.destination_list[index]
        dest_id = self.destination_list[index].split('_')[1].split('.')[0]

        while next_saturday <= self.last_date:
            date_debut = datetime.strftime(next_saturday, '%Y-%m-%d')
            date_fin = datetime.strftime(
                next_saturday + timedelta(days=6), '%Y-%m-%d')
            urls.append(
                f"{base_url}?date_debut={date_debut}&date_fin={date_fin}&residence_cle={dest_id}&formule=0&ordreSeo=prixAsc")
            next_saturday += timedelta(days=7)

        return urls

    def save_history(self, index, log_key):
        logs = {}

        try:
            with open(self.log, 'r') as openfile:
                logs = json.load(openfile)
        except Exception as e:
            print(e)
            pass

        logs[log_key] = index

        with open(self.log, 'w') as outfile:
            outfile.write(json.dumps(logs, indent=4))

    def load_history(self, log_key):
        try:
            with open(self.log, 'r') as openfile:
                logs = json.load(openfile)
                return logs[log_key] if log_key in logs.keys() else -1
        except:
            return -1

    def start(self):
        last_index = self.load_history('last_destination_index')
        
        if self.principal:
            refresh_connection()

        counter = 0

        try:
            instance = AnnonceMaeva()
            instance.set_price_date(self.date_price)
            instance.set_storage(self.output)

            if self.principal:
                instance.set_to_principal()

            for index in range(last_index+1, len(self.destination_list)):
                print(
                    f"Destination {index+1}/{len(self.destination_list)}:", self.destination_list[index])

                urls = self.generate_urls(index)

                for url in urls:
                    print(f"Week {urls.index(url)+1}/{len(urls)}")
                    instance.set_url(url)
                    instance.execute()

                    if self.principal:
                        counter += 1
                        if counter == 50:
                            refresh_connection()
                            counter = 0

                self.save_history(index, 'last_destination_index')

            instance.driver.quit()

        except Exception as e:
            print(e)
            sys.exit("Arrêt !")


"""MaevaDestinationInitializer: Classe utilisée pour initialiser les listes de destinations"""


class MaevaDestinationInitializer:

    def __init__(self, dest_list_source=False, station_list_source=False):
        self.destination_list = []
        self.dests = {}
        self.stations = []
        self.scrap_list = []
        self.dest_source = dest_list_source

        if self.dest_source and station_list_source:
            with open(station_list_source, 'r') as openfile:
                self.stations = json.load(openfile)

        self.data_file = 'annonce.json'
        self.log = 'logs.json'
        self.principal = False

    def set_log(self, log):
        self.log = f'{log}.json'

    def set_to_principal(self):
        self.principal = True

    def save_history(self, index, log_key):
        logs = {}

        try:
            with open(self.log, 'r') as openfile:
                logs = json.load(openfile)
        except:
            pass

        logs[log_key] = index

        with open(self.log, 'w') as outfile:
            outfile.write(json.dumps(logs, indent=4))

    def load_history(self, log_key):
        try:
            with open(self.log, 'r') as openfile:
                logs = json.load(openfile)
                return logs[log_key] if log_key in logs.keys() else -1
        except:
            return -1

    def start(self):
        instance = DestinationListMaeva(is_background=True)
        last_index = self.load_history('station_index')

        if self.principal:
            refresh_connection()

        counter = 0

        try:

            for index in range(last_index+1, len(self.stations)):
                key = self.stations[index]
                print(f"station {key} : {index+1}/{len(self.stations)}")
                instance.set_station_key(key)
                instance.set_storage(self.dest_source)
                instance.execute()
                self.save_history(index, 'station_index')

                if self.principal:
                    counter += 1
                    if counter == 50:
                        refresh_connection()
                        counter = 0

            instance.driver.quit()

        except Exception as e:
            print(e)
            instance.driver.quit()
            sys.exit("Adresse IP bani!")

    def remove_duplicates(self):
        dests = {}
        checked_dests = set()

        with open(self.dest_source, 'r') as openfile:
            self.dests = json.load(openfile)

        for [key, value] in self.dests.items():
            key_dests = []

            for dest in value:
                if dest not in checked_dests:
                    checked_dests.add(dest)
                    key_dests.append(dest)
                else:
                    checked_dests.add(dest)

            dests[key] = key_dests

        with open('destinations_3.json', 'w') as outfile:
            outfile.write(json.dumps(dests, indent=4))

    def is_done(self, url):
        last_scraped_urls = self.load_history('last_scraped_urls')
        return url in last_scraped_urls


class MaevaCleaner(object):

    def __init__(self, folder: str, week_scrap: str) -> None:
        self.week_scrap = week_scrap
        self.folder = folder

    def clean(self) -> bool:
        csv_list = []

        csv_headers = pd.DataFrame(columns=[
            'web-scraper-order',
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

        all_dirsfiles = os.listdir(self.folder)
        csv_files = list(filter(lambda f: f.endswith('.csv'), all_dirsfiles))
        csv_files = [f"{self.folder}/{x}" for x in csv_files]

        for file in csv_files:
            csv_list.append(pd.read_csv(file, encoding="latin-1"))

        csv_merged = pd.concat(csv_list)
        csv_merged = csv_merged.sort_values(inplace=True, ascending=True, by=[
            'Nb semaines', 'date_debut'])
        csv_merged = csv_merged.drop_duplicates(subset=['date_price', 'date_debut', 'date_fin',
                                                        'prix_init', 'prix_actuel', 'typologie', 'n_offre', 'nom', 'localite'])
        csv_merged.to_csv(
            f'{self.folder}/cleaned/maeva_cleaned_{self.week_scrap}.csv', index=False)


def maeva_main():

    dotenv.load_dotenv()

    data_folder = os.environ.get('STATICS_FOLDER')
    log_folder = os.environ.get('LOGS')
    output_folder = os.environ.get('OUTPUT_FOLDER')

    args = main_arguments()

    date_scrap = args.date_price

    log_path = f"{log_folder}/maeva/{date_scrap.replace('/', '_')}"
    output_path = f"{output_folder}/maeva/{date_scrap.replace('/', '_')}"

    if not os.path.exists(log_path):
        os.makedirs(log_path)

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    if args.action and args.action == 'init':

        miss = check_arguments(args, ['-d', '-s', '-n'])

        if not len(miss):

            m = MaevaDestinationInitializer(
                f'{data_folder}/{args.destinations}', f'{data_folder}/{args.stations}')
            m.set_log(f'{log_path}/d_{args.name}')

            if args.principal:
                m.set_to_principal()
            
            m.start()

        else:
            raise Exception(f"Argument(s) manquant(s): {', '.join(miss)}")

    if args.action and args.action == 'start':

        miss = check_arguments(args, ['-d', '-b', '-e', '-n'])

        if not len(miss):

            m = MaevaDestinationScraper(
                f'{data_folder}/{args.destinations}', args.date_price)
            m.set_interval(args.start_date, args.end_date)
            m.set_log(f'{log_path}/{args.name}')
            m.set_output(f'{output_path}/{args.name}')
            if args.principal:
                m.set_to_principal()

            m.start()

        else:
            raise Exception(f"Argument(s) manquant(s): {', '.join(miss)}")

    if args.action and args.action == 'uploadcsv':
        miss = check_arguments(args, ['-f','-st', '-l'])

        if not len(miss):
            up = CSVUploader(freq=args.frequency, source=args.storage, log=args.log, site='maeva', site_url = 'https://www.maeva.com')
            up.upload()

        else:
            raise Exception(f"Argument(s) manquant(s): {', '.join(miss)}")   
