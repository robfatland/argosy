# Spectral Graph Analysis (SGA)


- 7 sequential modules 
- run from `chapters/SpectralGraphAnalysis.ipynb`
- operates on post-processing tier 6 (`pp06`) shard dataset
    - source data location: `~/ooi/postproc/pp06`
    - considers 6 HDS scalar sensors: Temp, salinity, DO, density, ChlorA, backscatter
        - CDOM, PAR, nitrate, pH, pCO2 not considered
            - CDOM has too many dropouts
            - PAR is diurnal; will confuse matters
            - nitrate, pH, pCO2 are low-sample-rate
                - would introduce confusing weighting
    - salinity/density are filtered to remove spikes
    - CDOM and ChlorA: Savitzky-Golay filter
        - for handling weak/quantized signals
    - backscatter is filtered to remove spikes
- Jupyter Lab environment is used to render charts
- Results are written in `~/ooi/analysis/sga`


## Motivation overview


- `pp06` source data is a filtered and cleaned version of `redux` shards so can be subjected to analysis
- Spectral graph theory is intended to define and classify water column state
    - Procedure description at a high level:
        - Transform depth-quantized profiles (6 sensors) into nodes of a graph
        - Calculate edge weights to encode pairwise similarity
            - Limit the number of allowed non-zero edge weights for a given node
    - Produce some variant of a graph Laplacian and calculate the eigenvalue spectrum
    - Pay particular attention to the second (Fiedler) eigenvalue
    - Use a subset of eigenvalues to define a set of water column states



## Module functions


1. Load, index data
    - User enters start and end years
    - Build a global-index-keyed file lookup
    - Builds `sensor_files[sensor][global_idx] = filepath`
    - Creates `profile_index.csv` with columns: global_idx, year, doy, daily_idx, date
    - Out: `~/ooi/analysis/sga/profile_index.csv`, `~/ooi/analysis/sga/sensor_files.pkl`
    - 10 seconds
2. Generate a feature matrix
    - Interpolate each profile to a standard depth grid
    - produces a rectangular feature matrix suitable for distance computation
    - here 'features' are sensor components (values) at a given depth
    - uses 80 standard depths: 2 meter bins
    - Missing data is assigned NaN
    - Output: `feature_matrix.npy` shape (n_profiles, 480 = 6 x 80)
    - 'minutes'



**Key correctness property**: Row N of the feature matrix corresponds to one physical
moment in time (one global index). All sensor values in that row are co-temporal.


**What to verify**: Completeness percentages. Temperature/DO should be highest (CTD
rarely offline). CDOM may be lower (FLORT gaps). If any sensor shows 0% → check paths.


3. Normalize the feature matrix
    - Handle missing data, then z-score normalize the feature matrix.
    - Missing data strategy (user selects):
        - Option 1 (default): Remove profiles with >50% NaN, impute remainder with column mean
        - Option 2: Impute all NaN with column mean
        - Option 3: Use only complete profiles
    - Z-score normalization: each column → mean=0, std=1
    - Effect of imputation: NaN → column mean → z-score ≈ 0
        - Missing data becomes "average" data 
        - Neutral but imperfect.

    - Output: `feature_matrix_normalized.npy`
    - Output: `profile_index_clean.csv` (rows that survived filtering)
    - Output: `scaler.pkl` (for inverse-transforming later)
    - ~10 seconds


**What to verify**: Mean ≈ 0, std ≈ 1. Profile count should drop slightly from Module 2.


4. Similarity Graph
    - Purpose: Compute pairwise distances, apply Gaussian kernel, build sparse graph.
    - Process:
        - Squared Euclidean distance between all pairs of normalized profiles
        - Gaussian kernel: similarity = exp(-d² / 2σ²), where σ² = median squared distance
        - Sparsify via k-Nearest Neighbors (default k=10): only retain the k strongest similarities per node; zero out everything else
        - Build NetworkX graph from sparse adjacency matrix


Left off here.


**Key parameters**:
- σ² (kernel width): controls how quickly similarity drops with distance.
  Median heuristic is standard. Narrower → more local structure; wider → more diffuse.
- k (neighbors): controls graph sparsity. k=10 is typical for spectral clustering.

**Output**:
- `similarity_graph.pkl`
- `adjacency_matrix.npy`
- `graph_metadata.pkl`

