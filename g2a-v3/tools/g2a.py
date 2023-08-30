import requests
import dotenv
import os
import json
import csv
import time

class G2A:

    def __init__(self, method="get", entity="", params={}, body={}, id=-1):
        dotenv.load_dotenv()

        self.method = method
        self.entity = entity
        self.headers = {
                            'Accept': 'application/json',
                            'Authorization': f'Bearer {os.environ.get("G2A_API_TOKEN")}'
                        }
        self.params = params
        self.body = body
        self.id = id
        self.api_url = os.environ.get("G2A_API_URL")
        self.page = 1

    def set_id(self, id):
        self.id = id

    def set_body(self, body):
        self.body = body

    def set_entity(self, entity):
        self.entity = entity

    def add_file(self, files):
        self.files = files

    def add_header(self, header):
        for key in header.keys():
            self.headers[key] = header[key]

    def set_params(self, params):
        self.params = params

    def set_page(self, page):
        self.page = page

    def execute(self):
        response = {}
        if self.method == 'delete':
            if self.id != -1:
                response = getattr(requests, self.method)(
                    f'{self.api_url}{self.entity}/{self.id}',
                    params=self.params,
                    headers=self.headers
                )
                return response
            else:
                print("Information", "Identifiant non spécifié!!!")

        elif self.method == 'update' or self.method == 'put':
            if self.id != -1:
                response = getattr(requests, self.method)(
                    f'{self.api_url}{self.entity}/{self.id}',
                    params=self.params,
                    headers=self.headers,
                    data=json.dumps(self.body)
                )
                return response
            else:
                print("Information", "Identifiant non spécifié!!!")

        elif self.method == 'getone':
            if self.id != -1:
                response = getattr(requests, 'get')(
                    f'{self.api_url}{self.entity}/{self.id}',
                    params=self.params,
                    headers=self.headers
                )
            else:
                print("Information", "Identifiant non spécifié!!!")
        else:
            if hasattr(self, 'files'):
                response = getattr(requests, self.method)(
                    f'{self.api_url}{self.entity}',
                    params=self.params,
                    data=self.body,
                    files=self.files,
                    headers=self.headers
                )
            else:
                response = getattr(requests, self.method)(
                    f'{self.api_url}{self.entity}?page={self.page}',
                    headers=self.headers,
                    data=self.body
                )

        if response.status_code >= 400:
            response.raise_for_status()

        return response

    @staticmethod
    def delete_multi(entity, ids):
        delete_instance = G2A("delete", entity)
        for item in ids:
            delete_instance.set_id(item)
            try:
                r = delete_instance.execute()
                print(r.status_code)
            except:
                pass

    @staticmethod
    def delete_all(entity):
        while True:
            get_req = G2A(entity=entity)
            res = get_req.execute()
            ids = [item['id'] for item in res.json()]
            if len(ids):
                G2A.delete_multi(entity, ids)
            else:
                break

    @staticmethod
    def post_accommodation(entity, params):
        post_instance = G2A("post", entity)
        post_instance.set_body(params)
        post_instance.add_file({'value_1': (None, '12345')})

        try:
            resp = post_instance.execute()
            return resp.text
        except Exception as e:
            print(e)
            pass
        return "Pass"

    @staticmethod
    def format_data(datas: list) -> str:
        def stringify_dict(item: dict) -> str:
            column_order = ['web-scrapper-order', 'date_price', 'date_debut', 'date_fin', 'prix_init', 'prix_actuel',
                            'typologie', 'n_offre', 'nom', 'localite', 'date_debut-jour', 'Nb semaines', 'cle_station', 'nom_station']
            result = ""
            url = ""

            if 'url' in item.keys():
                url = item['url'].replace('&', '$')[8:]
                item.pop('url')

            for column in column_order:
                v = str(item[column]).replace(',', ' - ').replace('&', ' and ')
                result += f'{v},'

            result += f'{url}'
            return result

        formated_datas = []

        for data in datas:
            formated_datas.append(stringify_dict(data))

        return ";".join(formated_datas)


class CSVUploader(object):

    def __init__(self, freq: str, source: str, log: str, site:str, site_url:str) -> None:
        dotenv.load_dotenv()
        
        self.freq = freq
        self.source = f'{os.environ.get("STATICS_FOLDER")}/{source}'
        self.log = f'{os.environ.get("LOGS")}/{log}'
        self.site = site
        self.site_url = site_url

    def upload(self):
      
        rows = []

        with open(self.source, encoding='utf-8') as csvf:
            csvReader = csv.DictReader(csvf)
            listrow = list(csvReader)

            start = self.get_history('last')

            for i in range(start, len(listrow)):

                if not 'cle_station' in listrow[i].keys():
                    listrow[i]['cle_station'] = ""

                if not 'nom_station' in listrow[i].keys():   
                    listrow[i]['nom_station'] = ""

                rows.append(listrow[i])

                self.set_history('lastrow', i)

                if len(rows) == 50 or i == len(listrow)-1:
                    try:
                        str_data = G2A.format_data(rows)
                        # print(str_data)
                        res = G2A.post_accommodation("accommodations/multi", {
                            "nights": self.freq,
                            "website_name": self.site,
                            "website_url": self.site_url,
                            "data_content": str_data
                        })
                        print(res)
                    except Exception as e:
                        print(e)
                        time.sleep(5)
                        self.upload()
                    
                    rows = []

    def get_history(self, key: str) -> object:
        logs = {}
        try:
            with open(self.log, 'r') as log_file:
                logs = json.load(log_file)
                return logs[key]
        except:
            return 0

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

# G2A.delete_all("reviews")
