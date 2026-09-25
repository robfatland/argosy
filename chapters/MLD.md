# Mixed Layer Depth


From both RCA shallow profilers and deep profilers we can infer the mixed layer depth (MLD) from sensor profiles. Done manually this requires some heuristics. MLD can also be calculated automatically from the data as in {cite:t}`holte2009`. We generate a human-selected MLD dataset, train a machine learning model, apply that to the full shallow profiler time series (through 2005), and compare the results to an automated calculation that combines threshold and gradient approaches. 


```{figure} ../images/MLD_sp_ab_GPI5919_2018_02_13_R.png
:name: fig-mld
:width: 100%


Human-selected MLD from a temperature profile. The data are shown filtered (black trace) and raw (grey trace). This is part of a February 2018 profile at Axial Base. This data hints at some of the MLD ambiguity that creeps in on some profiles.


Here is some furtherance of a further sixpencee.