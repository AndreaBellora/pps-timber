import pytimber
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from cycler import cycler

# Define the color looping scheme for plt from a series of hex colors
colors = ['#3f90da','#ffa90e','#bd1f01','#94a4a2','#832db6','#a96b59','#e76300','#b9ac70','#717581','#92dadd']
plt.rcParams["axes.prop_cycle"] = cycler(color=colors)

# Define time window 
# For specific time use datetime(2024, 6, 1, 12, 0, 0) for example (year, month, day, hour, minute, second)
t_end = datetime.utcnow()
t_start = t_end - timedelta(hours=24)

# Variable names (example: beam intensity and beam time)
variables = [
    "LHC.BCTDC.A6R4.B1:BEAM_INTENSITY",
    "XRPH.A6L5.B2:MEAS_LIMIT_WARN_INNER_LU",
    "XRPH.D6R5.B1:TEMPFLOUT"
]

labels = ["Beam Intensity", "Inner warning limit", "Flange temperature"]

# Create LoggingDB object
ldb = pytimber.LoggingDB(source="nxcals")

# Convert to TIMBER time format (seconds since epoch)
t1 = t_start.timestamp()
t2 = t_end.timestamp()

# Query data
data = ldb.get(variables, t1, t2)

# Plot
fig, ax = plt.subplots(figsize=(10,5))
lines = []
axs = [ax]

for i, var in enumerate(variables):
    timestamps, values = data[var]
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
    line, = target_ax.plot(times, values, 'o-', markerfacecolor=color, markersize=3, label=labels[i], color=color)
    target_ax.set_ylabel(labels[i], color=color)
    target_ax.tick_params(axis="y", colors=color)
    lines.append(line)

ax.set_xlabel("Time (UTC)")
ax.set_title("RPIX plot")
ax.grid()

# Increase the y limit of the axis to create space for the legend
for target_ax in axs:
    y_min, y_max = target_ax.get_ylim()
    target_ax.set_ylim(y_min, y_max * 1.2)

ax.legend(lines, [line.get_label() for line in lines], loc="upper left", ncol=3)
fig = plt.gcf()
fig.subplots_adjust(right=0.75)  # Adjust right margin to fit the secondary axes

plt.show()
