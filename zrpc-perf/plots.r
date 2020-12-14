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

# Reading GET bench results
get_files <- c();
for(ld in logdir) {
  get_files <- c(get_files, list.files(ld, pattern = "get-*", full.names=TRUE));
}

get_data <- get_files %>%
  map_df(~ read_dir(.))


call_files <- c();
for(ld in logdir) {
  call_files <- c(call_files, list.files(ld, pattern = "call-*", full.names=TRUE));
}

call_data <- call_files %>%
  map_df(~ read_dir(.))


grpc_files <- c();
for(ld in logdir) {
  grpc_files <- c(grpc_files, list.files(ld, pattern = "grpc-*", full.names=TRUE));
}

grpc_data <- grpc_files %>%
  map_df(~ read_dir(.))


nocheck_files <- c();
for(ld in logdir) {
  nocheck_files <- c(nocheck_files, list.files(ld, pattern = "nochk-call-*", full.names=TRUE));
}

nocheck_data <- nocheck_files %>%
  map_df(~ read_dir(.))


# state_files <- c();
# for(ld in logdir) {
#   state_files <- c(state_files, list.files(ld, pattern = "state*", full.names=TRUE));
# }
# 
# state_data <- state_files %>%
#   map_df(~ read_dir(.))
# 
# 
# zstate_files <- c();
# for(ld in logdir) {
#   zstate_files <- c(zstate_files, list.files(ld, pattern = "zstate*", full.names=TRUE));
# }
# 
# zstate_data <- zstate_files %>%
#   map_df(~ read_dir(.))

eval_files <- c();
for(ld in logdir) {
  eval_files <- c(eval_files, list.files(ld, pattern = "eval-*", full.names=TRUE));
}

eval_data <- eval_files %>%
  map_df(~ read_dir(.))


raw_data <- bind_rows(get_data, call_data, eval_data, grpc_data, nocheck_data) %>% mutate(MBIT_THR = THR/1024/1024)

sizes = c(8,16,32, 64, 128,256,512,1024,2048,4096,8192,16384,32768,65536)


## Getting statistics
data <- raw_data %>% group_by(SIZE,KIND) %>% summarise( MEAN_MSGS = mean(MSGS),
                                                        SD_MSGS=sd(MSGS),
                                                        MEAN_THR= mean(MBIT_THR),
                                                        SD_THR=sd(MBIT_THR),
                                                        MEAN_RTT= mean(RTT_US),
                                                        COUNT = n()
                                            ) %>% mutate (
                                              SE_MSGS= (SD_MSGS) / sqrt(COUNT),
                                              SE_THR = (SD_THR) / sqrt(COUNT),
                                              LCI_MSGS = lower_ci(MEAN_MSGS, SE_MSGS, COUNT),
                                              UCI_MSGS = upper_ci(MEAN_MSGS, SE_MSGS, COUNT),
                                              LCI_THR = lower_ci(MEAN_THR, SE_THR, COUNT),
                                              UCI_THR = upper_ci(MEAN_THR, SE_THR, COUNT),
                                            )


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
  scale_y_log10() +
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
  scale_y_log10() +
  scale_x_discrete(breaks = sizes, labels = sizes) +
  ggtitle("zrpc zenoh comparison rtt localhost") +
  xlab("Payload size") + ylab("RTT µS")
plot(p_rtt)

ggsave("msgs-comparison.pdf",plot = p_msgs, width = 10, height = 10, limitsize = TRUE);
ggsave("thr-comparison.pdf",plot = p_thr, width = 10, height = 10, limitsize = TRUE);
ggsave("rtt-comparison.pdf",plot = p_rtt, width = 10, height = 10, limitsize = TRUE);

print("Done")