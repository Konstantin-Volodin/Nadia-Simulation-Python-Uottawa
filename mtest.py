# %% 
import simpy
import pandas as pd
import pyarrow.feather as feather
from modules import singleQueue
from modules import readParams

def run_simulation(input_data):
    res_patients = pd.DataFrame()
    res_queue = pd.DataFrame()
    for repl in range(input_data.simParams.replications):
        env = simpy.Environment()
        simulation = singleQueue.Nadia_Simulation(env, input_data, repl, None)
        simulation.main_simulation()
        simulation.export_data()
        res_patients = pd.concat([res_patients, simulation.patient_results])
        res_queue = pd.concat([res_queue, simulation.arr_queue_results])
    return(res_patients, res_queue)

#%% Read Params
input_data = readParams.input_param()
readParams.readParameters(f'{input_data.directory}\\input\\input_parameters.xlsx', input_data)

# input_data.simParams.replications = 2
# input_data.simParams.duration = 10000
# input_data.arrParams.arrival_rate = 0
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
arrivals = [6*3, 8.6*3, 10*3, 15*3]
for arr in arrivals:
    input_data.arrParams.arrival_rate = arr

    capacity = [3]
    for cap in capacity:
        input_data.arrParams.capacity = cap
        
        ### Baseline
        input_data.scanResParams.delay_distribution['Negative']['Delay Numb'] = [30*12]
        input_data.scanResParams.delay_distribution['Suspicious']['Delay Prob'] = [0.625, 1]
        res_pat, res_queue = run_simulation(input_data)
        feather.write_feather(res_pat, f'{input_data.directory}\\output\\Baseline\\baseline-arr{arr}-mm{cap}-patients.feather', compression='zstd')
        feather.write_feather(res_queue, f'{input_data.directory}\\output\\Baseline\\baseline-arr{arr}-mm{cap}-queue.feather', compression='zstd')

        ### Option 1
        input_data.scanResParams.delay_distribution['Negative']['Delay Numb'] = [30*24]
        input_data.scanResParams.delay_distribution['Suspicious']['Delay Prob'] = [0.625, 1]
        res_pat, res_queue = run_simulation(input_data)
        feather.write_feather(res_pat, f'{input_data.directory}\\output\\Scenario 1\\sch1-arr{arr}-mm{cap}-patients.feather', compression='zstd')
        feather.write_feather(res_queue, f'{input_data.directory}\\output\\Scenario 1\\sch1-arr{arr}-mm{cap}-queue.feather', compression='zstd')

        ### Option 2
        input_data.scanResParams.delay_distribution['Negative']['Delay Numb'] = [30*12]
        input_data.scanResParams.delay_distribution['Suspicious']['Delay Prob'] = [1, 1]
        res_pat, res_queue = run_simulation(input_data)
        feather.write_feather(res_pat, f'{input_data.directory}\\output\\Scenario 2\\sch2-arr{arr}-mm{cap}-patients.feather', compression='zstd')
        feather.write_feather(res_queue, f'{input_data.directory}\\output\\Scenario 2\\sch2-arr{arr}-mm{cap}-queue.feather', compression='zstd')

        ### Option 3
        input_data.scanResParams.delay_distribution['Negative']['Delay Numb'] = [30*12]
        input_data.scanResParams.delay_distribution['Suspicious']['Delay Prob'] = [0, 1]
        res_pat, res_queue = run_simulation(input_data)
        feather.write_feather(res_pat, f'{input_data.directory}\\output\\Scenario 3\\sch3-arr{arr}-mm{cap}-patients.feather', compression='zstd')
        feather.write_feather(res_queue, f'{input_data.directory}\\output\\Scenario 3\\sch3-arr{arr}-mm{cap}-queue.feather', compression='zstd')

        ### Option 4
        input_data.scanResParams.delay_distribution['Negative']['Delay Numb'] = [30*24]
        input_data.scanResParams.delay_distribution['Suspicious']['Delay Prob'] = [1, 1]
        res_pat, res_queue = run_simulation(input_data)
        feather.write_feather(res_pat, f'{input_data.directory}\\output\\Scenario 4\\sch4-arr{arr}-mm{cap}-patients.feather', compression='zstd')
        feather.write_feather(res_queue, f'{input_data.directory}\\output\\Scenario 4\\sch4-arr{arr}-mm{cap}-queue.feather', compression='zstd')

        ### Option 5
        input_data.scanResParams.delay_distribution['Negative']['Delay Numb'] = [30*24]
        input_data.scanResParams.delay_distribution['Suspicious']['Delay Prob'] = [0, 1]
        res_pat, res_queue = run_simulation(input_data)
        feather.write_feather(res_pat, f'{input_data.directory}\\output\\Scenario 5\\sch5-arr{arr}-mm{cap}-patients.feather', compression='zstd')
        feather.write_feather(res_queue, f'{input_data.directory}\\output\\Scenario 5\\sch5-arr{arr}-mm{cap}-queue.feather', compression='zstd')



# res_patients = pd.DataFrame()
# res_queue = pd.DataFrame()
# for repl in range(input_data.simParams.replications):
#     env = simpy.Environment()
#     simulation = singleQueue.Nadia_Simulation(env, input_data, repl, None)
#     simulation.main_simulation()
#     simulation.export_data()
#     res_patients = pd.concat([res_patients, simulation.patient_results])
#     res_queue = pd.concat([res_queue, simulation.arr_queue_results])
# feather.write_feather(res_patients, f'{simulation.directory}\\output\\Steady State Arrival\\variable-arrival-baseline-patients.feather', compression='zstd')
# feather.write_feather(res_queue, f'{simulation.directory}\\output\\Steady State Arrival\\variable-arrival-baseline-queue.feather', compression='zstd')


# simulation.mainSimulation()
# simulation.calculateAggregate()
# %%

# %%
