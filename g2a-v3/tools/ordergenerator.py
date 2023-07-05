from datetime import datetime, timedelta
import json
import dotenv
import os

dotenv.load_dotenv()
project_folder = os.environ.get('PROJECT_FOLDER')

def read_product_base() -> dict:
    with open(f'{project_folder}/tools/og.params.json', 'r') as jsonFile:
        data = json.load(jsonFile)
    return data

def increment_product_base() -> None:
    params = read_product_base()
    params['product'] += 1
    with open(f'{project_folder}/tools/og.params.json', 'w') as jsonFile:
        jsonFile.seek(0)  # rewind
        json.dump(params, jsonFile)
        jsonFile.truncate()

def create_code() -> str:
    today = datetime.now()
    base_product = read_product_base()['product']
    base_code = read_product_base()['base']
    increment_product_base()
    return base_code + today.year*base_product  + today.month*base_product + today.day*base_product + today.hour*base_product + today.minute*base_product + today.second*base_product

def get_fullcode(code: int, index: int):
    return f"{code}-{index}"