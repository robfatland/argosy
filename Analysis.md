# Analysis Concepts


## Prompt


There are 11 scalar sensors (scalar: one data value per sample) and four vector sensors 
(more than one data value per sample). The total count on the vector side is about 153 
data values per sample. In the shallow profiler framework these sensors can be said 
to instantaneously observe the water column (on a time scale of ten years) across a 
depth range of 180 meters. Hence we have a time axis (10 years), a depth axis, and 
11 scalar + 150 vector values per sample. List some possible approaches to analyzing 
this data with the scientific objective in mind of better characterizing the upper 
water column or epipelagic zone in this part of the northeast Pacific ocean. 


## Response


Given the rich multidimensional dataset (time × depth × {11 scalars / 4 vector }) 
spanning 10 years and 200 meters of the epipelagic zone, here are five analytical approaches:


### Empirical Orthogonal Function (EOF) / Principal Component Analysis


Decompose the spatiotemporal variability to identify dominant modes of water column structure. 
This would reveal:


- Primary patterns of vertical stratification and their temporal evolution
- Coupled behavior between scalar and vector measurements (e.g., how temperature gradients relate to current patterns)
- Seasonal vs. interannual modes of variability
- Potential identification of "regime shifts" in the epipelagic zone
- Implementation: Flatten depth profiles into feature vectors, apply EOF analysis separately to scalars and vectors, then examine correlations between their principal components.


### Unsupervised Clustering of Vertical Profiles


Use machine learning (k-means, hierarchical clustering, or Gaussian 
mixture models) to identify distinct "water column states".


- Classify profiles into categories (e.g., "well-mixed", "strongly stratified", "upwelling signature")
- Track frequency and duration of each state over the 10-year period
- Identify transition patterns between states and their environmental drivers
- Create a "state space" representation showing how the system moves through different configurations
- Value: This creates an objective taxonomy of epipelagic conditions without assuming functional forms.


### Mixed Layer Depth (MLD) Dynamics with Multi-Sensor Validation


Since you already looked at TMLD (Temperature Mixed Layer Depth), extend this:


- Calculate MLD using multiple criteria: temperature, density, salinity, dissolved oxygen, fluorescence
- Quantify agreement/disagreement between different MLD definitions
- Correlate MLD variations with vector data (current shear, spectral irradiance attenuation)
- Build predictive models for MLD evolution using lagged correlations with meteorological forcing
- Novel aspect: The vector sensors (especially spectral data) could reveal bio-optical signatures of mixing events.


### Depth-Resolved Anomaly Detection and Event Characterization


Identify and catalog "interesting events" across the 10-year record:


- Upwelling events (temperature, nutrient, chlorophyll signatures)
- Phytoplankton blooms (fluorescence, backscatter, oxygen supersaturation)
- Internal wave passages (isopycnal displacement, current oscillations)
- Storm mixing events (erosion of stratification)
- Approach: Use multivariate anomaly detection (e.g., isolation forests, autoencoders) trained on "typical" profiles to flag unusual conditions, then manually characterize event types


### Spectral Analysis of Vertical Structure Evolution


Treat each depth as a time series and apply spectral methods:


- Identify dominant temporal frequencies at each depth (diurnal, tidal, seasonal, interannual)
- Use wavelet analysis to capture non-stationary periodicities
- Examine phase relationships between depths (e.g., how surface signals propagate downward)
- Cross-spectral analysis between scalar and vector components to identify coupled oscillations
- Insight: This reveals the "memory" of the system at different depths and timescales
    - e.g., surface layers respond to daily forcing while deeper layers show seasonal patterns.


### Integrated Water Column "Fingerprinting"


Create composite indices that integrate multiple sensors:


- Productivity Index: Combine chlorophyll, PAR, nutrients, oxygen
- Stratification Index: Combine temperature, salinity, density gradients
- Mixing Intensity: Combine current shear, density stability, backscatter variability
- Track these indices over time to create a holistic view of epipelagic zone "health" and variability.


AI recommendation: Start with approach clustering: Exploratory, will inform other approaches. 
The clustering results can guide which specific processes (MLD dynamics, events, spectral 
features) deserve deeper investigation. The EOF analysis would be a strong second step 
to understand the dominant modes within each cluster.


## Pivot to spectral graph theory


Polemic: The water column is not just a collection of measurements. It is a dynamical 
system whose structure can be encoded as a graph, where spectral methods reveal 
that structure's fundamental properties.


