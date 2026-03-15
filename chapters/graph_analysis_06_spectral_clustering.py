# Module 6: Spectral Clustering
# Identifies water column regimes using spectral methods

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score
import pickle

# Load spectral data
print("Loading spectral analysis results...")
eigenvalues = np.load('eigenvalues.npy')
eigenvectors = np.load('eigenvectors.npy')
profile_index = pd.read_csv('profile_index_clean.csv')
profile_index['date'] = pd.to_datetime(profile_index['date'])

with open('spectral_properties.pkl', 'rb') as f:
    spectral_props = pickle.load(f)

print(f"Profiles: {len(profile_index)}")
print(f"Eigenvalues: {len(eigenvalues)}")

# Determine optimal number of clusters
print("\n=== Determining Optimal Number of Clusters ===")

# Use first k eigenvectors for clustering
n_eigenvectors = int(input("Number of eigenvectors to use (default 10): ").strip() or "10")
n_eigenvectors = min(n_eigenvectors, eigenvectors.shape[1])

embedding = eigenvectors[:, :n_eigenvectors]
print(f"Using first {n_eigenvectors} eigenvectors")

# Test different numbers of clusters
k_range = range(2, 11)
silhouette_scores = []
davies_bouldin_scores = []
inertias = []

print("\nEvaluating cluster quality...")
for k in k_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(embedding)
    
    silhouette = silhouette_score(embedding, labels)
    davies_bouldin = davies_bouldin_score(embedding, labels)
    
    silhouette_scores.append(silhouette)
    davies_bouldin_scores.append(davies_bouldin)
    inertias.append(kmeans.inertia_)
    
    print(f"  k={k}: Silhouette={silhouette:.3f}, Davies-Bouldin={davies_bouldin:.3f}")

# Plot cluster quality metrics
fig, axes = plt.subplots(1, 3, figsize=(15, 4))

axes[0].plot(k_range, silhouette_scores, 'o-', markersize=6)
axes[0].set_xlabel('Number of Clusters')
axes[0].set_ylabel('Silhouette Score')
axes[0].set_title('Silhouette Score (higher is better)')
axes[0].grid(True, alpha=0.3)

axes[1].plot(k_range, davies_bouldin_scores, 'o-', markersize=6)
axes[1].set_xlabel('Number of Clusters')
axes[1].set_ylabel('Davies-Bouldin Index')
axes[1].set_title('Davies-Bouldin Index (lower is better)')
axes[1].grid(True, alpha=0.3)

axes[2].plot(k_range, inertias, 'o-', markersize=6)
axes[2].set_xlabel('Number of Clusters')
axes[2].set_ylabel('Inertia')
axes[2].set_title('Elbow Plot')
axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('cluster_quality.png', dpi=150, bbox_inches='tight')
plt.show()

print("\nCluster quality plot saved to cluster_quality.png")

# Select number of clusters
best_k_silhouette = k_range[np.argmax(silhouette_scores)]
print(f"\nRecommended k (max silhouette): {best_k_silhouette}")

n_clusters = int(input(f"Select number of clusters (default {best_k_silhouette}): ").strip() or str(best_k_silhouette))

# Perform final clustering
print(f"\n=== Spectral Clustering with k={n_clusters} ===")
kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=20)
cluster_labels = kmeans.fit_predict(embedding)

# Add cluster labels to profile index
profile_index['cluster'] = cluster_labels

# Cluster statistics
print("\nCluster sizes:")
for i in range(n_clusters):
    count = np.sum(cluster_labels == i)
    pct = count / len(cluster_labels) * 100
    print(f"  Cluster {i}: {count} profiles ({pct:.1f}%)")

# Temporal distribution of clusters
fig, axes = plt.subplots(2, 1, figsize=(14, 8))

# Timeline colored by cluster
for i in range(n_clusters):
    mask = cluster_labels == i
    axes[0].scatter(profile_index.loc[mask, 'date'], 
                   np.ones(np.sum(mask)) * i,
                   s=10, alpha=0.6, label=f'Cluster {i}')

axes[0].set_xlabel('Date')
axes[0].set_ylabel('Cluster')
axes[0].set_title('Temporal Distribution of Water Column Regimes')
axes[0].set_yticks(range(n_clusters))
axes[0].legend(loc='upper right', ncol=n_clusters)
axes[0].grid(True, alpha=0.3)

# Monthly distribution
profile_index['month'] = profile_index['date'].dt.month
monthly_counts = profile_index.groupby(['month', 'cluster']).size().unstack(fill_value=0)

monthly_counts.plot(kind='bar', stacked=True, ax=axes[1], width=0.8)
axes[1].set_xlabel('Month')
axes[1].set_ylabel('Number of Profiles')
axes[1].set_title('Seasonal Distribution of Clusters')
month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
axes[1].set_xticklabels([month_names[m-1] for m in monthly_counts.index], rotation=0)
axes[1].legend(title='Cluster', loc='upper right')
axes[1].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('cluster_temporal.png', dpi=150, bbox_inches='tight')
plt.show()

print("\nCluster temporal distribution saved to cluster_temporal.png")

# Embedding visualization (first 2 eigenvectors)
fig, ax = plt.subplots(figsize=(10, 8))

for i in range(n_clusters):
    mask = cluster_labels == i
    ax.scatter(eigenvectors[mask, 1], eigenvectors[mask, 2], 
              s=20, alpha=0.6, label=f'Cluster {i}')

ax.set_xlabel('2nd Eigenvector (Fiedler)')
ax.set_ylabel('3rd Eigenvector')
ax.set_title('Spectral Embedding (First 2 Non-trivial Eigenvectors)')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('spectral_embedding.png', dpi=150, bbox_inches='tight')
plt.show()

print("Spectral embedding plot saved to spectral_embedding.png")

# Save clustering results
print("\nSaving clustering results...")
profile_index.to_csv('profile_index_clustered.csv', index=False)
np.save('cluster_labels.npy', cluster_labels)

clustering_results = {
    'n_clusters': n_clusters,
    'n_eigenvectors': n_eigenvectors,
    'silhouette_score': silhouette_score(embedding, cluster_labels),
    'davies_bouldin_score': davies_bouldin_score(embedding, cluster_labels),
    'cluster_sizes': [np.sum(cluster_labels == i) for i in range(n_clusters)]
}

with open('clustering_results.pkl', 'wb') as f:
    pickle.dump(clustering_results, f)

print("\nSaved:")
print("  - profile_index_clustered.csv")
print("  - cluster_labels.npy")
print("  - clustering_results.pkl")
print("  - cluster_quality.png")
print("  - cluster_temporal.png")
print("  - spectral_embedding.png")

print("\n=== Clustering Complete ===")
print(f"Identified {n_clusters} distinct water column regimes")
print("Next step: Characterize each cluster by examining representative profiles")
