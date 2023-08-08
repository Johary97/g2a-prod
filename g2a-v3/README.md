# Twenit scraper programs

Contain all programs of scraping by TwenIt

## Environment Variables

To run this project, you will need to add the following environment variables to your .env file

`API_URL`
`OUTPUT_FOLDER`
`STATICS_FOLDER`
`LOGS`
`ANOTHER_API_KEY`
`G2A_API_URL=https://g2a-api-dev.nexties.fr/api/`
`G2A_API_TOKEN=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpYXQiOjE2OTAzNTc5NjAsImV4cCI6MzI0NTU1Nzk2MCwicm9sZXMiOlsiUk9MRV9BUEkiLCJST0xFX0FETUlOIiwiUk9MRV9VU0VSIl0sInVzZXJuYW1lIjoic2NyYXBlckBnbWFpbC5jb20ifQ.lXk8P8B92nq8QRSTxx0Rnf3LWQS5Cyx5C7wk-N7aj99rqZbkacNCQDInjvbxGnLKjYCWnV4p11Yob40u7vZryzkYxGLJ3Axb8aKhU4Dy7KakPManVAU0bjEh87C1IbhRhXCP1Vo7iNN0Y8K2rj7Z-GDj5lZrXOTx8D68q5sX25wexbujp1GFLSzljQVThffqpWr12jVJyw2c2qtA_hQ3PAS3gLGz1e5SXygfrpsnVGF-Qepa2xD9Pm2lwX4AgQtA8LCejeGisQbmO7VOmEqDAX_VDS6hs_NCglOLi3lAnxYq9_arMD25ZI53G-iiIHW0T_IfV1BqOuPrYtDiuT6d4A`

## Deployment

To run a program

- All filename must be with extension
- Dates format: dd/mm/YYYY

### Maeva

- Destination list initialization

  ```bash
  python g2a-v3 -p "maeva" -a "init" <-s station filename> <-d destination filename> <-l log filename>
  ```

  Exemple:

  ```bash
  python g2a-v3 -p "maeva" -a "init" -d "maeva_destination5.json" -s "stations5.json" -l "d_station_log_5.json"
  ```
- Scrap annonces

  ```bash
  python maeva.py -a "start" <-d destination filename> <-l log filename> <-b start date> <-e end date> <-st output_filename> [-w date price]
  ```

  Exemple:

  ```bash
  g2a-v3 -p "maeva" -a "start" -b "15/05/2023" -e "31/10/2023"  -d "maeva_destination1.json" -st "maeva_part_1.csv"  -l "log_1.json"
  ```

  ```bash
  g2a-v3 -p "maeva" -a "start" -b "15/05/2023" -e "31/10/2023"  -d "maeva_destination1.json" -st "maeva_part_1.csv"  -l "log_1.json" -w "15/05/2023"
  ```

### Booking

- Scrap annonces

  ```bash
  python g2a-v3 -p "booking" -a "start" <-n name> <-d destination filename> <-l log filename> <-b start date> <-e end date> <-f frequence> [-w date price]
  ```

  Exemple:

  ```bash
  python g2a-v3 -p "booking" -a "start" -n "test" -b "15/05/2023" -e "22/05/2023" -l "log.json" -f "3" -d "destination_id.csv"
  ```

  ```bash
  python g2a-v3 -p "booking" -a "start" -n "test" -b "15/05/2023" -e "22/05/2023" -l "log.json" -f "3" -d "destination_id.csv" -w "15/05/2023"
  ```

### Campings

- Destination list initialization

  ```bash
  python g2a-v3 -p "campings" -a "init" <-s regions list filename> <-d destination filename> <-b start date> <-e end date> <-l log>
  ```
  Exemple:

  ```bash
  python g2a-v3 -p "campings" -a "init" -d "campings_destination5.json" -s "regions5.json" -b "15/05/2023" -e "30/05/2023" -l "log.json"
  ```
- Scrap annonces

  ```bash
  python g2a-v3 -p "campings" -a "start" <-d destination filename> <-l log filename> [-w date price]
  ```
  Exemple:

  ```bash
  python g2a-v3 -p "campings" -a "start" -d "campings_destination5.json" -l "campings_5.json" -w "15/05/2023"
  ```
