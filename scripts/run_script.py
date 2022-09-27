"""
Runner for system_simulator.py

Reference from "pysim5g", written by Edward Oughton
GitHub: https://github.com/edwardoughton/pysim5g.git

"""
import os
import sys
import configparser
import csv

import math
import fiona
from shapely.geometry import shape, Point, LineString, mapping
import numpy as np
from random import choice
from rtree import index

from collections import OrderedDict

from pysim5g.generate_hex import produce_sites_and_site_areas
from pysim5g.system_simulator import SimulationManager

np.random.seed(42)

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']


def generate_receivers(site_area, parameters, grid):
    """

    Generate receiver locations as points within the site area.

    Sampling points can either be generated on a grid (grid=1)
    or more efficiently between the transmitter and the edge
    of the site (grid=0) area.

    Parameters
    ----------
    site_area : polygon
        Shape of the site area we want to generate receivers within.
    parameters : dict
        Contains all necessary simulation parameters.
    grid : int
        Binary indicator to dictate receiver generation type.

    Output
    ------
    receivers : List of dicts
        Contains the quantity of desired receivers within the area boundary.

    """
    receivers = []

    if grid == 1:

        geom = shape(site_area[0]['geometry'])
        geom_box = geom.bounds

        minx = geom_box[0]
        miny = geom_box[1]
        maxx = geom_box[2]
        maxy = geom_box[3]

        id_number = 0

        x_axis = np.linspace(
            minx, maxx, num=(
                int(math.sqrt(geom.area) / (math.sqrt(geom.area)/20))
                )
            )
        y_axis = np.linspace(
            miny, maxy, num=(
                int(math.sqrt(geom.area) / (math.sqrt(geom.area)/20))
                )
            )

        xv, yv = np.meshgrid(x_axis, y_axis, sparse=False, indexing='ij')
        for i in range(len(x_axis)):
            for j in range(len(y_axis)):
                receiver = Point((xv[i,j], yv[i,j]))
                indoor_outdoor_probability = np.random.rand(1,1)[0][0]
                if geom.contains(receiver):
                    receivers.append({
                        'type': "Feature",
                        'geometry': {
                            "type": "Point",
                            "coordinates": [xv[i,j], yv[i,j]],
                        },
                        'properties': {
                            'ue_id': "id_{}".format(id_number),
                            "misc_losses": parameters['rx_misc_losses'],
                            "gain": parameters['rx_gain'],
                            "losses": parameters['rx_losses'],
                            "ue_height": float(parameters['rx_height']),
                            "indoor": (True if round(float(indoor_outdoor_probability), 2) < \
                                float(0.80) else False),
                        }
                    })
                    id_number += 1

                else:
                    pass

    else:

        centroid = shape(site_area[0]['geometry']).centroid

        coord = site_area[0]['geometry']['coordinates'][0][0]
        path = LineString([(coord), (centroid)])
        length = int(path.length)
        increment = int(length / 20)

        indoor = parameters['indoor_users_percentage'] / 100

        id_number = 0
        for increment_value in range(1, 11):
            point = path.interpolate(increment * increment_value)
            indoor_outdoor_probability = np.random.rand(1,1)[0][0]
            receivers.append({
                'type': "Feature",
                'geometry': mapping(point),
                'properties': {
                    'ue_id': "id_{}".format(id_number),
                    "misc_losses": parameters['rx_misc_losses'],
                    "gain": parameters['rx_gain'],
                    "losses": parameters['rx_losses'],
                    "ue_height": float(parameters['rx_height']),
                    "indoor": (True if round(float(indoor_outdoor_probability), 2) < \
                        float(indoor) else False),
                }
            })
            id_number += 1

    return receivers


