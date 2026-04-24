import sys
import os
import torch
import pytest

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.gnn_model import GNNModel, GINModel

def test_gnn_model_forward():
    """Test the GNNModel forward pass and output shape."""
    num_node_features = 320
    hidden_dim = 64
    batch_size = 2
    num_nodes = 5
    
    model = GNNModel(num_node_features=num_node_features, hidden_dim=hidden_dim)
    
    # Mock data
    x = torch.randn(num_nodes * batch_size, num_node_features)
    # Fully connected mock graph within each batch
    edge_index = torch.tensor([[0, 1, 1, 2, 3, 4], 
                               [1, 0, 2, 1, 4, 3]], dtype=torch.long)
    batch = torch.tensor([0, 0, 0, 1, 1], dtype=torch.long)
    
    out = model(x, edge_index, batch)
    
    assert out.shape == (batch_size, 1), f"Expected output shape (2, 1), got {out.shape}"
    assert not torch.isnan(out).any(), "Model output contains NaNs"

def test_gin_model_forward():
    """Test the GINModel forward pass and output shape."""
    num_node_features = 320
    hidden_dim = 128
    batch_size = 3
    num_nodes = 6
    
    model = GINModel(num_node_features=num_node_features, hidden_dim=hidden_dim)
    
    # Mock data
    x = torch.randn(num_nodes * batch_size, num_node_features)
    edge_index = torch.tensor([[0, 1, 2, 3, 4, 5], 
                               [1, 2, 3, 4, 5, 0]], dtype=torch.long)
    batch = torch.tensor([0, 0, 1, 1, 2, 2], dtype=torch.long)
    
    out = model(x, edge_index, batch)
    
    assert out.shape == (batch_size, 1), f"Expected output shape (3, 1), got {out.shape}"
    assert not torch.isnan(out).any(), "Model output contains NaNs"
