import simpy 
import numpy as np
import pandas as pd
from copy import deepcopy
from dataclasses import dataclass
from tqdm import trange

from modules import dataAnalysis

class Nadia_Simulation:

    # Initializes parameters
    def __init__(self, env, sim_params, replication, arrival_data):

        # Extra Stuff
        self.env = env
        self.directory = sim_params.directory

        # Input_data
        self.curr_repl = replication
        self.input_data = deepcopy(sim_params)
        self.replication = replication

        # random streams
        self.rand_arrivals = np.random.RandomState()
        self.rand_other = np.random.RandomState()
        self.rand_arrivals.seed(replication)
        self.rand_other.seed(replication)

        # Resource
        self.scan_resource = simpy.PriorityResource(env, self.input_data.arrParams.capacity)

        # Results
        self.patient_results = []
        self.arr_queue_results = {
            'day': [],
            'initial_arrival': [],
            'end_queue': []
        }


    # The following 3 functions deal with process a patient goes through
    def patient_process(self, pat_id):
        
        returns = 0
        while True:

            # Generates a Patient Entry
            self.patient_results.append(Patient(self.replication, pat_id))
            patient = self.patient_results[-1]
            patient.prev_returns = returns
            patient.arrived = round(self.env.now,4)

            with self.scan_resource.request(priority = 2) as resource:

                # Scan Process
                yield resource
                patient.start_scan = round(self.env.now,4)
                timeout_dur = self.rand_other.exponential(self.input_data.arrParams.service_time)
                yield self.env.timeout(timeout_dur)
                patient.end_scan = round(self.env.now,4)

            # Scan Results
            patient.scan_result = self.generate_scan_result()

            # Negative Result Logic
            if patient.scan_result == "Negative":
                patient.post_scan = self.generate_bulk_result(patient)
                if patient.post_scan == 'Stays in System':
                    patient.return_delay = self.generate_delay_amount(patient)

            # Suspicious Result Logic
            if patient.scan_result == 'Suspicious':
                patient.post_scan = self.generate_biopsy_need(patient)
                if patient.post_scan == "Needs Biopsy":
                    patient.biopsy_result = self.generate_biopsy_result(patient)
                    if patient.biopsy_result == "Negative Biopsy":
                        patient.return_delay = self.generate_delay_amount(patient)
                    else:
                        patient.cancer_stage = self.generate_cancer_type(patient)
                else:
                    patient.return_delay = self.generate_delay_amount(patient)
                    
            # Positive Result Logic
            if patient.scan_result == 'Positive':
                patient.biopsy_result = self.generate_biopsy_result(patient)
                if patient.biopsy_result == "Negative Biopsy":
                    patient.return_delay = self.generate_delay_amount(patient)
                else:
                    patient.cancer_stage = self.generate_cancer_type(patient)

            # Leave the system check
            # print(patient)
            if patient.return_delay == None:
                break 
            else: 
                if patient.scan_result == 'Negative':
                    returns += 1
                yield self.env.timeout(patient.return_delay)

    # Intermediate functions in patient process
    def generate_scan_result(self): 
        scan_result = ""
        random_numb = self.rand_other.random()

        for i in range(len(self.input_data.scanResParams.result_distribution)):
            if random_numb <= self.input_data.scanResParams.result_distribution[i]:
                scan_result = self.input_data.scanResParams.result_types[i]
                break

        return scan_result
    def generate_bulk_result(self, patient):
        post_scan_result = ""
        random_numb = self.rand_other.random()

        if patient.prev_returns >= 2:
            post_scan_result = "Left System"
        elif random_numb <= self.input_data.scanResParams.negative_bulk:
            post_scan_result = "Bulked System"
        else:
            post_scan_result = "Stays in System"

        return post_scan_result
    def generate_delay_amount(self, patient):
        delay_result = 0
        delay_distribution = []
        if patient.scan_result == 'Positive':
            delay_distribution = self.input_data.scanResParams.delay_distribution['Suspicious']
        else:
            delay_distribution = self.input_data.scanResParams.delay_distribution[patient.scan_result]
        random_numb = self.rand_other.random()

        for i in range(len(delay_distribution['Delay Prob'])):
            if random_numb <= delay_distribution['Delay Prob'][i]:
                delay_result = delay_distribution['Delay Numb'][i]
                break

        return delay_result
    def generate_biopsy_need(self, patient):
        biopsy_need_result = ""
        random_numb = self.rand_other.random()

        if random_numb <= self.input_data.scanResParams.suspicious_biopsy:
            biopsy_need_result = "Needs Biopsy"
        else:
            biopsy_need_result = "Doesn't Need Biopsy"
        
        return biopsy_need_result
    def generate_biopsy_result(self, patient):
        biopsy_result = ""
        biopsy_distribution = self.input_data.biopsyResParams.cancer_chance[patient.scan_result]
        random_numb = self.rand_other.random()

        if random_numb <= biopsy_distribution:
            biopsy_result = "Positive Biopsy"
        else:
            biopsy_result = "Negative Biopsy"

        return biopsy_result
    def generate_cancer_type(self, patient):
        cancer_result = ''
        patient_wait = patient.end_scan - patient.arrived
        cancer_distribution = deepcopy(self.input_data.biopsyResParams.cancer_staging)
        cancer_growth = self.input_data.biopsyResParams.growth_rate
        growth_interval = self.input_data.biopsyResParams.growth_interval
        random_numb = self.rand_other.random()

        # Converts to density percentage
        cancer_distribution[1:] -= cancer_distribution[:-1].copy()

        # Adjusts Cancer Staging
        counter = 1
        while patient_wait >= counter*growth_interval:
            for i in range(len(cancer_distribution)):
                cancer_distribution[i] += cancer_growth[i]*(growth_interval/30)
            # total = np.sum(cancer_distribution)
            # for i in range(len(cancer_distribution)):
            #     cancer_distribution[i] = cancer_distribution[i]/total
            counter += 1
        cancer_distribution = np.cumsum(cancer_distribution)

        # print(f'PatientWait: {patient_wait}, CancerGrowth: {cancer_growth}, distribution: {cancer_distribution}')

        # Generates Cancer Type
        for i in range(len(cancer_distribution)):
            if random_numb <= cancer_distribution[i]:
                cancer_result = self.input_data.biopsyResParams.cancer_types[i]
                break
        
        return cancer_result

    # The following function simulates a schedule for resource capacity
    # It works as follows (a high priority resource takes up the capacity at times when there is no capacity)
    # It lets the previous process finish (allows overflowing) and then takes from the overflow time until the next capacity block
    def scheduled_capacity(self, day, resource):
        day_of_week = day%7
        schedule = self.input_data.schedule[day_of_week]

        for item in range(len(schedule)):
            if (item%2) == 0:

                with resource.request(priority=-100) as req:
                    yield req
                    hour_of_day = self.env.now%1
                    time_until_next_stage = (schedule[item]/24) - hour_of_day
                    # print(f'\tOccupies Resource at {self.env.now} for {time_until_next_stage}')
                    yield self.env.timeout(time_until_next_stage)
            else:

                # print(f'Current env time {self.env.now}')
                hour_of_day = self.env.now%1
                time_until_next_stage = (schedule[item]/24) - hour_of_day
                # print(f'\tDoesnt occupie Resource at {self.env.now} for {time_until_next_stage}')
                yield self.env.timeout(time_until_next_stage)       
    # This function deals with generating arrivals, waitlist, and simulate scheduled capacity (main simulation logic)
    def arrivals_node(self):
        
        patId = 0
        adjust_counter = 0
        adjust_mem = 'less'
        adjust_dur = 5
        adjust_size = 1000

        for day in range(self.input_data.simParams.duration):
            # print(f'DAY {day+1}')
            # Simulates busy Intervals
            for cap in range(self.input_data.arrParams.capacity):
                self.env.process(self.scheduled_capacity(day, self.scan_resource))

            # Generates Daily Arrivals
            arrivals = self.rand_arrivals.poisson(self.input_data.arrParams.arrival_rate)
            for i in range(arrivals):
                self.env.process(self.patient_process(patId))
                patId += 1

            # Finishes up a day in the simulation
            yield self.env.timeout(1)

            # Saves Arrival & Queue  Data
            self.arr_queue_results['day'].append(day+1)
            self.arr_queue_results['initial_arrival'].append(self.input_data.arrParams.arrival_rate)
            self.arr_queue_results['end_queue'].append(len(self.scan_resource.queue))

            # print(f'Queue Size: {len(self.scan_resource.queue)}, mem: {adjust_mem}, counter: {adjust_counter}, old_arr: {self.input_data.arrParams.arrival_rate}', end=', ')
            # Adjusts Arriavl rate
            # if len(self.scan_resource.queue) >= adjust_size:
            #     if adjust_mem == 'more':
            #         adjust_counter += 1
            #     else:
            #         adjust_mem = 'more'
            #         adjust_counter = 1
            # else: 
            #     if adjust_mem == 'less':
            #         adjust_counter += 1
            #     else:
            #         adjust_mem = 'less'
            #         adjust_counter = 1

            # if adjust_counter >= adjust_dur:
            #     if adjust_mem == 'less':
            #         self.input_data.arrParams.arrival_rate += 1
            #         adjust_counter = 0
            #     else:
            #         self.input_data.arrParams.arrival_rate -= 1
            #         if self.input_data.arrParams.arrival_rate < 0: self.input_data.arrParams.arrival_rate = 0
            #         adjust_counter = 0
            # # print(f'new arrival: {self.input_data.arrParams.arrival_rate}')

    # This function executes the simulation
    def main_simulation(self):
        self.env.process(self.arrivals_node())
        self.env.run(until=self.input_data.simParams.duration)

    # Exports data
    def export_data(self):
        df = pd.DataFrame([x.as_dict() for x in self.patient_results])
        self.patient_results = df

        df2 = pd.DataFrame(self.arr_queue_results)
        self.arr_queue_results = df2

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
@dataclass
class Patient():
    replication: int
    patient_id: int
    prev_returns: int = None
    arrived: float = None
    start_scan: float = None
    end_scan: float = None
    scan_result: str = None
    post_scan: str = None
    return_delay: str = None
    biopsy_result: str = None
    cancer_stage: str = None

    def __init__(self, replication, id):
        self.replication = replication
        self.patient_id = id
    
    def as_dict(self):
        return {
            'replication': self.replication,
            'patient_id': self.patient_id,
            'prev_neg_returns': self.prev_returns,
            'arrived': self.arrived,
            'start_scan': self.start_scan,
            'end_scan': self.end_scan,
            'scan_result': self.scan_result,
            'post_scan_result': self.post_scan,
            'biopsy_result': self.biopsy_result,
            'cancer_stage': self.cancer_stage,
            'return_delay': self.return_delay
        }