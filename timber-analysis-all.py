from datetime import datetime, timedelta
from cycler import cycler
from pprint import pprint
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import pytimber
import pickle
import os
import matplotlib.ticker as ticker
from matplotlib.backends.backend_pdf import PdfPages


os.makedirs("cache", exist_ok=True)

# Amenities
# Define the color looping scheme for plt from a series of hex colors
colors = ['#3f90da','#ffa90e','#bd1f01','#94a4a2','#832db6','#a96b59','#e76300','#b9ac70','#717581','#92dadd']

# Get fills with SB declared in the last 3 days
# Define time window 
# For specific time use datetime(2024, 6, 1, 12, 0, 0) for example (year, month, day, hour, minute, second)
# t_end = datetime.now() # End time is current time minus 5 minutes to ensure data availability
#group1 
t_end = datetime(2026, 3, 28, 10, 0, 0) # End time is current time minus 5 minutes to ensure data availability
t_start = datetime(2026, 3, 7, 10, 0, 0)
#group2
#t_end = datetime(2026, 4, 26, 3, 0, 0) # End time is current time minus 5 minutes to ensure data availability
#t_start = datetime(2026, 3, 30, 10, 0, 0)
#group3
#t_end = datetime(2026, 5, 17, 0, 0, 0) # End time is current time minus 5 minutes to ensure data availability
#t_start = datetime(2026, 5, 1, 21, 0, 0)



#t_end - timedelta(days=21)

print(f"Time window for fill selection: {t_start} to {t_end}")

# Create LoggingDB object
ldb = pytimber.LoggingDB(source="nxcals")

fill_list = ldb.get_interval_by_lhc_modes(t_start, t_end, mode1='STABLE', mode2='STABLE')

print('Fills to process:')
for fill in fill_list:
    sb_start = datetime.fromtimestamp(fill.modeFirstAttribute)
    sb_end = datetime.fromtimestamp(fill.modeSecondAttribute)
    n = fill.fillNumber
    print(f"\tFill {n} has SB from {sb_start} to {sb_end}")

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

variables = [
    "LHC.BCTDC.A6R4.B1:BEAM_INTENSITY",
    "LHC.BQM.B1:BUNCH_LENGTH_MEAN",
    "LHC.BCTDC.A6R4.B2:BEAM_INTENSITY",
    "LHC.BQM.B2:BUNCH_LENGTH_MEAN",
    "LHC.BCTFR.B6R4.B1:BUNCH_COUNT",
    "LHC.BCTFR.B6R4.B2:BUNCH_COUNT",
]

for rp, timber_name in pps_rp_name_map.items():
    if timber_name.startswith("E"):
        variables.append(f"XRPH.{timber_name}:LU:TEMPFLOUT")
    else:
        variables.append(f"XRPH.{timber_name}:TEMPFLOUT")
    variables.append(f"XRPH.{timber_name}:MEAS_LIMIT_WARN_INNER_LU")    
    variables.append(f"XRPH.{timber_name}:MEAS_LVDT_LU")
    
print("Variables to retrieve:")
pprint(variables)


######################################### Tier 1 - sample with all variables

