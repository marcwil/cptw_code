source("helper.R")
source("girg_stats.R")

df <- read_csv("../output_data/branching_variants_girg.csv")

df <- remove_empty_cols(df)

df <- parse_girg_params(df)

# colnames: "GraphInput.error_status", "alpha", "dimension",
# "girg_deg", "ple", "seed", "graph_type", "GraphInput.m",
# "GraphInput.n", "GraphInput.n_gen", "GraphInput.option",
# "GraphInput.time", "PartitionBags.error_status",
# "PartitionBags.max_partition_num", "PartitionBags.max_weight",
# "PartitionBags.mean_partition_num", "PartitionBags.median_partition_num"
#, "PartitionBags.num_branching_max", "PartitionBags.num_branching_mean"
#, "PartitionBags.num_branching_median",
# "PartitionBags.num_branching_sum", "PartitionBags.num_clq_red",
# "PartitionBags.num_lb2_reductions_max",
# "PartitionBags.num_lb2_reductions_mean",
# "PartitionBags.num_lb2_reductions_median",
# "PartitionBags.num_lb2_reductions_sum",
# "PartitionBags.num_lb_reductions_max",
# "PartitionBags.num_lb_reductions_mean",
# "PartitionBags.num_lb_reductions_median",
# "PartitionBags.num_lb_reductions_sum", "PartitionBags.num_leaves_max",
# "PartitionBags.num_leaves_mean", "PartitionBags.num_leaves_median",
# "PartitionBags.num_leaves_sum", "PartitionBags.num_sw_reductions_max",
# "PartitionBags.num_sw_reductions_mean",
# "PartitionBags.num_sw_reductions_median",
# "PartitionBags.num_sw_reductions_sum", "PartitionBags.partition_option"
#, "PartitionBags.status", "PartitionBags.time",
# "Treewidth.error_status", "Treewidth.num_bags", "Treewidth.option"
#, "Treewidth.time", "Treewidth.treewidth", "error_status",
# "option", "time"

branching_variants <- df %>%
  transmute(
    time=time,
    error_status=error_status,
    n=GraphInput.n,
    n_gen=GraphInput.n_gen,
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
    max_partition_num=PartitionBags.max_partition_num,
    num_branching_sum=PartitionBags.num_branching_sum,
    num_clq_red=PartitionBags.num_clq_red,
    num_lb2_reductions_sum=PartitionBags.num_lb2_reductions_sum,
    num_lb2_reductions_max=PartitionBags.num_lb2_reductions_max,
    num_lb_reductions_sum=PartitionBags.num_lb_reductions_sum,
    num_lb_reductions_max=PartitionBags.num_lb_reductions_max,
    num_sw_reductions_sum=PartitionBags.num_sw_reductions_sum,
    num_sw_reductions_max=PartitionBags.num_sw_reductions_max,
  )
branching_variants <- rename_partition_option(branching_variants)

branching_variants <- branching_variants %>%
  group_by(n_gen, dimension, alpha, ple, seed) %>%
  mutate(
    sw_red = case_when(
      num_sw_reductions_sum > 0 ~ "SW",
      TRUE ~ "noSW"),
    lb_red = num_lb_reductions_sum > 0,
    lb2_red = num_lb2_reductions_sum > 0,
    lower_bounds = as.factor(case_when(
      lb_red==FALSE & lb2_red==FALSE ~ "none",
      lb_red==TRUE & lb2_red==FALSE ~ "S",
      lb_red==FALSE & lb2_red==TRUE ~ "S+V",
      lb_red==TRUE & lb2_red==TRUE ~ "S+V",
    )),
    reductions = interaction(sw_red, lower_bounds)
  )


compare_partition_solvers_scatter <- branching_variants %>%
  filter(n_gen == 5000) %>%
#  filter(partition_option!="HSGRB") %>%
  mutate(no_errors=error_status=="none" &
           treewidth_status=="success" &
           partition_status=="success") %>%
  filter(graph_type=="girg" & no_errors==TRUE) %>%
                                        #  filter(partition_option != "Partition(MinHSPartition)" &
                                        #         partition_option != "Partition(WeightedHSPartition)") %>%
  group_by(n_gen, dimension, alpha, ple, seed) %>%
  mutate(min_weight = min(weighted_treewidth),
         min_time = min(partition_time),
         weight_relative = weighted_treewidth / min_weight,
         time_relative = partition_time / min_time) %>%
  ggplot(aes(y=time_relative, color=lower_bounds, shape=as.factor(n_gen))) +
  geom_boxplot() +
  labs(color="Partition solver",
       shape="n",
       x="Run time (seconds, rel.)",
       y="Weighted treewidth (rel.)",
       ) +
  scale_y_log10() +
  #scale_x_log10(labels=c("1","10","100","1K","10K"), breaks=c(1,10,100,1000,10000),) +
  theme(
    legend.position = "top",
    legend.margin = margin(t=0, b=0, unit='cm'),
    legend.box.spacing = unit(0.1, 'cm'),
  ) +
  facet_grid(alpha ~ ple, scales = "free")
compare_partition_solvers_scatter

compare_redrules_data <- branching_variants %>%
  filter(alpha != 1.375,
         alpha != 1.75) %>%
  mutate(no_errors=error_status=="none" &
           treewidth_status=="success" &
           partition_status=="success",
         suf_weight_red = factor(ifelse(sw_red=='SW', "with", "without"), levels = c("without", "with"))
         ) %>%
  filter(graph_type=="girg" & no_errors==TRUE)
