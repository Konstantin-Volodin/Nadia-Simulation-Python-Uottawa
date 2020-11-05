import numpy as np
import pandas as pd

# Reading and Preprocessing of Patient Data
def patientDataTypesChange(df):
    df.iloc[:,0] = pd.to_numeric(df.iloc[:,0])
    df.iloc[:,1] = pd.to_numeric(df.iloc[:,1])
    df.iloc[:,2] = pd.to_numeric(df.iloc[:,2])
    df.iloc[:,4] = pd.to_numeric(df.iloc[:,4])
    df.iloc[:,5] = pd.to_numeric(df.iloc[:,5])
    return df

# Reading and Preprocessing of Queue Data
def queueDataTypesChange(df):
    df.iloc[:,0] = pd.to_numeric(df.iloc[:,0])
    df.iloc[:,1] = pd.to_numeric(df.iloc[:,1])
    df.iloc[:,3] = pd.to_numeric(df.iloc[:,3])
    return df

def preProcessing(df):
    df.columns = [x.strip().replace("\n",'').replace(" ", "_").lower() for x in df.columns]
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    df = df.replace({'\n': '',' ': '_'}, regex=True)
    return df
def flattenMultiIndex(df):
    df_mi = df.columns.tolist()
    df_index = pd.Index([e[0] + "_" + e[1] for e in df_mi])
    df.columns = df_index
    return df

# Analysis Patient Data
# Adding Basic Columns
def basicColumnsPatientData(df):
    df['in_queue'] = df['start_service'] - df['arrived']
    df['in_system'] = df['end_service'] - df['arrived']
    df['service_time'] = (df['end_service'] - df['start_service']) * 24 * 60 
    return df

# Cancer Details
def cancerDetailsAnalysis_Replication(df):
    df = df[df['post_scan_status'] != '']
    df_cancer_details = df.groupby(['post_scan_status', 'replication']).id.agg(['count']).reset_index()
    df_cancer_details['percentage_of_total_scans'] = df_cancer_details['count'] / df_cancer_details.groupby(['replication'])['count'].transform('sum') * 100
    df_cancer_details['percentage_of_positive_biopsies'] = df_cancer_details['count'] / df_cancer_details[df_cancer_details['post_scan_status'].isin(['Stage_1/2', 'Stage_3/4'])].groupby('replication')['count'].transform('sum') * 100
    df_cancer_details = df_cancer_details[df_cancer_details['post_scan_status'].isin(['Stage_1/2', 'Stage_3/4'])]
    return df_cancer_details
def cancerDetailsAnalysis_Simulation(df_cancer_details):
    df_cancer_details = df_cancer_details.drop(['replication'], axis=1).groupby(['post_scan_status']).agg(['mean', 'std', 'max', 'min', 'median'])
    df_cancer_details = df_cancer_details.pipe(flattenMultiIndex)
    df_cancer_details = df_cancer_details.T
    return df_cancer_details

# Time in System Details
def timeInSystemAnalysis_Replication(df):
    df = df[df['post_scan_status'] != '']
    df_time_in_system = df[['replication', 'in_queue', 'in_system', 'service_time']].groupby('replication').agg(['mean', 'max']).reset_index()
    df_time_in_system = df_time_in_system.pipe(flattenMultiIndex)
    df_time_in_system = df_time_in_system.rename(columns={'replication_': 'replication'})
    return df_time_in_system
def timeInSystemAnalysis_Simulation(df_time_in_system):
    df_time_in_system = df_time_in_system.drop(['replication'], axis=1)
    df_time_in_system = df_time_in_system.agg(
        {'in_queue_mean': ['mean', 'std', 'median'],
        'in_queue_max': ['mean', 'std', 'max'],
        'in_system_mean': ['mean', 'std', 'median'],
        'in_system_max': ['mean', 'std', 'max'],
        'service_time_mean': ['mean', 'std', 'median']}
    )
    # df_time_in_system = df_time_in_system.rename(columns={
    #     'in_queue_mean':'days_in_queue', 'in_queue_max': 'overall_max_days_in_queue', 'in_system_mean': 'days_in_system', 'in_system_max': 'overall_max_days_in_system',
    #     'service_time_mean': 'service_time_in_minutes'
    # })
    return df_time_in_system