def get_t1_data_with_caching(variables, fillInterval):
    fill_to_analyze = fillInterval.fillNumber
    fill_to_analyze_sb_start = datetime.fromtimestamp(fillInterval.modeFirstAttribute)
    fill_to_analyze_sb_end = datetime.fromtimestamp(fillInterval.modeSecondAttribute)

    try:
        with open(f"cache/cached_data_analysis_{fill_to_analyze}_t1.pkl", "rb") as f:
            cached_data = pickle.load(f)
            # Check if cached data matches the current query parameters (variables and time range)
            if (set(variables).issubset(set(cached_data.keys())) and
                't_start' in cached_data and 't_end' in cached_data and
                abs(cached_data['t_start'] - fill_to_analyze_sb_start) <= timedelta(minutes=15) and
                abs(cached_data['t_end'] - fill_to_analyze_sb_end) <= timedelta(minutes=15)):
                print("Using cached data")
                data = cached_data
            else:
                print("Cached data does not match the current query. Querying new data.")

                # Convert to TIMBER time format (seconds since epoch)
                t1 = fill_to_analyze_sb_start.timestamp()
                t2 = fill_to_analyze_sb_end.timestamp()

                data = ldb.get_aligned(variables, t1, t2)
                
                data['t_start'] = fill_to_analyze_sb_start
                data['t_end'] = fill_to_analyze_sb_end
                
                with open(f"cache/cached_data_analysis_{fill_to_analyze}_t1.pkl", "wb") as f:
                    pickle.dump(data, f)
                
    except FileNotFoundError:
        print("No cached data found. Querying new data.")
        # Create LoggingDB object
        ldb = pytimber.LoggingDB(source="nxcals")

        # Convert to TIMBER time format (seconds since epoch)
        t1 = fill_to_analyze_sb_start.timestamp()
        t2 = fill_to_analyze_sb_end.timestamp()

        data = ldb.get_aligned(variables, t1, t2)
        
        data['t_start'] = fill_to_analyze_sb_start
        data['t_end'] = fill_to_analyze_sb_end
        
        # Cache the data for future use
        with open(f"cache/cached_data_analysis_{fill_to_analyze}_t1.pkl", "wb") as f:
            pickle.dump(data, f)
            
    # Make all arrays of the same length by trimming to the shortest one
    min_length = min(len(arr) for arr in data.values() if isinstance(arr, np.ndarray))
    for key in data:
        if isinstance(data[key], np.ndarray) and len(data[key]) > min_length:
            data[key] = data[key][:min_length]

    df_t1 = pd.DataFrame({k: data[k] for k in data if k not in ['t_start', 't_end']})
    df_t1['fill'] = fill_to_analyze
    df_t1['time'] = pd.to_datetime(df_t1['timestamps'],unit='s')
    df_t1['data_tier'] = 'Tier 1'

    return df_t1

######################################### Tier2 -- only with RP inserted

# Drop all data with all the *MEAS_LVDT_LU larger than 5
# Create a new df for that

def get_t2_data_with_caching(variables, fillInterval, no_remove_t1=False):
    
    cache_path = f"cache/cached_data_analysis_{fillInterval.fillNumber}_t2.pkl"

    if os.path.exists(cache_path):
        df_t2 = pd.read_pickle(cache_path)
        print(f"Loaded df_t2 from {cache_path}")
    else:
        # Get the t1 data for the fill
        df_t1 = get_t1_data_with_caching(variables, fillInterval)
        df_t2 = df_t1.copy()
        df_t2.to_pickle(cache_path)
        print(f"Cached df_t2 to {cache_path}")
        if not no_remove_t1:
            # Delete t1 cache
            t1_cache_path = f"cache/cached_data_analysis_{fillInterval.fillNumber}_t1.pkl"
            if os.path.exists(t1_cache_path):
                os.remove(t1_cache_path)

    meas_limit_cols = df_t2.filter(regex="MEAS_LVDT_LU")
    mask = (meas_limit_cols > 3).all(axis=1)
    df_t2 = df_t2[~mask]

    df_t2["data_tier"] = "Tier 2"
    return df_t2

#########################################

## Example to compare the two data tiers
#df_t1 = pd.DataFrame()
#df_t2 = pd.DataFrame()
#
#for fill in fill_list[:40]:
#    print(f"Processing fill {fill.fillNumber}...")
#    df_t1 = pd.concat([df_t1,get_t1_data_with_caching(variables, fill)])
#    df_t2 = pd.concat([df_t2,get_t2_data_with_caching(variables, fill)])

## Find the total time range covered by the data
#overall_start = df_t1['time'].min()
#overall_end = df_t1['time'].max()
#print(f"Overall time range covered by the data: {overall_start} to {overall_end}")
#
## Print size info on the two dfs
#print(f"Tier 1 dataset size: {df_t1.shape[0]} rows, {df_t1.shape[1]} columns")
#print(f"Tier 2 dataset size: {df_t2.shape[0]} rows, {df_t2.shape[1]} columns")
#
#df_all = pd.concat([df_t1, df_t2], ignore_index=True)
#
#plt.figure(0,figsize=(20, 5))
#sns.scatterplot(data=df_all, x="time", y="XRPH.E6R5.B1:MEAS_LVDT_LU", hue='data_tier', s=3, edgecolor=None, linewidth=0)
#
#plt.xticks(rotation=45)
#plt.legend(loc='upper right', fontsize='large')
#plt.tight_layout()
#plt.show()

