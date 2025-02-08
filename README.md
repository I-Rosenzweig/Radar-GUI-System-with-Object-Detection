# Radar GUI System with Object Detection

A Python-based radar visualization system that combines real-time radar data with computer vision object detection, featuring an interactive GUI and live video feed processing.

## Features

- Real-time radar visualization with adjustable sweep
- YOLOv8 object detection integration
- Live video stream processing
- Interactive GUI with multiple control options
- Distance calibration mode
- Adjustable minimum distance threshold
- Color-coded object detection feedback
- Network-based data transmission

## System Requirements

### Software Dependencies
- Python 3.x
- tkinter (for GUI)
- OpenCV (`cv2`)
- Ultralytics YOLOv8 (`pip install ultralytics`)
- Socket library (built-in)
- Threading library (built-in)
- Math library (built-in)
- Pickle library (built-in)
- Struct library (built-in)

### Hardware Requirements
- Radar sensor system
- Camera for object detection
- Network connection between sensor system and display system

## Installation

1. Clone the repository:
```bash
git clone [your-repository-url]
cd [repository-name]
```

2. Install required packages:
```bash
pip install ultralytics opencv-python
```

3. Download YOLOv8 weights:
```bash
# The system expects weights at "yolo-Weights/yolov8n.pt"
# Create the directory and download the weights:
mkdir yolo-Weights
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt -O yolo-Weights/yolov8n.pt
```

## Configuration

1. Update the network settings in the code:
```python
self.raspberry_ip = '192.168.137.102'  # Replace with your device IP
```

2. Adjust the radar parameters if needed:
```python
self.center_x = 350
self.center_y = 275
self.radar_radius = 240
```

## Usage

1. Start the application:
```bash
python final_version.py
```

2. GUI Controls:
- **Start**: Begin radar sweep
- **Stop**: Pause radar sweep
- **Calibration**: Toggle calibration mode
- **Quit**: Exit application
- **Distance Slider**: Adjust minimum detection distance

3. Display Features:
- Concentric circles showing distance markers
- Angle indicators (0-360°)
- Color-coded detection points:
  - Green: Normal detection
  - Orange: Detection within minimum distance
  - Red: Critical proximity alert
  - Blue: Calibration points

4. Status Indicators:
- Connection status (red/green)
- Calibration mode status (red/green)

## Network Protocol

The system uses two network connections:
1. Radar data (Port 12345):
   - Format: "angle,distance" as UTF-8 string
2. Video stream (Port 10050):
   - Format: Serialized frames using pickle and struct

## Object Detection

- Uses YOLOv8 for real-time object detection
- Supports 80 different object classes
- Displays bounding boxes and class labels on video feed
- Shows confidence scores for detections

## Error Handling

- Automatic reconnection attempts for network failures
- Visual indicators for connection status
- Graceful shutdown capabilities

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Your chosen license]

## Contact

[Your contact information]

## Acknowledgments

- YOLOv8 by Ultralytics
- [Other acknowledgments]
