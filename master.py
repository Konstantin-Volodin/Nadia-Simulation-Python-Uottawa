import numpy as np
import pandas as pd
import xlrd
import simpy
import os
import math

import contextlib
import joblib
from joblib import Parallel, delayed
from tqdm import tqdm
import multiprocessing

from modules import multiQueue 
from modules import singleQueue
from modules import dataAnalysis


# ~~~~~~~~~~~~~~~~~~~~~~~~~~ Part 1: Read Param Functions ~~~~~~~~~~~~~~~~~~~~~
# Reads the excel sheet
def readParameters(string_path, sim_param):
    book = xlrd.open_workbook(f"{string_path}.xlsx")

    gen_sheet = book.sheet_by_name("General Parameters")
    dist_sheet = book.sheet_by_name("Distributions")
    suspic_delay_sheet = book.sheet_by_name("Suspicious Delay Distribution")

    sim_param.replications = int(gen_sheet.cell_value(1,0))
    sim_param.warm_up_days = int(gen_sheet.cell_value(1,1))
    sim_param.duration_days = int(gen_sheet.cell_value(1,2))
    sim_param.initial_wait_list = int(gen_sheet.cell_value(1,3))
    sim_param.arrival_rate_per_day = gen_sheet.cell_value(1,4)
    sim_param.service_time = (gen_sheet.cell_value(1,5)/60)/24
    sim_param.ottawa_scan_capacity = int(gen_sheet.cell_value(1,6))
    sim_param.renfrew_scan_capacity = int(gen_sheet.cell_value(1,7))
    sim_param.cornwall_scan_capacity = int(gen_sheet.cell_value(1,8))

    for i in range(3):
        sim_param.results_names[i] = dist_sheet.cell_value(i+1,0)
        sim_param.result_distribution[i] = dist_sheet.cell_value(i+1,1)
    sim_param.negative_return_probability = dist_sheet.cell_value(1,2)
    sim_param.negative_return_delay = int(dist_sheet.cell_value(1,3))
    sim_param.suspicious_need_biopsy_probablity = dist_sheet.cell_value(1,4)
    sim_param.biopsy_positive_result_probablity = dist_sheet.cell_value(1,5)
    for i in range(4):
        sim_param.cancer_types[i] = dist_sheet.cell_value(i+1,6)
        sim_param.cancer_probability_distribution[i] = dist_sheet.cell_value(i+1,7)
    sim_param.cancer_types_modified = [x.replace(' ', '_') for x in sim_param.cancer_types]

    sim_param.suspicious_delay_propbability_distribution = []
    sim_param.suspicious_delay_duration = []
    i = 1
    while True:
        try:
            sim_param.suspicious_delay_propbability_distribution.append(suspic_delay_sheet.cell_value(i,0))
            sim_param.suspicious_delay_duration.append(int(suspic_delay_sheet.cell_value(i,1)))
            i += 1
        except IndexError:
            break
def printParams(sim_param):
    print(f'Replications: {sim_param.replications}, Warm-Up: {sim_param.warm_up_days}, Duration: {sim_param.duration_days}')
    print(f'Initial Wait List: {sim_param.initial_wait_list}, Arrival Rate: {sim_param.arrival_rate_per_day}, Service Time {sim_param.service_time*60*24}')
    print(f'Ottawa Capacity: {sim_param.ottawa_scan_capacity}, Renfrew Rate: {sim_param.renfrew_scan_capacity}, Cornwall: {sim_param.cornwall_scan_capacity}')
    print(f'Scan Result Names: {sim_param.results_names}, Scan Result Distribution: {sim_param.result_distribution}')
    print(f'Negative Return Probability: {sim_param.negative_return_probability}, Negative Delay: {sim_param.negative_return_delay}')
    print(f'Suspicious Need Bipsy Probability: {sim_param.suspicious_need_biopsy_probablity}, Positive Biopsy Probability: {sim_param.biopsy_positive_result_probablity}')
    print(f'Cancer Types: {sim_param.cancer_types}, Cancer Types Distribution: {sim_param.cancer_probability_distribution}')
    print(f'Suspicious Delay Duration: {sim_param.suspicious_delay_duration}, Suspicious Delay Probability: {sim_param.suspicious_delay_propbability_distribution}')
def silentremove(filename):
    try:
        os.remove(filename)
    except OSError:
        pass
@contextlib.contextmanager
def tqdm_joblib(tqdm_object):
    """Context manager to patch joblib to report into tqdm progress bar given as argument"""
    class TqdmBatchCompletionCallback(joblib.parallel.BatchCompletionCallBack):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        def __call__(self, *args, **kwargs):
            tqdm_object.update(n=self.batch_size)
            return super().__call__(*args, **kwargs)

    old_batch_callback = joblib.parallel.BatchCompletionCallBack
    joblib.parallel.BatchCompletionCallBack = TqdmBatchCompletionCallback
    try:
        yield tqdm_object
    finally:
        joblib.parallel.BatchCompletionCallBack = old_batch_callback
        tqdm_object.close()   


