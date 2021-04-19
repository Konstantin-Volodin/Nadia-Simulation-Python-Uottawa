library(readr)
library(tidyverse)

testing <- read_csv("D:/Documents/Projects/Self/Nadia-Simulation-Python-Uottawa/output/BASELINE/baseline_arr35_single_raw_patients.txt", 
                      col_types = cols(Arrived = col_number(), 
                                       `End Service` = col_number(), ID = col_number(), 
                                       `Number of Negatives Scans Before` = col_number(), 
                                       Replication = col_number(), `Start Service` = col_number()),
                      col_names = c('replication','numb_negative_bf','id',
                                    'arrived','que_to','start','end',
                                    'scan_res','biopsy_res','post_scan_res'),
                      skip=1)
testing <- testing %>% drop_na() %>% filter(arrived >= 1080)
testing <- testing %>%
    mutate(in_queue = start - arrived) %>%
    mutate(in_system = end - arrived) %>%
    mutate(service_time = (end - start)*24*60)

testing_35_s <- testing

gen_data <- function(arrival_rate, type, scenario, scenario_folder) {
    path <- paste0("D:/Documents/Projects/Self/Nadia-Simulation-Python-Uottawa/output/",
                   scenario_folder, "/", scenario,
                   "_arr", arrival_rate, 
                   "_", type, "_raw_patients.txt")
    print(path)
    data <- read_csv(
        path,
        col_types = cols(Arrived = col_number(), 
                         `End Service` = col_number(), ID = col_number(), 
                         `Number of Negatives Scans Before` = col_number(), 
                         Replication = col_number(), `Start Service` = col_number()),
        col_names = c('replication','numb_negative_bf','id',
                      'arrived','que_to','start','end',
                      'scan_res','biopsy_res','post_scan_res'),
        skip=1)
    data <- data %>% drop_na() %>% filter(arrived >= 1080)
    return (data)
}
bas_25_s <- gen_data(25, 'single', 'baseline', 'BASELINE')
bas_30_s <- gen_data(30, 'single', 'baseline', 'BASELINE')
bas_35_s <- gen_data(35, 'single', 'baseline', 'BASELINE')
bas_40_s <- gen_data(40, 'single', 'baseline', 'BASELINE')

biopsy_details <- testing_25_m %>%
    count(scan_res, biopsy_res) 
biopsy_details %>%
    filter(scan_res == 'Suspicious', biopsy_res != "not performed") %>%
    mutate(p = n/sum(n))
biopsy_details %>%
    filter(scan_res == 'Positive') %>%
    mutate(p = n/sum(n))
biopsy_details %>%
    filter(scan_res == 'Suspicious') %>%
    mutate(p = n/sum(n))


cancer_details <- testing %>%
    group_by(replication, post_scan_res) %>%
    summarize(count = n()) %>%
    filter(post_scan_res %in% c('Stage_1/2', 'Stage_3/4')) %>%
    mutate(percent_of_positive = count/sum(count)) %>%
    mutate(percent_of_total = count/testing %>% count() %>% pull(n))
cancer_details %>% ungroup() %>% group_by(post_scan_res) %>%
    summarize(
        count_mean = mean(count),
        count_std = sd(count),
        count_max = max(count),
        count_min = min(count),
        count_median = median(count)
    )

time_in_system <- testing %>%
    summarize(in_queue_mean = mean(in_queue),
              in_queue_max = max(in_queue),
              in_system_mean = mean(in_system),
              in_system_max = max(in_system),
              service_time_mean = mean(service_time),
              service_time_max = max(service_time),)
time_in_system

testing %>% distinct(id) %>% count()
testing %>% count()
