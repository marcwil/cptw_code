source("helper.R")
source("girg_stats.R")

tbl <- read.csv("../output_data/rw_greedy_ub.csv")
tbl <- tibble(tbl)


weighted_treewidth <- tbl %>%
  transmute(
    graph = GraphInput.graph,
    m = GraphInput.m,
    n = GraphInput.n,
    avg_deg = 2*m/n,
    time_total = time,
    time_treewidth = Treewidth.time,
    time_partitionbags = PartitionBags.time,
    weighted_tw = PartitionBags.max_weight,
    treewidth = Treewidth.treewidth,
    clique_number = Treewidth.clique_number,
    max_part_num = PartitionBags.max_partition_num,
    mean_part_num = PartitionBags.mean_partition_num,
    median_part_num = PartitionBags.median_partition_num
  )



rwstats <- get_rw_stats()

rw_upper_bounds <- weighted_treewidth %>%
  filter(m>10) %>%
  inner_join(rwstats, by=c("graph", "m", "n")) %>%
  ggplot(aes(
    x = treewidth,
    y = weighted_tw,
    color = clustering,
  )) +
  geom_point(size=0.3) +
  scale_color_viridis() +
  scale_x_log10() +
  scale_y_log10() +
  annotation_logticks(sides='lb',
                      alpha = 0.8,
                      long=unit(0.1, unit='cm'),
                      mid=unit(0.07, unit='cm'),
                      short=unit(0.05, unit='cm')) +
  labs(
    x = "treewidth",
    y = "clique-partitioned treewidth",
    color = "Clustering coeff."
  ) +
  theme(
    legend.position = "top",
    legend.margin = margin(t=0, b=0, unit='cm'),
    legend.box.spacing = unit(0.1, 'cm'),
    legend.key.size = unit(0.4, 'cm'),
    axis.text = element_text(size=6),
    )
rw_upper_bounds
create_pdf("../output.pdf/rw_upper_bounds.pdf", rw_upper_bounds, width=0.48, height=0.43)

tbl <- weighted_treewidth %>%
  inner_join(rwstats, by=c("graph", "m", "n")) %>%
  mutate(small = m<1000,
         small_tw = treewidth <= 20,
         small_wtw = weighted_tw <= 20,
         wtw_cmp_0.9 = weighted_tw <= treewidth*0.9,
         wtw_cmp_0.5 = weighted_tw <= treewidth*0.5,
         wtw_cmp_0.3 = weighted_tw <= treewidth*0.3,
         wtw_cmp_0.1 = weighted_tw <= treewidth*0.1,
         clustering_high = clustering > 0.5) %>%
  pivot_longer(
    c(small,
      small_tw,
      small_wtw),
    names_to = "group",
    values_to = "group_value") %>%
  group_by(group, group_value) %>%
  summarise(
    num = n(),
    num_tw_10 = sum(treewidth<=10),
    num_tw_20 = sum(treewidth<=20),
    num_wtw_10 = sum(weighted_tw<=10),
    num_wtw_20 = sum(weighted_tw<=20),
    "n (mean)" = mean(n),
    "m (mean)" = mean(m),
  )
