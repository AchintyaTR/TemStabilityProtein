import torch
import torch.nn.functional as F
from torch.nn import Linear, Sequential, BatchNorm1d, ReLU
from torch_geometric.nn import GCNConv, GINConv, global_add_pool, global_mean_pool

class GNNModel(torch.nn.Module):
    def __init__(self, num_node_features=320, hidden_dim=64):
        super(GNNModel, self).__init__()
        self.conv1 = GCNConv(num_node_features, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, hidden_dim)
        self.conv3 = GCNConv(hidden_dim, hidden_dim)
        self.lin = Linear(hidden_dim, 1)

    def forward(self, x, edge_index, batch):
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
    def __init__(self, num_node_features, hidden_dim=64):
        super(GINModel, self).__init__()
        
        nn1 = Sequential(Linear(num_node_features, hidden_dim), BatchNorm1d(hidden_dim), ReLU(),
                         Linear(hidden_dim, hidden_dim), ReLU())
        self.conv1 = GINConv(nn1)
        self.bn1 = BatchNorm1d(hidden_dim)

        nn2 = Sequential(Linear(hidden_dim, hidden_dim), BatchNorm1d(hidden_dim), ReLU(),
                         Linear(hidden_dim, hidden_dim), ReLU())
        self.conv2 = GINConv(nn2)
        self.bn2 = BatchNorm1d(hidden_dim)
        
        self.lin1 = Linear(hidden_dim, hidden_dim)
        self.lin2 = Linear(hidden_dim, 1)

    def forward(self, x, edge_index, batch):
        x = self.conv1(x, edge_index)
        x = self.bn1(x)
        x = self.conv2(x, edge_index)
        x = self.bn2(x)

        x = global_add_pool(x, batch)
        
        x = self.lin1(x).relu()
        x = F.dropout(x, p=0.5, training=self.training)
        x = self.lin2(x)
        return x
