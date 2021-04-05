library("zoo")
library("tidyverse")
library("here")
library("sys")
library("gridExtra")

generate_queueVSsarrival_graph <- function(scenarioFolder, scenarioName, arrival_rate) {
  
  
  path <- rstudioapi::getActiveDocumentContext()$path %>% dirname() %>% dirname()
  # Import Data
  raw_multi_arrival <- read_csv(paste(path,"/output/",scenarioFolder,"/",scenarioName,"_arr",arrival_rate,"_multi_raw_arrival.txt",sep=""))
  raw_single_arrival <- read_csv(paste(path,"/output/",scenarioFolder,"/",scenarioName,"_arr",arrival_rate,"_single_raw_arrival.txt",sep=""))
  raw_multi_arrival <- raw_multi_arrival %>% rename(arrival = 'Arrival Amount') %>%
    mutate(Replication=as.factor(Replication))
  raw_single_arrival <- raw_single_arrival %>% rename(arrival = 'Arrival Amount') %>%
    mutate(Replication=as.factor(Replication))
  
  # Preprocessing
  raw_multi_queue <- read_csv(paste(path,"/output/",scenarioFolder,"/",scenarioName,"_arr",arrival_rate,"_multi_raw_queue.txt",sep=""))
  raw_single_queue <- read_csv(paste(path,"/output/",scenarioFolder,"/",scenarioName,"_arr",arrival_rate,"_single_raw_queue.txt",sep=""))
  raw_multi_queue <- raw_multi_queue %>% rename(queue = 'Queued To', queue_amount = 'Queue Amount') %>%
    mutate(Replication=as.factor(Replication)) %>%
    select(-c(queue)) %>% group_by(Replication, Day) %>% summarize(queue = sum(queue_amount)) %>% ungroup()
  raw_single_queue <- raw_single_queue %>% rename(queue = 'Queued To', queue_amount = 'Queue Amount')%>%
    mutate(Replication=as.factor(Replication)) %>%
    select(-c(queue)) %>% group_by(Replication, Day) %>% summarize(queue = sum(queue_amount)) %>% ungroup()
  
  # Raw Stats
  raw_multi_arrival %>% filter(Day >= 3000) %>% 
    select(-c(Day)) %>% group_by(Replication) %>% summarise(mean=mean(arrival)) %>%
    ungroup() %>% summarise(mean_final = mean(mean), sd_final=sd(mean))
  raw_single_arrival %>% filter(Day >= 3000) %>% 
    select(-c(Day)) %>% group_by(Replication) %>% summarise(mean=mean(arrival)) %>%
    ungroup() %>% summarise(mean_final = mean(mean), sd_final=sd(mean))
  raw_multi_queue %>% filter(Day >= 3000) %>%
    select(-c(Day)) %>% group_by(Replication) %>% summarise(mean=mean(queue)) %>%
    ungroup() %>% summarise(mean_final = mean(mean), sd_final=sd(mean))
  raw_single_queue %>% filter(Day >= 3000) %>%
    select(-c(Day)) %>% group_by(Replication) %>% summarise(mean=mean(queue)) %>%
    ungroup() %>% summarise(mean_final = mean(mean), sd_final=sd(mean))
  
  # Combines Data
  raw_multi <- inner_join(raw_multi_arrival, raw_multi_queue, by=c('Replication', 'Day')) %>%
    select(-c(Replication)) %>% group_by(Day) %>%
    summarise(mean_arrival = mean(arrival), mean_queue = mean(queue)) %>% ungroup()
  raw_multi$type <- "Multi Queue"
  raw_signle <- inner_join(raw_single_arrival, raw_single_queue, by=c('Replication', 'Day')) %>%
    select(-c(Replication)) %>% group_by(Day) %>%
    summarise(mean_arrival = mean(arrival), mean_queue = mean(queue)) %>% ungroup()
  raw_signle$type <- "Single Queue"
  raw_data <- rbind(raw_multi, raw_signle)
  
  
  colors <- c("Arrival" = "steelblue2", "Queue/5" = "indianred2", "Mean"="steelblue4")
  pMulti <- ggplot(raw_multi, aes(x=Day)) +
    geom_line(aes(y=mean_arrival), color='grey60')+
    geom_line(aes(y=mean_queue), color='grey60')+
    geom_line(aes(y=rollmean(mean_arrival, 180, na.pad=TRUE), color="Arrival"), size=1)+
    geom_line(aes(y=rollmean(mean_queue, 180, na.pad=TRUE), color="Queue/5"), size=1)+
    ggtitle(paste("Arrival Rate VS Queue Size. Arrival Rate = ",arrival_rate, sep="")) + labs(x = "Simulation Day",y = "People",color = "Legend") + 
    scale_color_manual(values = colors)
  pSingle <- ggplot(raw_signle, aes(x=Day)) +
    geom_line(aes(y=mean_arrival), color='grey60')+
    geom_line(aes(y=mean_queue), color='grey60')+
    geom_line(aes(y=rollmean(mean_arrival, 180, na.pad=TRUE), color="Arrival"), size=1)+
    geom_line(aes(y=rollmean(mean_queue, 180, na.pad=TRUE), color="Queue/5"), size=1)+
    ggtitle(paste("Arrival Rate VS Queue Size. Arrival Rate = ",arrival_rate, sep="")) + labs(x = "Simulation Day",y = "People",color = "Legend") + 
    scale_color_manual(values = colors)
  ggsave(
    filename = paste(path,"/output/",scenarioFolder,"/",scenarioName,"_arr",arrival_rate,"_single_queue_vs_arrivals.jpeg",sep=""),
    pSingle
  )
  ggsave(
    filename = paste(path,"/output/",scenarioFolder,"/",scenarioName,"_arr",arrival_rate,"_multi_queue_vs_arrivals.jpeg",sep=""),
    pMulti
  )
}

