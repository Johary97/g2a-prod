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