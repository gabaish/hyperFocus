import numpy as np
import time
from pylsl import StreamInlet, resolve_byprop
from brainflow.data_filter import DataFilter, FilterTypes, DetrendOperations
import matplotlib.pyplot as plt
import pandas as pd
import threading
from collections import deque

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

def get_focus_status():
    """
    Get the current focus status from the global focus_status variable.
    This function can be called from other parts of the application.
    Returns:
        str: Current focus status ('unknown', 'focused', 'out_of_focus', 'transitioning')
    """
    # This will be updated by the main function
    global focus_status
    return focus_status if 'focus_status' in globals() else 'unknown'

def sliding_window_analysis(data_buffer, thresholds, window_size=10, sample_rate=256):
    """
    Analyze the sliding window for focus status changes.
    Args:
        data_buffer: Deque containing (timestamp, ratio1, ratio2) tuples
        thresholds: Dictionary with threshold values including focus and unfocus thresholds
        window_size: Window size in seconds
        sample_rate: Sample rate in Hz
    Returns:
        dict: Analysis results with focus status and details
    """
    if len(data_buffer) < window_size * sample_rate * 0.1:  # Need at least 10% of window
        return {'focus_status': 'unknown', 'details': 'Insufficient data'}
    
    # Get the last window_size seconds of data
    window_samples = int(window_size * sample_rate * 0.1)  # Assuming 10Hz ratio calculation
    recent_data = list(data_buffer)[-window_samples:]
    
    if len(recent_data) == 0:
        return {'focus_status': 'unknown', 'details': 'No recent data'}
    
    # Calculate means for the window
    ratio1_values = [item[1] for item in recent_data]
    ratio2_values = [item[2] for item in recent_data]
    
    window_mean_ratio1 = np.mean(ratio1_values)
    window_mean_ratio2 = np.mean(ratio2_values)
    
    # Check focus status using both thresholds
    # Out of focus: below baseline * 0.6
    # Back to focus: above baseline * 0.85
    ratio1_out_of_focus = window_mean_ratio1 < thresholds['beta_theta_ratio_unfocus']
    ratio2_out_of_focus = window_mean_ratio2 < thresholds['beta_alpha_theta_ratio_unfocus']
    
    ratio1_back_to_focus = window_mean_ratio1 >= thresholds['beta_theta_ratio_focus']
    ratio2_back_to_focus = window_mean_ratio2 >= thresholds['beta_alpha_theta_ratio_focus']
    
    # Determine focus status
    if ratio1_out_of_focus or ratio2_out_of_focus:
        focus_status = 'out_of_focus'
    elif ratio1_back_to_focus and ratio2_back_to_focus:
        focus_status = 'focused'
    else:
        focus_status = 'transitioning'  # Between thresholds
    
    details = {
        'window_mean_ratio1': window_mean_ratio1,
        'window_mean_ratio2': window_mean_ratio2,
        'ratio1_unfocus_threshold': thresholds['beta_theta_ratio_unfocus'],
        'ratio2_unfocus_threshold': thresholds['beta_alpha_theta_ratio_unfocus'],
        'ratio1_focus_threshold': thresholds['beta_theta_ratio_focus'],
        'ratio2_focus_threshold': thresholds['beta_alpha_theta_ratio_focus'],
        'ratio1_out_of_focus': ratio1_out_of_focus,
        'ratio2_out_of_focus': ratio2_out_of_focus,
        'ratio1_back_to_focus': ratio1_back_to_focus,
        'ratio2_back_to_focus': ratio2_back_to_focus,
        'window_samples': len(recent_data)
    }
    
    return {
        'focus_status': focus_status,
        'details': details
    }

