parse_girg_params <- function(df) {
  res <- df %>% extract(
                  GraphInput.girg_options,
                  c("alpha", "dimension", "girg_deg", "ple", "seed", "graph_type"),
                  "alpha=(\\S+)\\sd=(\\S+)\\sdeg=(\\S+)\\sple=(\\S+)\\sseed=(\\S+)\\stype=(\\S+)"
                )
  return(res)
}

rename_partition_option <- function(df){
  return(df %>%
         mutate(
           partition_option = case_when(
             partition_option =="BranchingPartition" ~ "B&B",
             partition_option =="FastLargestClique" ~ "MC",
             partition_option =="LargestCliqueRepeat" ~ "RMC",
             partition_option =="MinHSPartition(HittingSet(HSBranchReduce))" ~ "SC",
             partition_option =="MinHSPartition(HittingSet(GurobiHS))" ~ "HSGRB",
             partition_option =="WeightedHSPartition" ~ "WSC",
           )) %>%
         mutate(
           partition_option = as.factor(partition_option)
         )
         )
}

rename_columns <- function(df){
  res <- df %>%
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
      avg_deg=GraphStats.avg_deg,
      largest_clique=GraphStats.largest_clique,
      num_clique=GraphStats.num_cliques,
      sum_clique_sizes=GraphStats.sum_clique_sizes,
      clustering=GraphStats.clustering,
      largest_bag_cc=GraphStats2.largest_bag_cc,
      error_status=error_status,
      weighted_treewidth=PartitionBags.max_weight,
      partition_time=PartitionBags.time,
      partition_error_status=PartitionBags.error_status,
      partition_status=PartitionBags.status,
      partition_option=gsub("Partition\\((.+)\\)", "\\1", PartitionBags.partition_option),
      max_partition_num=PartitionBags.max_partition_num,
      mean_partition_num = PartitionBags.mean_partition_num,
      median_partition_num = PartitionBags.median_partition_num,
      max_partition_num=PartitionBags.max_partition_num,
      num_branching_sum=PartitionBags.num_branching_sum,
      num_clq_red=PartitionBags.num_clq_red,
      num_lb2_reductions_sum=PartitionBags.num_lb2_reductions_sum,
      num_lb2_reductions_max=PartitionBags.num_lb2_reductions_max,
      num_lb_reductions_sum=PartitionBags.num_lb_reductions_sum,
      num_lb_reductions_max=PartitionBags.num_lb_reductions_max,
      num_sw_reductions_sum=PartitionBags.num_sw_reductions_sum,
      num_sw_reductions_max=PartitionBags.num_sw_reductions_max,
      treewidth=Treewidth.treewidth,
      treewidth_time=Treewidth.time,
      treewidth_error_status=Treewidth.error_status,
      treewidth_status=Treewidth.status,
      )
  return(res)
}

remove_empty_cols <- function(df) {
  return(df[,colSums(is.na(df)) < nrow(df)])
}


prepare_data <- function(df) {
  df <- df %>%
    parse_girg_params %>%
    rename_columns %>%
    rename_partition_option %>%
    remove_empty_cols

  return(df)
}

read_data <- function(path) {
  df <- read_csv(path) %>%
    prepare_data

  return(df)
}
