import h5py
'''High performance data store for time series data.'''


class DataStore(object):

    def __init__(self, store_name='data/datastore.hdf5'):
        '''Load up the store.'''
        self.store_name = store_name

    def write(self, session_id, channel_number, data_name, data, metadata={}):
        '''Writing data to the datastore.'''
        with h5py.File(self.store_name, 'a') as f:
            # Define path to data; create if necessary.
            channel_number = int(channel_number)
            data_path = '{:s}/{:02d}'.format(session_id, channel_number)
            if data_path not in f:
                group = f.create_group(data_path)
            else:
                group = f[data_path]

            # Push data to dataset. Resize if necessary.
            if data_name in group:
                dset = group[data_name]
                size = dset.shape[0]
                dset.resize(size + data.shape[0], axis=0)
                dset[size:] = data
            else:
                dset = group.create_dataset(data_name, data=data,\
                        maxshape=(None,), chunks=True)

    def read_all(self, session_id, channel_number):
        '''Return dictionary of all data in a given session/channel.'''
        data = {}
        data_path = '{:s}/{:02d}'.format(session_id, channel_number)
        with h5py.File(self.store_name, 'r') as f:
            if data_path in f:
                for key in f[data_path].keys():
                    data[key] = f[data_path][key][:]
        return data


if __name__ == '__main__':
    pass
    # import numpy as np
    # d = DataStore()
    # d.write('mjl.03', 0, 'time', np.random.randn(5000))
    # d.write('mjl.03', 0, 'values', np.random.randn(5000))