def main(record_duration=30, record_start_time=2, continue_plotting=True):
    """
    Main function with simultaneous recording, plotting, and sliding window analysis.
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
    fig, ax = plt.subplots(1, 1, figsize=(12, 4))  # Single plot for better performance
    fig.suptitle('Muse EEG Focus Monitoring - Beta/Theta Ratio with Dual Thresholds', fontsize=16)

    # Main ratio plot (only Beta/Theta for performance)
    line1, = ax.plot(times, ratio1_buffer, label='Beta/Theta Ratio', color='blue')
    
    # Pre-allocate threshold lines (more efficient than removing/adding)
    threshold_line1, = ax.plot([], [], color='red', linestyle='--', alpha=0.7, label='Unfocus Threshold (0.6x)')
    threshold_line2, = ax.plot([], [], color='green', linestyle='--', alpha=0.7, label='Focus Threshold (0.85x)')
    
    # Set up plot formatting
    ax.set_ylabel('Beta/Theta Ratio')
    ax.set_xlabel('Time (s)')
    ax.grid(True)
    ax.legend(loc='upper right')
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])

    # Shared data between threads
    recorded_data = []
    recording_complete = threading.Event()
    recording_means = None
    thresholds = None
    
    # Sliding window data
    sliding_window_data = deque(maxlen=2560)  # 10 seconds at 256Hz
    global focus_status
    focus_status = 'unknown'  # 'unknown', 'focused', 'out_of_focus', 'transitioning'
    last_analysis_time = 0
    last_plot_update_time = 0
    
    # Performance optimization flags - MUCH less frequent updates
    plot_update_interval = 0.5  # Update plot every 500ms instead of 100ms
    analysis_interval = 5.0     # Analysis every 5 seconds
    background_color_changed = False
    
    def record_data():
        """Thread function to record data"""
        nonlocal recorded_data, recording_means, thresholds
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
                'beta_theta_ratio_unfocus': recording_means['beta_theta_ratio'] * 0.6,
                'beta_alpha_theta_ratio_unfocus': recording_means['beta_alpha_theta_ratio'] * 0.6,
                'beta_theta_ratio_focus': recording_means['beta_theta_ratio'] * 0.85,
                'beta_alpha_theta_ratio_focus': recording_means['beta_alpha_theta_ratio'] * 0.85
            }
            print(f"Unfocus thresholds (0.6x): Beta/Theta: {thresholds['beta_theta_ratio_unfocus']:.4f}, Beta/(Alpha+Theta): {thresholds['beta_alpha_theta_ratio_unfocus']:.4f}")
            print(f"Focus thresholds (0.85x): Beta/Theta: {thresholds['beta_theta_ratio_focus']:.4f}, Beta/(Alpha+Theta): {thresholds['beta_alpha_theta_ratio_focus']:.4f}")
            
            # Update threshold lines once when calculated
            if thresholds is not None:
                threshold_line1.set_data([times[0], times[-1]], [thresholds['beta_theta_ratio_unfocus'], thresholds['beta_theta_ratio_unfocus']])
                threshold_line2.set_data([times[0], times[-1]], [thresholds['beta_theta_ratio_focus'], thresholds['beta_theta_ratio_focus']])

    # Start recording thread if duration > 0
    if record_duration > 0:
        record_thread = threading.Thread(target=record_data)
        record_thread.start()
    
    # Live plotting with sliding window analysis
    gen = stream_muse_ratios(verbose=False)
    
    try:
        for ratio1, ratio2 in gen:
            current_time = time.time()
            
            # Add data to sliding window
            sliding_window_data.append((current_time, ratio1, ratio2))
            
            # Roll buffers and update (only for the plot we're showing)
            ratio1_buffer = np.roll(ratio1_buffer, -1)
            ratio1_buffer[-1] = ratio1
            
            # Update plot line (lightweight operation)
            line1.set_ydata(ratio1_buffer)
            
            # Sliding window analysis (heavy operation - only every 5 seconds)
            if current_time - last_analysis_time >= analysis_interval and thresholds is not None:
                analysis_result = sliding_window_analysis(sliding_window_data, thresholds)
                new_focus_status = analysis_result['focus_status']
                
                # Only print messages when status actually changes
                if new_focus_status != focus_status:
                    if new_focus_status == 'out_of_focus':
                        focus_status = 'out_of_focus'
                        details = analysis_result['details']
                        print(f"\n🚨 OUT OF FOCUS DETECTED at {current_time:.1f}s")
                        print(f"   Beta/Theta: {details['window_mean_ratio1']:.4f} (unfocus threshold: {details['ratio1_unfocus_threshold']:.4f})")
                        print(f"   Beta/(Alpha+Theta): {details['window_mean_ratio2']:.4f} (unfocus threshold: {details['ratio2_unfocus_threshold']:.4f})")
                        print(f"   Ratio1 out of focus: {details['ratio1_out_of_focus']}, Ratio2 out of focus: {details['ratio2_out_of_focus']}")
                        
                        # Visual feedback: Red background
                        ax.set_facecolor('lightcoral')
                        background_color_changed = True
                        
                    elif new_focus_status == 'focused':
                        focus_status = 'focused'
                        details = analysis_result['details']
                        print(f"\n✅ BACK TO FOCUS at {current_time:.1f}s")
                        print(f"   Beta/Theta: {details['window_mean_ratio1']:.4f} (focus threshold: {details['ratio1_focus_threshold']:.4f})")
                        print(f"   Beta/(Alpha+Theta): {details['window_mean_ratio2']:.4f} (focus threshold: {details['ratio2_focus_threshold']:.4f})")
                        print(f"   Ratio1 back to focus: {details['ratio1_back_to_focus']}, Ratio2 back to focus: {details['ratio2_back_to_focus']}")
                        
                        # Visual feedback: Green background
                        ax.set_facecolor('lightgreen')
                        background_color_changed = True
                        
                    elif new_focus_status == 'transitioning':
                        focus_status = 'transitioning'
                        details = analysis_result['details']
                        print(f"\n🔄 TRANSITIONING at {current_time:.1f}s")
                        print(f"   Beta/Theta: {details['window_mean_ratio1']:.4f} (between thresholds)")
                        print(f"   Beta/(Alpha+Theta): {details['window_mean_ratio2']:.4f} (between thresholds)")
                        
                        # Visual feedback: Yellow background
                        ax.set_facecolor('lightyellow')
                        background_color_changed = True
                        
                    elif new_focus_status == 'unknown':
                        focus_status = 'unknown'
                        print(f"\n❓ UNKNOWN FOCUS STATUS at {current_time:.1f}s - insufficient data")
                        
                        # Reset background color
                        if background_color_changed:
                            ax.set_facecolor('white')
                            background_color_changed = False
                
                    last_analysis_time = current_time
            
            # Heavy plot updates only every 500ms (much less frequent)
            if current_time - last_plot_update_time >= plot_update_interval:
                # Only do autoscaling occasionally to improve performance
                ax.relim()
                ax.autoscale_view(scaley=True, scalex=False)
                
                # Flush events less frequently
                fig.canvas.draw()
                fig.canvas.flush_events()
                last_plot_update_time = current_time
            
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

def start_focus_monitoring(record_duration=30, record_start_time=2, continue_plotting=True):
    """
    Start the focus monitoring system with the new dual-threshold approach.
    
    Args:
        record_duration (float): Duration in seconds to record baseline data
        record_start_time (float): Time in seconds from program start to begin recording
        continue_plotting (bool): Whether to continue plotting after recording is complete
    
    Returns:
        dict: Dictionary with baseline mean values for each channel, or None if no recording was done
    
    Focus Status Logic:
    - If ratio drops below baseline * 0.6 -> 'out_of_focus'
    - If ratio rises above baseline * 0.85 -> 'focused'
    - If ratio is between thresholds -> 'transitioning'
    - If insufficient data -> 'unknown'
    """
    return main(record_duration, record_start_time, continue_plotting)

if __name__ == "__main__":
    main()
