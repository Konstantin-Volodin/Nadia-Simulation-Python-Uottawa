#%% 
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
from modules import readParams

# ~~~~~~~~~~~~~~~~~~~~~~~~~~ Part 1: Misc Functions ~~~~~~~~~~~~~~~~~~~~~

def silentremove(filename):
    try:
        os.remove(filename)
    except OSError:
        pass
def silentAdd(foldePath):
    try:
        os.mkdir(foldePath)
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


# ~~~~~~~~~~~~~~~~~~~~~~~~~~ Part 2: Prepares Multicore Functions ~~~~~~~~~~~~~~~~~~~~~
# Multicore Functions
def multiCoreSimulationMultiQueue(sim_params, repl, arrival_rates_data):
    env = simpy.Environment()
    simulation = multiQueue.Nadia_Simulation(env, sim_params, repl, arrival_rates_data)
    simulation.mainSimulation()
    simulation.calculateAggregate()
    return  (simulation.patient_results, simulation.daily_queue_data, simulation.cancer_aggregate, simulation.time_in_system_aggregate, 
            simulation.total_aggregate, simulation.queue_aggregate, simulation.utilization_aggregate, simulation.historic_arrival_rate_external)
def signleCoreSimulationSingleQueue(sim_params, repl, arrival_rates_data):
    env = simpy.Environment()
    simulation = singleQueue.Nadia_Simulation(env, sim_params, repl, arrival_rates_data)
    simulation.mainSimulation()
    simulation.calculateAggregate()
    return  (simulation.patient_results, simulation.daily_queue_data, simulation.cancer_aggregate, simulation.time_in_system_aggregate,
            simulation.total_aggregate, simulation.queue_aggregate, simulation.utilization_aggregate, simulation.historic_arrival_rate_external)
pd.set_option("display.max_rows", None, "display.max_columns", None, 'display.expand_frame_repr', False)
num_cores = multiprocessing.cpu_count()
num_cores = 6

