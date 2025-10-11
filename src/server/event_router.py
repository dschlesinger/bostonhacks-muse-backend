import time

from typing import Dict

def route_frontend_ping(message: Dict, manager: 'ConnectionManager') -> None:

    print(message)
    
    match message['type']:

        case 'start_artifact_sample':

            time.sleep(5)

            manager.artifact_detected()
        
        case _:

           print(f'Ping of type {message['type']} is unknown')