#########################################Definition variables for Tier 3 (operations with existing variables 


def make_t3_data(df_t2, no_remove_t2=False):
    lvdt_cols = [c for c in df_t2.columns if 'MEAS_LVDT_LU' in c]
    limit_cols = [c for c in df_t2.columns if 'MEAS_LIMIT_WARN_INNER_LU' in c]

    pairs = {}
    for col in lvdt_cols:
        prefix = col.split(":")[0]
        limit_match = [c for c in limit_cols if c.startswith(prefix)]
        if limit_match:
            pairs[prefix] = (col, limit_match[0])        

    distance_df = pd.DataFrame(index=df_t2.index)
    distance_df['fill'] = df_t2['fill']

    # Compute the absolute distance between the LVDT measurement and the inner limit for each RP
    for prefix, (lvdt, limit) in pairs.items():
        distance_df[prefix+':MIN_DIST_FROM_WARN_LIMIT'] = (df_t2[lvdt] - df_t2[limit]).abs()

    distance_df = distance_df.groupby('fill').min().reset_index()

    # Compute the maximum temperature and the temperature at insertion time
    temp_cols = [c for c in df_t2.columns if "TEMPFLOUT" in c]
    first_vals = df_t2.sort_values("time").groupby("fill")[temp_cols].first()
    max_vals = df_t2.groupby("fill")[temp_cols].max()

    # Compute the start and end times of each fill
    t_start = df_t2.groupby("fill")["time"].first()
    t_end = df_t2.groupby("fill")["time"].last()
    n_bunches = df_t2.groupby("fill")["LHC.BCTFR.B6R4.B1:BUNCH_COUNT"].first()
    intensity = df_t2.groupby("fill")["LHC.BCTDC.A6R4.B1:BEAM_INTENSITY"].first()
    
    # Compute the initial LVDT insertion and warning limit value (15 rows delay seems to be enough, ~15 s)
    nrows_delay = 15
    initial_lvdt = df_t2.groupby("fill").nth(nrows_delay).set_index("fill")[lvdt_cols]
    w_limit = df_t2.groupby("fill").nth(nrows_delay).set_index("fill")[limit_cols]

    # Put everything together
    t_start = t_start.to_frame("time_start")
    t_end = t_end.to_frame("time_end")
    n_bunches = n_bunches.to_frame("n_bunches")
    intensity = intensity.to_frame("intensity")
    initial_lvdt = initial_lvdt.add_suffix("_initial")
    w_limit = w_limit.add_suffix("_limit")
    max_vals = max_vals.add_suffix("_max")
    first_vals = first_vals.add_suffix("_first")

    tmp_df = (
        max_vals
        .join(first_vals)
        .join(t_start)
        .join(t_end)
        .join(n_bunches)
        .join(intensity)
        .join(initial_lvdt)
        .join(w_limit)
        .reset_index()
    )

    df_t3 = distance_df.merge(tmp_df.reset_index(), on='fill').reset_index(drop=True).drop(columns=['index'])

    df_t3['data_tier'] = 'Tier 3'
    df_t3 = df_t3.reset_index(drop=True)
    
    # Find unique fill numbers in df_t3
    fills = df_t3['fill'].unique()
    
    if not no_remove_t2:
        for fill in fills:
            t2_cache_path = f"cache/cached_data_analysis_{fill}_t2.pkl"
            if os.path.exists(t2_cache_path):
                os.remove(t2_cache_path)
    return df_t3
    
