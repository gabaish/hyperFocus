import numpy as np
import time
from pylsl import StreamInlet, resolve_byprop
from brainflow.data_filter import DataFilter, FilterTypes, DetrendOperations
import matplotlib.pyplot as plt
import pandas as pd
import threading

def calculate_band_power(buffer):
    """Calculate the power of a frequency band using RMS"""
    return np.sqrt(np.mean(np.square(buffer)))


def stream_muse_ratios(duration=5, verbose=True):
    """
    Stream Muse EEG data and yield only the two ratio channels:
    - Beta/Theta
    - Beta/(Alpha+Theta)
    Yields a tuple: (beta_theta_ratio, beta_alpha_theta_ratio)
    """
    # Look for an EEG stream
    if verbose:
        print("Looking for an EEG stream...")
    streams = resolve_byprop('type', 'EEG')
    if not streams:
        raise RuntimeError("No EEG stream found! Make sure Muse is streaming.")
    if verbose:
        print(f"Found stream: {streams[0].name()} (type: {streams[0].type()}, rate: {streams[0].nominal_srate()} Hz)")
    inlet = StreamInlet(streams[0])
    srate = float(streams[0].nominal_srate())
    samples = int(duration * srate)
    raw_buffer = np.zeros(samples)
    band_buffers = [np.zeros(samples) for _ in range(4)]  # 4 basic bands: Filtered, Alpha, Beta, Theta
    BAND_RANGES = [(1, 50), (8, 13), (13, 30), (4, 8)]
    
    while True:
        sample, timestamp = inlet.pull_sample(timeout=0.1)
        if sample:
            # Roll buffers
            raw_buffer = np.roll(raw_buffer, -1)
            for i in range(len(band_buffers)):
                band_buffers[i] = np.roll(band_buffers[i], -1)
            # Update raw data buffer with first channel (e.g., TP9)
            raw_buffer[-1] = sample[0]
            try:
                # Process each frequency band
                for idx, (low_freq, high_freq) in enumerate(BAND_RANGES):
                    data_to_filter = raw_buffer.copy()
                    DataFilter.detrend(data_to_filter, DetrendOperations.CONSTANT.value)
                    DataFilter.perform_bandpass(data_to_filter, int(srate), low_freq, high_freq, 4, FilterTypes.BUTTERWORTH.value, 0)
                    band_buffers[idx][-1] = data_to_filter[-1]
                # Calculate ratios using the most recent data (last 50 samples)
                beta_power = calculate_band_power(band_buffers[2][-50:])
                theta_power = calculate_band_power(band_buffers[3][-50:])
                alpha_power = calculate_band_power(band_buffers[1][-50:])
                beta_theta_ratio = beta_power / (theta_power + 1e-10)
                beta_alpha_theta_ratio = beta_power / (alpha_power + theta_power + 1e-10)
                yield (beta_theta_ratio, beta_alpha_theta_ratio)
            except Exception as e:
                if verbose:
                    print(f"Filtering error: {e}")
        else:
            if verbose:
                print("No data received - Check connection", end='\r')
            time.sleep(0.1)

def record_ratios_to_df(record_time, start_time=0, verbose=True):
    """
    Record streamed ratio data into a pandas DataFrame.
    Args:
        record_time (float): Duration in seconds to record data.
        start_time (float): Time in seconds from program start to begin recording.
        verbose (bool): Print status messages.
    Returns:
        pd.DataFrame: DataFrame with columns ['timestamp', 'beta_theta_ratio', 'beta_alpha_theta_ratio']
    """
    import time
    data = []
    start_program = time.time()
    # Wait until start_time seconds have passed
    if verbose:
        print(f"Waiting {start_time} seconds before starting recording...")
    while time.time() - start_program < start_time:
        time.sleep(0.05)
    if verbose:
        print(f"Starting recording for {record_time} seconds...")
    gen = stream_muse_ratios(verbose=verbose)
    record_start = time.time()
    while time.time() - record_start < record_time:
        ratio1, ratio2 = next(gen)
        now = time.time() - start_program  # relative timestamp
        data.append([now, ratio1, ratio2])
    if verbose:
        print(f"Recording complete. Collected {len(data)} samples.")
    df = pd.DataFrame(data, columns=['timestamp', 'beta_theta_ratio', 'beta_alpha_theta_ratio'])
    return df

