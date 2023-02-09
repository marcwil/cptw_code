
get_graph_stats <- function(path) {
  stats_df <- read_csv(path)
  stats_df <- stats_df %>% extract(
                             GraphInput.girg_options,
                             c("alpha", "dimension", "girg_deg", "ple", "seed", "graph_type"),
                             "alpha=(\\S+)\\sd=(\\S+)\\sdeg=(\\S+)\\sple=(\\S+)\\sseed=(\\S+)\\stype=(\\S+)"
                           )
  stats_df <- stats_df %>%
    transmute(
      time=time,
      error_status=error_status,
      graph=GraphInput.graph,
      n=GraphInput.n,
      n_gen=GraphInput.n_gen,
      m=GraphInput.m,
      alpha=alpha,
      dimension=dimension,
      girg_deg=girg_deg,
      ple=ple,
      seed=seed,
      graph_type=graph_type,
      deg_cov=GraphStats.deg_cov,
      avg_deg=GraphStats.deg_cov,
      largest_clique=GraphStats.largest_clique,
      num_clique=GraphStats.num_cliques,
      sum_clique_sizes=GraphStats.sum_clique_sizes,
      clustering=GraphStats.clustering,
    )
  stats_df <- stats_df[ , colSums(is.na(stats_df)) < nrow(stats_df)]

  return(stats_df)
}

get_girg_stats <- function() {
  get_graph_stats("../output_data/girg_stats.csv")
}
get_rw_stats <- function() {
  get_graph_stats("../output_data/rw_stats.csv")
}

get_graph_stats2 <- function(path) {
  stats_df <- read_csv(path)
  stats_df <- stats_df %>% extract(
                             GraphInput.girg_options,
                             c("alpha", "dimension", "girg_deg", "ple", "seed", "graph_type"),
                             "alpha=(\\S+)\\sd=(\\S+)\\sdeg=(\\S+)\\sple=(\\S+)\\sseed=(\\S+)\\stype=(\\S+)"
                           )
  stats_df <- stats_df %>%
    transmute(
      time=time,
      error_status=error_status,
      graph=GraphInput.graph,
      n=GraphInput.n,
      n_gen=GraphInput.n_gen,
      m=GraphInput.m,
      alpha=alpha,
      dimension=dimension,
      girg_deg=girg_deg,
      ple=ple,
      seed=seed,
      graph_type=graph_type,
      deg_cov=GraphStats.deg_cov,
      avg_deg=GraphStats.deg_cov,
      largest_clique=GraphStats.largest_clique,
      num_clique=GraphStats.num_cliques,
      sum_clique_sizes=GraphStats.sum_clique_sizes,
      clustering=GraphStats.clustering,
      largest_bag_cc=GraphStats2.largest_bag_cc,
    )
  stats_df <- stats_df[ , colSums(is.na(stats_df)) < nrow(stats_df)]

  return(stats_df)
}
