source("helper.R")
source("data_helper.R")

df <- read_data("../output_data/branching_variants_girg.csv") %>%
  filter(alpha != 1.375,
         alpha != 1.75)

branching_variants <- df %>%
  mutate(
    alpha = factor(
      alpha,
      levels = c("1.25", "2.5", "5", 'inf'),
      labels = c("1.25", "2.5", "5", '∞')
    )
  ) %>%
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

compare_redrules_data <- branching_variants %>%
  mutate(
    no_errors=error_status=="none" &
      treewidth_status=="success" &
      partition_status=="success",
    suf_weight_red = factor(ifelse(sw_red=='SW', "with", "without"), levels = c("without", "with"))
  ) %>%
  filter(graph_type=="girg",
         no_errors==TRUE)
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
      text = element_text(family = "LM Math"),
      legend.position = "top",
      legend.margin = margin(t=0, b=0, unit='cm'),
      legend.box.spacing = unit(0.1, 'cm'),
      legend.key.size = unit(0.5, 'cm'),
      legend.text = element_text(size = 6)
      )
  )
}

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
