source("helper.R")
source("data_helper.R")

library(latex2exp)
library(xtable)

scalingdf <- read_data("../output_data/girg_scaling.csv")
scalingdflarge <- read_data("../output_data/girg_scaling_large.csv")


snapshot_plot <- function(data){
  return(data %>%
         filter(partition_status != 'timeout') %>%
         group_by(n_gen, dimension, alpha, ple, partition_option) %>%
         filter(n() > 5) %>%
         mutate(mean_time = mean(partition_time),
                mean_size = mean(n),
                partition_option = as.factor(partition_option)) %>%
         ggplot(aes(x=mean_size, y=mean_time, color=partition_option)) +
         geom_point(size=0.2) +
         geom_line() +
         labs(
           color = "Partition Solver",
           x = "Graph Size",
           y = "Run time (s)"
         ) +
         theme(
           legend.position = "top",
           legend.margin = margin(t=0, b=0, unit='cm'),
           legend.box.spacing = unit(0.1, 'cm'),
           legend.key.size = unit(0.5, 'cm'),
#           axis.text = element_text(size=6),
           )
         )
}

snapshot1 <- scalingdf %>%
  filter(ple==2.5, alpha=='inf') %>%
  snapshot_plot +
  scale_x_continuous(breaks = c(10000, 30000, 50000), minor_breaks = c(10000, 20000, 30000, 40000, 50000)) +
  labs(
    caption=TeX("ple 2.5,  $\\alpha$ = $\\infty$")
  ) +
  theme(legend.position = "top",
        plot.caption = element_text(hjust = 0, family = 'LM Math'))
snapshot1

snapshot12 <- snapshot1 +
  scale_x_log10() + scale_y_log10() +
  annotation_logticks(sides='lb',
                      alpha = 0.8,
                      long=unit(0.1, unit='cm'),
                      mid=unit(0.07, unit='cm'),
                      short=unit(0.05, unit='cm'))
snapshot12


snapshot2 <- scalingdf %>%
  filter(ple==2.1, alpha==5) %>%
  snapshot_plot +
  labs(caption=TeX("ple 2.1,  $\\alpha$ = 5")) +
  theme(legend.position = "top",
        plot.caption = element_text(hjust = 0, family = 'LM Math'))

snapshot3 <- scalingdf %>%
  filter(ple==2.1, alpha==5) %>%
#  filter(partition_option %in% c("B&B", "SC")) %>%
  snapshot_plot +
  scale_x_log10() + scale_y_log10() +
  annotation_logticks(sides='lb',
                      alpha = 0.8,
                      long=unit(0.1, unit='cm'),
                      mid=unit(0.07, unit='cm'),
                      short=unit(0.05, unit='cm')) +
  labs(caption=TeX("ple 2.1,  $\\alpha$ = 5")) +
  scale_color_hue(drop=FALSE) +
  theme(legend.position = "none",
        plot.caption = element_text(hjust = 0, family = 'LM Math'))
snapshot3

#scaling_snapshots <- (snapshot1 + snapshot12 + snapshot2 + snapshot3 +
scaling_snapshots <- (snapshot1 + snapshot12 + snapshot3 +
  plot_layout(nrow=1, guides = "collect", ) &
  scale_color_discrete() &
  theme(legend.position='top'))
scaling_snapshots


#create_pdf("../output.pdf/scaling_snapshots.pdf", scaling_snapshots, width=1, height = 0.35)
create_pdf("../output.pdf/scaling_snapshots.pdf", scaling_snapshots, width=1, height = 0.35)


# same plot for whole α~ple grid
scaling_cmp_alpha_ple <- scalingdf %>%
  filter(partition_status != 'timeout') %>%
  group_by(n_gen, dimension, alpha, ple, partition_option) %>%
#  filter(max(partition_time) < 160) %>%
  filter(n() > 5) %>%
  mutate(mean_time = mean(partition_time),
         mean_size = mean(n)) %>%
  ggplot(aes(x=mean_size, y=mean_time, color=partition_option,shape=partition_option)) +
  geom_point() +
  facet_grid(alpha~ple, scales="free") +
  scale_x_log10() + scale_y_log10() +
  annotation_logticks(sides='lb',
                      alpha = 0.8,
                      long=unit(0.1, unit='cm'),
                      mid=unit(0.07, unit='cm'),
                      short=unit(0.05, unit='cm')) +
  labs(
    color = "Partition Solver",
    shape = "Partition Solver",
    x = "Graph size",
    y = "Run time (s)"
  ) +
  theme(
      legend.position = "top",
      legend.margin = margin(t=0, b=0, unit='cm'),
      legend.box.spacing = unit(0.1, 'cm'),
      legend.key.size = unit(0.5, 'cm'),
  )
scaling_cmp_alpha_ple

create_pdf("../output.pdf/scaling_cmp_alpha_ple.pdf", scaling_cmp_alpha_ple, width=1, height=0.6)


# how does pf-treewidth scale?
scalingdflarge %>%
  group_by(n_gen, dimension, alpha, ple, seed, partition_option) %>%
  mutate(no_errors=error_status=="none" &
           treewidth_status=="success" &
           partition_status=="success") %>%
  filter(sum(no_errors) >= n()/2) %>%
  group_by(n_gen, dimension, alpha, ple, seed) %>%
  summarise(
    min_pftw = min(weighted_treewidth),
    mean_n = mean(n)
  ) %>%
  group_by(n_gen, dimension, alpha, ple) %>%
  summarise(
    mean_pftw = mean(min_pftw),
    mean_n = mean_n
  ) %>%
  ggplot(aes(x = mean_n, y = mean_pftw, color = dimension)) +
  geom_point() +
  facet_grid(alpha ~ ple, scales = "free") +
  scale_x_log10(labels = scales::scientific) +
  scale_y_log10(labels = scales::scientific) +
  annotation_logticks(sides='lb',
                      alpha = 0.8,
                      long=unit(0.1, unit='cm'),
                      mid=unit(0.07, unit='cm'),
                      short=unit(0.05, unit='cm')) +
  labs(
    x = "Graph size (n)",
    y = "pf-treewidth",
    title = "Scaling of pftw on GIRGs with dim=1"
  )


