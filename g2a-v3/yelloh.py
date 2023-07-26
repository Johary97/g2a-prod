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
from tools.changeip import refresh_connection
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait

SEARCH_BTN = "#mm-1 > div.main > div:nth-child(2) > header > div.Header-container.Container > div:nth-child(1) > button:nth-child(3)"
SEARCH_OPTIONLIST = "#mm-1 > div.main > div:nth-child(2) > header > div.Header-search > div > form > div.Search-wrapper.Search-wrapper--larger > div.Search-autocompleteDropdown > div.Search-autocompleteBox.Search-autocompletePart > div > button"
SEARCH_FIRSTOPTION = "#mm-1 > div.main > div:nth-child(2) > header > div.Header-search > div > form > div.Search-wrapper.Search-wrapper--larger > div.Search-autocompleteDropdown > div.Search-autocompleteBox.Search-autocompletePart > div > button"
SEARCH_PERSONFILTER = "#mm-1 > div.main > div:nth-child(2) > header > div.Header-search > div > form > div.Search-wrapper.Search-wrapper--small > div.Select.Search-select > ul > li:nth-child(2)"
SEARCH_SUBMIT = "#mm-1 > div.main > div:nth-child(2) > header > div.Header-search > div > form > button"
SEARCH_RESULT = "#map-container > section.CampingList > div > section.CampingList-subsection.CampingList-subsection--strict"


class YellohDestinationScraper(Scraping):

    def __init__(self, dest_location: str, in_background: bool = False) -> None:
        super().__init__(in_background)
        refresh_connection()
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
            self.driver.find_element(By.ID, 'searchText').clear()
            time.sleep(randint(1, 5))
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
            # print("An error occured!!!!")
            # print(e)
            pass

    def extract(self) -> None:
        print("Extracting")
        try:
            soupe = BeautifulSoup(self.driver.page_source, 'lxml')
            # print(soupe)
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
        refresh_connection()
        print("Executing")
        try:
            while not self.scrap_finished:
                self.setup_search()
                time.sleep(5)
                self.extract()
                self.save_dests()
                self.set_index()
                self.navigate_init_page()
            print("Yelloh destination scraped !")
        except:
            pass
            
        if not self.scrap_finished:
            self.execute()


