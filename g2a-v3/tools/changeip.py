import subprocess
import dotenv
import time

def activate_deactivate_connection(connection_id, status):
    command = ["nmcli", "con", status, "id", connection_id]
    try:
        subprocess.run(command, check=True)
        print("Connection " + status)
    except subprocess.CalledProcessError as e:
        print("Error " + status + " connection:", e)

def refresh_connection():
    dotenv.load_dotenv()
    connection_id = os.environ.get('CONNECTION_ID')

    activate_deactivate_connection(connection_id,"down")
    time.sleep(5)
    activate_deactivate_connection(connection_id,"up")
    time.sleep(5)