import math
from typing import List
import plotly.graph_objects as go
import click
import json
import numpy as np
import cv2 as cv
import itertools
from scipy.ndimage.filters import gaussian_filter
from scipy.interpolate import Akima1DInterpolator
from .ui_common import Resolution
import os

def replacePeaks(arr: np.array, threshold: float, windowSize: int):
    """
    Given an array and threshold, replace peaks with local average of
    windowSize×windowSize.
    """
    result = np.copy(arr)
    height, width = arr.shape

    halfWindow = windowSize // 2

    for i in range(halfWindow, height - halfWindow):
        for j in range(halfWindow, width - halfWindow):
            if arr[i, j] > threshold:
                localWindow = arr[i - halfWindow: i + halfWindow + 1, j - halfWindow: j + halfWindow + 1]
                localWindowWithoutPeak = localWindow[localWindow != arr[i, j]]
                localAverage = np.mean(localWindowWithoutPeak)
                result[i, j] = localAverage

    return result

def normalizeData(data: List[List[dict]], lowThreshold=0) -> List[List[float]]:
    # Extract just the values from the measurement dictionaries
    values = [[point['value'] for point in row] for row in data]
    
    # Convert to numpy array
    npArray = np.array(values)

    # There are often faulty peaks in the source data, let's filter them out
    mean = np.mean(npArray)
    npArray = replacePeaks(npArray, 1.5 * mean, 3)

    max = np.max(npArray)
    npArray = np.clip(npArray, lowThreshold, max)
    npArray[npArray == lowThreshold] = None

    return npArray.tolist()

@click.command()
@click.argument("input", type=click.Path())
@click.argument("output", type=click.Path())
@click.option("--title", type=str, default="Display measurement",
    help="Plot title")
@click.option("--show", type=bool, is_flag=True,
    help="Immediately show")
@click.option("--threshold", type=int, default=0,
    help="Minimal value to crop")
def visualize(input, output, title, show, threshold):
    with open(input) as f:
        measurement = json.load(f)
    data = normalizeData(measurement["measurements"], lowThreshold=threshold)
    
    # Calculate statistics
    np_data = np.array(data)
    min_val = np.nanmin(np_data)
    max_val = np.nanmax(np_data)
    avg_val = np.nanmean(np_data)
    
    # Add statistics to title
    stats_title = f"{title}<br>Min: {min_val:.3f} | Max: {max_val:.3f} | Avg: {avg_val:.3f}"
    
    # Create figure with proper orientation
    fig = go.Figure(data=[go.Surface(z=data)])
    
    # Update layout to ensure X0Y0 is at top left
    fig.update_layout(
        title=stats_title,
        autosize=True,
        scene=dict(
            aspectmode="manual",
            aspectratio=dict(x=1, y=measurement["resolution"][1]/measurement["resolution"][0], z=0.1),
            camera=dict(
                up=dict(x=0, y=0, z=1),
                center=dict(x=0, y=0, z=0),
                eye=dict(x=1.5, y=1.5, z=1.5)
            ),
            xaxis=dict(
                title='X',
                range=[0, len(data[0])-1],
                autorange='reversed'  # Reverse X axis to match X0Y0 at top left
            ),
            yaxis=dict(
                title='Y',
                range=[0, len(data)-1]
            ),
            zaxis=dict(
                title='Brightness'
            )
        )
    )
    
    fig.write_html(output)
    if show:
        fig.show()

def lineIntersection(line1, line2):
    """
    Finds the intersection of two lines given in Hesse normal form.

    Returns closest integer pixel locations.
    See https://stackoverflow.com/a/383527/5087436
    """
    rho1, theta1 = line1
    rho2, theta2 = line2
    A = np.array([
        [np.cos(theta1), np.sin(theta1)],
        [np.cos(theta2), np.sin(theta2)]
    ])
    b = np.array([[rho1], [rho2]])
    try:
        x0, y0 = np.linalg.solve(A, b)
    except np.linalg.LinAlgError:
        return None
    x0, y0 = int(np.round(x0)), int(np.round(y0))
    return (x0, y0)

