import threading, time, matplotlib.pyplot as plt, json, \
    numpy as np, math, scipy

from pydantic import BaseModel, model_serializer
from detector.detect import Anomaly
from detector.muse import events

from itertools import groupby
from dtaidistance import dtw
from typing import Dict, List, Optional

lock = threading.Lock()

class DataPoint(BaseModel):

    classification: str | None
    anom: Anomaly
    
    @model_serializer(mode='plain')
    def model_ser(self) -> Dict:
        return {
            'anom': json.loads(self.anom.model_dump_json()),
            'classification': self.classification,
        } 

class NoDatasetLoaded(Exception):
    pass
        
def pad_center(d: List[np.ndarray], max_len: int | None = None) -> np.ndarray:
    
    max_len = max(*[di.data.shape[1] for di in d], max_len or 0)

    padded = []
    
    for di in d:
        
        pad_needed = max_len - di.data.shape[1]
            
        left_pad, right_pad = pad_needed // 2, math.ceil(pad_needed / 2)
        
        p = np.pad(di.data, ((0, 0), (left_pad, right_pad)), mode='mean')
        
        padded.append(p)
        
    return np.array(padded)

model = None

class Model(BaseModel):
    """Dynamic Time Warp based on previous data points"""
    
    datapoints: Optional[List[DataPoint]] = None
    
    @property
    def dataset_loaded(self) -> bool:
        return self.datapoints is not None
    
    def load_data(self, filepath: str) -> None:
        
        datapoints = []
        
        with open(filepath, 'r') as e:
            rd = json.load(e)
            for dp in rd:
                
                an = dp['anom']
                
                a = Anomaly(
                    start=an['start'],
                    end=an['end'],
                    data=np.array(an['data']),
                    final=True,
                )
                
                d = DataPoint(
                    classification=dp['classification'],
                    anom=a
                )
                
                datapoints.append(d)
                
        self.datapoints = datapoints
        
    def predict(self, artifact: Anomaly) -> str:
        
        if self.datapoints is None:
            
            raise NoDatasetLoaded
        
        x = artifact.data
        
        classes = [dp.classification for dp in self.datapoints]
        
        print(x.shape)
        
        w = pad_center([dp.anom.data for dp in self.datapoints], max_len=x.shape[1])
        
        if w.shape[1] > x.shape[1]:
            # Pad x to reach w
            diff = w.shape[1] - x.shape[1]
        
            left_pad, right_pad = diff // 2, math.ceil(diff / 2)
            
            x = np.pad(x, ((left_pad, right_pad)), mode='mean')
            
        values = []
        
        for di in w:
            
            values.append(sum([dtw.distance_fast(xi, di) for xi, di in zip(x, di)]))
            
        cls_choice = []
        cls_values = []
        
        z = sorted(list(zip(values, classes)), key=lambda a: a[1])
            
        for c, vls in groupby(z, key=lambda a: a[1]):
            
            vls = [v[0] for v in list(vls)]
            
            cls_choice.append(c)
            cls_values.append(sum(vls) / len(vls))

        a = np.array(cls_values)
        
        a = (a - a.mean()) / a.std()
        
        probs = scipy.special.softmax(a)
        
        # for pro, cls in zip(probs, cls_choice):
            
        #     print(f'\t{cls}: {pro.item():.2f}')
        
        return cls_choice[probs.argmin().item()]
            
datapoints = []

# Key for checking new event is new
previous_event: float | None = None


def check_for_emission(model_arg: Optional[Model] = None) -> None:
    global previous_event, model
    
    model = model_arg or model
    
    if model is None or model.datapoints is None:
        
        raise NoDatasetLoaded
    
    if previous_event is None and events:
        
        with lock:
            
            previous_event = events[-1].start
            
    elif events:
        
        for e in events[::-1]:

            if e.start == previous_event:
                # We found our refrence
                break

            if e.start != previous_event and e.final:
                
                # Classify
                
                classification = model.predict(e)

                # we have a new event
                print(f'Emmited event {classification}')

                break

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

def remove_last_sample() -> None:
    
    if datapoints:

        datapoints.pop(-1)
        
def reset_datapoints() -> None:
    global datapoints
    
    datapoints = []
    
def save_data(name: str) -> None:
    
    with open(f'data_store/{name}.json', 'w') as f:
    
        f.write(json.dumps([json.loads(di.model_dump_json()) for di in datapoints]))
        
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