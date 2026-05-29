from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import pytimber
import pickle
import os

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

def get_t1_data_with_caching(variables, 
                             fillInterval, 
                             cache_file_path='cache/cached_data_analysis_{fill_to_analyze}_t1.pkl', 
                             ldb=None):
    """Tier 1 - sample with all variables"""
    
    if ldb is None:
        ldb = pytimber.LoggingDB(source="nxcals")
    
    fill_to_analyze = fillInterval.fillNumber
    fill_to_analyze_sb_start = datetime.fromtimestamp(fillInterval.modeFirstAttribute)
    fill_to_analyze_sb_end = datetime.fromtimestamp(fillInterval.modeSecondAttribute)

    try:
        with open(cache_file_path.format(fill_to_analyze=fill_to_analyze), "rb") as f:
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
                
                with open(cache_file_path.format(fill_to_analyze=fill_to_analyze), "wb") as f:
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
        with open(cache_file_path.format(fill_to_analyze=fill_to_analyze), "wb") as f:
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

def get_t2_data_with_caching(variables, 
                             fillInterval, 
                             no_remove_t1=False, 
                             t1_cache_path='cache/cached_data_analysis_{fill_to_analyze}_t1.pkl',
                             t2_cache_path='cache/cached_data_analysis_{fill_to_analyze}_t2.pkl',
                             ldb=None):
    """
    Drop all data with all the *MEAS_LVDT_LU larger than 5
    Create a new df for that
    """
    if ldb is None:
        ldb = pytimber.LoggingDB(source="nxcals")
    
    cache_path = t2_cache_path.format(fill_to_analyze=fillInterval.fillNumber)

    if os.path.exists(cache_path):
        df_t2 = pd.read_pickle(cache_path)
        print(f"Loaded df_t2 from {cache_path}")
    else:
        # Get the t1 data for the fill
        df_t1 = get_t1_data_with_caching(variables, fillInterval, t1_cache_path, ldb)
        df_t2 = df_t1.copy()
        df_t2.to_pickle(cache_path)
        print(f"Cached df_t2 to {cache_path}")
        if not no_remove_t1:
            # Delete t1 cache
            t1_cache_path = t1_cache_path.format(fill_to_analyze=fillInterval.fillNumber)
            if os.path.exists(t1_cache_path):
                os.remove(t1_cache_path)

    meas_limit_cols = df_t2.filter(regex="MEAS_LVDT_LU")
    mask = (meas_limit_cols > 3).all(axis=1)
    df_t2 = df_t2[~mask]

    df_t2["data_tier"] = "Tier 2"
    return df_t2

def make_t3_data(df_t2, 
                 t2_cache_path='cache/cached_data_analysis_{fill_to_analyze}_t2.pkl'):
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
    
    return df_t3

def get_t3_data_with_caching(variables, 
                             fill_list, 
                             no_remove_t1=False,
                             no_remove_t2=False,
                             t1_cache_path='cache/cached_data_analysis_{fill_to_analyze}_t1.pkl',
                             t2_cache_path='cache/cached_data_analysis_{fill_to_analyze}_t2.pkl',
                             t3_cache_path='cache/cached_data_analysis_t3.pkl',
                             ldb=None):
    
    if ldb is None:
        ldb = pytimber.LoggingDB(source="nxcals")
    
    # Divide the fills in groups of five
    fill_groups = [fill_list[i:i+5] for i in range(0, len(fill_list), 5)]
    df_t3 = pd.DataFrame()

    if os.path.exists(t3_cache_path):
        with open(t3_cache_path, "rb") as f:
            print("Using cached t3 data")
            df_t3 = pickle.load(f)
    else:
        for group in fill_groups:
            # Dataframe to store t2 data for the group
            df_t2 = pd.DataFrame()
            for fill in group:
                print(f"Processing fill {fill.fillNumber}...")
                # Get the t2 data for the fill
                df_t2 = pd.concat([df_t2,get_t2_data_with_caching(variables, fill, 
                                                                  no_remove_t1=no_remove_t1, 
                                                                  t1_cache_path=t1_cache_path, 
                                                                  t2_cache_path=t2_cache_path, 
                                                                  ldb=ldb)])

            # Generate the t3 data for this group of fills
            df_t3 = pd.concat([df_t3,make_t3_data(df_t2, t2_cache_path=t2_cache_path)])
            if not no_remove_t2:
                for fill in group:
                    # Delete t2 cache
                    t2_cache_path_file = t2_cache_path.format(fill_to_analyze=fill.fillNumber)
                    print(f"Removing {t2_cache_path_file}")
                    os.remove(t2_cache_path_file)
        with open(t3_cache_path, "wb") as f:
            pickle.dump(df_t3, f)
    return df_t3

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

if __name__ == '__main__':
    
    t_end = datetime(2026, 3, 28, 10, 0, 0) # End time is current time minus 5 minutes to ensure data availability
    t_start = datetime(2026, 3, 7, 10, 0, 0)
    
    t3_cache_output = 'cache/cached_data_analysis_t3.pkl'

    os.makedirs("cache", exist_ok=True)
    
    # Create LoggingDB object
    ldb = pytimber.LoggingDB(source="nxcals")

    fill_list = ldb.get_interval_by_lhc_modes(t_start, t_end, mode1='STABLE', mode2='STABLE')

    print('Fills to process:')
    for fill in fill_list:
        sb_start = datetime.fromtimestamp(fill.modeFirstAttribute)
        sb_end = datetime.fromtimestamp(fill.modeSecondAttribute)
        n = fill.fillNumber
        print(f"\tFill {n} has SB from {sb_start} to {sb_end}")
        
    df_t3 = get_t3_data_with_caching(variables, fill_list, no_remove_t2=False, t3_cache_path=t3_cache_output, ldb=ldb)
    
    print('Extracted Tier 3 dataframe structure:')
    print(df_t3.info())
    print('Dataframe saved to file: ', t3_cache_output)
