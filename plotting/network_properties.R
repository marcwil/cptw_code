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

stats_renamed <- read_data('../output_data/girg_stats.csv')

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
         alpha != 1.75) %>%
  mutate(alpha = factor(alpha, levels = c("1.25", "2.5", "5", 'inf')))

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
  scale_color_discrete(labels = c("1.25", "2.5", "5", TeX("$\\infty$"))) +
  scale_shape_discrete(labels = c("1.25", "2.5", "5", TeX("$\\infty$"))) +
  annotation_logticks(sides='l',
                      alpha = 0.8,
                      long=unit(0.1, unit='cm'),
                      mid=unit(0.07, unit='cm'),
                      short=unit(0.05, unit='cm')) +
  labs(
    x=NULL,
    y="cp-treewidth",
    color="α",
    shape="α",
  ) +
  theme(text = element_text(family = "LM Math"))
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
  scale_color_discrete(labels = c("1.25", "2.5", "5", TeX("$\\infty$"))) +
  scale_shape_discrete(labels = c("1.25", "2.5", "5", TeX("$\\infty$"))) +
  annotation_logticks(sides='l',
                      alpha = 0.8,
                      long=unit(0.1, unit='cm'),
                      mid=unit(0.07, unit='cm'),
                      short=unit(0.05, unit='cm')) +
  labs(
    x=NULL,
    y="Clique count (sol.)",
    color="α",
    shape="α",
  ) +
  theme(text = element_text(family = "LM Math"))
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
  scale_color_discrete(labels = c("1.25", "2.5", "5", TeX("$\\infty$"))) +
  scale_shape_discrete(labels = c("1.25", "2.5", "5", TeX("$\\infty$"))) +
  labs(
    x=NULL,
    y="Clique count",
    color="α",
    shape="α",
  ) +
  theme(text = element_text(family = "LM Math"))
plot_params_num_clique
create_pdf("../output.pdf/plot_alpha_ple_num_clique.pdf", plot_params_num_clique, 0.48)

# what is the relationship of alpha*ple ~ instance_size
stats2_df <- read_data("../output_data/girg_stats2.csv")
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
  scale_color_discrete(labels = c("1.25", "2.5", "5", TeX("$\\infty$"))) +
  scale_shape_discrete(labels = c("1.25", "2.5", "5", TeX("$\\infty$"))) +
  annotation_logticks(sides='l',
                      alpha = 0.8,
                      long=unit(0.1, unit='cm'),
                      mid=unit(0.07, unit='cm'),
                      short=unit(0.05, unit='cm')) +
  labs(
    x=NULL,
    y="Clique count (bag)",
    color="α",
    shape="α",
  ) +
  theme(text = element_text(family = "LM Math"))
plot_params_instance_size
create_pdf("../output.pdf/plot_alpha_ple_inst_size.pdf", plot_params_instance_size, 0.48)

blanklabelplot<-ggplot()+
  labs(x="Power-law exponent")+
  theme_classic()+
  theme(axis.title.x = element_text(family = "LM Math", size=9))+
  guides(x = "none", y = "none")
plot_params_stast3 <- ((plot_params_wtw |
  plot_params_num_clique |
  plot_params_instance_size) / blanklabelplot) +
  plot_layout(guides = "collect", heights = c(1000,1)) &
#  scale_color_discrete() &
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
  theme(
    legend.position = "top",
    legend.margin = margin(t=0, b=0, unit='cm'),
    legend.box.spacing = unit(0.1, 'cm'),
  )
plot_params_stats4
create_pdf("../output.pdf/plot_params_stats4.pdf", plot_params_stats4, width=1, height = 0.37)

((plot_params_num_clique | plot_params_instance_size | plot_params_sol_size | plot_params_wtw) / blanklabelplot) +
  plot_layout(guides = "collect", heights = c(1000,1)) &
#  scale_color_discrete(labels = c("1.25", "2.5", "5", TeX("$\\infty$"))) &
#  scale_shape_discrete(labels = c("1.25", "2.5", "5", TeX("$\\infty$"))) &
  theme(
    legend.position = "top",
    legend.margin = margin(t=0, b=0, unit='cm'),
    legend.box.spacing = unit(0.1, 'cm'),
  )

(plot_params_num_clique | plot_params_instance_size) +
  plot_layout(guides = "collect", heights = c(1000,1)) &
#  scale_color_discrete(labels = c("1.25", "2.5", "5", TeX("$\\infty$"))) &
#  scale_shape_discrete(labels = c("1.25", "2.5", "5", TeX("$\\infty$"))) &
  theme(
    legend.position = "top",
    legend.margin = margin(t=0, b=0, unit='cm'),
    legend.box.spacing = unit(0.1, 'cm'),
  ) &
  labs(
    color="α",
    shape="α",
  )
