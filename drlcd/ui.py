from nicegui import ui
from .machine import Machine
from .sensor import Sensor
import json
from time import sleep


# # links rechts
mm_to_inch_x = 0.0393701 * 129.0 / 136.0 * (129.0 - 1.8) / 129.0 * (225.0 + 7.0) / 225.0 * (225.0 + 2.6) / 225.0
# # hoch runter
mm_to_inch_y = 0.0393701 * 129.0 / 136.0 * (129.0 - 1.8) / 129.0

class LCDController:
    def __init__(self):
        self.machine = None
        self.current_x = 0
        self.current_y = 0
        self.origin_offset = (0, 0)
        self.size_x = 225  # Default size
        self.size_y = 129  # Default size
        self.resolution_x = self.size_x // 7  # Default resolution
        self.resolution_y = self.size_y // 7  # Default resolution
        self.sleeptime = 1.0
        self.brightness_threshold = 0.5
        self.filename = "measurement.json"
        self.sensor = None
        self.sensor_accuracy = 0.1  # Default sensor accuracy threshold
    
    def connect_machine(self):
        self.machine = Machine()
        self.sensor = Sensor()
        ui.notify('Machine and sensor connected successfully')

    def adjust_position(self, axis, amount):
        if self.machine is None:
            ui.notify('Please connect to machine first!')
            return

        if axis == 'x':
            self.current_x += amount
        else:
            self.current_y += amount
        
        x_inch = (self.current_x + self.origin_offset[0]) * mm_to_inch_x
        y_inch = (self.current_y + self.origin_offset[1]) * mm_to_inch_y
        
        self.machine.move_to(x_inch, y_inch)
        ui.notify(f'Adjusted {axis} position by {amount}mm')

    def set_origin(self):
        if self.machine is None:
            ui.notify('Please connect to machine first!')
            return

        self.origin_offset = (self.current_x + self.origin_offset[0], self.current_y + self.origin_offset[1])
        self.current_x = 0
        self.current_y = 0
        ui.notify('Origin set to current position')

    def pen_up(self):
        if self.machine is None:
            ui.notify('Please connect to machine first!')
            return

        self.machine.stop_measure()

    def pen_down(self):
        if self.machine is None:
            ui.notify('Please connect to machine first!')
            return

        self.machine.start_measure()

    def move_to_origin(self):
        if self.machine is None:
            ui.notify('Please connect to machine first!')
            return

        self.machine.move_to(0, 0)
        self.current_x = 0
        self.current_y = 0
        ui.notify('Moved to origin')

    def move_to_corner(self, corner):
        if self.machine is None:
            ui.notify('Please connect to machine first!')
            return

        if self.size_x == 0 or self.size_y == 0:
            ui.notify('Please set the size first!')
            return

        if corner == 'top_left':
            x = self.size_x
            y = self.size_y
        elif corner == 'top_right':
            x = 0
            y = self.size_y
        elif corner == 'bottom_left':
            x = self.size_x
            y = 0
        elif corner == 'bottom_right':
            x = 0
            y = 0
        
        x_inch = (x + self.origin_offset[0]) * mm_to_inch_x
        y_inch = (y + self.origin_offset[1]) * mm_to_inch_y
        
        self.machine.move_to(x_inch, y_inch)
        self.current_x = x
        self.current_y = y
        ui.notify(f'Moved to {corner} corner')

    def start_measurement(self):
        if self.machine is None:
            ui.notify('Please connect to machine first!')
            return
        
        if self.sensor is None:
            ui.notify('Please connect to sensor first!')
            return

        self.move_to_corner('bottom_right')
        sleep(1)
        self.move_to_corner('bottom_left')
        sleep(1)
        self.move_to_corner('top_left')
        sleep(1)
        self.move_to_corner('top_right')
        sleep(1)
        self.move_to_corner('bottom_right')

        self.resolution_x = int(self.resolution_x)
        self.resolution_y = int(self.resolution_y)
        
        step_x = self.size_x / (self.resolution_x - 1)
        step_y = self.size_y / (self.resolution_y - 1)
        
        measurements = [[{} for _ in range(self.resolution_x)] for _ in range(self.resolution_y)]
        
        for y in range(self.resolution_y):
            for x in range(self.resolution_x):
                pos_x = x * step_x
                pos_y = y * step_y
                
                x_inch = (pos_x + self.origin_offset[0]) * mm_to_inch_x
                y_inch = (pos_y + self.origin_offset[1]) * mm_to_inch_y

                self.machine.move_to(x_inch, y_inch)
                print("moved to", x_inch, y_inch)
                self.machine.start_measure()
                sleep(self.sleeptime)

                while True:
                    data1 = self.sensor.get_latest_reading()
                    data2 = self.sensor.get_latest_reading()
                    data3 = self.sensor.get_latest_reading()
                    print(data1, data2, data3)
                    if abs(data1 - data2) < self.sensor_accuracy and abs(data2 - data3) < self.sensor_accuracy:
                        if data2 > self.brightness_threshold:
                            break

                self.machine.stop_measure()

                measurements[y][x] = {
                    'value': data2,
                    'x': x * step_x,
                    'y': y * step_y
                }
        
        result = {
            "sensor": "TSL2561",
            "size": [self.size_x, self.size_y],
            "resolution": [self.resolution_x, self.resolution_y],
            "measurements": measurements
        }
        
        with open(self.filename, 'w') as f:
            json.dump(result, f)
        
        print("Done")
        ui.notify(f'Measurement completed and saved to {self.filename}')