def get_t3_data_with_caching(variables, fillInterval, no_remove_t2=False):
    # Divide the fills in groups of five
    fill_groups = [fill_list[i:i+5] for i in range(0, len(fill_list), 5)]
    df_t3 = pd.DataFrame()

    t3_cache_path = f"cache/cached_data_analysis_t3.pkl"

    if os.path.exists(t3_cache_path):
        with open(t3_cache_path, "rb") as f:
            print("Using cached t3 data")
            df_t3 = pickle.load(f)
    else:
        for group in fill_groups:
            df_t2 = pd.DataFrame()
            for fill in group:
                print(f"Processing fill {fill.fillNumber}...")
                df_t2 = pd.concat([df_t2,get_t2_data_with_caching(variables, fill)])
            df_t3 = pd.concat([df_t3,make_t3_data(df_t2, no_remove_t2=no_remove_t2)])
        with open(t3_cache_path, "wb") as f:
            pickle.dump(df_t3, f)
    return df_t3

df_t3 = get_t3_data_with_caching(variables, fill_list, no_remove_t2=False)
print(df_t3)

print('Tier 3 dataframe structure:')
print(df_t3.info())
#################################################################################3
def format_df(df_t3):
    """Better shape for plotting"""

    df_t3 = df_t3.drop(columns=['data_tier'])
    id_cols = ["fill", "time_start", "time_end", "n_bunches", "intensity"]

    df_long = df_t3.melt(
        id_vars=id_cols,
        var_name="raw",
        value_name="value"
    )

    df_long[["xrph", "metric_group"]] = df_long["raw"].str.split(":", n=1, expand=True)
    df_long = df_long.drop(columns=["raw"])

    df_final = df_long.pivot_table(
        index=["fill", "xrph", "time_start", "time_end", "n_bunches", "intensity"],
        columns="metric_group",
        values="value"
    ).reset_index()

    df_final["TEMPFLOUT_first"] = (
        df_final["TEMPFLOUT_first"]
        .combine_first(df_final["LU:TEMPFLOUT_first"])
    )

    df_final["TEMPFLOUT_max"] = (
        df_final["TEMPFLOUT_max"]
        .combine_first(df_final["LU:TEMPFLOUT_max"])
    )

    df_final.drop(columns=["LU:TEMPFLOUT_first", "LU:TEMPFLOUT_max"], inplace=True)

    mapping = {'XRPH.'+v:k for k,v in pps_rp_name_map.items()}
    
    df_final['rp'] = df_final['xrph'].map(mapping)
    df_final['TEMPFLOUT_excursion'] = df_final['TEMPFLOUT_max'] - df_final['TEMPFLOUT_first']
    df_final['LVDT_excursion'] = df_final['MEAS_LVDT_LU_initial']-(df_final['MEAS_LIMIT_WARN_INNER_LU_limit']+df_final['MIN_DIST_FROM_WARN_LIMIT'])
    
    return df_final
    
###########################################################################################################################

plot_df = format_df(df_t3)

pd.set_option('display.max_rows', None)     
pd.set_option('display.max_columns', None)  
pd.set_option('display.width', 1000)        

print(plot_df)

print('Plotting dataframe structure:')
print(plot_df.info())

############################################################################################################################


############################################################################################################################
with PdfPages('pps-timber-GR1.pdf') as pdf:
   
   
# exclude fills in group1 
     exclude_fill = [11475,11477,11479,11505,11510] 

     plot_df_part = plot_df[plot_df['rp'].isin(['45-220-fr-hr', '45-220-cyl-hr', '45-220-nr-hr','45-210-fr-hr'])& 
     (~plot_df['fill'].isin(exclude_fill))]

     fig16=plt.figure(figsize=(10, 5))
     sns.lineplot(data=plot_df_part, x="intensity", y="LVDT_excursion", hue='rp',legend=False)
     sns.scatterplot(data=plot_df_part, x="intensity",y="LVDT_excursion" , hue='rp', s=12, edgecolor=None, linewidth=0)
     plt.xticks(rotation=45)
#plt.legend(loc='upper right', fontsize='large')
#plt.title("")
     plt.legend(loc='best', fontsize='large')
     plt.tight_layout()
     plt.gca().xaxis.set_major_locator(ticker.MaxNLocator(nbins=15))
     plt.gca().yaxis.set_major_locator(ticker.MaxNLocator(nbins=12))
     pdf.savefig(fig16)

     fig17=plt.figure(figsize=(10, 5))
     sns.lineplot(data=plot_df_part,x="fill", y="LVDT_excursion", hue='rp',legend=False)
     sns.scatterplot(data=plot_df_part, x="fill", y="LVDT_excursion", hue='rp', s=12, edgecolor=None, linewidth=0)
     plt.xticks(rotation=45)
