# This is the guide to connect the sensor to your PC
We are using Adafruit FT232H Breakout that allows the computer to talk directly to the devices. This chip from FTDI is similar to their USB to serial converter chips but adds a 'multi-protocol synchronous serial engine' which allows it to speak many common protocols like SPI, I2C, serial UART, JTAG et al.
This chip is powerful and useful to have when you want to use Python (for example) to quickly iterate and test a device that uses I2C, SPI or plain general purpose I/O. 
For more about this device, check: https://www.adafruit.com/product/2264

Here you can find more details on connecting it with different OS: https://learn.adafruit.com/circuitpython-on-any-computer-with-ft232h

TO be aware that we are using [CircuitPython Libraries](https://github.com/adafruit/Adafruit_CircuitPython_Bundle). Also, be aware that the FT232H is not exposed as one of standard serial ports. Instead, it is exposed as a USB device with multiple interfaces. 

The FT232H can be used to communicate with devices using I2C, SPI, GPIO, and other protocols. To use the FT232H with Python, you will need to install the `pyftdi` library, which provides a high-level interface for working with the FT232H.
which means you can't find as `/dev/i2c-X` , and any code that directly uses the Linux I2C interfaces(like `smbus2`) won't talk to it.
So the sensor is ACCESSED through BLINKA's busio.I2c. That's why you will see `"No such device" error`.

# Option A: Use a Linux I²C Bus (Physical Connection to a Linux I²C Device)
If you have the possibility to connect your sensor to one of the Linux I²C buses like the onboard SMBus or an adapter that creates a `/dev/i2c-X device`, do the following:

Connect the sensor to the proper SDA and SCL pins for that bus. Open the terminal and type:
```shell
    sudo apt-get install python-smbus2
```
Download the MS5837-python repository by using git:
```shell
    git clone https://github.com/bluerobotics/ms5837-python
```
Then, to use the package, you need to pass the correct bus number to your ms5837 code. For example, if your sensor is on `/dev/i2c-1`, use:

```python
    import ms5837
    sensor = ms5837.MS5837_02BA(1)
    sensor.init()

    sensor.read(ms5837.OSR_256) 
    #ms5837.OSR_256
    #ms5837.OSR_512
    #ms5837.OSR_1024
    #ms5837.OSR_2048
    #ms5837.OSR_4096
    #ms5837.OSR_8192
```

Double-check the sensor’s address (0x76 is the typical default, but sometimes it could be 0x77).

for more details, check: https://github.com/bluerobotics/ms5837-python


# Option B: Use the FT232H (USB to I²C Bridge) on Linux
Be sure to install Blinka before proceeding. When you use a desktop computer with a USB adapter, like the MCP2221A, FT232H. If firmware on an RP2040, you will also use pip3. However, do not install the library with sudo pip3, as mentioned in some guides. Instead, just install with pip3. 

Install libusb
```shell
    sudo apt-get install libusb-1.0-0-dev
```
Setup udev rules

```shell
    sudo nano /etc/udev/rules.d/11-ftdi.rules
```
add the following line to the file:
```bash   
    # /etc/udev/rules.d/11-ftdi.rules
    SUBSYSTEM=="usb", ATTR{idVendor}=="0403", ATTR{idProduct}=="6001", GROUP="plugdev", MODE="0666"
    SUBSYSTEM=="usb", ATTR{idVendor}=="0403", ATTR{idProduct}=="6011", GROUP="plugdev", MODE="0666"
    SUBSYSTEM=="usb", ATTR{idVendor}=="0403", ATTR{idProduct}=="6010", GROUP="plugdev", MODE="0666"
    SUBSYSTEM=="usb", ATTR{idVendor}=="0403", ATTR{idProduct}=="6014", GROUP="plugdev", MODE="0666"
    SUBSYSTEM=="usb", ATTR{idVendor}=="0403", ATTR{idProduct}=="6015", GROUP="plugdev", MODE="0666"
```
The settings will take effect the next time you plug in the FT232H.

Install pyftdi
```shell    
    pip3 install pyftdi
```
install Blinka
```shell    
    pip3 install adafruit-blinka
```
#set environment variable,  Don't forget this step. Things won't work unless BLINKA_FT232H is set. 
```shell    
    export BLINKA_FT232H=1
```
Go ahead and plug in your FT232H to a USB port on your PC.
Check pyftdi is installed
    
```python
    from pyftdi.ftdi import Ftdi
    Ftdi().open_from_url('ftdi:///?')
```

Most likely, you will get something like this:
<p align="center">
    <a href="https://gymnasium.farama.org/" target = "_blank">
    <img src="https://cdn-learn.adafruit.com/assets/assets/000/081/372/large1024/sensors_Screenshot_from_2019-09-24_13-59-50.png?1569358803" width="500px" />
</a>

</p>

Then Check environment variable within python:
```shell    
    python 
```

```python
import os
os.environ["BLINKA_FT232H"]
```
If you have set it correctly, you'll get a value back
<p align="center">
    <a href="https://gymnasium.farama.org/" target = "_blank">
    <img src="https://cdn-learn.adafruit.com/assets/assets/000/081/616/large1024/sensors_image.png?1569634052" width="500px" />
</a>

</p>

now type `import board`. You should get no errors at all, in which case you can continue onto the next steps!
We are using the latest verion(update since Feb. 12 2020). Notice that: 
I2C and SPI share the same pins, so only one mode can be used at a time. 
<p align="center">
    <a href="https://gymnasium.farama.org/" target = "_blank">
    <img src="https://cdn-learn.adafruit.com/assets/assets/000/088/862/large1024/sensors_ft232h_usbc_pintouts.jpg?1583268189" width="500px" />
</a>

</p>

# I2C connection with the Sensor(MS5837)
I believe you already solder the sensor correctly, but remember to check the datasheet of the [MS5837](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=showdoc&DocId=Data+Sheet%7FMS5837-30BA%7FB1%7Fpdf%7FEnglish%7FENG_DS_MS5837-30BA_B1.pdf%7FCAT-BLPS0017)
Since we are using the new version, do remember to set the I2C MODE switch to `ON`.

Now feel free to use it!

I have writen the app to directly call from the terminal:

```shell
python ms5837_app.py
```
or try to personalized your own functions:

```python
import os
import time
import board
import busio

# ----- Initialization of I2C -----
i2c = busio.I2C(board.SCL, board.SDA)
while not i2c.try_lock():
    pass

sensor_address = 0x76  # Update if your sensor uses a different address

try:
    # Send reset command 0x1E
    i2c.writeto(sensor_address, bytes([0x1E]))
    time.sleep(0.05)  # wait 50ms for reset
    
    # Read first PROM register (0xA0, returns 2 bytes), check sensor’s datasheet
    i2c.writeto(sensor_address, bytes([0xA0]))
    buffer = bytearray(2)
    i2c.readfrom_into(sensor_address, buffer)
    coeff = (buffer[0] << 8) | buffer[1]
    print(f"PROM coefficient: {coeff}")
    
except Exception as e:
    print("Error communicating with sensor:", e)
finally:
    i2c.unlock()

```