def obtain_percentile_values(results, transmission_type, parameters, confidence_intervals):
    """

    Get the threshold value for a metric based on a given percentiles.

    Parameters
    ----------
    results : list of dicts
        All data returned from the system simulation.

    parameters : dict
        Contains all necessary simulation parameters.

    Output
    ------
    percentile_site_results : dict
        Contains the percentile value for each site metric.

    """
    output = []

    path_loss_values = []
    received_power_values = []
    interference_values = []
    sinr_values = []
    spectral_efficiency_values = []
    estimated_capacity_values = []
    estimated_capacity_values_km2 = []

    for result in results:

        path_loss_values.append(result['path_loss'])

        received_power_values.append(result['received_power'])

        interference_values.append(result['interference'])

        sinr = result['sinr']
        if sinr == None:
            sinr = 0
        else:
            sinr_values.append(sinr)

        spectral_efficiency = result['spectral_efficiency']
        if spectral_efficiency == None:
            spectral_efficiency = 0
        else:
            spectral_efficiency_values.append(spectral_efficiency)

        estimated_capacity = result['capacity_mbps']
        if estimated_capacity == None:
            estimated_capacity = 0
        else:
            estimated_capacity_values.append(estimated_capacity)

        estimated_capacity_km2 = result['capacity_mbps_km2']
        if estimated_capacity_km2 == None:
            estimated_capacity_km2 = 0
        else:
            estimated_capacity_values_km2.append(estimated_capacity_km2)

    for confidence_interval in confidence_intervals:

        output.append({
            'confidence_interval': confidence_interval,
            'tranmission_type': transmission_type,
            'path_loss': np.percentile(
                path_loss_values, confidence_interval #<- low path loss is better
            ),
            'received_power': np.percentile(
                received_power_values, 100 - confidence_interval
            ),
            'interference': np.percentile(
                interference_values, confidence_interval #<- low interference is better
            ),
            'sinr': np.percentile(
                sinr_values, 100 - confidence_interval
            ),
            'spectral_efficiency': np.percentile(
                spectral_efficiency_values, 100 - confidence_interval
            ),
            'capacity_mbps': np.percentile(
                estimated_capacity_values, 100 - confidence_interval
            ),
            'capacity_mbps_km2': np.percentile(
                estimated_capacity_values_km2, 100 - confidence_interval
            )
        })

    return output


def obtain_threshold_values_choice(results, parameters):
    """

    Get the threshold capacity based on a given percentile.

    Parameters
    ----------
    results : list of dicts
        All data returned from the system simulation.
    parameters : dict
        Contains all necessary simulation parameters.

    Output
    ------
    matching_result : float
        Contains the chosen percentile value based on the input data.

    """
    sinr_values = []

    percentile = parameters['percentile']

    for result in results:

        sinr = result['sinr']

        if sinr == None:
            pass
        else:
            sinr_values.append(sinr)

    sinr = np.percentile(sinr_values, percentile, interpolation='nearest')

    matching_result = []

    for result in results:
        if float(result['sinr']) == float(sinr):
            matching_result.append(result)

    return float(choice(matching_result))


def convert_results_geojson(data):
    """

    Convert results to geojson format, for writing to shapefile.

    Parameters
    ----------
    data : list of dicts
        Contains all results ready to be written.

    Outputs
    -------
    output : list of dicts
        A list of geojson dictionaries ready for writing.

    """
    output = []

    for datum in data:
        output.append({
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [
                    datum['receiver_x'], datum['receiver_y']]
                },
            'properties': {
                'path_loss': float(datum['path_loss']),
                'received_power': float(datum['received_power']),
                'interference': float(datum['interference']),
                'noise': float(datum['noise']),
                'sinr': float(datum['sinr']),
                'spectral_efficiency': float(
                    datum['spectral_efficiency']
                ),
                'capacity_mbps': float(
                    datum['capacity_mbps']
                ),
                'capacity_mbps_km2': float(
                    datum['capacity_mbps_km2']
                ),
                },
            }
        )

    return output


