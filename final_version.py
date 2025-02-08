import tkinter as tk
import math
import socket
import threading
import pickle
import struct
import cv2
from ultralytics import YOLO


model = YOLO("yolo-Weights/yolov8n.pt")

# object classes
classNames = ["person", "bicycle", "car", "motorbike", "aeroplane", "bus", "train", "truck", "boat",
              "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
              "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella",
              "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite", "baseball bat",
              "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
              "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange", "broccoli",
              "carrot", "hot dog", "pizza", "donut", "cake", "chair", "sofa", "pottedplant", "bed",
              "diningtable", "toilet", "tvmonitor", "laptop", "mouse", "remote", "keyboard", "cell phone",
              "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors",
              "teddy bear", "hair drier", "toothbrush"
              ]


class RadarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Radar GUI 0.7")
        self.root.configure(bg="black")
        #self.root.attributes("-fullscreen", True)  # Make the GUI fullscreen
        #self.raspberry_ip = '192.168.1.53'  # Replace with the server IP

        # Set up canvas
        self.canvas = tk.Canvas(root, width=650, height=550, bg='black', highlightthickness=0)
        self.canvas.grid(row=0, column=0, columnspan=5, padx=10, pady=10)

        # Radar center coordinates
        self.center_x = 350#275
        self.center_y = 275
        self.radar_radius = 240

        # Draw radar circles (concentric circles) and distance labels
        for i in range(1, 5):
            radius = i * 60
            self.canvas.create_oval(self.center_x - radius, self.center_y - radius,
                                    self.center_x + radius, self.center_y + radius,
                                    outline="green", width=2)
            distance_label = f"{(radius / self.radar_radius) * 10:.1f} m"
            self.canvas.create_text(self.center_x + radius + 25, self.center_y+10,
                                    text=distance_label, fill="white", font=("Arial", 10))
            self.canvas.create_text(self.center_x - radius - 25, self.center_y-10,
                                    text=distance_label, fill="white", font=("Arial", 10))
            self.canvas.create_text(self.center_x+10, self.center_y - radius - 15,
                                    text=distance_label, fill="white", font=("Arial", 10))
            self.canvas.create_text(self.center_x-10, self.center_y + radius + 15,
                                    text=distance_label, fill="white", font=("Arial", 10))

        # Draw polar grid lines (lines radiating from the center) and angle labels
        for angle in range(0, 360, 30):
            x_end = self.center_x + self.radar_radius * math.cos(math.radians(angle))
            y_end = self.center_y - self.radar_radius * math.sin(math.radians(angle))
            self.canvas.create_line(self.center_x, self.center_y, x_end, y_end, fill="green", width=2)

            # Position angle labels at a comfortable distance from the radar circle
            label_distance = self.radar_radius + 35
            label_x = self.center_x + label_distance * math.cos(math.radians(angle))
            label_y = self.center_y - label_distance * math.sin(math.radians(angle))
            self.canvas.create_text(label_x, label_y, text=f"{angle}°", fill="white", font=("Arial", 10))

        # Radar sweep line
        self.line = self.canvas.create_line(self.center_x, self.center_y,
                                            self.center_x, self.center_y - self.radar_radius,
                                            fill="lime", width=4)

        # Angle display
        self.angle_label = tk.Label(root, text="Angle: 0°", font=("Arial", 16), fg="lime", bg="black")
        self.angle_label.grid(row=1, column=0, columnspan=5, pady=10)

        # State indicator (calibration mode)
        self.state_indicator = self.canvas.create_oval(510, 10, 530, 30, fill="gray", outline="gray")

        # Connection status indicator
        self.connection_indicator = self.canvas.create_oval(480, 10, 500, 30, fill="red", outline="red")

        # Control buttons
        button_style = {"font": ("Arial", 14), "fg": "white", "bg": "gray20", "activebackground": "gray40", "width": 12}

        self.start_button = tk.Button(root, text="Start", command=self.start_sweep, **button_style)
        self.start_button.grid(row=1, column=0, padx=5, pady=15)

        self.stop_button = tk.Button(root, text="Stop", command=self.stop_sweep, **button_style)
        self.stop_button.grid(row=1, column=1, padx=5, pady=15)

        # self.restart_button = tk.Button(root, text="Restart", command=self.restart_sweep, **button_style)
        # self.restart_button.grid(row=4, column=2, padx=5, pady=15)

        self.calibration_button = tk.Button(root, text="Calibration", command=self.toggle_calibration, **button_style)
        self.calibration_button.grid(row=1, column=2, padx=5, pady=15)

        # self.quit_button = tk.Button(root, text="Quit", command=self.root.quit, **button_style)
        # self.quit_button.grid(row=4, column=3, padx=5, pady=15)
        self.quit_button = tk.Button(root, text="Quit", command=self.quit_sweep, **button_style)
        self.quit_button.grid(row=1, column=3, padx=5, pady=15)

        # Initial angle and running state
        self.angle = 0
        self.running = False
        self.distance = 0
        self.calibration_mode = False
        self.calibrated_points = {}
        self.points = {}
        self.connected = False
        self.calibrated_dots = {}
        self.non_calibrated_dots = {}

        # Minimum distance and scrollbar setup
        self.min_distance = 0.5

        self.min_distance_circle = self.canvas.create_oval(
            self.center_x - self.min_distance * self.radar_radius / 10,
            self.center_y - self.min_distance * self.radar_radius / 10,
            self.center_x + self.min_distance * self.radar_radius / 10,
            self.center_y + self.min_distance * self.radar_radius / 10,
            outline="red"
        )

        self.scrollbar = tk.Scale(root, from_=0.5, to=10.0, orient="vertical", resolution=0.1,
                                  command=self.update_min_distance, length=200)
        self.scrollbar.set(self.min_distance)
        self.scrollbar.grid(row=0, column=5, padx=10, pady=10, rowspan=2)
        #self.raspberry_ip='192.168.1.66'
        self.raspberry_ip = '192.168.137.102'
        #self.raspberry_ip = '10.100.102.17'
        #self.raspberry_ip = '192.168.1.213'  # Replace with the server IP



        # Start socket thread
        self.start_socket_thread()
        self.start_vid_socket_thread()
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.raspberry_ip, 12345))  # Replace with Raspberry Pi's IP
        # self.vid_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.vid_client_socket.connect(('192.168.137.102', 10050))  # Replace with Raspberry Pi's IP

    def start_socket_thread(self):
        threading.Thread(target=self.socket_client, daemon=True).start()

    def start_vid_socket_thread(self):
        threading.Thread(target=self.vid_socket_client, daemon=True).start()

    def vid_socket_client(self):

        vid_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        vid_client_socket.connect((self.raspberry_ip, 10050))  # Replace with Raspberry Pi's IP

        data = b""
        payload_size = struct.calcsize("Q")  # Q is a format for unsigned long long

        while True:
            # Retrieve the message size first
            while len(data) < payload_size:
                packet = vid_client_socket.recv(4096)
                if not packet:
                    break
                data += packet

            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack("Q", packed_msg_size)[0]

            # Retrieve the actual frame data
            while len(data) < msg_size:
                data += vid_client_socket.recv(4096)

            frame_data = data[:msg_size]
            data = data[msg_size:]

            # Deserialize the frame using pickle
            frame = pickle.loads(frame_data)
            results = model(frame, stream=True)
            for r in results:
                boxes = r.boxes

                for box in boxes:
                    # bounding box
                    x1, y1, x2, y2 = box.xyxy[0]
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)  # convert to int values

                    # put box in cam
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 255), 3)

                    # confidence
                    confidence = math.ceil((box.conf[0] * 100)) / 100
                    #print("Confidence --->", confidence)

                    # class name
                    cls = int(box.cls[0])
                    #print("Class name -->", classNames[cls])


                    #print("Distance -->",self.distance)
                    # object details
                    org = [x1, y1]
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    fontScale = 1
                    color = (255, 0, 0)
                    thickness = 2

                    cv2.putText(frame, classNames[cls], org, font, fontScale, color, thickness)

            # Display the frame
            cv2.imshow("Live Stream", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        vid_client_socket.close()
        cv2.destroyAllWindows()
    def socket_client(self):
        while not self.connected:
            try:
                self.connected = True
                self.update_connection_indicator(True)

                while True:
                    data = self.client_socket.recv(1024).decode('utf-8')
                    print(data)
                    D = data.split(',')
                    if data:
                        self.distance = float(D[1]) / 100
                        print(self.distance)
                        self.angle = float(D[0]) * 2.8125
                        print(self.angle)
                        self.map_point()
            except ConnectionRefusedError:
                self.update_connection_indicator(False)
                self.connected = False
                self.root.after(1000, self.socket_client)  # Retry connection every 1 second

    def send_start_command(self):
        self.client_socket.sendall(b"start")
        print("start")

    def send_stop_command(self):
        self.client_socket.sendall(b"stop")
        print("stop")

    def send_quit_command(self):
        self.client_socket.sendall(b"quit")
        print("quit")
    def update_connection_indicator(self, status):
        color = "green" if status else "red"
        self.canvas.itemconfig(self.connection_indicator, fill=color, outline=color)

    def update_min_distance(self, value):
        self.min_distance = float(value)
        radius = (self.min_distance / 10) * self.radar_radius
        self.canvas.coords(
            self.min_distance_circle,
            self.center_x - radius,
            self.center_y - radius,
            self.center_x + radius,
            self.center_y + radius
        )

    def map_point(self):
        max_distance = 10.0
        distance_meters = min(self.distance, max_distance)
        scaled_distance = (distance_meters / max_distance) * self.radar_radius
        x_end = self.center_x + scaled_distance * math.cos(math.radians(self.angle))
        y_end = self.center_y - scaled_distance * math.sin(math.radians(self.angle))

        if self.calibration_mode:
            # Remove old calibrated dot if it exists
            if self.angle in self.calibrated_dots:
                self.canvas.delete(self.calibrated_dots[self.angle])

            # Draw new calibrated dot and update dictionary
            self.calibrated_points[self.angle] = scaled_distance
            self.calibrated_dots[self.angle] = self.canvas.create_oval(
                x_end - 2, y_end - 2, x_end + 2, y_end + 2, fill="blue", outline="blue"
            )
        else:
            # Remove old non-calibrated dot if it exists
            if self.angle in self.non_calibrated_dots:
                self.canvas.delete(self.non_calibrated_dots[self.angle])

            # Draw new non-calibrated dot and update dictionary
            self.points[self.angle] = scaled_distance
            if self.angle in self.calibrated_points:
                if scaled_distance < (self.calibrated_points[self.angle])  :
                    #if scaled_distance<self.min_distance:
                    if self.distance < self.min_distance:
                        self.non_calibrated_dots[self.angle] = self.canvas.create_oval(
                            x_end - 2, y_end - 2, x_end + 2, y_end + 2, fill="red", outline="red")
                    else:
                        self.non_calibrated_dots[self.angle] = self.canvas.create_oval(
                            x_end - 2, y_end - 2, x_end + 2, y_end + 2, fill="orange", outline="orange")
                else:
                    self.non_calibrated_dots[self.angle] = self.canvas.create_oval(
                        x_end - 2, y_end - 2, x_end + 2, y_end + 2, fill="green", outline="green"
                    )
            else:
                self.non_calibrated_dots[self.angle] = self.canvas.create_oval(
                    x_end - 2, y_end - 2, x_end + 2, y_end + 2, fill="green", outline="green"
                )

    def update_sweep(self):
        if self.running:
            x_end = self.center_x + self.radar_radius * math.cos(math.radians(self.angle))
            y_end = self.center_y - self.radar_radius * math.sin(math.radians(self.angle))
            self.canvas.coords(self.line, self.center_x, self.center_y, x_end, y_end)
            self.angle_label.config(text=f"Angle: {self.angle}°")
            self.root.after(30, self.update_sweep)

    def start_sweep(self):
        self.send_start_command()
        if not self.running:
            self.running = True
            self.update_sweep()

    def stop_sweep(self):
        self.send_stop_command()
        self.running = False

    def quit_sweep(self):
        self.running = False
        self.send_quit_command()
        self.root.quit()



    def restart_sweep(self):
        self.stop_sweep()
        self.angle = 0
        self.canvas.delete("all")
        self.points.clear()
        self.calibrated_points.clear()
        self.calibrated_dots.clear()
        self.non_calibrated_dots.clear()
        self.start_sweep()

    def toggle_calibration(self):
        self.calibration_mode = not self.calibration_mode
        self.update_state_indicator()

    def update_state_indicator(self):
        color = "red" if self.calibration_mode else "green"
        self.canvas.itemconfig(self.state_indicator, fill=color, outline=color)


# Set up the main application window
root = tk.Tk()
app = RadarApp(root)
root.mainloop()
