import serial
import time
import csv

def read_serial_data(port='COM6', baudrate=115200, timeout=1, output_file='measurements.csv'):
    try:
        # Serielle Verbindung öffnen
        ser = serial.Serial(port, baudrate, timeout=timeout)
        print(f"Verbindung zu {port} hergestellt.")
        
        # Datenaufzeichnung starten
        ser.write(b'Datarecording\tStart\r\n')
        time.sleep(1)  # Wartezeit für Antwort
        print("Started")
        
        with open(output_file, mode='w', newline='') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerow(["Sensor1 Typ", "Messwert [klx]", "Offset", "Dosis [klxs]", "Min", "Max", "Temp [°C]", 
                             "Sensor2 Typ", "Messwert [W/cm2]", "Offset", "Dosis [J/cm2]", "Min", "Max", "Temp [°C]"])
            
            while True:
                try:
                    print("Waiting")
                    line = ser.readline().decode('utf-8').strip()
                    print(line)
                    if not line:
                        continue
                    
                    if "Datarecording" in line:
                        print("Datenaufnahme beendet.")
                        break
                    
                    # Werte parsen
                    values = line.split(';')
                    if len(values) > 6:
                        writer.writerow(values[1])
                        print(f"Daten gespeichert: {values[1]}")
                
                except KeyboardInterrupt:
                    print("Messung manuell gestoppt.")
                    break
        
        # Datenaufzeichnung stoppen
        ser.write(b'Datarecording\tStop\r\n')
        ser.close()
        print("Verbindung geschlossen.")
    
    except serial.SerialException as e:
        print(f"Fehler bei der seriellen Kommunikation: {e}")
    except Exception as e:
        print(f"Allgemeiner Fehler: {e}")

if __name__ == "__main__":
    read_serial_data()