**What to verify**: Graph should be connected (Connected: True). Edge count ≈ n × k / 2.

**Runtime**: ~2–5 minutes (dominated by pairwise distance computation on 20K+ profiles).


## Module 5: Spectral Analysis

**Purpose**: Compute eigenvalues/eigenvectors of the graph Laplacian.

**Process**:
- Compute normalized Laplacian: L_sym = I - D^(-1/2) A D^(-1/2)
- Find smallest 50 eigenvalues via sparse eigensolver
- Analyze spectral properties: Fiedler value, spectral gap, effective dimensionality

**Key outputs**:
- Eigenvalue spectrum plot (where are the gaps?)
- Fiedler vector (2nd eigenvector) plotted vs time → shows the primary partitioning

**Interpretation**:
- Large spectral gap between λ_k and λ_{k+1} suggests k natural clusters
- Fiedler vector sign: positive vs negative = the 2-cluster split
- If Fiedler vector shows seasonal oscillation → the primary structure is seasonal

**Output**:
- `eigenvalues.npy`, `eigenvectors.npy`
- `spectral_properties.pkl`
- `eigenspectrum.png`, `fiedler_vector.png`

**Runtime**: ~1–2 minutes.


## Module 6: Spectral Clustering

**Purpose**: Cluster profiles in the spectral embedding space.

**Process**:
- Embed profiles using first n eigenvectors (default 10, skipping eigenvector 0)
- Run k-means for k=2..10, evaluate silhouette and Davies-Bouldin scores
- User selects final k
- Assign cluster labels

**External script**: `%run /home/rob/argosy/_sga_module6.py`

**Interpretation challenges** (from prior runs):
- With multi-year data, the dominant signal is the seasonal cycle → k=2 wins
  (summer stratified vs winter mixed). This overwhelms sub-seasonal structure.
- If clusters are "everything vs a few outliers": likely data quality issue
  (erratics, sensor dropouts creating extreme z-scores in imputed profiles).
  The pp06 filtering should reduce this.

**Diagnosis plan if clusters look wrong**:
1. Check Fiedler vector temporal plot from Module 5: is it seasonal?
2. Identify the "outlier" cluster profiles: what dates/sensors are they?
3. Load their raw feature vectors and check for anomalous values
4. Consider: is the distance metric appropriate? (Euclidean in z-score space
   weights all sensors equally — is that desirable?)
5. Try different k values, different n_eigenvectors, different σ²

**Output**:
- `profile_index_clustered.csv`
- `cluster_labels.npy`
- `cluster_metadata.pkl`
- `cluster_evaluation.png`, `cluster_temporal.png`

**Runtime**: ~2–5 minutes.


## Module 7: Characterize Regimes

**Purpose**: Examine the physical properties of each cluster.

**Process**:
- For each cluster: compute mean and std of each sensor at each depth
- Plot mean profiles per cluster (colored by cluster) for each sensor
- Identify what distinguishes the clusters physically

**Interpretation**: Clusters should map to recognizable oceanographic states
(e.g. stratified summer, mixed winter, upwelling event, anomalous year).

**Runtime**: ~1 minute.


## Diagnostic Checklist

Before running the full pipeline, verify:

- [ ] pp06 exists and is populated (`ls ~/ooi/postproc/pp06/`)
- [ ] environment.yml matches current packages (`conda env export` and diff)
- [ ] `profile_index.csv` column names match what Modules 4+ expect
  (global_idx, year, doy, daily_idx, date)
- [ ] Module 4 references `global_idx` not `profile_idx`
- [ ] Eigenspectrum from Module 5 shows meaningful gaps (not flat)
- [ ] Fiedler vector shows temporal structure (not noise)


## Known Issues / History

- **Positional indexing bug** (fixed June 2026): Original Modules 1–2 indexed sensors
  by file list position, causing co-temporality errors between CTD and FLORT sensors.
  New modules use global index lookup.
- **Library version drift** (fixed June 2026): scikit-learn 1.2.2 incompatible with
  threadpoolctl 3.6.0. Upgraded sklearn. Environment pinned in `environment.yml`.
- **Two-cluster problem**: Prior runs with 4+ years of data always converge to k=2
  (seasonal). Need to investigate: run per-year, force higher k, examine what σ²
  does to the similarity structure, or apply the analysis to sub-annual windows.
