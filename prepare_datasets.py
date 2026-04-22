import pandas as pd
import os
from sklearn.model_selection import train_test_split

def prepare_datasets():
    # Define paths
    project_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(project_dir, 'protein_data.csv')
    train_file = os.path.join(project_dir, 'train_data.csv')
    test_file = os.path.join(project_dir, 'test_data.csv')
    ids_file = os.path.join(project_dir, 'uniprot_ids.txt')

    print(f"Loading data from {input_file}...")
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    print(f"Total records: {len(df)}")

    # Extract UniProt IDs
    print(f"Extracting UniProt IDs to {ids_file}...")
    uniprot_ids = df['uniprot_id'].unique()
    with open(ids_file, 'w') as f:
        for uid in uniprot_ids:
            f.write(f"{uid}\n")
    print(f"Extracted {len(uniprot_ids)} unique IDs.")

    # Split data
    print("Splitting data into Train (80%) and Test (20%)...")
    train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)

    print(f"Train set: {len(train_df)} records")
    print(f"Test set: {len(test_df)} records")

    print(f"Saving to {train_file}...")
    train_df.to_csv(train_file, index=False)

    print(f"Saving to {test_file}...")
    test_df.to_csv(test_file, index=False)

    print("Dataset preparation complete.")

if __name__ == "__main__":
    prepare_datasets()
