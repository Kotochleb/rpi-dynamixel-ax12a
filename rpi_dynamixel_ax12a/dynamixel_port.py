import time
from serial import Serial

try:
    import RPi.GPIO as GPIO
except ImportError:
    pass

try:
    import Jetson.GPIO as GPIO
except ImportError:
    pass

try:
    GPIO.getmode()
except NameError:
    raise ImportError('Couldn\'t find matching GPIO library')



class DynamixelPort:
    PROTOCOL_SLEEP = 0.00003
    DIRECTION_RX = GPIO.LOW
    DIRECTION_TX = GPIO.HIGH

    def __init__(self, port_id='/dev/ttyAMA0', pin=18):
        self._port_id = port_id
        self._data_pin = pin
        self._port = Serial(self._port_id, baudrate=1000000, timeout=1)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self._data_pin, GPIO.OUT)
        GPIO.output(self._data_pin, DynamixelPort.DIRECTION_TX)

    
    def __del__(self):
        GPIO.cleanup()
        
    def write(self, packet_id, length, instruction, params):
        GPIO.output(self._data_pin, DynamixelPort.DIRECTION_TX)
        payload = [0xFF, 0xFF]
        payload.append(packet_id)
        payload.append(length)
        payload.append(instruction)
        payload.extend(params)
        payload.append(self.checksum(payload[2:]))
        self._port.write(payload)
        time.sleep(DynamixelPort.PROTOCOL_SLEEP)



    def read(self, packet_id):
        GPIO.output(self._data_pin, DynamixelPort.DIRECTION_RX)
        response = list(self._port.read(4))

        if len(response) == 0:
            raise Exception()

        if response[0] != 0xFF or response[1] != 0xFF:
            raise ValueError
        if packet_id != 0xFE and response[2] != packet_id:
            raise ValueError
        
        resp_len = response[3]
        payload = list(self._port.read(resp_len))
        if payload[0] != 0x00:
            raise ValueError()
        checksum = (self.checksum(response[2:] + payload[:-1]))
        if payload[-1] != checksum:
            raise ValueError()

        if resp_len > 0:
            return payload[1:-1]
        return []


    def flush(self):
        self._port.flush()

    def checksum(self, payload):
        return (~(sum(payload))) & 0xFF