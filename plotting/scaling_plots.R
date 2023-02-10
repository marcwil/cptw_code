source("helper.R")
source("girg_stats.R")

library(latex2exp)
library(xtable)

read_scaling_data <- function(path) {
  df <- read_csv(path)


  df <- parse_girg_params(df)

  scalingdf <- df %>%
    transmute(
      time=time,
      error_status=error_status,
      n=GraphInput.n,
      n_gen=GraphInput.n_gen,
      graph = GraphInput.graph,
      m=GraphInput.m,
      alpha=alpha,
      dimension=dimension,
      girg_deg=girg_deg,
      ple=ple,
      seed=seed,
      graph_type=graph_type,
      treewitdh=Treewidth.treewidth,
      weighted_treewidth=PartitionBags.max_weight,
      partition_time=PartitionBags.time,
      partition_error_status=PartitionBags.error_status,
      partition_status=PartitionBags.status,
      partition_option=gsub("Partition\\((.+)\\)", "\\1", PartitionBags.partition_option),
      treewidth_time=PartitionBags.time,
      treewidth_error_status=PartitionBags.error_status,
      treewidth_status=PartitionBags.status,
      )
  df <- remove_empty_cols(df)
  scalingdf <- rename_partition_option(scalingdf)
  return(scalingdf)
}

scalingdf <- read_scaling_data("../output_data/girg_scaling.csv")


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
  labs(caption=TeX("ple 2.5, alpha=inf")) +
  theme(legend.position = "top",
        plot.caption = element_text(hjust = 0))
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
  labs(caption="ple 2.1, alpha=5") +
  theme(legend.position = "top",
        plot.caption = element_text(hjust = 0))

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
  labs(caption="ple 2.1, alpha=5") +
  scale_color_hue(drop=FALSE) +
  theme(legend.position = "none",
        plot.caption = element_text(hjust = 0))
snapshot3

#scaling_snapshots <- (snapshot1 + snapshot12 + snapshot2 + snapshot3 +
scaling_snapshots <- (snapshot1 + snapshot12 + snapshot3 +
  plot_layout(nrow=1, guides = "collect", ) &
  scale_color_discrete() &
  theme(legend.position='top'))
scaling_snapshots


#create_pdf("../output.pdf/scaling_snapshots.pdf", scaling_snapshots, width=1, height = 0.35)
create_pdf("../output.pdf/scaling_snapshots.pdf", scaling_snapshots, width=1, height = 0.35)




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



rwscalingdf <- read_scaling_data("../output_data/rw_ext_vs_heu.csv")

rwscalingdf %>%
  mutate(no_errors=error_status=="none" &
           treewidth_status=="success" &
           partition_status=="success") %>%
  group_by(partition_option) %>%
  summarise(
    num = n(),
    num_solved = sum(no_errors),
    )

rw_compare_relative <- rwscalingdf %>%
  mutate(no_errors=error_status=="none" &
           treewidth_status=="success" &
           partition_status=="success") %>%
  group_by(graph) %>%
  filter(sum(no_errors)==4) %>%  # only include instances where all solvers finished
  mutate(min_weight = min(weighted_treewidth),
         min_time = min(partition_time),
         weight_relative = weighted_treewidth / min_weight,
         time_relative = partition_time / min_time,
         exact_group = factor(case_when(
           partition_option == "B&B" ~ "exact",
           partition_option == "MC" ~ "MC",
           partition_option == "RMC" ~ "RMC",
           TRUE ~ "hittingset"), levels=c("exact", "MC", "RMC", "hittingset")
         )
         )


# how many networks were solved by all solvers?
rw_compare_relative %>% group_by(partition_option) %>%
  summarise(num = n())

boxplot_solver_quality_rw <- rw_compare_relative %>%
  ggplot(aes(x=partition_option, y=weight_relative, color = exact_group)) +
  geom_boxplot() +
#  labs(color="Partition Solver") +
#  scale_color_discrete(labels=c("1", "2","3","4","5","6")) +
  labs(
    x = "Partition Solver",
    y = "cptw (rel.)",
  ) +
  theme(
    legend.position = "none",
    axis.text = element_text(size = 6)
  )
