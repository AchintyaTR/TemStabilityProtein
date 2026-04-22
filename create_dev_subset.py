import pandas as pd
import os
import argparse

def create_subset(n, output_csv, output_ids):
    project_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(project_dir, 'protein_data.csv')
    
    output_csv = os.path.join(project_dir, output_csv)
    output_ids = os.path.join(project_dir, output_ids)

    print(f"Reading from {input_file}...")
    if not os.path.exists(input_file):
        print("Error: Input file not found.")
        return

    df = pd.read_csv(input_file)
    
    if len(df) < n:
        print(f"Warning: Dataset has fewer than {n} records. Using all records.")
        dev_df = df
    else:
        print(f"Sampling {n} records...")
        dev_df = df.sample(n=n, random_state=42)

    print(f"Saving dev dataset to {output_csv}...")
    dev_df.to_csv(output_csv, index=False)

    print(f"Extracting IDs to {output_ids}...")
    with open(output_ids, 'w') as f:
        for uid in dev_df['uniprot_id'].unique():
            f.write(f"{uid}\n")

    print("Subset creation complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--n', type=int, default=20000, help='Number of samples')
    parser.add_argument('--out_csv', type=str, default='data_20k.csv', help='Output CSV name')
    parser.add_argument('--out_txt', type=str, default='uniprot_ids_20k.txt', help='Output IDs text file name')
    args = parser.parse_args()
    
    create_subset(args.n, args.out_csv, args.out_txt)
