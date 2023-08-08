import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FireFoxService
from selenium.webdriver.firefox.options import Options as FireFoxOptions
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary  
from selenium.webdriver.edge.service import Service as EdgeService
import pandas as pd 
from selenium.webdriver.common.action_chains import ActionChains
import re, os, time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from random import randint
import asyncio

__months__ = {
    'jan.': 1,
    'févr.': 2,
    'mars': 3,
    'avr.': 4,
    'mai': 5,
    'juin': 6,
    'juil.': 7,
    'aout': 8,
    'sept.': 9,
    'oct.': 10,
    'nov.': 11,
    'dec.': 12
}

def get_days(date):
    date = date.split(' ')
    start = datetime(day=int(date[2]), month=__months__[date[3]], year=int(date[4])+2000)
    end = datetime(day=int(date[7]), month=__months__[date[8]], year=int(date[9])+2000) + timedelta(days=-1)
    return [start.strftime('%d-%m-%Y'), end.strftime('%d-%m-%Y')]


class MaevaScraping(object):
    
    def __init__(self, urls, dest_name, dest_folder) -> None:
        
        self.drivers = ['chrome', 'chrome']
        
        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument('--ignore-certificate-errors')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--incognito')
        
        self.firefox_options = webdriver.FirefoxOptions()
        self.firefox_options.add_argument('--ignore-certificate-errors')
        self.firefox_options.add_argument('--disable-gpu')
        # self.firefox_options.add_argument('--headless')
        self.firefox_options.add_argument('--incognito')
        
        self.edge_options = webdriver.EdgeOptions()
        self.edge_options.add_argument('--ignore-certificate-errors')
        self.edge_options.add_argument('--disable-gpu')
        # self.ie_options.add_argument('--headless')
        self.edge_options.add_argument('--incognito')
        
        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=self.chrome_options)
        self.current_driver = 'chrome'
        
        self.result_file = dest_name + '.xlsx'
        self.result_folder = dest_folder
        self.full_path = f'{self.result_folder}/{self.result_file}'
        self.index_file = f'{dest_folder}/{dest_name}-lastScrapped.txt'

        if not os.path.exists(self.index_file):
            try:
                with open(self.index_file, 'w') as file:
                    file.write("0, 0")
            except Exception as e:
                print("Exception: ", e.__traceback__())
        
        if not os.path.exists('C:/src/programs/twenitscraper/no_station.txt'):
            open('C:/src/programs/twenitscraper/no_station.txt', 'x')

        self.create_file()
        print('file_created')
        self.urls = pd.read_excel(urls)['urls'].to_list()
        self.total = len(self.urls)
        self.station_keys = self.init_station_dict()

        self.run = False

    def init_station_dict(self):
        mydict = {}

        with open('C:/src/programs/twenitscraper/annonce station.csv', newline='') as csv_annonce_ids:
            reader = csv.DictReader(csv_annonce_ids)
            for row in reader:
                mydict[row['annonce']] = {'key': row['station_key'], 'name': row['station_name']}

        return mydict
    
    def start(self):
        self.run = True
        self.loop()

    def stop(self):
        self.run = False

    def loop(self):
        self.last_index = self.get_last_index()

        for i in range(self.last_index[0], len(self.urls)):
            if i == len(self.urls):
                print("scrap finished ('_')")
            if self.run:
                try:
                    self.run_scrapping(self.urls[i])
                    # with open(self.index_file, 'w') as file:
                    #     file.write(f"{i}, {self.last_index[1]}")
                    #     print(i)
                    self.set_page_index(i)
                except Exception as e:
                    print(e)
            else:
                break          
                
    def run_scrapping(self, url:str) -> None:
        """function to start scrapping"""
        page = self.run_driver(self.driver, url)
        datas = self.extract_data(page, url)

        if datas['showed_date'] != '':
            existdates = get_days(datas['showed_date'])
            if int(float(datas['prix_init'])) > 0 and existdates[0] == datas['date_debut'] and existdates[1] == datas['date_fin']:
                data_saved = self.save_data(datas, self.full_path)
                # print("Enregistrement ...")
                if not data_saved:
                    self.switch_driver()
                    self.run_scrapping(url)
            
    def get_last_index(self):
        try:
            with open(self.index_file, 'r') as file:
                index = file.readline()
                # return int(index) + 1 if index else 0
                return list(map(lambda x: int(x), index.split(', '))) if index else [0, 0]
        except FileNotFoundError:
            return 0

    def set_page_index(self, i):
        saved = self.get_last_index()[1]

        try:
            with open(self.index_file, 'w') as file:
                file.write(f"{i}, {saved}")
                print(i)
        except FileNotFoundError:
            return 0

    def set_total_saved(self):
        indexes = self.get_last_index()
        new_value = indexes[1] + 1
        print("save: ", new_value)
        try:
            with open(self.index_file, 'w') as file:
                file.write(f"{indexes[0]}, {new_value}")
        except FileNotFoundError:
            return 0
    
    def run_driver(self, driver:object, url=None) -> None:
        """ function to run driver """
        try:
            driver.get(url) 
            WebDriverWait(self.driver, randint(0, 2))
            time.sleep(0.5)
            # self.simulate_presence()
            return driver.page_source
        except Exception as e:
            print(e)
            with open(f'{self.result_file}-AttributeError.txt', 'a') as file:
                file.write(f"{url}\n")
                self.switch_driver()
                self.run_driver(self.driver, url)
                
    def simulate_presence(self) -> None:
        action = ActionChains(self.driver)
        
        action_types = ['scrolling', 'moveon']
        action_type = action_types[randint(0, 1)]
        match action_type:
            case 'scrolling':
                # action.move_to_element(self.driver.find_element(By.XPATH, '//*[@id="header-account"]'))
                # self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(0.5)
                action.move_to_element(self.driver.find_element(By.XPATH, f'//*[@id="menu-desktop"]/a[{randint(1, 4)}]'))
                action.perform()
                
            case 'moveon':
                action.move_to_element(self.driver.find_element(By.XPATH, f'//*[@id="menu-desktop"]/a[{randint(1, 4)}]'))
                time.sleep(0.5)
                action.move_to_element(self.driver.find_element(By.XPATH, f'//*[@id="menu-desktop"]/a[{randint(1, 4)}]'))
                action.perform()  
        return

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
            # case 'edge':
            #     self.driver = webdriver.Edge(service=EdgeService(EdgeChromiumDriver().install()), options=self.edge_options)  
    
    def extract_data(self, page:object, url:str) -> dict:
        """ function to extract data from a web page """
        soupe = BeautifulSoup(page, 'lxml')
        
        type_residence = soupe.find('h2', class_="maeva-black").text.strip() \
            if soupe.find('h2', class_="maeva-black") != None else ''
        type_residence = ''.join(x[0].upper() if not bool(re.search(r'\d', x)) else x for x in type_residence)
        
        residence = soupe.find('h1', attrs={'id':'fiche-produit-residence-libelle'}).text.strip() \
            if soupe.find('h1', attrs={'id':'fiche-produit-residence-libelle'}) else ''
        
        prix_actuel = soupe.find('div', {'class':"fiche-produit-prix-item"}).text[:-1].strip().replace(',', '.') \
            if soupe.find('div', {'class':"fiche-produit-prix-item"}) != None else '0.00'
            
        prix_init = soupe.find('span', {'class':"fiche-produit-prix-barre-item"}).text[:-1].strip().replace(',', '.') \
            if soupe.find('span', {'class':"fiche-produit-prix-barre-item"}) != None else '0.00'
            
        # stars = soupe.find('span', {'id':"fiche-produit-note"}).text.strip() \
        #     if soupe.find('span', {'id':"fiche-produit-note"}) != None else '0'
            
        localite = soupe.find('div', attrs={'id':"fiche-produit-localisation"}).find('span', {'class':"maeva-black"}).text.strip() \
            if soupe.find('div', attrs={'id':"fiche-produit-localisation"}).find('span', {'class':"maeva-black"}) else ''
            
        n_offre = soupe.find('div', attrs={'id':"fiche-produit-logement"}).find('div', {'class':'bold'}).text.split(':')[1].strip() \
            if soupe.find('div', attrs={'id':"fiche-produit-logement"}).find('div', {'class':'bold'}) != None else ''

        showed_date = soupe.find('div', attrs={'class':"fiche__book-infos"}).find('div', {'data-info':'date'}).text.strip() \
            if soupe.find('div', attrs={'class':"fiche__book-infos"}).find('div', {'data-info':'date'}) != None else ''

        station_key = self.station_keys[n_offre]['key'] if n_offre in self.station_keys.keys() else ''
        station_name = self.station_keys[n_offre]['name'] if n_offre in self.station_keys.keys() else ''

        if station_key == '':
            print("no station ...")
            with open('C:/src/programs/twenitscraper/no_station.txt', 'a') as file:
                file.write(f"{n_offre}\n")
                # return False

        date_debut, date_fin = self.get_dates(url)
        date = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime('%d/%m/%Y')
        data = {
            'nom':residence, 
            'typologie': type_residence,
            'date_price': date,
            'date_debut': date_debut,
            'date_fin': date_fin,
            'prix_actuel': prix_actuel,
            'prix_init': prix_actuel if int(float(prix_init)) == 0 else prix_init,
            'localite': localite,
            'n_offre': n_offre,
            'showed_date': showed_date,
            'station_name': station_name,
            'station_key': station_key
            }
        print(data)
        return data
    
    def create_file(self) -> None:
        """ function to create new excel file where data will be stored """
        if not os.path.exists(self.full_path):
            df = pd.DataFrame(
                columns=[
                        'web-scrapper-order',
                        'date_price',
                        'date_debut', 
                        'date_fin',
                        'prix_init',
                        'prix_actuel',
                        'typologie',
                        'n_offre',
                        # 'stars',
                        'nom',
                        'localite',
                        'date_debut-jour',
                        'Nb semaines',
                        'cle_station',
                        'nom_station'
                        ])
            df.to_excel(self.full_path, index=False)
    
    def save_data(self, data:dict, file:str) -> bool:
        """ function to append data at the excel file """
        date_price, date_debut, date_fin, prix_init, prix_actuel, typologie, n_offre, nom, localite = [], [], [], [], [], [], [], [], []
        web_scrapper_order, date_debut_jour, nb_semaine, station_key, station_name = [], [], [], [], []
        date_price.append(data['date_price'])
        date_debut.append(datetime.strptime(data['date_debut'], '%d-%m-%Y').strftime('%d/%m/%Y'))
        date_fin.append(datetime.strptime(data['date_fin'], '%d-%m-%Y').strftime('%d/%m/%Y'))
        prix_init.append(data['prix_init'])
        prix_actuel.append(data['prix_actuel'])
        typologie.append(data['typologie'])
        n_offre.append(data['n_offre'])
        nom.append(data['nom'])
        localite.append(data['localite'])
        # stars.append(data['stars'])
        web_scrapper_order.append('')
        nb_semaine.append(datetime.strptime(data['date_debut'], '%d-%m-%Y').isocalendar()[1])
        date_debut_jour.append('')
        station_key.append(data['station_key'])
        station_name.append(data['station_name'])
        
        last_index = len(pd.read_excel(file)) + 1
        df = pd.DataFrame({
            'web-scrapper-order': web_scrapper_order,
            'date_price':date_price,
            'date_debut':date_debut,
            'date_fin': date_fin,
            'prix_init': prix_init,
            'prix_actuel': prix_actuel,
            'typologie': typologie,
            'n_offre': n_offre,
            # 'stars':stars,
            'nom':nom,
            'localite':localite,
            'date_debut-jour': date_debut_jour,
            'Nb semaines': nb_semaine,
            'cle_station': station_key,
            'nom_station': station_name,
        })

        i = 1
        try:
            with pd.ExcelWriter(file, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
                if last_index >= 60000:
                    df.to_excel(writer, sheet_name=f'Sheet{i + 1}', startrow=last_index, header=False, index=False)
                else:
                    df.to_excel(writer, sheet_name=f'Sheet{i}', startrow=last_index, header=False, index=False)
                
            self.set_total_saved()
            return True
        except Exception as e:
            with open('SaveDataError.txt', 'a') as file:
                file.write(f"{e}\n")
                return False
            
    def get_dates(self, url:str) -> tuple:
        """ function to get dates in url """
        url_params = parse_qs(urlparse(url).query)
        try:
            sep = '-'
            return sep.join(url_params['date_debut'][0].split('-')[::-1]), sep.join(url_params['date_fin'][0].split('-')[::-1])
        except KeyError:
            return 
        
        
# if __name__ == '__main__':
#     Scrapping()
        