tbl
## A tibble: 15 × 9
## Groups:   group [7]
#   group           group…¹   num num_t…² num_t…³ num_w…⁴ num_w…⁵ n (me…⁶ m (me…⁷
#   <chr>           <lgl>   <int>   <int>   <int>   <int>   <int>   <dbl>   <dbl>
# 1 clustering_high FALSE    2090     507    1128     481    1174  2859.  10904.
# 2 clustering_high TRUE      311     130     189     154     232  1152.  13783.
# 3 clustering_high NA          2       2       2       2       2     1.5     0.5
# 4 small           FALSE    1224      75     243      68     293  4988.  21657.
# 5 small           TRUE     1179     564    1076     569    1115   194.    481.
# 6 small_tw        FALSE    1084       0       0      17     119  4782.  21913.
# 7 small_tw        TRUE     1319     639    1319     620    1289   872.   2518.
# 8 wtw_cmp_0.1     FALSE    2391     639    1319     632    1397  2640.  11189.
# 9 wtw_cmp_0.1     TRUE       12       0       0       5      11  1838.  26752.
#10 wtw_cmp_0.3     FALSE    2362     639    1317     618    1377  2656.  10968.
#11 wtw_cmp_0.3     TRUE       41       0       2      19      31  1472.  28521.
#12 wtw_cmp_0.5     FALSE    2282     637    1306     607    1356  2687.  10240.
#13 wtw_cmp_0.5     TRUE      121       2      13      30      52  1678.  30636.
#14 wtw_cmp_0.9     FALSE    1187     530    1009     484     997  1887.   4773.
#15 wtw_cmp_0.9     TRUE     1216     109     310     153     411  3367.  17607.
## … with abbreviated variable names ¹​group_value, ²​num_tw_10, ³​num_tw_20,
##   ⁴​num_wtw_10, ⁵​num_wtw_20, ⁶​`n (mean)`, ⁷​`m (mean)`

rw_upper_bounds_m <- weighted_treewidth %>%
  filter(m>10) %>%
  inner_join(rwstats, by=c("graph", "m", "n")) %>%
  ggplot(aes(
    x = m,
    y = weighted_tw,
#    color = clustering,
  )) +
  geom_point(size=0.3) +
#  geom_hex(bins=20) +
  scale_fill_viridis() +
  scale_x_log10() +
  scale_y_log10() +
  annotation_logticks(sides='lb',
                      alpha = 0.8,
                      long=unit(0.1, unit='cm'),
                      mid=unit(0.07, unit='cm'),
                      short=unit(0.05, unit='cm')) +
  labs(
    x = "Edge count",
    y = "Weighted treewidth",
#    color = "Clustering coeff."
  ) +
  theme(
    legend.position = "top",
    legend.margin = margin(t=0, b=0, unit='cm'),
    legend.box.spacing = unit(0.1, 'cm'),
    legend.key.size = unit(0.4, 'cm'),
    axis.text = element_text(size=6),
    )
rw_upper_bounds_m
create_pdf("../output.pdf/rw_upper_bounds_m.pdf", rw_upper_bounds_m, width=0.48, height=0.43)

rw_ub_het_loc_wtw <- weighted_treewidth %>%
  filter(m>10) %>%
  inner_join(rwstats, by=c("graph", "m", "n")) %>%
  ggplot(aes(
    x = deg_cov,
    y = clustering,
#    size = weighted_tw / (treewidth+1),
    color = weighted_tw / (treewidth+1)
  )) +
  geom_point() +
  scale_color_viridis() +
  scale_x_log10() +
  labs(
    x = "Degree coeff. of var.",
    y = "Clustering coeff. (global)",
    color = "cptw / (tw + 1)"
  ) +
  theme(
    legend.position = "top",
    legend.margin = margin(t=0, b=0, unit='cm'),
    legend.box.spacing = unit(0.1, 'cm'),
    legend.key.size = unit(0.4, 'cm'),
    legend.title = element_text(size=6),
    legend.text = element_text(size=6),
    axis.text = element_text(size=6),
    )
rw_ub_het_loc_wtw

create_pdf("../output.pdf/rw_ub_het_loc_wtw.pdf", rw_ub_het_loc_wtw, width=0.48, height=0.43)

# density plot clustering
rw_ub_wtw_clustering <- weighted_treewidth %>%
  filter(m>10) %>%
  inner_join(rwstats, by=c("graph", "m", "n")) %>%
  ggplot(aes(
#    x = num_clique / m,
  #   x = log(num_clique) / log(m),
    x = clustering,
    color = weighted_tw / (treewidth+1) < 0.25,
  )) +
