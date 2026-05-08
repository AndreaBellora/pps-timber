import pytimber
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from cycler import cycler
import pickle


# Define the color looping scheme for plt from a series of hex colors
colors = ['#3f90da','#ffa90e','#bd1f01','#94a4a2','#832db6','#a96b59','#e76300','#b9ac70','#717581','#92dadd']
plt.rcParams["axes.prop_cycle"] = cycler(color=colors)

# Define time window 
# For specific time use datetime(2024, 6, 1, 12, 0, 0) for example (year, month, day, hour, minute, second)
t_end = datetime.now() # End time is current time minus 5 minutes to ensure data availability
t_start = t_end - timedelta(hours=6)

title = "56-220-nr-hr (A6R5)"

# Variable names (example: beam intensity and beam time)
variables = [
    "XRPH.A6R5.B1:MEAS_LIMIT_WARN_INNER_LU",
    "XRPH.A6R5.B1:MEAS_LVDT_LU",
    "LHC.BCTDC.A6R4.B1:BEAM_INTENSITY",
    "XRPH.A6R5.B1:TEMPFLOUT"
]

labels = ["Inner warning limit", "LVDT measurement", "Beam Intensity", "Flange temperature"]
# labels = []

# Per-variable y-rlimits (None means auto-scale)
y_limits = [(1.8,1.95), (1.8,1.95), None, None]  # [(y_min, y_max), ...]
# y_limits = [None, None, None, None]  # [(y_min, y_max), ...]

if len(labels) < len(variables):
    print("Warning: Not enough labels provided for the variables. Some variables will be unlabeled in the plot.")
    for i in range (len(labels), len(variables)):
        labels.append(variables[i])  # Use variable name as label if not enough labels provided
        y_limits.append(None)  # Add default y-range for any additional variables

data = None
# Check if cached data, matching the query, exist already
try:
    with open("cached_data_lvdt.pkl", "rb") as f:
        cached_data = pickle.load(f)
        # Check if cached data matches the current query parameters (variables and time range)
        if (set(variables).issubset(set(cached_data.keys())) and
            't_start' in cached_data and 't_end' in cached_data and
            abs(cached_data['t_start'] - t_start) <= timedelta(minutes=15) and
            abs(cached_data['t_end'] - t_end) <= timedelta(minutes=15)):
            print("Using cached data")
            data = cached_data
        else:
            print("Cached data does not match the current query. Querying new data.")
            # Create LoggingDB object
            ldb = pytimber.LoggingDB(source="nxcals")

            # Convert to TIMBER time format (seconds since epoch)
            t1 = t_start.timestamp()
            t2 = t_end.timestamp()

            data = ldb.get_aligned(variables, t1, t2)
            
            data['t_start'] = t_start
            data['t_end'] = t_end
            
            with open("cached_data_lvdt.pkl", "wb") as f:
                pickle.dump(data, f)
            
except FileNotFoundError:
    print("No cached data found. Querying new data.")
    # Create LoggingDB object
    ldb = pytimber.LoggingDB(source="nxcals")

    # Convert to TIMBER time format (seconds since epoch)
    t1 = t_start.timestamp()
    t2 = t_end.timestamp()

    data = ldb.get_aligned(variables, t1, t2)
    
    data['t_start'] = t_start
    data['t_end'] = t_end
    
    # Cache the data for future use
    with open("cached_data_lvdt.pkl", "wb") as f:
        pickle.dump(data, f)

# Plot
fig, ax = plt.subplots(figsize=(20,5))
lines = []
axs = [ax]

for i, var in enumerate(variables):
    timestamps = data['timestamps']
    values = data[var]
    
    # Fix potential length mismatch between timestamps and values
    min_len = min(len(timestamps), len(values))
    timestamps = timestamps[:min_len]
    values = values[:min_len]
    
    times = [datetime.fromtimestamp(ts) for ts in timestamps]

    if i == 0:
        target_ax = ax
    else:
        target_ax = ax.twinx()
        axs.append(target_ax)
        target_ax.spines["right"].set_position(("axes", 1 + 0.1 * (i - 1)))
        target_ax.set_frame_on(True)
        target_ax.patch.set_visible(False)

    color = plt.rcParams["axes.prop_cycle"].by_key()["color"][i % len(colors)]
    line, = target_ax.plot(times, values, 'o-', markerfacecolor=color, markersize=1, label=labels[i], color=color)
    target_ax.set_ylabel(labels[i], color=color)
    target_ax.tick_params(axis="y", colors=color)
    lines.append(line)
    

ax.set_xlabel("Time (UTC)")
ax.set_title(title)
ax.grid()

# Increase the y limit of the axis to create space for the legend
for target_ax in axs:
    y_min, y_max = target_ax.get_ylim()
    target_ax.set_ylim(y_min, y_max * 1.2)

# Apply manual y-limits if specified
for i, target_ax in enumerate(axs):
    if y_limits[i] is not None:
        print(f"Setting y-axis limits for {labels[i]}: {y_limits[i]}")
        target_ax.set_ylim(y_limits[i])

ax.legend(lines, [line.get_label() for line in lines], loc="upper left", ncol=5)
fig = plt.gcf()
fig.subplots_adjust(right=0.75)  # Adjust right margin to fit the secondary axes

plt.show()
