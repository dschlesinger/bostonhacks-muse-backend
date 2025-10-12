import threading, time, matplotlib.pyplot as plt, math

from pydantic import BaseModel
from detector.detect import Anomaly
from detector.muse import events

lock = threading.Lock()

class DataPoint(BaseModel):

    classification: str | None
    anom: Anomaly

datapoints = []

def gather_sample(classification: str) -> DataPoint | None:
    global datapoints

    print('Gathering sample')

    prev_event_st: int = None
    found_datapoint: DataPoint | None = None

    with lock:

        if events:

            prev_event_st = events[-1].start
        
        else:

            prev_event_st = 0

    break_while_loop: bool = False

    while True:

        with lock:

            for e in events[::-1]:

                if e.start == prev_event_st:
                    # We found our refrence
                    break

                if e.start != prev_event_st and e.final:

                    # we have a new event
                    print('Found sample')

                    found_datapoint = DataPoint(
                        classification=classification,
                        anom=e.copy()
                    )

                    datapoints.append(found_datapoint)

                    break_while_loop = True

                    break
            
            if break_while_loop:
                break

            time.sleep(0.1)
    
    return found_datapoint

def print_data_points() -> None:

    print(len(datapoints))

    if datapoints:

        # Graph datapoints
        fig, axs = plt.subplots(len(datapoints), 4, figsize=(12, 3*len(datapoints)))

        # Handle single datapoint case (axs won't be 2D)
        if len(datapoints) == 1:
            axs = [axs]

        for dp, ax_row in zip(datapoints, axs):

            for i, a in enumerate(ax_row):

                a.plot(dp.anom.data[:, i])
                a.set_ylabel(f'Channel {i}')

        plt.tight_layout()
        plt.savefig('datapoints.png')
        plt.close()