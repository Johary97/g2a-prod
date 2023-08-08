from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
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
import csv
import twenitlib.ordergenerator as og


class BookingScraping(object):
    
    def __init__(self, name, start, end, freq) -> None:
        
        self.drivers = ['chrome', 'chrome']
        
        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument('--ignore-certificate-errors')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        # self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--incognito')
        
        self.current_driver = 'chrome'

        self.data_containers = Queue()
        self.page_containers = Queue()
        self.path = self.get_storage(freq)

        self.outputname = f"{self.path}/{name}_{freq}j_{datetime.strptime(start, '%Y-%m-%d').strftime('%d_%m_%Y')}-{datetime.strptime(end, '%Y-%m-%d').strftime('%d_%m_%Y')}.csv" 
        self.scrap_finished = False
        self.stopped = False
        
        self.name = name
        self.frequency = freq

        self.create_file(self.outputname)

        self.urlfilepath = self.generate_url_list(
                name=f"{self.path}/urls/{name}_{freq}j_urls",
                dest_ids="C:/src/destination_id.csv",
                start_date=start,
                end_date=end,
                freq=freq
            )

        self.urls = pd.read_excel(self.urlfilepath)['urls'].to_list()
        self.last_index = self.get_last_url_index()
        self.total = len(self.urls)

        self.code = og.create_code()
        self.order_index = 1

        self.thread_one = Thread(target=self.get_pages)
        self.thread_two = Thread(target=self.get_data)
        self.thread_three = Thread(target=self.set_data)

        self.msg_status = ''

        self.run = True

    def start(self):
        self.run = True
        self.stopped = False
        self.scrap_finnished = False

        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=self.chrome_options)
        
        self.thread_one = Thread(target=self.get_pages)
        self.thread_two = Thread(target=self.get_data)
        self.thread_three = Thread(target=self.set_data)
        
        self.thread_one.start()
        time.sleep(2)
        self.thread_two.start()
        time.sleep(2)
        self.thread_three.start()

        # Commencer à vérifier périodiquement si le process est terminé.
        self.schedule_check(self.thread_one)
        self.schedule_check(self.thread_two)
        self.schedule_check(self.thread_three)

    def stop(self):
        self.run = False

    def schedule_check(self, t):
        if not self.stopped:
            time.sleep(2)
            self.check_if_done(t)

    def check_if_done(self, t):
        # Afficher un message si le process s'arrête

        if self.scrap_finished and self.data_containers.empty() and self.data_containers.empty():
            self.run = False
            self.stopped = True
            print("Scrap terminé avec tous les traitements et enregistrements!!!")

        elif not self.run and self.data_containers.empty() and self.data_containers.empty():
            print("Scrap arreté, traitement et enregistrement terminé!!!")
            self.stopped = True

        elif not t.is_alive():
            print("Information", "Scaping arrêté !")
        else:
            # Revérifier après une seconde
            self.schedule_check(t)
                
    def run_scrapping(self, url:str) -> None:
        """function to start scrapping"""
        pages = list(self.run_driver(url))
        for page in pages:
            datas = self.extract_data(page, url)
            data_saved = self.save_data(datas, 'booking_data.xlsx')
            if not data_saved:
                url = self.driver.current_url
                self.switch_driver()
                self.run_scrapping(url)

    def get_pages(self) -> None:
        for i in range(self.last_index, len(self.urls)+1):
            if self.run:
                if i >= len(self.urls):
                    print('scrapping finished')
                    self.scrap_finished = True
                    self.stopped = True
                    self.driver.quit()
                    sys.exit()

                self.msg_status = f'récupération {i} ...'
                print(f"url {self.urls.index(self.urls[i])}: {self.urls[i]}, reste: {len(self.urls)-self.urls.index(self.urls[i])}")
                try:
                    with open(f"{self.path}/indexes/{self.name}_{self.frequency}j-lastScrapped.txt", 'w') as file:
                        file.write(f"{i}")
                    # self.run_scrapping(self.urls[i])
                    pages = list(self.run_driver(self.urls[i]))
                    self.page_containers.put({'pages': pages, 'url': self.urls[i]})
                    self.clear_page_index()
                except Exception as e:
                    print(e)
                
            else:
                self.msg_status ="Arreté !!!"
                break

    def get_data(self) -> None:
        self.msg_status = 'traitement ...'
        while not self.scrap_finished:
            if self.page_containers.empty():
                time.sleep(2)
                self.get_data()
            else: 
                items = self.page_containers.get()
                url = items['url']
                for item in items['pages']:
                    self.data_containers.put(self.extract_data(item, url))
                self.get_data()

    def set_data(self) -> None:
        self.msg_status = 'enregistrement ...'
        while not self.scrap_finished:
            if self.data_containers.empty():
                time.sleep(2)
                self.set_data()
            else:
                data = self.data_containers.get()
                self.save_data(data, self.outputname)
                self.set_data()

    def clear_page_index(self) -> None:
        with open('lastIndex.txt', 'w'):
            pass
            
    def run_driver(self, url=None) -> None:
        def element_exist(selector=By.ID, value=''):
            try:
                self.driver.find_element(selector, value)
                return True
            except:
                return False

        """ function to run driver """
        try:
            self.driver.get(url) 
            self.navigate_last_page_index(self.get_last_page())
            WebDriverWait(self.driver, randint(0, 2))
            time.sleep(1.5)
            yield self.driver.page_source

            try:
                if element_exist(By.ID, 'onetrust-accept-btn-handler'):
                # if self.driver.find_element(By.ID, 'onetrust-accept-btn-handler'):
                    self.driver.find_element(By.ID, 'onetrust-accept-btn-handler').click()
            except:
                pass

            time.sleep(.5)
            if self.driver.find_elements(By.CLASS_NAME, 'f9d6150b8e'):
                while not self.driver.find_elements(By.CLASS_NAME, 'f9d6150b8e')[1].get_property('disabled'):
                    self.driver.find_elements(By.CLASS_NAME, 'f9d6150b8e')[1].click()
                    WebDriverWait(self.driver, randint(0, 2))
                    with open('lastIndex.txt', 'w') as file:
                        file.write(str(self.get_last_page() + 1))
                    yield self.driver.page_source
                with open('lastIndex.txt', 'w') as f:
                    f.write(str(self.get_last_page() + 1))
            else:
                pass
        except Exception as e:
            print(e)
            with open('AttributeError.txt', 'a') as file:
                file.write(f"{url}\n")
                self.switch_driver()
                self.run_driver(url)
                
    def navigate_last_page_index(self, index_page:int=0) -> None:
        index = 0
        if index_page > 0:
            while index != index_page:
                print('not equal')
                index += 1
                self.driver.find_elements(By.CLASS_NAME, 'f9d6150b8e')[1].click()
                
    def get_last_url_index(self) -> int:
        try:
            with open(f"{self.path}/indexes/{self.name}_{self.frequency}j-lastScrapped.txt", 'r') as file:
                index = file.readline()
                return int(index) if index else 0
        except FileNotFoundError as e:
            print(e)
            return 0
        
    def get_last_page(self) -> int:
        try:
            with open('lastIndex.txt', 'r') as f:
                index = f.readline()
                return int(index) if index else 0
        except FileNotFoundError as e:
            print(e)
            return 0

    def extract_data(self, page:object, url:str) -> dict:

        data = []

        soupe = BeautifulSoup(page, 'lxml')
        cards = soupe.find_all('div', {'data-testid':"property-card"})
        for card in cards:
            nom = card.find('div', {'data-testid':"title"}).text.replace('\n', '') \
                if card.find('div', {'data-testid':"title"}) else ''
            star = card.find('div', {'data-testid':"rating-stars"}) \
                if card.find('div', {'data-testid':"rating-stars"}) else ''
            localite = card.find('span', {'data-testid':"address"}).text.replace('\n', '') \
                if card.find('span', {'data-testid':"address"}) else ''
            tax = card.find('div', {'data-testid':'taxes-and-charges'}).text \
                if card.find('div', {'data-testid':"taxes-and-charges"}) else 0
            taxe = 0 if 'comp' in tax else int(tax.split('€')[1])
            prix_actuel = int(card.find('span', class_='fcab3ed991').text[2:].replace(' ', '')) \
                if card.find('span', class_='fcab3ed991') else 0
            prix_init = card.find('span', class_='c5888af24f').text[2:].replace(' ', '') \
                if card.find('span', class_='c5888af24f') else 0
            prix_init = int(prix_init) if prix_init != 0 else prix_actuel
            typologie = card.find('span', class_="df597226dd").text.replace('\n', '') \
                if card.find('span', class_="df597226dd") else ''
            date_prix = (datetime.now() + timedelta(days=-datetime.now().weekday())).strftime('%d/%m/%Y')
            date_debut, date_fin = self.get_dates(url)
            data.append({
                'nom': nom,
                'n_offre': '',
                'date_debut': date_debut,
                'date_fin': date_fin,
                'localite': localite,
                'prix_actuel': prix_actuel,
                'prix_init': prix_init,
                'typologie': typologie,
                'date_price': date_prix,
                'Nb semaines': datetime.strptime(date_debut, '%d/%m/%Y').isocalendar()[1],
                'date_debut-jour': '',
                'web-scraper-order': og.get_fullcode(self.code, self.order_index)
            })

            self.order_index += 1 
        
        # data['nom'] = noms
        # data['n_offre'] = n_offres
        # data['date_debut'] = dates_debut
        # data['date_fin'] = dates_fin
        # # data['stars'] = stars
        # data['localite'] = localites
        # data['prix_actuel'] = prix_actuels
        # # data['prix_actuel_taxe'] = prix_actuel_taxes
        # data['prix_init'] = prix_inits
        # data['typologie'] = typologies
        # data['date_price'] = dates_prix
        # data['Nb semaines'] = nb_semaines
        # data['date_debut-jour'] = date_debut_jours
        # data['web-scrapper-order'] = web_scrapper_orders
            
        print(data)
            
        return data     

    def create_file(self, filename:str) -> None:
        """ function to create new excel file where data will be stored """
        if not os.path.exists(f"{filename}"):
            with open(filename, 'w') as file:
                field_names = [
                        'web-scraper-order',
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
                        'Nb semaines'
                    ] 
                writers = csv.writer(file)
                writers.writerow(field_names)

    def get_storage(self, freq:str):
        folder = 'C:/Files/tmp/results/booking/'+(datetime.now() + timedelta(days=-datetime.now().weekday())).strftime('%d_%m_%Y')
        
        if not os.path.exists(folder):
            os.makedirs(folder)

        file_folder = f"{folder}/{freq}j"
        
        if not os.path.exists(file_folder):
            os.makedirs(file_folder)
            os.makedirs(f"{file_folder}/urls")
            os.makedirs(f"{file_folder}/indexes")

        return file_folder

    def save_data(self, data:dict, filename:str) -> bool:
        
        """ function to append data at the excel file """
        # return True
        try:
            field_names = [
                        'web-scraper-order',
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
                        'Nb semaines'
                    ]

            with open(filename, 'a', newline='') as f_object:
                dictwriter_object = csv.DictWriter(f_object, fieldnames=field_names)
                dictwriter_object.writerows(data)
                return True
        except Exception as e:
            with open('SaveDataError.txt', 'a') as file:
                file.write(f"{e}")
                return False     
    
    # def save_data(self, data:dict, filename:str) -> bool:
    #     last_index = int(len(pd.read_excel(filename)) + 1)
    #     df = pd.DataFrame({
    #         'web-scrapper-order': data['web_scrapper_order'],
    #         'date_price': data['date_prix'],
    #         'date_debut': data['date_debut'],
    #         'date_fin': data['date_fin'],
    #         'prix_init': data['prix_init'],
    #         'prix_actuel': data['prix_actuel'],
    #         'prix_actuel_taxes': data['prix_actuel_taxe'],
    #         'typologie': data['typologie'],
    #         'n_offre': data['n_offres'],
    #         'stars': data['stars'],
    #         'nom': data['noms'],
    #         'localite': data['localite'],
    #         'date_debut-jour': data['date_debut_jour'],
    #         'Nb semaines': data['nb_semain']
    #     })

    #     try:
    #         with pd.ExcelWriter(filename, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
    #             if last_index >= 1000:
    #                 sheet_index = (last_index % 1000) + 1
    #                 df.to_excel(writer, sheet_name=f'Sheet{sheet_index}', startrow=last_index, header=False, index=False)
    #             else:
    #                 df.to_excel(writer, sheet_name=f'Sheet1', startrow=last_index, header=False, index=False)
    #             return True
            
    #     except Exception as e:
    #         with open('SaveDataError.txt', 'a') as file:
    #             file.write(f"{e}\n{datetime.now().isoformat()}")
    #             return False
    
    def switch_driver(self) -> None:
        """ function to make switch driver """
        self.drivers = self.drivers[1:] + self.drivers[0:1]
        self.driver.quit()
        self.current_driver = self.drivers[0]
        match self.current_driver:
            case 'chrome':
                self.driver = webdriver.Chrome(options=self.chrome_options)
    
    # def create_file(self, filename:str) -> None:
    #     """function to create new file where data will be stored"""
        
    #     if not os.path.exists(f"{filename}"):
    #         df = pd.DataFrame(
    #             columns = [
    #                 'web-scrapper-order',
    #                 'date_price',
    #                 'date_debut', 
    #                 'date_fin',
    #                 'prix_init',
    #                 'prix_actuel',
    #                 'prix_actuel_taxes',
    #                 'typologie',
    #                 'n_offre',
    #                 'stars',
    #                 'nom',
    #                 'localite',
    #                 'date_debut-jour',
    #                 'Nb semaines'
    #             ]
    #         )
    #         df.to_excel(f"{filename}", index=False)
    #         print('file created')
    #     print('file already exist')

    def generate_url(self, checkin:str, checkout:str, dest_id:int) -> str:
        return f"https://www.booking.com/searchresults.fr.html?label=gog235jc-1DCAYoTUIGc2F2b2llSA1YA2hNiAEBmAENuAEXyAEM2AED6AEB-AECiAIBqAIDuAK37uOQBsACAdICJDJjMjgxMmVhLTIyM2MtNDI1Mi1iYTM4LTA3MmE4MjI3MWFkMdgCBOACAQ&sid=086e078aef1832684e5d5671c99a12b1&aid=356980&dest_id={dest_id}&dest_type=region&nflt=ht_id%3D204%3Brpt%3D1&shw_aparth=0&checkin={checkin}&checkout={checkout}&selected_currency=EUR"
                
    def generate_url_list(self, name:str, dest_ids:str, start_date:str, end_date:str, freq:object) -> str:
        start_url = []
        frequencies = []
        if not os.path.exists(f"{name}.xlsx"):
            
            match freq:
                case 'all': frequencies = [1, 3, 7]
                case _: frequencies.append(int(freq))

            df = pd.read_csv(dest_ids)
            dest_ids = df['dest_id']
            for freq in frequencies:
                checkin_date = datetime.strptime(start_date, "%Y-%m-%d")
                checkout_date = datetime.strptime(end_date, "%Y-%m-%d")
                date_space = int((checkout_date - checkin_date).days) + 1

                checkin = datetime.strptime(start_date, "%Y-%m-%d")
                checkout = checkin + timedelta(days=freq)

                for i in range(date_space):
                    for dest_id in dest_ids:
                        start_url.append(self.generate_url(checkin.strftime("%Y-%m-%d"), checkout.strftime("%Y-%m-%d"), dest_id))
                    checkin += timedelta(days=1) 
                    checkout += timedelta(days=1)

            print(len(start_url))
            # start_url = list(reversed(start_url))

            pd.DataFrame({'urls': start_url}).to_excel(f"{name}.xlsx", index=False)
        return f"{name}.xlsx"

    def get_dates(self, url:str) -> tuple:
        """ function to get dates in url """
        url_params = parse_qs(urlparse(url).query)
        try:
            sep = '/'
            return sep.join(url_params['checkin'][0].split('-')[::-1]), sep.join(url_params['checkout'][0].split('-')[::-1])
        except KeyError:
            return    

    def change_output_format(self, defaultfilename:str, file_format:str, outputlocation:str, filename:str):
        df = pd.read_excel(defaultfilename)
        match file_format:
            case 'excel':
                df.to_excel(f"{outputlocation}/{filename}.xslx")
            case 'csv':
                df.to_csv(f"{outputlocation}/{filename}.csv")
    