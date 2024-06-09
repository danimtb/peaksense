from enum import Enum


class DataType(Enum):
    STATUS = 0  # Status
    TEMPERATURE = 1  # Temperature
    TEMPERATURE2 = 2  # Temperature #2
    HUMIDITY = 3  # Relative Humidity
    PRESSURE = 4  # Atmospheric Pressure
    LIGHT = 5  # Light (lux)
    VOLTAGE = 16  # Voltage
    LATITUDE = 21  # GPS Latitude
    LONGITUDE = 22  # GPS Longitude
    ALTITUDE = 23  # GPS Altitude
    HDOP = 24  # GPS HDOP
    SPEED = 999  # GPS Speed
    SPEED_LATITUDE_LONGITUDE_ALTITUDE_HDOP = 1000  # GPS Latitude, Longitude, Altitude, HDOP