boxplot_solver_quality_rw

solution_quality_df <- rw_compare_relative %>%
  filter(partition_option!="B&B") %>%
  group_by(partition_option) %>%
  summarise(
    Mean = round(mean(weight_relative), 3),
    Median = median(weight_relative),
    "90th percentile" = round(quantile(weight_relative, c(0.90)), 3),
    "99th percentile" = round(quantile(weight_relative, c(0.99)), 3),
    Maximum = round(max(weight_relative), 3),
  )
solution_quality_df


colnames(solution_quality_df)[1] <- "Partition Solver"
sol_quality_transposed <- as_tibble(cbind(nms = names(solution_quality_df), t(solution_quality_df)))

print(xtable(sol_quality_transposed, type = "latex"))


boxplot_solver_time_rw <- rw_compare_relative %>%
  ggplot(aes(x=partition_option, y=time_relative, color = exact_group)) +
  geom_boxplot() +
  xlab("Partition Solver") +
  ylab("Run time (rel.)") + scale_y_log10(labels = scales::scientific) +
  annotation_logticks(sides='l',
                      alpha = 0.8,
                      long=unit(0.1, unit='cm'),
                      mid=unit(0.07, unit='cm'),
                      short=unit(0.05, unit='cm')) +
  theme(
    legend.position = "none",
    axis.text = element_text(size = 6)
  )
boxplot_solver_time_rw
create_pdf("../output.pdf/boxplot_solver_time_rw.pdf", boxplot_solver_time_rw, width=0.37, height = 0.25)


rw_scaling_scatter_time <- rwscalingdf %>%
  mutate(
    no_timeout = error_status=="none" & treewidth_status=="success" & partition_status=="success",
    timeout_status = ifelse(!no_timeout, "Timeout", "No Timeout"),
    partition_time = ifelse(no_timeout, partition_time, 300)
  ) %>%
  filter(no_timeout) %>%
  ggplot(aes(
    x=n,
    y=partition_time,
    color=partition_option,
 #   shape=timeout_status
  )) +
  geom_point(alpha=0.5, size=0.5) +
  scale_x_log10(breaks = c(10, 1000, 100000)) +
  scale_y_log10() +
  facet_wrap(~partition_option, nrow=1, scales = "free") +
  annotation_logticks(sides='lb', alpha = 0.8,) +
  labs(
    color = "Partition Solver",
    x = "Graph Size",
    y = "Run time (s)"
  ) +
  theme(legend.position = "top", legend.margin = margin(t=0, b=0, unit='cm'), legend.box.spacing = unit(0.1, 'cm'), legend.key.size = unit(0.5, 'cm'))
rw_scaling_scatter_time

create_pdf("../output.pdf/rw_scaling_scatter_time.pdf", rw_scaling_scatter_time, height=0.33)

rw_scaling_scatter_qualy <- rwscalingdf %>%
  filter(
    error_status=="none",
    treewidth_status=="success",
    partition_status=="success"
  ) %>%
  mutate(partition_name = case_when(
           partition_option == "B&B" ~ "branching",
           partition_option == "MC" ~ "lc_heur",
           partition_option == "RMC" ~ "lcr_heur",
           partition_option == "HS" ~ "hs",
           TRUE ~ "nope")) %>%
  pivot_wider(
    id_cols = c(graph,n,m),
    names_from = partition_name,
    values_from = weighted_treewidth
  ) %>%
  filter(branching > 0, lc_heur > 0) %>%
  ggplot(aes(x=n, y=lc_heur / branching)) +
  geom_point() +
#  scale_x_log10() +
#  scale_y_log10() +
#  annotation_logticks(sides='l', alpha = 0.8,)+
  labs(
    color = "Partition Solver",
    x = "Graph size",
    y = "Weighted treewidth (rel. to opt.)"
  ) +
  theme(legend.position = "top", legend.margin = margin(t=0, b=0, unit='cm'), legend.box.spacing = unit(0.1, 'cm'), legend.key.size = unit(0.5, 'cm'))
