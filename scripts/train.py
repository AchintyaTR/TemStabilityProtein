import os
import sys
import argparse
import logging
import torch
import torch.nn.functional as F
from torch_geometric.loader import DataLoader
from torch.utils.data import Subset
import numpy as np
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error, root_mean_squared_error
from scipy.stats import pearsonr
import matplotlib.pyplot as plt

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.gnn_data import ProteinGraphDataset
from src.models.gnn_model import GNNModel, GINModel

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def train(args):
    DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Using device: {DEVICE}")

    # Paths
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pdb_dir = os.path.join(project_dir, 'alphafold_structures_100k')
    csv_file = os.path.join(project_dir, 'data_100k.csv') 
    dataset_root = os.path.join(project_dir, 'gnn_dataset_100k')

    # Load Dataset
    logger.info("Loading dataset...")
    dataset = ProteinGraphDataset(root=dataset_root, csv_file=csv_file, pdb_dir=pdb_dir)
    logger.info(f"Dataset size: {len(dataset)}")

    # Split (Streaming approach to save RAM)
    indices = np.random.permutation(len(dataset))
    train_size = int(0.8 * len(dataset))
    train_indices = indices[:train_size]
    test_indices = indices[train_size:]

    train_dataset = Subset(dataset, train_indices)
    test_dataset = Subset(dataset, test_indices)

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False)

    # Model
    model = GINModel(num_node_features=320, hidden_dim=args.hidden_dim).to(DEVICE)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    criterion = torch.nn.MSELoss()

    # Early Stopping parameters
    best_test_loss = float('inf')
    best_epoch = 0
    patience_counter = 0

    # Training Loop
    train_losses = []
    test_losses = []

    logger.info(f"Starting training for {args.epochs} epochs...")
    for epoch in range(args.epochs):
        model.train()
        total_loss = 0
        for data in train_loader:
            data = data.to(DEVICE)
            optimizer.zero_grad()
            out = model(data.x, data.edge_index, data.batch)
            loss = criterion(out.squeeze(), data.y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * data.num_graphs
        
        avg_train_loss = total_loss / len(train_loader.dataset)
        train_losses.append(avg_train_loss)

        # Validation
        model.eval()
        total_test_loss = 0
        all_preds = []
        all_targets = []
        
        with torch.no_grad():
            for data in test_loader:
                data = data.to(DEVICE)
                out = model(data.x, data.edge_index, data.batch)
                loss = criterion(out.squeeze(), data.y)
                total_test_loss += loss.item() * data.num_graphs
                
                all_preds.extend(out.squeeze().cpu().numpy())
                all_targets.extend(data.y.cpu().numpy())
        
        avg_test_loss = total_test_loss / len(test_loader.dataset)
        test_losses.append(avg_test_loss)
        
        # Calculate additional metrics
        rmse = root_mean_squared_error(all_targets, all_preds)
        mae = mean_absolute_error(all_targets, all_preds)
        r2 = r2_score(all_targets, all_preds)
        pearson_corr, _ = pearsonr(all_targets, all_preds)

        logger.info(
            f'Epoch {epoch+1:03d} | Train MSE: {avg_train_loss:.4f} | '
            f'Test MSE: {avg_test_loss:.4f} | Test RMSE: {rmse:.4f} | '
            f'Test MAE: {mae:.4f} | Test R2: {r2:.4f} | Test Pearson: {pearson_corr:.4f}'
        )

        # Early Stopping Check
        if avg_test_loss < best_test_loss:
            best_test_loss = avg_test_loss
            best_epoch = epoch + 1
            patience_counter = 0
            torch.save(model.state_dict(), 'gin_model_best.pth')
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                logger.info(f"Early stopping triggered at Epoch {epoch+1:03d}!")
                logger.info(f"Saved best model from Epoch {best_epoch:03d} with Test MSE: {best_test_loss:.4f}")
                break

    # Save Model
    torch.save(model.state_dict(), 'gin_model.pth')
    logger.info("Model saved to gin_model.pth")

    # Plot
    plt.figure()
    plt.plot(train_losses, label='Train Loss')
    plt.plot(test_losses, label='Test Loss')
    plt.xlabel('Epoch')
    plt.ylabel('MSE Loss')
    plt.legend()
    plt.savefig('gin_training_curve.png')
    logger.info("Training curve saved to gin_training_curve.png")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train GNN Model for Protein Stability")
    parser.add_argument('--batch_size', type=int, default=32, help='Batch size for training')
    parser.add_argument('--epochs', type=int, default=50, help='Number of epochs to train')
    parser.add_argument('--lr', type=float, default=0.001, help='Learning rate')
    parser.add_argument('--hidden_dim', type=int, default=128, help='Hidden dimension size for the model')
    parser.add_argument('--weight_decay', type=float, default=1e-4, help='Weight decay for optimizer')
    parser.add_argument('--patience', type=int, default=8, help='Early stopping patience')
    
    args = parser.parse_args()
    train(args)
