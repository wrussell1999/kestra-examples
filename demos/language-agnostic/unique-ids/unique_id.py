import pandas as pd
import hashlib

def generate_md5_hash(row):
    # Use string representation exactly as-is from CSV
    fields = [
        str(row['VendorID']),
        str(row['lpep_pickup_datetime']),
        str(row['lpep_dropoff_datetime']),
        str(row['PULocationID']),
        str(row['DOLocationID']),
        str(row['fare_amount']),
        str(row['trip_distance']),
    ]
    raw_input = ''.join(fields)
    return hashlib.md5(raw_input.encode('utf-8')).hexdigest()

def add_unique_hash_column(input_csv_path, output_csv_path):
    # Load the CSV file
    df = pd.read_csv(input_csv_path, dtype=str, keep_default_na=False)

    # Generate the hash for each row
    df['unique_row_id'] = df.apply(generate_md5_hash, axis=1)

    # Save the modified DataFrame to a new CSV
    df.to_csv(output_csv_path, index=False)
    print(f"Processed file saved to: {output_csv_path}")

# Example usage
input_csv = 'green_tripdata_2019-01.csv'  # Replace with your input file path
output_csv = 'python.csv'  # Replace with desired output file path
add_unique_hash_column(input_csv, output_csv)
