import os
import torch
import torch.nn.functional as F
from torch_geometric.loader import DataLoader
from torch.utils.data import Subset
import numpy as np
from gnn_data import ProteinGraphDataset
from gnn_model import GNNModel, GINModel
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error, root_mean_squared_error
from scipy.stats import pearsonr
import matplotlib.pyplot as plt

def train():
    # settings
    BATCH_SIZE = 32
    EPOCHS = 50
    LR = 0.001
    DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {DEVICE}")

    # Paths
    project_dir = os.path.dirname(os.path.abspath(__file__))
    pdb_dir = os.path.join(project_dir, 'alphafold_structures_100k')
    csv_file = os.path.join(project_dir, 'data_100k.csv') 
    dataset_root = os.path.join(project_dir, 'gnn_dataset_100k')

    # Load Dataset
    dataset = ProteinGraphDataset(root=dataset_root, csv_file=csv_file, pdb_dir=pdb_dir)
    print(f"Dataset size: {len(dataset)}")

    # Split (Streaming approach to save RAM)
    indices = np.random.permutation(len(dataset))
    train_size = int(0.8 * len(dataset))
    train_indices = indices[:train_size]
    test_indices = indices[train_size:]

    train_dataset = Subset(dataset, train_indices)
    test_dataset = Subset(dataset, test_indices)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)

    # Model
    model = GINModel(num_node_features=320, hidden_dim=128).to(DEVICE) # Increased hidden dim too
    optimizer = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=1e-4) # Added Weight Decay (L2)
    criterion = torch.nn.MSELoss()

    # Early Stopping parameters
    best_test_loss = float('inf')
    best_epoch = 0
    patience = 8
    patience_counter = 0

    # Training Loop
    train_losses = []
    test_losses = []

    for epoch in range(EPOCHS):
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

        if (epoch + 1) % 1 == 0:
            print(f'Epoch {epoch+1:03d} | Train MSE: {avg_train_loss:.4f} | Test MSE: {avg_test_loss:.4f} | Test RMSE: {rmse:.4f} | Test MAE: {mae:.4f} | Test R2: {r2:.4f} | Test Pearson: {pearson_corr:.4f}', flush=True)

        # Early Stopping Check
        if avg_test_loss < best_test_loss:
            best_test_loss = avg_test_loss
            best_epoch = epoch + 1
            patience_counter = 0
            torch.save(model.state_dict(), 'gin_model_best.pth')
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"Early stopping triggered at Epoch {epoch+1:03d}!")
                print(f"Saved best model from Epoch {best_epoch:03d} with Test MSE: {best_test_loss:.4f}")
                break

    # Save Model
    torch.save(model.state_dict(), 'gin_model.pth')
    print("Model saved to gin_model.pth")

    # Plot
    plt.figure()
    plt.plot(train_losses, label='Train Loss')
    plt.plot(test_losses, label='Test Loss')
    plt.xlabel('Epoch')
    plt.ylabel('MSE Loss')
    plt.legend()
    plt.savefig('gin_training_curve.png')
    print("Training curve saved to gin_training_curve.png")

if __name__ == "__main__":
    train()
