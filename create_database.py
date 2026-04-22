import pandas as pd
import os

def parse_fasta(file_path):
    """
    Parses a FASTA file and extracts (UniProt ID, Sequence, Tm).
    Assumes header format: >OrganismID|UniProtID|Tm
    """
    data = []
    
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return []

    try:
        with open(file_path, 'r') as f:
            header = None
            sequence = []
            
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith('>'):
                    # Save previous entry if exists
                    if header:
                        # Extract info from header
                        try:
                            parts = header[1:].split('|')
                            if len(parts) >= 3:
                                uniprot_id = parts[1]
                                tm = float(parts[2])
                                full_sequence = "".join(sequence)
                                data.append({'uniprot_id': uniprot_id, 'sequence': full_sequence, 'tm': tm})
                        except ValueError as e:
                            print(f"Skipping malformed header or Tm: {header} - {e}")
                        except IndexError as e:
                            print(f"Skipping malformed header format: {header} - {e}")

                    # Start new entry
                    header = line
                    sequence = []
                else:
                    sequence.append(line)
            
            # Process the last entry
            if header:
                try:
                    parts = header[1:].split('|')
                    if len(parts) >= 3:
                        uniprot_id = parts[1]
                        tm = float(parts[2])
                        full_sequence = "".join(sequence)
                        data.append({'uniprot_id': uniprot_id, 'sequence': full_sequence, 'tm': tm})
                except ValueError as e:
                    print(f"Skipping malformed header or Tm in last entry: {header} - {e}")

    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return []

    return data

def create_database():
    # Define file paths
    # Using relative path assuming script is in GNN_Project and Dataset is in parent/Dataset
    dataset_path = os.path.join(os.path.dirname(__file__), '..', 'Dataset', 'TemStaPro-Major-30-imbal-training.fasta')
    dataset_path = os.path.abspath(dataset_path)
    output_path = 'protein_data.csv'

    print(f"Reading dataset from: {dataset_path}")
    
    data = parse_fasta(dataset_path)
    
    if not data:
        print("No data extracted. Exiting.")
        return

    print(f"Extracted {len(data)} entries.")
    
    df = pd.DataFrame(data)
    
    print("DataFrame Header:")
    print(df.head())
    
    print(f"Saving to {output_path}...")
    df.to_csv(output_path, index=False)
    print("Database creation complete.")

if __name__ == "__main__":
    create_database()