#plt.legend(loc='upper right', fontsize='large')
#plt.title("")
     plt.legend(loc='best', fontsize='large')
     plt.tight_layout()
     plt.gca().xaxis.set_major_locator(ticker.MaxNLocator(nbins=15))
     plt.gca().yaxis.set_major_locator(ticker.MaxNLocator(nbins=12))
     pdf.savefig(fig17)

     fig18=plt.figure(figsize=(10, 5))
     sns.lineplot(data=plot_df_part,x="n_bunches", y="LVDT_excursion", hue='rp',legend=False)
     sns.scatterplot(data=plot_df_part, x="n_bunches", y="LVDT_excursion", hue='rp', s=12, edgecolor=None, linewidth=0)
     plt.xticks(rotation=45)
#plt.legend(loc='upper right', fontsize='large')
#plt.title("")
     plt.legend(loc='best', fontsize='large')
     plt.tight_layout()
     pdf.savefig(fig18)


     plot_df_part = plot_df[plot_df['rp'].isin(['56-220-fr-hr', '56-220-cyl-hr', '56-220-nr-hr','56-210-fr-hr'])& 
     (~plot_df['fill'].isin(exclude_fill))]

     fig1=plt.figure(figsize=(10, 5))
     sns.lineplot(data=plot_df_part,x="n_bunches", y="LVDT_excursion", hue='rp',legend=False)
     sns.scatterplot(data=plot_df_part, x="n_bunches", y="LVDT_excursion", hue='rp', s=12, edgecolor=None, linewidth=0)
     plt.xticks(rotation=45)
#plt.legend(loc='upper right', fontsize='large')
#plt.title("")
     plt.legend(loc='best', fontsize='large')
     plt.tight_layout()
     pdf.savefig(fig1)


     fig2=plt.figure(figsize=(10, 5))
     sns.lineplot(data=plot_df_part, x="intensity", y="LVDT_excursion", hue='rp',legend=False)
     sns.scatterplot(data=plot_df_part, x="intensity",y="LVDT_excursion" , hue='rp', s=12, edgecolor=None, linewidth=0)
     plt.xticks(rotation=45)
#plt.legend(loc='upper right', fontsize='large')
#plt.title("")
     plt.legend(loc='best', fontsize='large')
     plt.tight_layout()
     plt.gca().xaxis.set_major_locator(ticker.MaxNLocator(nbins=15))
     plt.gca().yaxis.set_major_locator(ticker.MaxNLocator(nbins=12))
     pdf.savefig(fig2)


     fig3=plt.figure(figsize=(10, 5))
     sns.lineplot(data=plot_df_part,x="fill", y="LVDT_excursion", hue='rp',legend=False)
     sns.scatterplot(data=plot_df_part, x="fill", y="LVDT_excursion", hue='rp', s=12, edgecolor=None, linewidth=0)
     plt.xticks(rotation=45)
#plt.legend(loc='upper right', fontsize='large')
#plt.title("")
     plt.legend(loc='best', fontsize='large')
     plt.tight_layout()
     plt.gca().xaxis.set_major_locator(ticker.MaxNLocator(nbins=15))
     plt.gca().yaxis.set_major_locator(ticker.MaxNLocator(nbins=12))
     pdf.savefig(fig3)



############################################################################################################################


     plot_df_part = plot_df[plot_df['rp'].isin(['45-220-fr-hr', '45-220-cyl-hr', '45-220-nr-hr','45-210-fr-hr'])& 
     (~plot_df['fill'].isin(exclude_fill))]

     fig4=plt.figure(figsize=(10, 5))
     sns.lineplot(data=plot_df_part, x="intensity", y="MEAS_LVDT_LU_initial", hue='rp',legend=False)
     sns.scatterplot(data=plot_df_part, x="intensity",y="MEAS_LVDT_LU_initial" , hue='rp', s=12, edgecolor=None, linewidth=0)
     plt.xticks(rotation=45)
