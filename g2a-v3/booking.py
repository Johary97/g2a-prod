from scraping import Scraping, Scraper
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import tools.ordergenerator as og
from urllib.parse import urlparse, parse_qs
import os
import pandas as pd
import dotenv
from csv import writer
import time
from random import randrange
import argparse
from tools.args import main_arguments, check_arguments
import sys
import json
from tools.changeip import refresh_connection
import csv
from tools.g2a import G2A, CSVUploader


class AnnonceBooking(Scraping):

    def __init__(self, in_background: bool = False) -> None:
        super().__init__(in_background)

        self.data_extension = 'csv'
        self.week_scrap = ''
        self.code = ''
        self.order_index = 0
        self.website_name = "booking"
        self.website_url = "https://www.booking.com"

    def set_week_scrap(self, date: str) -> None:
        self.week_scrap = date

    def set_code(self, code: str) -> None:
        self.code = code

    def get_dates(self, url: str) -> tuple:
        """ function to get dates in url """
        url_params = parse_qs(urlparse(url).query)
        try:
            sep = '/'
            return sep.join(url_params['checkin'][0].split('-')[::-1]), sep.join(url_params['checkout'][0].split('-')[::-1])
        except KeyError:
            return

    def extract(self) -> None:
        data = []

        while True:
            time.sleep(randrange(2, 4, 1))
            soupe = BeautifulSoup(self.driver.page_source, 'lxml')

            header = soupe.find('div', {'data-component': 'arp-header'}).find('h1').text.strip() if soupe.find('div', {'data-component': 'arp-header'}) else soupe.find('h1', {'class': 'fcab3ed991'}).text.strip()
            region_name = header.split(':')[0]
            region_key = parse_qs(urlparse(self.driver.current_url).query)['dest_id'][0]

            cards = soupe.find_all('div', {'data-testid': "property-card"})

            for card in cards:
                nom = card.find('div', {'data-testid': "title"}).text.replace('\n', '').replace(',', '-').replace('"', '\'') \
                    if card.find('div', {'data-testid': "title"}) else ''
                localite = card.find('span', {'data-testid': "address"}).text.replace('\n', '') \
                    if card.find('span', {'data-testid': "address"}) else ''
                prix_actuel = int(card.find('span', {'data-testid': 'price-and-discounted-price'}).text[2:].replace(' ', '')) \
                    if card.find('span', {'data-testid': 'price-and-discounted-price'}) else 0
                prix_init = card.find('span', class_='c5888af24f').text[2:].replace(' ', '') \
                    if card.find('span', class_='c5888af24f') else prix_actuel
                
                typologie = card.find('span', class_="df597226dd").text.replace('\n', '') \
                    if card.find('span', class_="df597226dd") else ''
                date_prix = self.week_scrap
                date_debut, date_fin = self.get_dates(self.driver.current_url)
                self.order_index += 1

                data.append({
                    'web-scrapper-order': og.get_fullcode(self.code, self.order_index),
                    'date_price': date_prix,
                    'date_debut': date_debut,
                    'date_fin': date_fin,
                    'prix_init': prix_init,
                    'prix_actuel': prix_actuel,
                    'typologie': typologie,
                    'n_offre': '',
                    'nom': nom,
                    'localite': localite,
                    'date_debut-jour': '',
                    'Nb semaines': datetime.strptime(date_debut, '%d/%m/%Y').isocalendar()[1],
                    'cle_station': region_key,
                    'nom_station': region_name,
                    'url': self.driver.current_url
                })

            next_btn = soupe.find(
                'button', {'aria-label': 'Page suivante', 'disabled': False})

            if next_btn:
                next_btn_selenium = self.driver.find_element(
                    By.XPATH, "//button[@aria-label='Page suivante']")
                self.driver.execute_script(
                    "arguments[0].click();", next_btn_selenium)
            else:
                break

        if data:
            self.data = data
        else:
            self.data = []


