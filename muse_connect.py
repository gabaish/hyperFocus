#!/usr/bin/env python3
"""
Simple Muse EEG Stream Viewer with bandpass filtering

First run in a separate terminal:
    muselsl stream

Then run this script:
    python muse_connect.py
"""

from collections import deque
import numpy as np
import matplotlib
matplotlib.use('TkAgg')  # Force TkAgg backend
import matplotlib.pyplot as plt
from pylsl import StreamInlet, resolve_byprop

from brainflow.data_filter import DataFilter, FilterTypes, DetrendOperations

def main():
    try:
        # Look for an EEG stream
        print("Looking for an EEG stream...")
        streams = resolve_byprop('type', 'EEG')
        
        if not streams:
            print("❌ No EEG stream found!")
            print("Please make sure:")
            print("1. Your Muse headband is turned on")
            print("2. It's properly paired with your computer")
            print("3. You've run 'muselsl stream' in another terminal")
            return

        print(f"Found stream: {streams[0].name()} (type: {streams[0].type()}, rate: {streams[0].nominal_srate()} Hz)")
        
        # Set up the stream inlet
        inlet = StreamInlet(streams[0])
        print("Created StreamInlet successfully")

        # Get sampling rate from the stream
        srate = streams[0].nominal_srate()
        print(f"Sampling rate: {srate} Hz")

        # Create figure
        plt.ion()  # Enable interactive mode
        fig, ax = plt.subplots(figsize=(12, 6))
        print("Created plot window")
        
        # Initialize the plot
        duration = 5  # Show 5 seconds of data
        samples = int(duration * srate)
        times = np.linspace(-duration, 0, samples)
        data_buffer = deque([0] * samples, maxlen=samples)
        filtered_buffer = deque([0] * samples, maxlen=samples)
        raw_line, = ax.plot(times, data_buffer, 'b-', alpha=0.5, label='Raw')
        filtered_line, = ax.plot(times, filtered_buffer, 'r-', label='Filtered')
        ax.legend()
        print(f"Initialized plot with {samples} samples at {srate} Hz")
        
        # Configure the plot
        ax.set_ylim(-100, 100)
        ax.set_xlim(-duration, 0)
        ax.grid(True)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('EEG (μV)')
        ax.set_title('Live Muse EEG (Raw and Filtered)')
        
        print("✅ Starting to plot data...")
        print("Press Ctrl+C to stop")
        
        # Add a text display for connection status
        status_text = ax.text(0.02, 0.98, 'Connected', transform=ax.transAxes,
                            verticalalignment='top',
                            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Initialize data array for filtering
        data_for_filtering = np.zeros(samples)
        
        while True:
            try:
                # Get data from the inlet
                sample, timestamp = inlet.pull_sample(timeout=0.1)
                if sample:
                    # Update raw data buffer
                    data_buffer.append(sample[0])
                    
                    # Update data array for filtering
                    data_for_filtering = np.array(list(data_buffer))
                    
                    try:
                        # Remove DC offset first
                        DataFilter.detrend(data_for_filtering, DetrendOperations.CONSTANT.value)
                        
                        # Apply bandpass filter (1-50 Hz)
                        filtered_data = data_for_filtering.copy()  # Create a copy for filtering
                        DataFilter.perform_bandpass(filtered_data, int(srate), 1.0, 45.0, 4,
                                                 FilterTypes.BUTTERWORTH.value, 0)
                        # Apply notch filter at 50/60 Hz to remove power line interference
                        DataFilter.perform_bandstop(filtered_data, int(srate), 48.0, 52.0, 4,
                                                  FilterTypes.BUTTERWORTH.value, 0)
                        # Update filtered buffer
                        filtered_buffer.extend(filtered_data[-1:])
                        
                        # Update plot
                        raw_line.set_ydata(data_buffer)
                        filtered_line.set_ydata(filtered_buffer)
                        status_text.set_text('Connected - Receiving Data')
                        status_text.set_color('green')
                    except Exception as filter_error:
                        print(f"Filtering error: {filter_error}")
                        status_text.set_text('Filtering Error')
                        status_text.set_color('orange')
                    
                    fig.canvas.draw()
                    fig.canvas.flush_events()
                else:
                    status_text.set_text('No Data - Check Connection')
                    status_text.set_color('red')
                    fig.canvas.draw()
                    fig.canvas.flush_events()
                    plt.pause(0.001)  # Small pause to prevent CPU overload
                    
            except Exception as e:
                print(f"Error during streaming: {e}")
                status_text.set_text(f'Error: {str(e)}')
                status_text.set_color('red')
                fig.canvas.draw()
                fig.canvas.flush_events()
                plt.pause(0.1)
                    
    except KeyboardInterrupt:
        print("\n✋ Stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        try:
            plt.close('all')
        except:
            pass

if __name__ == "__main__":
    main()