#plt.legend(loc='upper right', fontsize='large')
#plt.title("")
     plt.legend(loc='best', fontsize='large')
     plt.tight_layout()
     plt.gca().xaxis.set_major_locator(ticker.MaxNLocator(nbins=15))
     plt.gca().yaxis.set_major_locator(ticker.MaxNLocator(nbins=12))
     pdf.savefig(fig4)

     fig5=plt.figure(figsize=(10, 5))
     sns.lineplot(data=plot_df_part,x="fill", y="MEAS_LVDT_LU_initial", hue='rp',legend=False)
     sns.scatterplot(data=plot_df_part, x="fill", y="MEAS_LVDT_LU_initial", hue='rp', s=12, edgecolor=None, linewidth=0)
     plt.xticks(rotation=45)
#plt.legend(loc='upper right', fontsize='large')
#plt.title("")
     plt.legend(loc='best', fontsize='large')
     plt.tight_layout()
     plt.gca().xaxis.set_major_locator(ticker.MaxNLocator(nbins=15))
     plt.gca().yaxis.set_major_locator(ticker.MaxNLocator(nbins=12))
     pdf.savefig(fig5)

     fig6=plt.figure(figsize=(10, 5))
     sns.lineplot(data=plot_df_part,x="n_bunches", y="MEAS_LVDT_LU_initial", hue='rp',legend=False)
     sns.scatterplot(data=plot_df_part, x="n_bunches", y="MEAS_LVDT_LU_initial", hue='rp', s=12, edgecolor=None, linewidth=0)
     plt.xticks(rotation=45)
#plt.legend(loc='upper right', fontsize='large')
#plt.title("")
     plt.legend(loc='best', fontsize='large')
     plt.tight_layout()
     pdf.savefig(fig6)



     plot_df_part = plot_df[plot_df['rp'].isin(['56-220-fr-hr', '56-220-cyl-hr', '56-220-nr-hr','56-210-fr-hr'])& 
     (~plot_df['fill'].isin(exclude_fill))]

     fig7=plt.figure(figsize=(10, 5))
     sns.lineplot(data=plot_df_part,x="n_bunches", y="MEAS_LVDT_LU_initial", hue='rp',legend=False)
     sns.scatterplot(data=plot_df_part, x="n_bunches", y="MEAS_LVDT_LU_initial", hue='rp', s=12, edgecolor=None, linewidth=0)
     plt.xticks(rotation=45)
#plt.legend(loc='upper right', fontsize='large')
#plt.title("")
     plt.legend(loc='best', fontsize='large')
     plt.tight_layout()
     pdf.savefig(fig7)



     fig8=plt.figure(figsize=(10, 5))
     sns.lineplot(data=plot_df_part, x="intensity", y="MEAS_LVDT_LU_initial", hue='rp',legend=False)
     sns.scatterplot(data=plot_df_part, x="intensity",y="MEAS_LVDT_LU_initial" , hue='rp', s=12, edgecolor=None, linewidth=0)
     plt.xticks(rotation=45)
#plt.legend(loc='upper right', fontsize='large')
#plt.title("")
     plt.legend(loc='best', fontsize='large')
     plt.tight_layout()
     plt.gca().xaxis.set_major_locator(ticker.MaxNLocator(nbins=15))
     plt.gca().yaxis.set_major_locator(ticker.MaxNLocator(nbins=12))
     pdf.savefig(fig8)



     fig9=plt.figure(figsize=(10, 5))
     sns.lineplot(data=plot_df_part,x="fill", y="MEAS_LVDT_LU_initial", hue='rp',legend=False)
     sns.scatterplot(data=plot_df_part, x="fill", y="MEAS_LVDT_LU_initial", hue='rp', s=12, edgecolor=None, linewidth=0)
     plt.xticks(rotation=45)
#plt.legend(loc='upper right', fontsize='large')
#plt.title("")
     plt.legend(loc='best', fontsize='large')
     plt.tight_layout()
     plt.gca().xaxis.set_major_locator(ticker.MaxNLocator(nbins=15))
     plt.gca().yaxis.set_major_locator(ticker.MaxNLocator(nbins=12))
     pdf.savefig(fig9)