def get_channel_means(df):
    """
    Calculate the mean values for each ratio channel from a recorded DataFrame.
    Args:
        df (pd.DataFrame): DataFrame with columns ['timestamp', 'beta_theta_ratio', 'beta_alpha_theta_ratio']
    Returns:
        dict: Dictionary with mean values for each channel
    """
    if df.empty:
        return None
    
    means = {
        'beta_theta_ratio': df['beta_theta_ratio'].mean(),
        'beta_alpha_theta_ratio': df['beta_alpha_theta_ratio'].mean()
    }
    return means

def main(record_duration=30, record_start_time=2, continue_plotting=True):
    """
    Main function with simultaneous recording and plotting.
    Args:
        record_duration (float): Duration in seconds to record data
        record_start_time (float): Time in seconds from program start to begin recording
        continue_plotting (bool): Whether to continue plotting after recording is complete
    Returns:
        dict: Dictionary with mean values for each channel, or None if no recording was done
    """
    # Set up plotting
    duration = 5  # seconds of buffer for plotting
    buffer_len = int(duration * 256)  # Default srate
    times = np.linspace(-duration, 0, buffer_len)
    ratio1_buffer = np.zeros(buffer_len)
    ratio2_buffer = np.zeros(buffer_len)

    plt.ion()
    fig, ax = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
    fig.suptitle('Muse EEG Ratio Channels (Live Plot)', fontsize=16)

    line1, = ax[0].plot(times, ratio1_buffer, label='Beta/Theta Ratio')
    line2, = ax[1].plot(times, ratio2_buffer, label='Beta/(Alpha+Theta) Ratio')

    for a in ax:
        a.grid(True)
        a.set_ylabel('Ratio')
        a.legend(loc='upper right')
    ax[1].set_xlabel('Time (s)')
    plt.tight_layout(rect=[0, 0, 1, 0.96])

    # Shared data between threads
    recorded_data = []
    recording_complete = threading.Event()
    recording_means = None
    
    def record_data():
        """Thread function to record data"""
        nonlocal recorded_data, recording_means
        print(f"Recording {record_duration} seconds of data (starting at {record_start_time}s)...")
        
        # Wait until start time
        start_program = time.time()
        while time.time() - start_program < record_start_time:
            time.sleep(0.05)
        
        # Start recording
        record_start = time.time()
        gen = stream_muse_ratios(verbose=False)
        
        while time.time() - record_start < record_duration:
            try:
                ratio1, ratio2 = next(gen)
                now = time.time() - start_program
                recorded_data.append([now, ratio1, ratio2])
            except Exception as e:
                print(f"Recording error: {e}")
                break
        
        recording_complete.set()
        print(f"Recording complete. Collected {len(recorded_data)} samples.")
        
        # Calculate and print means
        if recorded_data:
            df = pd.DataFrame(recorded_data, columns=['timestamp', 'beta_theta_ratio', 'beta_alpha_theta_ratio'])
            recording_means = get_channel_means(df)
            print(f"\nRecording Results:")
            print(f"Beta/Theta ratio mean: {recording_means['beta_theta_ratio']:.4f}")
            print(f"Beta/(Alpha+Theta) ratio mean: {recording_means['beta_alpha_theta_ratio']:.4f}")
            print(f"Total samples recorded: {len(df)}")

            thresholds = {
                'beta_theta_ratio' : recording_means['beta_theta_ratio'] * 0.7,
                'beta_alpha_theta_ratio' : recording_means['beta_alpha_theta_ratio'] * 0.7
            }
            print(f"Thresholds: {thresholds}")

    # Start recording thread if duration > 0
    if record_duration > 0:
        record_thread = threading.Thread(target=record_data)
        record_thread.start()
    
    # Live plotting
    update_every = 10
    counter = 0
    gen = stream_muse_ratios(verbose=False)
    
    try:
        for ratio1, ratio2 in gen:
            # Roll buffers and update
            ratio1_buffer = np.roll(ratio1_buffer, -1)
            ratio2_buffer = np.roll(ratio2_buffer, -1)
            ratio1_buffer[-1] = ratio1
            ratio2_buffer[-1] = ratio2
            
            # Update plot lines
            line1.set_ydata(ratio1_buffer)
            line2.set_ydata(ratio2_buffer)
            
            counter += 1
            if counter % update_every == 0:
                for a in ax:
                    a.relim()
                    a.autoscale_view(scaley=True, scalex=False)
                fig.canvas.draw()
                fig.canvas.flush_events()
            
            # Check if recording is complete and we should stop
            if recording_complete.is_set() and not continue_plotting:
                break
                
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"Plotting error: {e}")
    
    # Wait for recording thread to complete if it's still running
    if record_duration > 0:
        record_thread.join()
    
    return recording_means

if __name__ == "__main__":
    main()
