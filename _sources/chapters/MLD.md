# Mixed Layer Depth


From both RCA shallow profilers and deep profilers we can infer the mixed layer depth (MLD) from sensor profiles. Done manually this requires some heuristics. MLD can also be calculated automatically from the data as in {cite:t}`holte2009`. We generate a human-selected MLD dataset, train a machine learning model, apply that to the full shallow profiler time series (through 2005), and compare the results to an automated calculation that combines threshold and gradient approaches. 