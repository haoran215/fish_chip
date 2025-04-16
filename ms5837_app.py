#!/usr/bin/env python3
import time
import board
import busio
import matplotlib.pyplot as plt
import csv
from datetime import datetime
from matplotlib.animation import FuncAnimation
import os

# ----- Initialization of I2C -----
i2c = busio.I2C(board.SCL, board.SDA)
while not i2c.try_lock():
    pass

sensor_address = 0x76  # Update if your sensor uses a different address

# ----- Calibration coefficients (example values from datasheet/PROM) -----
# Typical values from the sensor datasheet (range: 0-65535)
C1 = 40127  
C2 = 36924
C3 = 23317
C4 = 23282
C5 = 33464
C6 = 28312

# ----- Data storage for plotting -----
time_steps = []
pressures = []
temperatures = []

# Control flags
paused = False
running = True

# ----- Sensor reading function -----
def read_sensor():
    # --- Get Raw Pressure (D1) ---
    # 0x48 corresponds to Convert D1 with OSR=4096.
    i2c.writeto(sensor_address, bytes([0x48]))
    time.sleep(0.02)  # wait about 20ms for conversion
    # Request ADC result (command 0x00)
    i2c.writeto(sensor_address, bytes([0x00]))
    raw_pressure_bytes = bytearray(3)
    i2c.readfrom_into(sensor_address, raw_pressure_bytes)
    D1 = (raw_pressure_bytes[0] << 16) | (raw_pressure_bytes[1] << 8) | raw_pressure_bytes[2]
    
    # --- Get Raw Temperature (D2) ---
    # 0x58 corresponds to Convert D2 with OSR=4096.
    i2c.writeto(sensor_address, bytes([0x58]))
    time.sleep(0.02)
    # Request ADC result (command 0x00)
    i2c.writeto(sensor_address, bytes([0x00]))
    raw_temp_bytes = bytearray(3)
    i2c.readfrom_into(sensor_address, raw_temp_bytes)
    D2 = (raw_temp_bytes[0] << 16) | (raw_temp_bytes[1] << 8) | raw_temp_bytes[2]

    # --- Calculation using datasheet formulas ---
    dT = D2 - (C5 * 256)
    
    # --- Compensation of temperature and pressure ---
    TEMP = 2000 + (dT * C6) / 8388608.0    # 8388608 = 2^23
    OFF = C2 * 131072 + (C4 * dT) / 64.0      # 65536 = 2^16, 128 = 2^7
    SENS = C1 * 65536 + (C3 * dT) / 128.0       # 32768 = 2^15, 256 = 2^8
    pressure = ((D1 * SENS) / 2097152.0 - OFF) / 32768.0  # 2097152 = 2^21, 32768 = 2^15
    
    # Return temperature in °C and pressure in mbar (both scaled by 100 per datasheet convention)
    return TEMP / 100.0, pressure / 100.0

# ----- Plotting and GUI -----
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6))

# ----- Event handler for keyboard input -----
def on_key(event):
    global paused, running
    if event.key == ' ':
        paused = not paused
        print("Paused" if paused else "Resumed")
    elif event.key == 'enter':
        running = False
        print("Exiting application...")
        save_data()  # Save data before exiting
        plt.close()
        
fig.canvas.mpl_connect('key_press_event', on_key)

start_time = time.time()

def update(frame):
    global paused, running, start_time
    if not paused:
        temp, press = read_sensor()
        current_time = time.time() - start_time
        time_steps.append(current_time)
        temperatures.append(temp)
        pressures.append(press)

        # Keep only the last 25 seconds of data
        if current_time > 25:
            start_index = next(i for i, t in enumerate(time_steps) if t >= current_time - 25)
            time_steps[:] = time_steps[start_index:]
            temperatures[:] = temperatures[start_index:]
            pressures[:] = pressures[start_index:]

        # Clear axes and update plot lines
        ax1.cla()
        ax2.cla()
        ax1.plot(time_steps, temperatures, 'r-', label="Temperature (°C)")
        ax2.plot(time_steps, pressures, 'b-', label="Pressure (mbar)")
        ax1.set_ylabel("Temperature (°C)")
        ax2.set_ylabel("Pressure (mbar)")
        ax2.set_xlabel("Time (s)")
        ax1.legend(loc='upper left')
        ax2.legend(loc='upper right')
    
    if not running:
        plt.close()

# ----- Save Data to CSV -----
def save_data():
    # Generate a unique filename with a timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sensor_data_{timestamp}.csv"

    # Specify the folder where the file will be saved
    folder_path = "/home/haoran/Documents/Robotic-fish/Pressure_Sensor/data"
    
    # Ensure the folder exists
    os.makedirs(folder_path, exist_ok=True)

    # Full path to the file
    file_path = os.path.join("/home/haoran/Documents/Robotic-fish/Pressure_Sensor/Experiments", filename)

    # Write data to the CSV file
    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Write the header
        writer.writerow(["Time (s)", "Temperature (°C)", "Pressure (mbar)"])
        # Write the data rows
        for t, temp, press in zip(time_steps, temperatures, pressures):
            writer.writerow([t, temp, press])

    print(f"Data saved to {file_path}")



ani = FuncAnimation(fig, update, interval=10, cache_frame_data=False)

# # Start the GUI event loop
# plt.show()

# # Release I2C lock after the GUI is closed
# i2c.unlock()

if __name__ == "__main__":
    # Start the GUI event loop
    plt.show()

    # Release I2C lock after the GUI is closed
    i2c.unlock()