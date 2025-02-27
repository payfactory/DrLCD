from pyaxidraw import axidraw   # import module
ad = axidraw.AxiDraw()          # Initialize class
ad.interactive()                # Enter interactive context
if not ad.connect():            # Open serial port to AxiDraw;
    quit()                      #   Exit, if no connection.
                                # Absolute moves follow:
ad.moveto(1, 1)                 # Absolute pen-up move, to (1 inch, 1 inch)
ad.lineto(0, 0)                 # Absolute pen-down move, back to origin.
ad.block()
ad.disconnect()                 # Close serial port to AxiDraw
