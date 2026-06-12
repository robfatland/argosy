# Module 5: Spectral Analysis of Similarity Graph
# Run this as: %run /home/rob/argosy/sga/sga_module5.py

import numpy as np
import pandas as pd
import networkx as nx
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh
import matplotlib.pyplot as plt
import pickle
from pathlib import Path

# Output directory
SGA_DIR = Path('~/ooi/analysis/sga').expanduser()

# Load config
with open(SGA_DIR / 'sga_config.pkl', 'rb') as f:
    config = pickle.load(f)

laplacian_type = config['laplacian_type']
n_eigenvalues_requested = config['n_eigenvalues']

# Load graph
print("Module 5: Spectral Analysis")
with open(SGA_DIR / 'similarity_graph.pkl', 'rb') as f:
    G = pickle.load(f)
profile_index = pd.read_csv(SGA_DIR / 'profile_index_clean.csv')
profile_index['date'] = pd.to_datetime(profile_index['date'])

print(f"  Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

# Compute graph Laplacian
if laplacian_type == "1":
    L = nx.laplacian_matrix(G).astype(float)
    laplacian_name = "Unnormalized"
elif laplacian_type == "2":
    A = nx.adjacency_matrix(G).astype(float)
    d = np.array(A.sum(axis=1)).flatten()
    d_inv_sqrt = np.zeros_like(d)
    nonzero = d > 0
    d_inv_sqrt[nonzero] = 1.0 / np.sqrt(d[nonzero])
    D_inv_sqrt = sp.diags(d_inv_sqrt)
    L = sp.eye(A.shape[0]) - D_inv_sqrt @ A @ D_inv_sqrt
    laplacian_name = "Symmetric Normalized"
elif laplacian_type == "3":
    A = nx.adjacency_matrix(G).astype(float)
    D = np.array(A.sum(axis=1)).flatten()
    D_inv = np.diag(1.0 / D)
    L = np.eye(len(D)) - D_inv @ A.toarray()
    laplacian_name = "Random Walk"

print(f"  Laplacian: {laplacian_name}, shape {L.shape}")

# Compute eigenvalues
n_eigenvalues = min(n_eigenvalues_requested, G.number_of_nodes() - 2)
print(f"  Computing {n_eigenvalues} smallest eigenvalues...")

if laplacian_type in ["1", "2"]:
    eigenvalues, eigenvectors = eigsh(L, k=n_eigenvalues, which='SM')
else:
    eigenvalues, eigenvectors = np.linalg.eigh(L)
    eigenvalues = eigenvalues[:n_eigenvalues]
    eigenvectors = eigenvectors[:, :n_eigenvalues]

sort_idx = np.argsort(eigenvalues)
eigenvalues = eigenvalues[sort_idx]
eigenvectors = eigenvectors[:, sort_idx]

# Spectral properties
fiedler_value = eigenvalues[1]
spectral_gap = eigenvalues[2] - eigenvalues[1]
cumulative_energy = np.cumsum(eigenvalues) / np.sum(eigenvalues)
effective_dim = np.searchsorted(cumulative_energy, 0.9) + 1

print(f"\n  Eigenvalue range: [{eigenvalues[0]:.6f}, {eigenvalues[-1]:.6f}]")
print(f"  Fiedler value (lambda_2): {fiedler_value:.6f}")
print(f"  Spectral gap (lambda_3 - lambda_2): {spectral_gap:.6f}")
print(f"  Effective dimensionality (90%): {effective_dim}")

# Plots
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].plot(range(len(eigenvalues)), eigenvalues, 'o-', markersize=4)
axes[0].axhline(y=fiedler_value, color='r', linestyle='--', label=f'Fiedler: {fiedler_value:.4f}')
axes[0].set_xlabel('Index')
axes[0].set_ylabel('Eigenvalue')
axes[0].set_title('Eigenspectrum')
axes[0].grid(True, alpha=0.3)
axes[0].legend()

n_plot = min(20, len(eigenvalues))
axes[1].plot(range(n_plot), eigenvalues[:n_plot], 'o-', markersize=6)
axes[1].set_xlabel('Index')
axes[1].set_ylabel('Eigenvalue')
axes[1].set_title('First 20 Eigenvalues')
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(SGA_DIR / 'eigenspectrum.png', dpi=150, bbox_inches='tight')
plt.show()

# Fiedler vector
fiedler_vector = eigenvectors[:, 1]
fig, axes = plt.subplots(2, 1, figsize=(12, 8))
axes[0].plot(profile_index['date'], fiedler_vector, '-', linewidth=0.5)
axes[0].axhline(y=0, color='r', linestyle='--', alpha=0.5)
axes[0].set_xlabel('Date')
axes[0].set_ylabel('Fiedler Vector')
axes[0].set_title('Fiedler Vector - Temporal Evolution')
axes[0].grid(True, alpha=0.3)

axes[1].hist(fiedler_vector, bins=50, edgecolor='black', alpha=0.7)
axes[1].axvline(x=0, color='r', linestyle='--', linewidth=2)
axes[1].set_xlabel('Fiedler Vector Value')
axes[1].set_ylabel('Count')
axes[1].set_title('Fiedler Vector Distribution')
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(SGA_DIR / 'fiedler_vector.png', dpi=150, bbox_inches='tight')
plt.show()

# Save
np.save(SGA_DIR / 'eigenvalues.npy', eigenvalues)
np.save(SGA_DIR / 'eigenvectors.npy', eigenvectors)

spectral_properties = {
    'laplacian_type': laplacian_name,
    'n_eigenvalues': len(eigenvalues),
    'fiedler_value': fiedler_value,
    'spectral_gap': spectral_gap,
    'effective_dimensionality': effective_dim,
    'eigenvalue_range': (eigenvalues[0], eigenvalues[-1])
}
with open(SGA_DIR / 'spectral_properties.pkl', 'wb') as f:
    pickle.dump(spectral_properties, f)

print(f"\n=== Module 5 Complete ===")
