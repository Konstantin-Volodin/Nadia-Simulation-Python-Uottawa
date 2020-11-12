import numpy as np
import pandas as pd
import xlrd
import os

# ~~~~~~~~~~~~~~~~~~~~~~~~~~ Part 1: Sim Param Class ~~~~~~~~~~~~~~~~~~~~~
# Placeholder Parameters
class simulationParameters:
    def __init__(self):
        self.directory = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        self.schedule = [
            [8,8,8],
            [8,8,8],
            [8,8,8],
            [8,8,8],
            [8,8,8],
            [24],
            [24]
        ]

        self.replications = 100
        self.warm_up_days = 50
        self.duration_days = 150
        self.initial_wait_list = 100
        self.arrival_rate = 40
        self.service_time = (15/60)/24
        self.ottawa_scan_capacity = 1
        self.renfrew_scan_capacity = 1
        self.cornwall_scan_capacity = 1

        self.results_names = ['Negative', 'Sus', 'Positive']
        self.result_distribution = [
            [0.33, 0.33, 0.34],
            [0.2, 0.3, 0.5]
        ]
        self.negative_return_probability = 0.50
        self.negative_scans_to_leave = 2
        self.delay_distribution = {
            'Negative': {'Delay Prob': [1], 'Delay Numb': [360]},
            'Sus': {'Delay Prob': [0.625, 1], 'Delay Numb': [180, 90]}
        }
        self.suspicious_need_biopsy_probablity = 0.5
        self.biopsy_positive_result_probablity = {
            'Sus': 0.75,
            'Positive': 0.85
        }
        self.cancer_types = ['Stage_1', 'Stage_2', 'Stage_3', 'Stage_4']
        self.cancer_probability_distribution = [0.4, 0.3, 0.2, 0.1]
        self.cancer_growth_rate = [1, 1, 1.25, 1.5]
        self.cancer_growth_interval = 180

# ~~~~~~~~~~~~~~~~~~~~~~~~~~ Part 2: Read Params ~~~~~~~~~~~~~~~~~~~~~
def readParameters(string_path, sim_param):
    book = xlrd.open_workbook(f"{string_path}.xlsx")

    gen_sheet = book.sheet_by_name("General Parameters")
    dist_sheet = book.sheet_by_name("Distributions")
    sus_delay_sheet = book.sheet_by_name("Suspicious Delay Distribution")
    neg_delay_sheet = book.sheet_by_name("Negative Delay Distribution")
    schedule_sheet = book.sheet_by_name("Schedules Data")
    cancer_sheet = book.sheet_by_name("Cancer Distribution")

    sim_param.replications = int(gen_sheet.cell_value(1,0))
    sim_param.warm_up_days = int(gen_sheet.cell_value(1,1))
    sim_param.duration_days = int(gen_sheet.cell_value(1,2))
    sim_param.initial_wait_list = int(gen_sheet.cell_value(1,3))
    sim_param.arrival_rate = gen_sheet.cell_value(1,4)
    sim_param.service_time = (gen_sheet.cell_value(1,5)/60)/24
    sim_param.ottawa_scan_capacity = int(gen_sheet.cell_value(1,6))
    sim_param.renfrew_scan_capacity = int(gen_sheet.cell_value(1,7))
    sim_param.cornwall_scan_capacity = int(gen_sheet.cell_value(1,8))

    
    sim_param.result_distribution = []
    for i in range(3):
        sim_param.results_names[i] = dist_sheet.cell_value(i+1,0)
    for i in range(int(dist_sheet.cell_value(0,1))):
        sim_param.result_distribution.append([])
        for j in range(3):
            sim_param.result_distribution[i].append(dist_sheet.cell_value(i+1,j+2))
    sim_param.negative_return_probability = dist_sheet.cell_value(1,5)
    sim_param.suspicious_need_biopsy_probablity = dist_sheet.cell_value(1,6)
    sim_param.biopsy_positive_result_probablity = {}
    sim_param.biopsy_positive_result_probablity['Suspicious'] = dist_sheet.cell_value(1,8)
    sim_param.biopsy_positive_result_probablity['Positive'] = dist_sheet.cell_value(2,8)
    sim_param.negative_scans_to_leave = dist_sheet.cell_value(1,9)

    sim_param.delay_distribution = {}
    i = 2
    sim_param.delay_distribution['Negative'] = ({'Delay Prob':[], 'Delay Numb':[]})
    while True:
        try:
            sim_param.delay_distribution['Negative']['Delay Prob'].append(neg_delay_sheet.cell_value(i,0))
            sim_param.delay_distribution['Negative']['Delay Numb'].append(neg_delay_sheet.cell_value(i,1))
            i += 1
        except IndexError:
            break
    sim_param.delay_distribution['Negative']['Delay Prob'] = np.cumsum(sim_param.delay_distribution['Negative']['Delay Prob'])

    i = 2
    sim_param.delay_distribution['Suspicious'] = ({'Delay Prob':[], 'Delay Numb':[]})
    while True:
        try:
            sim_param.delay_distribution['Suspicious']['Delay Prob'].append(sus_delay_sheet.cell_value(i,0))
            sim_param.delay_distribution['Suspicious']['Delay Numb'].append(sus_delay_sheet.cell_value(i,1))
            i += 1
        except IndexError:
            break
    sim_param.delay_distribution['Suspicious']['Delay Prob'] = np.cumsum(sim_param.delay_distribution['Suspicious']['Delay Prob'])

    for i in range(4):
        sim_param.cancer_types[i] = cancer_sheet.cell_value(i+1,0)
        sim_param.cancer_probability_distribution[i] = cancer_sheet.cell_value(i+1,1)
        sim_param.cancer_growth_rate[i] = cancer_sheet.cell_value(i+1,2)
    sim_param.cancer_growth_interval = cancer_sheet.cell_value(1,3)

    for i in range(7):
        sim_param.schedule[i] = [int(float(j)) for j in str(schedule_sheet.cell_value(i+1, 1)).split(',')]

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