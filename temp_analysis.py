import numpy as np
import json

def analyze_measurements(filename, description):
    # Load the measurement data
    with open(filename, 'r') as f:
        data = json.load(f)

    # Convert measurements to numpy array - handle both formats
    if isinstance(data['measurements'][0][0], dict):
        # Format with dictionaries containing 'value' key
        measurements = np.array([[point['value'] for point in row] for row in data['measurements']])
    else:
        # Format with direct numeric values
        measurements = np.array(data['measurements'])

    # Calculate key statistics
    min_val = np.min(measurements)
    max_val = np.max(measurements)
    mean_val = np.mean(measurements)
    std_val = np.std(measurements)
    range_val = max_val - min_val

    # Calculate percentiles
    p5 = np.percentile(measurements, 5)
    p25 = np.percentile(measurements, 25)
    p50 = np.percentile(measurements, 50)
    p75 = np.percentile(measurements, 75)
    p95 = np.percentile(measurements, 95)

    # Count values outside mean ± 0.1 mW
    deviation_threshold = 0.1
    values_outside_range = np.sum(np.abs(measurements - mean_val) > deviation_threshold)
    percentage_outside = (values_outside_range / measurements.size) * 100

    print(f"\nMeasurement Analysis {description}:")
    print(f"Minimum value: {min_val:.3f} mW")
    print(f"Maximum value: {max_val:.3f} mW")
    print(f"Mean value: {mean_val:.3f} mW")
    print(f"Standard deviation: {std_val:.3f} mW")
    print(f"Range (max-min): {range_val:.3f} mW")
    print(f"\nPercentiles:")
    print(f"5th percentile: {p5:.3f} mW")
    print(f"25th percentile: {p25:.3f} mW")
    print(f"50th percentile (median): {p50:.3f} mW")
    print(f"75th percentile: {p75:.3f} mW")
    print(f"95th percentile: {p95:.3f} mW")
    print(f"\nUniformity Analysis:")
    print(f"Values outside mean ± {deviation_threshold} mW: {values_outside_range} pixels")
    print(f"Percentage outside tolerance: {percentage_outside:.1f}%")

    # Analyze spatial patterns
    print("\nSpatial Analysis:")
    print("Average by region:")
    rows, cols = measurements.shape
    print(f"Top left quarter: {np.mean(measurements[:rows//2, :cols//2]):.3f} mW")
    print(f"Top right quarter: {np.mean(measurements[:rows//2, cols//2:]):.3f} mW")
    print(f"Bottom left quarter: {np.mean(measurements[rows//2:, :cols//2]):.3f} mW")
    print(f"Bottom right quarter: {np.mean(measurements[rows//2:, cols//2:]):.3f} mW")
    
    return measurements, mean_val, std_val, range_val

# Analyze both datasets
print("="*80)
measurements_no_mask, mean_no_mask, std_no_mask, range_no_mask = analyze_measurements(
    'gammatec_sonicxl4k_no_mask.json', 
    'WITHOUT Compensation Mask'
)

print("\n" + "="*80)
measurements_with_mask, mean_with_mask, std_with_mask, range_with_mask = analyze_measurements(
    'gammatec_sonicxl4k_mask5.json',
    'WITH Compensation Mask'
)

# Calculate improvement metrics
print("\n" + "="*80)
print("\nImprovement Analysis:")
print(f"Mean value reduction: {((mean_no_mask - mean_with_mask) / mean_no_mask * 100):.1f}%")
print(f"Standard deviation improvement: {((std_no_mask - std_with_mask) / std_no_mask * 100):.1f}%")
print(f"Range reduction: {((range_no_mask - range_with_mask) / range_no_mask * 100):.1f}%") 