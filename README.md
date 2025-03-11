# Measuring Acc. with Digiducer by The Modal Shop

Model : 333D01

You can see waveform on code editor (spyder).

This project is a sample code for acquiring digital signals from USB audio devices produced by The Modal Shop (TMS), including digital accelerometers and digital signal conditioners. The acquired data is cumulatively stored and displayed as a real-time waveform, with the horizontal axis corresponding to the total acquisition time of all samples.

---

## Overview

- **Device Detection:**  
  The `TMSFindDevices()` function automatically detects TMS-compatible devices. It parses the device name to extract the model number, serial number, calibration date, data format, and sensor sensitivity.

- **Signal Acquisition and Processing:**  
  The program acquires a fixed number of samples per block (defined by `blocksize`, e.g., 1024) and loops for a set number of blocks (defined by `num_blocks`, e.g., 200). This results in a total of `blocksize × num_blocks` samples (e.g., 204800 samples). The acquired data is scaled according to the sensor sensitivity and converted into engineering units (Volts or g).

- **Graph Display:**  
  The horizontal axis of the plot is set to the total acquisition time (in seconds) corresponding to the total number of samples. The plot is updated in real time using matplotlib.

---

## Supported Environment

- **Operating System:** Windows  
- **Python:** 3.10.5 (or later)  
- **Required Packages:**  
  - numpy  
  - sounddevice  
  - matplotlib  
- **Hardware:** TMS-compatible USB audio devices

---

## Useage

- Clone or download this repository.
- Connect a TMS-compatible device to your PC.
- Run the script from your terminal or IDE (e.g., Spyder) : $python TMS_Digital_Audio.py
- The program will detect the device, acquire the data, and display the cumulative waveform in real time.

---

## Code Datailes

- **Initialization:**  
  The program calls `sd._initialize()` at the very beginning to initialize PortAudio. This ensures that functions like `sd.query_hostapis()` and `sd.query_devices()` operate correctly.

- **Device Detection:**  
  The `TMSFindDevices()` function scans the connected audio devices to identify those that are TMS-compatible. It looks for specific substrings in the device name (e.g., "485B", "333D", "633A", "SDC0") and extracts essential details such as the model number, serial number, calibration date, data format, sensor sensitivity, and a calculated scale factor.

- **Signal Acquisition and Accumulation:**  
  An input stream is created using `sd.InputStream` within a with-statement (ensuring automatic closure). A callback function (`callback()`) sends blocks of data (each containing `blocksize` samples) to a queue. Each block is scaled and then stored in the `all_data` array, which cumulatively holds all samples. The total number of samples is defined as:

---

## Customization

- **Adjusting Sample Count:**  
  Modify the values of `blocksize` and `num_blocks` to change the number of samples per block and the total number of samples. This will directly affect the total acquisition time and the horizontal axis display of the graph.

- **Signal Scaling:**  
  Adjust `eu_sen` and `eu_units` to properly scale the digital signal into the desired engineering units (e.g., Volts or g).

- **Plot Settings:**  
  You can customize the plot title, axis labels, and automatic y-axis scaling settings according to your requirements.
