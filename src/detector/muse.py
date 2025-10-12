import threading, numpy as np, matplotlib.pyplot as plt, asyncio
from typing import Union

from muselsl import stream, list_muses, view
from pylsl import StreamInlet, resolve_byprop
from time import sleep

from main.config import Settings
from detector.detect import detect_anamolies

buffer = np.zeros((Settings.BUFFER_LENGTH,4))
timestamp_buffer = np.zeros((Settings.BUFFER_LENGTH,))

muse_has_buffered = False
stream_started = False
events = []

# Lock for threading safely
lock = threading.Lock()

class MuseNotConnected(Exception):
    pass

def connect_to_eeg() -> Union['inlet', None]:
    """Returns inlet else none"""
    global stream_started

    # Create and set event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:

        print('Finding muses...')
        muses = list_muses()

        print('muses found', muses)

        # Handles len == 0 or None
        if not muses:
            print('No muses found')
            return None
        
        def stream_handler(address: str):
            global stream_started

            import asyncio
            asyncio.set_event_loop(asyncio.new_event_loop())
            stream(address=address)
            
        muse_thread = threading.Thread(target=stream_handler, args=(muses[0]['address'],), daemon=True)
        muse_thread.start()

        muse_view = threading.Thread(target=view, daemon=True)
        muse_view.start()

        sleep(10)

        streams = resolve_byprop('type', 'EEG', timeout=5)
        try:
            inlet = StreamInlet(streams[0])  # IndexError if streams is empty
        except IndexError:
            raise Exception('Could not find stream')

        return inlet
    
    except Exception as e:
        return None

def eeg_loop(num_samples_to_buffer: int = Settings.BUFFER_LENGTH) -> None:
    global buffer, timestamp_buffer, muse_has_buffered, events

    total_number_off_sample: int = 0

    # Connect to eeg
    print('Connecting to EEG')
    inlet = connect_to_eeg()

    while True:

        try:

            if inlet is None:
                raise MuseNotConnected()
                
            samples, timestamps = inlet.pull_chunk(timeout=1, max_samples=Settings.MAX_SAMPLES_PER_CHUNK)

            samples = np.array(samples)[:, :4]

            timestamps = np.array(timestamps)

            num_samples = samples.shape[0]

            total_number_off_sample += num_samples

            if total_number_off_sample == 345:

                fig, axs = plt.subplots(4, 1)

                axs = axs.flatten()

                for i, ax in enumerate(axs):

                    ax.plot(timestamp_buffer, buffer[:, i])

                plt.savefig('test.png')

            if num_samples == 0:
                raise MuseNotConnected()
            
            buffer = np.concat([buffer[num_samples:], samples])
            timestamp_buffer = np.concat([timestamp_buffer[num_samples:], timestamps])

            # Give time to buffer
            if total_number_off_sample > num_samples_to_buffer:

                if not muse_has_buffered: print('Muse has buffered')

                muse_has_buffered = True
            
                with lock:

                    detect_anamolies(buffer, timestamp_buffer, events)

        except KeyboardInterrupt:
            pass
        except MuseNotConnected:

            print('Muse disconnected attempting reconnect')

            sleep(3)
            inlet = connect_to_eeg()
            continue