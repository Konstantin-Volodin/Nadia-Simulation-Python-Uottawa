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
#sim_params.initial_wait_list = 100000
#sim_params.duration_days = 1500
sim_params.arrival_rate = 30

#%%
env = simpy.Environment()
simulation = singleQueue.Nadia_Simulation(env, sim_params, 1)
simulation.mainSimulation()
simulation.calculateAggregate()
final_results = simulation.patient_results

# simulation.calculateAggregate()
# %%
with open(f"{sim_params.directory}/testing40.txt", "w") as text_file:
    print('Replication, Number of Negatives Scans Before, ID, Arrived, Queued To, Start Service, End Service, Scan Results, Biopsy Results, Post Scan Status', file=text_file)
    for patient in final_results:
        print(patient, file=text_file)
    



# %%
