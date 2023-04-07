source("helper.R")
source("data_helper.R")
library(xtable)

rwscalingdf <- read_data("../output_data/rw_ext_vs_heu.csv")

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