def locateScreenAutomatic(image, threshold):
    npImg = np.array(image)
    ret, thresholded = cv.threshold(npImg, threshold, 255, cv.THRESH_BINARY)
    thresholded = np.uint8(thresholded)

    contours, hierarchy = cv.findContours(thresholded, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    # We draw contours to find lines in the using Hough transform
    countoursImg = np.zeros((len(image), len(image[0])), dtype=np.uint8)
    cv.drawContours(countoursImg, contours, 0, 255,  1)

    # Detect the lines
    lines = cv.HoughLines(countoursImg, 0.5, np.pi / 360, len(image[0]) // 5, None, 0, 0, 0, 3 / 4 * np.pi)
    dbgImg1 = cv.cvtColor(countoursImg, cv.COLOR_GRAY2RGB)

    def thetaClose(a, b):
        return abs(a - b) < np.pi / 40

    def rhoClose(a, b):
        return abs(a - b) < 10

    if lines is not None:
        # Find strong lines
        strongLines = []
        for line in lines:
            rho, theta = line[0][0], line[0][1]
            if any(rhoClose(rho, l[0]) and thetaClose(theta, l[1]) for l in strongLines):
                continue
            strongLines.append((rho, theta))

        # Draw lines into dbg image:
        for line in strongLines:
            rho, theta = line[0], line[1]
            a = math.cos(theta)
            b = math.sin(theta)
            x0 = a * rho
            y0 = b * rho
            pt1 = (int(x0 + 1000*(-b)), int(y0 + 1000*(a)))
            pt2 = (int(x0 - 1000*(-b)), int(y0 - 1000*(a)))
            cv.line(dbgImg1, pt1, pt2, (255,0,255), 1, cv.LINE_AA)

    intersections = [lineIntersection(l1, l2) for l1, l2 in itertools.product(strongLines, strongLines) if l1 != l2]
    fitsInImage = lambda p: p[0] > 0 and p[0] <= len(image[0]) and p[1] > 0 and p[1] <= len(image)
    corners = list(set([x for x in intersections if x is not None and fitsInImage(x)]))
    return corners

def originDistance(point):
    return point[0] ** 2 + point[1] ** 2

def cropToScreen(image, corners, screenSize):
    assert len(corners) == 4

    npImg = np.array(image)

    # Sort corners to ensure X0Y0 is at the black corner
    sortedCorners = sorted(corners, key=lambda p: (p[0] + p[1]))  # Sort by sum of coordinates
    expected = sorted([(0, 0), (0, screenSize[1]), (screenSize[0], 0), screenSize],
                      key=lambda p: (p[0] + p[1]))  # Sort by sum of coordinates

    perspTransform = cv.getPerspectiveTransform(np.float32(sortedCorners), np.float32(expected))
    return cv.warpPerspective(npImg, perspTransform, screenSize)

@click.command()
@click.argument("output", type=click.Path())
@click.option("--measurement", type=click.Path(exists=True, file_okay=True, dir_okay=False),
    required=True,
    help="The full-screen measurement JSON file")
@click.option("--min", "min_value", type=int, default=0,
    help="The minimal brightness value (0-255)")
@click.option("--max", "max_value", type=int, default=255,
    help="The maximal brightness value (0-255)")
@click.option("--screen", type=Resolution(), required=True,
    help="The screen resolution in pixels")
@click.option("--manual", is_flag=True,
    help="Locate screen manually")
def compensate(output, measurement, min_value, max_value, screen, manual):
    """
    Build a compensation mask for a given LCD. Provide a full-screen measurement
    and screen resolution to build a PNG compensation mask that you can load
    into UVTools and apply it.
    """
    with open(measurement) as f:
        measurement = json.load(f)
    
    # Extract values from the measurement data structure
    data = np.array([[point['value'] for point in row] for row in measurement["measurements"]])

    # Analyze measurement values
    min_val = np.nanmin(data)
    max_val = np.nanmax(data)
    mean_val = np.nanmean(data)
    
    # Calculate a more meaningful minimum value
    # Use the 5th percentile as minimum to exclude extreme outliers
    valid_min = np.nanpercentile(data, 5)
    
    print(f"\nMeasurement analysis:")
    print(f"Raw minimum value: {min_val:.2f} mW")
    print(f"Valid minimum value (5th percentile): {valid_min:.2f} mW")
    print(f"Maximum value: {max_val:.2f} mW")
    print(f"Mean value: {mean_val:.2f} mW")
    print(f"Dynamic range: {max_val/valid_min:.1f}x")

    corners = []
    if not manual:
        corners = [(0, 0), (0, data.shape[0]), (data.shape[1], 0), (data.shape[1], data.shape[0])]
    if len(corners) != 4 or manual:
        from .manual_crop import locateScreenManually
        corners = locateScreenManually(data)
        print(corners)

    map = cropToScreen(data, corners, screen)
    
    # Replace any NaN values with the mean value
    map = np.nan_to_num(map, nan=mean_val)
    
    # Apply general smoothing to reduce noise
    map = gaussian_filter(map, sigma=0.8)
    
    # Create base compensation mask
    compensation = np.ones_like(map)
    
    # Define threshold levels based on measured values
    # Calculate thresholds relative to the measured range
    max_measured = max_val
    min_measured = valid_min
    range_measured = max_measured - min_measured
    
    # Create interpolation points for smooth transitions
    x_points = np.array([min_measured, 
                        min_measured + range_measured * 0.1,
                        min_measured + range_measured * 0.2,
                        min_measured + range_measured * 0.35,
                        min_measured + range_measured * 0.5,
                        min_measured + range_measured * 0.65,
                        min_measured + range_measured * 0.8,
                        min_measured + range_measured * 0.9,
                        max_measured])
    
    # Sanftere Kompensation mit mehr Zwischenstufen
    y_points = np.array([0.99, 0.97, 0.95, 0.93, 0.91, 0.89, 0.87, 0.86, 0.85])
    
    # Create Akima interpolator for smooth transitions
    interpolator = Akima1DInterpolator(x_points, y_points)
    
    # Apply compensation using interpolation
    compensation = interpolator(map)
    compensation = np.clip(compensation, 0.85, 1.0)  # Ensure values stay within reasonable range
    
    # Apply edge-preserving smoothing with reduced parameters
    compensation = cv.bilateralFilter(compensation.astype(np.float32), d=3, sigmaColor=0.02, sigmaSpace=3)
    
    # Additional detail-preserving smoothing with minimal smoothing
    compensation = gaussian_filter(compensation, sigma=0.08)
    
    # Handle edge regions - create a border mask
    border_width = 50  # Width of border region to check
    height, width = compensation.shape
    border_mask = np.ones_like(compensation, dtype=bool)
    border_mask[border_width:-border_width, border_width:-border_width] = False
    
    # Set border regions to maximum brightness (1.0) if they are too dark
    border_values = compensation[border_mask]
    border_threshold = 0.9  # Sehr hoher Schwellenwert für Randbereiche
    compensation[border_mask] = np.where(border_values < border_threshold, 1.0, border_values)
    
    # Replace any remaining NaN or infinite values with 1.0 (full brightness)
    compensation = np.nan_to_num(compensation, nan=1.0, posinf=1.0, neginf=1.0)
    
    # Ensure all values are within valid range before scaling
    compensation = np.clip(compensation, 0.0, 1.0)
    
    # Scale to output range (0-255)
    compensation = min_value + (max_value - min_value) * compensation
    
    # Calculate statistics for the entire mask
    valid_values = compensation[compensation > 0]
    
    if len(valid_values) > 0:
        min_valid = np.min(valid_values)
        max_valid = np.max(valid_values)
        mean_valid = np.mean(valid_values)
        
        print("\nCompensation mask statistics:")
        print(f"Minimum value: {min_valid:.2f} (0-255)")
        print(f"Maximum value: {max_valid:.2f} (0-255)")
        print(f"Mean value (average brightness): {mean_valid:.2f} (0-255)")
        print(f"Compensation range: {max_valid/min_valid:.1f}x")
        
        # Calculate detailed statistics for each threshold
        print("\nDetailed compensation analysis:")
        for x, y in zip(x_points, y_points):
            mask = map > x
            pixels = np.sum(mask)
            if pixels > 0:
                avg_power = np.mean(map[mask])
                avg_comp = np.mean(compensation[mask])
                print(f"- Areas >{x:3.1f} mW ({pixels/compensation.size*100:4.1f}% of pixels):")
                print(f"  Avg power: {avg_power:.2f} mW, Avg compensation: {avg_comp:.1f}")
        
        # Calculate and display the impact of compensation
        strongest_dimming = (min_valid / 255.0) * 100
        print(f"\nCompensation impact:")
        print(f"- Maximum brightness reduction: {100-strongest_dimming:.1f}%")
        print(f"- Compensation thresholds: {min(x_points):.1f} mW to {max(x_points):.1f} mW")
        print(f"- Compensation range: {min(y_points)*100:.0f}% to 100% of original brightness")
    else:
        print("\nWarning: No valid compensation values found (all values are zero)")
    
    # Final cleanup and conversion to 8-bit format
    compensation = np.clip(compensation, 0, 255)  # Ensure values are in valid range
    compensation = np.round(compensation)  # Round to nearest integer
    compensation = compensation.astype(np.uint8)  # Convert to 8-bit format
    
    # Rotate the image 180 degrees and flip horizontally
    compensation = cv.rotate(compensation, cv.ROTATE_180)
    compensation = cv.flip(compensation, 1)  # Flip horizontally
    
    # Save with optimized PNG compression and settings
    cv.imwrite(output, compensation, [
        cv.IMWRITE_PNG_COMPRESSION, 9,
        cv.IMWRITE_PNG_STRATEGY, cv.IMWRITE_PNG_STRATEGY_FILTERED,
        cv.IMWRITE_PNG_BILEVEL, 0
    ])
    
    # Print file size information
    file_size = os.path.getsize(output)
    print(f"\nOutput file size: {file_size / 1024:.1f} KB")


