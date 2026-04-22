import os
import torch
import numpy as np
import matplotlib.pyplot as plt
from torch_geometric.loader import DataLoader
from gnn_data import ProteinGraphDataset
from gnn_model import GNNModel, GINModel
from scipy.stats import pearsonr

def evaluate():
    DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {DEVICE}")

    project_dir = os.path.dirname(os.path.abspath(__file__))
    pdb_dir = os.path.join(project_dir, 'alphafold_structures_100k')
    csv_file = os.path.join(project_dir, 'data_100k.csv') 
    dataset_root = os.path.join(project_dir, 'gnn_dataset_100k')

    print("Loading Dataset from disk to RAM (this may take a few minutes)...")
    dataset = ProteinGraphDataset(root=dataset_root, csv_file=csv_file, pdb_dir=pdb_dir)
    
    # Take a 4000 sample slice using memory-safe Subset to generate a clean scatter plot
    from torch.utils.data import Subset
    indices = np.random.permutation(len(dataset))
    test_dataset = Subset(dataset, indices[:4000])
    loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

    print("Loading the optimized 100K Hybrid Model...")
    model = GINModel(num_node_features=320, hidden_dim=128).to(DEVICE)
    model.load_state_dict(torch.load('gin_model_best.pth', map_location=DEVICE))
    model.eval()

    all_preds = []
    all_targets = []
    
    print("Generating Predictions...")
    with torch.no_grad():
        for data in loader:
            data = data.to(DEVICE)
            out = model(data.x, data.edge_index, data.batch)
            all_preds.extend(out.squeeze().cpu().numpy())
            all_targets.extend(data.y.cpu().numpy())

    all_preds = np.array(all_preds)
    all_targets = np.array(all_targets)
    
    corr, _ = pearsonr(all_targets, all_preds)
    print(f"Pearson Correlation: {corr:.4f}")

    # Plot
    print("Rendering scatter plot...")
    plt.figure(figsize=(10, 8))
    
    # Use seaborn-style colors and transparency for dense scatter plots
    plt.scatter(all_targets, all_preds, alpha=0.4, color='royalblue', edgecolors='none', s=20)
    
    # Line of perfect prediction
    plt.plot([min(all_targets), max(all_targets)], [min(all_targets), max(all_targets)], 
             color='crimson', linestyle='--', linewidth=2.5, label='Perfect Prediction')
             
    plt.xlabel('True Melting Temperature (°C)', fontsize=14, fontweight='bold')
    plt.ylabel('Predicted Melting Temperature (°C)', fontsize=14, fontweight='bold')
    plt.title(f'Hybrid GIN Predictions (Pearson r = {corr:.3f})', fontsize=16, fontweight='bold', pad=15)
    
    plt.legend(fontsize=12)
    plt.grid(True, linestyle=':', alpha=0.6)
    
    # Make background slightly styled
    ax = plt.gca()
    ax.set_facecolor('#f8f9fa')
    
    plt.tight_layout()
    plt.savefig('gin_prediction_scatter.png', dpi=300, bbox_inches='tight')
    print("Successfully saved stunning scatter plot to gin_prediction_scatter.png")

if __name__ == "__main__":
    evaluate()