class DrLCDUI:
    def __init__(self):
        self.controller = LCDController()
    
    def create_ui(self):
        with ui.column().classes('w-full items-center'):
            ui.label('Dentoo UV Sensor Control').classes('text-2xl')

            with ui.row().classes('gap-4 m-4'):
                ui.button('Connect Machine', on_click=self.controller.connect_machine)
            
            # Size and resolution inputs
            with ui.row().classes('gap-4 m-4'):
                ui.number('Width (mm)', value=self.controller.size_x, on_change=lambda e: setattr(self.controller, 'size_x', e.value))
                ui.number('Height (mm)', value=self.controller.size_y, on_change=lambda e: setattr(self.controller, 'size_y', e.value))
            
            # Origin controls
            with ui.row().classes('gap-4 m-4'):
                ui.button('Set Origin', on_click=self.controller.set_origin)
                ui.button('Move to Origin', on_click=self.controller.move_to_origin)
            
            # Corner buttons
            with ui.grid(columns=2).classes('gap-4 m-4'):
                ui.button('Top Left', on_click=lambda: self.controller.move_to_corner('top_left'))
                ui.button('Top Right', on_click=lambda: self.controller.move_to_corner('top_right'))
                ui.button('Bottom Left', on_click=lambda: self.controller.move_to_corner('bottom_left'))
                ui.button('Bottom Right', on_click=lambda: self.controller.move_to_corner('bottom_right'))
            
            # Position adjustment
            with ui.row().classes('gap-4 m-4'):
                ui.button('←', on_click=lambda: self.controller.adjust_position('x', 1))
                ui.button('→', on_click=lambda: self.controller.adjust_position('x', -1))
                ui.button('↑', on_click=lambda: self.controller.adjust_position('y', 1))
                ui.button('↓', on_click=lambda: self.controller.adjust_position('y', -1))
            
            # Fine adjustment
            with ui.row().classes('gap-4 m-4'):
                ui.button('← 0.1', on_click=lambda: self.controller.adjust_position('x', 0.1))
                ui.button('→ 0.1', on_click=lambda: self.controller.adjust_position('x', -0.1))
                ui.button('↑ 0.1', on_click=lambda: self.controller.adjust_position('y', 0.1))
                ui.button('↓ 0.1', on_click=lambda: self.controller.adjust_position('y', -0.1))
            
            # Pen controls
            with ui.row().classes('gap-4 m-4'):
                ui.button('Pen Up', on_click=self.controller.pen_up)
                ui.button('Pen Down', on_click=self.controller.pen_down)
            
            with ui.row().classes('gap-4 m-4'):
                ui.number('Resolution X', value=self.controller.resolution_x, on_change=lambda e: setattr(self.controller, 'resolution_x', e.value))
                ui.number('Resolution Y', value=self.controller.resolution_y, on_change=lambda e: setattr(self.controller, 'resolution_y', e.value))
            
            # Measurement parameters
            with ui.row().classes('gap-4 m-4'):
                ui.number('Sleep Time (s)', value=self.controller.sleeptime, on_change=lambda e: setattr(self.controller, 'sleeptime', e.value))
                ui.number('Brightness Threshold', value=self.controller.brightness_threshold, on_change=lambda e: setattr(self.controller, 'brightness_threshold', e.value))
                ui.number('Sensor Accuracy', value=self.controller.sensor_accuracy, on_change=lambda e: setattr(self.controller, 'sensor_accuracy', e.value))
            
            # Filename input
            ui.input('Output Filename', value=self.controller.filename).bind_value(self.controller, 'filename')
            
            # Start measurement button
            ui.button('Start Measurement', on_click=self.controller.start_measurement).classes('m-4')
            
            # Current position display
            ui.label().bind_text_from(self.controller, 'current_x', lambda x: f'Current X: {x:.1f}mm')
            ui.label().bind_text_from(self.controller, 'current_y', lambda y: f'Current Y: {y:.1f}mm')
            ui.label().bind_text_from(self.controller, 'origin_offset', lambda o: f'Origin Offset: {o[0]:.1f}mm, {o[1]:.1f}mm')

def main():
    drlcd_ui = DrLCDUI()
    drlcd_ui.create_ui()
    ui.run(title='Dentoo UV Sensor', port=8080)

if __name__ in {"__main__", "__mp_main__"}:
    main()
