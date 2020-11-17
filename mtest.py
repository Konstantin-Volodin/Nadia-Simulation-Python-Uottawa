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

sim_params = readParams.simulationParameters()
readParams.readParameters(f"{sim_params.directory}/input/input_parameters", sim_params)

print('Sim Params')
print(sim_params.cancer_probability_distribution)
print(sim_params.cancer_growth_rate)
print(sim_params.cancer_growth_interval)
print()

prob_dens = sim_params.cancer_probability_distribution.copy()
prob_cum = np.cumsum(sim_params.cancer_probability_distribution)
g_rate = sim_params.cancer_growth_rate
g_interv = sim_params.cancer_growth_interval

print('Initial Class Copy')
print(prob_dens)
print(prob_cum)
print(g_rate)
print(g_interv)
print()

for j in range(10):
    cancer_adjusted_probs = prob_dens.copy()

    curr_interval = 0
    while True:
        if (curr_interval+g_interv) > 180:
            break
        else:
            curr_interval += g_interv
            for i in range(len(cancer_adjusted_probs)):
                cancer_adjusted_probs[i] = cancer_adjusted_probs[i] * g_rate[i]
            cancer_prob_sum = np.sum(cancer_adjusted_probs)
            for i in range(len(cancer_adjusted_probs)):
                cancer_adjusted_probs[i] = cancer_adjusted_probs[i] / cancer_prob_sum
        print(cancer_adjusted_probs)
        
    cancer_adjusted_probs = np.cumsum(cancer_adjusted_probs)

    print()
    print(f'{j} Class Copy')
    print(prob_dens)
    print(prob_cum)
    print(g_rate)
    print(g_interv)
    print(cancer_adjusted_probs)
    print()