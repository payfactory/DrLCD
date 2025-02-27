from time import sleep
from typing import Any, Callable, List, Optional, Tuple

from drlcd.sensor import Sensor, sensor_connection
from .machine import machineConnection, Machine
from .ui_common import Resolution
import click
import json

@click.command()
@click.argument("output", type=click.Path())
@click.option("--port", type=str, default="COM6",
    help="Port for UV Sensor connection")
@click.option("--sleeptime", type=float, default=3.0,
    help="time in seconds to sleep before measurment")
@click.option("--brightness_threshold", type=float, default=1.0,
    help="brightness to pause")
@click.option("--sensor_accuracy", type=float, default=0.1,
    help="sensor_accuracy")
@click.option("--size", type=Resolution(),
    help="Screen size in millimeters")
@click.option("--resolution", type=Resolution(),
    help="Number of samples in vertical and horizontal direction")
@click.option("--sensor", type=click.Choice(["TSL2561", "AS7625"]), default="TSL2561",
    help="Sensor used for measurement")
def measureLcd(port, output, size, resolution, sensor, sleeptime, brightness_threshold, sensor_accuracy) -> None:
    """
    Take and LCD measurement and save the result into a file
    """
    measurement = {
        "sensor": sensor,
        "size": size,
        "resolution": resolution
    }

    with machineConnection() as machine:
        with sensor_connection(port) as sensor:
            # machine.command("M17") # activate steppers
            # machine.command("G92 X0 Y0") # set as zero
            # machine.command(f"G0 X0 Y0 F{feedrate}")

            measurements = conservativeMeasurement(machine, size, resolution, sensor, sleeptime, brightness_threshold, sensor_accuracy)

            # machine.command(f"G0 X0 Y0 F{feedrate}")
            # machine.command("M400", timeout=40)
            # machine.command("M18")
    measurement["measurements"] = measurements

    with open(output, "w") as f:
        json.dump(measurement, f)

def conservativeMeasurement(machine: Machine, size: Tuple[int, int],
        resolution: Tuple[int, int], sensor: Sensor, sleeptime: float, brightness_threshold: float, sensor_accuracy: float) -> List[List[Any]]:
    
    mm_to_inch = 0.0393701
    measurements = []
    for y in range(resolution[1]):
        row = [0 for x in range(resolution[0])]

        xRange = range(resolution[0])
        if y % 2 == 1:
            xRange = reversed(xRange)
        for x in xRange:
            targetX = x * size[0] / (resolution[0] - 1) * mm_to_inch
            targetY = y * size[1] / (resolution[1] - 1) * mm_to_inch
            machine.move_to(targetX, targetY)
            machine.start_measure()
            sleep(sleeptime)
            while True:
                data1 = sensor.get_latest_reading()
                data2 = sensor.get_latest_reading()
                data3 = sensor.get_latest_reading()
                print(data1, data2, data3)
                if abs(data1 - data2) < sensor_accuracy and abs(data2 - data3) < sensor_accuracy:
                    if data2 > brightness_threshold:
                        break
            machine.stop_measure()
            print(f"{x}, {y}: {data2}")
            row[x] = data2
        measurements.append(row)
    machine.move_to(0, 0)
    return measurements