######################################################################################################

     plot_df_part = plot_df[plot_df['rp'].isin(['45-220-fr-hr', '45-220-cyl-hr', '45-220-nr-hr','45-210-fr-hr'])& 
     (~plot_df['fill'].isin(exclude_fill))]

     fig10=plt.figure(figsize=(10, 5))
     sns.lineplot(data=plot_df_part, x="TEMPFLOUT_excursion", y="LVDT_excursion", hue='rp',legend=False)
     sns.scatterplot(data=plot_df_part, x="TEMPFLOUT_excursion", y="LVDT_excursion", hue='rp', s=12, edgecolor=None, linewidth=0)
     plt.xticks(rotation=45)
#plt.legend(loc='upper right', fontsize='large')
#plt.title("")
     plt.legend(loc='best', fontsize='large')
     plt.tight_layout()
     pdf.savefig(fig10)


     fig11=plt.figure(figsize=(10, 5))
     sns.lineplot(data=plot_df_part, x="TEMPFLOUT_excursion", y="MIN_DIST_FROM_WARN_LIMIT", hue='rp',legend=False)
     sns.scatterplot(data=plot_df_part, x="TEMPFLOUT_excursion", y="MIN_DIST_FROM_WARN_LIMIT", hue='rp', s=12, edgecolor=None, linewidth=0)
     plt.xticks(rotation=45)
     plt.legend(loc='best', fontsize='large')
     plt.tight_layout()
     pdf.savefig(fig11)


     fig12=plt.figure(figsize=(10, 5))
     sns.lineplot(data=plot_df_part, x="TEMPFLOUT_first", y="MEAS_LVDT_LU_initial", hue='rp', legend=False)
     sns.scatterplot(data=plot_df_part, x="TEMPFLOUT_first", y="MEAS_LVDT_LU_initial", hue='rp', s=12, edgecolor=None, linewidth=0)
     plt.xticks(rotation=45)
     plt.legend(loc='best', fontsize='large')
     plt.tight_layout()
     pdf.savefig(fig12)




     plot_df_part = plot_df[plot_df['rp'].isin(['56-220-fr-hr', '56-220-cyl-hr', '56-220-nr-hr','56-210-fr-hr'])& 
     (~plot_df['fill'].isin(exclude_fill))]

     fig13=plt.figure(figsize=(10, 5))
     sns.lineplot(data=plot_df_part, x="TEMPFLOUT_excursion", y="LVDT_excursion", hue='rp',legend=False)
     sns.scatterplot(data=plot_df_part, x="TEMPFLOUT_excursion", y="LVDT_excursion", hue='rp', s=12, edgecolor=None, linewidth=0)
     plt.xticks(rotation=45)
#plt.legend(loc='upper right', fontsize='large')
#plt.title("")
     plt.legend(loc='best', fontsize='large')
     plt.tight_layout()
     pdf.savefig(fig13)


     fig14=plt.figure(figsize=(10, 5))
     sns.lineplot(data=plot_df_part, x="TEMPFLOUT_excursion", y="MIN_DIST_FROM_WARN_LIMIT", hue='rp',legend=False)
     sns.scatterplot(data=plot_df_part, x="TEMPFLOUT_excursion", y="MIN_DIST_FROM_WARN_LIMIT", hue='rp', s=12, edgecolor=None, linewidth=0)
     plt.xticks(rotation=45)
     plt.legend(loc='best', fontsize='large')
     plt.tight_layout()
     pdf.savefig(fig14)


     fig15=plt.figure(figsize=(10, 5))
     sns.lineplot(data=plot_df_part, x="TEMPFLOUT_first", y="MEAS_LVDT_LU_initial", hue='rp', legend=False)
     sns.scatterplot(data=plot_df_part, x="TEMPFLOUT_first", y="MEAS_LVDT_LU_initial", hue='rp', s=12, edgecolor=None, linewidth=0)
     plt.xticks(rotation=45)
     plt.legend(loc='best', fontsize='large')
     plt.tight_layout()
     pdf.savefig(fig15)


#plt.xticks(np.arange(start=0, stop=101, step=5)) 



plt.show()

#plt.close('all')

##fill = fill_list[3]
##fill
##get_t2_data_with_caching(variables, fill)
