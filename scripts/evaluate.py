import os
import sys
import argparse
import logging
import torch
import numpy as np
import matplotlib.pyplot as plt
from torch_geometric.loader import DataLoader
from torch.utils.data import Subset
from scipy.stats import pearsonr

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.gnn_data import ProteinGraphDataset
from src.models.gnn_model import GNNModel, GINModel

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def evaluate(args):
    DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Using device: {DEVICE}")

    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pdb_dir = os.path.join(project_dir, 'alphafold_structures_100k')
    csv_file = os.path.join(project_dir, 'data_100k.csv') 
    dataset_root = os.path.join(project_dir, 'gnn_dataset_100k')

    logger.info("Loading Dataset from disk to RAM (this may take a few minutes)...")
    dataset = ProteinGraphDataset(root=dataset_root, csv_file=csv_file, pdb_dir=pdb_dir)
    
    # Take a sample slice using memory-safe Subset to generate a clean scatter plot
    indices = np.random.permutation(len(dataset))
    test_dataset = Subset(dataset, indices[:args.num_samples])
    loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False)

    logger.info(f"Loading the optimized Hybrid Model from {args.model_path}...")
    model = GINModel(num_node_features=320, hidden_dim=args.hidden_dim).to(DEVICE)
    model.load_state_dict(torch.load(args.model_path, map_location=DEVICE, weights_only=True))
    model.eval()

    all_preds = []
    all_targets = []
    
    logger.info("Generating Predictions...")
    with torch.no_grad():
        for data in loader:
            data = data.to(DEVICE)
            out = model(data.x, data.edge_index, data.batch)
            all_preds.extend(out.squeeze().cpu().numpy())
            all_targets.extend(data.y.cpu().numpy())

    all_preds = np.array(all_preds)
    all_targets = np.array(all_targets)
    
    corr, _ = pearsonr(all_targets, all_preds)
    logger.info(f"Pearson Correlation: {corr:.4f}")

    # Plot
    logger.info("Rendering scatter plot...")
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
    logger.info("Successfully saved stunning scatter plot to gin_prediction_scatter.png")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate GNN Model for Protein Stability")
    parser.add_argument('--batch_size', type=int, default=32, help='Batch size for evaluation')
    parser.add_argument('--hidden_dim', type=int, default=128, help='Hidden dimension size for the model')
    parser.add_argument('--num_samples', type=int, default=4000, help='Number of samples to evaluate on')
    parser.add_argument('--model_path', type=str, default='gin_model_best.pth', help='Path to saved model weights')
    
    args = parser.parse_args()
    evaluate(args)
