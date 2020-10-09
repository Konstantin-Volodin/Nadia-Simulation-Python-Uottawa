import simpy 
import numpy as np
from tqdm import tqdm

import math
import os

class Nadia_Simulation:

    # Initializes parameters
    def __init__(self, env, sim_params, replication):
        self.env = env
        self.directory = sim_params.directory
        self.replication = replication
        self.random_stream = np.random.RandomState()
        self.random_stream.seed(replication)

        self.warm_up_days = sim_params.warm_up_days
        self.duration_days = sim_params.duration_days
        self.initial_wait_list = sim_params.initial_wait_list
        self.arrival_rate = sim_params.arrival_rate_per_day
        self.service_time = sim_params.service_time
        self.ottawa_scan = simpy.PriorityResource(env, sim_params.ottawa_scan_capacity)
        self.renfrew_scan = simpy.PriorityResource(env, sim_params.renfrew_scan_capacity)
        self.cornwall_scan = simpy.PriorityResource(env, sim_params.cornwall_scan_capacity)

        self.scan_results_names = sim_params.results_names
        self.scan_results_distribution = np.cumsum(sim_params.result_distribution)
        self.negative_return_probability = sim_params.negative_return_probability
        self.negative_return_delay = sim_params.negative_return_delay
        self.suspicious_need_biopsy_probablity = sim_params.suspicious_need_biopsy_probablity
        self.biopsy_positive_result_probablity = sim_params.biopsy_positive_result_probablity
        self.cancer_names = sim_params.cancer_types
        self.cancer_results_distribution = np.cumsum(sim_params.cancer_probability_distribution)

        self.suspicious_delay_propbability_distribution = np.cumsum(sim_params.suspicious_delay_propbability_distribution)
        self.suspicious_delay_duration = sim_params.suspicious_delay_duration

        self.patient_results = []
        self.daily_queue_data = []


    # The following 3 functions deal with process a patient goes through
    def patientProcess(self, pat_id):
        in_the_system = True
        while in_the_system:

            # Creates new Patient
            new_patient = self.createPatient(self.replication, pat_id)

            # Arrived Logic
            new_patient.arrived = self.env.now
            # print(f"Patient {pat_id} Arrived: {new_patient.arrived}")

            # Scan Process Logic   
            with self.selectHospitalQueue(new_patient).request(priority=2) as req:
                yield req
                new_patient.start_scan = self.env.now
                # print(f"Patient {pat_id} Started Scan: {new_patient.start_scan}")
                yield self.env.timeout(self.random_stream.exponential(self.service_time))
                new_patient.end_scan = self.env.now
                # print(f"Patient {pat_id} Finished Scan: {new_patient.end_scan}")
            
            # Post Scan Logic
            post_scan_decisions = self.postScanProcessLogic(new_patient)
            in_the_system = post_scan_decisions['In System']
            yield self.env.timeout(post_scan_decisions['Delay'])
    def createPatient(self, replication, pat_id):
        self.patient_results.append(Patient(replication, pat_id))
        new_patient = self.patient_results[-1]
        return new_patient
    def selectHospitalQueue(self, patient):
        selection = np.random.choice(3, 1)[0]
        switcher = [self.ottawa_scan, self.renfrew_scan, self.cornwall_scan]
        switcherName = ['Ottawa Hospital', 'Renfrew', 'Cornwall']
        patient.queued_hospital = switcherName[selection]
        return switcher[selection]
    def postScanProcessLogic(self, patient):

        results = {'Delay': 0, 'In System': True}
        scan_res = self.random_stream.rand()

        # If Negative
        if scan_res <= self.scan_results_distribution[0]:
            patient.scan_result = self.scan_results_names[0]
            patient.biopsy_results = 'not performed'

            negative_return = self.random_stream.rand()
            if not (negative_return < self.negative_return_probability):
                results['In System'] = False
                patient.post_scan_status = 'balked'
            else:
                patient.post_scan_status = f'returns in {self.negative_return_delay} days'
                results['Delay'] = self.negative_return_delay


        # If suspicious
        elif scan_res <= self.scan_results_distribution[1]:
            patient.scan_result = self.scan_results_names[1]

            need_biopsy = self.random_stream.rand()
            if need_biopsy <= self.suspicious_need_biopsy_probablity:

                biopsy_results = self.random_stream.rand()
                if biopsy_results <= self.biopsy_positive_result_probablity:
                    results['In System'] = False
                    patient.biopsy_results = 'positive biopsy'
                    
                    cancer_type = self.random_stream.rand()
                    for cancer_item in range(len(self.cancer_results_distribution)):
                        if cancer_type <= self.cancer_results_distribution[cancer_item]:
                            patient.post_scan_status = self.cancer_names[cancer_item]
                            break

                else:
                    patient.biopsy_results = 'negative biopsy'
                    suspicious_delay = self.random_stream.rand()
                    for delay_item in range(len(self.suspicious_delay_propbability_distribution)):
                        if suspicious_delay <= self.suspicious_delay_propbability_distribution[delay_item]:
                            patient.post_scan_status = f'returns in {self.suspicious_delay_duration[delay_item]} days'
                            results['Delay'] = self.suspicious_delay_duration[delay_item]
                            break

            else:
                patient.biopsy_results = 'not performed'

                suspicious_delay = self.random_stream.rand()
                for delay_item in range(len(self.suspicious_delay_propbability_distribution)):
                    if suspicious_delay <= self.suspicious_delay_propbability_distribution[delay_item]:
                        patient.post_scan_status = f'returns in {self.suspicious_delay_duration[delay_item]} days'
                        results['Delay'] = self.suspicious_delay_duration[delay_item]
                        break



        # If positive
        else:
            patient.scan_result = self.scan_results_names[2]

            biopsy_results = self.random_stream.rand()
            if biopsy_results < self.biopsy_positive_result_probablity:
                results['In System'] = False
                patient.biopsy_results = 'positive biopsy'

                cancer_type = self.random_stream.rand()
                for cancer_item in range(len(self.cancer_results_distribution)):
                    if cancer_type <= self.cancer_results_distribution[cancer_item]:
                        patient.post_scan_status = self.cancer_names[cancer_item]
                        break

            else:
                patient.biopsy_results = 'negative biopsy'

                suspicious_delay = self.random_stream.rand()
                for delay_item in range(len(self.suspicious_delay_propbability_distribution)):
                    if suspicious_delay <= self.suspicious_delay_propbability_distribution[delay_item]:
                        results['Delay'] = self.suspicious_delay_duration[delay_item]
                        patient.post_scan_status = f'returns in {self.suspicious_delay_duration[delay_item]} days'
                        break

        return results


    # The following function simulates a schedule for resource capacity
    # It works as follows (a high priority resource takes up the capacity at times when there is no capacity)
    # It lets the previous process finish (allows overflowing) and then takes from the overflow time until the next capacity block
    def scheduledCapacity(self, day, resource):
        day_of_week = day%7
        schedule = []

        if (day_of_week >= 5):
            schedule = [[24,1]]
        else:
            schedule = [[8,1],[16,0],[24,1]]

        # print(schedule)
        for element in schedule:
            if element[1] == 1:
                with resource.request(priority=-100) as req:
                    yield req
                    hour_of_day = self.env.now%1
                    time_until_next_stage = (element[0]/24) - hour_of_day
                    yield self.env.timeout(time_until_next_stage)
            else:
                hour_of_day = self.env.now%1
                time_until_next_stage = (element[0]/24) - hour_of_day
                yield self.env.timeout(time_until_next_stage)        

    # This function deals with generating arrivals, waitlist, and simulate scheduled capacity (main simulation logic)
    def arrivalsNode(self):
        patId = 0
        for day in range(self.duration_days):
        # for day in tqdm(range(self.duration_days), desc=f'Replication {self.replication+1}'):
            # print(f"Simulation Day {day+1}")

            # Simulates Schedule for capacity
            for cap in range(self.ottawa_scan.capacity):
                self.env.process(self.scheduledCapacity(day, self.ottawa_scan))
            for cap in range(self.cornwall_scan.capacity):
                self.env.process(self.scheduledCapacity(day, self.cornwall_scan))
            for cap in range(self.renfrew_scan.capacity):
                self.env.process(self.scheduledCapacity(day, self.renfrew_scan))

            # Initial Waitlist
            if day == 0:
                for wait_list_size in range(self.initial_wait_list):
                    self.env.process(self.patientProcess(patId))
                    patId += 1
                

            # Daily Arrivals
            for patient in range(self.random_stream.poisson(self.arrival_rate)):
                self.env.process(self.patientProcess(patId))
                patId += 1
            
            # Records queue and proceeds
            if day > 0:
                self.daily_queue_data.append(
                    len(self.ottawa_scan.queue)+ len(self.cornwall_scan.queue) + len(self.renfrew_scan.queue)
                )
            else:
                self.daily_queue_data.append(self.initial_wait_list)

            yield self.env.timeout(1)


    # This function executes the simulation
    def mainSimulation(self):
        self.env.process(self.arrivalsNode())
        self.env.run(until=self.duration_days)
    

    # This function outputs raw results
    def outputRaw(self, output_string):
        with open(f"{self.directory}/{output_string}_multi_patients.txt", "a") as text_file:
            for i in self.patient_results:
                if i.arrived >= self.warm_up_days:
                    print(i, file=text_file)
        with open(f"{self.directory}/{output_string}_multi_queue.txt", "a") as text_file:
            for i in range(len(self.daily_queue_data)):
                if i >= self.warm_up_days:
                    print(f"{self.replication}, {i+1}, {self.daily_queue_data[i]}", file=text_file)


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

    def __init__(self, replication, id):
        self.replication = replication
        self.patient_id = id
    def __str__(self):
        return f"{self.replication}, {self.patient_id}, {self.arrived}, {self.queued_hospital}, {self.start_scan}, {self.end_scan}, {self.scan_result}, {self.biopsy_results}, {self.post_scan_status}"