# ~~~~~~~~~~~~~~~~~~~~~~~~~~ Part 2: Sim Param Class ~~~~~~~~~~~~~~~~~~~~~
# Placeholder Parameters
class simulationParameters:
    def __init__(self):
        self.directory = os.path.dirname(os.path.realpath(__file__))

        self.replications = 100
        self.warm_up_days = 50
        self.duration_days = 150
        self.initial_wait_list = 100
        self.arrival_rate_per_day = 40
        self.service_time = (15/60)/24
        self.ottawa_scan_capacity = 1
        self.renfrew_scan_capacity = 1
        self.cornwall_scan_capacity = 1

        self.results_names = ['Negative', 'Sus', 'Positive']
        self.result_distribution = [0.33, 0.33, 0.34]
        self.negative_return_probability = 0.50
        self.negative_return_delay = 100
        self.suspicious_need_biopsy_probablity = 0.5
        self.biopsy_positive_result_probablity = 0.8
        self.cancer_types = ['Stage 1', 'Stage 2', 'Stage 3', 'Stage 4']
        self.cancer_types_modified = [x.replace(' ', '_') for x in self.cancer_types]
        self.cancer_probability_distribution = [0.1, 0.2, 0.3, 0.4]

        self.suspicious_delay_propbability_distribution = [0.33, 0.33, 0.34]
        self.suspicious_delay_duration = [50, 25, 10]


# ~~~~~~~~~~~~~~~~~~~~~~~~~~ Part 3: Multicore Functions ~~~~~~~~~~~~~~~~~~~~~
# Multicore Functions
def multiCoreSimulationMultiQueue(sim_params, repl):
    env = simpy.Environment()
    simulation = multiQueue.Nadia_Simulation(env, sim_params, repl)
    simulation.mainSimulation()
    return simulation.patient_results[sim_params.warm_up_days:], simulation.daily_queue_data[sim_params.warm_up_days:]
def signleCoreSimulationSingleQueue(sim_params, repl):
    env = simpy.Environment()
    simulation = singleQueue.Nadia_Simulation(env, sim_params, repl)
    simulation.mainSimulation()
    return simulation.patient_results[sim_params.warm_up_days:], simulation.daily_queue_data[sim_params.warm_up_days:]


# ~~~~~~~~~~~~~~~~~~~~~~~~~~ Part 4: Generate Parameters ~~~~~~~~~~~~~~~~~~~~~
# Simulation/Main Parameters Generation
sim_params = simulationParameters()
readParameters(f"{sim_params.directory}/input/input_parameters", sim_params)
pd.set_option("display.max_rows", None, "display.max_columns", None, 'display.expand_frame_repr', False)
num_cores = math.floor(multiprocessing.cpu_count() * 0.75)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~ Part 4a: Deletes Files ~~~~~~~~~~~~~~~~~~~~~
silentremove(f"{sim_params.directory}/output/raw_multi_patients.txt")
silentremove(f"{sim_params.directory}/output/raw_multi_queue.txt")
silentremove(f"{sim_params.directory}/output/aggregate_multi.txt")
silentremove(f"{sim_params.directory}/output/raw_single_patients.txt")
silentremove(f"{sim_params.directory}/output/raw_single_queue.txt")
silentremove(f"{sim_params.directory}/output/aggregate_single.txt")


# ~~~~~~~~~~~~~~~~~~~~~~~~~~ Part 5: Perform Multi Queue ~~~~~~~~~~~~~~~~~~~~~
# Simulation
multi_final_results = []
with tqdm_joblib(tqdm(desc="MULTI QUEUE SIMULATION", total=sim_params.replications)) as progress_bar:
    multi_final_results = Parallel(n_jobs=num_cores)(delayed(multiCoreSimulationMultiQueue)(sim_params, i) for i in range(sim_params.replications))

# Output Raw
with open(f"{sim_params.directory}/output/raw_multi_patients.txt", "w") as text_file:
    print('Replication, ID, Arrived, Queued To, Start Service, End Service, Scan Results, Biopsy Results, Post Scan Status', file=text_file)
    for repl in multi_final_results:
        for patient in repl[0]:
            print(patient, file=text_file)
with open(f"{sim_params.directory}/output/raw_multi_queue.txt", "w") as text_file:
    print('Replication, Day, Queue Amount', file=text_file)
    for repl in range(len(multi_final_results)):
        for day in range(len(multi_final_results[repl][1])):
            print(f"{repl}, {day+sim_params.warm_up_days}, {multi_final_results[repl][1][day]}", file=text_file)

# Aggregate Results
print('Calculates Aggregate Data')
dataAnalysis.main_analysis(f"{sim_params.directory}/output/raw_multi_patients", f"{sim_params.directory}/output/raw_multi_queue", f"{sim_params.directory}/output/aggregate_multi")


# ~~~~~~~~~~~~~~~~~~~~~~~~~~ Part 6: Perform Single Queue ~~~~~~~~~~~~~~~~~~~~~
# Simulation
single_final_results = []
with tqdm_joblib(tqdm(desc="SINGLE QUEUE SIMULATION", total=sim_params.replications)) as progress_bar:
    single_final_results = Parallel(n_jobs=num_cores)(delayed(signleCoreSimulationSingleQueue)(sim_params, i) for i in range(sim_params.replications))

# Output Raw
with open(f"{sim_params.directory}/output/raw_single_patients.txt", "w") as text_file:
    print('Replication, ID, Arrived, Queued To, Start Service, End Service, Scan Results, Biopsy Results, Post Scan Status', file=text_file)
    for repl in single_final_results:
        for patient in repl[0]:
            print(patient, file=text_file)
with open(f"{sim_params.directory}/output/raw_single_queue.txt", "w") as text_file:
    print('Replication, Day, Queue Amount', file=text_file)
    for repl in range(len(single_final_results)):
        for day in range(len(single_final_results[repl][1])):
            print(f"{repl}, {day+sim_params.warm_up_days}, {single_final_results[repl][1][day]}", file=text_file)

# Aggregate Results
print('Calculates Aggregate Data')
dataAnalysis.main_analysis(f"{sim_params.directory}/output/raw_single_patients", f"{sim_params.directory}/output/raw_single_queue", f"{sim_params.directory}/output/aggregate_single")