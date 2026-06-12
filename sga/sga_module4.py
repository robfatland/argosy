# Module 4: Build Depth-Time Similarity Graph
# Run this as: %run /home/rob/argosy/sga/sga_module4.py

import numpy as np
import pandas as pd
import networkx as nx
from scipy.spatial.distance import pdist, squareform
import pickle
from pathlib import Path

# Output directory
SGA_DIR = Path('~/ooi/analysis/sga').expanduser()

# Load config
with open(SGA_DIR / 'sga_config.pkl', 'rb') as f:
    config = pickle.load(f)

sigma_choice = config['sigma_choice']
graph_type = config['graph_type']
knn_k = config['knn_k']
epsilon_threshold = config['epsilon_threshold']

# Load normalized data
print("Module 4: Similarity Graph")
feature_matrix = np.load(SGA_DIR / 'feature_matrix_normalized.npy')
profile_index = pd.read_csv(SGA_DIR / 'profile_index_clean.csv')
profile_index['date'] = pd.to_datetime(profile_index['date'])

n_profiles = feature_matrix.shape[0]
print(f"  Profiles: {n_profiles}")

# Pairwise squared distances
print("  Computing pairwise squared distances...")
sq_distances = pdist(feature_matrix, metric='sqeuclidean')
sq_distance_matrix = squareform(sq_distances)
print(f"  Distance range: [{sq_distance_matrix[sq_distance_matrix > 0].min():.2f}, {sq_distance_matrix.max():.2f}]")

# Sigma selection
median_sq_distance = np.median(sq_distance_matrix[sq_distance_matrix > 0])

if sigma_choice == 'median':
    sigma_sq = median_sq_distance
elif sigma_choice == '0.25x':
    sigma_sq = 0.25 * median_sq_distance
elif sigma_choice == '4x':
    sigma_sq = 4.0 * median_sq_distance
else:
    sigma_sq = float(sigma_choice) ** 2

sigma = np.sqrt(sigma_sq)
print(f"  Sigma: {sigma:.2f} (sigma^2={sigma_sq:.2f}, median_sq={median_sq_distance:.2f})")

# Gaussian kernel
similarity_matrix = np.exp(-sq_distance_matrix / (2 * sigma_sq))
np.fill_diagonal(similarity_matrix, 0)
print(f"  Similarity range: [{similarity_matrix[similarity_matrix > 0].min():.6f}, {similarity_matrix.max():.6f}]")

# Graph construction
if graph_type == 'knn':
    print(f"  Building {knn_k}-NN graph...")
    adjacency = np.zeros_like(similarity_matrix)
    for i in range(n_profiles):
        top_k_indices = np.argsort(similarity_matrix[i])[-knn_k:]
        adjacency[i, top_k_indices] = similarity_matrix[i, top_k_indices]
    adjacency = np.maximum(adjacency, adjacency.T)

elif graph_type == 'epsilon':
    print(f"  Building epsilon-ball graph (threshold={epsilon_threshold})...")
    adjacency = similarity_matrix.copy()
    adjacency[adjacency < epsilon_threshold] = 0

elif graph_type == 'full':
    print("  Building full graph...")
    adjacency = similarity_matrix.copy()

n_edges = np.sum(adjacency > 0) // 2
print(f"  Edges: {n_edges}")

# Create NetworkX graph
print("  Creating NetworkX graph...")
G = nx.from_numpy_array(adjacency)

for i, row in profile_index.iterrows():
    G.nodes[i]['date'] = row['date']
    G.nodes[i]['year'] = row['year']
    G.nodes[i]['doy'] = row['doy']
    G.nodes[i]['global_idx'] = row['global_idx']

print(f"  Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
print(f"  Connected: {nx.is_connected(G)}")

if not nx.is_connected(G):
    components = list(nx.connected_components(G))
    print(f"  Components: {len(components)}, largest: {len(max(components, key=len))}")

# Save
with open(SGA_DIR / 'similarity_graph.pkl', 'wb') as f:
    pickle.dump(G, f)
np.save(SGA_DIR / 'similarity_matrix.npy', similarity_matrix)
np.save(SGA_DIR / 'adjacency_matrix.npy', adjacency)

metadata = {
    'n_profiles': n_profiles,
    'sigma': sigma,
    'sigma_sq': sigma_sq,
    'graph_type': graph_type,
    'n_edges': n_edges,
    'date_range': (profile_index['date'].min(), profile_index['date'].max())
}
with open(SGA_DIR / 'graph_metadata.pkl', 'wb') as f:
    pickle.dump(metadata, f)

print(f"\n=== Module 4 Complete ===")
