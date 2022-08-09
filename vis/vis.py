import os
import configparser
import sys
import glob
import csv
import pprint
import matplotlib
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from  matplotlib.ticker import FuncFormatter

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__),'..','scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA = os.path.join(BASE_PATH, '..', 'results')
DATA_OUTPUT = os.path.join(BASE_PATH, '..', 'vis', 'outputs')


if not os.path.exists(DATA_OUTPUT):
    os.mkdir(DATA_OUTPUT)


def load_in_all_main_lut(max_isd_distance):

    filenames = glob.iglob(os.path.join(DATA, 'full_tables', 'full_capacity_lut_urban*'))

    output = pd.concat((pd.read_csv(f) for f in filenames))

    output['capacity_per_Hz_km2'] = (
        output['capacity_mbps_km2'] / (output['bandwidth_MHz'] * 1e6)
        )

    output['sites_per_km2'] = output.sites_per_km2.round(1)

    output['inter_site_distance_km'] = output['inter_site_distance_m'] / 1e3

    output = output.replace(
        {
            'environment':{
                'urban': 'Urban',
                'suburban': 'Suburban',
                'rural': 'Rural',
            }
        }
    )

    output = output.reset_index().reset_index(drop=True)

    ISD = output.inter_site_distance_km.astype(int) < max_isd_distance
    output = output[ISD]

    return output


def plotting_function1_isd(data):

    data_subset = data[['inter_site_distance_km','frequency_GHz','path_loss_dB',
    'received_power_dB', 'interference_dB', 'sinr_dB', 'spectral_efficiency_bps_hz',
    'capacity_mbps_km2']]

    data_subset.columns = ['Inter-Site Distance (km)', 'Frequency (GHz)', 'Path Loss',
        'Received Power', 'Interference', 'SINR', 'SE',
        'Channel Capacity']

    long_data = pd.melt(data_subset,
        id_vars=['Inter-Site Distance (km)', 'Frequency (GHz)'],
        value_vars=['Path Loss', 'Received Power', 'Interference',
            'SINR', 'SE', 'Channel Capacity'])

    long_data.columns = ['Inter-Site Distance (km)', 'Frequency (GHz)',
        'Metric', 'Value']

    sns.set(font_scale=1.1)

#    long_data['Inter-Site Distance (km)'] = round(long_data['Inter-Site Distance (km)'], 3)
#    bins = [0, 1, 2, 3, 4, 5]
#    long_data['ISD_binned'] = pd.cut(long_data['Inter-Site Distance (km)'], bins, labels=["1", "2", "3", "4", "5"])

    plot = sns.relplot(x='Inter-Site Distance (km)', y='Value', hue="Frequency (GHz)",
        col="Metric", col_wrap=2, palette=sns.color_palette("husl", 6),
        kind="line", data=long_data,
        facet_kws=dict(sharex=False, sharey=False),
        legend="full")

    handles = plot._legend_data.values()
    labels = plot._legend_data.keys()
    plot._legend.remove()
    plot.fig.legend(handles=handles, labels=labels, loc='lower center', ncol=7)

    plot.axes[0].set_ylabel('Path Loss (dB)')
    plot.axes[1].set_ylabel('Received Power (dBm)')
    plot.axes[2].set_ylabel('Interference (dBm)')
    plot.axes[3].set_ylabel('SINR (dB)')
    plot.axes[4].set_ylabel('SE (Bps/Hz)')
    plot.axes[5].set_ylabel('Capacity (Mbps km^2)')

    plot.axes[0].set_xlabel('Inter-Site Distance (km)')
    plot.axes[1].set_xlabel('Inter-Site Distance (km)')
    plot.axes[2].set_xlabel('Inter-Site Distance (km)')
    plot.axes[3].set_xlabel('Inter-Site Distance (km)')
    plot.axes[4].set_xlabel('Inter-Site Distance (km)')
    plot.axes[5].set_xlabel('Inter-Site Distance (km)')

    plt.subplots_adjust(hspace=0.3, wspace=0.3, bottom=0.07)

    plot.savefig(DATA_OUTPUT + '/frequency_capacity_lineplot_isd.png', dpi=300)

    return print('completed (frequency) lineplot (isd)')



