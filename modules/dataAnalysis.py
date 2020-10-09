import numpy as np
import pandas as pd

# Reading and Preprocessing of Patient Data
def readPatientDataFile(stringPath):
    data = []
    with open(f'{stringPath}.txt', 'r') as txt_file:
        for line in txt_file:
            data.append(line.split(','))
    data = np.array(data)
    df = pd.DataFrame(data=data[1:], columns=data[0])
    return df
def patientDataTypesChange(df):
    df.iloc[:,0] = pd.to_numeric(df.iloc[:,0])
    df.iloc[:,1] = pd.to_numeric(df.iloc[:,1])
    df.iloc[:,2] = pd.to_numeric(df.iloc[:,2])
    df.iloc[:,4] = pd.to_numeric(df.iloc[:,4])
    df.iloc[:,5] = pd.to_numeric(df.iloc[:,5])
    return df

# Reading and Preprocessing of Queue Data
def readQueueDataFile(stringPath):
    data = []
    with open(f'{stringPath}.txt', 'r') as txt_file:
        for line in txt_file:
            data.append(line.split(','))
    data = np.array(data)
    df = pd.DataFrame(data=data[1:], columns=data[0])
    return df
def queueDataTypesChange(df):
    df.iloc[:,0] = pd.to_numeric(df.iloc[:,0])
    df.iloc[:,1] = pd.to_numeric(df.iloc[:,1])
    df.iloc[:,2] = pd.to_numeric(df.iloc[:,2])
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
def basicColumns(df):
    df['in_queue'] = df['start_service'] - df['arrived']
    df['in_system'] = df['end_service'] - df['arrived']
    df['service_time'] = (df['end_service'] - df['start_service']) * 24 * 60 
    return df
# Cancer Details
def cancerDetailsAnalysis(df):
    df = df[df['post_scan_status'] != '']
    df_cancer_details = df.groupby(['post_scan_status', 'replication']).id.agg(['count']).reset_index()
    df_cancer_details['percentage_of_total_scans'] = df_cancer_details['count'] / df_cancer_details.groupby(['replication'])['count'].transform('sum') * 100
    df_cancer_details['percentage_of_positive_biopsies'] = df_cancer_details['count'] / df_cancer_details[df_cancer_details['post_scan_status'].isin(['Stage_1', 'Stage_2', 'Stage_3', 'Stage_4'])].groupby('replication')['count'].transform('sum') * 100
    df_cancer_details = df_cancer_details[df_cancer_details['post_scan_status'].isin(['Stage_1', 'Stage_2', 'Stage_3', 'Stage_4'])]
    df_cancer_details = df_cancer_details.drop(['replication'], axis=1).groupby(['post_scan_status']).agg(['mean', 'std', 'max', 'min', 'median'])
    df_cancer_details = df_cancer_details.pipe(flattenMultiIndex)
    df_cancer_details = df_cancer_details.T
    return df_cancer_details
# Time in System Details
def timeInSystemAnalysis(df):
    df = df[df['post_scan_status'] != '']
    df_time_in_system = df[['replication', 'in_queue', 'in_system', 'service_time']].groupby('replication').agg(['mean', 'max']).reset_index()
    df_time_in_system = df_time_in_system.pipe(flattenMultiIndex)
    df_time_in_system = df_time_in_system.drop(['replication_'], axis=1)
    df_time_in_system = df_time_in_system.agg(
        {'in_queue_mean': ['mean', 'std', 'max', 'min', 'median'],
        'in_queue_max': ['max'],
        'in_system_mean': ['mean', 'std', 'max', 'min', 'median'],
        'in_system_max': ['max'],
        'service_time_mean': ['mean', 'std', 'max', 'min', 'median']}
    )
    df_time_in_system = df_time_in_system.rename(columns={
        'in_queue_mean':'days_in_queue', 'in_queue_max': 'overall_max_days_in_queue', 'in_system_mean': 'days_in_system', 'in_system_max': 'overall_max_days_in_system',
        'service_time_mean': 'service_time_in_minutes'
    })
    return df_time_in_system
# Total Patient Details
def totalPatientDetailsAnalysis(df):
    df_total_unique_arrivals = df[['id', 'replication']].groupby(['replication']).agg(['nunique', 'count']).reset_index()
    df_total_unique_arrivals = df_total_unique_arrivals.rename(columns={'nunique':'total_unique_arrivals', 'count': 'total_patients_returned_to_queue'})

    df_total_patients_served = df[df['end_service'] != -1][['id', 'replication']].groupby(['replication']).agg(['count']).reset_index()
    df_total_patients_served = df_total_patients_served.rename(columns={'count': 'total_patients_served'})

    df_total_patient_details = df_total_unique_arrivals.join(df_total_patients_served.set_index('replication'), on='replication').pipe(flattenMultiIndex)
    df_total_patient_details = df_total_patient_details.drop(columns=['replication_'])
    df_total_patient_details = df_total_patient_details.agg(['mean', 'std', 'max', 'min', 'median'])
    return df_total_patient_details

# Analysis of Queue Data
def aggregateQueueAnalysis(df):
    df_aggregated_queue = df[['replication','queue_amount']].groupby(['replication']).agg(['mean', 'max']).reset_index().pipe(flattenMultiIndex).drop(columns={'replication_'}).agg({
        'queue_amount_mean': ['mean', 'std', 'max', 'min', 'median'],
        'queue_amount_max': ['max']
    }).rename(columns={
        'queue_amount_mean': 'number_in_queue',
        'queue_amount_max': 'overall_max_in_queue'
    })
    return df_aggregated_queue


def main_analysis(patient_path, queue_path, output_path):
    # Execution of Patient Data
    df = readPatientDataFile(patient_path).pipe(preProcessing).pipe(patientDataTypesChange).pipe(basicColumns)
    df_cancer_details = cancerDetailsAnalysis(df)
    df_time_in_system = timeInSystemAnalysis(df)
    df_totals_details = totalPatientDetailsAnalysis(df)

    # Execution of Queue Data
    df = readQueueDataFile(queue_path).pipe(preProcessing).pipe(queueDataTypesChange)
    df_aggregated_queue = aggregateQueueAnalysis(df)

    with open(f'{output_path}.txt', "w") as text_file:
        print(df_totals_details, file=text_file)
        print('\n\n',file=text_file)
        print(df_time_in_system, file=text_file)
        print('\n\n',file=text_file)
        print(df_cancer_details, file=text_file)
        print('\n\n',file=text_file)
        print(df_aggregated_queue, file=text_file)