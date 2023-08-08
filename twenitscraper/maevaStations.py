import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import NoSuchElementException
import pandas as pd 
import re, os, time
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from random import randint
import asyncio
import numpy as np
import sys
from datetime import datetime, timedelta
from queue import Queue
from threading import Thread
import math
import csv
from urllib.parse import urlparse, parse_qs
import pyautogui


class MaevaStation(object):
    
    def __init__(self) -> None:
        
        self.drivers = ['chrome', 'chrome']
        
        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument('--ignore-certificate-errors')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--incognito')
        
        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=self.chrome_options)
        self.current_driver = 'chrome'
        self.dict = {}
        # self.stations_key = [19, 72, 32, 58, 11, 105, 64, 567, 30]
        # self.stations_key = [566, 1224, 44, 610, 80, 86, 29, 54, 81]
        # self.stations_key = [25, 29994, 113, 317, 38129, 73, 24, 324, 33]
        # self.stations_key = [52, 28, 42, 101, 22, 104, 223,333, 93]
        # self.stations_key = [55, 109, 321, 304, 569, 85, 4866, 48, 520]
        # self.stations_key = [38, 108, 23, 39, 69, 588, 334, 45, 47]
        # self.stations_key = [91, 1174, 568, 4337, 660, 318, 103, 67, 107]
        # self.stations_key = [61, 43, 50, 84, 110, 70, 59, 82, 102, 79]
        # self.stations_key = ['%2A506', '%2A430', '%2A489', '%2A428', '%2A427', '%2A467']

        for i in range(0, len(self.stations_key)):
            if i >= len(self.stations_key):
                print('scrapping finished')
                self.scrap_finished = True
                self.driver.quit()
            try:
                self.run_scrapping(self.stations_key[i])
            except Exception as e:
                print(e)

            self.save_data({self.stations_key[i]: self.dict[self.stations_key[i]]})
    
    def navigate_last_page_index(self, index_page:int=0) -> None:
        index = 0
        if index_page > 0:
            while index != index_page:
                print('not equal')
                index += 1
                self.driver.find_elements(By.CLASS_NAME, 'f9d6150b8e')[1].click()

    def run_scrapping(self, station_key) -> None:
        """function to start scrapping"""
        url = f"https://www.maeva.com/fr-fr/searchlist.php?&acces_direct=1&station_cle={station_key}&etendre_min=30&trier_par=zerank&page=1"
        self.dict[station_key] = []
        count = self.get_items_count(url)
        urls = []
        print("Clé station: ", station_key)
        for i in range(1, math.ceil(count/30)):
            page_url = f'https://www.maeva.com/fr-fr/searchlist.php?&acces_direct=1&station_cle={station_key}&etendre_min=30&trier_par=zerank&page={i}'

            print("Page: ", i)
            pages = list(self.run_driver(page_url))
            for page in pages:
                print("Extraction ...")
                datas = self.extract_data(page, url)
                print(datas)
                self.dict[station_key].extend(datas)
            
        self.dict[station_key] = set(self.dict[station_key])
        
    def run_driver(self, url=None) -> None:
        """ function to run driver """
        try:
            self.driver.get(url) 
            WebDriverWait(self.driver, randint(0, 2))
            time.sleep(0.5)
            yield self.driver.page_source
        except Exception as e:
            print(e)
            with open('AttributeError.txt', 'a') as file:
                file.write(f"{url}\n")
                self.switch_driver()
                self.run_driver(url)

    def get_items_count(self, url=None) -> None:
        """ function to run driver """
        try:
            self.driver.get(url)
            print("Crawling ...")
            WebDriverWait(self.driver, randint(0, 2))
            time.sleep(0.5)
            print("Crawling end ...")
            total = int(list(map(lambda x: x.text, self.driver.find_elements(By.CLASS_NAME, 'maeva-red')))[1])
            
            return total
        except Exception as e:
            print(e)
            with open('AttributeError.txt', 'a') as file:
                file.write(f"{url}\n")
                self.switch_driver()
                self.run_driver(url)

    def extract_data(self, page:object, url:str) -> dict:
        soupe = BeautifulSoup(page, 'lxml')
        cards = soupe.find_all('div', class_='toaster-produit-container')
        annonces = []
        for card in cards:
            link = f"https://www.maeva.com{card.find('a', class_='ui-maeva-cta-ghost-black')['href']}" \
                if card.find('a', class_='ui-maeva-cta-ghost-black') else ''

            annonces.append(parse_qs(urlparse(link).query)['id'][0])
        return annonces

    def switch_driver(self) -> None:
        """ function to make switch driver """
        self.drivers = self.drivers[1:] + self.drivers[0:1]
        self.driver.quit()
        self.current_driver = self.drivers[0]
        match self.current_driver:
            case 'chrome':
                self.driver = webdriver.Chrome(options=self.chrome_options) 

    def save_data(self, dict) -> bool:
        fieldnames = ['station', 'annonce']
        if not os.path.exists('maeva station annonce.csv'):
            with open('maeva station annonce.csv', 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for (key, value) in dict.items():
                    writer.writerow({'station': key, 'annonce': ' / '.join(value)})
        else:
            with open('maeva station annonce.csv', 'a') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                for (key, value) in dict.items():
                    writer.writerow({'station': key, 'annonce': ' / '.join(value)})


class BrowseStation(object):
    
    def __init__(self, file_list, file_dest, index) -> None:
        
        self.drivers = ['chrome', 'chrome']
        
        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument('--ignore-certificate-errors')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--incognito')
        
        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=self.chrome_options)
        self.current_driver = 'chrome'
        self.dict = {}
        self.file_list = file_list
        self.file_dest = file_dest

        self.station_keys = {}
        self.load_existed_stations(index)
        self.fieldnames = ['annonce', 'station_key', 'station_name']
        if not os.path.exists(file_dest):
            with open(file_dest, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
                writer.writeheader()

    def load_existed_stations(self, index):
        tmpset = set()
        for i in range(1, index):
            with open(f'C:/Files/no_stations/annonce station {i}.csv', 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                for line in reader:
                    if line['station_name'] not in tmpset:
                        tmpset.add(line['station_name'])
                        self.station_keys[line['station_name']] = line['station_key']

    def run(self):
        with open(self.file_list, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for line in reader:
                self.run_browse(line['annonce'])

        self.key_dict = {}

        self.station_list = Queue()
        for station in self.dict.keys():
            self.station_list.put(station)

        while not self.station_list.empty():
            station = self.station_list.get()
            exist_station = self.station_keys[station.upper()] if station.upper() in self.station_keys.keys() else ''
            if exist_station == '':
                station_page = list(self.run_find_key(station))
                for page in station_page:
                    params = parse_qs(urlparse(page).query)
                    if 'station_cle' in params.keys():
                        station_key = params['station_cle'][0]
                        self.key_dict[station] = station_key
                        print(f'Station: {station}, key: {station_key}')
                    else:
                        print(page)
                        self.station_list.put(station)
            else:
                self.key_dict[station] = exist_station
                print(f'Station déjà trouvée: {station}, key: {exist_station}')

        self.save_data(self.key_dict, self.dict, self.file_dest)

    def save_data(self, key_dict, annonce_dict, file_dest) -> bool:
        with open(file_dest, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
            print(self.key_dict)
            for (station, annonces) in annonce_dict.items():
                for annonce in annonces:
                    if station in self.key_dict.keys():
                        print("Ecriture: ", annonce, self.key_dict[station], station.upper())
                        writer.writerow({'annonce': annonce, 'station_key': self.key_dict[station], 'station_name': station.upper()})

    def run_browse(self, annonce_id) -> None:
        """function to start scrapping"""
        url = f"https://www.maeva.com/pages/fiche.php?id={annonce_id}&date_debut=2023-07-01&date_fin=2023-07-07"

        pages = list(self.run_driver(url))
        for page in pages:
            station = self.extract_data(page, url)
            if station != '':
                print( annonce_id, station)
                if not station in self.dict.keys():
                    self.dict[station] = []
                
                self.dict[station].append(annonce_id)

    def run_find_key(self, station) -> None:

        """function to start scrapping"""
        url = "https://www.maeva.com/fr-fr/"
        try:
            self.driver.get(url)

            WebDriverWait(self.driver, 2)

            try:
                self.driver.find_element(By.ID, "didomi-notice-agree-button").click()
            except:
                pass

            time.sleep(0.5)

            station_input = self.driver.find_element(By.NAME, "choix_destination_recherche")
            station_input.send_keys(station)

            WebDriverWait(self.driver, 1)
            time.sleep(.5)

            submit_btn =self.driver.find_element(By.NAME, "oboo-go")
            submit_btn.click()

            WebDriverWait(self.driver, 1)

            time.sleep(0.5)

            yield self.driver.current_url

        except Exception as e:
            print("Exception trouvé:", e)
            self.switch_driver()
            self.station_list.put(station)

    def run_driver(self, url=None) -> None:
        """ function to run driver """
        try:
            self.driver.get(url) 
            WebDriverWait(self.driver, randint(0, 2))
            time.sleep(0.5)
            yield self.driver.page_source
        except Exception as e:
            print(e)
            with open('AttributeError.txt', 'a') as file:
                file.write(f"{url}\n")
                self.switch_driver()
                self.run_driver(url)

    def extract_data(self, page:object, url:str) -> dict:
        soupe = BeautifulSoup(page, 'lxml')
        station = soupe.find('div', attrs={'id':"fiche-produit-localisation"}).find('span', {'class':"maeva-black"}).text.strip() \
            if soupe.find('div', attrs={'id':"fiche-produit-localisation"}) and soupe.find('div', attrs={'id':"fiche-produit-localisation"}).find('span', {'class':"maeva-black"}) else ''

        return station.split(' - ')[0]

    def switch_driver(self) -> None:
        """ function to make switch driver """
        self.drivers = self.drivers[1:] + self.drivers[0:1]
        self.driver.quit()
        self.current_driver = self.drivers[0]
        match self.current_driver:
            case 'chrome':
                self.driver = webdriver.Chrome(options=self.chrome_options)
            case 'firefox':
                self.driver = webdriver.Firefox(options=self.firefox_options)

def fusionner():
    tmplist = []
    for i in range(1, 23):
        with open(f'C:/Files/no_stations/annonce station {i}.csv', 'r') as csvfile:
            reader = csv.DictReader(csvfile, fieldnames=['annonce', 'station_key', 'station_name'])
            for line in reader:
                tmplist.append(line)
    
    with open(f'C:/Files/no_stations/annonce station full.csv', 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['annonce', 'station_key', 'station_name'])
        writer.writeheader()

        writer.writerows(tmplist)
    
if __name__ == '__main__':

    fusionner()
#     MaevaStation()
    # scraps = []
    # for i in range(14, 23):
    #     print("Initialisation scrap: ", i)
    #     b = BrowseStation(f'C:/Files/no_stations/p{i}.csv', f'C:/Files/no_stations/annonce station {i}.csv', i)
    #     b.run()
    #     pyautogui.alert("Finished !!!")
    #     # time.sleep(180)