class BookingScraper(Scraper):

    def __init__(self, name, start, end, freq):
        self.name = name
        self.destids = []
        self.start_date = start
        self.end_date = end
        self.frequency = freq
        self.urls = []
        self.week_scrap = ''
        self.code = og.create_code()
        self.set_logfile()
        self.max_cycle = 140

    def get_next_monday(self):
        next_monday = datetime.now() + timedelta(7 - datetime.now().weekday() or 7)
        return next_monday.strftime('%d/%m/%Y')

    def set_week_scrap(self, date: str) -> None:
        self.week_scrap = date

    def generate_url(self, checkin: str, checkout: str, dest_id: str) -> str:
        return f"https://www.booking.com/searchresults.fr.html?label=gog235jc-1DCAYoTUIGc2F2b2llSA1YA2hNiAEBmAENuAEXyAEM2AED6AEB-AECiAIBqAIDuAK37uOQBsACAdICJDJjMjgxMmVhLTIyM2MtNDI1Mi1iYTM4LTA3MmE4MjI3MWFkMdgCBOACAQ&sid=086e078aef1832684e5d5671c99a12b1&aid=356980&dest_id={dest_id}&dest_type=region&nflt=ht_id%3D204%3Brpt%3D1&shw_aparth=0&checkin={checkin}&checkout={checkout}&selected_currency=EUR"

    def set_destids(self, filename):
        df = pd.read_csv(f"{os.environ.get('STATICS_FOLDER')}/{filename}")
        self.destids = df['dest_id']

    def initialize(self) -> None:

        if not self.week_scrap:
            self.week_scrap = self.get_next_monday()

        checkin_date = datetime.strptime(self.start_date, "%d/%m/%Y")
        checkout_date = datetime.strptime(self.end_date, "%d/%m/%Y")
        date_space = int((checkout_date - checkin_date).days) + 1

        checkin = datetime.strptime(self.start_date, "%d/%m/%Y")
        checkout = checkin + timedelta(days=int(self.frequency))

        for i in range(date_space):
            for dest_id in self.destids:
                self.urls.append(self.generate_url(checkin.strftime(
                    "%Y-%m-%d"), checkout.strftime("%Y-%m-%d"), str(dest_id)))
            checkin += timedelta(days=1)
            checkout += timedelta(days=1)

    def start(self) -> None:
        refresh_connection()
        instance = AnnonceBooking()
        instance.set_week_scrap(self.week_scrap)
        instance.set_nights(self.frequency)

        last_scraped = self.get_history('last_scraped')
        counter = 0

        for last_url in range(last_scraped + 1, len(self.urls)):
            try:
                print(f"Progress: {last_url}/{len(self.urls)}")
                instance.set_url(self.urls[last_url])
                instance.set_code(self.code)
                instance.scrap()
                instance.extract()
                instance.save()
                counter += 1
                self.set_history('last_scraped', last_url)
            except Exception as e:
                print(e)
                break
            if counter == self.max_cycle:
                refresh_connection()
                counter = 0

        last_url = self.get_history('last_scraped')
        
        if last_url < len(self.urls) - 1:
            self.start()

    def get_history(self, key: str) -> object:
        logs = {}
        try:
            with open(self.log, 'r') as log_file:
                logs = json.load(log_file)
                return logs[key]
        except:
            return -1

    def set_history(self, key: str, value: int) -> None:
        log = {}
        if os.path.exists(self.log):
            try:
                with open(self.log, 'r') as log_file:
                    log = json.load(log_file)
            except:
                pass

        log[key] = value

        with open(self.log, 'w') as log_file:
            log_file.write(json.dumps(log, indent=4))

    def set_logfile(self):
        logpath = f"{os.environ.get('LOGS')}/booking/{self.week_scrap.replace('/', '_')}/{self.frequency}j"
        logfile = f"{logpath}/{self.name}_{self.frequency}j_{self.start_date.replace('/', '_')}-{self.end_date.replace('/', '_')}.json"

        if not os.path.exists(logpath):
            os.makedirs(logpath)

        self.log = logfile

    def set_cycle(self, number) -> None:
        self.max_cycle = number


class CleanBooking(object):

    def __init__(self, freq: object, folder: str, start_date: str, end_date: str, sources: list) -> None:
        self.freq = freq
        self.folder = folder
        self.start_date = start_date
        self.end_date = end_date
        self.sources = sources

    def check_dates(self, dates: list) -> None:
        all_dates = []
        start = datetime.strptime(self.start_date, '%d/%m/%Y')
        end = datetime.strptime(self.end_date, '%d/%m/%Y')
        index_date = start

        retrieve_dates = set()

        while index_date <= end:
            all_dates.append(index_date.strftime('%d/%m/%Y'))
            index_date = index_date + timedelta(days=1)

        for d in dates:
            if d in all_dates:
                retrieve_dates.add(d)

        missing_dates = []

        for d in all_dates:
            if d not in list(retrieve_dates):
                missing_dates.append(d)

        return missing_dates

    def set_interval(self, start_date: str, end_date: str) -> None:
        self.start_date = start_date
        self.end_date = end_date

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

        for file in self.sources:
            csv_list.append(pd.read_csv(file, encoding="latin-1"))

        csv_merged = pd.concat(csv_list)
        csv_merged = csv_merged.sort_values(inplace=True, ascending=True, by=[
            'Nb semaines', 'date_debut'])
        csv_merged = csv_merged.drop_duplicates(subset=['date_price', 'date_debut', 'date_fin',
                                                        'prix_init', 'prix_actuel', 'typologie', 'n_offre', 'nom', 'localite'])

        m_dates = self.check_dates(
            csv_merged['date_debut'].tolist(), self.start_date, self.end_date)
        m_dates = []

        if len(m_dates):
            print(f"Dates manquantes:")
            [print(f"->\t{date}") for date in m_dates]
            return False

        else:
            start_date = self.start_date.replace('/', '_')
            end_date = self.end_date.replace('/', '_')
            csv_merged.to_csv(
                f'{self.folder}/booking_{self.freq}j_cleaned_{start_date}_{end_date}.csv', index=False)
            return True


def booking_main():

    dotenv.load_dotenv()

    log_folder = os.environ.get('LOGS')

    args = main_arguments()

    if args.action and args.action == 'clean':
        miss = check_arguments(args, ['-d', '-st', '-l'])

        if not len(miss):
            pass

        else:
            raise Exception(f"Argument(s) manquant(s): {', '.join(miss)}")

    if args.action and args.action == 'uploadcsv':
        miss = check_arguments(args, ['-f','-st', '-l'])

        if not len(miss):
            up = CSVUploader(freq=args.frequency, source=args.storage, log=args.log, site='booking', site_url = 'https://www.booking.com')
            up.upload()

        else:
            raise Exception(f"Argument(s) manquant(s): {', '.join(miss)}")        

    if args.action and args.action == 'start':
        miss = check_arguments(
            args, ['-n', '-b', '-e', '-l', '-f', '-d'])

        if not len(miss):
            date_scrap = args.date_price

            b = BookingScraper(args.name,
                               args.start_date,
                               args.end_date,
                               args.frequency)
            b.set_destids(args.destinations)
            b.set_week_scrap(args.date_price)

            if args.cycle:
                b.set_cycle(int(args.cycle))

            b.initialize()
            b.start()

        else:
            raise Exception(f"Argument(s) manquant(s): {', '.join(miss)}")
