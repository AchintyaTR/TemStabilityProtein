# Structure-Guided Graph Neural Network for Predicting Protein Melting Temperature

A deep learning approach that combines **ESM-2 protein language model embeddings** with **3D structural graphs from AlphaFold** to predict protein melting temperatures (Tm) using Graph Neural Networks (GCN and GIN).

## Overview

Protein thermal stability is crucial for industrial and pharmaceutical applications. This project builds a GNN-based regression model that leverages:

- **ESM-2 embeddings** — per-residue representations from Meta's protein language model
- **AlphaFold predicted structures** — 3D coordinates used to construct contact graphs (Cα distance < 8Å)
- **GCN / GIN architectures** — Graph Convolutional and Graph Isomorphism Networks for Tm regression

## Project Structure

```
├── .github/                # CI/CD pipelines
├── docs/                   # Reports and presentations
├── scripts/                # Executable entry points
│   ├── create_database.py
│   ├── prepare_datasets.py
│   ├── download_pdb.py
│   ├── train.py            # Training pipeline with argparse support
│   └── evaluate.py         # Model evaluation and visualization
├── src/                    # Source code package
│   ├── data/               # Data processing (gnn_data.py)
│   └── models/             # Neural network architectures (gnn_model.py)
├── tests/                  # Unit tests (pytest)
├── requirements.txt        # Core Python dependencies
├── requirements-dev.txt    # Development dependencies (pytest, black, etc.)
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
pip install -r requirements-dev.txt  # Optional: for development and testing
```

### Dataset

The model is trained on the **TemStaPro** dataset (Major-30 set). Due to its large size (~314MB), the raw FASTA file is excluded from this repository.

### Download Instructions

1.  Download the dataset from **Zenodo**: [https://doi.org/10.5281/zenodo.7743637](https://doi.org/10.5281/zenodo.7743637)
2.  Extract the `TemStaPro-Major-30-imbal-training.fasta` file.
3.  Place it in a folder named `Dataset` as a sibling to the project directory:

```
├── Dataset/
│   └── TemStaPro-Major-30-imbal-training.fasta
└── TemStabilityProtein/  (This repo)
    ├── scripts/
    │   ├── create_database.py
    │   └── ...
    └── ...
```

### Citation

If you use this dataset, please cite:
> Pudžiuvelytė, I., et al. "TemStaPro: protein thermostability prediction using deep learning." Bioinformatics (2023).

## Usage

Run the pipeline in order from the project root:

```bash
# 1. Parse FASTA → CSV database
python scripts/create_database.py

# 2. Split into train/test sets
python scripts/prepare_datasets.py

# 3. Download AlphaFold PDB structures
python scripts/download_pdb.py

# 4. Train the GNN model (configurable via argparse)
python scripts/train.py --batch_size 32 --epochs 50 --lr 0.001

# 5. Evaluate the trained model
python scripts/evaluate.py --model_path gin_model_best.pth
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