# ~~~~~~~~~~~~~~~~~~~~~~~~~~ Part 3: Generate Parameters ~~~~~~~~~~~~~~~~~~~~~
# Simulation/Main Parameters Generation
sim_params = readParams.simulationParameters()
readParams.readParameters(f"{sim_params.directory}/input/input_parameters", sim_params)
#readParams.printParams(sim_params)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~ Part 4: Main Multicore Function ~~~~~~~~~~~~~~~~~~~~~
def runSimulation(filePath, fileNameStart, simFunction, arrival_rates_data, queueData = False, rawData = False, replicationData = False):
    silentAdd(f"{sim_params.directory}/output/{filePath}")
    final_results = []
    with tqdm_joblib(tqdm(desc=f"{filePath} SIMULATION", total=sim_params.replications)) as progress_bar:
    # final_results.append(signleCoreSimulationSingleQueue(sim_params, 0))
        final_results = Parallel(n_jobs=num_cores)(delayed(simFunction)(sim_params, i, arrival_rates_data) for i in range(sim_params.replications))

    ### Output Raw
    if rawData:
        # Patient Data
        with open(f"{sim_params.directory}/output/{filePath}/{fileNameStart}_raw_patients.txt", "w") as text_file:
            print('Replication, Number of Negatives Scans Before, ID, Arrived, Queued To, Start Service, End Service, Scan Results, Biopsy Results, Post Scan Status', file=text_file)
            for repl in final_results:
                for patient in repl[0]:
                    print(patient, file=text_file)
    if queueData:
        # Queue Data
        with open(f"{sim_params.directory}/output/{filePath}/{fileNameStart}_raw_queue.txt", "w") as text_file:
            print('Replication, Day, Queued To, Queue Amount', file=text_file)
            for repl in range(len(final_results)):
                for item in final_results[repl][1]:
                    print(f"{item['replication']}, {item['day']}, {item['queue']}, {item['size']}", file=text_file)
        # Arrival Data
        with open(f"{sim_params.directory}/output/{filePath}/{fileNameStart}_raw_arrival.txt", "w") as text_file:
            print('Replication, Day, Arrival Amount', file=text_file)
            for repl in range(len(final_results)):
                for day in range(len(final_results[repl][7])):
                    print(f"{repl}, {day}, {final_results[repl][7][day]}", file=text_file)

    ### Calculate Replication Data
    # print('Calculates Replication Details Data')
    cancer_aggregate = [] 
    time_in_system_aggregate = []
    total_aggregate = [] 
    queue_aggregate = []
    utilization_aggregate = []
    for repl in range(len(final_results)):    
        if repl == 0:
            cancer_aggregate = final_results[repl][2]
            time_in_system_aggregate = final_results[repl][3]
            total_aggregate = final_results[repl][4]
            queue_aggregate = final_results[repl][5]
            utilization_aggregate = final_results[repl][6]
        else:
            cancer_aggregate = cancer_aggregate.append([final_results[repl][2]])
            time_in_system_aggregate = time_in_system_aggregate.append([final_results[repl][3]])
            total_aggregate = total_aggregate.append([final_results[repl][4]])
            queue_aggregate = queue_aggregate.append([final_results[repl][5]])
            utilization_aggregate = utilization_aggregate.append([final_results[repl][6]])

    ### Prints Replication Data
    if replicationData:
        with open(f"{sim_params.directory}/output/{filePath}/{fileNameStart}_replication.html", 'w') as html_file:
            html_file.write(
                cancer_aggregate.to_html() + '\n\n' +
                time_in_system_aggregate.to_html() + '\n\n' +
                total_aggregate.to_html() + '\n\n' +
                queue_aggregate.to_html() + '\n\n' +
                utilization_aggregate.to_html()
            )
    del final_results

    ### Calculate Aggregate Data
    # print('Calculates Aggregate Data')
    cancer_aggregate = cancer_aggregate.pipe(dataAnalysis.cancerDetailsAnalysis_Simulation)
    time_in_system_aggregate = time_in_system_aggregate.pipe(dataAnalysis.timeInSystemAnalysis_Simulation)
    total_aggregate = total_aggregate.pipe(dataAnalysis.totalPatientDetailsAnalysis_Simulation)
    queue_aggregate = queue_aggregate.pipe(dataAnalysis.aggregateQueueAnalysis_Simulation)
    utilization_aggregate = utilization_aggregate.pipe(dataAnalysis.aggregateUtilizationAnalysis_Simulation)
    with open(f"{sim_params.directory}/output/{filePath}/{fileNameStart}_aggregate.html", 'w') as html_file:
        html_file.write(
            cancer_aggregate.to_html() + '\n\n' +
            time_in_system_aggregate.to_html() + '\n\n' +
            total_aggregate.to_html() + '\n\n' +
            queue_aggregate.to_html() + '\n\n' +
            utilization_aggregate.to_html()
        )
    with open(f"{sim_params.directory}/output/{filePath}/{fileNameStart}_aggregate.txt", 'w') as txt_file:
        txt_file.write(
            cancer_aggregate.to_json(indent=4) + '\n\n' +
            time_in_system_aggregate.to_json(indent=4) + '\n\n' +
            total_aggregate.to_json(indent=4) + '\n\n' +
            queue_aggregate.to_json(indent=4) + '\n\n' +
            utilization_aggregate.to_json(indent=4)
        )

# sim_params.duration_days = 2000
# sim_params.warm_up_days = 1000