def load_in_all_main_lut_specific(max_isd_distance):

    filenames = glob.iglob(os.path.join(DATA, 'full_tables', 'full_capacity_lut_urban_290*'))

    output = pd.concat((pd.read_csv(f) for f in filenames))

    output['capacity_per_Hz_km2'] = (
        output['capacity_mbps_km2'] / (output['bandwidth_MHz'] * 1e6)
        )

    output['sites_per_km2'] = output.sites_per_km2.round(1)

    output['inter_site_distance_km'] = output['inter_site_distance_m'] / 1e3

    output = output.replace(
        {
            'environment':{
                'urban': 'Urban',
                'suburban': 'Suburban',
                'rural': 'Rural',
            }
        }
    )

    output = output.reset_index().reset_index(drop=True)

    ISD = output.inter_site_distance_km.astype(int) < max_isd_distance
    output = output[ISD]

    return output

def plotting_function2_isd(data):

    data_subset = data[['inter_site_distance_km','frequency_GHz','path_loss_dB',
    'received_power_dB', 'interference_dB', 'sinr_dB', 'spectral_efficiency_bps_hz',
    'capacity_mbps_km2']]

    data_subset.columns = ['Inter-Site Distance (km)', 'Frequency (GHz)', 'Path Loss',
        'Received Power', 'Interference', 'SINR', 'SE',
        'Channel Capacity']

    long_data = pd.melt(data_subset,
        id_vars=['Inter-Site Distance (km)', 'Frequency (GHz)'],
        value_vars=['Path Loss', 'Received Power', 'Interference',
            'SINR', 'SE', 'Channel Capacity'])

    long_data.columns = ['Inter-Site Distance (km)', 'Frequency (GHz)',
        'Metric', 'Value']

    sns.set(font_scale=1.1)

    plot = sns.catplot(x="Inter-Site Distance (km)", y='Value', hue="Frequency (GHz)",
        col="Metric", col_wrap=2,
        kind="bar",
        data=long_data,
        palette=sns.color_palette("husl", 6),
        sharex=False,
        sharey=False,
        legend="full")

    handles = plot._legend_data.values()
    labels = plot._legend_data.keys()
    plot._legend.remove()
    plot.fig.legend(handles=handles, labels=labels, loc='lower center', ncol=7)

    plot.axes[0].set_ylabel('Path Loss (dB)')
    plot.axes[1].set_ylabel('Received Power (dBm)')
    plot.axes[2].set_ylabel('Interference (dBm)')
    plot.axes[3].set_ylabel('SINR (dB)')
    plot.axes[4].set_ylabel('SE (Bps/Hz)')
    plot.axes[5].set_ylabel('Capacity (Mbps km^2)')

    plot.axes[0].set_xlabel('Inter-Site Distance (km)')
    plot.axes[1].set_xlabel('Inter-Site Distance (km)')
    plot.axes[2].set_xlabel('Inter-Site Distance (km)')
    plot.axes[3].set_xlabel('Inter-Site Distance (km)')
    plot.axes[4].set_xlabel('Inter-Site Distance (km)')
    plot.axes[5].set_xlabel('Inter-Site Distance (km)')

    plt.subplots_adjust(hspace=0.3, wspace=0.3, bottom=0.07)

    plot.savefig(DATA_OUTPUT + '/frequency_capacity_barplot_isd_specific.png', dpi=300)

    return print('completed (frequency) barplot (isd) -specific')


def csv_writer(data, directory, filename):
    """
    Write data to a CSV file path
    """
    # Create path
    if not os.path.exists(directory):
        os.makedirs(directory)

    fieldnames = []
    for name, value in data[0].items():
        fieldnames.append(name)

    with open(os.path.join(directory, filename), 'w') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames, lineterminator = '\n')
        writer.writeheader()
        writer.writerows(data)


if __name__ == '__main__':

    max_isd_distance = 5

    data = load_in_all_main_lut(max_isd_distance)

#    csv_writer(data, './vis/LUT', 'LUT_sum')

#    print(data)

    plotting_function1_isd(data)

    specific_data = load_in_all_main_lut_specific(max_isd_distance)

    plotting_function2_isd(specific_data)

