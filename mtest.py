#%% 
import simpy
import pandas as pd
import pyarrow.feather as feather
from modules import singleQueue
from modules import readParams


#%% Read Params
input_data = readParams.input_param()
readParams.readParameters(f'{input_data.directory}\\input\\input_parameters.xlsx', input_data)

input_data.simParams.replications = 1
# input_data.simParams.duration = 
# input_data.simParams.warm_up = 50

#%% Generates Arrivals

# np.random.seed(100)
# arrival_rates_data_mm3 = []
# arrival_rates_data_mm1 = []
# for repl in range(sim_params.replications):
#     arrival_rates_data_mm3.append([])
#     arrival_rates_data_mm1.append([])

#     for day in range(sim_params.duration_days):
#         arrival_rates_data_mm3[repl].append(np.random.poisson(sim_params.arrival_rate))
#         arrival_rates_data_mm1[repl].append(int(round(arrival_rates_data_mm3[repl][day]/3, 0)))
# %% Test Simulation
env = simpy.Environment()
simulation = singleQueue.Nadia_Simulation(env, input_data, 0, None)
simulation.main_simulation()
simulation.export_data()
feather.write_feather(simulation.patient_results, f'{simulation.directory}\\output\\testing.feather', compression='zstd')


# simulation.mainSimulation()
# simulation.calculateAggregate()
# %%

# %%
