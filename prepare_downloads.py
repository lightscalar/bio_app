from datastore import DataStore
import datetime
import numpy as np
import pandas as pd
import os
import re
from solid_db import SolidDB
from zipfile import ZipFile


AVAILABLE_CHANNELS = ['PZT', 'PPG']
TMP_LOCATION = '.'


def parse_histories(histories):
    '''Cycle through histories and grab the latest version.'''
    history_dict = {}
    unique_histories = []
    for history in histories:
        history_dict[history['uid']] = history
    for key,val in history_dict.items():
        unique_histories.append(val)
    return unique_histories


def create_csv(session_id):
    '''Construct CSV files from recorded data and annotations.'''
    ds = DataStore()
    db = SolidDB('data/db.json')
    files_to_compress = []

    # Load the session from the database.
    session = db.find_by_id(session_id)
    human_id = session['hid'].upper()
    tstamp = session['createdAt']
    tstamp = re.sub(r"\s+", '_', tstamp)
    tstamp = tstamp.replace(':', '')

    # Read channel data and write to CSV files.
    for channel_number, channel_name in enumerate(AVAILABLE_CHANNELS):
        channel_data_present = False
        try:
            channel_data = ds.read_all(session_id, channel_number)
            channel_data_present = True
        except:
            pass

        if channel_data_present:
            try:
                filename = '{}/{}--{}--{}.csv'\
                        .format(TMP_LOCATION, tstamp, human_id, channel_name)
                df = pd.DataFrame(channel_data)
                df = df[['t', 't_sys', 'v', 'filtered']]
                df = df.rename(index=str, columns={'t': 'local_timestamp',\
                        't_sys': 'unix_timestamp', 'v': 'value',\
                        'filtered': 'filtered_value'})
                df.to_csv(filename)
                files_to_compress.append(filename)
            except:
                print('Cannot create data files. No data collected?')

    # Save annotation data.
    filename = 'annotations.csv'
    raw_annotations = db.find_where('annotations', 'session_id', session_id)
    if len(raw_annotations)>0:
        df = pd.DataFrame(raw_annotations)
        df = df[['date', 'time', 'description', 'value', 'units']]
        df.to_csv(filename)
        files_to_compress.append(filename)

    compressed_filename = '/Users/mjl/Desktop/exported_sessions/{}_{}.zip'\
            .format(tstamp, human_id)

    if len(files_to_compress) > 0:
        with ZipFile(compressed_filename, 'w') as f:
            for filename in files_to_compress:
                f.write(filename)
                os.remove(filename)