#%%
# silentAdd(f"{sim_params.directory}/output/BASELINE")
# ~~~~~~~~~~~~~~~~~~~~~~~~~~ Part 5: Running Various Scenarios ~~~~~~~~~~~~~~~~~~~~~
arrival_rates = [25, 27, 30, 35]
for i in tqdm(arrival_rates, desc=f'Scenario Simulation'):
    sim_params.arrival_rate = i

    np.random.seed(100)
    arrival_rates_data_mm3 = []
    arrival_rates_data_mm1 = []
    for repl in range(sim_params.replications):
        arrival_rates_data_mm3.append([])
        arrival_rates_data_mm1.append([])

        for day in range(sim_params.duration_days):
            arrival_rates_data_mm3[repl].append(np.random.poisson(sim_params.arrival_rate))
            arrival_rates_data_mm1[repl].append(int(round(arrival_rates_data_mm3[repl][day]/3, 0)))


    ### Baseline
    sim_params.delay_distribution['Negative']['Delay Numb'] = [30*12]
    sim_params.delay_distribution['Suspicious']['Delay Prob'] = [0.625, 1]
    runSimulation("BASELINE",f"base_{sim_params.arrival_rate}_mm3", signleCoreSimulationSingleQueue, arrival_rates_data_mm3)
    sim_params.cornwall_scan_capacity = 0
    sim_params.renfrew_scan_capacity = 0
    runSimulation("BASELINE",f"base_{sim_params.arrival_rate}_mm1", signleCoreSimulationSingleQueue, arrival_rates_data_mm1)

    ### Option 1
    sim_params.delay_distribution['Negative']['Delay Numb'] = [30*24]
    sim_params.delay_distribution['Suspicious']['Delay Prob'] = [0.625, 1]
    sim_params.cornwall_scan_capacity = 1
    sim_params.renfrew_scan_capacity = 1
    runSimulation("SCENARIO 1",f"scn1_{sim_params.arrival_rate}_mm3", signleCoreSimulationSingleQueue, arrival_rates_data_mm3)
    sim_params.cornwall_scan_capacity = 0
    sim_params.renfrew_scan_capacity = 0
    runSimulation("SCENARIO 1",f"scn1_{sim_params.arrival_rate}_mm1", signleCoreSimulationSingleQueue, arrival_rates_data_mm1)

    ### Option 2
    sim_params.delay_distribution['Negative']['Delay Numb'] = [30*12]
    sim_params.delay_distribution['Suspicious']['Delay Prob'] = [1, 1]
    sim_params.cornwall_scan_capacity = 1
    sim_params.renfrew_scan_capacity = 1
    runSimulation("SCENARIO 2",f"scn2_{sim_params.arrival_rate}_mm3", signleCoreSimulationSingleQueue, arrival_rates_data_mm3)
    sim_params.cornwall_scan_capacity = 0
    sim_params.renfrew_scan_capacity = 0
    runSimulation("SCENARIO 2",f"scn2_{sim_params.arrival_rate}_mm1", signleCoreSimulationSingleQueue, arrival_rates_data_mm1)

    ### Option 3
    sim_params.delay_distribution['Negative']['Delay Numb'] = [30*12]
    sim_params.delay_distribution['Suspicious']['Delay Prob'] = [0, 1]
    sim_params.cornwall_scan_capacity = 1
    sim_params.renfrew_scan_capacity = 1
    runSimulation("SCENARIO 3",f"scn3_{sim_params.arrival_rate}_mm3", signleCoreSimulationSingleQueue, arrival_rates_data_mm3)
    sim_params.cornwall_scan_capacity = 0
    sim_params.renfrew_scan_capacity = 0
    runSimulation("SCENARIO 3",f"scn3_{sim_params.arrival_rate}_mm1", signleCoreSimulationSingleQueue, arrival_rates_data_mm1)

    ### Option 4
    sim_params.delay_distribution['Negative']['Delay Numb'] = [30*24]
    sim_params.delay_distribution['Suspicious']['Delay Prob'] = [1, 1]
    sim_params.cornwall_scan_capacity = 1
    sim_params.renfrew_scan_capacity = 1
    runSimulation("SCENARIO 4",f"scn4_{sim_params.arrival_rate}_mm3", signleCoreSimulationSingleQueue, arrival_rates_data_mm3)
    sim_params.cornwall_scan_capacity = 0
    sim_params.renfrew_scan_capacity = 0
    runSimulation("SCENARIO 4",f"scn4_{sim_params.arrival_rate}_mm1", signleCoreSimulationSingleQueue, arrival_rates_data_mm1)

    ### Option 5
    sim_params.delay_distribution['Negative']['Delay Numb'] = [30*24]
    sim_params.delay_distribution['Suspicious']['Delay Prob'] = [0, 1]
    sim_params.cornwall_scan_capacity = 1
    sim_params.renfrew_scan_capacity = 1
    runSimulation("SCENARIO 5",f"scn5_{sim_params.arrival_rate}_mm3", signleCoreSimulationSingleQueue, arrival_rates_data_mm3)
    sim_params.cornwall_scan_capacity = 0
    sim_params.renfrew_scan_capacity = 0
    runSimulation("SCENARIO 5",f"scn5_{sim_params.arrival_rate}_mm1", signleCoreSimulationSingleQueue, arrival_rates_data_mm1)
# %%

# %%
