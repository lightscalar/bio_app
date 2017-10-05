from events import Events
from datastore import *
from filters import *
import numpy as np
from queue import Queue
from threading import Thread
from time import time
from watchdog import Watchdog
from utils import Vessel


class Engine(object):
    '''Main data controller for the biomonitor. Listens for data from the
       Oracle, then filters/processes it. If we're recording, we save it
       to the hdf5 datastore. If broadcast is enabled, we fire an event so
       sockets above can handle appropriately shipping data to the UI.'''

    def __init__(self):

        # Set up socket connections/event bus.
        self.events = Events()

        # Boot up datastore/etc.
        self.valid_keys = ['t', 't_sys', 'v', 'filtered']
        self.datastore = DataStore()
        self.session_id = None
        self.is_recording = False
        self.is_broadcasting = True
        self.counter = 0

        # Configure filtering.
        self.allowed_channels = [0, 1]
        self.freq_cutoff = 10
        self.filter_order = 6
        self.downsample_rate = 100
        self.zi = {}
        self.channel_data = {}
        self.buffers_to_watch = []
        for chn in self.allowed_channels:
            self.zi[chn] = np.zeros(self.filter_order)
            self.channel_data[chn] = []
            self.buffers_to_watch.append('buffer-{:02d}.dat'.format(chn))
        self.buffers_to_watch.append('oracle_status.dat')

        # Listen for buffer changes:
        self.watchdog = Watchdog(self.buffers_to_watch)

        # Set up threading to handle i/o in background.
        self.q = Queue()
        nb_workers = 3
        target = self.data_received
        for _ in range(nb_workers):
            worker = Thread(target=target, args=(self.q,), daemon=True)
            worker.start()

        # Listen for data from the server.
        self.watchdog.events.on_change += self.push_to_queue
        self.last_time = time()

    def push_to_queue(self, data):
        '''Add received data to the queue.'''
        self.q.put(data)

    def data_received(self, q):
        '''Data has been received by the server.'''
        while True:
            buffer_name = q.get()
            try:
                d = Vessel(buffer_name)
            except:
                print('Problem reading data.')

            # Oracle status has changed; alert everyone!
            if buffer_name == 'oracle_status.dat':
                connected = d.connected
                if connected:
                    message = 'Data Available'
                else:
                    message = 'Board Not Connected'
                    self.is_recording = False
                status = {}
                status['message'] = message
                status['connected'] = connected
                self.events.on_status(status)
                q.task_done()

            else:
                # Otherwise, new data package is available. Process!
                ichn = int(d.channel_number)

                # Filter the data.
                d.filtered, self.zi[ichn] = lowpass(d.t, d.v,\
                        freq_cutoff=self.freq_cutoff,\
                        filter_order=self.filter_order, zi=self.zi[ichn])

                # Downsample and broadcast the data.
                if self.is_broadcasting:
                    t_down, s_down = downsample(d.t, d.filtered,\
                            self.downsample_rate)
                    package = [ichn, self.downsample_rate, s_down, t_down]
                    self.events.on_data(package)

                # Save the data to h5df store.
                if self.is_recording:
                    for key in self.valid_keys:
                        val = np.array(d.__dict__[key])
                        self.datastore.write(self.session_id, ichn, key, val)

                # End data processing.
                q.task_done()

    def start_recording(self, session_id):
        '''Start saving data to datastore.'''
        print('Setting recording to True')
        self.session_id = session_id
        self.is_recording = True

    def stop_recording(self):
        '''Stop streaming to the datastore.'''
        print('Setting recording to False')
        self.session_id = None
        self.is_recording = False

    def kill(self):
        '''Close the socket connection.'''
        self.server.close()
