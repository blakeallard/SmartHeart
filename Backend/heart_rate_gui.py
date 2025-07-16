import tkinter as tk
from tkinter import messagebox
import csv
import datetime
import serial
import threading
import time

# Global flag for stopping logging
logging_active = False
ser = None

def start_logging():
    global logging_active, ser

    # Get user input
    name   = name_var.get()
    age    = age_var.get()
    gender = gender_var.get()
    height = height_var.get()
    weight = weight_var.get()

    if not all([name, age, gender, height, weight]):
        messagebox.showwarning("Missing Info", "Please fill out all fields before starting.")
        return

    try:
        ser_port = port_var.get()
        ser_baud = int(baud_var.get())
        ser_timeout = 1

        # Setup serial connection
        ser = serial.Serial(ser_port, ser_baud, timeout=ser_timeout)
        time.sleep(2)

    except Exception as e:
        messagebox.showerror("Serial Error", f"Could not open serial port:\n{e}")
        return

    # Write header
    with open('bpm_log.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Name", "Age", "Gender", "Height_cm", "Weight_kg", "BPM", "Sp02", "is_healthy"]) 
        # Updated 7/8 - added "Sp02" 

    logging_active = True
    start_button.config(state=tk.DISABLED)
    stop_button.config(state=tk.NORMAL)

    # Run logger in a background thread
    threading.Thread(target=log_bpm, args=(name, age, gender, height, weight), daemon=True).start()

def stop_logging():
    global logging_active, ser
    logging_active = False
    start_button.config(state=tk.NORMAL)
    stop_button.config(state=tk.DISABLED)
    if ser:
        ser.close()
        ser = None
    bpm_var.set("Stopped.")

def log_bpm(name, age, gender, height, weight):
    global ser

    try:
        while logging_active:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                if line.startswith("BPM:"):
                    bpm = line.split(":")[1].strip()
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    is_healthy = 1 if 50 <= int(bpm) <= 90 else 0

                    with open('bpm_log.csv', mode='a', newline='') as file:
                        writer = csv.writer(file)
                        writer.writerow([timestamp, name, age, gender, height, weight, bpm, is_healthy])

                    bpm_var.set(f"{timestamp} | BPM: {bpm}")
    except Exception as e:
        messagebox.showerror("Logging Error", str(e))
        stop_logging()

# GUI setup
root = tk.Tk()
root.title("Heart Rate Logger")

# Form fields
frame = tk.Frame(root, padx=15, pady=15)
frame.pack()

tk.Label(frame, text = "Name:").grid(row = 0, column = 0, sticky = "e")
tk.Label(frame, text = "Age:").grid(row = 1, column = 0, sticky = "e")
tk.Label(frame, text = "Gender:").grid(row = 2, column = 0, sticky = "e")
tk.Label(frame, text = "Height (cm):").grid(row = 3, column = 0, sticky = "e")
tk.Label(frame, text = "Weight (kg):").grid(row = 4, column = 0, sticky = "e")
tk.Label(frame, text = "Serial Port (e.g., COM3 or /dev/tty.usbmodem12201):").grid(row = 5, column = 0, sticky = "e")
tk.Label(frame, text = "Baud Rate:").grid(row = 6, column = 0, sticky = "e")

name_var   = tk.StringVar()
age_var    = tk.StringVar()
gender_var = tk.StringVar()
height_var = tk.StringVar()
weight_var = tk.StringVar()
port_var   = tk.StringVar(value = "/dev/tty.usbmodem12201")
baud_var   = tk.StringVar(value = "115200")

tk.Entry(frame, textvariable = name_var).grid(row = 0, column = 1)
tk.Entry(frame, textvariable = age_var).grid(row = 1, column = 1)
tk.Entry(frame, textvariable = gender_var).grid(row = 2, column = 1)
tk.Entry(frame, textvariable = height_var).grid(row = 3, column = 1)
tk.Entry(frame, textvariable = weight_var).grid(row = 4, column = 1)
tk.Entry(frame, textvariable = port_var).grid(row = 5, column = 1)
tk.Entry(frame, textvariable = baud_var).grid(row = 6, column = 1)

# Buttons
start_button = tk.Button(frame, text = "Start Logging", command = start_logging)
start_button.grid(row = 7, column = 0, pady = 10)

stop_button = tk.Button(frame, text = "Stop Logging", command = stop_logging, state = tk.DISABLED)
stop_button.grid(row = 7, column = 1, pady = 10)

# BPM display
bpm_var = tk.StringVar(value = "Waiting for data...")
tk.Label(root, textvariable = bpm_var, font = ("Courier", 12), pady = 10).pack()

root.mainloop()
