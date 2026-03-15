# Module 4: Build Depth-Time Similarity Graph
# Constructs weighted graph based on profile similarity

import numpy as np
import pandas as pd
import networkx as nx
from scipy.spatial.distance import pdist, squareform
from scipy.sparse import csr_matrix
import pickle

# Load normalized data
print("Loading normalized feature matrix...")
feature_matrix = np.load('feature_matrix_normalized.npy')
profile_index = pd.read_csv('profile_index_clean.csv')
profile_index['date'] = pd.to_datetime(profile_index['date'])

n_profiles = feature_matrix.shape[0]
print(f"Profiles: {n_profiles}")

# Compute pairwise squared distances (skip sqrt - only d^2 is needed for Gaussian kernel)
print("\n=== Computing Pairwise Squared Distances ===")
print("This may take a few minutes for large datasets...")

sq_distances = pdist(feature_matrix, metric='sqeuclidean')
sq_distance_matrix = squareform(sq_distances)

print(f"Squared distance matrix shape: {sq_distance_matrix.shape}")
print(f"Squared distance range: [{sq_distance_matrix[sq_distance_matrix > 0].min():.2f}, {sq_distance_matrix.max():.2f}]")

# Convert squared distances to similarities using Gaussian kernel
# w_ij = exp(-d_ij^2 / (2 * sigma^2))  where sigma^2 = median squared distance
print("\n=== Converting to Similarities ===")

# Adaptive sigma^2: use median squared distance
# (equivalent to sigma = sqrt(median_distance), but computed directly without sqrt)
median_sq_distance = np.median(sq_distance_matrix[sq_distance_matrix > 0])
print(f"Median squared distance: {median_sq_distance:.2f}")
print(f"Equivalent sigma: {np.sqrt(median_sq_distance):.2f}")

# Sigma^2 options
print("\nSigma² (kernel width) options:")
print(f"  1. Median sq. distance: {median_sq_distance:.2f}")
print(f"  2. 0.25 × median (narrower): {0.25 * median_sq_distance:.2f}")
print(f"  3. 4.0 × median (wider): {4.0 * median_sq_distance:.2f}")
print("  4. Custom sigma value (will be squared)")

sigma_choice = input("Select sigma (1/2/3/4, default 1): ").strip() or "1"

if sigma_choice == "1":
    sigma_sq = median_sq_distance
elif sigma_choice == "2":
    sigma_sq = 0.25 * median_sq_distance
elif sigma_choice == "3":
    sigma_sq = 4.0 * median_sq_distance
elif sigma_choice == "4":
    sigma = float(input("Enter custom sigma value: "))
    sigma_sq = sigma ** 2

sigma = np.sqrt(sigma_sq)
print(f"\nUsing sigma = {sigma:.2f} (sigma² = {sigma_sq:.2f})")

# Gaussian kernel: w_ij = exp(-d_ij^2 / (2 * sigma^2))
similarity_matrix = np.exp(-sq_distance_matrix / (2 * sigma_sq))

# Set diagonal to 0 (no self-loops)
np.fill_diagonal(similarity_matrix, 0)

print(f"Similarity range: [{similarity_matrix[similarity_matrix > 0].min():.6f}, {similarity_matrix.max():.6f}]")

# Graph construction strategy
print("\n=== Graph Construction Strategy ===")
print("Options:")
print("  1. k-Nearest Neighbors (sparse, k edges per node)")
print("  2. Epsilon-ball (edges for similarity > threshold)")
print("  3. Full graph (all edges, may be large)")

graph_type = input("Select strategy (1/2/3, default 1): ").strip() or "1"

if graph_type == "1":
    # k-NN graph
    k = int(input("Enter k (default 10): ").strip() or "10")
    print(f"\nBuilding {k}-NN graph...")
    
    # For each node, keep only k nearest neighbors
    adjacency = np.zeros_like(similarity_matrix)
    for i in range(n_profiles):
        # Get k largest similarities (excluding self)
        top_k_indices = np.argsort(similarity_matrix[i])[-k:]
        adjacency[i, top_k_indices] = similarity_matrix[i, top_k_indices]
    
    # Make symmetric (if i->j, then j->i)
    adjacency = np.maximum(adjacency, adjacency.T)
    
    n_edges = np.sum(adjacency > 0) // 2
    print(f"Edges: {n_edges}")
    
elif graph_type == "2":
    # Epsilon-ball graph
    epsilon = float(input("Enter similarity threshold (0-1, default 0.1): ").strip() or "0.1")
    print(f"\nBuilding epsilon-ball graph (threshold={epsilon})...")
    
    adjacency = similarity_matrix.copy()
    adjacency[adjacency < epsilon] = 0
    
    n_edges = np.sum(adjacency > 0) // 2
    print(f"Edges: {n_edges}")
    
elif graph_type == "3":
    # Full graph
    print("\nBuilding full graph...")
    adjacency = similarity_matrix.copy()
    n_edges = np.sum(adjacency > 0) // 2
    print(f"Edges: {n_edges}")

# Create NetworkX graph
print("\nCreating NetworkX graph...")
G = nx.from_numpy_array(adjacency)

# Add node attributes
for i, row in profile_index.iterrows():
    G.nodes[i]['date'] = row['date']
    G.nodes[i]['year'] = row['year']
    G.nodes[i]['doy'] = row['doy']
    G.nodes[i]['profile_idx'] = row['profile_idx']

print(f"\nGraph statistics:")
print(f"  Nodes: {G.number_of_nodes()}")
print(f"  Edges: {G.number_of_edges()}")
print(f"  Density: {nx.density(G):.6f}")
print(f"  Connected: {nx.is_connected(G)}")

if not nx.is_connected(G):
    components = list(nx.connected_components(G))
    print(f"  Connected components: {len(components)}")
    print(f"  Largest component size: {len(max(components, key=len))}")

# Save graph and matrices
print("\nSaving graph and matrices...")
with open('similarity_graph.pkl', 'wb') as f:
    pickle.dump(G, f)
np.save('similarity_matrix.npy', similarity_matrix)
np.save('adjacency_matrix.npy', adjacency)

# Save metadata
metadata = {
    'n_profiles': n_profiles,
    'sigma': sigma,
    'sigma_sq': sigma_sq,
    'graph_type': graph_type,
    'n_edges': n_edges,
    'date_range': (profile_index['date'].min(), profile_index['date'].max())
}

with open('graph_metadata.pkl', 'wb') as f:
    pickle.dump(metadata, f)

print("\nSaved:")
print("  - similarity_graph.pkl")
print("  - similarity_matrix.npy")
print("  - adjacency_matrix.npy")
print("  - graph_metadata.pkl")