#  scale_x_log10() +
  geom_density() +
  scale_color_discrete(name="cptw / (tw + 1)", labels=c(">= 0.25", "<0.25")) +
  labs(
    x = "Clustering Coefficient (global)",
    y = "Density"
  ) +
  theme(
    legend.position = "top",
    legend.margin = margin(t=0, b=0, unit='cm'),
    legend.box.spacing = unit(0.1, 'cm'),
    legend.key.size = unit(0.2, 'cm'),
    legend.title = element_text(size=6),
    legend.text = element_text(size=6),
    axis.text = element_text(size=6),
    )
rw_ub_wtw_clustering

rw_upper_bounds | rw_ub_wtw_clustering

create_pdf("../output.pdf/rw_ub_wtw_clustering.pdf", rw_ub_wtw_clustering, width=0.48, height=0.43)




# wtw vs graph stats
# clustering: high clustering good
# log_m(num_cliques): small good
# deg_cov: meh
#
avg_deg_plt <- weighted_treewidth %>%
  filter(m>10) %>%
  inner_join(rwstats, by=c("graph", "m", "n")) %>%
  ggplot(aes(x = avg_deg.y, y = weighted_tw / (treewidth+1))) +
  geom_hex(bins=15) +
  scale_fill_viridis(limits = c(0, 600)) +
    scale_x_log10() +
  annotation_logticks(sides='b',
                      alpha = 0.8,
                      long=unit(0.1, unit='cm'),
                      mid=unit(0.07, unit='cm'),
                      short=unit(0.05, unit='cm')) +
  xlab("Avg. degree") +
  ylab(NULL) +
  theme(axis.title.x = element_text(family = "LM Roman", size=8))
avg_deg_plt

deg_cov_plt <- weighted_treewidth %>%
    filter(m>10) %>%
    inner_join(rwstats, by=c("graph", "m", "n")) %>%
    ggplot(aes(x = deg_cov, y = weighted_tw / (treewidth+1))) +
    geom_hex(bins=15) +
  scale_fill_viridis(limits = c(0, 600)) +
    scale_x_log10() +
  annotation_logticks(sides='b',
                      alpha = 0.8,
                      long=unit(0.1, unit='cm'),
                      mid=unit(0.07, unit='cm'),
                      short=unit(0.05, unit='cm')) +
    xlab("Degree coeff. of var.") +
  ylab(NULL) +
  theme(axis.title.x = element_text(family = "LM Roman", size=8))
clustering_plt <- weighted_treewidth %>%
    filter(m>10) %>%
    inner_join(rwstats, by=c("graph", "m", "n")) %>%
    ggplot(aes(x = clustering, y = weighted_tw / (treewidth+1))) +
    geom_hex(bins=15) +
  scale_fill_viridis(limits = c(0, 600)) +
    xlab("Clustering coeff. (global)") +
  ylab(NULL) +
  theme(axis.title.x = element_text(family = "LM Roman", size=8))
clique_count_rel_plt <- weighted_treewidth %>%
    filter(m>10) %>%
    inner_join(rwstats, by=c("graph", "m", "n")) %>%
    ggplot(aes(x = num_clique / m, y = weighted_tw / (treewidth+1))) +
    geom_hex(bins=15) +
  scale_fill_viridis(limits = c(0, 600)) +
    scale_x_log10() +
  annotation_logticks(sides='b',
                      alpha = 0.8,
                      long=unit(0.1, unit='cm'),
                      mid=unit(0.07, unit='cm'),
                      short=unit(0.05, unit='cm')) +
    xlab("Clique count / m") +
  ylab(NULL) +
  theme(axis.title.x = element_text(family = "LM Roman", size=8))
clique_clique_count_exp_plt <- weighted_treewidth %>%
    filter(m>10) %>%
    inner_join(rwstats, by=c("graph", "m", "n")) %>%
    ggplot(aes(x = log(num_clique) / log(m), y = weighted_tw / (treewidth+1))) +
    geom_hex(bins=15) +
  scale_fill_viridis(limits = c(0, 600)) +
    xlab("log_m(Clique count)") +
  ylab(NULL) +
  theme(axis.title.x = element_text(family = "LM Roman", size=8))
