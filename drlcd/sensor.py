import serial
import time
import csv
import threading
from contextlib import contextmanager
from typing import Generator, Optional

class Sensor:
    def __init__(self) -> None:
        try:
            self.latest_reading = None
            self.running = True
            self.thread = threading.Thread(target=self._read_data_thread, daemon=True)
            self.thread.start()
            
        except serial.SerialException as e:
            print(f"Fehler bei der seriellen Kommunikation: {e}")
            return False
    
    def disconnect(self) -> None:
        if self.ser:
            self.running = False

            if self.thread:
                self.thread.join()
                print("Hintergrund-Datenaufzeichnung gestoppt.")

            self.ser.write(b'Datarecording\tStop\r\n')
            print("Messung gestoppt.")
            self.ser.close()
            print("Verbindung geschlossen.")

    def _read_data_thread(self) -> None:
        self.ser = serial.Serial('COM6', 115200)
        print(f"Verbindung zu COM6 hergestellt.")

        self.ser.write(b'Datarecording\tStart\r\n')
        print("Messung gestartet.")
        # discard first line
        line = self.ser.readline().decode('utf-8').strip()
        line = self.ser.readline().decode('utf-8').strip()
        values = line.split(';')
        time.sleep(1)
        if len(values) > 6:
            self.latest_reading = float(values[1])
        time.sleep(3)

        while self.running:
            try:
                line = self.ser.readline().decode('utf-8').strip()
                if line and "Datarecording" not in line:
                    values = line.split(';')
                    if len(values) > 6:
                        self.latest_reading = float(values[1])
            except Exception as e:
                print(f"Fehler beim Lesen der Daten: {e}")

    def get_latest_reading(self) -> Optional[list]:
        while self.latest_reading == None:
            time.sleep(0.1)
        last_reading = self.latest_reading
        self.latest_reading = None
        return last_reading
