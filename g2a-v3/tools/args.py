import argparse
from datetime import datetime, timedelta


def main_arguments() -> object:

    def get_monday():
        return str((datetime.now() - timedelta(days = datetime.now().weekday())).strftime("%d/%m/%Y"))

    parser = argparse.ArgumentParser(description="Booking program",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--platform', '-p', dest='platform',
                        default='booking', help="Site source")
    parser.add_argument('--action', '-a', dest='action', default='',
                        help="""Tâche à faire: \n \t 'init': actualiser la liste des destinations. | 'start': Lancer le scraping des annonces. | 'clean': pour nettoyer le résultat""")
    parser.add_argument('--stations', '-s', dest='stations', default='', help="Nom du fichier contenant la liste des stations")
    parser.add_argument('--name', '-n', dest='name',
                        default='', help="Nom du fichier qui va contenir les donner")
    parser.add_argument('--start-date', '-b', dest='start_date',
                        default='', help="Date début format 'dd/mm/YYYY'")
    parser.add_argument('--end-date', '-e', dest='end_date',
                        default='', help="Date fin format 'dd/mm/YYYY'")
    parser.add_argument('--log-file', '-l', dest='log',
                        default='', help="Nom du fichier log")
    parser.add_argument('--frequency', '-f', dest='frequency',
                        default='', help="Frequence du scrap \n \t '3' : pour frequence de 3 jours | '7' pour frequence de 7 jours | 'all' : pour tous les frequences")
    parser.add_argument('--storage', '-st', dest='storage',
                        default='', help="Chemin de stockage du fichier contenant les resultats")
    parser.add_argument('--week-scrap', '-w', dest='date_price', default=get_monday(), help="Date du lundi de la semaine à scraper format 'dd/mm/YYYY'")
    parser.add_argument('--destinations', '-d', dest='destinations', default='', help="Nom du fichier contenant la liste des destinations")
    parser.add_argument('--cycle', '-c', dest='cycle', default='', help="Cycle de scrap, la connexion sera réinitialisée à chaque fin de cycle.")
    parser.add_argument('--principal-program','-fp', dest='principal', default=None, help="Seul le programme principale peut changer l'adresse IP.")
    return parser.parse_args()


ARGS_INFO = {
        '-a': {'long': '--action', 'dest': 'action', 'help': """Tâche à faire: \n \t
        'init': Récupération des urls à scraper. | 'start': Lancer le scraping des annonces. | 'clean': Nettoyer le résultat"""},
        '-d': {'long': '--destinations', 'dest': 'destinations', "help": "chemin du fichier contenant les destinations"},
        '-n': {'long': '--name', 'dest': 'name', "help": "Nom du fichier qui va contenir les donner"},
        '-st': {'long': '--storage', 'dest': 'storage', "help": "Chemin de stockage du fichier contenant les resultats"},
        '-f': {'long': '--frequency', 'dest': 'frequency', "help": "Frequence du scrap \n \t '3' : pour frequence de 3 jours | '7' pour frequence de 7 jours | 'all' : pour tous les frequences"},
        '-b': {'long': '--start-date', 'dest': 'start_date', "help": "Date début format 'dd/mm/YYYY'"},
        '-e': {'long': '--end-date', 'dest': 'end_date', "help": "Date fin format 'dd/mm/YYYY'"},
        '-l': {'long': '--log-file', 'dest': 'log', "help": "Nom du fichier log"},
        '-w': {'long': '--week-scrap', 'dest': 'date_price', "help": "Date du lundi de la semaine à scraper"},
        '-s': {'long': '--stations', 'dest': 'stations', "help": "Nom du fichier contenant la liste des stations ou regions"},
        '-c': {'long': '--cycle', 'dest': 'cycle', 'help': "Cycle de scrap, la connexion sera réinitialisée à chaque fin de cycle."},
        '-fp': {'long': '--principal-program', 'dest': 'principal', 'help': "Seul le programme principale peut changer l'adresse IP."}
    }

def check_arguments(args, required):
    miss = []

    for item in required:
        if not getattr(args, ARGS_INFO[item]['dest']):
            miss.append(
                f'{item} ou {ARGS_INFO[item]["long"]} ({ARGS_INFO[item]["help"]})')

    return miss