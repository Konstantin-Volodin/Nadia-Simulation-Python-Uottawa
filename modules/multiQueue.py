import simpy 
import numpy as np
import pandas as pd
from tqdm import tqdm

import math
import os
from modules import dataAnalysis

class Nadia_Simulation:

    # Initializes parameters
    def __init__(self, env, sim_params, replication):
        self.env = env
        self.directory = sim_params.directory
        self.replication = replication
        self.random_stream = np.random.RandomState()
        self.random_stream.seed((replication*28+4589)*78)

        self.schedule = sim_params.schedule.copy()
        for i in range(len(self.schedule)):
            self.schedule[i] = np.cumsum(self.schedule[i])

        self.warm_up_days = sim_params.warm_up_days
        self.duration_days = sim_params.duration_days
        self.initial_wait_list = sim_params.initial_wait_list
        self.arrival_rate = sim_params.arrival_rate
        self.service_time = sim_params.service_time
        self.capacity = sim_params.ottawa_scan_capacity
        self.ottawa_scan = simpy.PriorityResource(env, sim_params.ottawa_scan_capacity)
        self.renfrew_scan = simpy.PriorityResource(env, sim_params.renfrew_scan_capacity)
        self.cornwall_scan = simpy.PriorityResource(env, sim_params.cornwall_scan_capacity)

        self.scan_results_names = sim_params.results_names
        self.scan_results_distribution = sim_params.result_distribution.copy()
        for i in range(len(self.scan_results_distribution)):
            self.scan_results_distribution[i] = np.cumsum(self.scan_results_distribution[i])

        self.negative_return_probability = sim_params.negative_return_probability
        self.delay_distribution = sim_params.delay_distribution
        self.suspicious_need_biopsy_probablity = sim_params.suspicious_need_biopsy_probablity
        self.biopsy_positive_result_probablity = sim_params.biopsy_positive_result_probablity
        self.cancer_names = sim_params.cancer_types
        self.cancer_results_distribution_non_cumulative = sim_params.cancer_probability_distribution.copy()
        self.cancer_results_distribution = np.cumsum(sim_params.cancer_probability_distribution)
        self.cancer_growth_rates = sim_params.cancer_growth_rate
        self.cancer_growth_interval = sim_params.cancer_growth_interval

        self.patient_results = []
        self.daily_queue_data = []
        self.historic_arrival_rate_external = [self.arrival_rate for i in range(self.duration_days)]


    # The following 3 functions deal with process a patient goes through
    def patientProcess(self, pat_id):
        in_the_system = True
        returns = 0
        while in_the_system:

            # Creates new Patient
            new_patient = self.createPatient(self.replication, pat_id)
            new_patient.returns = returns

            # Arrived Logic
            new_patient.arrived = self.env.now
            print(f"Patient {pat_id} Arrived: {self.env.now}")

            # Scan Process Logic   
            selection = self.selectHospitalQueue(new_patient)
            with selection[0].request(priority=2) as req:
                yield req
                print(f"Patient {pat_id} Seizes {selection[1]}: {self.env.now}")
                new_patient.start_scan = self.env.now
                print(f"Patient {pat_id} Started Scan: {self.env.now}")
                yield self.env.timeout(self.random_stream.exponential(self.service_time))
                new_patient.end_scan = self.env.now
                print(f"Patient {pat_id} Finished Scan: {self.env.now}")
            print(f"Patient {pat_id} Released {selection[1]}: {self.env.now}")
            
            # Post Scan Logic
            post_scan_decisions = self.postScanProcessLogic(new_patient)
            in_the_system = post_scan_decisions['In System']
            yield self.env.timeout(post_scan_decisions['Delay'])

            # Adds a return count
            if new_patient.scan_result == self.scan_results_names[0]:
                returns += 1
    def createPatient(self, replication, pat_id):
        self.patient_results.append(Patient(replication, pat_id))
        new_patient = self.patient_results[-1]
        return new_patient
    def selectHospitalQueue(self, patient):
        selection = np.random.choice(3, 1)[0]
        switcher = [self.ottawa_scan, self.renfrew_scan, self.cornwall_scan]
        switcherName = ['Ottawa Hospital', 'Renfrew', 'Cornwall']
        patient.queued_hospital = switcherName[selection]
        return switcher[selection], switcherName[selection]
    def postScanProcessLogic(self, patient):

        results = {'Delay': 0, 'In System': True}

        # Scan Results
        scan_res = self.random_stream.rand()
        distribution_count = 0
        for i in range(len(self.scan_results_distribution[distribution_count])):
            if scan_res <= self.scan_results_distribution[distribution_count][i]:
                patient.scan_result = self.scan_results_names[i]
                break     
            
        # Preparing Parameters for Later
        patient_need_biopsy = False

        # Scan decisions
        # If Negative Scan
        if patient.scan_result == self.scan_results_names[0]:   
            patient.biopsy_results = 'not performed'         
            # Negative Balking
            negative_return = self.random_stream.rand()
            if not (negative_return < self.negative_return_probability):
                results['In System'] = False
                patient.post_scan_status = 'balked'

        # If Suspicious Scan
        elif patient.scan_result == self.scan_results_names[1]:
            need_biopsy = self.random_stream.rand()
            if need_biopsy <= self.suspicious_need_biopsy_probablity:
                patient_need_biopsy = True

        # If Positive Scan
        elif patient.scan_result == self.scan_results_names[2]:
            patient_need_biopsy = True

        # Generates biopsy results
        if patient_need_biopsy == True:
            self.generateBiopsyResults(patient)    
        else:
            patient.biopsy_results = 'not performed'
        
        if patient.biopsy_results == 'positive biopsy':
            results['In System'] = False

        # Checks if patient leaves the system
        if patient.scan_result == self.scan_results_names[0] and patient.returns == 2:
            patient.post_scan_status = 'left the system'
            results['In System'] = False

        # Generates delay amount
        if patient.biopsy_results != 'positive biopsy' and results['In System'] == True:
            if patient.scan_result == self.scan_results_names[0] or patient.scan_result == self.scan_results_names[1]:
                delay_value= self.random_stream.rand()
                for delay_item in range(len(self.delay_distribution[patient.scan_result]['Delay Prob'])):
                    if delay_value <= self.delay_distribution[patient.scan_result]['Delay Prob'][delay_item]:
                        patient.post_scan_status = f'returns in {self.delay_distribution[patient.scan_result]["Delay Numb"][delay_item]} days'
                        results['Delay'] = self.delay_distribution[patient.scan_result]['Delay Numb'][delay_item]

                        # Adjusts future arrival rates, to accomodate the returning person
                        # future_date = int((np.floor(patient.arrived) + self.delay_distribution[patient.scan_result]['Delay Numb'][delay_item]))
                        # if future_date < self.duration_days and self.historic_arrival_rate_external[future_date] >= 1:
                        #     self.historic_arrival_rate_external[future_date] = self.historic_arrival_rate_external[future_date] - 1
                        break

        return results
    def generateBiopsyResults(self, patient):
        biopsy_results = self.random_stream.rand()
        if biopsy_results <= self.biopsy_positive_result_probablity[patient.scan_result]:
            patient.biopsy_results = 'positive biopsy'
        else:
            patient.biopsy_results = 'negative biopsy'
        
        if patient.biopsy_results == 'positive biopsy':

            # Calculates Adjusted Probabilities
            wait_time = patient.start_scan - patient.arrived
            curr_interval = 0
            cancer_adjusted_probs = self.cancer_results_distribution_non_cumulative.copy()
            while True:
                if (curr_interval+self.cancer_growth_interval) > wait_time:
                    break
                else:
                    curr_interval += self.cancer_growth_interval
                    for i in range(len(cancer_adjusted_probs)):
                        cancer_adjusted_probs[i] = cancer_adjusted_probs[i] * self.cancer_growth_rates[i]
                    cancer_prob_sum = np.sum(cancer_adjusted_probs)
                    for i in range(len(cancer_adjusted_probs)):
                        cancer_adjusted_probs[i] = cancer_adjusted_probs[i] / cancer_prob_sum
            cancer_adjusted_probs = np.cumsum(cancer_adjusted_probs)
            
            # Generates Cancer Stage
            cancer_type = self.random_stream.rand()
            for i in range(len(cancer_adjusted_probs)):
                if cancer_type <= cancer_adjusted_probs[i]:
                    patient.post_scan_status = self.cancer_names[i]
                    break

            if patient.post_scan_status == self.cancer_names[0] or patient.post_scan_status == self.cancer_names[1]:
                patient.post_scan_status = "Stage_1/2"
            else:
                patient.post_scan_status = "Stage_3/4"

    # The following function simulates a schedule for resource capacity
    # It works as follows (a high priority resource takes up the capacity at times when there is no capacity)
    # It lets the previous process finish (allows overflowing) and then takes from the overflow time until the next capacity block
    def scheduledCapacity(self, day, resource, name):
        day_of_week = day%7
        schedule = self.schedule[day_of_week]

        for item in range(len(schedule)):
            if (item%2) == 0:
                with resource.request(priority=-100) as req:
                    print(f'Start of schedule packing {name}: {self.env.now}')
                    yield req
                    hour_of_day = self.env.now%1
                    time_until_next_stage = (schedule[item]/24) - hour_of_day
                    # print(f"Time Now: {self.env.now}, resource taken, duration: {time_until_next_stage}")
                    yield self.env.timeout(time_until_next_stage)
                    print(f'End of schedule packing {name}: {self.env.now}')
            else:
                hour_of_day = self.env.now%1
                time_until_next_stage = (schedule[item]/24) - hour_of_day
                # print(f"Time Now: {self.env.now}, resource not taken, duration: {time_until_next_stage}")
                yield self.env.timeout(time_until_next_stage)        

    # This function deals with generating arrivals, waitlist, and simulate scheduled capacity (main simulation logic)
    def arrivalsNode(self):
        patId = 0
        for day in range(self.duration_days):
        # for day in tqdm(range(self.duration_days), desc=f'Replication {self.replication+1}'):
            print(f'Start of day {day+1}: {self.env.now}')

            # Simulates Schedule for capacity
            print('\tStart of capacity simulation')
            for cap in range(self.ottawa_scan.capacity):
                self.env.process(self.scheduledCapacity(day, self.ottawa_scan, 'ottawa'))
            for cap in range(self.cornwall_scan.capacity):
                self.env.process(self.scheduledCapacity(day, self.cornwall_scan, 'cornwall'))
            for cap in range(self.renfrew_scan.capacity):
                self.env.process(self.scheduledCapacity(day, self.renfrew_scan, 'renfrew'))

            # Initial Waitlist
            if day == 0:
                for wait_list_size in range(self.initial_wait_list):
                    self.env.process(self.patientProcess(patId))
                    patId += 1
                
            print('\tStart of patient simulations for the day')
            # Daily Arrivals
            for patient in range(self.random_stream.poisson(self.historic_arrival_rate_external[day])):
                self.env.process(self.patientProcess(patId))
                patId += 1
            
            # Records queue and proceeds
            self.daily_queue_data.append({'replication': self.replication, 'day': day, 'queue': 'ottawa', 'size': len(self.ottawa_scan.queue)})
            self.daily_queue_data.append({'replication': self.replication, 'day': day, 'queue': 'cornwall', 'size': len(self.cornwall_scan.queue)})
            self.daily_queue_data.append({'replication': self.replication, 'day': day, 'queue': 'renfew', 'size': len(self.renfrew_scan.queue)})


            # Adjusts future arrival rate based on queue
            # if self.daily_queue_data[-1]['size'] >= 100:
            #     for i in range(day+1, len(self.historic_arrival_rate_external)):
            #         if self.historic_arrival_rate_external[i] >= 1:
            #             self.historic_arrival_rate_external[i] -= 0.25 
            # else:                
            #     for i in range(day+1, len(self.historic_arrival_rate_external)):
            #         self.historic_arrival_rate_external[i] += 0.25


            yield self.env.timeout(1)


    # This function executes the simulation
    def mainSimulation(self):
        self.env.process(self.arrivalsNode())
        self.env.run(until=self.duration_days)
    
    
    # This function calculates aggregate results
    def calculateAggregate(self):

        # Patient Data
        
        patient_data = []
        patient_data.append(['replication', 'numb_negative_bf', 'id', 'arrived', 'que_to', 'start', 'end', 'scan_res', 'biopsy_res', 'post_scan_res'])
        for i in self.patient_results:
            data = str(i).split(',')
            data = [i.strip() for i in data]
            patient_data.append(data)
        patient_data = pd.DataFrame(patient_data)
        patient_data.columns = patient_data.iloc[0]
        patient_data = patient_data[1:]
        
        patient_aggregate = dataAnalysis.preProcessing(patient_data)
        patient_aggregate = dataAnalysis.patientDataTypesChange(patient_aggregate)
        patient_aggregate = dataAnalysis.basicColumnsPatientData(patient_aggregate, True, self.warm_up_days)
        del patient_data

        self.cancer_aggregate = patient_aggregate.pipe(dataAnalysis.cancerDetailsAnalysis_Replication)
        # print(self.cancer_aggregate)
        self.time_in_system_aggregate = patient_aggregate.pipe(dataAnalysis.timeInSystemAnalysis_Replication)
        # print(self.time_in_system_aggregate)
        self.total_aggregate = patient_aggregate.pipe(dataAnalysis.totalPatientDetailsAnalysis_Replication)
        # print(self.total_aggregate)

        # Utilization Data
        utilization_data = []
        utilization_data.append(['replication', 'numb_negative_bf', 'id', 'arrived', 'que_to', 'start', 'end', 'scan_res', 'biopsy_res', 'post_scan_res'])
        for i in self.patient_results:
            data = str(i).split(',')
            data = [i.strip() for i in data]
            utilization_data.append(data)
        utilization_data = pd.DataFrame(utilization_data)
        utilization_data.columns = utilization_data.iloc[0]
        utilization_data = utilization_data[1:]
        
        utilization_processed = dataAnalysis.preProcessing(utilization_data)
        utilization_processed = dataAnalysis.patientDataTypesChange(utilization_processed)
        utilization_processed = dataAnalysis.basicColumnsPatientData(utilization_processed, False, self.warm_up_days)
        del utilization_data

        total_minutes = []
        for day_of_week in range(len(self.schedule)):
            total_minutes.append(0)
            for sched in range(len(self.schedule[day_of_week])):
                if (sched%2) == 1:
                    total_minutes[day_of_week] += (self.schedule[day_of_week][sched] - self.schedule[day_of_week][sched-1])*60
                
        self.utilization_aggregate = utilization_processed.pipe(dataAnalysis.aggregateUtilizationAnalysis_Replication, total_minutes, self.capacity, self.replication)
        # print(self.utilization_aggregate)
        del utilization_processed

        # Queue Data
        queue_data = pd.DataFrame(self.daily_queue_data)
        queue_data = queue_data[queue_data['day'] >= self.warm_up_days]
        queue_data = queue_data.pipe(dataAnalysis.preProcessing).pipe(dataAnalysis.queueDataTypesChange)
        self.queue_aggregate = queue_data.pipe(dataAnalysis.aggregateQueueAnalysis_Replication)
        # print(self.queue_aggregate)
        del queue_data



# This class corresponds to each patient, to ease data export
class Patient():
    replication = -1
    patient_id = -1
    arrived = -1
    queued_hospital = ''
    start_scan = -1
    end_scan = -1
    scan_result = ''
    biopsy_results = ''
    post_scan_status = ''
    returns = 0

    def __init__(self, replication, id):
        self.replication = replication
        self.patient_id = id
    def __str__(self):
        return f"{self.replication}, {self.returns}, {self.patient_id}, {self.arrived}, {self.queued_hospital}, {self.start_scan}, {self.end_scan}, {self.scan_result}, {self.biopsy_results}, {self.post_scan_status}"


