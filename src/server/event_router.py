import time
from detector.model import gather_sample, print_data_points, remove_last_sample, save_data, \
    reset_datapoints
from detector import muse

from typing import Dict

async def route_frontend_ping(message: Dict, manager: 'ConnectionManager') -> None:

    print(message)
    
    match message['type']:

        case 'start_artifact_sample':

            if not manager.test:
                
                dp = gather_sample(classification=message['data']['classification'])

                if dp:

                    artifact_data = dp.anom.data.T.tolist()
                    
                    print('sending sensors', muse.sensors)

                    await manager.artifact_detected([{'sensor': s, 'data': r} for s, r in zip(muse.sensors, artifact_data)]) 
                
            else:

                await manager.artifact_detected([{'sensor': s, 'data': r} for s, r in zip(['A', 'B', 'C', 'D'], [[1, 2], [1, 2], [1, 2], [1, 2]])]) 

        case 'print_data':

            print_data_points()
        
        case 'sample_not_good':

            remove_last_sample()
            
        case 'reset_samples':

            reset_datapoints()
            
        case 'save_data':
            
            save_data(message['data']['name'])
        
        case _:

           print(f'Ping of type {message['type']} is unknown')