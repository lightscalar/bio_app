import numpy as np
from scipy.signal import butter, lfilter
from scipy.interpolate import interp1d


def smart_sample(t, x, target_sampling_rate):
    '''Use cubic spline to downsample.'''
    t, x = np.array(t), np.array(x)
    y = interp1d(t, x, kind='cubic')
    fs = 1/np.median(np.diff(t))
    dt = int(np.ceil(fs/target_sampling_rate))
    idx = range(0, len(x), dt)
    t_ = t[idx]
    x_ = y(t_)
    return t_.tolist(), x_.tolist()


def lowpass(t, y, filter_order=5, freq_cutoff=10, zi=[]):
    '''Lowpass Butterworth filter the signal.'''
    # Determine the sampling rate of the supplied data.
    fs = 1/np.median(np.diff(t))
    nyquist=0.5*fs
    f_low = freq_cutoff/nyquist

    # Create a butterworth filter
    a,b  = butter(filter_order, f_low, 'low', analog=False)

    # Check to see of previous filter delays are passed in.
    if len(zi) == 0:
        zi = np.zeros(filter_order)

    # Filter the actual signal
    y_filt, zf = lfilter(a, b, y, axis=-1, zi=zi)

    # Return BOTH filtered signal and updated tap delays.
    return y_filt, zf


def dumb_downsample(t, x, target_sampling_rate):
    '''Simple downsampling!'''
    # Convert to numpy arrays.
    t, x = np.array(t), np.array(x)

    # Estimate current sampling rate.
    fs = 1/np.median(np.diff(t))
    dt = int(np.ceil(fs/target_sampling_rate))
    idx = range(0, len(x), dt)
    t_ = t[idx].tolist()
    v_ = x[idx].tolist()
    return t_, v_


def downsample(t, x, target_sampling_rate):
    '''Smarter downsampling. We now pad out to appropriate length, and average
       samples appropriately in order to approximately achieve the target
       downsampling rate.
    '''

    if len(t) == 0:
        # Nothing to downsample. So, um. Sort of awkward.
        return t, x

    # Convert to numpy arrays.
    t, x = np.array(t), np.array(x)

    # Estimate current sampling rate.
    fs = 1/np.median(np.diff(t))

    # Calculate the downsample factor, given the target sampling rate.
    R = int(np.ceil(fs/target_sampling_rate))

    # Determine the padding size & pad the data.
    padsize = int(np.ceil(len(x)/R)*R - len(x))
    t = np.append(t, np.zeros(padsize)*np.NaN)
    x = np.append(x, np.zeros(padsize)*np.NaN)

    # Reshape the data.
    x = x.reshape(-1, R)
    t = t.reshape(-1, R)

    # Take the mean along axis 1 and convert back to list. Et voila!
    x_ = list(np.nanmean(x, 1))
    t_ = list(np.nanmean(t, 1))

    return t_, x_


if __name__ == '__main__':

    # Load some data.
    v = Vessel('good_collection.dat')
    t = v.t * 1e-6
    y = v.y
    N = len(t[:5000])
    ds = 10

    y_filt = []
    zf = []
    for itr in range(0,N,ds):
        print(itr)
        yf, zf = lowpass(t[itr:itr+ds], y[itr:itr+ds], zi=zf)
        y_filt += yf


    # half = int(np.floor(N/2))

    # t0 = t[0:half]
    # t1 = t[half+1:]

    # y0 = y[0:half]
    # y1 = y[half+1:]

    # filter_order = 4
    # yf, zo = lowpass(t0, y0)
    # y0_filt,zi = lowpass(t0, y0, filter_order=filter_order, freq_cutoff=6)
    # y1_filt,zi = lowpass(t1, y1, filter_order, freq_cutoff=8, zi=zi)

    # import pylab as plt
    # plt.ion()
    # plt.close('all')
    # plt.figure(100)
    # plt.plot(t[:N], y_filt)
    # plt.plot(t0, y0_filt)
    # plt.plot(t1, y1_filt)

