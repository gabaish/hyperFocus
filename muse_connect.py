#!/usr/bin/env python3
"""
Multi-channel Muse EEG Stream Viewer

First run in a separate terminal:
    muselsl stream

Then run this script:
    python muse_connect.py
"""

import sys
import time
from collections import deque

import numpy as np
import matplotlib
matplotlib.use('TkAgg')  # Force TkAgg backend
import matplotlib.pyplot as plt
from pylsl import StreamInlet, resolve_byprop

from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from brainflow.data_filter import DataFilter, FilterTypes, DetrendOperations

BAND_NAMES = ['Filtered (1-50 Hz)', 'Alpha (8-13 Hz)', 'Beta (13-30 Hz)', 'Theta (4-8 Hz)']
BAND_RANGES = [(1, 50), (8, 13), (13, 30), (4, 8)]  # (low, high) frequency ranges in Hz

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
        srate = float(streams[0].nominal_srate())  # Convert to float immediately
        print(f"Sampling rate: {srate} Hz")

        # Create figure
        plt.ion()  # Enable interactive mode
        fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True)
        fig.suptitle('Muse EEG Frequency Bands', fontsize=16)
        print("Created plot window")
        
        # Initialize buffers
        duration = 5  # Store 5 seconds of data
        samples = int(duration * srate)
        times = np.linspace(-duration, 0, samples)
        
        # Initialize buffers for raw and each frequency band
        raw_buffer = np.zeros(samples)
        band_buffers = [np.zeros(samples) for _ in range(4)]
        
        # Create plot lines for each band
        lines = []
        
        for idx, (ax, name) in enumerate(zip(axes, BAND_NAMES)):
            if idx == 0:  # First plot shows raw and filtered
                raw_line, = ax.plot(times, raw_buffer, 'b-', alpha=0.5, label='Raw')
                band_line, = ax.plot(times, band_buffers[idx], 'r-', label='Filtered')
                lines.append((raw_line, band_line))
            else:  # Other plots show just the frequency band
                band_line, = ax.plot(times, band_buffers[idx], '-', label=name)
                lines.append((None, band_line))
            
            # Configure each subplot
            ax.set_ylim(-100, 100)
            ax.grid(True)
            ax.set_ylabel('(μV)')
            ax.legend(loc='upper right')
            
        # Set common x-label
        axes[-1].set_xlabel('Time (s)')
        
        # Adjust layout
        plt.tight_layout()
        print("✅ Starting to plot data...")
        print("Press Ctrl+C to stop")
        
        while True:
            try:
                # Get data from the inlet
                sample, timestamp = inlet.pull_sample(timeout=0.1)
                if sample:
                    # Roll the buffers
                    raw_buffer = np.roll(raw_buffer, -1)
                    for i in range(len(band_buffers)):
                        band_buffers[i] = np.roll(band_buffers[i], -1)
                    
                    # Update raw data buffer with first channel (we'll just use TP9)
                    raw_buffer[-1] = sample[0]
                        
                    try:
                        # Process each frequency band
                        for idx, ((low_freq, high_freq), buffer) in enumerate(zip(BAND_RANGES, band_buffers)):

                            # Create a copy of the current buffer for filtering
                            data_to_filter = raw_buffer.copy()
                            
                            # Remove DC offset
                            DataFilter.detrend(data_to_filter, DetrendOperations.CONSTANT.value)
                            
                            # Apply bandpass filter for the specific frequency band
                            DataFilter.perform_bandpass(data_to_filter, int(srate), low_freq, high_freq, 4,
                                                     FilterTypes.BUTTERWORTH.value, 0)
                            
                            # Update band buffer
                            band_buffers[idx][-1] = data_to_filter[-1]
                            
                            # Update plot lines
                            if idx == 0:  # First plot shows both raw and filtered
                                lines[idx][0].set_ydata(raw_buffer)
                                lines[idx][1].set_ydata(band_buffers[idx])
                            else:  # Other plots show just the band
                                lines[idx][1].set_ydata(band_buffers[idx])
                            
                    except Exception as filter_error:
                        print(f"Filtering error on band {BAND_NAMES[idx]}: {filter_error}")
                    
                    # Update the figure
                    fig.canvas.draw()
                    fig.canvas.flush_events()
                else:
                    print("No data received - Check connection", end='\r')
                    plt.pause(0.1)
                    
            except Exception as e:
                print(f"Error during streaming: {e}")
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
    