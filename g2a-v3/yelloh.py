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
import pandas as pd
from urllib.parse import urlparse, parse_qs
from scraping import Scraping, Scraper
from tools.args import main_arguments, ARGS_INFO, check_arguments
import dotenv

SEARCH_BTN = "#mm-1 > div.main > div:nth-child(2) > header > div.Header-container.Container > div:nth-child(1) > button:nth-child(3)"
SEARCH_OPTIONLIST = "#mm-1 > div.main > div:nth-child(2) > header > div.Header-search > div > form > div.Search-wrapper.Search-wrapper--larger > div.Search-autocompleteDropdown > div.Search-autocompleteBox.Search-autocompletePart > div > button"
SEARCH_FIRSTOPTION = "#mm-1 > div.main > div:nth-child(2) > header > div.Header-search > div > form > div.Search-wrapper.Search-wrapper--larger > div.Search-autocompleteDropdown > div.Search-autocompleteBox.Search-autocompletePart > div > button"
SEARCH_PERSONFILTER = "#mm-1 > div.main > div:nth-child(2) > header > div.Header-search > div > form > div.Search-wrapper.Search-wrapper--small > div.Select.Search-select > ul > li:nth-child(2)"
SEARCH_SUBMIT = "#mm-1 > div.main > div:nth-child(2) > header > div.Header-search > div > form > button"
SEARCH_RESULT = "#map-container > section.CampingList > div > section.CampingList-subsection.CampingList-subsection--strict"


class YellohDestinationScraper(Scraping):

    def __init__(self, dest_location: str, in_background: bool = False) -> None:
        super().__init__(in_background)
        self.dest_location = dest_location
        self.data_extension = 'json'
        self.key_index = 0
        self.search_keys = [
            "Provence-Alpes-Côte d’Azur",
            "Languedoc-Roussillon",
            "Corse",
            "Poitou-Charentes",
            "Rhône-Alpes",
            "Midi-Pyrénées",
            "Auvergne",
            "Picardie",
            "Bourgogne"
        ]
        self.scrap_finished = False
        self.navigate_init_page()

    def navigate_init_page(self) -> None:
        self.driver.get("https://www.yellohvillage.fr/destination/mer")
        WebDriverWait(self.driver, 10)
        self.close_popup()

    def set_index(self) -> None:
        if len(self.search_keys) > self.key_index:
            self.key_index += 1
        else:
            print("All key index visited")
            self.scrap_finished = True

    def close_popup(self) -> None:
        try:
            self.driver.find_element(
                By.ID, 'didomi-notice-agree-button').click()
        except:
            pass

    def setup_search(self) -> None:
        print("Setup search")
        global SEARCH_BTN
        global SEARCH_OPTIONLIST
        global SEARCH_FIRSTOPTION
        global SEARCH_RESULT
        global SEARCH_PERSONFILTER

        try:
            self.driver.find_element(By.CSS_SELECTOR, SEARCH_BTN).click()
            time.sleep(randint(1, 3))
            self.driver.find_element(By.ID, 'searchText').send_keys(
                self.search_keys[self.key_index])
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, SEARCH_OPTIONLIST)))
            self.driver.find_element(By.CSS_SELECTOR, SEARCH_FIRSTOPTION).click()
            time.sleep(1)
            self.driver.find_element(By.ID, 'personnesInput').click()
            time.sleep(1)
            self.driver.find_element(By.CSS_SELECTOR, SEARCH_PERSONFILTER).click()
            self.driver.find_element(By.CSS_SELECTOR, SEARCH_SUBMIT).click()
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, SEARCH_RESULT))
            )
        except Exception as e:
            print("An error occured!!!!")
            print(e)

    def extract(self) -> None:
        print("Extracting")
        try:
            print(self.driver.current_url)
            soupe = BeautifulSoup(self.driver.page_source, 'lxml')
            campings = soupe.find(
                'div', class_="CampingList-masonry").find_all('article', class_="Camping")
            print(f"==> {len(campings)} destinations found")
            for i in range(len(campings)):
                self.data.append("https://www.yellohvillage.fr" +
                                campings[i].find('a', class_="Camping-btn--location", href=True)['href'])
        except Exception as e:
            print("Extraction error")
            print(e)

    def save_dests(self) -> None:
        current_list = []
        print("Saving")

        try:

            if os.path.exists(self.dest_location):
                with open(self.dest_location, 'r') as openfile:
                    current_list = json.load(openfile)

            current_data = list(set([item for item in current_list + self.data]))
            json_object = json.dumps(current_data, indent=4)

            with open(self.dest_location, "w") as dest_file:
                dest_file.write(json_object)
            self.dests = []

        except Exception as e:
            print(e)

    def execute(self) -> None:
        print("Executing")
        try:
            while not self.scrap_finished:
                self.setup_search()
                self.extract()
                self.save_dests()
                self.set_index()
                self.navigate_init_page()
            print("Yelloh destination scraped !")
        except:
            pass


