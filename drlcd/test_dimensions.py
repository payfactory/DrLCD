from nicegui import ui
from drlcd.machine import machineConnection, Machine
import json
from pathlib import Path
from .acquire import mm_to_inch_x, mm_to_inch_y

class DimensionTester:
    def __init__(self):
        self.current_x = 0
        self.current_y = 0
        self.corners = {
            'top_left': {'x': 0, 'y': 0},
            'top_right': {'x': 0, 'y': 0},
            'bottom_right': {'x': 0, 'y': 0},
            'bottom_left': {'x': 0, 'y': 0}
        }
        self.machine = None
        self.origin_offset = (0, 0)
        self.size_x = 225
        self.size_y = 129

    def connect_machine(self):
        if self.machine is None:
            self.machine = machineConnection().__enter__()
            ui.notify('Machine connected!')
        else:
            ui.notify('Machine already connected!')

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
        
        # Move to origin (0,0)
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
        
        # Move to origin (0,0) in machine coordinates
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

def main():
    tester = DimensionTester()
    
    with ui.column().classes('w-full items-center'):
        ui.label('Display Dimension Tester').classes('text-2xl')
        
        # Connection button
        ui.button('Connect to Machine', on_click=tester.connect_machine).classes('m-4')
        
        # Size input
        with ui.row().classes('gap-4 m-4'):
            ui.number('Width (mm)', value=tester.size_x, on_change=lambda e: setattr(tester, 'size_x', e.value))
            ui.number('Height (mm)', value=tester.size_y, on_change=lambda e: setattr(tester, 'size_y', e.value))
        
        # Origin controls
        with ui.row().classes('gap-4 m-4'):
            ui.button('Set Origin', on_click=tester.set_origin)
            ui.button('Move to Origin', on_click=tester.move_to_origin)
        
        # Corner buttons
        with ui.grid(columns=2).classes('gap-4 m-4'):
            ui.button('Top Left', on_click=lambda: tester.move_to_corner('top_left'))
            ui.button('Top Right', on_click=lambda: tester.move_to_corner('top_right'))
            ui.button('Bottom Left', on_click=lambda: tester.move_to_corner('bottom_left'))
            ui.button('Bottom Right', on_click=lambda: tester.move_to_corner('bottom_right'))
        
        # Large adjustment (10mm)
        with ui.row().classes('gap-4 m-4'):
            ui.button('← 10', on_click=lambda: tester.adjust_position('x', 10))
            ui.button('→ 10', on_click=lambda: tester.adjust_position('x', -10))
            ui.button('↑ 10', on_click=lambda: tester.adjust_position('y', 10))
            ui.button('↓ 10', on_click=lambda: tester.adjust_position('y', -10))
        
        # Position adjustment
        with ui.row().classes('gap-4 m-4'):
            ui.button('←', on_click=lambda: tester.adjust_position('x', 1))
            ui.button('→', on_click=lambda: tester.adjust_position('x', -1))
            ui.button('↑', on_click=lambda: tester.adjust_position('y', 1))
            ui.button('↓', on_click=lambda: tester.adjust_position('y', -1))
        
        # Fine adjustment
        with ui.row().classes('gap-4 m-4'):
            ui.button('← 0.1', on_click=lambda: tester.adjust_position('x', 0.1))
            ui.button('→ 0.1', on_click=lambda: tester.adjust_position('x', -0.1))
            ui.button('↑ 0.1', on_click=lambda: tester.adjust_position('y', 0.1))
            ui.button('↓ 0.1', on_click=lambda: tester.adjust_position('y', -0.1))

        # Pen up and down
        ui.button('Pen Up', on_click=lambda: tester.pen_up())
        ui.button('Pen Down', on_click=lambda: tester.pen_down())
        
        # Current position display
        ui.label().bind_text_from(tester, 'current_x', lambda x: f'Current X: {x:.1f}mm')
        ui.label().bind_text_from(tester, 'current_y', lambda y: f'Current Y: {y:.1f}mm')
        ui.label().bind_text_from(tester, 'origin_offset', lambda o: f'Origin Offset: {o[0]:.1f}mm, {o[1]:.1f}mm')

if __name__ in {"__main__", "__mp_main__"}:
    main()
    ui.run(title='Display Dimension Tester', port=8080) 
    