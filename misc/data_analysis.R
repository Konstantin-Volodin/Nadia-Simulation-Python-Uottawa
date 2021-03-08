library(readr)
library(tidyverse)

testing <- read_csv("C:/Volodin.K/Work Documents/Nadia-Simulation-Python-Uottawa/testing30.txt", 
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

cancer_details <- testing %>%
    group_by(post_scan_res) %>%
    summarize(count = n()) %>%
    filter(post_scan_res %in% c('Stage_1/2', 'Stage_3/4')) %>%
    mutate(percent_of_positive = count/sum(count)) %>%
    mutate(percent_of_total = count/testing %>% count() %>% pull(n))
cancer_details

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