class AnnonceYellohScraper(Scraping):

    def __init__(self) -> None:
        super().__init__()

        self.file_extension = 'csv'
        self.week_scrap = ''
        self.website_name = 'yellow_village'
        self.website_url = 'www.yellohvillage.fr'
        self.scrap_finished = False
        self.data_container = []
        self.navigate_init_page()

    def navigate_init_page(self) -> None:
        self.driver.get("https://www.yellohvillage.fr/destination/mer")
        WebDriverWait(self.driver, 10)
        self.close_popup()

    def close_popup(self) -> None:
        try:
            self.driver.find_element(
                By.ID, 'didomi-notice-agree-button').click()
        except:
            pass

    def set_week_scrap(self, date: str) -> None:
        self.week_scrap = date

    def set_dates(self, start_date: str, end_date: str):
        self.driver.execute_script(
            f"window.localStorage.setItem('date_start', {start_date});)")
        self.driver.execute_script(
            f"window.localStorage.setItem('date_end', {end_date});)")
        self.driver.execute_script("window.location.reload();")

    def extract(self) -> None:
        soupe = BeautifulSoup(self.driver.page_source, "lxml")
        accomodationContainer = soupe.find('section', class_='AccommodationList').find(
            'ul', 'Container-accommodation')
        accomodations = accomodationContainer.find_all(
            'article', class_='AccomodationBlock')

        for accomodation in accomodations:
            data = {}
            data["web_scraper_order"] = ""
            data["name"] = soupe.find(
                'span', class_="SectionHeadVillage-name").text.strip()
            data["locality"] = soupe.find(
                'p', class_="SectionHeadVillage-location").text.strip()
            data["date_price"] = datetime.now().strftime("%d/%m/%Y")
            data["date_debut"] = self.driver.execute_script(
                "return window.localStorage.getItem('date_start');")
            data["date_fin"] = self.driver.execute_script(
                "return window.localStorage.getItem('date_end');")
            data["prix_actuel"] = re.sub(r"[^(\d)]", '', accomodation.find(
                "p", class_="PriceTag-finalPrice").text.strip())
            data["prix_init"] = data["prix_actuel"]
            data["n_offres"] = re.sub(r"[^(\d)]", '', accomodation.find(
                "a", class_="AccomodationBlock-actionBtn", href=True)["href"])
            data["date_debut_jour"] = ""
            data["typologie"] = accomodation.find(
                "div", class_="AccommodationDetails-characs--persons").text.strip()
            data["nb_semaine"] = ""
            self.data_container.append(data)

    def save(self):
        pass


def yelloh_main():
    dotenv.load_dotenv()

    data_folder = os.environ.get('STATICS_FOLDER')

    args = main_arguments()
    date_scrap = args.date_price

    if args.action and args.action == 'init':

        miss = check_arguments(args, ['-d', '-l'])

        if not len(miss):
            y = YellohDestinationScraper(
                f'{data_folder}/{args.destinations}')
            y.set_logfile('yellohvillage', f'd_{args.log}', args.date_price)
            y.execute()

    if args.action and args.action == 'start':
        miss = check_arguments(args, ['-d', '-b', '-e', '-l'])

        if not len(miss):

            y = AnnonceYellohScraper(
                f'{data_folder}/{args.destinations}', args.date_price)
            y.set_interval(args.start_date, args.end_date)
            y.set_logfile('yellohvillage', f'a_{args.log}', args.date_price)
            y.execute()

        else:
            raise Exception(f"Argument(s) manquant(s): {', '.join(miss)}")
