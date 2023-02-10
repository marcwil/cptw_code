source("helper.R")
source("girg_stats.R")

df_girg_branch <- read_csv("../output_data/girg_branch.csv")
df_girg_flc <- read_csv("../output_data/girg_flc.csv")
df_girg_hs <- read_csv("../output_data/girg_hs.csv")
df_girg_lcrep <- read_csv("../output_data/girg_lcrep.csv")
df_girg_whs <- read_csv("../output_data/girg_whs.csv")

df <- rbind(
  df_girg_flc,
  df_girg_lcrep,
  df_girg_hs,
  df_girg_branch,
  df_girg_whs
)

# remove columns that are all NA
df <- remove_empty_cols(df)

df <- parse_girg_params(df)

df_renamed <- df %>%
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
    max_partition_num=PartitionBags.max_partition_num,
    treewidth_time=PartitionBags.time,
    treewidth_error_status=PartitionBags.error_status,
    treewidth_status=PartitionBags.status,
  )
df_renamed <- rename_partition_option(df_renamed)

df_compare_relative <- df_renamed %>%
  filter(graph_type=="girg") %>%
  filter(partition_option != "WSC") %>%
  mutate(no_errors=error_status=="none" &
           treewidth_status=="success" &
           partition_status=="success") %>%
  group_by(n_gen, dimension, alpha, ple, seed) %>%
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

boxplot_solver_quality <- df_compare_relative %>%
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
    axis.text = element_text(size = 6))
  )
boxplot_solver_quality

compare_time_plot <- function(x) {
  return(
    ggplot(x, aes(x=partition_option,
                  y=time_relative,
                  color = exact_group)) +
#    geom_violin() +
    geom_boxplot() +
    xlab("Partition Solver") +
    ylab("Run time (rel.)")
    + scale_y_log10(labels = scales::scientific) +
    annotation_logticks(sides='l',
                        alpha = 0.8,
                        long=unit(0.1, unit='cm'),
                        mid=unit(0.07, unit='cm'),
                        short=unit(0.05, unit='cm')) +
    theme(legend.position = "none",
          axis.text = element_text(size = 6))
  )
}

boxplot_solver_time <- df_compare_relative %>%
  mutate(partition_option = recode(
           partition_option, name1="A", name2="B", name3="C", name4="D", name5="E", name6="F"
         )
         ) %>%
  compare_time_plot
boxplot_solver_time

boxplot_solver_time_large <- df_compare_relative %>%
  filter(n > 500) %>%
  compare_time_plot
boxplot_solver_time_large

create_pdf("../output.pdf/boxplot_solver_quality.pdf", boxplot_solver_quality, width=0.49, height = 0.37)
create_pdf("../output.pdf/boxplot_solver_time.pdf", boxplot_solver_time, width=0.49, height = 0.37)
create_pdf("../output.pdf/boxplot_solver_time_large.pdf", boxplot_solver_time_large)
create_pdf("../output.pdf/boxplot_solver_quality_small.pdf", boxplot_solver_quality, width=0.30, height = 0.25)
create_pdf("../output.pdf/boxplot_solver_time_small.pdf", boxplot_solver_time, width=0.30, height = 0.25)

                                        # compare partition options
#df_renamed %>%
#  filter(n_gen==50000) %>%
#  mutate(no_errors=error_status=="none" &
#           treewidth_status=="success" &
#           partition_status=="success") %>%
#  filter(graph_type=="girg") %>%
#  filter(no_errors==TRUE) %>%
#  group_by(n_gen, dimension, alpha, ple, partition_option) %>%
#  summarise(mean_weight = mean(weighted_treewidth),
#            mean_time = mean(partition_time),
#            n) %>%
#  ggplot(aes(x=mean_time, y=mean_weight, color=partition_option)) +
#  geom_point(size=2) +
#  facet_grid(alpha ~ ple, scales = "free")

# compare partition options relative (individual)
compare_partition_solvers_scatter <- df_renamed %>%
  filter(alpha != 1.375,
         alpha != 1.75) %>%
