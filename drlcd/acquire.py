# from time import sleep
# from typing import Any, Callable, List, Optional, Tuple

# from drlcd.sensor import Sensor, sensor_connection
# from .machine import machineConnection, Machine
# from .ui_common import Resolution
# import click
# import json

# # links rechts
# mm_to_inch_x = 0.0393701 * 129.0 / 136.0 * (129.0 - 1.8) / 129.0 * (225.0 + 7.0) / 225.0 * (225.0 + 2.6) / 225.0
# # hoch runter
# mm_to_inch_y = 0.0393701 * 129.0 / 136.0 * (129.0 - 1.8) / 129.0

# def measureLcd(port, output, size, resolution, sensor, sleeptime, brightness_threshold, sensor_accuracy, calibrate) -> None:
#     """
#     Take and LCD measurement and save the result into a file
#     """
#     measurement = {
#         "sensor": sensor,
#         "size": size,
#         "resolution": resolution,
#         "start_point": {"x": 0, "y": 0}  # Add start point information
#     }

#     with machineConnection() as machine:
#         machine.move_to(0, 0)
#         machine.start_measure()
#         sleep(5)
#         machine.stop_measure()
#         machine.move_to(size[0] * mm_to_inch_x, 0)
#         machine.start_measure()
#         sleep(5)
#         machine.stop_measure()
#         machine.move_to(size[0] * mm_to_inch_x, size[1] * mm_to_inch_y)
#         machine.start_measure()
#         sleep(5)
#         machine.stop_measure()
#         machine.move_to(0, size[1] * mm_to_inch_y)
#         machine.start_measure()
#         sleep(5)
#         machine.stop_measure()
#         machine.move_to(0, 0)

#         if not calibrate:
#             with sensor_connection(port) as sensor:
#                 # machine.command("M17") # activate steppers
#                 # machine.command("G92 X0 Y0") # set as zero
#                 # machine.command(f"G0 X0 Y0 F{feedrate}")

#                 measurements = conservativeMeasurement(machine, size, resolution, sensor, sleeptime, brightness_threshold, sensor_accuracy)

#                 # machine.command(f"G0 X0 Y0 F{feedrate}")
#                 # machine.command("M400", timeout=40)
#                 # machine.command("M18")
#     measurement["measurements"] = measurements

#     with open(output, "w") as f:
#         json.dump(measurement, f)

# def conservativeMeasurement(machine: Machine, size: Tuple[int, int],
#         resolution: Tuple[int, int], sensor: Sensor, sleeptime: float, brightness_threshold: float, sensor_accuracy: float) -> List[List[Any]]:
#     measurements = []
#     for y in range(resolution[1]):
#         row = [0 for x in range(resolution[0])]

#         xRange = range(resolution[0])
#         if y % 2 == 1:
#             xRange = reversed(xRange)
#         for x in xRange:
#             targetX = x * size[0] / (resolution[0] - 1) * mm_to_inch_x
#             targetY = y * size[1] / (resolution[1] - 1) * mm_to_inch_y
#             machine.move_to(targetX, targetY)
#             machine.start_measure()
#             sleep(sleeptime)
#             while True:
#                 data1 = sensor.get_latest_reading()
#                 data2 = sensor.get_latest_reading()
#                 data3 = sensor.get_latest_reading()
#                 print(data1, data2, data3)
#                 if abs(data1 - data2) < sensor_accuracy and abs(data2 - data3) < sensor_accuracy:
#                     if data2 > brightness_threshold:
#                         break
#             machine.stop_measure()
#             print(f"{x}, {y}: {data2}")
#             # Store measurement with coordinates
#             row[x] = {
#                 'value': data2,
#                 'x': x * size[0] / (resolution[0] - 1),  # X coordinate in mm
#                 'y': y * size[1] / (resolution[1] - 1)   # Y coordinate in mm
#             }
#         measurements.append(row)
#     machine.move_to(0, 0)
#     return measurements
