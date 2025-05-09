import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import matplotlib.image as mpimg
from scipy.ndimage import zoom

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

def calculate_differences(original_values, all_values):
    """Calculate the difference between each measurement and the original measurement."""
    differences = []
    for values in all_values:
        if values is not None:
            diff = values - original_values
            differences.append(diff)
        else:
            differences.append(None)
    return differences

def plot_measurements_and_masks(measurement_files, mask_files, output_path=None):
    """Plot measurements and corresponding mask images side by side."""
    n_measurements = len(measurement_files)
    n_rows = n_measurements
    n_cols = 2  # One for measurement, one for mask
    
    # First load all measurement data
    all_values = []
    all_sensors = []
    for meas_file in measurement_files:
        try:
            values, sensor = load_measurement_data(meas_file)
            all_values.append(values)
            all_sensors.append(sensor)
        except Exception as e:
            print(f"Error processing measurement {meas_file}: {e}")
            all_values.append(None)
            all_sensors.append(None)
    
    # Calculate differences from the original measurement
    original_values = all_values[0]  # First measurement is considered the original
    differences = calculate_differences(original_values, all_values)
    
    # Find global min and max from valid differences
    valid_diffs = [d for d in differences if d is not None]
    if valid_diffs:
        vmin = min(d.min() for d in valid_diffs)
        vmax = max(d.max() for d in valid_diffs)
    else:
        vmin, vmax = -1, 1  # Default range if no valid differences
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(12, 6*n_rows))
    if n_rows == 1:
        axes = axes.reshape(1, -1)
    
    # Plot each difference and mask pair
    for idx, (diff, sensor, mask_file) in enumerate(zip(differences, all_sensors, mask_files)):
        # Plot difference data
        if diff is not None:
            im = axes[idx, 0].imshow(diff, cmap='RdBu', vmin=vmin, vmax=vmax, origin='lower')
            axes[idx, 0].set_title(f'{Path(measurement_files[idx]).stem}\nSensor: {sensor}')
            cbar = plt.colorbar(im, ax=axes[idx, 0])
            cbar.set_label('Difference from Original')
            axes[idx, 0].set_xlabel('X position')
            axes[idx, 0].set_ylabel('Y position')
        else:
            axes[idx, 0].text(0.5, 0.5, f'Error loading\n{Path(measurement_files[idx]).name}',
                            ha='center', va='center')
        
        # Plot mask image if available, otherwise show "No mask" message
        if mask_file is None:
            axes[idx, 1].text(0.5, 0.5, 'No mask\n(Original measurement)',
                            ha='center', va='center', fontsize=12)
            axes[idx, 1].set_title('No mask')
        else:
            try:
                if Path(mask_file).exists():
                    mask = mpimg.imread(mask_file)
                    # Convert to grayscale if it's a color image
                    if len(mask.shape) == 3:
                        mask = np.mean(mask, axis=2)
                    # Scale mask values to 0-255 range
                    mask = (mask * 255).astype(np.uint8)
                    mask_im = axes[idx, 1].imshow(mask, cmap='gray', vmin=0, vmax=255, origin='lower')
                    axes[idx, 1].set_title(f'Mask: {Path(mask_file).stem}')
                    # Add color bar showing mask brightness values
                    cbar = plt.colorbar(mask_im, ax=axes[idx, 1])
                    cbar.set_label('Mask Brightness (0-255)')
                else:
                    axes[idx, 1].text(0.5, 0.5, f'Mask file not found:\n{mask_file}',
                                    ha='center', va='center')
            except Exception as e:
                print(f"Error processing mask {mask_file}: {e}")
                axes[idx, 1].text(0.5, 0.5, f'Error loading\n{Path(mask_file).name}',
                                ha='center', va='center')
        
        axes[idx, 1].set_xlabel('X position')
        axes[idx, 1].set_ylabel('Y position')
        
        # Remove ticks for cleaner look
        axes[idx, 0].set_xticks([])
        axes[idx, 0].set_yticks([])
        axes[idx, 1].set_xticks([])
        axes[idx, 1].set_yticks([])
    
    # Add a title showing the difference range
    fig.suptitle(f'Difference Range: {vmin:.3f} to {vmax:.3f}', y=1.02)
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
    else:
        plt.show()

def create_measurement_distribution(measurement_files, mask_files, original_measurement_file="gammatec_sonicxl4k_no_mask.json", output_path="measurement_distribution.png"):
    """Create a scatter plot showing the relationship between mask brightness and measurement differences for all measurements."""
    # Load original measurement data (without mask)
    original_values, _ = load_measurement_data(original_measurement_file)
    
    # Create scatter plot
    plt.figure(figsize=(12, 8))
    
    # Define colors for different masks
    colors = ['blue', 'red', 'green']
    
    # Plot each measurement-mask pair
    for meas_file, mask_file, color in zip(measurement_files[1:], mask_files[1:], colors):
        if mask_file is not None:
            # Load current measurement data
            values, sensor = load_measurement_data(meas_file)
            
            # Load and process mask image
            mask = mpimg.imread(mask_file)
            if len(mask.shape) == 3:  # Convert to grayscale if color image
                mask = np.mean(mask, axis=2)
            mask = (mask * 255).astype(np.uint8)  # Scale to 0-255 range
            
            # Downsize mask to match measurement resolution
            zoom_factors = (values.shape[0] / mask.shape[0], values.shape[1] / mask.shape[1])
            mask_resized = zoom(mask, zoom_factors, order=1)  # order=1 for bilinear interpolation
            
            # Calculate differences from original measurement
            differences = values - original_values
            
            # Plot the data
            plt.scatter(mask_resized.flatten(), differences.flatten(), 
                       alpha=0.5, s=10, color=color,
                       label=f'Mask {Path(mask_file).stem.split("_")[-1]}')
    
    # Add labels and title
    plt.xlabel('Mask Brightness (0-255)')
    plt.ylabel('Measurement Difference')
    plt.title(f'Relationship between Mask Brightness and Measurement Differences\nSensor: {sensor}')
    
    # Add legend
    plt.legend()
    
    # Add grid
    plt.grid(True, alpha=0.3)
    
    # Save the plot
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    # List of measurement files and corresponding mask files
    measurements = [
        "gammatec_sonicxl4k_no_mask.json",  # Original measurement without mask
        "gammatec_sonicxl4k_mask5.json",
        "gammatec_sonicxl4k_mask4.json",
        "gammatec_sonicxl4k_mask_3.json"
    ]
    
    masks = [
        None,  # No mask for the original measurement
        "gammatec_sonicxl4k_mask5.png",
        "gammatec_sonicxl4k_mask4.png",
        "gammatec_sonicxl4k_mask3.png"
    ]
    
    # Plot measurements and masks
    plot_measurements_and_masks(measurements, masks, "measurement_differences.png")
    
    # Create single scatter plot for all measurements
    create_measurement_distribution(measurements, masks) 