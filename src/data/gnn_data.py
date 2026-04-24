import os
import torch
import pandas as pd
import numpy as np
from torch_geometric.data import Dataset, Data
from biopandas.pdb import PandasPdb
from tqdm import tqdm

import esm

class ProteinGraphDataset(Dataset):
    def __init__(self, root, csv_file, pdb_dir, threshold=8.0, transform=None, pre_transform=None):
        self.csv_file = csv_file
        self.pdb_dir = pdb_dir
        self.threshold = threshold
        self.df = pd.read_csv(csv_file)
        
        # Load ESM-2 model (t6_8M is the smallest, output dim = 320)
        print("Loading ESM-2 model (8M parameters)...")
        self.esm_model, self.esm_alphabet = esm.pretrained.esm2_t6_8M_UR50D()
        self.esm_batch_converter = self.esm_alphabet.get_batch_converter()
        self.esm_model.eval()
        
        # Move ESM model to GPU if available to speed up processing
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.esm_model = self.esm_model.to(self.device)
        print(f"ESM-2 model loaded on {self.device}")

        super(ProteinGraphDataset, self).__init__(root, transform, pre_transform)

    @property
    def raw_file_names(self):
        return [self.csv_file]

    @property
    def processed_file_names(self):
        # We'll save one file per protein for simplicity in this dev phase
        return [f'data_{i}.pt' for i in range(len(self.df))]

    def download(self):
        # Data is assumed to be downloaded already via download_pdb.py
        pass

    def process(self):
        print(f"Processing {len(self.df)} proteins...")
        
        for idx, row in tqdm(self.df.iterrows(), total=len(self.df)):
            # Resume gracefully if we already generated this graph before the crash
            if os.path.exists(os.path.join(self.processed_dir, f'data_{idx}.pt')):
                continue
                
            uniprot_id = row['uniprot_id']
            sequence = str(row['sequence'])
            tm = row['tm']
            
            # Truncate extremely fast to prevent ESM-2 CUDA OOM failures on massive proteins
            if len(sequence) > 1022:
                sequence = sequence[:1022]
                
            pdb_path = os.path.join(self.pdb_dir, f"{uniprot_id}.pdb")
            
            # Node Features: ESM-2 Sequence Embeddings
            x = self._get_esm_embedding(sequence)
            
            # Edge Features: Structure-based connectivity
            if os.path.exists(pdb_path):
                try:
                    ppdb = PandasPdb().read_pdb(pdb_path)
                    # Extract C-alpha atoms
                    ca_df = ppdb.df['ATOM'][ppdb.df['ATOM']['atom_name'] == 'CA']
                    
                    # Ensure alignment between sequence and structure
                    # AlphaFold models usually cover the full sequence, but let's be safe
                    # If lengths don't match, we might need more complex alignment.
                    # For this MVP, we assume they align or truncate/pad if needed, 
                    # but simple logic: use the coordinates if count matches, else verify.
                    
                    coords = ca_df[['x_coord', 'y_coord', 'z_coord']].to_numpy()
                    
                    if len(coords) != len(sequence):
                        # Fallback: Sequence-only graph (linear chain) if structure mismatch
                        # print(f"Warning: Length mismatch for {uniprot_id} (Seq: {len(sequence)}, Struct: {len(coords)})")
                        # For now, let's treat mismatch as 'missing structure' to be safe, or just use sequence edges.
                        # Strategy: Use sequence distance loop (i connected to i+1)
                        edge_index = self._build_sequence_edges(len(sequence))
                    else:
                        # Compute distance matrix
                        dist_matrix = np.linalg.norm(coords[:, None, :] - coords[None, :, :], axis=-1)
                        # Create adjacency matrix from threshold
                        adj = (dist_matrix < self.threshold) & (dist_matrix > 0) # Exclude self-loops
                        src, dst = np.where(adj)
                        edge_index = torch.tensor([src, dst], dtype=torch.long)
                        
                except Exception as e:
                    print(f"Error parsing PDB for {uniprot_id}: {e}")
                    edge_index = self._build_sequence_edges(len(sequence))
            else:
                # Missing PDB: Create linear chain graph
                edge_index = self._build_sequence_edges(len(sequence))
            
            # Target
            y = torch.tensor([tm], dtype=torch.float)
            
            data = Data(x=x, edge_index=edge_index, y=y, uniprot_id=uniprot_id)
            
            torch.save(data, os.path.join(self.processed_dir, f'data_{idx}.pt'))

    def _get_esm_embedding(self, sequence):
        """Extracts ESM-2 embeddings for a given sequence."""
        data = [("protein", sequence)]
        batch_labels, batch_strs, batch_tokens = self.esm_batch_converter(data)
        batch_tokens = batch_tokens.to(self.device)
        
        with torch.no_grad():
            results = self.esm_model(batch_tokens, repr_layers=[6], return_contacts=False)
        
        token_representations = results["representations"][6]
        
        # Remove <cls> and <eos> tokens (first and last)
        sequence_representations = token_representations[0, 1 : len(sequence) + 1]
        
        # Move back to CPU for Dataset storage to save RAM
        return sequence_representations.cpu()

    def _build_sequence_edges(self, length):
        # Connect i to i+1
        source = list(range(length - 1))
        target = list(range(1, length))
        # Bidirectional
        src = source + target
        dst = target + source
        return torch.tensor([src, dst], dtype=torch.long)

    def len(self):
        return len(self.df)

    def get(self, idx):
        return torch.load(os.path.join(self.processed_dir, f'data_{idx}.pt'), weights_only=False)

if __name__ == "__main__":
    # Test dataset creation
    root_dir = os.path.dirname(os.path.abspath(__file__))
    dataset = ProteinGraphDataset(
        root=os.path.join(root_dir, 'gnn_dataset_dev'),
        csv_file=os.path.join(root_dir, 'dev_data.csv'),
        pdb_dir=os.path.join(root_dir, 'alphafold_structures_dev')
    )
    print(f"Created dataset with {len(dataset)} graphs.")
    print(f"First graph: {dataset[0]}")
