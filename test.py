test_to_run: str = input('What test do you want to run?: ')

match test_to_run:

    case 'websocket':
        import uvicorn
        from server.websocket import app, manager
        manager.test = True
        uvicorn.run(app, host="0.0.0.0", port=8000)

    case 'eeg':
        from detector.muse import eeg_loop

        eeg_loop()

    case 'data-eeg':
        from detector.detect import detect_anamolies
        import pandas as pd, numpy as np, matplotlib.pyplot as plt
        from main.config import Settings

        SENSORS = ['TP9', 'AF7', 'AF8', 'TP10']

        data = pd.read_csv('EEG_recording_2025-10-12-00.38.00.csv')

        timestamps = data['timestamps'].to_numpy()
        buffer = data[SENSORS].to_numpy()
        start = Settings.BUFFER_LENGTH
        print(len(timestamps))
        r = len(timestamps) - 1 - 2 * Settings.BUFFER_LENGTH

        print(r)

        events = []

        for i in range(r):

            s = slice(start + i, start + i + Settings.BUFFER_LENGTH)

            if i == r - 1: print(len(events))

            detect_anamolies(buffer[s], timestamps[s], events)

        fig, axs = plt.subplots(4, 1)

        axs = axs.flatten()

        for i, ax in enumerate(axs):

            for e in events:

                ax.fill_between(np.linspace(e.start, e.end, num=1000), -200, 200, color='blue', alpha=0.5)

            ax.plot(timestamps[Settings.BUFFER_LENGTH:], buffer[Settings.BUFFER_LENGTH:, i])

        plt.savefig('deltas.png')
        
    case 'dp-ser':
        from detector.detect import Anomaly
        from detector.model import DataPoint
        import numpy as np, json
        
        a = Anomaly(
            start=0,
            end=0,
            data=np.array([0, 0, 0])
        )
        
        d = DataPoint(
            classification='blah',
            anom=a
        )
        
        print(d.model_dump_json())
        
        with open(f'data_store/example.json', 'w') as f:
        
            f.write(json.dumps([json.loads(di.model_dump_json()) for di in [d, d]]))

    case _:
        raise Exception(f'{test_to_run} is not an option')