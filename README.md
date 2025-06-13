# HyperFocus - Neural Concentration Monitor

A neuroscience-based system that monitors brain activity in real-time to detect concentration loss while watching videos and provides gentle interventions to help regain focus.

## 🧠 Overview

HyperFocus uses EEG (Electroencephalography) data from a Muse headband to monitor your brain's beta/theta ratio - a key indicator of attention and focus. When concentration drops, the system automatically triggers subtle interventions like volume changes or screen brightness flickers to help you regain focus without disrupting your viewing experience.

## ✨ Features

-   **Real-time EEG Monitoring**: Continuously tracks brain activity using Muse headband
-   **Focus Detection**: Analyzes beta/theta ratio to determine focus status
-   **Gentle Interventions**:
    -   Volume boost to re-engage attention
    -   Screen brightness flicker to refocus eyes
-   **Visual Feedback**: Progress bar shows focus periods during video playback
-   **Session Summary**: Detailed breakdown of focus vs. distraction time
-   **Live Visualization**: Real-time plots of brain frequency bands and attention ratios

## 🛠️ Requirements

### Hardware

-   **Muse 2 or Muse S headband** (or compatible EEG device)
-   Computer with Bluetooth capability
-   Speakers/headphones for audio feedback

### Software Dependencies

-   Python 3.7+
-   Muse LSL (Lab Streaming Layer) for EEG data streaming
-   See `hyperFocus/requirements.txt` for full Python package list

## 📦 Installation

1. **Clone the repository**:

    ```bash
    git clone <repository-url>
    cd BGU-Brain-Hackathon
    ```

2. **Install Python dependencies**:

    ```bash
    cd hyperFocus
    pip install -r requirements.txt
    ```

3. **Install Muse LSL** (if not already installed):

    ```bash
    pip install muselsl
    ```

4. **Set up your Muse headband**:
    - Turn on your Muse headband
    - Pair it with your computer via Bluetooth
    - Ensure it's properly positioned on your head

## 🚀 Usage

### Basic Setup

1. **Start EEG streaming** (in a separate terminal):

    ```bash
    muselsl stream
    ```

2. **Run the main application**:
    ```bash
    cd hyperFocus
    python run_focus_video.py
    ```

### Advanced Usage

#### Real-time EEG Visualization

For detailed brain activity monitoring:

```bash
python muse_connect.py
```

#### Focus Monitoring Only

To monitor focus without video playback:

```bash
python concentration.py
```

#### Custom Video

Replace the video file in `hyperFocus/assets/` with your own content and update the path in `run_focus_video.py`.

## 🔬 How It Works

### Brain Signal Processing

1. **EEG Data Collection**: Raw brain signals are captured from the Muse headband
2. **Frequency Analysis**: Signals are filtered into different frequency bands:
    - **Beta (13-30 Hz)**: Associated with active thinking and focus
    - **Theta (4-8 Hz)**: Associated with drowsiness and daydreaming
    - **Alpha (8-13 Hz)**: Associated with relaxed alertness
3. **Ratio Calculation**: Beta/theta ratio is computed as a focus indicator
4. **Threshold Analysis**: System determines focus status based on ratio thresholds

### Focus Detection Algorithm

-   **Focused**: Beta/theta ratio above baseline threshold
-   **Out of Focus**: Ratio drops below unfocus threshold
-   **Transitioning**: Ratio between thresholds (recovering)

### Intervention System

When concentration loss is detected:

-   **Volume Boost**: Temporarily increases audio volume
-   **Brightness Flicker**: Creates subtle screen brightness changes
-   **Random Selection**: System randomly chooses intervention type

## 📊 Understanding the Output

### Real-time Plots

-   **Filtered Signal**: Cleaned EEG data
-   **Frequency Bands**: Individual alpha, beta, theta power
-   **Attention Ratios**: Beta/theta and beta/(alpha+theta) ratios

### Video Progress Bar

-   **Green Segments**: Periods of maintained focus
-   **Red Segments**: Periods of detected distraction
-   **Black Line**: Current playback position

### Session Summary

-   **Focus Time**: Percentage of time spent focused
-   **Lost Focus**: Percentage of time distracted
-   **Visual Breakdown**: Color-coded progress bars

## 🎯 Calibration

The system automatically calibrates to your baseline focus levels during the first 30 seconds of use. For optimal performance:

1. **Baseline Recording**: Stay focused during initial calibration period
2. **Consistent Environment**: Use in similar lighting and noise conditions
3. **Proper Headband Fit**: Ensure Muse headband is positioned correctly

## 🔧 Configuration

### Adjustable Parameters

-   **Recording Duration**: Modify `record_duration` in `concentration.py`
-   **Threshold Sensitivity**: Adjust focus/unfocus thresholds
-   **Intervention Frequency**: Modify intervention triggers
-   **Video Path**: Change video file in `run_focus_video.py`

### Custom Interventions

Add new intervention types by creating functions in:

-   `volume_change.py` - Audio-based interventions
-   `brightness.py` - Visual-based interventions

## 📁 Project Structure

```
├── README.md                 # This file
├── muse_connect.py          # Real-time EEG visualization
└── hyperFocus/
    ├── run_focus_video.py   # Main application
    ├── concentration.py     # Focus detection algorithm
    ├── volume_change.py     # Audio intervention system
    ├── brightness.py        # Visual intervention system
    ├── video_display.py     # Video playback interface
    ├── requirements.txt     # Python dependencies
    ├── assets/              # Video and audio files
    ├── data/                # Session data storage
    └── testing/             # Test scripts and utilities
```

## 🐛 Troubleshooting

### Common Issues

**"No EEG stream found"**

-   Ensure Muse headband is turned on and paired
-   Check that `muselsl stream` is running in another terminal
-   Verify Bluetooth connection

**Poor focus detection**

-   Check headband positioning
-   Ensure good electrode contact
-   Try recalibrating in a quiet environment

**Video playback issues**

-   Verify video file exists in assets folder
-   Check video format compatibility
-   Ensure sufficient system resources

### Debug Mode

Enable verbose logging by setting `verbose=True` in concentration functions.

## 🔬 Technical Details

### EEG Processing Pipeline

1. **Data Acquisition**: 256 Hz sampling rate from Muse headband
2. **Preprocessing**: DC offset removal and bandpass filtering
3. **Feature Extraction**: RMS power calculation for frequency bands
4. **Ratio Computation**: Beta/theta ratio as focus metric
5. **Sliding Window Analysis**: 10-second window for status determination

### Signal Processing

-   **Filtering**: Butterworth bandpass filters (4th order)
-   **Power Calculation**: Root Mean Square (RMS) method
-   **Thresholding**: Adaptive thresholds based on baseline calibration

## 🤝 Contributing

This project was developed for the BGU Brain Hackathon. Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is part of the BGU Brain Hackathon and is provided for educational and research purposes.

## 🙏 Acknowledgments

-   **Muse by InteraXon** for EEG hardware and SDK
-   **Lab Streaming Layer (LSL)** for real-time data streaming
-   **BrainFlow** for signal processing capabilities
-   **BGU Brain Hackathon** organizers and participants

---

**Note**: This system is designed for educational and research purposes. It is not intended for medical diagnosis or treatment. Always consult healthcare professionals for medical concerns related to attention or focus.
