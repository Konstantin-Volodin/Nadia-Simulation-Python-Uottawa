library(here)
library(arrow)
library(tidyverse)

data <- arrow::read_feather(here('output', 'testing.feather'))
data <- data %>% 
  mutate(wait_time = start_scan - arrived) %>%
  mutate(in_system = end_scan - arrived) %>%
  mutate(service_time = end_scan - start_scan) %>% 
  mutate(wait_time_cat=cut(wait_time, 
                           breaks=c(-1, 180, 180*2, 180*3, 180*4, 180*5, 180*6, 180*7, 180*9, 180*10, Inf), 
                           labels=c("0-6 Month","6-12 Month","12-18 Month", "18-24 Month", "24-30 Month", "30-36 Month", 
                                    "36-42 Month", "42-48 Month", "48-54 Month", "54-60 Month")))

# Checks Numbers
data %>% distinct(patient_id) %>% count() # Arrivals
data %>% drop_na(end_scan) %>% count() # Total Scanned
data %>% count() - data %>% distinct(patient_id) %>% count() # Total Returns
data %>% summarize(service_time = mean(service_time, na.rm = T), # Average Times
                   wait_time = mean(wait_time, na.rm = T),
                   in_system = mean(in_system, na.rm = T))

# Makes Sure data is saved correctly
data %>% distinct(replication)
data %>% distinct(prev_neg_returns)
data %>% distinct(scan_result)
data %>% distinct(post_scan_result)
data %>% distinct(biopsy_result)
data %>% distinct(cancer_stage)
data %>% distinct(return_delay)


# Scan Distribution
data %>% count(scan_result) %>% drop_na() %>% mutate(p = n/sum(n)*100)


# Negative Scan Checking
data %>% filter(scan_result == "Negative") %>% distinct(post_scan_result)
data %>% filter(scan_result == "Negative") %>% distinct(biopsy_result)
data %>% filter(scan_result == "Negative") %>% distinct(cancer_stage)
data %>% filter(scan_result == "Negative") %>% distinct(return_delay)
data %>% filter(scan_result == "Negative") %>% distinct(wait_time_cat)
data %>% filter(scan_result == "Negative") %>% count(prev_neg_returns, post_scan_result) %>% # Balking
  group_by(prev_neg_returns) %>% mutate(p = n/sum(n)*100)
data %>% filter(scan_result == "Negative") %>% count(post_scan_result, return_delay) %>% # Return Delay
  group_by(post_scan_result) %>% mutate(p = n/sum(n)*100)

# Suspicious Scan Checking
data %>% filter(scan_result == "Suspicious") %>% distinct(post_scan_result)
data %>% filter(scan_result == "Suspicious") %>% distinct(biopsy_result)
data %>% filter(scan_result == "Suspicious") %>% distinct(cancer_stage)
data %>% filter(scan_result == "Suspicious") %>% distinct(return_delay)
data %>% filter(scan_result == "Suspicious") %>% distinct(wait_time_cat)
data %>% filter(scan_result == "Suspicious") %>% count(post_scan_result) %>% mutate(p=n/sum(n)) # Biopsy Need Distribution
data %>% filter(scan_result == "Suspicious") %>% count(post_scan_result, biopsy_result) %>% # Biopsy Distribution
  group_by(post_scan_result) %>% mutate(p=n/sum(n)) 
data %>% filter(scan_result == "Suspicious") %>% count(post_scan_result, biopsy_result, return_delay) %>% # Return Delay Distribution
  group_by(post_scan_result, biopsy_result) %>% mutate(p=n/sum(n)) 
data %>% filter(scan_result == "Suspicious") %>% count(wait_time_cat, biopsy_result, cancer_stage) %>% # Cancer Staging
  group_by(biopsy_result, wait_time_cat) %>% mutate(p=n/sum(n))

# Positive Scan Checking
data %>% filter(scan_result == "Positive") %>% distinct(post_scan_result)
data %>% filter(scan_result == "Positive") %>% distinct(biopsy_result)
data %>% filter(scan_result == "Positive") %>% distinct(cancer_stage)
data %>% filter(scan_result == "Positive") %>% distinct(return_delay)
data %>% filter(scan_result == "Positive") %>% distinct(wait_time_cat)
data %>% filter(scan_result == "Positive") %>% count(biopsy_result) %>% mutate(p=n/sum(n))  # Biopsy Distribution
data %>% filter(scan_result == "Positive") %>% count(biopsy_result, return_delay) %>% # Return Delay Distribution
  group_by(biopsy_result) %>% mutate(p=n/sum(n)) 
data %>% filter(scan_result == "Positive") %>% count(wait_time_cat, biopsy_result, cancer_stage) %>% # Cancer Staging
  group_by(biopsy_result, wait_time_cat) %>% mutate(p=n/sum(n))

