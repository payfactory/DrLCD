# DrLCD – Calibration of MSLA Resin Printers LCD For Even Backlight

The backlight of the masked SLA resin printers isn't perfect and it can affect
the dimensional accuracy.

This device allows you to measure the backlight and compensate for the defects:

![Illustration](assets/banner.png)

It does so via a moving a sensor over the printer's LCD:

![The device](assets/device.png)

You can learn more in the [corresponding blog
post](https://blog.honzamrazek.cz/2022/12/about-the-successful-quest-for-perfect-msla-printer-uv-backlight/).

# Structure

The repository contains a Marlin-based firmware in the `fw` directory and
command line control app that allows you to acquire data and process them in the
`drlcd` directory.

# Usage

```
# Installation
$ pip install .
$ pip install https://cdn.evilmadscientist.com/dl/ad/public/AxiDraw_API.zip


# Acquire data
$ python -m drlcd measurelcd --size <display_size_in_mm> --resolution <number_of_samples> --fast <output_file>
# E.g. drlcd measurelcd --size 202x130 --resolution 202x130 test.json

# Visualize measurement
$ python -m drlcd visualize --show --title "<graph name>" <measurement file> <output HTML>

# Create compensation map
$ python -m drlcd compensate --measurement <measurement file> --min <low value to compensate> --max <high value to compensate> --by <amount of dimming> --screen <resolution in px> --cutoff <black value for screen detection> <output PNG file>
```

```
python -m drlcd measurelcd --size 192x115 --resolution 64x38 --sleeptime 0.3 --brightness_threshold=0.5 test.json --calibrate true
python -m drlcd measurelcd --size 192x115 --resolution 64x38 --sleeptime 0.3 --brightness_threshold=0.5 test.json 
python -m drlcd visualize --show --title "Test title" test.json test.html
python -m drlcd compensate --measurement test.json --min 210 --max 255 --screen 3840x2400 test.png


```
```




python -m drlcd compensate --measurement test.json --min 0 --max 255 --screen 3840x2400 test.png --manual

python -m drlcd measurelcd --size 30x30 --resolution 10x10 --sleeptime 3.0 --brightness_threshold=0.5 test.json
python -m drlcd visualize --show --title "test" test.json test.html
python -m drlcd compensate --measurement test.json --min 210 --max 255 --screen 3840x2400 test.png
```

python -m drlcd measurelcd --size 180x109 --resolution 31x19 --sleeptime 0.3 --brightness_threshold=0.5 gammatec_sonicxl4k_mask.json --calibrate true
python -m drlcd visualize --show --title "gammatec_sonicxl4k_mask240_255" gammatec_sonicxl4k_mask_240_255.json gammatec_sonicxl4k_240_255.html
python -m drlcd compensate --measurement gammatec_sonicxl4k.json --min 210 --max 255 --screen 3840x2400 test.png --manual



python -m drlcd visualize --show --title "gammatec_sonicxl4k_no_mask.json " gammatec_sonicxl4k_no_mask.json  gammatec_sonicxl4k_no_mask.html
python -m drlcd compensate --measurement gammatec_sonicxl4k_no_mask.json --screen 3840x2400 gammatec_sonicxl4k_mask2.png --manual


python -m drlcd visualize --show --title "gammatec_sonicxl4k_mask5" gammatec_sonicxl4k_mask5.json gammatec_sonicxl4k_mask5.html

gammatec_sonicxl4k_mask5
python -m drlcd measurelcd --size 180x109 --resolution 31x19 --sleeptime 0.3 --brightness_threshold=0.5 gammatec_sonicxl4k_mask_test2.json

python -m drlcd compensate --measurement gammatec_sonicxl4k_no_mask.json --screen 3840x2400 gammatec_sonicxl4k_mask2.png --manual
python -m drlcd visualize --show --title "gammatec_sonicxl4k_mask_3" gammatec_sonicxl4k_mask_3.json gammatec_sonicxl4k_mask_3.html


