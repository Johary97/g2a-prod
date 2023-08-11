import subprocess
import dotenv
import time
import os

def activate_deactivate_connection(connection_id, status):
    command = ["sudo", "nmcli", "con", status, "id", connection_id]
    try:
        subprocess.run(command, check=True)
        print("Connection " + status)
    except subprocess.CalledProcessError as e:
        print("Error " + status + " connection:", e)

def refresh_connection():
    dotenv.load_dotenv()
    connection_id = os.environ.get('CONNECTION_ID')
    system_name = os.environ.get('SYSTEM')

    if system_name == 'linux':
        try:
            print("Déconnexion ...")
            activate_deactivate_connection(connection_id,"down")
            time.sleep(5)
        except :
            pass

        try:
            print("Reconnexion ...")
            activate_deactivate_connection(connection_id,"up")
            time.sleep(5)
        except:
            pass

    if system_name == 'windows':
        print('\n********************************************************************************')
        touche = input('\n**** Veuillez changer d\'adresse IP puis appuiez sur la touche "Entrer" (ici) **** \n')
        if touche:
            return
            

