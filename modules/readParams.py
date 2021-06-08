# %%
import os
from dataclasses import dataclass
from typing import Dict
import numpy as np
import xlrd

# %% ~~~~~~~~~~~~~~~~~~~~~~~~~~ Part 1: Data Classes ~~~~~~~~~~~~~~~~~~~~~
@dataclass
class sim_param:
    replications: int
    duration: int
    warm_up: int
@dataclass
class arr_cap_param:
    initial_wait_list: int
    arrival_rate: float
    service_time: float
    capacity: int
@dataclass
class scan_res_param:
    result_types: list
    result_distribution: list
    negative_bulk: float
    suspicious_biopsy: float
    negatives_to_leave: int
    delay_distribution: dict
@dataclass
class biopsy_res_param:
    cancer_chance: dict
    cancer_types: list
    cancer_staging: list
    growth_rate: list
    growth_interval: int

# Input Parameters
@dataclass
class input_param:
    directory: str = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    
    # Simulation Hyper Params
    simParams: sim_param = sim_param(30, 50, 150)
    # Arrival and Capacity
    arrParams: arr_cap_param = arr_cap_param(0, 25, (15/60)/24, 1)
    # Scan Result Distribution Data
    scanResParams: scan_res_param = scan_res_param(
        ['Negative', 'Suspicious', 'Positive'],
        [0.85, 0.13, 0.02],
        0.91,
        0.62,
        2,
        {
            'Negative': {'Delay Prob': [1], 'Delay Numb': [360]},
            'Suspicious': {'Delay Prob': [0.625, 1], 'Delay Numb': [180, 90]}
        }
    )
    # Biopsy Result Data
    biopsyResParams: biopsy_res_param = biopsy_res_param(
        {'Suspicious': 0.75, 'Positive': 0.85},
        ['Stage_1', 'Stage_2', 'Stage_3', 'Stage_4'],
        [0.63, 0.07, 0.15, 0.15],
        [1, 1, 1.25, 1.5],
        180
    )
    # Schedule Data
    schedule = [
            [8,8,8],
            [8,8,8],
            [8,8,8],
            [8,8,8],
            [8,8,8],
            [24],
            [24]
    ]

