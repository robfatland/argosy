# Visualization


Working from sharded data build out both interactive visualizations and data
animation generators. Code for this and related tasks is in `chapters/Visualizations.ipynb`.


## Bundle plots


- Use matplotlib
- marker size typically 1 (small)
- `temperature` is on the x-axis with range wide enough to accommodate all the temperature data
- `depth` is on the y-axis with a range of 0 meters to 200 meters: From top to bottom
- The bundle plot means that several-to-many consecutive profiles are plotted on a single chart
- The bundle is chosen via two widget sliders called `nProfiles` and `index0`:
    - `nProfiles` is a number of time-consecutive profiles to plot on a single chart (a bundle of profile plots)
        - The minimum value is 0, the default starts at 1, the maximum value is 100
    - `index0` is the index of the first profile (chronologically) in the bundle plot
        - this is an integer from 1 to 157 (the number of profiles produced in the redux step)
        - the code will need to translate from the index0 value to the corresponding filename from `~/ooi/redux/redux2018`
        - if the bundle specifications `nProfiles` and `index0` go over the end file (file 157) the code handles this gracefully
        - The bundle plot only refreshes when the User is done dragging the slider to a new value (left mouse button release)
- Each refresh of the bundle plot should indicate the profile range as `yyyy-doy-profile to yyyy-doy-profile`:
    - yyyy is year
    - doy is day of year or Julian day
    - profile is a day-relative profile number from 1 to 9


### Navigation buttons


There are additional buttons in the control area laid out horizontally with
labels "--", "-", "+", "++". These affect the current value of the index0 slider.
The "-" and "+" buttons will decrement / increment the index0 slider value by 1 profile.
The "--" and "++" buttons will decrement / increment the index0 slider by half of the
current nProfiles value. Tapping any of these four buttons updates the chart.


### Dual-sensor display


In the case of a bundle chart with 2 sensors: The plot is wider. The
x-axis is extended to give more horizontal extent and the two sensor ranges will
be offset from one another so that the resulting sensor bundle traces will not (ideally)
overlap. This is done by having two respective axes, one for each sensor, where the
range of the axes is determined as follows:


Suppose the x-axis range for sensor 1 is from `a` to `b`. For sensor 2 it is from `c` to `d`.
Then the bundle chart range will accommodate both sets of sensor profiles by having a sensor 1
axis running from `a` to `(2b - a)`; and a sensor 2 axis running from `(2c - d)` to `d`.
In this way sensor 2 data will be displaced to the right and sensor 1 to the left so that
the profiles do not overlap.


As a concrete example: temperature in range 7 to 20 deg C means that the x-axis for the
temperature sensor should run from 7 to 33 deg C. Then suppose sensor 2 is salinity with
range 32 to 34: Then the chart should have a second horizontal axis with a data range
from 30 to 34.


### Mode toggle


Rather than have the User choose 'bundle' or 'meanstd' as a permanent choice: Install a choice control
widget in the interface, one for each sensor being charted. The choices are 'bundle' and 'meanstd' so
the User can switch between views.


## Bundle animation


- Write a version of the bundle plot visualization that creates an animation: As an output .mp4 file.
- This code will run in a Jupyter cell
- The input questions take on the default value if the User just hits Enter.
    - Start by asking "Include TMLD estimate in the visualization? Default is no. [y/n]"
    - Then ask "How many profiles in the bundle? Default is 18 (two days)" refer to this as N
    - Then ask "How many seconds delay between frames? (0.1 sec):" refer to this as d
    - Then ask "Start date (default 01-JAN-2018):" refer to this as T0
    - Then ask "End date (default 31-DEC-2018):" refer to this as T1
- Start at T0 and continue to T1: To create an animated chart sequence
    - The output file should be called 'temp_bundle_animation.mp4'
    - Each frame of the animation consists of N profiles bundled in one chart
    - The horizontal axis is fixed at 7 deg C to 19 deg C, does not change from one frame to another
    - The vertical axis is fixed as before from 200 meters to 0 meters
    - Show N profiles per frame of the animation
    - For a given profile: If the TMLD option is selected but there is no value for the TMLD in the CSV file: Omit adding that marker.
    - If possible: Add in a 'hold time' per frame of d seconds
    - If a time gap > 48 hours exists between any two consecutive profiles in a given bundle/frame:
        - This chart frame includes in large black letters at the lower right 'Time Gap'
        - The Time Gap message persists until all N consecutive profiles do not have a time gap
- Check that the output file exists and report its status


## Curtain plot


A curtain plot encodes data values as colors on a color map. Depth is y axis down from
the surface, time is the x axis typically spanning months to years. Each profile becomes
a thin vertical line. Collectively the effect is a curtain. The code also superimposes
iso-sensor lines making it visually easier to track depth variability with time.

Code is in `chapters/Visualizations.ipynb`.


## Midnight/Noon annotation


The local time at the Oregon Slope Base site is UTC-8 during standard time and UTC-7 during
daylight savings time. Create a data structure tied to Oregon Slope Base that contains this
information. Then add the following feature:


When a profile bundle size is nProfiles = 1: When that profile start-end interval spans
local midnight place the word MIDNIGHT in large font on the chart at the lower right. Likewise
when the profile start-end interval spans local noon place the word NOON in large font on the
chart at the lower right.


### Condition logic


The condition for a profile to be considered at local noon is: Local noon falls in
a time window defined by [(local) `start` time - 30 minutes, (local) `end` time + 30 minutes].
That is: Both times defining this time window are in local time for a meaningful comparison
to local noon. The same logic applies to local midnight.


As a temporary validation measure: When printing 'NOON' or 'MIDNIGHT': Underneath that
print the profile `peak` time shifted to local time. Again this time shift is -8 hours
during standard time and -7 hours during daylight savings.


## Annotation file


The next feature to add will be annotation per profile from a source CSV file: In the
form of either text or markers. The name of the annotation file will be arbitrary so there
will be (at the bottom of the user interface) a blank field where the user will type a
filename such as `~/argosy/annotation.csv`.


Next to the filename field place a button labeled `Annotation Load`. When this is clicked
the code will attempt to render annotations from the given CSV file. This button will toggle
on/off.


The CSV file must have the following column labels present in row 1:


```
shard, profile, depth, value, color, markersize, opacity, text
```


- `shard` will be the sensor designation as found in shard filenames.
- `profile` will be the global profile index as found in `profileIndices`.
- `depth` is depth in meters, positive downward
- `value` is a data value for this sensor type
- `color` is a marker color
- `markersize` is a marker size
- `opacity` is a marker opacity
- `text` is some annotation text


If one of the CSV fields is not present in row 1: Print a message to this effect
and do nothing further.


For each subsequent row present: Fields can be blank by having no text, i.e. two commas `,,`
or one comma at the end `,`. The `shard` and `profile` fields can not be empty. If they
are: Print an error message and do nothing further.


If the text field is not empty: Print the text on the chart when the corresponding
shard is active and the single bundle profile matches the profile value. Otherwise
render a marker of the given location, size, color and opacity.


For marker rendering:


- If no markersize is given: The marker size is 9.
- If no opacity is given: The default is fully opaque.
- If no color is given: Use the color of the `shard` sensor
- If no depth is given: Use depth = 180.
- If no value is given: Use value = center of x-axis range for this sensor


## Visualization questions and ideas


- Does the visualization code read the entire dataset into RAM at the outset?
    - If so let's shift to reading only the data needed for a given chart...
        - ...each time the chart parameters change, for example due to moving a slider.
