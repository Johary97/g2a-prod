from csv import writer
from datetime import datetime, timedelta
from random import randint
import sys
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import ElementNotVisibleException, ElementNotSelectableException
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import re
from abc import ABC, abstractmethod
import dotenv
import os
import json
from selenium.webdriver.common.keys import Keys
import socket
from selenium.webdriver.remote.command import Command
from tools.g2a import G2A


class Scraping(object):

    def __init__(self, in_background: bool = False) -> None:

        # driver options
        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument('--ignore-certificate-errors')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument(
            '--disable-blink-features=AutomationControlled')
        in_background and self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--incognito')

        self.firefox_options = webdriver.FirefoxOptions()
        self.firefox_options.add_argument('--disable-gpu')
        self.firefox_options.add_argument('--ignore-certificate-errors')
        in_background and self.firefox_options.add_argument('--headless')
        self.firefox_options.add_argument('--incognito')

       #  self.driver = webdriver.Firefox(service=FirefoxService(
       #             GeckoDriverManager().install()), options=self.firefox_options)

        self.driver = webdriver.Chrome(service=ChromeService(
            ChromeDriverManager().install()), options=self.chrome_options)
        self.driver.maximize_window()
        self.drivers = ['chrome', 'firefox']
        self.current_driver = self.drivers[0]

        self.url = ""
        self.urls = []
        self.data = []
        self.history_file = ""

        self.min_cycle = 30
        self.max_cycle = 30
        self.driver_cycle = 30
        self.counter = 0
        self.nights = 7

    def set_nights(self, nights):
        self.nights = nights

    def permute_driver(self) -> None:
        self.driver.quit()
        if self.current_driver == 'firefox':
            try:
                self.driver = webdriver.Chrome(options=self.chrome_options)
            except:
                self.driver = webdriver.Chrome(service=ChromeService(
                    ChromeDriverManager().install()), options=self.chrome_options)
            self.current_driver = 'chrome'
        else:
            try:
                self.driver = webdriver.Firefox(options=self.firefox_options)
            except:
                self.driver = webdriver.Firefox(service=FirefoxService(
                    GeckoDriverManager().install()), options=self.firefox_options)
            self.current_driver = 'firefox'
        self.counter = 0
        self.set_driver_cycle(randint(self.min_cycle, self.max_cycle))

    def set_driver_interval(self, min: int, max: int) -> None:
        self.min_cycle = min
        self.max_cycle = max
        self.set_driver_cycle(randint(self.min_cycle, self.max_cycle))

    def increment_counter(self) -> None:
        self.counter = self.counter + 1
        self.check_counter()

    def check_counter(self) -> None:
        if self.counter == self.driver_cycle:
            print("Changement de driver!!!")
            self.permute_driver()

    def set_driver_cycle(self, cycle: int) -> None:
        self.driver_cycle = cycle

    def set_url(self, url: str) -> None:
        self.url = url

    def set_urls(self, urls: list) -> None:
        self.urls = urls

    def set_storage(self, storage: str) -> None:
        self.storage_file = storage

    def execute(self) -> None:
        for url in self.urls:
            try:
                self.set_url(url)
                self.scrap()
                time.sleep(2)
                self.extract()
                self.save()
            except Exception as e:
                print(e)
                self.driver.quit()
                sys.exit("Arret")

        self.driver.quit()

    def scrap(self) -> None:
        self.navigate()

    def navigate(self) -> None:
        self.driver.get(self.url)

    def refresh(self) -> None:
        self.driver.refresh()

    @abstractmethod
    def extract(self) -> None:
        pass

    @abstractmethod
    def generate_url(self) -> None:
        pass

    def create_file(self) -> None:
        with open(f"{self.storage_file}", 'w', encoding="utf-16") as file:
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
                'localite',
                'date_debut-jour',
                'Nb semaines',
                'cle_station',
                'nom_station'
            ]
            writers = writer(file)
            writers.writerow(fields_name)

    def save(self) -> None:

        if len(self.data):
            str_datas = G2A.format_data(self.data)
            res = G2A.post_accommodation("accommodations/multi", {
                "nights": self.nights,
                "website_name": self.website_name,
                "website_url": self.website_url,
                "data_content": str_datas
            })
            print(res)

    def set_history_file(self, filepath: str) -> None:
        with open(f"{filepath}.json", "w") as file:
            self.history_file = f"{filepath}.json"

    def set_history(self, key: str) -> None:
        logs = {}
        try:
            with open('logs.json', 'r') as openfile:
                logs = json.load(openfile)
        except:
            pass
        dest_station_init = logs[key] if key in logs.keys() else []
        logs[key] = dest_station_init
        with open('logs.json', 'w') as outfile:
            outfile.write(json.dumps(logs, indent=4))

    def get_history(self, key: str, value: str) -> object:
        try:
            with open('logs.json', 'r') as openfile:
                logs = json.load(openfile)
                return logs
        except:
            pass
        return

    def set_dest(self, new_storage: str) -> None:
        self.storage_file = new_storage


class Scraper(object):

    def __init__(self) -> None:
        self.urls = []
        self.output_name = ""
        self.log = ""

    @abstractmethod
    def initialize(self) -> None:
        pass

    @abstractmethod
    def start(self) -> None:
        pass
