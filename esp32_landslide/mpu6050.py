import math

MPU6050_ADDR = 0x68
PWR_MGMT_1 = 0x6B
ACCEL_XOUT_H = 0x3B


class MPU6050:
    def __init__(self, i2c, addr=MPU6050_ADDR):
        self.i2c = i2c
        self.addr = addr
        # Wake the sensor up (it starts in sleep mode)
        self.i2c.writeto_mem(self.addr, PWR_MGMT_1, b'\x00')

    def _read_word(self, reg):
        high = self.i2c.readfrom_mem(self.addr, reg, 1)[0]
        low = self.i2c.readfrom_mem(self.addr, reg + 1, 1)[0]
        val = (high << 8) | low
        if val >= 0x8000:
            val -= 0x10000
        return val

    def read_accel(self):
        ax = self._read_word(ACCEL_XOUT_H) / 16384.0
        ay = self._read_word(ACCEL_XOUT_H + 2) / 16384.0
        az = self._read_word(ACCEL_XOUT_H + 4) / 16384.0
        return ax, ay, az

    def read_tilt_deg(self):
        """Returns the tilt angle (in degrees) away from perfectly flat."""
        ax, ay, az = self.read_accel()
        # Angle between the measured gravity vector and the vertical (Z) axis
        magnitude = math.sqrt(ax * ax + ay * ay + az * az)
        if magnitude == 0:
            return 0
        az_norm = max(-1.0, min(1.0, az / magnitude))
        angle_rad = math.acos(az_norm)
        return math.degrees(angle_rad)