def write_full_results(data, environment, site_radius, frequency,
    bandwidth, generation, ant_type, transmittion_type, directory,
    filename, parameters):
    """

    Write full results data to .csv.

    Parameters
    ----------
    data : list of dicts
        Contains all results ready to be written.
    environment : string
        Either urban, suburban or rural clutter type.
    site_radius : int
        Radius of site area in meters.
    frequency : float
        Spectral frequency of carrier band in GHz.
    bandwidth : int
        Channel bandwidth of carrier band in MHz.
    generation : string
        Either 4G or 5G depending on technology generation.
    ant_type : string
        The type of transmitter modelled (macro, micro etc.).
    tranmission_type : string
        The type of tranmission (SISO, MIMO 4x4, MIMO 8x8 etc.).
    directory : string
        Folder the data will be written to.
    filename : string
        Name of the .csv file.
    parameters : dict
        Contains all necessary simulation parameters.

    """
    sectors = parameters['sectorization']
    inter_site_distance = site_radius * 2
    site_area_km2 = (
        math.sqrt(3) / 2 * inter_site_distance ** 2 / 1e6
    )
    sites_per_km2 = 1 / site_area_km2

    if not os.path.exists(directory):
        os.makedirs(directory)

    full_path = os.path.join(directory, filename)

    results_file = open(full_path, 'w', newline='')
    results_writer = csv.writer(results_file)
    results_writer.writerow(
        (
            'environment',
            'inter_site_distance_m',
            'sites_per_km2',
            'frequency_GHz',
            'bandwidth_MHz',
            'number_of_sectors',
            'generation',
            'ant_type',
            'transmittion_type',
            'receiver_x',
            'receiver_y',
            'r_distance',
            'path_loss_dB',
            'r_model',
            'received_power_dB',
            'interference_dB',
            'i_model',
            'noise_dB',
            'sinr_dB',
            'spectral_efficiency_bps_hz',
            'capacity_mbps',
            'capacity_mbps_km2'
        )
    )

    for row in data:
        results_writer.writerow((
            environment,
            inter_site_distance,
            sites_per_km2,
            frequency,
            bandwidth,
            sectors,
            generation,
            ant_type,
            transmittion_type,
            row['receiver_x'],
            row['receiver_y'],
            row['distance'],
            row['path_loss'],
            row['r_model'],
            row['received_power'],
            row['interference'],
            row['i_model'],
            row['noise'],
            row['sinr'],
            row['spectral_efficiency'],
            row['capacity_mbps'],
            row['capacity_mbps_km2'],
            ))


def write_frequency_lookup_table(results, environment, site_radius,
    frequency, bandwidth, generation, ant_type, tranmission_type,
    directory, filename, parameters):
    """

    Write the main, comprehensive lookup table for all environments,
    site radii, frequencies etc.

    Parameters
    ----------
    results : list of dicts
        Contains all results ready to be written.
    environment : string
        Either urban, suburban or rural clutter type.
    site_radius : int
        Radius of site area in meters.
    frequency : float
        Spectral frequency of carrier band in GHz.
    bandwidth : int
        Channel bandwidth of carrier band in MHz.
    generation : string
        Either 4G or 5G depending on technology generation.
    ant_type : string
        Type of transmitters modelled.
    tranmission_type : string
        The transmission type (SISO, MIMO etc.).
    directory : string
        Folder the data will be written to.
    filename : string
        Name of the .csv file.
    parameters : dict
        Contains all necessary simulation parameters.

    """
    inter_site_distance = site_radius * 2
    site_area_km2 = math.sqrt(3) / 2 * inter_site_distance ** 2 / 1e6
    sites_per_km2 = 1 / site_area_km2

    sectors = parameters['sectorization']

    if not os.path.exists(directory):
        os.makedirs(directory)

    directory = os.path.join(directory, filename)

    if not os.path.exists(directory):
        lut_file = open(directory, 'w', newline='')
        lut_writer = csv.writer(lut_file)
        lut_writer.writerow(
            (
                'confidence_interval',
                'environment',
                'inter_site_distance_m',
                'site_area_km2',
                'sites_per_km2',
                'frequency_GHz',
                'bandwidth_MHz',
                'number_of_sectors',
                'generation',
                'ant_type',
                'transmission_type',
                'path_loss_dB',
                'received_power_dBm',
                'interference_dBm',
                'sinr_dB',
                'spectral_efficiency_bps_hz',
                'capacity_mbps',
                'capacity_mbps_km2',
            )
        )
    else:
        lut_file = open(directory, 'a', newline='')
        lut_writer = csv.writer(lut_file)

    for result in results:
        lut_writer.writerow(
            (
                result['confidence_interval'],
                environment,
                inter_site_distance,
                site_area_km2,
                sites_per_km2,
                frequency,
                bandwidth,
                sectors,
                generation,
                ant_type,
                tranmission_type,
                result['path_loss'],
                result['received_power'],
                result['interference'],
                result['sinr'],
                result['spectral_efficiency'],
                result['capacity_mbps'],
                result['capacity_mbps_km2'] * sectors,
            )
        )

    lut_file.close()



