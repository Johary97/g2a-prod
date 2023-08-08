from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from queue import Queue
from csv import DictWriter, writer
from unidecode import unidecode
from datetime import datetime, timedelta
import pandas as pd
import requests
import time
import os




class YellowScraping(object):

    def __init__(self, output_name:str, start_date:str, end_date:str) -> None:
        self.start_date = start_date
        self.end_date = end_date
        self.output_name = output_name
        self.base_url = 'https://www.yellohvillage.fr/destination/mer#location'

        self.create_file(self.output_name)
        self.scraping_dates = Queue()
        self.setup_dates()
        self.page_container = Queue()
        self.data_container = []
        self.link_container = Queue()
        self.detail_links = Queue()

        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument('--ignore-certificate-errors')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        # self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--incognito')
        self.current_driver = 'chrome'
        self.drivers = ['chrome', 'chrome']

        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=self.chrome_options)
        self.set_base_page()
        try:
            self.driver.find_element(By.ID, 'didomi-notice-agree-button').click()
        except Exception:
            pass

        time.sleep(3)

        self.scrap()


    def scrap(self) -> None:
        while not self.scraping_dates.empty():
            current_date = self.scraping_dates.get()
            self.set_dates(current_date)
            print(f"scraping date {current_date}")
            time.sleep(2)
            self.scrap_target()
            self.get_target_pages()
            self.get_detail_page(current_date)
            self.get_data()
            self.save_data(self.output_name)
            self.set_base_page()

    def set_base_page(self) -> None:
        self.driver.get(self.base_url)
        time.sleep(2)


    def set_dates(self, date:str) -> None:
        start_date = datetime.strptime(date, '%d/%m/%Y').strftime('%d/%m/%Y')
        end_date = (datetime.strptime(date, '%d/%m/%Y') + timedelta(days=7)).strftime('%d/%m/%Y')
        try:
            self.driver.find_element(By.NAME, 'search_d1').click()
            time.sleep(1)
            self.driver.find_element(By.NAME, 'search_d1').send_keys(start_date)
            time.sleep(2)
            self.driver.find_element(By.NAME, 'search_d2').click()
            time.sleep(1)
            self.driver.find_element(By.NAME, 'search_d2').send_keys(end_date)
            time.sleep(2)
            self.driver.find_element(By.ID, 'reserve_sejour').click()
            self.driver.find_element(By.CLASS_NAME, 'mm-wrapper').click()
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="village_1"]')))
            time.sleep(2)
        except Exception:
            self.set_dates(date)

    def scrap_target(self) -> None:
        print('start getting scrap target')
        targets = ['campings languedoc-roussillon', 'campings provence-alpes-côte d’azur']
        try:
            soupe = BeautifulSoup(self.driver.page_source, 'lxml')
            regions = soupe.find('div', {'id':'list-campings'}).find_all('div', class_='block-region')
            target_data = [region if region.find('h2', class_='titre-region').text.strip().lower() in targets else '' for region in regions]
            target_data.remove('')
            print(f'number of station {len(target_data)}')
            base_links = []
            for item in target_data:
                item = BeautifulSoup(f'{item}', 'lxml')
                titles = item.find_all('h3', class_='titre-village')
                links = ['https://www.yellohvillage.fr/camping/' + unidecode(link.text.strip().lower()[8:].replace(' ', '_')) + '/nos_locations#content' for link in titles]
                base_links.append(links)
            base_links = sum(base_links, []) 
            for link in base_links:
                self.link_container.put(link)
            print('getting scrap target finished')
        except Exception as e:
            time.sleep(3)
            print(e)
            # self.get_scrap_target()

    def get_target_pages(self) -> None:
        print('getting pages')
        while not self.link_container.empty():
            url = self.link_container.get()
            self.driver.get(url) 
            soupe = BeautifulSoup(self.driver.page_source, 'lxml')
            articles = soupe.find('ul', class_='AccommodationList-list').find_all('article', class_='AccomodationBlock')

            for article in articles:
                if article.find('span', class_='AccommodationDetails-label').text.strip() in ['4', '6', '8']:
                    self.detail_links.put('https://www.yellohvillage.fr' + article.find('a', class_='AccomodationBlock-actionBtn',href=True)['href'])
        print('getting pages finished')


    def get_detail_page(self, date:str) -> None:
        while not self.detail_links.empty():
            url = self.detail_links.get()
            self.driver.get(url)
            data = {'page':self.driver.page_source, 'date': date, 'url':self.driver.current_url}
            self.page_container.put(data)

    def get_data(self) -> None:
        print('print getting data')
        while not self.page_container.empty():
            item = self.page_container.get()
            data = self.extract_data(item)
            self.data_container.append(data)

    def save_data(self, filename:str) -> None:
        print('saving data')
        print(f'{self.data_container}')
        self.data_container = sum(self.data_container, [])
        df = pd.DataFrame(self.data_container)
        try:
            df.to_csv(filename, mode='a', index=False, header=False)
            self.data_container = list()

        except Exception as e:
            print(e)
            

    def extract_data(self, data:str) -> dict:
        soupe = BeautifulSoup(data['page'], 'lxml')
        datas = []
        try:
            name = soupe.find('span', class_='SectionHeadAccommodation-village').text.strip() \
                if soupe.find('span', class_='SectionHeadAccommodation-village') else ''
            stars = soupe.find('span', class_='SectionHeadAccommodation-classification').attrs['class'][1][-1] \
                if soupe.find('span', class_='SectionHeadAccommodation-classification') else ''
            stars = stars if stars.isnumeric() else 0
            typology = soupe.find('p', class_='TabItem-text').text.strip() \
                if soupe.find('p', class_='TabItem-text') else ''
            persons = soupe.find_all('li', class_='TechnicalInfo-line')[1].text.strip() \
                if soupe.find_all('li', class_='TechnicalInfo-line') else ''
            localite = soupe.find('p', class_='SectionHeadVillage-location').text.strip().split(',')[0] \
                if soupe.find('p', class_='SectionHeadVillage-location') else ''
            items = soupe.find_all('div', class_='AccommodationAvailabilityInline') \
                if soupe.find_all('div', class_='AccommodationAvailabilityInline') else None

            if items:
                for item in items:
                    price = unidecode(item.find('p', class_='PriceTag-price PriceTag-finalPrice').text.strip()[:-2]).replace(' ', '')
                    dat = {}
                    dat['web-scraper-order'] = ''
                    dat['date_price'] = str((datetime.now() - timedelta(days = datetime.now().weekday())).strftime("%d/%m/%Y"))
                    dat['date_debut'] = data['date']
                    dat['date_fin'] = (datetime.strptime(data['date'], '%d/%m/%Y') + timedelta(days=7)).strftime('%d/%m/%Y')
                    dat['prix_init'] = price
                    dat['prix_actuel'] = price
                    dat['typologie'] = typology
                    dat['n_offre'] = data['url'].split('/')[-1].split('#')[0]
                    dat['stars'] = stars
                    dat['nom'] = name
                    dat['localite'] = localite
                    dat['Nb personnes'] = persons
                    dat['date_debut-jour'] = ''
                    dat['Nb semaines'] = datetime.strptime(data['date'], '%d/%m/%Y').isocalendar()[1]
                    datas.append(dat)
                print(datas)
                return datas
            else:
                return datas
        except Exception as e:
            with open('Error', 'w') as file:
                file.write(f'{e}\n')
            with open('page', 'w') as pagefile:
                pagefile.write(f"{data['page']}  \n")

    def setup_dates(self) -> None:
        start_date = datetime.strptime(self.start_date, '%d/%m/%Y').strftime('%Y/%m/%d')
        end_date = datetime.strptime(self.end_date, '%d/%m/%Y').strftime('%Y/%m/%d')
        dates = pd.bdate_range(start=start_date, end=end_date, freq="C", weekmask="Sat")
        dates = [date.to_pydatetime().strftime("%d/%m/%Y") for date in dates]
        print(dates)
        for date in dates:
            self.scraping_dates.put(date)
        print(f"total dates {self.scraping_dates.qsize()}")
        

    def create_file(self, filename:str) -> None:
        print("creating file")
        if not os.path.exists(f"{filename}"):
            with open(f"{filename}", 'w') as file:
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
                    'Nb personnes',
                    'date_debut-jour',
                    'Nb semaines'
                ]
                writers = writer(file)
                writers.writerow(fields_name)


if __name__=='__main__':
    YellowScraping('data.csv', '1/04/2023', '30/04/2023')
