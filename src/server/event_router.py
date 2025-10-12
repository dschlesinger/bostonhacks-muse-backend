import time
from detector.model import gather_sample, print_data_points

from typing import Dict

async def route_frontend_ping(message: Dict, manager: 'ConnectionManager') -> None:

    print(message)
    
    match message['type']:

        case 'start_artifact_sample':

            dp = gather_sample(classification=message['data']['classification'])

            r = None

            if dp:

                r = dp.anom.data.T.tolist()

            await manager.artifact_detected(r)

        case 'print_data':

            print_data_points()
        
        case _:

           print(f'Ping of type {message['type']} is unknown')