import torch
import torch.nn.functional as F
from torch.nn import Linear, Sequential, BatchNorm1d, ReLU
from torch_geometric.nn import GCNConv, GINConv, global_add_pool, global_mean_pool

class GNNModel(torch.nn.Module):
    """
    Graph Convolutional Network (GCN) model for predicting protein melting temperature.
    
    Uses 3 layers of GCNConv followed by global mean pooling and a linear readout.
    """
    def __init__(self, num_node_features: int = 320, hidden_dim: int = 64):
        super(GNNModel, self).__init__()
        self.conv1 = GCNConv(num_node_features, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, hidden_dim)
        self.conv3 = GCNConv(hidden_dim, hidden_dim)
        self.lin = Linear(hidden_dim, 1)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, batch: torch.Tensor) -> torch.Tensor:
        """
        Forward pass for the GNNModel.
        
        Args:
            x (torch.Tensor): Node feature matrix of shape [num_nodes, num_node_features].
            edge_index (torch.Tensor): Graph edge indices of shape [2, num_edges].
            batch (torch.Tensor): Batch vector assigning each node to a specific graph.
            
        Returns:
            torch.Tensor: Predicted values of shape [batch_size, 1].
        """
        # 1. Obtain node embeddings 
        x = self.conv1(x, edge_index)
        x = x.relu()
        x = self.conv2(x, edge_index)
        x = x.relu()
        x = self.conv3(x, edge_index)

        # 2. Readout layer
        x = global_mean_pool(x, batch)  # [batch_size, hidden_channels]

        # 3. Apply a final classifier
        x = F.dropout(x, p=0.5, training=self.training)
        x = self.lin(x)
        
        return x

class GINModel(torch.nn.Module):
    """
    Graph Isomorphism Network (GIN) model for predicting protein melting temperature.
    
    Uses 2 layers of GINConv with MLPs, batch normalization, global add pooling, 
    and a 2-layer MLP readout.
    """
    def __init__(self, num_node_features: int, hidden_dim: int = 64):
        super(GINModel, self).__init__()
        
        nn1 = Sequential(
            Linear(num_node_features, hidden_dim), BatchNorm1d(hidden_dim), ReLU(),
            Linear(hidden_dim, hidden_dim), ReLU()
        )
        self.conv1 = GINConv(nn1)
        self.bn1 = BatchNorm1d(hidden_dim)

        nn2 = Sequential(
            Linear(hidden_dim, hidden_dim), BatchNorm1d(hidden_dim), ReLU(),
            Linear(hidden_dim, hidden_dim), ReLU()
        )
        self.conv2 = GINConv(nn2)
        self.bn2 = BatchNorm1d(hidden_dim)
        
        self.lin1 = Linear(hidden_dim, hidden_dim)
        self.lin2 = Linear(hidden_dim, 1)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, batch: torch.Tensor) -> torch.Tensor:
        """
        Forward pass for the GINModel.
        
        Args:
            x (torch.Tensor): Node feature matrix of shape [num_nodes, num_node_features].
            edge_index (torch.Tensor): Graph edge indices of shape [2, num_edges].
            batch (torch.Tensor): Batch vector assigning each node to a specific graph.
            
        Returns:
            torch.Tensor: Predicted values of shape [batch_size, 1].
        """
        x = self.conv1(x, edge_index)
        x = self.bn1(x)
        x = self.conv2(x, edge_index)
        x = self.bn2(x)

        x = global_add_pool(x, batch)
        
        x = self.lin1(x).relu()
        x = F.dropout(x, p=0.5, training=self.training)
        x = self.lin2(x)
        return x