for (val in seq(41,50)) {
  generate_queueVSsarrival_graph("BASELINE","baseline",val)
  generate_queueVSsarrival_graph("SCENARIO 1","scn1",val)
  generate_queueVSsarrival_graph("SCENARIO 2","scn2",val)
  generate_queueVSsarrival_graph("SCENARIO 3","scn3",val)
  generate_queueVSsarrival_graph("SCENARIO 4","scn4",val)
  generate_queueVSsarrival_graph("SCENARIO 5","scn5",val)
}

temp_fun <- function(scenarioFolder, scenarioName, queueType, arrival_rate) {
  
  patient_data <- read_csv(
      paste("D:/Documents/Projects/Self/Nadia-Simulation-Python-Uottawa/output/",
            scenarioFolder,"/",scenarioName,
            "_arr",arrival_rate,"_",queueType,"_raw_patients.txt", sep="")
    )
  patient_data <- patient_data %>% rename(nNeg = 'Number of Negatives Scans Before', 
                                          queTo = 'Queued To', stServ = 'Start Service',
                                          enServ = 'End Service', scanRes = 'Scan Results', 
                                          bioRes = 'Biopsy Results', postRes = 'Post Scan Status')
  patient_data <- patient_data %>% filter(Arrived >=1080) %>% filter(stServ >= 0)
  patient_data <- patient_data %>% mutate(wt = stServ-Arrived) %>% 
    mutate(wtGroup = ifelse(wt < 180, 0, 
                            ifelse(wt < 360, 1, 
                                   ifelse( wt < 540, 2, 3))))
  
  percentage <- patient_data %>% filter(bioRes == 'positive biopsy') %>% group_by(postRes, wtGroup) %>% count() %>%
    ungroup(postRes) %>% mutate(freq = n/sum(n)) %>% arrange(wtGroup)
  
  return(percentage)
}

for (val in seq(40,41)) {
 print(val)
 print(
   temp_fun("BASELINE-Test","baseline",'multi',val)
 )
 print(
   temp_fun("BASELINE-Test","baseline",'single',val)
 )
}