# Total Patient Details
def totalPatientDetailsAnalysis_Replication(df):
    df_total_unique_arrivals = df[['id', 'replication']].groupby(['replication']).agg(['nunique', 'count']).reset_index()
    df_total_unique_arrivals = df_total_unique_arrivals.rename(columns={'nunique':'total_unique_arrivals', 'count': 'total_patients_returned_to_queue'})

    df_total_patients_served = df[df['end_service'] != -1][['id', 'replication']].groupby(['replication']).agg(['count']).reset_index()
    df_total_patients_served = df_total_patients_served.rename(columns={'count': 'total_patients_served'})

    df_total_patient_details = df_total_unique_arrivals.join(df_total_patients_served.set_index('replication'), on='replication').pipe(flattenMultiIndex)
    df_total_patient_details = df_total_patient_details.rename(columns={'replication_': 'replication'})
    return df_total_patient_details
def totalPatientDetailsAnalysis_Simulation(df_total_patient_details):
    df_total_patient_details = df_total_patient_details.drop(columns=['replication'])
    df_total_patient_details = df_total_patient_details.agg(['mean', 'std', 'max', 'min', 'median'])
    return df_total_patient_details

# Analysis of Queue Data
def aggregateQueueAnalysis_Replication(df):
    df_aggregated_queue = df[['replication','queue', 'size']].rename(columns={'size':'queue_size'}).groupby(['replication','queue']).agg(['mean', 'max']).reset_index().pipe(flattenMultiIndex)
    df_aggregated_queue = df_aggregated_queue.rename(columns={'replication_':'replication','queue_':'queue'})
    return df_aggregated_queue
def aggregateQueueAnalysis_Simulation(df_aggregated_queue):
    df_aggregated_queue = df_aggregated_queue[['queue','queue_size_mean', 'queue_size_max']].groupby('queue').agg({
        'queue_size_mean': ['mean', 'std', 'median'],
        'queue_size_max': ['mean', 'std', 'max']
    })
    return df_aggregated_queue

# Analysis of Utilization Data
def aggregateUtilizationAnalysis_Replication(df, minutes_array, capacity, repl):

    # Adds utilization per patient
    df['day'] = np.floor(df['start_service'])
    df['day_of_week'] = df['day'].mod(7)
    df = df[df['post_scan_status'] != ''].copy()
    new_column = []
    for index, row in df.iterrows():
        new_column.append(
            (row['service_time'] / (minutes_array[int(row['day_of_week'])])) / capacity
        )
    df['utilization'] = np.array(new_column).copy()

    # Aggregates utilization by day
    df = df[['replication', 'day', 'queued_to', 'utilization']].groupby(['replication', 'queued_to', 'day']).agg(['sum']).reset_index().pipe(flattenMultiIndex)
    df = df.rename(columns={'replication_':'replication','day_':'day','utilization_sum':'utilization', 'queued_to_': 'queued_to'})

    # Reindex
    min_day = int(df['day'].min())
    max_day = int(df['day'].max())
    new_index = [i for i in range(min_day,max_day+1)]
    df = df.set_index(['day','queued_to']).unstack(fill_value=0).reindex(new_index, fill_value=0).stack().sort_index(level=1).reset_index()
    df['day_of_week'] = df['day'].mod(7)
    df = df[df['day_of_week'] != 5]
    df = df[df['day_of_week'] != 6]
    df = df[['replication', 'queued_to', 'utilization']]
    df['replication'] = repl

    # Aggregates utilization for replication
    df = df.groupby(['replication','queued_to']).agg(['mean', 'max']).reset_index().pipe(flattenMultiIndex) 
    df = df.rename(columns={'replication_':'replication','queued_to_':'queued_to'})

    return df
def aggregateUtilizationAnalysis_Simulation(df):
    df = df.drop(columns={'replication'}).groupby(['queued_to']).agg({
        'utilization_mean': ['mean', 'std', 'median'],
        'utilization_max': ['mean', 'std', 'max']
    })
    return df