def write_shapefile(data, directory, filename, crs):
    """

    Write geojson data to shapefile.

    """
    prop_schema = []
    for name, value in data[0]['properties'].items():
        fiona_prop_type = next((
            fiona_type for fiona_type, python_type in \
                fiona.FIELD_TYPES_MAP.items() if \
                python_type == type(value)), None
            )

        prop_schema.append((name, fiona_prop_type))

    sink_driver = 'ESRI Shapefile'
    sink_crs = {'init': crs}
    sink_schema = {
        'geometry': data[0]['geometry']['type'],
        'properties': OrderedDict(prop_schema)
    }

    if not os.path.exists(directory):
        os.makedirs(directory)

    with fiona.open(
        os.path.join(directory, filename), 'w',
        driver=sink_driver, crs=sink_crs, schema=sink_schema) as sink:
        for datum in data:
            sink.write(datum)


def run_simulator(parameters, spectrum_portfolio, ant_types,
    site_radii, modulation_and_coding_lut, confidence_intervals):
    """

    Function to run the simulator and all associated modules.

    """
    unprojected_point = {
        'type': 'Feature',
        'geometry': {
            'type': 'Point',
            'coordinates': (106.6630555,10.7724298),
            },
        'properties': {
            'site_id': 'HCMUT Tower'
            }
        }

    unprojected_crs = 'epsg:4326'
    projected_crs = 'epsg:3857'

    environments =[
        'urban',
#        'suburban',
#        'rural'
    ]

    for environment in environments:
        for ant_type in ant_types:
            site_radii_generator = site_radii[ant_type]
            for site_radius in site_radii_generator[environment]:

                if environment == 'urban' and site_radius > 5000:
                    continue
                if environment == 'suburban' and site_radius > 15000:
                    continue

                print('--working on {}: {}'.format(environment, site_radius))

                transmitter, interfering_transmitters, site_area, interfering_site_areas = \
                    produce_sites_and_site_areas(
                        unprojected_point['geometry']['coordinates'],
                        site_radius,
                        unprojected_crs,
                        projected_crs
                        )

                receivers = generate_receivers(site_area, PARAMETERS, 1)

                for frequency, bandwidth, generation, transmission_type in spectrum_portfolio:

                    print('{}, {}, {}, {}'.format(frequency, bandwidth, generation, transmission_type))

                    MANAGER = SimulationManager(
                        transmitter, interfering_transmitters, ant_type,
                        receivers, site_area, PARAMETERS
                        )

                    results = MANAGER.estimate_link_budget(
                        frequency,
                        bandwidth,
                        generation,
                        ant_type,
                        transmission_type,
                        environment,
                        modulation_and_coding_lut,
                        parameters
                        )

                    folder = os.path.join(BASE_PATH, '..', 'results', 'full_tables')
                    filename = 'full_capacity_lut_{}_{}_{}_{}_{}.csv'.format(
                        environment, site_radius, frequency, ant_type, transmission_type)

                    write_full_results(results, environment, site_radius,
                        frequency, bandwidth, generation, ant_type, transmission_type,
                        folder, filename, parameters)

                    percentile_site_results = obtain_percentile_values(
                        results, transmission_type, parameters, confidence_intervals
                    )

                    results_directory = os.path.join(BASE_PATH, '..', 'results')
                    write_frequency_lookup_table(percentile_site_results, environment,
                        site_radius, frequency, bandwidth, generation,
                        ant_type, transmission_type, results_directory,
                        'capacity_lut_by_frequency.csv', parameters
                    )


                    geojson_receivers = convert_results_geojson(results)

                    write_shapefile(
                        geojson_receivers, os.path.join(results_directory, 'shapes'),
                        'receivers_{}.shp'.format(site_radius),
                        projected_crs
                        )

                    write_shapefile(
                        transmitter, os.path.join(results_directory, 'shapes'),
                        'transmitter_{}.shp'.format(site_radius),
                        projected_crs
                    )

                    write_shapefile(
                        site_area, os.path.join(results_directory, 'shapes'),
                        'site_area_{}.shp'.format(site_radius),
                        projected_crs
                    )

                    write_shapefile(
                        interfering_transmitters, os.path.join(results_directory, 'shapes'),
                        'interfering_transmitters_{}.shp'.format(site_radius),
                        projected_crs
                    )

                    write_shapefile(
                        interfering_site_areas, os.path.join(results_directory, 'shapes'),
                        'interfering_site_areas_{}.shp'.format(site_radius),
                        projected_crs
                    )