redrules_box_plotting <- function(x) {
  return(
    ggplot(x, aes(x=lower_bounds, y=partition_time, color=suf_weight_red)) +
    geom_boxplot() +
#    scale_color_discrete(labels = c("with", "without")) + #(direction = -1, breaks = c("with", "without")) +
    labs(color="Sufficient weight reduction",
         x="Lower Bounds",
         y="Run time (s)",
         ) +
    scale_y_log10() +
    annotation_logticks(sides='l',
                        alpha = 0.8,
                        long=unit(0.1, unit='cm'),
                        mid=unit(0.07, unit='cm'),
                        short=unit(0.05, unit='cm')) +
    theme(
      legend.position = "top",
      legend.margin = margin(t=0, b=0, unit='cm'),
      legend.box.spacing = unit(0.1, 'cm'),
      legend.key.size = unit(0.5, 'cm'),
      legend.text = element_text(size = 6)
      )
  )
}

compare_redrules_select <- compare_redrules_data %>%
  filter(n_gen == 5000) %>%
  filter(ple %in% c("2.1", "2.9")) %>%
  redrules_box_plotting +
    facet_wrap(~alpha * ple, nrow=1, scales = "free")
compare_redrules_select

compare_redrules_box_500 <- compare_redrules_data %>%
  filter(n_gen == 500) %>%
  redrules_box_plotting +
    facet_grid(alpha ~ ple, scales = "free")
compare_redrules_box_500

compare_redrules_box_5000 <- compare_redrules_data %>%
  filter(n_gen == 5000) %>%
  redrules_box_plotting +
    facet_grid(alpha ~ ple, scales = "free")
compare_redrules_box_5000

compare_redrules_box_50000 <- compare_redrules_data %>%
  filter(n_gen == 50000) %>%
  redrules_box_plotting +
    facet_grid(alpha ~ ple, scales = "free")
compare_redrules_box_50000

create_pdf("../output.pdf/compare_redrules_box_500.pdf", compare_redrules_box_500, width=1, height=0.7)
create_pdf("../output.pdf/compare_redrules_box_5000.pdf", compare_redrules_box_5000, width=1, height=0.5)
create_pdf("../output.pdf/compare_redrules_box_50000.pdf", compare_redrules_box_50000, width=1, height=0.5)

# time limit exceeded?
# -> all tle for alpha < 5; one tle at PLE=2.1 for alpha >= 5
branching_variants %>%
  filter(n_gen==5000) %>%
  mutate(no_errors=error_status=="none" &
           treewidth_status=="success" &
           partition_status=="success") %>%
  filter(graph_type=="girg") %>%
  group_by(n_gen, dimension, alpha, ple, lower_bounds) %>%
  summarise(num_total=n(), num_failed=sum(!no_errors)) %>%
  ggplot(aes(x=lower_bounds,y=num_failed/num_total,color=lower_bounds)) +
  geom_point() +
  facet_grid(alpha ~ ple)


stats_df <- get_girg_stats()

plot_num_clique <- compare_redrules_data %>%
  inner_join(stats_df, by = c("dimension", "n_gen", "ple", "alpha", "seed")) %>%
#  group_by(alpha, ple) %>%
  ggplot(aes(x = ple, y = num_clique)) +
  geom_boxplot() +
  facet_wrap( ~ alpha, nrow=2)
plot_num_clique

plot_clustering <- compare_redrules_data %>%
  inner_join(stats_df, by = c("dimension", "n_gen", "ple", "alpha", "seed")) %>%
#  group_by(alpha, ple) %>%
  ggplot(aes(x = ple, y = clustering)) +
  geom_boxplot() +
  facet_wrap(~alpha)
plot_clustering

plot_partition_size <- compare_redrules_data %>%
  inner_join(stats_df, by = c("dimension", "n_gen", "ple", "alpha", "seed")) %>%
#  group_by(alpha, ple) %>%
  ggplot(aes(x = ple, y = max_partition_num)) +
  geom_boxplot() +
  facet_wrap(~ alpha)
plot_partition_size

boxplot_all_stats <- compare_redrules_data %>%
  inner_join(stats_df, by = c("dimension", "n_gen", "ple", "alpha", "seed")) %>%
  pivot_longer(
    cols = c(num_clique, clustering, max_partition_num),
    names_to = "param_name",
    values_to = "param_value",
  ) %>%
  ggplot(aes(x = ple, y = param_value)) +
  geom_boxplot() +
  facet_wrap(~ interaction(param_name, alpha), scales = "free")
boxplot_all_stats

# plot showing reductions per branching vs time
compare_redrules_data %>%
  group_by(ple, alpha, reductions) %>%
  pivot_longer(cols = c(
#                 num_branching_sum,
                 num_lb2_reductions_sum / num_branching_sum,
                 num_lb_reductions_sum / num_branching_sum,
                 num_sw_reductions_sum / num_branching_sum),
               names_to = "stat_name",
               values_to = "stat_value"
               ) %>%
ggplot(aes(x=partition_time, y=stat_value, color=stat_name)) +
  geom_point() +
  scale_x_log10() + scale_y_log10() +
  facet_grid(alpha ~ ple, scales = "free")

# num partitions, weighted_treewidth?

# clique numbers
#

# all reductions vs no reductions
# ~
# num_cliques, ple, alpha, clique number
