library("zoo")
library("tidyverse")

# Import Data
raw_multi_arrival <- read_csv("D:/Documents/Projects/Self/Nadia-Simulation-Python-Uottawa/output/raw_multi_arrival.txt")
raw_single_arrival <- read_csv("D:/Documents/Projects/Self/Nadia-Simulation-Python-Uottawa/output/raw_signle_arrival.txt")
raw_multi_arrival <- raw_multi_arrival %>% rename(arrival = 'Arrival Amount') %>%
  mutate(Replication=as.factor(Replication))
raw_single_arrival <- raw_single_arrival %>% rename(arrival = 'Arrival Amount') %>%
  mutate(Replication=as.factor(Replication))

# Preprocessing
raw_multi_queue <- read_csv("D:/Documents/Projects/Self/Nadia-Simulation-Python-Uottawa/output/raw_multi_queue.txt")
raw_single_queue <- read_csv("D:/Documents/Projects/Self/Nadia-Simulation-Python-Uottawa/output/raw_single_queue.txt")
raw_multi_queue <- raw_multi_queue %>% rename(queue = 'Queued To', queue_amount = 'Queue Amount') %>%
  mutate(Replication=as.factor(Replication)) %>%
  select(-c(queue)) %>% group_by(Replication, Day) %>% summarize(queue = sum(queue_amount)) %>% ungroup()
raw_single_queue <- raw_single_queue %>% rename(queue = 'Queued To', queue_amount = 'Queue Amount')%>%
  mutate(Replication=as.factor(Replication)) %>%
  select(-c(queue)) %>% group_by(Replication, Day) %>% summarize(queue = sum(queue_amount)) %>% ungroup()

# Raw Stats
raw_multi_arrival %>% filter(Day >= 0) %>% 
  select(-c(Day)) %>% group_by(Replication) %>% summarise(mean=mean(arrival))
raw_single_arrival %>% filter(Day >= 0) %>% 
  select(-c(Day)) %>% group_by(Replication) %>% summarise(mean=mean(arrival))
raw_multi_queue %>% filter(Day >= 0) %>%
  select(-c(Day)) %>% group_by(Replication) %>% summarise(mean=mean(queue))
raw_single_queue %>% filter(Day >= 0) %>%
  select(-c(Day)) %>% group_by(Replication) %>% summarise(mean=mean(queue))

# Combines Data
raw_multi <- inner_join(raw_multi_arrival, raw_multi_queue, by=c('Replication', 'Day')) %>%
  select(-c(Replication)) %>% group_by(Day) %>%
  summarise(mean_arrival = mean(arrival), mean_queue = mean(queue)) %>% ungroup()
raw_signle <- inner_join(raw_single_arrival, raw_single_queue, by=c('Replication', 'Day')) %>%
  select(-c(Replication)) %>% group_by(Day) %>%
  summarise(mean_arrival = mean(arrival), mean_queue = mean(queue)) %>% ungroup()


ggplot(raw_multi, aes(x=Day)) +
  geom_line(aes(y=mean_arrival), color='grey40')+
  geom_line(aes(y=mean_queue/5), color='grey40')+
  geom_line(aes(y=rollmean(mean_arrival, 180, na.pad=TRUE)), color='dodgerblue4', size=1)+
  geom_line(aes(y=rollmean(mean_queue/5, 180, na.pad=TRUE)), color='brown4', size=1)+
  ggtitle("Multi Queue")
ggplot(raw_signle, aes(x=Day, y=arrival, color=Replication)) +
  geom_line(aes(y=mean_arrival), color='grey40')+
  geom_line(aes(y=mean_queue/5), color='grey40')+
  geom_line(aes(y=rollmean(mean_arrival, 180, na.pad=TRUE)), color='dodgerblue4', size=1)+
  geom_line(aes(y=rollmean(mean_queue/5, 180, na.pad=TRUE)), color='brown4', size=1)+
  ggtitle("Single Queue")