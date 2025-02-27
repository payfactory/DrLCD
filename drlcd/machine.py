from contextlib import contextmanager
from typing import Generator, List
from serial import Serial # type: ignore
from pyaxidraw import axidraw   # import module

class Machine:
    def __init__(self) -> None:
        self.axidraw = axidraw.AxiDraw()
        self.axidraw.interactive()
        if not self.axidraw.connect():            # Open serial port to AxiDraw;
            exit(1)

    def waitForBoot(self) -> None:
        """
        Wait for the board to boot up - that is there are no new info is echoed
        """
        pass

    def move_to(self, x: float, y: float) -> None:
        self.axidraw.moveto(x, y)
        self.axidraw.block()

    def start_measure(self) -> None:
        self.axidraw.pendown()
        self.axidraw.block()

    def stop_measure(self) -> None:
        self.axidraw.penup()
        self.axidraw.block()


@contextmanager
def machineConnection() -> Generator[Machine, None, None]:
    machine = Machine()
    try:
        yield machine
    finally:
        machine.move_to(0, 0)