Spectral graph theory naturally handles the multi-scale, multi-sensor 
nature of the data. It doesn't assume linearity (unlike PCA) and can 
reveal non-obvious relationships. The eigenvalue spectrum provides a 
compact summary of system complexity, and the eigenvectors give you 
interpretable "modes" of water column behavior.


### Core Graph Construction


#### Depth-Time Similarity Graph


- Nodes: Each profile (time point) becomes a node 
- Edges: Complete graph with edges weighted by profile similarity
    - use a kernel function
        - Gaussian kernel on multivariate distance (all 11 scalars + vector summaries)
        - Edge weight reflects how similar two water column states are
- Spectral Analysis:
    - Graph Laplacian eigenvalues reveal the intrinsic dimensionality of water column states
    - Fiedler vector (2nd eigenvector) often reveals natural clustering/transitions
    - Spectral clustering identifies coherent regimes more robustly than k-means
    - Diffusion maps embed high-dimensional profiles into low-dimensional manifolds


Oceanographic Insight: The eigenvalue spectrum tells you how many "fundamental modes" 
characterize the epipelagic zone. A large spectral gap suggests distinct regimes 
(e.g., summer stratification vs. winter mixing).


### Temporal Evolution Graph (Visibility Graph)


Construction: Use horizontal visibility graph algorithm on time series of 
integrated metrics (e.g., total water column heat content, integrated chlorophyll) 


- Nodes: Time points 
- Edges: Connect time points that are "mutually visible" in the time series
- Spectral Analysis
    - Degree distribution reveals temporal complexity (periodic vs. chaotic)
    - Clustering coefficient indicates memory/persistence
    - Spectral entropy quantifies predictability


Oceanographic Insight: Distinguishes between regular seasonal cycles and 
chaotic/turbulent periods. High spectral entropy suggests external forcing dominates.


### Sensor Correlation Graph


- Nodes: Each of your 11 scalar + 150 vector components 
- Edges: Weighted by correlation (or mutual information) across all time-depth samples
- Spectral Analysis:
    - Community detection identifies groups of co-varying sensors
    - Graph cuts reveal which sensors provide redundant vs. unique information
    - Centrality measures identify "keystone" sensors that capture system state


Oceanographic Insight: Discovers emergent relationships (e.g., "bio-optical cluster", 
"physical stratification cluster"). Could guide sensor prioritization for future deployments.


#### Multi-Layer Depth Network


- Structure: Each depth level is a separate graph layer 
    - Nodes: Time points at each depth Intra-layer
    - Edges: Connect temporally adjacent measurements at the same depth 
    - Inter-layer edges: Connect the same time point across depths (vertical coupling)
- Spectral Analysis
    - Supra-Laplacian captures both temporal evolution and vertical coupling
    - Eigenvectors reveal depth-dependent temporal patterns
    - Can identify depths that are strongly coupled vs. decoupled
    - Algebraic connectivity quantifies vertical coherence


Oceanographic Insight: Reveals how surface forcing propagates downward, 
identifies the pycnocline as a "bottleneck" in the graph structure.


### Persistent Homology + Mapper Algorithm


Hybrid approach: Use Mapper to create a graph representation of the high-dimensional data manifold Process:


- Project data to 2-3D using PCA or diffusion maps
- Cover the projection with overlapping bins
- Cluster data within each bin
- Create graph where nodes are clusters, edges connect overlapping clusters
- Spectral Analysis:
    - Standard graph spectral methods on the resulting Mapper graph
    - Persistent homology tracks topological features (loops, voids) across scales


Oceanographic Insight: Reveals the "shape" of your data - e.g., does the epipelagic 
zone cycle through states in a loop (seasonal), or explore a more complex manifold?


### Specific Spectral Graph Metrics for Oceanography


- Algebraic Connectivity (Fiedler Value)
    - Measures how "well-connected" the water column is
    - Low values → strong stratification (surface decoupled from depth)
    - High values → well-mixed conditions
- Spectral Gap
    - Large gap → distinct regimes (e.g., upwelling vs. non-upwelling)
    - Small gap → continuous gradation of states
- Heat Kernel Signature
    - Characterizes each profile by how "information" diffuses through the graph
    - Profiles with similar signatures are dynamically similar even if instantaneously different
- Graph Fourier Transform
    - Decompose spatial (depth) patterns into "graph frequencies"
    - Low frequencies = large-scale vertical structure
    - High frequencies = fine-scale features (e.g., thin layers)


### Recommended Implementation Strategy


