library("zoo")
library("tidyverse")
library("here")
library("sys")
library("gridExtra")

generate_queueVSsarrival_graph <- function(scenarioFolder, scenarioName) {
  # Import Data
  mm1_arrival <- read_csv(here("output",scenarioFolder,paste0(scenarioName,"_mm1_raw_arrival.txt")))
  mm3_arrival <- read_csv(here("output",scenarioFolder,paste0(scenarioName,"_mm3_raw_arrival.txt")))
  mm1_arrival <- mm1_arrival %>% rename(arrival = 'Arrival Amount') %>%
    mutate(Replication=as.factor(Replication))
  mm3_arrival <- mm3_arrival %>% rename(arrival = 'Arrival Amount') %>%
    mutate(Replication=as.factor(Replication))
  
  # Preprocessing
  mm1_queue <- read_csv(here("output",scenarioFolder,paste0(scenarioName,"_mm1_raw_queue.txt")))
  mm3_queue <- read_csv(here("output",scenarioFolder,paste0(scenarioName,"_mm3_raw_queue.txt")))
  mm1_queue <- mm1_queue %>% rename(queue = 'Queued To', queue_amount = 'Queue Amount') %>%
    mutate(Replication=as.factor(Replication)) %>%
    select(-c(queue)) %>% group_by(Replication, Day) %>% summarize(queue = sum(queue_amount)) %>% ungroup()
  mm3_queue <- mm3_queue %>% rename(queue = 'Queued To', queue_amount = 'Queue Amount') %>%
    mutate(Replication=as.factor(Replication)) %>%
    select(-c(queue)) %>% group_by(Replication, Day) %>% summarize(queue = sum(queue_amount)) %>% ungroup()
  
  # Raw Stats
  mm1_arrival %>% filter(Day >= 2500) %>% 
    select(-c(Day)) %>% group_by(Replication) %>% summarise(mean=mean(arrival)) %>%
    ungroup() %>% summarise(mean_final = mean(mean), sd_final=sd(mean))
  mm3_arrival %>% filter(Day >= 2500) %>% 
    select(-c(Day)) %>% group_by(Replication) %>% summarise(mean=mean(arrival)) %>%
    ungroup() %>% summarise(mean_final = mean(mean), sd_final=sd(mean))
  mm1_queue %>% filter(Day >= 2500) %>%
    select(-c(Day)) %>% group_by(Replication) %>% summarise(mean=mean(queue)) %>%
    ungroup() %>% summarise(mean_final = mean(mean), sd_final=sd(mean))
  mm3_queue %>% filter(Day >= 2500) %>%
    select(-c(Day)) %>% group_by(Replication) %>% summarise(mean=mean(queue)) %>%
    ungroup() %>% summarise(mean_final = mean(mean), sd_final=sd(mean))
  
  # Combines Data
  mm1 <- inner_join(mm1_arrival, mm1_queue, by=c('Replication', 'Day')) %>%
    select(-c(Replication)) %>% group_by(Day) %>%
    summarise(mean_arrival = mean(arrival), mean_queue = mean(queue)) %>% ungroup()
  mm1$type <- "MM1"
  mm3 <- inner_join(mm3_arrival, mm3_queue, by=c('Replication', 'Day')) %>%
    select(-c(Replication)) %>% group_by(Day) %>%
    summarise(mean_arrival = mean(arrival), mean_queue = mean(queue)) %>% ungroup()
  mm3$type <- "MM3"
  raw_data <- rbind(mm1, mm3)
  
  
  colors <- c("Arrival" = "steelblue2", "Queue/100" = "indianred2", "Mean"="steelblue4")
  pmm1 <- ggplot(mm1, aes(x=Day)) +
    geom_line(aes(y=mean_arrival), color='grey60')+
    geom_line(aes(y=mean_queue/100), color='grey60')+
    geom_line(aes(y=rollmean(mean_arrival, 180, na.pad=TRUE), color="Arrival"), size=1)+
    geom_line(aes(y=rollmean(mean_queue/100, 180, na.pad=TRUE), color="Queue/100"), size=1) +
    geom_hline(aes(yintercept = mean(mm1 %>% filter(Day >= 2500) %>% pull(mean_arrival)))) +
    geom_text(aes(2500,
                  mean(mm1 %>% filter(Day >= 2500) %>% pull(mean_arrival)) + 3,
                  label = mean(mm1 %>% filter(Day >= 2500) %>% pull(mean_arrival)) %>% round(2),
                  size = 2)) +
    ggtitle("MM1 - Arrival Rate VS Queue Size") + labs(x = "Simulation Day",y = "People",color = "Legend") + 
    scale_color_manual(values = colors)
  pmm3 <- ggplot(mm3, aes(x=Day)) +
    geom_line(aes(y=mean_arrival), color='grey60')+
    geom_line(aes(y=mean_queue/100), color='grey60')+
    geom_line(aes(y=rollmean(mean_arrival, 180, na.pad=TRUE), color="Arrival"), size=1)+
    geom_line(aes(y=rollmean(mean_queue/100, 180, na.pad=TRUE), color="Queue/100"), size=1)+
    geom_hline(aes(yintercept = mean(mm3 %>% filter(Day >= 2500) %>% pull(mean_arrival)))) +
    geom_text(aes(2500,
                  mean(mm3 %>% filter(Day >= 2500) %>% pull(mean_arrival)) + 3,
                  label = mean(mm3 %>% filter(Day >= 2500) %>% pull(mean_arrival)) %>% round(2),
                  size = 2)) +
    ggtitle("MM3 - Arrival Rate VS Queue Size") + labs(x = "Simulation Day",y = "People",color = "Legend") + 
    scale_color_manual(values = colors)
  p <- grid.arrange(pmm1, pmm3)
  # return(p)
  ggsave(filename = here("output",scenarioFolder,paste0(scenarioName,"_plot.jpeg")), p, width=10, height=10)
}

generate_queueVSsarrival_graph('Steady_State_Arrival', 'base')
generate_queueVSsarrival_graph('Steady_State_Arrival', 'scn1')
generate_queueVSsarrival_graph('Steady_State_Arrival', 'scn2')
generate_queueVSsarrival_graph('Steady_State_Arrival', 'scn3')
generate_queueVSsarrival_graph('Steady_State_Arrival', 'scn4')
generate_queueVSsarrival_graph('Steady_State_Arrival', 'scn5')
