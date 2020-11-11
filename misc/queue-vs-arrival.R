library("zoo")
library("tidyverse")
library("here")
library("sys")
library("gridExtra")

path <- rstudioapi::getActiveDocumentContext()$path %>% dirname() %>% dirname()
# Import Data
raw_multi_arrival <- read_csv(paste(path,"/output/raw_multi_arrival.txt",sep=""))
raw_single_arrival <- read_csv(paste(path,"/output/raw_signle_arrival.txt",sep=""))
raw_multi_arrival <- raw_multi_arrival %>% rename(arrival = 'Arrival Amount') %>%
  mutate(Replication=as.factor(Replication))
raw_single_arrival <- raw_single_arrival %>% rename(arrival = 'Arrival Amount') %>%
  mutate(Replication=as.factor(Replication))

# Preprocessing
raw_multi_queue <- read_csv(paste(path,"/output/raw_multi_queue.txt",sep=""))
raw_single_queue <- read_csv(paste(path,"/output/raw_single_queue.txt",sep=""))
raw_multi_queue <- raw_multi_queue %>% rename(queue = 'Queued To', queue_amount = 'Queue Amount') %>%
  mutate(Replication=as.factor(Replication)) %>%
  select(-c(queue)) %>% group_by(Replication, Day) %>% summarize(queue = sum(queue_amount)) %>% ungroup()
raw_single_queue <- raw_single_queue %>% rename(queue = 'Queued To', queue_amount = 'Queue Amount')%>%
  mutate(Replication=as.factor(Replication)) %>%
  select(-c(queue)) %>% group_by(Replication, Day) %>% summarize(queue = sum(queue_amount)) %>% ungroup()

# Raw Stats
raw_multi_arrival %>% filter(Day >= 2000) %>% 
  select(-c(Day)) %>% group_by(Replication) %>% summarise(mean=mean(arrival)) %>%
  ungroup() %>% summarise(mean_final = mean(mean), sd_final=sd(mean))
raw_single_arrival %>% filter(Day >= 2000) %>% 
  select(-c(Day)) %>% group_by(Replication) %>% summarise(mean=mean(arrival)) %>%
  ungroup() %>% summarise(mean_final = mean(mean), sd_final=sd(mean))
raw_multi_queue %>% filter(Day >= 2000) %>%
  select(-c(Day)) %>% group_by(Replication) %>% summarise(mean=mean(queue)) %>%
  ungroup() %>% summarise(mean_final = mean(mean), sd_final=sd(mean))
raw_single_queue %>% filter(Day >= 2000) %>%
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
ggplot(raw_data, aes(x=Day)) +
  geom_line(aes(y=mean_arrival), color='grey60')+
  geom_line(aes(y=mean_queue/5), color='grey60')+
  geom_line(aes(y=rollmean(mean_arrival, 180, na.pad=TRUE), color="Arrival"), size=1)+
  geom_line(aes(y=rollmean(mean_queue/5, 180, na.pad=TRUE), color="Queue/5"), size=1)+
  geom_segment(aes(x = 2000, y = 22.7, yend = 22.7, xend=4320, color="Mean"), linetype="longdash", size=0.9) +
  geom_vline(xintercept= 2000, colour = "grey30", linetype="dashed") +
  facet_grid(. ~ type) +
  ggtitle("Variable Arrival Rate VS Queue Size") + labs(x = "Simulation Day",y = "People",color = "Legend") + 
  scale_color_manual(values = colors)
