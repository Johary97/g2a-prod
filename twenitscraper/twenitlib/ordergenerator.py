from datetime import datetime, timedelta
import json


def read_product_base() -> dict:
    with open('C:/src/programs/twenitscraper/twenitlib/og.params.json', 'r') as jsonFile:
        data = json.load(jsonFile)
    return data

def increment_product_base() -> None:
    params = read_product_base()
    params['product'] += 1
    with open('C:/src/programs/twenitscraper/twenitlib/og.params.json', 'w') as jsonFile:
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

# tmp = []
# for j in range(5):
#     tmp2 = []
#     last_index = 0
#     for i in range(200):
#         code, last_index = create_code(1670000000, last_index)
#         tmp2.append(code)

#     print(tmp2)
#     tmp.append(tmp2)
#     increment_product_base()

# print(tmp)