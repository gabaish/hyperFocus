#!/usr/bin/env python3
"""
Muse EEG Data Recorder

Records beta/theta and beta/(alpha+theta) ratios from Muse EEG headband.
First run 'muselsl stream' in another terminal, then run this script.
"""

import numpy as np
import csv
from datetime import datetime
from pylsl import StreamInlet, resolve_byprop
from brainflow.data_filter import DataFilter, FilterTypes, DetrendOperations

BAND_RANGES = {
    'alpha': (8, 13),
    'beta': (13, 30), 
    'theta': (4, 8)
}

def calculate_band_power(buffer):
    """Calculate the power of a frequency band using RMS"""
    return np.sqrt(np.mean(np.square(buffer)))

def main():
    try:
        # Look for EEG stream
        print("Looking for an EEG stream...")
        streams = resolve_byprop('type', 'EEG')
        
        if not streams:
            print("❌ No EEG stream found!")
            print("Please make sure:")
            print("1. Your Muse headband is turned on")
            print("2. It's properly paired with your computer") 
            print("3. You've run 'muselsl stream' in another terminal")
            return

        # Set up stream inlet
        inlet = StreamInlet(streams[0])
        srate = float(streams[0].nominal_srate())
        print(f"✅ Connected to Muse stream at {srate} Hz")

        # Create buffers for raw data and bands
        buffer_duration = 1  # 1 second buffer
        buffer_size = int(buffer_duration * srate)
        raw_buffer = np.zeros(buffer_size)
        
        # Initialize band buffers
        alpha_buffer = np.zeros(buffer_size)
        beta_buffer = np.zeros(buffer_size)
        theta_buffer = np.zeros(buffer_size)

        # Create output file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"muse_recording_{timestamp}.csv"
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['lsl_timestamp', 'iso_timestamp', 'beta_theta_ratio', 'beta_alpha_theta_ratio'])
            
            print(f"Recording data to {filename}")
            print("Press Ctrl+C to stop recording")
            
            while True:
                sample, timestamp = inlet.pull_sample(timeout=0.1)
                
                if sample:
                    # Update raw buffer
                    raw_buffer = np.roll(raw_buffer, -1)
                    raw_buffer[-1] = sample[0]  # Using TP9 channel
                    
                    # Process each frequency band
                    for band_name, (low_freq, high_freq) in BAND_RANGES.items():
                        # Copy and filter data
                        filtered_data = raw_buffer.copy()
                        DataFilter.detrend(filtered_data, DetrendOperations.CONSTANT.value)
                        DataFilter.perform_bandpass(filtered_data, int(srate), low_freq, high_freq, 4,
                                                 FilterTypes.BUTTERWORTH.value, 0)
                        
                        # Update appropriate buffer
                        if band_name == 'alpha':
                            alpha_buffer = np.roll(alpha_buffer, -1)
                            alpha_buffer[-1] = filtered_data[-1]
                        elif band_name == 'beta':
                            beta_buffer = np.roll(beta_buffer, -1)
                            beta_buffer[-1] = filtered_data[-1]
                        elif band_name == 'theta':
                            theta_buffer = np.roll(theta_buffer, -1)
                            theta_buffer[-1] = filtered_data[-1]
                    
                    # Calculate ratios
                    beta_power = calculate_band_power(beta_buffer[-50:])  # Use last 50 samples
                    theta_power = calculate_band_power(theta_buffer[-50:])
                    alpha_power = calculate_band_power(alpha_buffer[-50:])
                    
                    # Calculate attention ratios
                    beta_theta_ratio = beta_power / (theta_power + 1e-10)  # Avoid division by zero
                    beta_alpha_theta_ratio = beta_power / (alpha_power + theta_power + 1e-10)
                    
                    # Write to CSV
                    iso_timestamp = datetime.fromtimestamp(timestamp).isoformat()
                    writer.writerow([timestamp, iso_timestamp, beta_theta_ratio, beta_alpha_theta_ratio])
                    csvfile.flush()  # Ensure data is written immediately
                    
                    # Print current values
                    print(f"β/θ: {beta_theta_ratio:.2f} | β/(α+θ): {beta_alpha_theta_ratio:.2f}", end='\r')
                    
    except KeyboardInterrupt:
        print("\n✋ Recording stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
