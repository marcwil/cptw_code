source("helper.R")
source("data_helper.R")

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

df_renamed <- prepare_data(df)


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
    axis.text = element_text(size = 6)
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

create_pdf("../output.pdf/boxplot_solver_quality_small.pdf", boxplot_solver_quality, width=0.30, height = 0.25)
create_pdf("../output.pdf/boxplot_solver_time_small.pdf", boxplot_solver_time, width=0.30, height = 0.25)

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