#  filter(n_gen<5000) %>%
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
  ggplot(aes(x=time_relative, y=weight_relative, color=partition_option, shape=as.factor(n_gen))) +
  geom_point() +
  labs(color="Solver",
       shape="n",
       x="Run time (rel.)",
       y="Weighted treewidth (rel.)",
       ) +
  scale_x_log10(labels=c("1","10","100","1K","10K"), breaks=c(1,10,100,1000,10000),) +
  theme(
    legend.position = "top",
    legend.margin = margin(t=0, b=0, unit='cm'),
    legend.box.spacing = unit(0.1, 'cm'),
  ) +
  facet_grid(alpha ~ ple)
compare_partition_solvers_scatter

create_pdf("../output.pdf/compare_partition_solvers_scatter.pdf", compare_partition_solvers_scatter, 1, 0.8)

# compare partition options relative (means)
df_renamed %>%
  filter(n_gen==5000) %>%
#  filter(partition_option!="MinHSPartition(HittingSet(GurobiHS))") %>%
#  filter(partition_option!="MinHSPartition(HittingSet(HSBranchReduce))") %>%
  mutate(no_errors=error_status=="none" &
           treewidth_status=="success" &
           partition_status=="success") %>%
  filter(graph_type=="girg" & no_errors==TRUE) %>%
                                        #  filter(partition_option != "Partition(MinHSPartition)" &
                                        #         partition_option != "Partition(WeightedHSPartition)") %>%
  group_by(n_gen, dimension, alpha, ple, partition_option) %>%
  summarise(mean_weight = mean(weighted_treewidth),
            mean_time = mean(partition_time)) %>%
  mutate(min_weight = min(mean_weight),
         min_time = min(mean_time),
         weight_relative = mean_weight / min_weight,
         time_relative = mean_time / min_time) %>%
  ggplot(aes(x=time_relative, y=weight_relative, color=partition_option)) +
  geom_point(size=5) +
  facet_grid(alpha ~ ple)

# time limit exceeded?
df_renamed %>%
  filter(n_gen==500) %>%
  mutate(no_errors=error_status=="none" &
           treewidth_status=="success" &
           partition_status=="success") %>%
  filter(graph_type=="girg") %>%
  group_by(n_gen, dimension, alpha, ple, partition_option) %>%
  summarise(num_total=n(), num_failed=sum(!no_errors)) %>%
  ggplot(aes(x=partition_option,y=num_failed/num_total,color=partition_option)) +
  geom_point() +
  facet_grid(alpha ~ ple)

## compare num solved
plot_num_solved <- df_renamed %>%
  filter(alpha != 1.375,
         alpha != 1.75) %>%
  mutate(no_errors=error_status=="none" &
           treewidth_status=="success" &
           partition_status=="success") %>%
  group_by(partition_option, n_gen) %>%
  summarise(
    num_total = n(),
    num_finished = sum(no_errors)) %>%
  ggplot(aes(x=partition_option, y = num_finished, fill=as.factor(n_gen))) +
  geom_bar(stat="identity") +
  scale_fill_brewer() +
  labs(
    x = "Partition solver",
    y = "# Solved instances",
    fill = "n"
  ) +
  theme(
    legend.position = "none",
    legend.margin = margin(t=0, b=0, unit='cm'),
    legend.box.spacing = unit(0.1, 'cm'),
    axis.text.x = element_text(size = 6),
  )
plot_num_solved
create_pdf("../output.pdf/barplot_num_solved.pdf", plot_num_solved, width=0.30, height = 0.25)

df_renamed %>%
  filter(alpha != 1.375,
         alpha != 1.75) %>%
  mutate(no_errors=error_status=="none" &
           treewidth_status=="success" &
           partition_status=="success") %>%
  group_by(partition_option) %>%
  summarise(
    num_total = n(),
    num_finished = sum(no_errors))

stats_renamed <- get_girg_stats()

# overview of all stats
stats_summary <- stats_renamed %>%
  filter(n_gen==5000) %>%
  group_by(n_gen, m, dimension, alpha, ple) %>%
  summarise(
    deg_cov = mean(deg_cov),
    largest_clique = mean(largest_clique),
    num_clique = mean(num_clique),
    sum_clique_sizes = mean(sum_clique_sizes),
    clustering=mean(clustering)
  )
stats_summary %>%
  pivot_longer(
    cols = c(deg_cov, clustering, largest_clique, num_clique, sum_clique_sizes),
    names_to="stat",
    values_to="stat_value") %>%
  ggplot(aes(x=alpha,y=stat_value,fill=alpha)) +
  facet_wrap(~ ple*stat, ncol=5, scales = "free") +
  geom_col()

