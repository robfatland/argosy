# Module 6: Spectral Clustering
# Run this as: %run /home/rob/argosy/sga/sga_module6.py

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score
import pickle
from pathlib import Path

# Output directory
SGA_DIR = Path('~/ooi/analysis/sga').expanduser()

# Load config
with open(SGA_DIR / 'sga_config.pkl', 'rb') as f:
    config = pickle.load(f)

n_eigvecs = config['n_eigenvectors']
k_min = config['k_range_min']
k_max = config['k_range_max']
final_k_override = config['final_k']

# Load spectral analysis results
print("Module 6: Spectral Clustering")
eigenvalues = np.load(SGA_DIR / 'eigenvalues.npy')
eigenvectors = np.load(SGA_DIR / 'eigenvectors.npy')
profile_index = pd.read_csv(SGA_DIR / 'profile_index_clean.csv')
profile_index['date'] = pd.to_datetime(profile_index['date'])

n_profiles = len(profile_index)
print(f"  Profiles: {n_profiles}")
print(f"  Eigenvectors used: {n_eigvecs}")
print(f"  k range: {k_min}-{k_max}")

# Spectral embedding (skip eigenvector 0 which is constant)
embedding = eigenvectors[:, 1:n_eigvecs + 1]

# Evaluate cluster quality
print("\n  Evaluating cluster quality...")
k_range = range(k_min, k_max + 1)
silhouette_scores = []
db_scores = []
inertias = []

for k in k_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
    labels = kmeans.fit_predict(embedding)

    sil = silhouette_score(embedding, labels)
    db = davies_bouldin_score(embedding, labels)

    silhouette_scores.append(sil)
    db_scores.append(db)
    inertias.append(kmeans.inertia_)

    print(f"    k={k}: Silhouette={sil:.3f}, DB={db:.3f}")

# Determine final k
best_k_idx = np.argmax(silhouette_scores)
best_k = list(k_range)[best_k_idx]

if final_k_override is not None:
    final_k = final_k_override
    print(f"\n  Final k (config override): {final_k}")
else:
    final_k = best_k
    print(f"\n  Final k (best silhouette): {final_k} (score={silhouette_scores[best_k_idx]:.3f})")

# Plot evaluation
fig, axes = plt.subplots(1, 3, figsize=(15, 4))

axes[0].plot(list(k_range), silhouette_scores, 'o-', markersize=6)
axes[0].axvline(x=final_k, color='r', linestyle='--', alpha=0.5, label=f'k={final_k}')
axes[0].set_xlabel('k')
axes[0].set_ylabel('Silhouette')
axes[0].set_title('Silhouette (higher=better)')
axes[0].grid(True, alpha=0.3)
axes[0].legend()

axes[1].plot(list(k_range), db_scores, 'o-', markersize=6, color='orange')
axes[1].set_xlabel('k')
axes[1].set_ylabel('Davies-Bouldin')
axes[1].set_title('Davies-Bouldin (lower=better)')
axes[1].grid(True, alpha=0.3)

axes[2].plot(list(k_range), inertias, 'o-', markersize=6, color='green')
axes[2].set_xlabel('k')
axes[2].set_ylabel('Inertia')
axes[2].set_title('Elbow Plot')
axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(SGA_DIR / 'cluster_evaluation.png', dpi=150, bbox_inches='tight')
plt.show()

# Final clustering
print(f"\n  Running final clustering with k={final_k}...")
kmeans_final = KMeans(n_clusters=final_k, random_state=42, n_init=10, max_iter=300)
final_labels = kmeans_final.fit_predict(embedding)

profile_index['cluster'] = final_labels

# Statistics
print(f"\n  Cluster statistics:")
for c in range(final_k):
    mask = final_labels == c
    cp = profile_index[mask]
    print(f"    Cluster {c}: {np.sum(mask)} profiles ({np.sum(mask)/n_profiles*100:.1f}%), "
          f"{cp['date'].min().strftime('%Y-%m-%d')} to {cp['date'].max().strftime('%Y-%m-%d')}")

# Temporal plot
fig, ax = plt.subplots(figsize=(14, 4))
ax.scatter(profile_index['date'], final_labels, c=final_labels, cmap='tab10', s=1, alpha=0.5)
ax.set_xlabel('Date')
ax.set_ylabel('Cluster')
ax.set_title(f'Spectral Clustering: {final_k} Regimes')
ax.set_yticks(range(final_k))
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(SGA_DIR / 'cluster_temporal.png', dpi=150, bbox_inches='tight')
plt.show()

# Save
profile_index.to_csv(SGA_DIR / 'profile_index_clustered.csv', index=False)
np.save(SGA_DIR / 'cluster_labels.npy', final_labels)

cluster_metadata = {
    'n_clusters': final_k,
    'n_eigenvectors': n_eigvecs,
    'silhouette_score': silhouette_scores[final_k - k_min],
    'davies_bouldin_score': db_scores[final_k - k_min],
    'inertia': inertias[final_k - k_min],
}
with open(SGA_DIR / 'cluster_metadata.pkl', 'wb') as f:
    pickle.dump(cluster_metadata, f)

print(f"\n=== Module 6 Complete ===")
