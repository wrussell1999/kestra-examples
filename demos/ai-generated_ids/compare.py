import pandas as pd

def load_unique_ids(file_path):
    df = pd.read_csv(file_path)
    if 'unique_row_id' not in df.columns:
        raise ValueError(f"'unique_row_id' column not found in {file_path}")
    return set(df['unique_row_id'].dropna())

def compare_csv_files(file1, file2):
    ids1 = load_unique_ids(file1)
    ids2 = load_unique_ids(file2)

    only_in_file1 = ids1 - ids2
    only_in_file2 = ids2 - ids1
    in_both = ids1 & ids2

    print(f"Total unique IDs in {file1}: {len(ids1)}")
    print(f"Total unique IDs in {file2}: {len(ids2)}")
    print(f"Matching IDs: {len(in_both)}")
    print(f"IDs only in {file1}: {len(only_in_file1)}")
    print(f"IDs only in {file2}: {len(only_in_file2)}")

    if not only_in_file1 and not only_in_file2:
        print("✅ The files are identical based on unique_row_id.")
    elif in_both:
        print("⚠️ The files partially overlap based on unique_row_id.")
    else:
        print("❌ The files are completely different based on unique_row_id.")

# Example usage
file_path_1 = 'python.csv'
file_path_2 = 'go.csv'
compare_csv_files(file_path_1, file_path_2)
