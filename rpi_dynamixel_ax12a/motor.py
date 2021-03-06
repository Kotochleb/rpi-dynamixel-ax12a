import time
import math
from typing import Optional, List

class Motor:
    class MemoryCell:
        def __init__(self, address, length, value, access, motor_id, uart_handler):
            self.address = address
            self.length = length
            self.access = access
            self._value = value
            self._motor_id = motor_id
            self._uart_handler = uart_handler

        @property
        def value(self):
            if 'r' in self.access:
                self._uart_handler.write(
                    packet_id=self._motor_id,
                    length=0x04,
                    instruction=Motor.Instruction.READ,
                    params=[self.address, self.length]
                )
                self._value = self._uart_handler.read(
                    packet_id=self._motor_id
                )
                return self._value
            else:
                raise ValueError()

        @value.setter
        def value(self, payload):
            if 'w' in self.access:
                p = [self.address]
                p.extend(payload)
                self._uart_handler.write(
                    packet_id=self._motor_id,
                    length=0x03 + self.length,
                    instruction=Motor.Instruction.REG_WRITE,
                    params=p
                )
            else:
                raise ValueError()
            self._uart_handler.read(self._motor_id)
    

    class Instruction:
        PING = 0x01
        READ = 0x02
        WRITE = 0x03
        REG_WRITE = 0x04
        ACTION = 0x05
        FACTORY_RESET = 0x06
        REBOOT = 0x08
        SYNC_WRITE = 0x03
        BULK_READ = 0x92


    class Error:
        INSTRUCTION_ERROR = 0x40
        OVERLOAD_ERROR = 0x20
        CHECKSUM_ERROR = 0x10
        RANGE_ERROR = 0x08
        OVERHEATING_ERROR = 0x04
        ANGLE_LIMIT_ERROR = 0x02
        INPUT_VOLTAGE_ERROR = 0x01


    class EEPROM:
        def __init__(self, motor_id, uart_handler):
            self._motor_id = motor_id
            self._uart_handler = uart_handler
            self.model = Motor.MemoryCell(0, 2, 12, 'r', self._motor_id, self._uart_handler)
            self.firmware = Motor.MemoryCell(2, 1, None, 'rw', self._motor_id, self._uart_handler)
            self.id = Motor.MemoryCell(3, 1, 1, 'rw', self._motor_id, self._uart_handler)
            self.baudrate = Motor.MemoryCell(4, 1, 1, 'rw', self._motor_id, self._uart_handler)
            self.return_delay_time = Motor.MemoryCell(5, 1, 250, 'rw', self._motor_id, self._uart_handler)
            self.cw_angle_limit = Motor.MemoryCell(6, 2, 0, 'rw', self._motor_id, self._uart_handler)
            self.ccw_angle_limit = Motor.MemoryCell(8, 2, 1023, 'rw', self._motor_id, self._uart_handler)
            self.temperature_limit = Motor.MemoryCell(11, 1, 70, 'rw', self._motor_id, self._uart_handler)
            self.min_voltage_limit = Motor.MemoryCell(12, 1, 60, 'rw', self._motor_id, self._uart_handler)
            self.max_voltage_limit = Motor.MemoryCell(13, 1, 140, 'rw', self._motor_id, self._uart_handler)
            self.max_torque = Motor.MemoryCell(14, 2, 1023, 'rw', self._motor_id, self._uart_handler)
            self.status_return_level = Motor.MemoryCell(16, 1, 2, 'rw', self._motor_id, self._uart_handler)
            self.alarm_led = Motor.MemoryCell(17, 1, 36, 'rw', self._motor_id, self._uart_handler)
            self.shutdown = Motor.MemoryCell(18, 1, 36, 'rw', self._motor_id, self._uart_handler)


    class RAM:
        def __init__(self, motor_id, uart_handler):
            self._motor_id = motor_id
            self._uart_handler = uart_handler
            self.torque_enable = Motor.MemoryCell(24, 1, 0, 'rw', self._motor_id, self._uart_handler)
            self.led = Motor.MemoryCell(25, 1, 0, 'rw', self._motor_id, self._uart_handler)
            self.cw_compliance_margin = Motor.MemoryCell(26, 1, 1, 'rw', self._motor_id, self._uart_handler)
            self.ccw_compliance_margin = Motor.MemoryCell(27, 1, 1, 'rw', self._motor_id, self._uart_handler)
            self.cw_compliance_slope = Motor.MemoryCell(28, 1, 32, 'rw', self._motor_id, self._uart_handler)
            self.ccw_compliance_slope = Motor.MemoryCell(29, 1, 32, 'rw', self._motor_id, self._uart_handler)
            self.goal_position = Motor.MemoryCell(30, 2, None, 'rw', self._motor_id, self._uart_handler)
            self.moving_speed = Motor.MemoryCell(32, 2, None, 'rw', self._motor_id, self._uart_handler)
            self.torque_limit = Motor.MemoryCell(34, 2, None, 'rw', self._motor_id, self._uart_handler)
            self.present_position = Motor.MemoryCell(36, 2, None, 'r', self._motor_id, self._uart_handler)
            self.present_speed = Motor.MemoryCell(38, 2, None, 'r', self._motor_id, self._uart_handler)
            self.present_load = Motor.MemoryCell(40, 2, None, 'r', self._motor_id, self._uart_handler)
            self.present_voltage = Motor.MemoryCell(42, 1, None, 'r', self._motor_id, self._uart_handler)
            self.present_temperature = Motor.MemoryCell(43, 1, None, 'r', self._motor_id, self._uart_handler)
            self.registered = Motor.MemoryCell(44, 1, 0, 'r', self._motor_id, self._uart_handler)
            self.moving = Motor.MemoryCell(46, 1, 0, 'r', self._motor_id, self._uart_handler)
            self.lock = Motor.MemoryCell(47, 1, 0, 'rw', self._motor_id, self._uart_handler)
            self.punch = Motor.MemoryCell(48, 2, 32, 'rw', self._motor_id, self._uart_handler)

            self.position_speed_torque = Motor.MemoryCell(self.goal_position.address, 
                self.goal_position.length + self.moving_speed.length + self.torque_limit.length,
                None, 'rw', self._motor_id, self._uart_handler)

            self.present_position_speed_load = Motor.MemoryCell(self.present_position.address, 
                self.present_position.length + self.present_speed.length + self.present_load.length,
                None, 'rw', self._motor_id, self._uart_handler)

            self.motor_status = Motor.MemoryCell(self.present_voltage.address, 
                self.present_voltage.length + self.present_temperature.length \
                    + self.registered.length + self.moving.length,
                None, 'rw', self._motor_id, self._uart_handler)


    def __init__(self,
                 port_handler,
                 motor_id,
                 baudrate: Optional[int] = 1,
                 pos_lim: Optional[List[int]] = [-100,100],
                 vel_lim: Optional[int] = 1,
                 max_tq: Optional[int] = 1.5,
                 temp_lim: Optional[int] = 80
                 ):
        self._motor_id = motor_id
        self._port_handler = port_handler
        self._pos_lim = pos_lim
        self._vel_lim = vel_lim
        self._max_torque = math.ceil(max_tq/1.5*1023)
        if self._max_torque > 1023:
            self._max_torque = 1023


        self.ram = Motor.RAM(self._motor_id, self._port_handler)
        self.eeprom = Motor.EEPROM(self._motor_id, self._port_handler)


    def target_position(self, pos):
        self.ram.goal_position.value = self._split_bytes(pos)


    def target_velovity(self, vel):
        self.ram.moving_speed.value = self._split_bytes(vel)

    def target_torque(self, torque):
        self.ram.torque_limit.value = self._split_bytes(torque)


    def position_speed_torque(self, pos, vel, tq):
        self.ram.position_speed_torque.value = self._split_bytes(pos) + self._split_bytes(vel) + self._split_bytes(tq)


    @property
    def current_position_speed_torque(self):
        status = self.ram.present_position_speed_load.value
        position = status[1] * 256 + status[0]
        velocity = status[3] * 256 + status[2]
        load = status[5] * 256 + status[4]
        return [position, velocity, load]
        


    @property
    def motor_status(self):
        return self.ram.motor_status.value


    def action(self):
        length = 0x02
        self._port_handler.write(
            packet_id=self._motor_id,
            length=length,
            instruction=Motor.Instruction.ACTION,
            params=[]
        )
        if self._motor_id != 0xFE:
            return self._port_handler.read(self._motor_id)
        return True

    
    def reboot(self):
        length = 0x02
        self._port_handler.write(
            packet_id=self._motor_id,
            length=length,
            instruction=Motor.Instruction.REBOOT,
            params=[]
        )
        return self._port_handler.read(self._motor_id)


    def factory_reset(self):
        length = 0x02
        self._port_handler.write(
            packet_id=self._motor_id,
            length=length,
            instruction=Motor.Instruction.FACTORY_RESET,
            params=[]
        )
        return self._port_handler.read(self._motor_id)


    def ping(self):
        length = 0x02
        self._port_handler.write(
            packet_id=self._motor_id,
            length=length,
            instruction=Motor.Instruction.PING,
            params=[]
        )
        return self._port_handler.read(self._motor_id)

    def _split_bytes(self, payload):
        upper = (payload >> 8) & 0xFF
        lower = payload & 0xFF
        return [lower, upper]