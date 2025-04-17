import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def load_measurement_data(file_path):
    """Load and process measurement data from JSON file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Extract dimensions
    width, height = data['size']
    resolution = data['resolution']
    measurements = data['measurements']
    
    # Create empty array for values
    values = np.zeros((resolution[1], resolution[0]))
    
    # Check if measurements is a list of lists of dictionaries or just a list of lists
    if isinstance(measurements[0][0], dict):
        # Format with dictionaries containing x, y, value
        for y, row in enumerate(measurements):
            for x, point in enumerate(row):
                values[y, x] = point['value']
    else:
        # Format with direct values
        for y, row in enumerate(measurements):
            for x, value in enumerate(row):
                values[y, x] = value
    
    # Flip the array vertically to mirror the y-axis
    values = np.flipud(values)
    
    return values, data['sensor']

def plot_measurement_comparison(measurement_files, output_path=None):
    """Plot two measurements and their difference side by side."""
    # Load both measurement data
    values1, sensor1 = load_measurement_data(measurement_files[0])
    values2, sensor2 = load_measurement_data(measurement_files[1])
    
    # Calculate difference
    difference = values2 - values1
    
    # Create figure with three subplots
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    # Plot first measurement
    im1 = axes[0].imshow(values1, cmap='viridis', origin='lower')
    axes[0].set_title(f'Measurement 1\n{Path(measurement_files[0]).stem}')
    cbar1 = plt.colorbar(im1, ax=axes[0])
    cbar1.set_label('Value')
    
    # Plot second measurement
    im2 = axes[1].imshow(values2, cmap='viridis', origin='lower')
    axes[1].set_title(f'Measurement 2\n{Path(measurement_files[1]).stem}')
    cbar2 = plt.colorbar(im2, ax=axes[1])
    cbar2.set_label('Value')
    
    # Plot difference with color bar
    vmax = max(abs(difference.min()), abs(difference.max()))
    im3 = axes[2].imshow(difference, cmap='RdBu', vmin=-vmax, vmax=vmax, origin='lower')
    axes[2].set_title('Difference (2 - 1)')
    cbar3 = plt.colorbar(im3, ax=axes[2])
    cbar3.set_label('Difference')
    
    # Add labels and adjust layout
    for ax in axes:
        ax.set_xlabel('X position')
        ax.set_ylabel('Y position')
        ax.set_xticks([])
        ax.set_yticks([])
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
    else:
        plt.show()
    
    return values1, values2

if __name__ == "__main__":
    # List of two measurement files to compare
    measurements = [
        "ANYCUBIC_M7Pro_Messung1.json",
        "ANYCUBICM7Pro_Messung2.json",
    ]
    
    # Plot comparison and get values for scatter plot
    values1, values2 = plot_measurement_comparison(measurements, "measurement_comparison.png")
    
    # Create scatter plot
    plt.figure(figsize=(10, 8))
    plt.scatter(values1.flatten(), values2.flatten(), alpha=0.5, s=10)
    
    # Add line of perfect agreement
    min_val = min(values1.min(), values2.min())
    max_val = max(values1.max(), values2.max())
    plt.plot([min_val, max_val], [min_val, max_val], 'r--', label='Perfect agreement')
    
    plt.xlabel('Measurement 1 Value')
    plt.ylabel('Measurement 2 Value')
    plt.title('Scatter Plot of Measurement Values')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.savefig("measurement_scatter.png", dpi=300, bbox_inches='tight')
    plt.close() 