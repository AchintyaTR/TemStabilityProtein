# Structure-Guided Graph Neural Network for Predicting Protein Melting Temperature

A deep learning approach that combines **ESM-2 protein language model embeddings** with **3D structural graphs from AlphaFold** to predict protein melting temperatures (Tm) using Graph Neural Networks (GCN and GIN).

## Overview

Protein thermal stability is crucial for industrial and pharmaceutical applications. This project builds a GNN-based regression model that leverages:

- **ESM-2 embeddings** — per-residue representations from Meta's protein language model
- **AlphaFold predicted structures** — 3D coordinates used to construct contact graphs (Cα distance < 8Å)
- **GCN / GIN architectures** — Graph Convolutional and Graph Isomorphism Networks for Tm regression

## Project Structure

```
├── create_database.py      # Parse FASTA dataset → protein_data.csv
├── prepare_datasets.py     # Train/test split (80/20)
├── download_pdb.py         # Download AlphaFold PDB structures
├── gnn_data.py             # PyG Dataset: graph construction + ESM-2 features
├── gnn_model.py            # GCN and GIN model architectures
├── train_gnn.py            # Training pipeline with evaluation
├── evaluate_model.py       # Model evaluation and visualization
├── requirements.txt        # Python dependencies
└── README.md
```

## Setup

### Prerequisites

- Python 3.9+
- CUDA-compatible GPU (recommended)

### Installation

```bash
git clone https://github.com/AchintyaTR/TemStabilityProtein.git
cd TemStabilityProtein
pip install -r requirements.txt
```

### Dataset

This project uses the **TemStaPro** dataset. Place the FASTA file at:
```
../Dataset/TemStaPro-Major-30-imbal-training.fasta
```

## Usage

Run the pipeline in order:

```bash
# 1. Parse FASTA → CSV database
python create_database.py

# 2. Split into train/test sets
python prepare_datasets.py

# 3. Download AlphaFold PDB structures
python download_pdb.py

# 4. Train the GNN model
python train_gnn.py

# 5. Evaluate the trained model
python evaluate_model.py
```

## Model Architecture

### GCN Model
- 3-layer Graph Convolutional Network
- Global mean pooling → fully connected regression head

### GIN Model
- 3-layer Graph Isomorphism Network with MLP message passing
- Batch normalization + global add pooling
- Dropout regularization

Both models take **1280-dimensional ESM-2 embeddings** as node features and predict a scalar Tm value.

## Results

| Model | R² | MAE (°C) | RMSE (°C) | Pearson r |
|-------|-----|----------|-----------|-----------|
| GCN   | 0.57 | 8.12    | 10.87     | 0.76      |
| GIN   | 0.62 | 7.45    | 10.21     | 0.79      |

## Tech Stack

- **PyTorch** + **PyTorch Geometric** — GNN framework
- **ESM-2** (Meta AI) — protein language model
- **BioPandas** — PDB file parsing
- **scikit-learn** — evaluation metrics
