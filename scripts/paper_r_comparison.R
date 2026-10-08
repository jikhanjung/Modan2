#!/usr/bin/env Rscript
# Independent implementation of the analyses of the Modan2 paper's worked
# example, for comparison with Modan2. Called by paper_r_comparison.py, which
# writes the raw coordinates and grouping variables to a JSON file and reads
# back what this script writes; it can also be run on its own:
#
#     Rscript scripts/paper_r_comparison.R input.json output.json
#
# Each step uses the standard R implementation, starting again from the raw
# coordinates rather than from anything Modan2 computed:
#
#   GPA     geomorph::gpagen, without projection to tangent space (Proj = FALSE),
#           since Modan2 analyses the Procrustes coordinates themselves
#   PCA     stats::prcomp on the aligned coordinates
#   CVA     MASS::lda on the leading principal component scores; leave-one-out
#           classification refits prcomp and lda without the held-out specimen
#   MANOVA  stats::manova on the same scores, all four test statistics
#
# The number of components is chosen by the rule the paper states (95% of the
# variance, at most 20 and at most n - g - 1), applied here to R's own PCA.

suppressPackageStartupMessages({
  library(jsonlite)
  library(geomorph)
  library(MASS)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2) stop("usage: paper_r_comparison.R input.json output.json")
input <- fromJSON(args[1], simplifyVector = TRUE)

raw <- input$coords                      # specimens x landmarks x dimensions
A <- aperm(raw, c(2, 3, 1))              # geomorph's landmarks x dimensions x specimens
n <- dim(A)[3]

gpa <- gpagen(A, Proj = FALSE, tol = input$gpa_tol, print.progress = FALSE)
X <- two.d.array(gpa$coords)             # x1, y1, z1, x2, ... as Modan2 flattens them

pca <- prcomp(X)
ratio <- pca$sdev^2 / sum(pca$sdev^2)
k95 <- which(cumsum(ratio) >= input$variance_target)[1]

components <- function(n_groups) min(k95, input$max_variables, n - n_groups - 1)

analyse <- function(groups) {
  g <- factor(groups)
  k <- components(nlevels(g))
  S <- pca$x[, 1:k, drop = FALSE]

  fit <- lda(S, grouping = g)
  resubstituted <- predict(fit)

  held_out <- character(n)
  for (i in seq_len(n)) {
    train <- prcomp(X[-i, , drop = FALSE])
    scores <- train$x[, 1:k, drop = FALSE]
    test <- predict(train, X[i, , drop = FALSE])[, 1:k, drop = FALSE]
    held_out[i] <- as.character(predict(lda(scores, grouping = droplevels(g[-i])), test)$class)
  }

  m <- manova(S ~ g)
  tests <- lapply(c(Wilks = "Wilks", Pillai = "Pillai", HotellingLawley = "Hotelling-Lawley", Roy = "Roy"),
                  function(test) {
                    row <- summary(m, test = test)$stats[1, ]
                    list(value = unname(row[2]), f_statistic = unname(row[3]),
                         df_num = unname(row[4]), df_den = unname(row[5]), p_value = unname(row[6]))
                  })

  list(
    n_groups = nlevels(g),
    components = k,
    canonical_proportions = fit$svd^2 / sum(fit$svd^2),
    canonical_scores = unname(resubstituted$x[, 1:min(2, ncol(resubstituted$x)), drop = FALSE]),
    resubstitution_predictions = as.character(resubstituted$class),
    loocv_predictions = held_out,
    loocv_accuracy = mean(held_out == as.character(g)) * 100,
    manova = tests
  )
}

versions <- sapply(c("geomorph", "RRPP", "MASS", "jsonlite"), function(p) as.character(packageVersion(p)))
result <- list(
  versions = as.list(c(R = paste(R.version$major, R.version$minor, sep = "."), versions)),
  gpa = list(coords = unname(aperm(gpa$coords, c(3, 1, 2))), iterations = gpa$iter),
  pca = list(eigenvalues = unname(pca$sdev^2), ratio = unname(ratio), components_to_target = k95,
             scores = unname(pca$x[, 1:k95, drop = FALSE])),
  groupings = lapply(input$groupings, analyse)
)
write_json(result, args[2], digits = NA, auto_unbox = TRUE)
