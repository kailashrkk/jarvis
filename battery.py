import smbus

ADDR = 0x2d

def get_percent() -> int:
    """Read battery percentage from UPS HAT E via I2C."""
    try:
        bus = smbus.SMBus(1)
        data = bus.read_i2c_block_data(ADDR, 0x20, 0x06)
        return int(data[4] | data[5] << 8)
    except Exception:
        return -1