rw_scaling_scatter_qualy

create_pdf("../output.pdf/rw_scaling_scatter_qualy.pdf", rw_scaling_scatter_qualy, width=1, height=0.6)


solution_quality_df <- rwscalingdf %>%
  filter(
    error_status=="none",
    treewidth_status=="success",
    partition_status=="success"
  ) %>%
  group_by(graph) %>%
  filter(n()==4) %>%  # all solvers solved
  transmute(flc_relative_wtw = weighted_treewidth / min(weighted_treewidth), partition_option=partition_option) %>%
  filter(partition_option != "B&B") %>%
  pivot_wider(id_cols = graph, names_from = partition_option, values_from = flc_relative_wtw)
print(quantile(solution_quality_df$MC, c(0, 0.99, 1), na.rm = TRUE))
print(quantile(solution_quality_df$RMC, c(0, 0.99, 1), na.rm = TRUE))
print(quantile(solution_quality_df$SC, c(0, 0.99, 1), na.rm = TRUE))
solution_quality_df %>%
  summary()
#+ >       0%      99%     100%
#1.000000 1.090507 1.253882
#>       0%      99%     100%
#1.000000 1.095319 1.192333
#>       0%      99%     100%
#1.000000 1.039090 1.113121
#> + >     graph                 MC              SC             RMC
# Length:2638        Min.   :1.000   Min.   :1.000   Min.   :1.000
# Class :character   1st Qu.:1.000   1st Qu.:1.000   1st Qu.:1.000
# Mode  :character   Median :1.000   Median :1.000   Median :1.000
#                    Mean   :1.009   Mean   :1.002   Mean   :1.008
#                    3rd Qu.:1.012   3rd Qu.:1.000   3rd Qu.:1.006
#                    Max.   :1.254   Max.   :1.113   Max.   :1.192
#                    NA's   :19      NA's   :434     NA's   :16

rwscalingdf %>%
  mutate(
    success = error_status=="none" & treewidth_status=="success" & partition_status=="success",
  ) %>%
  group_by(partition_option) %>%
  summarise(num = n(), success=sum(success))
## A tibble: 2 × 3
#  partition_option   num success
#  <chr>            <int>   <int>
#1 B&B               2090    1162
#2 LC                2090    2085


rw_scaling_cmpdf <- rwscalingdf %>%
  filter(
    error_status=="none",
    treewidth_status=="success",
    partition_status=="success"
  ) %>%
  group_by(graph) %>%
  mutate(
    lowest_weight = min(weighted_treewidth),
    lowest_time = min(partition_time),
    time_rel = partition_time / lowest_time,
    weight_rel = weighted_treewidth / lowest_weight,
  )

rw_cmp_time <- rw_scaling_cmpdf %>%
  ggplot(aes(x=partition_option, y = time_rel)) +
  geom_boxplot() +
  scale_y_log10()
rw_cmp_time

rw_cmp_weight <- rw_scaling_cmpdf %>%
  ggplot(aes(x=weight_rel)) +
  geom_density()
rw_cmp_weight


rw_scaling_density_qualy <- rwscalingdf %>%
  group_by(graph, partition_option) %>%
  mutate(opt=min(weighted_treewidth),
         failed=is.na(weighted_treewidth) | weighted_treewidth < 0) %>%
  filter(partition_option=="LC") %>%
  ggplot(aes(x=n, y=weighted_treewidth/opt), color=failed) +
  geom_point()
rw_scaling_density_qualy




rwstats <- get_rw_stats()

scalingandstats <- rwscalingdf %>%
  mutate(
    no_timeout =error_status=="none" &
      treewidth_status=="success" &
      partition_status=="success"
  ) %>%
  inner_join(rwstats, by = c("graph", "n", "m"))

scalingandstats %>%
  filter(partition_option=="B&B") %>%
  ggplot(aes(x=clustering, y = partition_time/m, color=partition_option)) +
  geom_point(alpha=0.2) +
  scale_y_log10()
