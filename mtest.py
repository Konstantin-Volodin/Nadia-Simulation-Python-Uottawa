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
#%%
sim_params = readParams.simulationParameters()
readParams.readParameters(f"{sim_params.directory}/input/input_parameters", sim_params)
sim_params.replications = 1
# sim_params.initial_wait_list = 1000
# sim_params.service_time = 0.25
sim_params.duration_days = 10
sim_params.warm_up_days = 0
sim_params.arrival_rate = 100
env = simpy.Environment()
simulation = multiQueue.Nadia_Simulation(env, sim_params, 0)
simulation.mainSimulation()

patient_data = []
patient_data.append(['replication', 'numb_negative_bf', 'id', 'arrived', 'que_to', 'start', 'end', 'scan_res', 'biopsy_res', 'post_scan_res'])
for i in simulation.patient_results:
    data = str(i).split(',')
    data = [i.strip() for i in data]
    patient_data.append(data)
patient_data = pd.DataFrame(patient_data)
patient_data.columns = patient_data.iloc[0]
patient_data = patient_data[1:]
patient_data.count()
patient_data['start'] = pd.to_numeric(patient_data["start"], downcast="float")

#%%
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
def multiCoreSimulationMultiQueue(sim_params, repl):
    env = simpy.Environment()
    simulation = multiQueue.Nadia_Simulation(env, sim_params, repl)
    simulation.mainSimulation()
    simulation.calculateAggregate()
    return  (simulation.patient_results, simulation.daily_queue_data, simulation.cancer_aggregate, simulation.time_in_system_aggregate, 
            simulation.total_aggregate, simulation.queue_aggregate, simulation.utilization_aggregate, simulation.historic_arrival_rate_external)

pd.set_option("display.max_rows", None, "display.max_columns", None, 'display.expand_frame_repr', False)
num_cores = multiprocessing.cpu_count()
num_cores = 6

# simulation.calculateAggregate()
# %%
with tqdm_joblib(tqdm("BASELINE SIMULATION", total=sim_params.replications)) as progress_bar:
        final_results = Parallel(n_jobs=num_cores)(delayed(multiCoreSimulationMultiQueue)(sim_params, i) for i in range(sim_params.replications))

#%%
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

#%%

cancer_ov_aggregate = cancer_aggregate.pipe(dataAnalysis.cancerDetailsAnalysis_Simulation)
time_in_system_ov_aggregate = time_in_system_aggregate.pipe(dataAnalysis.timeInSystemAnalysis_Simulation)
total_ov_aggregate = total_aggregate.pipe(dataAnalysis.totalPatientDetailsAnalysis_Simulation)
queue_ov_aggregate = queue_aggregate.pipe(dataAnalysis.aggregateQueueAnalysis_Simulation)
utilization_ov_aggregate = utilization_aggregate.pipe(dataAnalysis.aggregateUtilizationAnalysis_Simulation)
    

#%%
with open(f"{sim_params.directory}/testing{sim_params.arrival_rate}.txt", "w") as text_file:
    print('Replication, Number of Negatives Scans Before, ID, Arrived, Queued To, Start Service, End Service, Scan Results, Biopsy Results, Post Scan Status', file=text_file)
    for repl in final_results:
        for patient in repl[0]:
            print(patient, file=text_file)
    



# %%