# join with treewidth
weight_summary <- df_renamed %>%
  filter(n_gen==5000) %>%
  filter(graph_type=="girg") %>%
  filter(weighted_treewidth!=-1) %>%
  group_by(n_gen, dimension, alpha, ple, seed) %>%
  summarise(weighted_tw = min(weighted_treewidth),
            max_part_num = min(max_partition_num)) %>%
  summarise(weighted_tw = mean(weighted_tw),
            max_part_num = mean(max_part_num))

weight_and_stats <- stats_summary %>%
  inner_join(weight_summary) %>%
  filter(alpha != 1.375,
         alpha != 1.75)

# alpha*ple ~ wtw
plot_params_wtw <- weight_and_stats %>%
  group_by(ple, alpha) %>%
  summarise(mean_wtw = mean(weighted_tw),
            mean_max_clique_num = mean(num_clique)) %>%
  ungroup() %>%
  ggplot(aes(x=ple, y=mean_wtw, color=alpha, shape=alpha, group=alpha)) +
  geom_point(size=2) +
  geom_line() +
  scale_y_log10() +
  annotation_logticks(sides='l',
                      alpha = 0.8,
                      long=unit(0.1, unit='cm'),
                      mid=unit(0.07, unit='cm'),
                      short=unit(0.05, unit='cm')) +
  labs(
    x=NULL,
    y="cp-treewidth",
    size="alpha",
    shape="alpha",
  )
plot_params_wtw
create_pdf("../output.pdf/plot_alpha_wtw.pdf", plot_params_wtw, 0.48)

plot_params_sol_size <- weight_and_stats %>%
  group_by(ple, alpha) %>%
  summarise(
    max_part_num = mean(max_part_num)
  ) %>%
  ggplot(aes(x=ple, y=max_part_num, color=alpha, shape=alpha, group=alpha)) +
  geom_point(size=2) +
  geom_line() +
  scale_y_log10() +
  annotation_logticks(sides='l',
                      alpha = 0.8,
                      long=unit(0.1, unit='cm'),
                      mid=unit(0.07, unit='cm'),
                      short=unit(0.05, unit='cm')) +
  labs(
    x=NULL,
    y="Clique count (sol.)",
    size="alpha",
    shape="alpha",
  )
plot_params_sol_size
create_pdf("../output.pdf/plot_alpha_sol_size.pdf", plot_params_wtw, 0.48)

# what is the relationship of alpha*ple ~ num_clique
plot_params_num_clique <- weight_and_stats %>%
  filter(n_gen==5000) %>%
  group_by(ple, alpha) %>%
  summarise(mean_wtw = mean(weighted_tw),
            mean_max_clique_num = mean(num_clique)) %>%
  ggplot(aes(x=ple, y=mean_max_clique_num, color=alpha, shape=alpha, group=alpha)) +
  geom_point(size=2) +
  geom_line() +
  labs(
    x=NULL,
    y="Clique count",
    size="alpha",
    shape="alpha",
  )
plot_params_num_clique
create_pdf("../output.pdf/plot_alpha_ple_num_clique.pdf", plot_params_num_clique, 0.48)

# what is the relationship of alpha*ple ~ instance_size
stats2_df <- get_graph_stats2("../output_data/girg_stats2.csv")
plot_params_instance_size <- stats2_df %>%
  filter(n_gen==5000) %>%
  filter(alpha != 1.375,
         alpha != 1.75) %>%
  group_by(ple, alpha) %>%
  summarise(mean_instance_size = mean(largest_bag_cc)) %>%
  ggplot(aes(x=ple, y=mean_instance_size, color=alpha, shape=alpha, group=alpha)) +
  geom_point(size=2) +
  geom_line() +
  scale_y_log10() +
  annotation_logticks(sides='l',
                      alpha = 0.8,
                      long=unit(0.1, unit='cm'),
                      mid=unit(0.07, unit='cm'),
                      short=unit(0.05, unit='cm')) +
  labs(
    x=NULL,
    y="Clique count (bag)",
    size="alpha",
    shape="alpha",
  )
plot_params_instance_size
create_pdf("../output.pdf/plot_alpha_ple_inst_size.pdf", plot_params_instance_size, 0.48)