if __name__ == '__main__':

    PARAMETERS = {
        'iterations': 1000,
        'seed_value1': 1,
        'seed_value2': 2,
        'indoor_users_percentage': 80,
        'los_breakpoint_m': 500,
        'tx_macro_baseline_height': 30,
        'tx_macro_power': 40,
        'tx_macro_gain': 16,
        'tx_macro_losses': 1,
        'tx_micro_baseline_height': 10,
        'tx_micro_power': 24,
        'tx_micro_gain': 5,
        'tx_micro_losses': 1,
        'rx_gain': 4,
        'rx_losses': 4,
        'rx_misc_losses': 4,
        'rx_height': 1.5,
        'building_height': 5,
        'street_width': 20,
        'above_roof': 0,
        'network_load': 50,
#        'percentile': 50,      #Replaced by confidence_intervals [5, 50, 95] (%)
        'sectorization': 3,
    }


# 4G: Band 7: UL (2500 MHz - 2570 MHz)
#             DL (2620 MHz - 2690 MHz)
#     Bandwidth (MHz): 5, 10, 15, 20
# 5G (Rel 17): Band n78 (3.3 GHz - 3.8 GHz) - the most popular frequency band used in 5G
#     Total BW: 500 MHz
#     Channel BW (MHz): 10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100 MHz
    SPECTRUM_PORTFOLIO = [
#        (2.63, 20, '4G', '1x1'),
        (2.65, 20, '4G', '1x1'),
#        (2.68, 20, '4G', '1x1'),
        (3.3, 40, '5G', '8x8'),
#        (3.5, 40, '5G', '8x8'),
#        (3.7, 40, '5G', '8x8'),
    ]

    ANT_TYPE = [
#        ('macro'),
        ('micro'),
    ]

    MODULATION_AND_CODING_LUT =[
        # 3GPP TS 38.214 Version 17.2.0; NR; Physical layer procedures for data (Release 17)
        # Generation, MIMO, CQI Index,	Modulation,	Coding rate,
        # Spectral efficiency (bps/Hz), SINR estimate (dB)
        ('4G', '1x1', 1, 'QPSK', 78, 0.1523, -6.7),
        ('4G', '1x1', 2, 'QPSK', 120, 0.2344, -4.7),
        ('4G', '1x1', 3, 'QPSK', 193, 0.377, -2.3),
        ('4G', '1x1', 4, 'QPSK', 308, 0.6016, 0.2),
        ('4G', '1x1', 5, 'QPSK', 449, 0.877, 2.4),
        ('4G', '1x1', 6, 'QPSK', 602, 1.1758, 4.3),
        ('4G', '1x1', 7, '16QAM', 378, 1.4766, 5.9),
        ('4G', '1x1', 8, '16QAM', 490, 1.9141, 8.1),
        ('4G', '1x1', 9, '16QAM', 616, 2.4063, 10.3),
        ('4G', '1x1', 10, '64QAM', 466, 2.7305, 11.7),
        ('4G', '1x1', 11, '64QAM', 567, 3.3223, 14.1),
        ('4G', '1x1', 12, '64QAM', 666, 3.9023, 16.3),
        ('4G', '1x1', 13, '64QAM', 772, 4.5234, 18.7),
        ('4G', '1x1', 14, '64QAM', 873, 5.1152, 21),
        ('4G', '1x1', 15, '64QAM', 948, 5.5547, 22.7),
        ('5G', '8x8', 1, 'QPSK', 78, 0.30, -6.7),
        ('5G', '8x8', 2, 'QPSK', 193, 2.05, -4.7),
        ('5G', '8x8', 3, 'QPSK', 449, 4.42, -2.3),
        ('5G', '8x8', 4, '16QAM', 378, 6.40, 0.2),
        ('5G', '8x8', 5, '16QAM', 490, 8.00, 2.4),
        ('5G', '8x8', 6, '16QAM', 616, 10.82, 4.3),
        ('5G', '8x8', 7, '64QAM', 466, 12.40, 5.9),
        ('5G', '8x8', 8, '64QAM', 567, 16.00, 8.1),
        ('5G', '8x8', 9, '64QAM', 666, 19.00, 10.3),
        ('5G', '8x8', 10, '64QAM', 772, 22.00, 11.7),
        ('5G', '8x8', 11, '64QAM', 873, 28.00, 14.1),
        ('5G', '8x8', 12, '256QAM', 711, 32.00, 16.3),
        ('5G', '8x8', 13, '256QAM', 797, 38.00, 18.7),
        ('5G', '8x8', 14, '256QAM', 885, 44.00, 21),
        ('5G', '8x8', 15, '256QAM', 948, 50.00, 22.7),
    ]

    CONFIDENCE_INTERVALS = [
        5,
        50,
        95,
    ]

    def generate_site_radii(min, max, increment):
        for n in range(min, max, increment):
            yield n

    #INCREMENT_MA = (400, 30400, 1000)
    #INCREMENT_MI = (40, 540, 80)
    INCREMENT_MA = (500, 30500, 500)
    INCREMENT_MI = (40, 540, 50)

    SITE_RADII = {
        'macro': {
            'urban':
                generate_site_radii(INCREMENT_MA[0],INCREMENT_MA[1],INCREMENT_MA[2]),
            'suburban':
                generate_site_radii(INCREMENT_MA[0],INCREMENT_MA[1],INCREMENT_MA[2]),
            'rural':
                generate_site_radii(INCREMENT_MA[0],INCREMENT_MA[1],INCREMENT_MA[2])
            },
        'micro': {
            'urban':
                generate_site_radii(INCREMENT_MI[0],INCREMENT_MI[1],INCREMENT_MI[2]),
            'suburban':
                generate_site_radii(INCREMENT_MI[0],INCREMENT_MI[1],INCREMENT_MI[2]),
            'rural':
                generate_site_radii(INCREMENT_MI[0],INCREMENT_MI[1],INCREMENT_MI[2])
            },
        }

    run_simulator(
        PARAMETERS,
        SPECTRUM_PORTFOLIO,
        ANT_TYPE,
        SITE_RADII,
        MODULATION_AND_CODING_LUT,
        CONFIDENCE_INTERVALS
        )