- Start with Depth-Time Similarity Graph
    - Construct graph with ~3,000-9,000 nodes (daily profiles over 10 years)
    - Compute Laplacian eigenspectrum
    - Apply spectral clustering to identify regimes
    - Visualize using diffusion map embedding


- Progress to the Sensor Correlation Graph (SCG)
    - Identify sensor communities
    - Use this to create "super-nodes" (sensor groups) for a reduced representation
    
    
- Integrate this with the Multi-Layer Depth Network
    - Examine how spectral properties change with depth
    - Identify critical depths where graph structure changes


- Software Tools
    - NetworkX (Python): General graph analysis
    - graph-tool (Python): Fast spectral methods for large graphs
    - PyGSP (Python): Graph signal processing, includes graph Fourier transforms
    - giotto-tda (Python): Persistent homology and Mapper
    - igraph (R/Python): Efficient community detection


## Spectral Graph Analysis


### Modules 1 and 2


Data preparation: Load and interpolate the sensor data by profile, result being an un-normalized feature matrix.
The output 2D table captures three dimensions of information: profile (time), sensor type and depth (binned).


- `feature_matrix.npy` is a `numpy` binary array file: { n-sensors x n-depth-bins columns } X { n-profiles rows }. This is referred
to as a feature matrix, as in "what is the feature measurement for temperature at 80 meters depth in a particular profile?"
- `feature_names.pkl` is a Python pickle file containing a list of { n-sensors x n-depth-bins } (e.g. 7 x 91 = 637)
strings, one per column of the feature matrix. Each string is formatted as "{sensor}_{depth}m", e.g. "temperature_0m", "temperature_2m", ..., "backscatter_180m". This is the column key for the feature matrix - it tells you what physical quantity each column represents.


The feature matrix together with the feature names form the core data structure for the graph analysis: 
The feature matrix is the numerical data, and feature_names is its labeled column index. 


- rows are individual profiles per the global numbering from `profileIndices`
- columns have a fast and a slow dimension
    - fast is depth bins (2 meters per bin)
    - slow is sensor (currently 7 types)



### Module 3


Module 3 reads both `feature_matrix.py` and `feature_names.pkl`. It normalizes the matrix,
handles missing data, and writes the results as `feature_matrix_normalized.npy` which has 
the same shape as `feature_matrix` but with z-score values instead of physical units.


### Module 4


- Let nProf be the number of profiles in consideration
- The source data from Module 3 has 
    - column count = nSensors x nBins {nS x nB} 
    - row count = nProf
    - An individual row is the {nS x nB} characterization of a profile
- The output matrices are square nProf rows x nProf columns
    - First output: Calculated squared Euclidean distance matrix: Distances between all pairs of profiles
        - Calculated from z-scores weights all sensors and depths equally
    - Second output: Similarity matrix: Apply a Gaussian kernel to produce weights on \[0, 1\]. 
    - Third output: A sparse *adjacency matrix* with strong weights retained, weak weights set to 0
        - Called an n-NN for n-Nearest Neighbors graph


### Module 5


- Analyze the adjacency matrix
    - Compute eigenvalues and eigenvectors
    - 


### Module 6



### Module 7



### Pending modifications

- Various control parameters for modules 1-7
    - depth bin size (initially 2 meters)
- Modules should always announce (print) what they are doing as they start and that they are done when they stop.
- To accommodate pH and pCO2 we will need more metadata on which profiles are 
midnight / noon runs.
- It is worth thinking about tidal correction and 'blowdown' correction: When
a current transverse to the anchor axis effectively lowers the shallow profiler
resting structure in the water column.
- We want to take a pre-analysis cleaning pass over the data
- We want to accommodate and flag coincident excursions from multiple sensors
- We want to flag "thin layer blips"



## Ingest these prompt / responses


### Prompt on cluster counts


Describe how I should be thinking about module 6, particularly with the idea of running it iteratively to get a reasonable number of clusters. I ran it once for just 2018 and got 10 clusters, most of which looked reasonable. And then I ran it again for a four year span 2016 through 2019 and it arrived at just two clusters as the default.


#### Response on two runs, namely 2018 vs 2016--2019


The two results are actually telling you something real, not contradicting each other.


What the silhouette score is optimizing


Silhouette measures how well-separated clusters are relative to their internal cohesion. With 4 years of data the dominant signal is the seasonal cycle - summer stratified vs. winter mixed. That contrast is so strong it overwhelms everything else, so k=2 wins the silhouette contest. With just 2018 the seasonal signal is still present but the algorithm has more resolution to find finer structure within seasons, so k=10 emerges.