blanklabelplot<-ggplot()+
  labs(x="Power-law exponent")+
  theme_classic()+
  theme(axis.title.x = element_text(family = "LM Roman", size=9))+
  guides(x = "none", y = "none")
plot_params_stast3 <- ((plot_params_wtw |
  plot_params_num_clique |
  plot_params_instance_size) / blanklabelplot) +
  plot_layout(guides = "collect", heights = c(1000,1)) &
  scale_color_discrete() &
  theme(
    legend.position = "top",
    legend.margin = margin(t=0, b=0, unit='cm'),
    legend.box.spacing = unit(0.1, 'cm'),
  )
plot_params_stast3

create_pdf("../output.pdf/plot_params_stats3.pdf", plot_params_stast3, width=1)

plot_params_stats4 <- ((plot_params_num_clique |
  plot_params_instance_size |
  plot_params_sol_size |
  plot_params_wtw) / blanklabelplot ) +
  plot_layout(guides = "collect", heights = c(1000,1)) &
  scale_color_discrete() &
  theme(
    legend.position = "top",
    legend.margin = margin(t=0, b=0, unit='cm'),
    legend.box.spacing = unit(0.1, 'cm'),
  )
plot_params_stats4
create_pdf("../output.pdf/plot_params_stats4.pdf", plot_params_stats4, width=1, height = 0.37)

# clustering*deg_cov ~ wtw
weight_and_stats %>%
  ggplot(aes(x=deg_cov, y=clustering, size=weighted_tw)) +
  xlab("Degree coefficient of variation") +
  ylab("Clustering coefficient (global)") +
  geom_point()

# stat ~ wtw
weight_and_stats %>%
  pivot_longer(
    cols = c(deg_cov, clustering, largest_clique, num_clique, sum_clique_sizes),
    names_to="stat",
    values_to="stat_value") %>%
  ggplot(aes(x=stat_value, y=weighted_tw, color=stat)) +
  geom_point() +
  facet_wrap(~stat, scales = "free")


# RW exact vs heuristic

df_rw_cmp <- read_csv("../output_data/rw_small_ext_vs_heu.csv")
df_rw_cmp <- df_rw_cmp[ , colSums(is.na(df_rw_cmp)) < nrow(df_rw_cmp)]

rw_cmp_renamed <- df_rw_cmp %>%
  transmute(
    time=time,
    error_status=error_status,
    n=GraphInput.n,
    graph=GraphInput.graph,
    m=GraphInput.m,
    graph_type="rw",
    treewidth=Treewidth.treewidth,
    weighted_treewidth=PartitionBags.max_weight,
    partition_time=PartitionBags.time,
    partition_error_status=PartitionBags.error_status,
    partition_status=PartitionBags.status,
    partition_option=PartitionBags.partition_option,
    treewidth_time=PartitionBags.time,
    treewidth_error_status=PartitionBags.error_status,
    treewidth_status=PartitionBags.status,
  )

# how many timeouts per variant?
rw_cmp_renamed %>%
  group_by(partition_option, partition_status) %>%
  summarise(num=n())

rw_cmp_renamed %>%
  ggplot(aes(x=n, y=m)) +
  geom_point() +
  facet_grid(partition_option~partition_status)


rw_cmp_renamed %>%
  group_by(graph) %>%
  filter(min(weighted_treewidth)!= -1) %>%
  ungroup() %>%
  ggplot(aes(x=n, y=weighted_treewidth, color=partition_option)) +
  geom_point()

rw_cmp_renamed %>%
  filter(treewidth>1) %>%
  filter(weighted_treewidth>1) %>%
  ggplot(aes(x=treewidth, y=weighted_treewidth, size=partition_option, color=2*m/n)) +
  geom_point() +
  scale_x_log10() + scale_y_log10() + annotation_logticks(sides="lb") +
  geom_abline(intercept = 0, slope = 1, color="black",
                  linetype="dashed", size=1.0)

rw_cmp_renamed %>%
  filter(weighted_treewidth!=-1) %>%
  group_by(graph) %>%
  mutate(relative_weight = weighted_treewidth/min(weighted_treewidth),
         relative_time = partition_time/min(partition_time),
         min_weight = min(weighted_treewidth)) %>%
  filter(min_weight!=-1) %>%
  ggplot(aes(x=relative_weight, color=partition_option)) +
  geom_density()