clique_clique_number_exp_plt <- weighted_treewidth %>%
    filter(m>10) %>%
    inner_join(rwstats, by=c("graph", "m", "n")) %>%
    ggplot(aes(x = log(clique_number) / log(m), y = weighted_tw / (treewidth+1))) +
    geom_hex(bins=15) +
  scale_fill_viridis(limits = c(0,600)) +
    xlab("log_m(Clique number)") +
  ylab(NULL) +
  theme(axis.title.x = element_text(family = "LM Roman", size=8))


blanklabelplot<-ggplot()+
  labs(y="cptw / (tw+1)")+
  theme_classic()+
  theme(axis.title.y = element_text(family = "LM Roman", size=8))+
  guides(x = "none", y = "none")

rw_wtw_vs_stats <- blanklabelplot + (avg_deg_plt +
  deg_cov_plt +
  clustering_plt +
  clique_count_rel_plt +
  clique_clique_count_exp_plt +
  clique_clique_number_exp_plt) +
  plot_layout(guides = "collect", widths = c(1,1000)) &
  scale_fill_viridis(limits = c(0,600)) &
  theme(
    legend.position='top',
    legend.margin = margin(t=0, b=0, unit='cm'),
    legend.box.spacing = unit(0.1, 'cm'),
    legend.key.size = unit(0.5, 'cm'),
  )
rw_wtw_vs_stats

create_pdf("../output.pdf/rw_wtw_vs_stats.pdf", rw_wtw_vs_stats, width=1, height=0.6)

clustering_standalone <- weighted_treewidth %>%
#    filter(m>10) %>%
  inner_join(rwstats, by=c("graph", "m", "n")) %>%
  ggplot(aes(x = clustering, y = weighted_tw / (treewidth+1))) +
  geom_hex(bins=20) +
  scale_fill_viridis(option='C') +
  labs(
    x = "Clustering coeff. (global)",
    y = "cptw / (tw + 1)") +
  theme(
    legend.position = "top",
    legend.margin = margin(t=0, b=0, unit='cm'),
    legend.box.spacing = unit(0.0, 'cm'),
    legend.key.size = unit(0.4, 'cm'),
    axis.text = element_text(size=6),
    )
clustering_standalone
create_pdf("../output.pdf/rw_clustering_standalone.pdf", clustering_standalone, width=0.48, height=0.43)


#weighted_treewidth %>%
#  pivot_longer(c(treewidth, weighted_tw, clique_number),
#               names_to = "property") %>%
#    ggplot(aes(x = m, y = value, color=property)) +
#    geom_point()
#
#my_breaks = rep(2, 7) ^ seq(from=1, to=7)
#weighted_treewidth %>%
#  filter(m>10) %>%
#  ggplot(aes(
#    x = clique_number / (treewidth+1),
#    y = weighted_tw / (treewidth+1),
#    size = m,
#    color = avg_deg
#  )) +
#  geom_point() +
#  scale_color_gradient(
#    name = "Avg. deg",
#    trans = "log",
#    breaks = my_breaks,
#    labels = my_breaks) +
#  scale_y_continuous(trans = "log10") +
#  annotation_logticks(sides = 'l') +
#  ggtitle("TW vs WTW on 2000 networks; m≤17472, n≤15575")
#
#weighted_treewidth %>%
#  filter(m>10) %>%
#  ggplot(aes(
#    x = treewidth,
#    y = weighted_tw / (treewidth+1),
#    size = m,
#    color = avg_deg
#  )) +
#  geom_point() +
#  scale_color_gradient(
#    name = "Avg. deg",
#    trans = "log",
#    breaks = my_breaks,
#    labels = my_breaks) +
#  scale_x_continuous(trans = "log10") +
#  scale_y_continuous(trans = "log10") +
#  annotation_logticks(sides = 'lb') +
#  ggtitle("TW vs WTW on 2000 networks; m≤17472, n≤15575")
