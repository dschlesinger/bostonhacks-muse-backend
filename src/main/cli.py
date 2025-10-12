import uvicorn
from server.websocket import app

from detector.muse import eeg_loop

import threading

def main() -> None:

    # Muse loop thread
    muse_loop_thread = threading.Thread(target=eeg_loop)
    muse_loop_thread.start()

    uvicorn.run(app, host="0.0.0.0", port=8000)
    return

if __name__ == '__main__':

    main()