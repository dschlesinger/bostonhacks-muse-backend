import time

from typing import Dict

def route_frontend_ping(message: Dict, manager: 'ConnectionManager') -> None:
    
    match message['type']:

        case 'start_artifact_sample':

            time.sleep(5)

            manager.artifact_detected()
        
        case _:

            raise Exception(f'Ping of type {message['type']} is unknown')