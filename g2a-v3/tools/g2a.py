import requests
import dotenv
import os
import json


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
                    f'{self.api_url}{self.entity}',
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

# G2A.delete_all("reviews")
