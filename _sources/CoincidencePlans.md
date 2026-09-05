# Coincidence Plans


## Overview


As we see transient behavior in sensor data with time: We want to
define auto-coincidence (persistence of a feature for one sensor)
and hetero-coincidence (persistence of a feature across multiple
sensors at the same depth over one or more profiles). This suggests
two plans (auto and hetero) with some details to be determined.


### Auto-coincidence


**Does a feature at depth *d* in profile *P_i* persist in profiles *P_{i+1}*, *P_{i+2}*, ...?**


**Does a feature signal behave as a transient with a return or as a shift 
with no discernable return?**


- Identify a particular PostProcessed dataset
    - Example: Interpolate profiles onto a common depth grid (1m bins, 0–200m)
    - Sensors with a high noise signal: Low pass filter
    - Reduce vector sensor data to one or more scalar sensor values
- Loop over sensors 
    - Use a rolling window of 2 or 3 days as a "baseline context"
    - Identify features
        - Example: From the SGA pipeline: z-score deviation from the running baseline
        - For each depth bin *d*: running mean μ(d) and std σ(d) { preceding N profiles }
        - Current profile score `z(d) = (value(d) - μ(d)) / σ(d)`
        - A **feature** is a contiguous depth range where |z| exceeds threshold T
            - For example 2.0 meaning 2 standard deviations 
        - Characterize the feature by: 
            - depth centroid, depth extent, peak z-score, sign (+/-)
    - Feature match across profiles 
        - For each detected feature in profile *P_i*:
            - Look forward into *P_{i+1}*, *P_{i+2}*, ... *P_{i+k}*
            - A feature **matches** if:
                - Depth centroid within a tolerance window (e.g. ±5m) 
                    - Allows for vertical migration of structure
                - Same sign (both positive or both negative excursion)
                - Peak z-score exceeds a reduced threshold 
                    - e.g. 1.5 instead of 2.0) — weaker persistence
            - Track the **persistence count**: how many consecutive profiles contain a matching feature
    - Score matches
        - Persistence = 1 profile: No auto-coincidence (could be noise)
        - Persistence = 2+ profiles: Flag with a proportional score
### 6. Implementation path

1. **Prototype on temperature, Slope Base, one month** — say a month with known interesting structure (fall transition, upwelling season)
2. Tune thresholds visually against bundle plots (do the flagged events look real?)
3. Extend to other sensors
4. Feed results into hetero-coincidence (do auto-coincident T features co-occur with auto-coincident S or DO features?)


### Considerations


- There are occasionally missing profiles: Singles, groups, dropouts
    - Need a strategy that may involve giving up until the profile sequence returns
- Diurnal cycle: The baseline will be affected by time-of-day effects. 
    - PAR and SPKIR are the most dramatic
  - Separate baselines for day vs. night profiles
  - Or include a diurnal harmonic in the baseline model
- **Depth drift tolerance:** Real features (e.g. an intrusion layer) may migrate vertically at ~1–5 m/hr. The matching window should accommodate this.
- **Gap handling:** If profiles are missing (maintenance, gaps), don't penalize — just skip and continue looking forward.
- **Output format:** A table of detected auto-coincident events:
  ```
  event_id, sensor, depth_start, depth_end, profile_first, profile_last, 
  persistence_count, mean_z_score, sign
  ```

