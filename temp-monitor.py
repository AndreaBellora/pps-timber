import pytimber
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from cycler import cycler
import pickle


# Define the color looping scheme for plt from a series of hex colors
colors = ['#3f90da','#ffa90e','#bd1f01','#94a4a2','#832db6','#a96b59','#e76300','#b9ac70','#717581','#92dadd']

# Define time window 
# For specific time use datetime(2024, 6, 1, 12, 0, 0) for example (year, month, day, hour, minute, second)
# t_end = datetime.now() # End time is current time minus 5 minutes to ensure data availability
t_end = datetime(2026, 5, 8, 11, 0, 0) # End time is current time minus 5 minutes to ensure data availability
t_start = t_end - timedelta(hours=6)

# Per-variable y-limits (None means auto-scale)
y_limits = [None, None, None, None]  # [(y_min, y_max), ...]

# Per-variable labels (if not enough labels are provided, variable names will be used as labels for the remaining variables)
labels = ["Beam intensity", "Bunch length (ns)", "Flange temperature", "Sensor temperature"]


def get_or_cache_data(variables, t_start, t_end, cache_filename):
    data = None
    # Check if cached data, matching the query, exist already
    try:
        with open("cached_data_temp.pkl", "rb") as f:
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
                
                with open("cached_data_temp.pkl", "wb") as f:
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
        with open("cached_data_temp.pkl", "wb") as f:
            pickle.dump(data, f)
    return data

if __name__ == "__main__":

    plt.rcParams["axes.prop_cycle"] = cycler(color=colors)

    pps_rp_name_map = {
        "45-220-fr-hr": "B6L5.B2",
        "45-220-cyl-hr": "E6L5.B2",
        "45-220-nr-hr": "A6L5.B2",
        "45-210-fr-hr": "D6L5.B2",
        "56-220-fr-hr": "B6R5.B1",
        "56-220-cyl-hr": "E6R5.B1",
        "56-220-nr-hr": "A6R5.B1",
        "56-210-fr-hr": "D6R5.B1"
    }

    # Variable names (example: beam intensity and beam time)
    variables = [
        "LHC.BCTDC.A6R4.B1:BEAM_INTENSITY",
        "LHC.BQM.B1:BUNCH_LENGTH_MEAN",
        "LHC.BCTDC.A6R4.B2:BEAM_INTENSITY",
        "LHC.BQM.B2:BUNCH_LENGTH_MEAN"]

    for rp, timber_name in pps_rp_name_map.items():
        if timber_name.startswith("E"):
            variables.append(f"XRPH.{timber_name}:LU:TEMPFLOUT")
        else:
            variables.append(f"XRPH.{timber_name}:TEMPFLOUT")
        variables.append(f"XRPH.{timber_name}:LU:TEMP01")

    from pprint import pprint
    print("Variables to query:")
    pprint(variables)

    data = get_or_cache_data(variables, t_start, t_end, "cached_data_temp.pkl")
    
    pprint("Data keys:")
    pprint(list(data.keys()))

    # Create plots in a layout with 2 columns and as many rows as needed
    ncols = 2
    nrows = (len(pps_rp_name_map) + ncols - 1) // ncols

    fig, axs = plt.subplots(nrows=nrows, ncols=ncols, figsize=(30, 5 * nrows))

    # Iterate from top to bottom left, then top to bottom right
    for i, rp in enumerate(pps_rp_name_map.keys()):
        row = i % nrows
        col = i // nrows
        ax = axs[row, col]
        ax.set_title(rp)
        ax.grid()
        
        labels_plot = labels.copy()  # Start with the default labels and modify if needed
        y_limits_plot = y_limits.copy()  # Start with the default y-limits and modify if needed
        
        # Variables to plot for the specific RP are the ones related to it 
        # and the beam intensity and bunch length of the relevant beam 
        rpname, beam = pps_rp_name_map[rp].split(".")[0], pps_rp_name_map[rp].split(".")[1]  # Extract RP name and beam from the timber variable name 
        vars_to_plot = []
        for var in variables:
            if var.startswith('LHC') and beam in var:
                vars_to_plot.append(var)
            elif var.startswith('XRPH') and rpname in var:
                vars_to_plot.append(var)
                
        print(f"Variables to plot for {rp}:")
        pprint(vars_to_plot)
        if len(labels) < len(vars_to_plot):
            print("Warning: Not enough labels provided for the variables. Some variables will be unlabeled in the plot.")
            for i in range (len(labels), len(vars_to_plot)):
                labels.append(vars_to_plot[i])  # Use variable name as label if not enough labels provided
                y_limits.append(None)  # Add default y-range for any additional variables

        subplot_axs = [ax]
        for ivar, var in enumerate(vars_to_plot):
            timestamps = data['timestamps']
            values = data[var]
            
            # Fix potential length mismatch between timestamps and values
            min_len = min(len(timestamps), len(values))
            timestamps = timestamps[:min_len]
            values = values[:min_len]
            
            times = [datetime.fromtimestamp(ts) for ts in timestamps]

            if ivar == 0:
                target_ax = ax
            else:
                target_ax = ax.twinx()
                target_ax.spines["right"].set_position(("axes", 1 + 0.1 * (ivar - 1)))
                target_ax.set_frame_on(True)
                target_ax.patch.set_visible(False)
                subplot_axs.append(target_ax)

            color = plt.rcParams["axes.prop_cycle"].by_key()["color"][ivar % len(colors)]
            target_ax.plot(times, values, 'o-', markerfacecolor=color, markersize=1, label=labels[ivar], color=color)
            target_ax.set_ylabel(labels[ivar], color=color)
            target_ax.tick_params(axis="y", colors=color)
            
        ax.set_xlabel("Time (UTC)")
        
        # Increase the y limit of the axis to create space for the legend
        for target_ax in subplot_axs:
            y_min, y_max = target_ax.get_ylim()
            if y_max > 0:
                target_ax.set_ylim(y_min, y_max * 1.2)
            else:
                target_ax.set_ylim(y_min, y_max * 0.8)

        # Apply manual y-limits if specified
        for i, target_ax in enumerate(subplot_axs):
            if y_limits[i] is not None:
                print(f"Setting y-axis limits for {labels[i]}: {y_limits[i]}")
                target_ax.set_ylim(y_limits[i])

    fig.subplots_adjust(hspace=0.4, wspace=0.35, left=0.02, top=0.97, bottom=0.045, right=0.88)  # Adjust margins to fit the subplots
    plt.show()
