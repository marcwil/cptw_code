library(tidyverse)
library(ggplot2)
library(viridis)
library(patchwork)
library(scales)
library(showtext)

remove_empty_cols <- function(df) {
  return(df[,colSums(is.na(df)) < nrow(df)])
}

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
             partition_option =="WeightedHSPartition" ~ "WSC"
           )) %>%
         mutate(
           partition_option = as.factor(partition_option)
         )
         )
}

### Theme stuff taken from https://github.com/thobl/external-validity/blob/main/R/helper/theme.R
## general theme
theme_set(theme_bw())

theme_update(plot.margin = margin(t=0.1,r=0.1,b=0.1,l=0.1, unit="cm"))

## latex font
font_add("LM Roman", "lmroman10-regular.otf")
showtext_auto()
theme_update(text = element_text(family = "LM Roman", size = 9))

## some colors
blue   <- "#5EA6E5"
green  <- "#6EC620"
yellow <- "#EEC200"
red    <- "#E62711"
violet <- "#c6468d"
purple <- "#613872"
gray   <- "#666666"

## pdf output; width and height relative to LIPIcs text width
create_pdf <- function(file, plot, width = 1, height = 0.43) {
    textwidth <- 14 / 2.54
    pdf(file, width = width * textwidth, height = height * textwidth)
    print(plot)
    no_output <- dev.off()
}
