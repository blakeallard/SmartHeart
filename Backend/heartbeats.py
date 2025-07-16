import csv
import datetime
import serial
import time

# Collect user info before reading BPM
name   = input("Enter your name: ")
age    = input("Enter your age: ")
gender = input("Enter your gender: ")
height = input("Enter your height (in cm): ")
weight = input("Enter your weight (in kg): ")

# Setup serial port (adjust 'COM3' or '/dev/ttyXXX' as needed)
ser = serial.Serial('/dev/tty.usbmodem12201', 115200, timeout=1)
time.sleep(2)  # give some time to establish connection

filename = 'bpm_log.csv'

# Write header and user info once
with open(filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Timestamp", "Name", "Age", "Gender", "Height_cm", "Weight_kg", "BPM", "is_healthy"])

print("Starting to log BPM data... Press Ctrl+C to stop.")

try:
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').strip()
            # Assume the BPM line looks like: "BPM: 75"
            if line.startswith("BPM:"):
                bpm = line.split(":")[1].strip()
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                is_healthy = 1 if 50 <= int(bpm) <= 90 else 0

                with open(filename, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([timestamp, name, age, gender, height, weight, bpm, is_healthy])

                print(f"{timestamp} | BPM: {bpm}")

except KeyboardInterrupt:
    print("Logging stopped by user.")
    ser.close()