How to think about the hierarchy


The clusters exist at multiple scales simultaneously:


Scale 1 (coarse): 2 clusters = winter mixing vs. summer stratification
Scale 2 (medium): ~4-6 clusters = spring transition, summer stratified, fall transition, winter mixed, upwelling events
Scale 3 (fine): 10+ clusters = sub-seasonal states, bloom events, anomalous profiles


The "right" number depends on your scientific question, not the silhouette score.


Iterative approach I'd recommend


Start with the 4-year run and override the default. Force k=4, k=6, k=8, k=10 and look at the cluster temporal plots each time. You're looking for:


Clusters that are seasonally coherent (good)


Clusters that are temporally scattered with no pattern (probably over-split noise)


Two clusters that always co-occur in the same season (probably should be merged)


The elbow plot from Module 6 is more useful than the silhouette score here - look for where adding another cluster stops meaningfully reducing inertia.


The 2018 result as a reference


Your 10-cluster 2018 result is valuable ground truth. Run the 4-year analysis at k=10 and compare - do the same physical states appear? Do they recur across years? That cross-validation tells you whether the clusters are robust oceanographic regimes or artifacts of a single year's data.



### Prompt on z-score


What is z-score?


#### z-score response


The z-score of a single value x is:


z = (x - mean) / std


It answers: "how many standard deviations is this value from the mean of its distribution?"


So if temperature at 10m has a mean of 12°C and std of 2°C, then a measurement of 16°C has z-score = (16-12)/2 = 2.0. A measurement of 10°C has z-score = -1.0.


Z-score normalization (what Module 3 does) applies this transformation to every column of the feature matrix independently. Each of the 637 columns gets its own mean and std computed, then every value in that column is replaced by its z-score.


The result: every column has mean=0 and std=1 regardless of its original units.


Why this matters for the distance calculation: Without it, the Euclidean distance would be dominated by whichever sensor has the largest absolute values. Density ranges from 1024-1028 kg/m³. Dissolved oxygen ranges from 50-300 µmol/kg. Salinity ranges from 32-34 PSU. If you compute raw distances, the dissolved oxygen differences (hundreds of units) would swamp the salinity differences (single units), even if salinity is equally informative oceanographically.


After z-score normalization every sensor contributes on equal footing - a 1-std deviation change in temperature counts the same as a 1-std deviation change in chlorophyll. The distance then measures "how unusual is this profile" in a sensor-agnostic way.




### prompt similarity to adjacency


Describe again the progression: From similarity (what is it? Inner product of column i and j?) to adjacency (edge weights on what range?)


#### response


Similarity here is not an inner product.


Squared Euclidean distance (Module 4, what's actually computed):


sq_d_ij = sum over all 637 features of (x_ik - x_jk)^2


Range: \[ 0, $\infty$). Zero means identical profiles, large means very different.


Similarity via Gaussian kernel (still Module 4):


s_ij = exp(-sq_d_ij / (2 * sigma^2))


Range: (0, 1]. Every pair gets a similarity value. s=1 means identical, s→0 means very different. This is the full similarity_matrix - dense, every entry nonzero.


Adjacency matrix (also Module 4, after the k-NN or epsilon-ball step):


This is where sparsification happens. For k-NN, most entries of similarity_matrix are zeroed out - only the k strongest similarities per node survive as edges. So:


Retained edges: weight in (0, 1], same values as similarity_matrix
Dropped edges: set to exactly 0
Range of nonzero entries: (0, 1].


So the distinction is: similarity_matrix is the complete dense pairwise similarity, adjacency is the sparse graph where weak connections have been pruned to zero. The Laplacian is then built from the adjacency, not the full similarity matrix.


An inner product would give you cosine similarity, which measures the angle between two profile vectors. That's a valid alternative but it conflates magnitude with direction - two profiles with the same shape but different absolute values would appear similar. The Euclidean distance approach treats absolute differences as meaningful, which is appropriate here since the features are z-score normalized.



## aside on AI2 Asta

    
I ran 20 experiments using AutoDiscovery on 81 x 4 profile files: { density, dissolved oxygen, salinity, temperature }. 
Files were for 2016, January 1 -- 9, 9 profiles per day. I borrowed text from `AIPrompt.md` to write up context for 
the data exploration. Of the 324 upload files a number (40+) had to be reloaded; so that is an obstacle.


URL: `https://autodiscovery.allen.ai/runs/3d1b04de-de13-4a16-b6e4-43b6f874fb28`
    

