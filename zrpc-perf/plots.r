library(ggplot2)
library(cowplot)
library(tidyverse)
library(cowplot)
library(hrbrthemes)
library(viridis)
library(readr)

setwd(".")

# The logs to read for 8K batches
read_dir <- function(file_name) {
  read_csv(file_name)
}

lower_ci <- function(mean, se, n, conf_level = 0.95){
  lower_ci <- mean - qt(1 - ((1 - conf_level) / 2), n - 1) * se
}

upper_ci <- function(mean, se, n, conf_level = 0.95){
  upper_ci <- mean + qt(1 - ((1 - conf_level) / 2), n - 1) * se
}

logdir <- c("./results");

data_files <- c();
 for(ld in logdir) {
   data_files <- c(data_files, list.files(ld, pattern = "*.csv", full.names=TRUE));
}
 
raw_data <- data_files %>%
   map_df(~ read_dir(.))

raw_data <- raw_data %>% filter(MSGS>0) %>% filter(RTT_US>0) %>% mutate(MBIT_THR = THR/1024/1024)

sizes = c(8,16,32, 64, 128,256,512,1024,2048,4096,8192,16384,32768,65536)


## Getting statistics
data <- raw_data %>% group_by(SIZE,KIND) %>% summarise( MEAN_MSGS = mean(MSGS),
                                                        SD_MSGS=sd(MSGS),
                                                        MEAN_THR= mean(MBIT_THR),
                                                        SD_THR=sd(MBIT_THR),
                                                        MEAN_RTT= mean(RTT_US),
                                                        MEDIAN_RTT=median(RTT_US),
                                                        COUNT = n()
                                            ) %>% mutate (
                                              SE_MSGS= (SD_MSGS) / sqrt(COUNT),
                                              SE_THR = (SD_THR) / sqrt(COUNT),
                                              LCI_MSGS = lower_ci(MEAN_MSGS, SE_MSGS, COUNT),
                                              UCI_MSGS = upper_ci(MEAN_MSGS, SE_MSGS, COUNT),
                                              LCI_THR = lower_ci(MEAN_THR, SE_THR, COUNT),
                                              UCI_THR = upper_ci(MEAN_THR, SE_THR, COUNT),
                                            )


data <- data %>% filter(KIND!="ZNRPC-RESP-SER" & KIND!="ZNRPC-RESP-DE")

# p_msgs <- ggplot(data=data, aes(x=factor(SIZE), y=MEAN_MSGS, fill=KIND)) +
#   geom_bar(stat="identity", position="dodge") + scale_y_log10()
# 
# plot(p_msgs)
# 
# p_rtt <- ggplot(data=data, aes(x=factor(SIZE), y=MEAN_RTT, fill=KIND)) +
#   geom_bar(stat="identity", position="dodge") + scale_y_log10()
# 
# plot(p_rtt)
# 
# ggsave("zrpc-msgs.pdf",plot = p_msgs, width = 10, height = 10, limitsize = TRUE);
# ggsave("zrpc-rtt.pdf",plot = p_rtt, width = 10, height = 10, limitsize = TRUE);


p_msgs<-ggplot(data=data, aes(x=factor(SIZE), y=MEAN_MSGS, colour=KIND, group=KIND)) +
  geom_point(size=2) +
  geom_line() +
  #scale_y_log10() +
  geom_errorbar(aes(ymin=MEAN_MSGS-SE_MSGS, ymax=MEAN_MSGS+SE_MSGS), colour="black", width=.2) +
  scale_x_discrete(breaks = sizes, labels = sizes) +
  ggtitle("zrpc zenoh comparison msg/s localhost") +
  xlab("Payload size") + ylab("msg/s")
plot(p_msgs)


p_thr<-ggplot(data=data, aes(x=factor(SIZE), y=MEAN_THR, colour=KIND, group=KIND)) +
  geom_point(size=2) +
  geom_line() +
  scale_y_log10() +
  geom_errorbar(aes(ymin=MEAN_THR-SE_THR, ymax=MEAN_THR+SE_THR), colour="black", width=.2) +
  scale_x_discrete(breaks = sizes, labels = sizes) +
  ggtitle("zrpc zenoh comparison throughput localhost") +
  xlab("Payload size") + ylab("Mbit/s")
plot(p_thr)


p_rtt<-ggplot(data=data, aes(x=factor(SIZE), y=MEAN_RTT, colour=KIND, group=KIND)) +
  geom_point(size=2) +
  geom_line() +
  #scale_y_log10() +
  scale_x_discrete(breaks = sizes, labels = sizes) +
  ggtitle("zrpc zenoh comparison rtt localhost") +
  xlab("Payload size") + ylab("RTT µS")
plot(p_rtt)

#p_rtt_median<-ggplot(data=data, aes(x=factor(SIZE), y=MEDIAN_RTT, colour=KIND, group=KIND))
#  geom_point(size=2) +
#  geom_line() +
#  scale_y_log10() +
#  scale_x_discrete(breaks = sizes, labels = sizes) +
#  ggtitle("zrpc zenoh comparison median rtt localhost") +
#  xlab("Payload size") + ylab("RTT µS")
#plot(p_rtt_median)


#dist_data <- raw_data %>% filter(SIZE==8)  %>% filter(KIND=="QUERY" | KIND=="QUERY-EVAL" | KIND=="P2P-QUERY-EVAL")  

# dist_data <- raw_data %>% filter(SIZE==8)
# 
# 
# p_rtt_dist<-ggplot(data=dist_data, aes(x=RTT_US, colour=KIND, group=KIND)) +
#   geom_density() +
#   #scale_y_log10() +
#   ggtitle("zenoh rtt density plot 8 byte") +
#   xlab("RTT µS") + ylab("Probability")
# plot(p_rtt_dist)
# 
# cmp_data <- data %>% filter(KIND=="PP-ZNRPC" |  KIND=="PP-QUERY-EVAL" | KIND=="GRPC-CLIENT" ) 
# p_msgs_cmp<-ggplot(data=cmp_data, aes(x=factor(SIZE), y=MEAN_MSGS, colour=KIND, group=KIND)) +
#   geom_point(size=2) +
#   geom_line() +
#   #  scale_y_log10() +
#   geom_errorbar(aes(ymin=MEAN_MSGS-SE_MSGS, ymax=MEAN_MSGS+SE_MSGS), colour="black", width=.2) +
#   scale_x_discrete(breaks = sizes, labels = sizes) +
#   ggtitle("zrpc zenoh comparison msg/s localhost") +
#   xlab("Payload size") + ylab("msg/s")
# plot(p_msgs_cmp)
# 
# 

ggsave("msgs-comparison.pdf",plot = p_msgs, width = 10, height = 10, limitsize = TRUE);
ggsave("thr-comparison.pdf",plot = p_thr, width = 10, height = 10, limitsize = TRUE);
ggsave("rtt-comparison.pdf",plot = p_rtt, width = 10, height = 10, limitsize = TRUE);
#ggsave("rtt-median-comparison.pdf",plot = p_rtt_median, width = 10, height = 10, limitsize = TRUE);

print("Done")