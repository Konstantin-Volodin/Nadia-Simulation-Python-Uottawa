import simpy 
import numpy as np

class Nadia_Simulation:
    def __init__(self, env):
        self.env = env

        self.warm_up_days = warm_up_days
        self.duration_days = duration_days

        self.initial_wait_list = initial_wait_list
        self.arrival_rate = arrival_rate_per_day
        self.service_time = (15/60)/24

        self.multi_queue = multi_queue

        self.ottawa_scan_capacity = simpy.PriorityResource(env, ottawa_scan_capacity)
        self.renfrew_scan_capacity = simpy.PriorityResource(env, renfrew_scan_capacity)
        self.cornwall_scan_capacity = simpy.PriorityResource(env, cornwall_scan_capacity)
        self.total_scan_capacity = simpy.PriorityResource(env, ottawa_scan_capacity+renfrew_scan_capacity+cornwall_scan_capacity)

        self.scan_results_distribution = np.cumsum(result_distribution)

        self.negative_return_probability = negative_return_probability
        self.negative_return_delay = negative_return_delay
        self.suspicious_need_biopsy_probablity = suspicious_need_biopsy_probablity
        self.suspicious_delay_propbability_distribution = np.cumsum(suspicious_delay_propbability_distribution)
        self.suspicious_delay_duration = suspicious_delay_duration

        self.biopsy_positive_result_probablity = biopsy_positive_result_probablity
        # self.negative_return_probability = negative_return_probability
        print(self.scan_results_distribution)

        self.patient_results = []


    def patientProcess(self, pat_id):
        in_the_system = True
        while in_the_system:

            # Creates new Patient
            new_patient = self.createPatient(pat_id)

            # Arrived Logic
            new_patient.arrived = self.env.now
            # print(f"Patient {pat_id} Arrived: {new_patient.arrived}")

            # Scan Process Logic   
            if self.multi_queue:
                with self.selectHospitalQueue(new_patient).request(priority = 2) as req:
                    yield req
                    new_patient.start_scan = self.env.now
                    # print(f"Patient {pat_id} Started Scan: {new_patient.start_scan}")
                    yield self.env.timeout(self.service_time)
                    new_patient.end_scan = self.env.now
                    # print(f"Patient {pat_id} Finished Scan: {new_patient.end_scan}")
            else: 
                with self.total_scan_capacity.request(priority = 2) as req:
                    new_patient.queued_hospital = "Single Queue"
                    yield req
                    new_patient.start_scan = self.env.now
                    # print(f"Patient {pat_id} Started Scan: {new_patient.start_scan}")
                    yield self.env.timeout(self.service_time)
                    new_patient.end_scan = self.env.now
                    # print(f"Patient {pat_id} Finished Scan: {new_patient.end_scan}")
            
            # Post Scan Logic
            post_scan_decisions = self.postScanProcessLogic(new_patient)
            in_the_system = post_scan_decisions['In System']
            yield self.env.timeout(post_scan_decisions['Delay'])
    def createPatient(self, pat_id):
        self.patient_results.append(Patient())
        new_patient = self.patient_results[-1]
        new_patient.patient_id = pat_id
        return new_patient
    def selectHospitalQueue(self, patient):
        selection = np.random.choice(3, 1)[0]
        switcher = [self.ottawa_scan_capacity, self.renfrew_scan_capacity, self.cornwall_scan_capacity]
        switcherName = ['Ottawa Hospital', 'Renfrew', 'Cornwall']
        patient.queued_hospital = switcherName[selection]
        return switcher[selection]
    def postScanProcessLogic(self, patient):

        results = {'Delay': 0, 'In System': True}
        scan_res = np.random.rand()
                # If Negative
        if scan_res <= self.scan_results_distribution[0]:
            patient.scan_result = 'negative'
            patient.biopsy_results = 'not performed'

            negative_return = np.random.rand()
            if not (negative_return < self.negative_return_probability):
                results['In System'] = False
                patient.post_scan_status = 'balked'
            else:
                patient.post_scan_status = f'returns in {self.negative_return_delay} days'
                results['Delay'] = self.negative_return_delay


            # If suspicious
        elif scan_res <= self.scan_results_distribution[1]:
            patient.scan_result = 'suspicious'

            need_biopsy = np.random.rand()
            if need_biopsy < self.suspicious_need_biopsy_probablity:

                biopsy_results = np.random.rand()
                if biopsy_results < self.biopsy_positive_result_probablity:
                    results['In System'] = False
                    patient.biopsy_results = 'positive biopsy'
                    patient.post_scan_status = 'leave system'
                else:
                    patient.biopsy_results = 'negative biopsy'

                    suspicious_delay = np.random.rand()
                    for delay_item in range(len(self.suspicious_delay_propbability_distribution)):
                        if suspicious_delay < suspicious_delay_propbability_distribution[delay_item]:
                            patient.post_scan_status = f'returns in {self.suspicious_delay_duration[delay_item]} days'
                            results['Delay'] = self.suspicious_delay_duration[delay_item]
                            break

            else:
                patient.biopsy_results = 'not performed'

                suspicious_delay = np.random.rand()
                for delay_item in range(len(self.suspicious_delay_propbability_distribution)):
                    if suspicious_delay < suspicious_delay_propbability_distribution[delay_item]:
                        patient.post_scan_status = f'returns in {self.suspicious_delay_duration[delay_item]} days'
                        results['Delay'] = self.suspicious_delay_duration[delay_item]
                        break



            # If positive
        else:
            patient.scan_result = 'positive'

            biopsy_results = np.random.rand()
            if biopsy_results < self.biopsy_positive_result_probablity:
                results['In System'] = False
                patient.biopsy_results = 'positive biopsy'
                patient.post_scan_status = 'leave system'

            else:
                patient.biopsy_results = 'negative biopsy'

                suspicious_delay = np.random.rand()
                for delay_item in range(len(self.suspicious_delay_propbability_distribution)):
                    if suspicious_delay < suspicious_delay_propbability_distribution[delay_item]:
                        results['Delay'] = self.suspicious_delay_duration[delay_item]
                        patient.post_scan_status = f'returns in {self.suspicious_delay_duration[delay_item]} days'
                        break

        return results

    def scheduledCapacity(self, day):
        day_of_week = day%7
        # print(day_of_week)

        if (day_of_week >= 5):
            print('Weekend')

        else:
            print('Weekday')
        

    def arrivalsNode(self):
        patId = 0
        # Initial Waitlist Generation
        for i in range(self.initial_wait_list):
            self.env.process(self.patientProcess(patId))
            patId += 1
        
        # Arrivals Generation
        for i in range(duration_days):
            self.scheduledCapacity(i)
            for j in range(self.arrival_rate):
                self.env.process(self.patientProcess(patId))
                patId += 1
            yield self.env.timeout(1)


    def mainSimulation(self):
        self.env.process(self.arrivalsNode())
        self.env.run(until=self.duration_days)
        # for i in self.patient_results:
        #     if i.arrived >= self.warm_up_days:
        #         print(i)

class Patient():
    patient_id = -1
    arrived = -1
    queued_hospital = ''
    start_scan = -1
    end_scan = -1
    scan_result = ''
    biopsy_results = ''
    post_scan_status = ''

    def __str__(self):
        return f"ID: {self.patient_id}, Arrived: {self.arrived}, Queue: {self.queued_hospital}, ScanBeg: {self.start_scan}, ScanEnd: {self.end_scan}, ScanRes: {self.scan_result}, Biopsy:{self.biopsy_results}, PostScanStatus: {self.post_scan_status}"



np.random.seed(19972906)

env = simpy.Environment()

warm_up_days = 0
duration_days = 1

initial_wait_list = 100
arrival_rate_per_day = 96


multi_queue = True
ottawa_scan_capacity = 1
renfrew_scan_capacity = 1
cornwall_scan_capacity = 1

result_distribution = [0.85, 0.13, 0.02]

negative_return_probability = 0.50
negative_return_delay = 365
suspicious_need_biopsy_probablity = 0.38
suspicious_delay_propbability_distribution = [0.625, 0.375]
suspicious_delay_duration = [24*7, 12*7]
biopsy_positive_result_probablity = 0.75


simulation = Nadia_Simulation(env)
simulation.mainSimulation()
