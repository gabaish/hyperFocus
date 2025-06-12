import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime, timedelta

def analyze_muse_recording(filename, start_time=None, duration_seconds=None):
    """
    Analyze a Muse recording CSV file and return basic statistics.
    
    Args:
        filename (str): Path to the Muse recording CSV file
        start_time (str, optional): Start time in format 'HH:MM:SS' or seconds from start
        duration_seconds (float, optional): Duration of the window to analyze in seconds
        
    Returns:
        dict: Dictionary containing statistics for beta/theta and beta/(alpha+theta) ratios
    """
    try:
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the full path to the CSV file
        full_path = os.path.join(script_dir, os.path.basename(filename))
        
        # Check if file exists
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {full_path}")
            
        # Read the CSV file
        df = pd.read_csv(full_path)
        
        # Check if required columns exist
        required_columns = ['beta_theta_ratio', 'beta_alpha_theta_ratio', 'timestamp']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

        # Convert timestamp column to float timestamps
        df['timestamp'] = df['timestamp'].astype(float)
        
        # Get the start timestamp (first row)
        initial_timestamp = df['timestamp'].iloc[0]
        
        # Apply time window filtering if specified
        if start_time is not None and duration_seconds is not None:
            if isinstance(start_time, str) and ':' in start_time:  # If time format is HH:MM:SS
                # Convert HH:MM:SS to seconds
                h, m, s = map(float, start_time.split(':'))
                start_seconds = h * 3600 + m * 60 + s
            else:
                start_seconds = float(start_time)
            
            # Calculate target timestamps
            target_start = initial_timestamp + start_seconds
            target_end = target_start + duration_seconds
            
            # Filter dataframe based on timestamps
            df = df[(df['timestamp'] >= target_start) & (df['timestamp'] < target_end)]

        if df.empty:
            raise ValueError("No data points found in the specified time window")
        
        # Calculate statistics for both ratios
        stats = {
            'beta_theta_ratio': {
                'mean': df['beta_theta_ratio'].mean(),
                'std': df['beta_theta_ratio'].std(),
                'median': df['beta_theta_ratio'].median(),
                'min': df['beta_theta_ratio'].min(),
                'max': df['beta_theta_ratio'].max()
            },
            'beta_alpha_theta_ratio': {
                'mean': df['beta_alpha_theta_ratio'].mean(),
                'std': df['beta_alpha_theta_ratio'].std(), 
                'median': df['beta_alpha_theta_ratio'].median(),
                'min': df['beta_alpha_theta_ratio'].min(),
                'max': df['beta_alpha_theta_ratio'].max()
            },
            'time_window': {
                'start': df['timestamp'].min(),
                'end': df['timestamp'].max(),
                'duration': df['timestamp'].max() - df['timestamp'].min(),
                'n_samples': len(df)
            }
        }
        
        return stats
    except Exception as e:
        print(f"Error analyzing file: {str(e)}")
        return None

def print_stats(stats):
    """Pretty print the statistics"""
    if not stats:
        return
        
    print("\nAnalysis Results:")
    print("-" * 50)
    
    # Print time window information first
    if 'time_window' in stats:
        print("\nTime Window:")
        print("-" * 30)
        tw = stats['time_window']
        print(f"Start time: {tw['start']}")
        print(f"End time: {tw['end']}")
        print(f"Duration: {tw['duration']:.2f} seconds")
        print(f"Samples: {tw['n_samples']}")
    
    # Print ratio statistics
    for ratio_name, ratio_stats in stats.items():
        if ratio_name != 'time_window':  # Skip time window info here
            print(f"\n{ratio_name.replace('_', '/')}:")
            print("-" * 30)
            for stat_name, value in ratio_stats.items():
                print(f"{stat_name.capitalize():>10}: {value:.4f}")

def main():
    try:
        # Get the filename from the command line
        filename = "./concentration_test_1.csv"
        
        # Example 1: Analyze entire recording
        print("\nAnalyzing entire recording:")
        stats_full = analyze_muse_recording(filename)
        if stats_full:
            print_stats(stats_full)
            
        # Example 2: Analyze a 10-second window starting at the start of the recording
        print("\nAnalyzing 10-second window starting at 00:00:")
        stats_window = analyze_muse_recording(filename, start_time=0, duration_seconds=10)
        if stats_window:
            print_stats(stats_window)

        # Example 2: Analyze a 10-second window starting at 00:10:00
        print("\nAnalyzing 10-second window starting at 00:10:00:")
        stats_window = analyze_muse_recording(filename, start_time=10, duration_seconds=10)
        if stats_window:
            print_stats(stats_window)


        # Example 3: Analyze every 30 seconds window
        for start_time in range(0, 120, 30):
            print(f"\nAnalyzing 30-second window starting at {start_time}:")
            stats_window = analyze_muse_recording(filename, start_time=start_time, duration_seconds=30)
            if stats_window:
                print_stats(stats_window)

                    
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()