class AnnonceYelloh(Scraping):

    def __init__(self) -> None:
        super().__init__()

        self.file_extension = 'csv'
        self.week_scrap = ''
        self.website_name = 'yellow_village'
        self.website_url = 'www.yellohvillage.fr'
        self.scrap_finished = False
        self.data = []
        self.navigate_init_page()
        self.nights = "7"

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

    def set_interval(self, start_date: str, end_date: str):
        self.start_date = start_date
        self.end_date = end_date

    def set_dates(self) -> None:
        self.driver.execute_script(f"window.localStorage.setItem('date_start', '{self.start_date}');")
        self.driver.execute_script(f"window.localStorage.setItem('date_end', '{self.end_date}');")

    def apply_configs(self) -> None:
        self.driver.execute_script("window.location.reload();")
        time.sleep(5)
        try:
            self.driver.find_element(By.XPATH, '//button[@aria-label="Voir prix et disponibilités"]').click()
            WebDriverWait(self.driver, 5)
        except Exception as e:
            print("Erreur bouton")
            print(e)
        
    def set_nb_pers(self, nb_script) -> None:
        self.driver.execute_script(nb_script)

    def extract(self) -> None:
        for i in range(5):
            self.driver.find_element(By.CSS_SELECTOR, 'body').send_keys(Keys.PAGE_DOWN)
            time.sleep(2)

        for i in range(5):
            self.driver.find_element(By.CSS_SELECTOR, 'body').send_keys(Keys.PAGE_UP)
            time.sleep(2)

        time.sleep(10)
        
        soupe = BeautifulSoup(self.driver.page_source, "lxml")
        accomodationContainer = soupe.find('section', class_='AccommodationList').find(
            'ul', 'Container-accommodation')
        accomodations = accomodationContainer.find_all(
            'article', class_='AccomodationBlock')

        for accomodation in accomodations:
            available = True \
                        if len(accomodation.find_all('span', {'class': 'Message-title'})) \
                            and accomodation.find_all('span', {'class': 'Message-title'})[0].text.strip() == 'Disponible' \
                        else False

            if available:
                data = {}
                data["web-scrapper-order"] = ""
                data["nom"] = soupe.find(
                    'span', class_="SectionHeadVillage-name").text.strip()
                data["localite"] = soupe.find(
                    'p', class_="SectionHeadVillage-location").text.strip()
                data["date_price"] = self.week_scrap
                data["date_debut"] = self.driver.execute_script(
                    "return window.localStorage.getItem('date_start');")
                data["date_fin"] = self.driver.execute_script(
                    "return window.localStorage.getItem('date_end');")
                data["prix_actuel"] = re.sub(r"[^(\d)]", '', accomodation.find(
                    "p", class_="PriceTag-finalPrice").text.strip())
                data["prix_init"] = data["prix_actuel"]
                data["n_offre"] = re.sub(r"[^(\d)]", '', accomodation.find(
                    "a", class_="AccomodationBlock-actionBtn", href=True)["href"])
                data["date_debut-jour"] = ""

                typos = accomodation.find_all("span", class_="AccommodationDetails-characs")
                typos_values = " ".join(list(map(lambda x: x.text.strip(), typos))[0:3])
                typo_pers = accomodation.find("div", class_="AccommodationDetails-characs--persons").text.strip()
                data["typologie"] = typos_values + typo_pers + " personnes"

                data["Nb semaines"] = datetime.strptime(self.start_date, '%d/%m/%Y').isocalendar()[1]
                data["cle_station"] = ""
                data["nom_station"] = data['localite']
                data["url"] = self.driver.current_url

                self.data.append(data)


class YellohScraper(Scraper):
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

    def set_interval(self, start_date: str, end_date: str):
        self.start_date = start_date
        self.end_date = end_date

    def prepare(self) -> None:
        print("Préparation ...")
        dates_saturday = [date.to_pydatetime().strftime("%d/%m/%Y") for date in pd.bdate_range(start=self.start_date, end=self.end_date, freq="C", weekmask='Sat')]
        dates_sunday = [date.to_pydatetime().strftime("%d/%m/%Y") for date in pd.bdate_range(start=self.start_date, end=self.end_date, freq="C", weekmask='Sun')]
        self.dates = dates_saturday + dates_sunday
    
    def start(self) -> None:
        c = AnnonceYelloh()
        c.set_week_scrap(self.week_scrap)
        last_index = self.get_history('last_index')
        # c.set_driver_interval(300, 500)
        for index in range(last_index + 1, len(self.urls)):
            try:
                print(index+1, ' / ', len(self.urls))
                c.set_url(self.urls[index])
                print("***** ", c.url, " *****")
                for d in self.dates:
                    begin = d
                    end = datetime.strftime(datetime.strptime(d, "%d/%m/%Y") + timedelta(days=7), "%d/%m/%Y")
                    print("Dates %s -> %s"% (begin, end))
                    c.set_interval(begin, end)
                    c.scrap()
                    time.sleep(5)
                    c.set_dates()
                    for nb in [
                        "window.localStorage.setItem('nb_personnes_label', '4+ pers');",
                        "window.localStorage.setItem('nb_personnes_label', '6+ pers');",
                        "window.localStorage.setItem('nb_personnes_label', '8+ pers');"]:
                        c.set_nb_pers(nb)
                        c.apply_configs()
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

            y = YellohScraper()
            y.set_destinations(f'{data_folder}/{args.destinations}')
            y.set_interval(args.start_date, args.end_date)
            y.set_week_scrap(args.date_price)
            y.set_logfile('yellohvillage', f'a_{args.log}', args.date_price)
            y.prepare()
            y.start()

        else:
            raise Exception(f"Argument(s) manquant(s): {', '.join(miss)}")