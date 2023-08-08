from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from bs4 import BeautifulSoup
from datetime import datetime
from csv import DictWriter, writer
from urllib.parse import urlparse, parse_qs
from queue import Queue
import pandas as pd
import threading
import json, re
import os
import time
from random import randint
from tkinter import messagebox
from openpyxl import Workbook


class MaevaScrap(object):

    def __init__(self, instance_index) -> None:
        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument('--ignore-certificate-errors')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        # self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--incognito')

        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=self.chrome_options)
        self.current_driver = 'chrome'
        self.drivers = ["chrome", "chrome"]

        self.data_container = Queue()
        self.page_container = Queue()

        self.instance_index = instance_index
        self.last_indexes = self.get_last_index()

        # self.remove_duplicates()

        self.station_keys = self.get_station_keys()
        # self.station_keys_queue = Queue()
        # for station in self.station_keys:
        #     self.station_keys_queue.put(station)

        with open('./config.json', 'r') as file:
            settings = json.loads(file.read())
            self.start_week = settings['interval'][0]
            self.end_week = settings['interval'][1]
            self.output_name = settings['instances'][self.instance_index]['destination_path']
        
        self.create_file(f'{self.output_name}')

        self.station_index = 1

        self.thread_one = threading.Thread(target=self.get_pages)
        self.thread_two = threading.Thread(target=self.get_datas)
        self.thread_three = threading.Thread(target=self.set_datas)

        # self.scraped = False

        self.thread_one.start()
        time.sleep(3)
        self.thread_two.start()
        time.sleep(3)
        self.thread_three.start()

        # self.schedule_check()

    def get_last_index(self) -> object:
        with open('./config.json', 'r') as file:
            settings = json.loads(file.read())
            last_scrapped_data = settings['instances'][self.instance_index]
            if last_scrapped_data:
                print(last_scrapped_data)
                return last_scrapped_data
            else:
                return None
            
    def get_station_keys(self) -> list:
        with open('./config.json', 'r') as configfile:
            settings = json.loads(configfile.read())
            station_keys = pd.read_excel(settings['instances'][self.instance_index]['station_key_path']).to_dict(orient='records')
            return station_keys

    def remove_duplicates(self) -> list:
        with open('./config.json', 'r') as configfile:
            settings = json.loads(configfile.read())
            station_keys = pd.read_excel(settings['instances'][self.instance_index]['station_key_path']).to_dict(orient='records')
            new_list_json = set()
            [new_list_json.add(json.dumps(station)) for station in station_keys]
            new_list = [json.loads(line) for line in new_list_json]
            print(len(new_list))

            wb = Workbook()
            current_sheet = wb.active

            current_sheet['A1'] = 'name'
            current_sheet['B1'] = 'station_key'

            i = 2
            for station in new_list:
                current_sheet[f'A{i}'] = station['name']
                current_sheet[f'B{i}'] = station['station_key']
                i += 1

            wb.save('stationkey2.xlsx')

    def get_pages(self):
        #get last station scrapped
        #get last station page scrapped
        for index in range(self.last_indexes['last_scrapped_key'], len(self.station_keys)):
        # for key in self.station_keys:
        # if not self.station_keys_queue.empty():
            # station = self.station_keys_queue.get()
            print(f"\n=> Station {index+1}/{len(self.station_keys)}: {self.station_keys[index]['name']} (session {self.instance_index})\n")
            # urls = self.get_station_urls(station['station_key'])
            urls = self.get_station_urls(self.station_keys[index]['station_key'])
            i = 1
            # for url in urls:
            # self.set_last_index(attr='page', action='set', page_index=self.last_indexes['saved_page'])
            for page_index in range(self.last_indexes['page_index'], len(urls)):
                print(f"\tPage: {page_index+1}/{len(urls)}")
                page = self.navigate_url(urls[page_index])
                self.page_container.put({'page':page, 'url': urls[page_index], 'station': self.station_keys[index], 'page_index':page_index})
                self.set_last_index(attr='page')
                i += 1
            
            self.set_last_index(attr='key')
            self.set_last_index(attr='page', action='reset')
            self.set_last_index(attr='saved', action='reset')

            answer = messagebox.askyesno("Notification", "Veuillez changer de serveur vpn!")
            self.station_index += 1
            
            if answer:
                # self.get_pages()
                continue
            else:
                break
                
        # self.scraped = True

    def navigate_url(self, url:str) -> object:
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, randint(0, 2))
            time.sleep(0.2)
            return self.driver.page_source
        except Exception as e:
            print(e)
            self.driver.quit()
            self.switch_driver()
            self.navigate_url(url)

    def get_datas(self) -> None:
        while self.thread_one.is_alive() or not self.page_container.empty():
            if self.page_container.empty():
                time.sleep(2)
            else:
                items = self.page_container.get()
                data, page_index = self.extract_data(items)
                self.data_container.put([data, page_index])

    def set_datas(self) -> None:
        while self.thread_one.is_alive() or self.thread_two.is_alive() or not self.data_container.empty():
            if self.data_container.empty():
                time.sleep(2)
                self.set_datas()
            else:
                data = self.data_container.get()
                print(f"\tEnregistrement ...: {len(data[0])} (station: {data[0][0]['nom_station'] if len(data) and len(data[0]) else '***'} / page index: {data[1]} / session {self.instance_index})")
                self.save_data(data[0], data[1], self.output_name)

    def set_last_index(self,attr='key', action='increment', page_index=0) -> None:
        with open('./config.json', 'r') as jsonFile:
            data = json.load(jsonFile)

        if attr == 'key':
            data["instances"][self.instance_index]["last_scrapped_key"] = 0 if action == 'reset' else data["instances"][self.instance_index]["last_scrapped_key"] + 1
        elif attr == 'page':
            if action == 'set':
                data["instances"][self.instance_index]["page_index"] = page_index
                self.last_indexes["page_index"] = page_index
            elif action == 'reset':
                data["instances"][self.instance_index]["page_index"] = 0
            else:
                data["instances"][self.instance_index]["page_index"] = data["instances"][self.instance_index]["page_index"] + 1
        else:
            data["instances"][self.instance_index]["saved_page"] = 0 if action == 'reset' else page_index

        with open('./config.json', 'w') as jsonFile:
            jsonFile.seek(0)  # rewind
            json.dump(data, jsonFile)
            jsonFile.truncate()
            self.last_indexes = data["instances"][self.instance_index]

    def get_station_urls(self, station_key:int) -> list:
        url = self.generate_url(station_key)
        pages_length = self.get_page_length(self.navigate_url(url[0]))
        # print(pages_length)
        return self.generate_url(station_key, pages_length)

    def generate_url(self, station_key:int, page:int=1) -> list:
        urls = []
        for i in range(1, (page + 1)):
            urls.append(f"https://www.maeva.com/fr-fr/searchlist.php?&acces_direct=1&station_cle={station_key}&etendre_min=30&type_produit_cle%5B0%5D=259&type_produit_cle%5B1%5D=261&type_produit_cle%5B2%5D=281&trier_par=zerank&page={i}")
        return urls 
    
    def get_page_length(self, page:object) -> int:
        soupe = BeautifulSoup(page, 'lxml')
        index_page = int(soupe.find('div', {'id': 'sl-resultats-tri'}).find_all('span', class_='maeva-red')[1].text.strip()) \
            if soupe.find('div', {'id': 'sl-resultats-tri'}).find_all('span', class_='maeva-red') else 1 
        if index_page > 30:
            page_numb = (index_page // 30) if (index_page % 30 == 0) else ((index_page // 30) + 1)
            return page_numb
        return index_page

    def create_file(self, filename:str):
        if not os.path.exists(f"{filename}"):
            with open(f"{filename}", 'w', encoding="utf-16") as file:
                fields_name = [
                    'web-scrapper-order',
                    'date_price',
                    'date_debut', 
                    'date_fin',
                    'prix_init',
                    'prix_actuel',
                    'typologie',
                    'n_offre',
                    'stars',
                    'nom',
                    'localite',
                    'date_debut-jour',
                    'Nb semaines',
                    'cle_station',
                    'nom_station'
                ]
                writers = writer(file)
                writers.writerow(fields_name)

    # def extract_data(self, page:object, station, page_index) -> list:
    def extract_data(self, source_data) -> list:

        def check_and_append(data, start, end, datas):
            if int(data['Nb semaines']) > start and int(data['Nb semaines']) < end:
                datas.append(data)
                # print(data)

        soupe = BeautifulSoup(source_data['page'], 'lxml')
        toasters = soupe.find('div', {"id": "sl-toaster-container"}).find_all('div', class_='toaster')

        datas = []
        station_key = re.sub(r"[(',)]", '', str(source_data['station']['station_key']))
        # print(station_key)

        for toast in toasters:
            residence = toast.find('div', class_="toaster-residence-libelle").text.strip() \
                if toast.find('div', class_="toaster-residence-libelle") else ''
            localisation = toast.find('div', class_="toaster-localization").find('span').text.strip() \
                if toast.find('div', class_="toaster-localization").find('span') else ''
            stars = toast.find('span', class_='toaster-note').text.strip() \
                if toast.find('span', class_='toaster-note') else '0'
            toast_descs = toast.find_all('div', class_="toaster-produit__row")
            if len(toast_descs) > 1:
                
                for toast_desc in toast_descs:
                    dat = {}
                    typologie = toast_desc.find('div', class_="is-h5").text.strip() \
                        if toast_desc.find('div', class_='is-h5') else ''
                    prix_actuel = toast_desc.find('span', class_="toaster-prix-item").text.strip()[:-1] \
                        if toast_desc.find('span', class_="toaster-prix-item") else 0.00
                    prix_init = toast_desc.find('div', class_="toaster-prix-barre").text.strip()[:-1] \
                        if toast_desc.find('div', class_="toaster-prix-barre") else prix_actuel
                    link = 'www.maeva.com' + toast_desc.find("a", class_="ui-maeva-cta-ghost-black", href=True)['href'] \
                        if toast_desc.find("a", class_="ui-maeva-cta-ghost-black", href=True) else None
                    n_offres, date_debut, date_fin = self.get_link_data(link)
                    dat['web-scrapper-order'] = ''
                    dat['date_price'] = str(datetime.now().strftime("%d-%m-%Y")).replace('-', '/')
                    dat['date_debut'] = date_debut
                    dat['date_fin'] = date_fin
                    dat['prix_init'] = prix_init
                    dat['prix_actuel'] = prix_actuel
                    dat['typologie'] = typologie
                    dat['n_offre'] = n_offres
                    dat['stars'] = stars
                    dat['nom'] = residence
                    dat['localite'] = localisation
                    dat['date_debut-jour'] = ''
                    dat['Nb semaines'] = datetime.strptime(date_debut, '%d/%m/%Y').isocalendar()[1]
                    dat['cle_station'] = station_key,
                    dat['nom_station'] = source_data['station']['name']

                    check_and_append(dat, self.start_week, self.end_week, datas)

            else:
                data = {}
                toast_desc = toast_descs[0]  
                typologie = toast_desc.find('div', class_="is-h5").text.strip() \
                    if toast_desc.find('div', class_='is-h5') else ''
                prix_actuel = toast_desc.find('span', class_="toaster-prix-item").text.strip()[:-1] \
                    if toast_desc.find('span', class_="toaster-prix-item") else 0.00
                prix_init = toast_desc.find('div', class_="toaster-prix-barre").text.strip()[:-1] \
                    if toast_desc.find('div', class_="toaster-prix-barre") else prix_actuel
                link = 'www.maeva.com' + toast_desc.find("a", class_="ui-maeva-cta-ghost-black", href=True)['href'] \
                    if toast_desc.find("a", class_="ui-maeva-cta-ghost-black", href=True) else None
                n_offres, date_debut, date_fin = self.get_link_data(link)
                data['web-scrapper-order'] = ''
                data['date_price'] = str(datetime.now().strftime("%d-%m-%Y")).replace('-', '/')
                data['date_debut'] = date_debut
                data['date_fin'] = date_fin
                data['prix_init'] = prix_init
                data['prix_actuel'] = prix_actuel
                data['typologie'] = typologie
                data['n_offre'] = n_offres
                data['stars'] = stars
                data['nom'] = residence
                data['localite'] = localisation
                data['date_debut-jour'] = ''
                data['Nb semaines'] = datetime.strptime(date_debut, '%d/%m/%Y').isocalendar()[1]
                data['cle_station'] = station_key,
                data['nom_station'] = source_data['station']['name']
                # if int(data['Nb semaines']) > self.start_week and int(data['Nb semaines']) < self.end_week:
                #     datas.append(data)

                check_and_append(data, self.start_week, self.end_week, datas)

        return datas, source_data['page_index']
    
    def get_link_data(self, url:str):
        """ function to get dates in url """
        url_params = parse_qs(urlparse(url).query)
        sep = '/'
        try:
            n_offres = sep.join(url_params['id'][0].split('-')[::-1])
            date_debut = sep.join(url_params['date_debut'][0].split('-')[::-1])
            date_fin = sep.join(url_params['date_fin'][0].split('-')[::-1])
            return n_offres, date_debut, date_fin
        except KeyError:
            return 

    def switch_driver(self) -> None:
        """ function to make switch driver """
        self.drivers = self.drivers[1:] + self.drivers[0:1]
        self.driver.quit()
        self.current_driver = self.drivers[0]
        match self.current_driver:
            case 'chrome':
                self.driver = webdriver.Chrome(options=self.chrome_options)


    def save_data(self, data:dict, page_index:int, filename:str) -> bool:
        df = pd.DataFrame(data)
        try:
            df.to_csv(filename, mode='a', index=False, header=False, encoding='utf-16')
            self.set_last_index(attr='saved', action='set', page_index=page_index)
            return True
        except Exception as e:
            print(e)

    def schedule_check(self):
        if self.thread_one.is_alive() or self.thread_two.is_alive() or self.thread_three.is_alive:
            threading.Timer(5.0, self.schedule_check).start()
            print("!!!!!!! check !!!!!!!")
        else:
            print("*************************** Done ************************")

if __name__=='__main__':
    MaevaScrap(0)
    MaevaScrap(1)
