from datetime import datetime, timedelta
from cycler import cycler
from pprint import pprint
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import pickle
import os
from data_extraction import format_df
import matplotlib.ticker as ticker
from matplotlib.backends.backend_pdf import PdfPages

pd.set_option('display.max_rows', None)     
pd.set_option('display.max_columns', None)  
pd.set_option('display.width', 1000)        


if __name__ == '__main__':
    t3_cache_files = [
        'cache/cached_data_analysis_t3.pkl',
    ]
    
    # Load all listed t3 files and concatenate them
    df_t3 = pd.DataFrame()
    for t3_cache_file in t3_cache_files:
        with open(t3_cache_file, "rb") as f:
            df_t3 = pd.concat([df_t3, pickle.load(f)])
    
    plot_df = format_df(df_t3)
    print(plot_df)

    print('Plotting dataframe structure:')
    print(plot_df.info()) 
    
    with PdfPages('pps-timber-GR1.pdf') as pdf:
    
        # exclude fills in group1 
        exclude_fill = [11475,11477,11479,11505,11510] 

        plot_df_part = plot_df[plot_df['rp'].isin(['45-220-fr-hr', '45-220-cyl-hr', '45-220-nr-hr','45-210-fr-hr'])& 
        (~plot_df['fill'].isin(exclude_fill))]

        fig16=plt.figure(figsize=(10, 5))
        sns.lineplot(data=plot_df_part, x="intensity", y="LVDT_excursion", hue='rp',legend=False)
        sns.scatterplot(data=plot_df_part, x="intensity",y="LVDT_excursion" , hue='rp', s=12, edgecolor=None, linewidth=0)
        plt.xticks(rotation=45)
        # plt.legend(loc='upper right', fontsize='large')
        # plt.title("")
        plt.legend(loc='best', fontsize='large')
        plt.tight_layout()
        plt.gca().xaxis.set_major_locator(ticker.MaxNLocator(nbins=15))
        plt.gca().yaxis.set_major_locator(ticker.MaxNLocator(nbins=12))
        pdf.savefig(fig16)

        fig17=plt.figure(figsize=(10, 5))
        sns.lineplot(data=plot_df_part,x="fill", y="LVDT_excursion", hue='rp',legend=False)
        sns.scatterplot(data=plot_df_part, x="fill", y="LVDT_excursion", hue='rp', s=12, edgecolor=None, linewidth=0)
        plt.xticks(rotation=45)
        # plt.legend(loc='upper right', fontsize='large')
        # plt.title("")
        plt.legend(loc='best', fontsize='large')
        plt.tight_layout()
        plt.gca().xaxis.set_major_locator(ticker.MaxNLocator(nbins=15))
        plt.gca().yaxis.set_major_locator(ticker.MaxNLocator(nbins=12))
        pdf.savefig(fig17)

        fig18=plt.figure(figsize=(10, 5))
        sns.lineplot(data=plot_df_part,x="n_bunches", y="LVDT_excursion", hue='rp',legend=False)
        sns.scatterplot(data=plot_df_part, x="n_bunches", y="LVDT_excursion", hue='rp', s=12, edgecolor=None, linewidth=0)
        plt.xticks(rotation=45)
        # plt.legend(loc='upper right', fontsize='large')
        # plt.title("")
        plt.legend(loc='best', fontsize='large')
        plt.tight_layout()
        pdf.savefig(fig18)


        plot_df_part = plot_df[plot_df['rp'].isin(['56-220-fr-hr', '56-220-cyl-hr', '56-220-nr-hr','56-210-fr-hr'])& 
        (~plot_df['fill'].isin(exclude_fill))]

        fig1=plt.figure(figsize=(10, 5))
        sns.lineplot(data=plot_df_part,x="n_bunches", y="LVDT_excursion", hue='rp',legend=False)
        sns.scatterplot(data=plot_df_part, x="n_bunches", y="LVDT_excursion", hue='rp', s=12, edgecolor=None, linewidth=0)
        plt.xticks(rotation=45)
        # plt.legend(loc='upper right', fontsize='large')
        # plt.title("")
        plt.legend(loc='best', fontsize='large')
        plt.tight_layout()
        pdf.savefig(fig1)


        fig2=plt.figure(figsize=(10, 5))
        sns.lineplot(data=plot_df_part, x="intensity", y="LVDT_excursion", hue='rp',legend=False)
        sns.scatterplot(data=plot_df_part, x="intensity",y="LVDT_excursion" , hue='rp', s=12, edgecolor=None, linewidth=0)
        plt.xticks(rotation=45)
        # plt.legend(loc='upper right', fontsize='large')
        # plt.title("")
        plt.legend(loc='best', fontsize='large')
        plt.tight_layout()
        plt.gca().xaxis.set_major_locator(ticker.MaxNLocator(nbins=15))
        plt.gca().yaxis.set_major_locator(ticker.MaxNLocator(nbins=12))
        pdf.savefig(fig2)


        fig3=plt.figure(figsize=(10, 5))
        sns.lineplot(data=plot_df_part,x="fill", y="LVDT_excursion", hue='rp',legend=False)
        sns.scatterplot(data=plot_df_part, x="fill", y="LVDT_excursion", hue='rp', s=12, edgecolor=None, linewidth=0)
        plt.xticks(rotation=45)
        # plt.legend(loc='upper right', fontsize='large')
        # plt.title("")
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
        # plt.legend(loc='upper right', fontsize='large')
        # plt.title("")
        plt.legend(loc='best', fontsize='large')
        plt.tight_layout()
        plt.gca().xaxis.set_major_locator(ticker.MaxNLocator(nbins=15))
        plt.gca().yaxis.set_major_locator(ticker.MaxNLocator(nbins=12))
        pdf.savefig(fig4)

        fig5=plt.figure(figsize=(10, 5))
        sns.lineplot(data=plot_df_part,x="fill", y="MEAS_LVDT_LU_initial", hue='rp',legend=False)
        sns.scatterplot(data=plot_df_part, x="fill", y="MEAS_LVDT_LU_initial", hue='rp', s=12, edgecolor=None, linewidth=0)
        plt.xticks(rotation=45)
        # plt.legend(loc='upper right', fontsize='large')
        # plt.title("")
        plt.legend(loc='best', fontsize='large')
        plt.tight_layout()
        plt.gca().xaxis.set_major_locator(ticker.MaxNLocator(nbins=15))
        plt.gca().yaxis.set_major_locator(ticker.MaxNLocator(nbins=12))
        pdf.savefig(fig5)

        fig6=plt.figure(figsize=(10, 5))
        sns.lineplot(data=plot_df_part,x="n_bunches", y="MEAS_LVDT_LU_initial", hue='rp',legend=False)
        sns.scatterplot(data=plot_df_part, x="n_bunches", y="MEAS_LVDT_LU_initial", hue='rp', s=12, edgecolor=None, linewidth=0)
        plt.xticks(rotation=45)
        # plt.legend(loc='upper right', fontsize='large')
        # plt.title("")
        plt.legend(loc='best', fontsize='large')
        plt.tight_layout()
        pdf.savefig(fig6)



        plot_df_part = plot_df[plot_df['rp'].isin(['56-220-fr-hr', '56-220-cyl-hr', '56-220-nr-hr','56-210-fr-hr'])& 
        (~plot_df['fill'].isin(exclude_fill))]

        fig7=plt.figure(figsize=(10, 5))
        sns.lineplot(data=plot_df_part,x="n_bunches", y="MEAS_LVDT_LU_initial", hue='rp',legend=False)
        sns.scatterplot(data=plot_df_part, x="n_bunches", y="MEAS_LVDT_LU_initial", hue='rp', s=12, edgecolor=None, linewidth=0)
        plt.xticks(rotation=45)
        # plt.legend(loc='upper right', fontsize='large')
        # plt.title("")
        plt.legend(loc='best', fontsize='large')
        plt.tight_layout()
        pdf.savefig(fig7)



        fig8=plt.figure(figsize=(10, 5))
        sns.lineplot(data=plot_df_part, x="intensity", y="MEAS_LVDT_LU_initial", hue='rp',legend=False)
        sns.scatterplot(data=plot_df_part, x="intensity",y="MEAS_LVDT_LU_initial" , hue='rp', s=12, edgecolor=None, linewidth=0)
        plt.xticks(rotation=45)
        # plt.legend(loc='upper right', fontsize='large')
        # plt.title("")
        plt.legend(loc='best', fontsize='large')
        plt.tight_layout()
        plt.gca().xaxis.set_major_locator(ticker.MaxNLocator(nbins=15))
        plt.gca().yaxis.set_major_locator(ticker.MaxNLocator(nbins=12))
        pdf.savefig(fig8)



        fig9=plt.figure(figsize=(10, 5))
        sns.lineplot(data=plot_df_part,x="fill", y="MEAS_LVDT_LU_initial", hue='rp',legend=False)
        sns.scatterplot(data=plot_df_part, x="fill", y="MEAS_LVDT_LU_initial", hue='rp', s=12, edgecolor=None, linewidth=0)
        plt.xticks(rotation=45)
        # plt.legend(loc='upper right', fontsize='large')
        # plt.title("")
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
        # plt.legend(loc='upper right', fontsize='large')
        # plt.title("")
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
        # plt.legend(loc='upper right', fontsize='large')
        # plt.title("")
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

    plt.show()

    