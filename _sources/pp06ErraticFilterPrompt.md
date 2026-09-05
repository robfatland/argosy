The shallow profiler data are at times erratic. The idea here is to describe a set of filters that produce pp06 from pp06 by means of filters numbered
0, 1, 2 etcetera. The zero filter is simply creating an actual shard dataset in the same format as redux using the pp05 manifest.  


### Filter 0: Baseline task from manifest to data


Create a copy of shard profiles under ~/ooi/pp06 using the pp05 manifest.


### Filter 1: Suppress conductivity erratics


The conductivity sensor produces both salinity and (with temperature) density profiles. This filter drops out salinity and density data values when the
salinity fails at least one of two criteria: The salinity must be in a physically possible range; and it must be close (via threshold) to the previous acceptable data value in the ascending profile. Dropped data are described in an annotation file.


#### Terms


- GPI: global profile index, some integer value P 
- -1 is the relative prior (possible) profile
    - If it exists it should be profile P-1
    - If it does not exist then P-1 would be found earlier in time
- +1 is the corresponding subsequent profile, again if it exists
- Depth values as given in the erratic examples are approximate
- MRA: Most Recent Acceptable data value
    - In a sequential walk-through of a profile: Most recent "good" data point
- Criteria: For accepting a profile data value as valid
    - PPC: physically possible criterion: Data on \[sp_{lo}, sp_{hi}\].
    - SSC: sample-to-sample criterion e.g. 0.5 PSU
        - Let D = | This data value - MRA |
        - If D > SSC: This data value is discarded (and logged to the CSV)
        - Else: MRA = This data value


A time series traverse of profile P will have sample indices 1, 2, ..., S. The first sample found within the PPC is the profile starting point; it becomes the MRA. Everything prior to that sample is removed from the profile and logged. From here we examine the subsequent samples up to S. Each time a sample is accepted it becomes the MRA.


Deleted samples are logged in a CSV file: Sensor, global profile index, sample index, sample value, sample depth. Output file is `~/ooi/pp06/pp06_filter1.csv`.


Note: This filter is specific to salinity and density and uses the salinity data. Every time a salinity data value is discarded and logged, the corresponding density data value is also discarded and logged. 


Note: More complicated Markov-style filters are possible but deferred.


#### Example filter 1 erratics


Salinity erratic: Profile 2016-328-2 GI 3278 at depth 37 meters; with the excursion negative. In the same profile there is another candidate sequence at about 57 meters. However this is real data: The same signal is visible in the +1 profile. These would argue for a larger SSC threshold.


Salinity erratic: GI 2075 at 81 meters. 


Salinity in GI 9043 shows a large erratic from depth 124m to 61m. It would ideally be removed in its entirety by means of the MRA not changing but this will also cut the upper part of the profile though the sensor appears to recover.


