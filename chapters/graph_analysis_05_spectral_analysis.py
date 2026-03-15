# Module 5: Spectral Analysis of Similarity Graph
# Computes eigenvalues and eigenvectors of graph Laplacian

import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from scipy.sparse.linalg import eigsh
import pickle

# Load graph
print("Loading similarity graph...")
with open('similarity_graph.pkl', 'rb') as f:
    G = pickle.load(f)
profile_index = pd.read_csv('profile_index_clean.csv')
profile_index['date'] = pd.to_datetime(profile_index['date'])

with open('graph_metadata.pkl', 'rb') as f:
    metadata = pickle.load(f)

print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

# Compute graph Laplacian
print("\n=== Computing Graph Laplacian ===")
print("Laplacian type:")
print("  1. Unnormalized: L = D - A")
print("  2. Symmetric normalized: L_sym = I - D^(-1/2) A D^(-1/2)")
print("  3. Random walk: L_rw = I - D^(-1) A")

laplacian_type = input("Select Laplacian (1/2/3, default 2): ").strip() or "2"

if laplacian_type == "1":
    L = nx.laplacian_matrix(G).astype(float)
    laplacian_name = "Unnormalized"
elif laplacian_type == "2":
    L = nx.normalized_laplacian_matrix(G).astype(float)
    laplacian_name = "Symmetric Normalized"
elif laplacian_type == "3":
    # Random walk Laplacian
    A = nx.adjacency_matrix(G).astype(float)
    D = np.array(A.sum(axis=1)).flatten()
    D_inv = np.diag(1.0 / D)
    L = np.eye(len(D)) - D_inv @ A.toarray()
    laplacian_name = "Random Walk"

print(f"Using {laplacian_name} Laplacian")
print(f"Laplacian shape: {L.shape}")

# Compute eigenvalues and eigenvectors
print("\n=== Computing Eigenspectrum ===")
n_eigenvalues = min(50, G.number_of_nodes() - 2)
print(f"Computing {n_eigenvalues} smallest eigenvalues...")

if laplacian_type in ["1", "2"]:
    # Use sparse eigensolver
    eigenvalues, eigenvectors = eigsh(L, k=n_eigenvalues, which='SM')
else:
    # Dense computation for random walk
    eigenvalues, eigenvectors = np.linalg.eigh(L)
    eigenvalues = eigenvalues[:n_eigenvalues]
    eigenvectors = eigenvectors[:, :n_eigenvalues]

# Sort by eigenvalue
sort_idx = np.argsort(eigenvalues)
eigenvalues = eigenvalues[sort_idx]
eigenvectors = eigenvectors[:, sort_idx]

print(f"\nEigenvalue range: [{eigenvalues[0]:.6f}, {eigenvalues[-1]:.6f}]")

# Key spectral properties
print("\n=== Spectral Properties ===")

# Algebraic connectivity (Fiedler value)
fiedler_value = eigenvalues[1]
print(f"Algebraic connectivity (λ₂): {fiedler_value:.6f}")
print("  Interpretation: Measures graph connectivity")
print("  Higher values → better connected (well-mixed water column)")

# Spectral gap
spectral_gap = eigenvalues[2] - eigenvalues[1]
print(f"\nSpectral gap (λ₃ - λ₂): {spectral_gap:.6f}")
print("  Interpretation: Indicates cluster structure")
print("  Large gap → distinct regimes exist")

# Effective dimensionality (90% of spectral energy)
cumulative_energy = np.cumsum(eigenvalues) / np.sum(eigenvalues)
effective_dim = np.searchsorted(cumulative_energy, 0.9) + 1
print(f"\nEffective dimensionality (90% energy): {effective_dim}")
print("  Interpretation: Number of fundamental modes")

# Plot eigenvalue spectrum
fig, axes = plt.subplots(1, 2, figsize=(12, 4))

# Full spectrum
axes[0].plot(range(len(eigenvalues)), eigenvalues, 'o-', markersize=4)
axes[0].axhline(y=fiedler_value, color='r', linestyle='--', label=f'Fiedler value: {fiedler_value:.4f}')
axes[0].set_xlabel('Index')
axes[0].set_ylabel('Eigenvalue')
axes[0].set_title('Graph Laplacian Eigenspectrum')
axes[0].grid(True, alpha=0.3)
axes[0].legend()

# First 20 eigenvalues (zoomed)
n_plot = min(20, len(eigenvalues))
axes[1].plot(range(n_plot), eigenvalues[:n_plot], 'o-', markersize=6)
axes[1].axhline(y=fiedler_value, color='r', linestyle='--', label=f'λ₂ (Fiedler)')
axes[1].axvline(x=1, color='r', linestyle='--', alpha=0.5)
axes[1].set_xlabel('Index')
axes[1].set_ylabel('Eigenvalue')
axes[1].set_title('First 20 Eigenvalues')
axes[1].grid(True, alpha=0.3)
axes[1].legend()

plt.tight_layout()
plt.savefig('eigenspectrum.png', dpi=150, bbox_inches='tight')
plt.show()

print("\nEigenspectrum plot saved to eigenspectrum.png")

# Plot Fiedler vector (2nd eigenvector)
fiedler_vector = eigenvectors[:, 1]

fig, axes = plt.subplots(2, 1, figsize=(12, 8))

# Fiedler vector vs time
axes[0].plot(profile_index['date'], fiedler_vector, '-', linewidth=0.5)
axes[0].axhline(y=0, color='r', linestyle='--', alpha=0.5)
axes[0].set_xlabel('Date')
axes[0].set_ylabel('Fiedler Vector Value')
axes[0].set_title('Fiedler Vector (2nd Eigenvector) - Temporal Evolution')
axes[0].grid(True, alpha=0.3)

# Histogram of Fiedler vector
axes[1].hist(fiedler_vector, bins=50, edgecolor='black', alpha=0.7)
axes[1].axvline(x=0, color='r', linestyle='--', linewidth=2, label='Zero crossing')
axes[1].set_xlabel('Fiedler Vector Value')
axes[1].set_ylabel('Count')
axes[1].set_title('Fiedler Vector Distribution')
axes[1].grid(True, alpha=0.3)
axes[1].legend()

plt.tight_layout()
plt.savefig('fiedler_vector.png', dpi=150, bbox_inches='tight')
plt.show()

print("Fiedler vector plot saved to fiedler_vector.png")

# Save spectral data
print("\nSaving spectral analysis results...")
np.save('eigenvalues.npy', eigenvalues)
np.save('eigenvectors.npy', eigenvectors)

spectral_properties = {
    'laplacian_type': laplacian_name,
    'n_eigenvalues': len(eigenvalues),
    'fiedler_value': fiedler_value,
    'spectral_gap': spectral_gap,
    'effective_dimensionality': effective_dim,
    'eigenvalue_range': (eigenvalues[0], eigenvalues[-1])
}

with open('spectral_properties.pkl', 'wb') as f:
    pickle.dump(spectral_properties, f)

print("\nSaved:")
print("  - eigenvalues.npy")
print("  - eigenvectors.npy")
print("  - spectral_properties.pkl")
print("  - eigenspectrum.png")
print("  - fiedler_vector.png")

print("\n=== Analysis Complete ===")
print(f"The Fiedler vector reveals natural partitioning of water column states.")
print(f"Profiles with similar Fiedler values are dynamically similar.")