# %% ~~~~~~~~~~~~~~~~~~~~~~~~~~ Part 2: Read Params ~~~~~~~~~~~~~~~~~~~~~
def readParameters(string_path, input_param):
    book = xlrd.open_workbook(f"{string_path}")

    # Relevant Sheets
    gen_sheet = book.sheet_by_name("General Parameters")
    dist_sheet = book.sheet_by_name("Distributions")
    sus_delay_sheet = book.sheet_by_name("Suspicious Delay Distribution")
    neg_delay_sheet = book.sheet_by_name("Negative Delay Distribution")
    schedule_sheet = book.sheet_by_name("Schedules Data")
    cancer_sheet = book.sheet_by_name("Cancer Distribution")

    # Hyper Params
    input_param.simParams.replications = int(gen_sheet.cell_value(1,0))
    input_param.simParams.warm_up = int(gen_sheet.cell_value(1,1))
    input_param.simParams.duration = int(gen_sheet.cell_value(1,2))

    # Arrival Params
    input_param.arrParams.initial_wait_list = int(gen_sheet.cell_value(1,3))
    input_param.arrParams.arrival_rate = gen_sheet.cell_value(1,4)
    input_param.arrParams.service_time = (gen_sheet.cell_value(1,5)/60)/24
    input_param.arrParams.capacity = int(gen_sheet.cell_value(1,6))

    # Scan Resuls
    input_param.scanResParams.result_types = []
    input_param.scanResParams.result_distribution = []
    for i in range(3):
        input_param.scanResParams.result_types.append(dist_sheet.cell_value(i+1,0))
        input_param.scanResParams.result_distribution.append(dist_sheet.cell_value(i+1,1)) 
    input_param.scanResParams.result_distribution = np.cumsum(input_param.scanResParams.result_distribution)

    input_param.scanResParams.negative_bulk = dist_sheet.cell_value(1,2)
    input_param.scanResParams.suspicious_biopsy = dist_sheet.cell_value(1,3)
    input_param.scanResParams.negatives_to_leave = dist_sheet.cell_value(1,6)

    # Delay Distribution
    input_param.scanResParams.delay_distribution = {}
    ind = 2
    input_param.scanResParams.delay_distribution['Negative'] = ({'Delay Prob':[], 'Delay Numb':[]})
    while True:
        try:
            input_param.scanResParams.delay_distribution['Negative']['Delay Prob'].append(neg_delay_sheet.cell_value(ind,0))
            input_param.scanResParams.delay_distribution['Negative']['Delay Numb'].append(neg_delay_sheet.cell_value(ind,1))
            ind += 1
        except IndexError:
            break
    input_param.scanResParams.delay_distribution['Negative']['Delay Prob'] = np.cumsum(input_param.scanResParams.delay_distribution['Negative']['Delay Prob'])
    
    ind = 2
    input_param.scanResParams.delay_distribution['Suspicious'] = ({'Delay Prob':[], 'Delay Numb':[]})
    while True:
        try:
            input_param.scanResParams.delay_distribution['Suspicious']['Delay Prob'].append(sus_delay_sheet.cell_value(ind,0))
            input_param.scanResParams.delay_distribution['Suspicious']['Delay Numb'].append(sus_delay_sheet.cell_value(ind,1))
            ind += 1
        except IndexError:
            break
    input_param.scanResParams.delay_distribution['Suspicious']['Delay Prob'] = np.cumsum(input_param.scanResParams.delay_distribution['Suspicious']['Delay Prob'])
    
    # Biopsy Results
    input_param.biopsyResParams.cancer_chance['Suspicious'] = dist_sheet.cell_value(1, 5)
    input_param.biopsyResParams.cancer_chance['Positive'] = dist_sheet.cell_value(2, 5)
    for i in range(4):
        input_param.biopsyResParams.cancer_types[i] = cancer_sheet.cell_value(i+1,0)
        input_param.biopsyResParams.cancer_staging[i] = cancer_sheet.cell_value(i+1,1)
        input_param.biopsyResParams.growth_rate[i] = cancer_sheet.cell_value(i+1,2)
    input_param.biopsyResParams.growth_interval = cancer_sheet.cell_value(1,3)
    input_param.biopsyResParams.cancer_staging = np.cumsum(input_param.biopsyResParams.cancer_staging)

    # Schedule
    for i in range(7):
        input_param.schedule[i] = [int(float(j)) for j in str(schedule_sheet.cell_value(i+1, 1)).split(',')]
        input_param.schedule[i] = np.cumsum(input_param.schedule[i])

# ~~~~~~~~~~~~~~~~~~~~~~~~~~ Part 3: Print Params ~~~~~~~~~~~~~~~~~~~~~

def printParams(sim_param):
    print(f'Replications: {sim_param.replications}, Warm-Up: {sim_param.warm_up_days}, Duration: {sim_param.duration_days}')
    print(f'Initial Wait List: {sim_param.initial_wait_list}, Service Time {sim_param.service_time*60*24}, Arrival Rate: {sim_param.arrival_rate}')
    print(f'Ottawa Capacity: {sim_param.ottawa_scan_capacity}, Renfrew Rate: {sim_param.renfrew_scan_capacity}, Cornwall: {sim_param.cornwall_scan_capacity}')
    print(f'Scan Result Names: {sim_param.results_names}, Scan Result Distribution: {sim_param.result_distribution}')
    print(f'Negative Return Probability: {sim_param.negative_return_probability}, Negative Scans to Leave {sim_param.negative_scans_to_leave}')
    print(f'Suspicious Need Bipsy Probability: {sim_param.suspicious_need_biopsy_probablity}, Positive Biopsy Probability: {sim_param.biopsy_positive_result_probablity}')
    print(f'Cancer Types: {sim_param.cancer_types}, Cancer Types Distribution: {sim_param.cancer_probability_distribution}, Cancer Types Growth: {sim_param.cancer_growth_rate}')
    print(f'Cancer Grow Interval: {sim_param.cancer_growth_interval}')
    print(f'Delay Data: {sim_param.delay_distribution}')
    print(f'Schedule: {sim_param.schedule}')
# %%
