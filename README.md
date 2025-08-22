Ultrasonic Radar Visualization (Processing + Arduino)

A radar-style visualization that displays real-time ultrasonic sensor readings from an Arduino in Processing.
The system simulates a scanning radar by sweeping an ultrasonic sensor and plotting detected objects on screen.

🚀 Features

Real-time radar sweep (0°–180°).

Object detection up to 40 cm.

Smooth radar sweep with motion blur.

Red markers for detected objects.

Heads-up display (HUD) with:

Angle (°)

Distance (cm)

Range indicators (10 cm, 20 cm, 30 cm, 40 cm)

Easy-to-configure serial port and range settings.

🛠 Hardware Requirements

Arduino UNO / Nano / Mega

Ultrasonic sensor (HC-SR04)

Servo motor (for sensor sweep)

Jumper wires + breadboard

USB cable (for Arduino → PC connection)

💻 Software Requirements

Arduino IDE
 (to upload Arduino code)

Processing IDE
 (to run visualization)

Processing Serial Library (comes built-in with Processing)

⚡ Data Format

The Arduino sends readings via Serial in the format:

angle,distance.


Example:

45,20.


➡ Means the sensor detected an object at 45° angle and 20 cm distance.

🔧 Setup & Usage

Connect ultrasonic sensor + servo to Arduino (according to your wiring).

Upload the Arduino sketch that controls the sweep and prints angle,distance. to Serial.

Open Processing IDE and load the provided radar_visualization.pde.

Change the port in the sketch if necessary:

final String PORT_NAME = "COM5"; // replace with your Arduino port (e.g., COM7, /dev/ttyUSB0)


Run the Processing sketch.

Watch the radar sweep and visualize detected objects 🎉

(https://github.com/user-attachments/assets/e0ced98e-8202-4ac6-aaca-fa0c717c65dc)


📂 Project Structure
├── Arduino/
│   └── ultrasonic_radar.ino     # Arduino code for sensor + servo
├── Processing/
│   └── radar_visualization.pde  # Processing visualization code
├── README.md
└── LICENSE

📜 License

This project is licensed under the MIT License – see the LICENSE
 file for details.

🌟 Future Improvements

Adjustable max detection range.

Multi-object detection and tracking.

Heatmap visualization of scanned area.

Save logs of detected distances for analysis.

🙌 Acknowledgements

Built with Arduino + Processing.

Inspired by classic ultrasonic radar visualizations.
