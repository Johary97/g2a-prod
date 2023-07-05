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
`G2A_API_TOKEN=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpYXQiOjE2ODYzMTU1MDYsImV4cCI6MzI0MTUxNTUwNiwicm9sZXMiOlsiUk9MRV9BRE1JTiIsIlJPTEVfVVNFUiJdLCJ1c2VybmFtZSI6ImFkbWluZzJhQHlvcG1haWwuY29tIn0.x-E8QOZbcrFWlHkDHWcEkJtcIWf1Sze-fGVavAI_STufGUtz77B3rhxbih5p6gKfC5ZG1sAkIJ9A2j8Lfi0L_PU2_-wGtv181uqLtaZin7wBO20XGDgK_gKKa9Y86B8fXISvWHbufpfFW6uJzSIFr-QL1PhPMtfJ1rxg9LbM-wEf0zmneg1ZFp0L-0pAJqtErurQRaPTSKVvNi2dY-IAB9hnS-Qw3tMDn4-2PpOXE7NU3rHgjhHsWd5bjNjY3RtfGb3IrnZ0yc9Du3jJtP87GVwHxHyPZpqmRe0tw72f58dD5l5SkEMEnENkq__4Z_6w2FlrSCSvOOVhRMmx7s52OQ`

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
