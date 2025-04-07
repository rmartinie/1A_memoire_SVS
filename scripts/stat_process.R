# ================================================
# ENS 2SEP
# Traitement et analyse des données mémoire 1A SVS 2024-2025
# MARTINIE Romain & ROUANET Léonine
# ================================================

# Chargement des bibliothèques nécessaires
library(readxl)        # Importation de données Excel
library(ggplot2)       # Visualisation
library(gridExtra)     # Organisation de plusieurs graphiques
library(dplyr)         # Manipulation de données
library(rstatix)       # Tests statistiques 
library(psych)         # Statistiques descriptives

# ---- Configuration du chemin  ----
# Définir le chemin du répertoire de travail
WRK_PATH <- "/home/user/path"

# Changer le répertoire de travail
setwd(WRK_PATH)

# Vérification du répertoire de travail
cat("Répertoire de travail actuel : ", getwd(), "\n")

# ---- Importation et préparation des données ----
# Importation et conversion des types de variables
data <- read_excel('dataframe.xlsx') |>
  mutate(
    condition = factor(condition, levels = c('NB', 'LB', 'WB')),
    across(
      c(max_force, delta_spine_flex, TTP, duration, speed_spine_flex), 
      as.numeric
    )
  )

# ---- Définition des variables d'analyse ----
# Variables à analyser
variables <- c("max_force", "delta_spine_flex")

# Titres des graphiques 
titres <- c(
  expression(bold(F[max]~"(N)")),
  expression(bold(Delta*Flex~"(°)"))
)

# Comparaisons paire à paire pour les tests post-hoc
my_comparisons <- list(c("LB", "WB"), c("LB", "NB"), c("WB", "NB"))

# ---- Vérification de la normalité ----
for(var in variables) {
  # Test de Shapiro-Wilk par condition
  normalite <- data %>% 
    group_by(condition) %>% 
    summarise(
      p_value = shapiro.test(!!sym(var))$p.value
    )
  
  cat("\n===== Test de normalité pour", var, "=====\n")
  print(normalite)
  
  # QQ plots pour visualisation de la normalité
  qqplot <- ggplot(data, aes(sample = !!sym(var))) +
    geom_qq() +
    geom_qq_line() +
    facet_wrap(~condition) +
    labs(title = paste("QQ Plot pour", var)) +
    theme_minimal()
  
  print(qqplot)
}

# ---- Analyse statistique et visualisation ----
# Initialisation des listes pour stockage
plots <- list()
results <- data.frame(Variable = character(), 
                      Comparison = character(), 
                      p_value = numeric(), 
                      cohen = numeric(),
                      stringsAsFactors = FALSE)

# Analyse pour chaque variable
for (i in 1:length(variables)) {
  var <- variables[i]
  titre <- titres[i]
  
  # ANOVA à mesures répétées
  anova_result <- data %>%
    anova_test(
      dv = var,                # Variable dépendante
      wid = subject,           # Identifiant des sujets
      within = condition,      # Condition intra-sujet
      effect.size = "pes"      # Eta carré partiel comme taille d'effet
    )
  
  # Application de la correction de Greenhouse-Geisser si sphéricité violée
  if (anova_result$`Mauchly's Test for Sphericity`$p < 0.05) {
    anova_table <- anova_result$`Sphericity Corrections` %>% 
      as_tibble() %>%
      select(Effect, `DF[GG]`, `p[GG]`) %>%
      rename("p" = "p[GG]")
    
    anova_table$`η² partiel` <- anova_result$ANOVA$pes
    anova_table$F <- anova_result$ANOVA$F
  } else {
    anova_table <- anova_result$ANOVA %>% 
      as_tibble() %>%
      select(Effect, DFn, DFd, F, p, pes) %>%
      rename(
        "F" = "F",
        "p" = "p",
        "η² partiel" = "pes"
      )
  }
  
  cat("\n===== ANOVA pour", var, "=====\n")
  print(anova_table)
  
  p_value <- anova_table$p
  text <- if(p_value < 0.001) {
    "ANOVA: p < 0.001"
  } else {
    sprintf("ANOVA: p = %.3f", p_value)
  }
  
  # Tests post-hoc (t-tests appariés)
  comparisons <- list(c("LB", "NB"), c("NB", "WB"), c("LB", "WB"))
  formula <- reformulate("condition", response = var)
  
  result <- data %>%
    pairwise_t_test(formula, paired = TRUE, p.adjust.method = "BH")
  
  # Stockage des résultats des comparaisons
  for (comp in comparisons) {
    group1 <- comp[1]
    group2 <- comp[2]
    
    filtered_result <- result %>%
      filter((group1 == !!group1 & group2 == !!group2) | (group1 == !!group2 & group2 == !!group1))
    
    if (nrow(filtered_result) > 0) {
      results <- rbind(results, data.frame(
        Variable = var,
        Comparison = paste(group1, "vs", group2),
        p_value = filtered_result$p.adj[1],
        cohen = filtered_result$statistic[1]
      ))
    }
  }
  
  # Affichage 
  if (p_value < 0.05){
    cat("\n===== Tests T post-hoc avec correction Benjamini Hochberg pour", var, "=====\n")
    print(result)
  }
  
  # Création du boxplot
  plot <- ggplot(data, aes(x = condition, y = !!sym(var), fill = condition, color = condition)) +
    geom_boxplot(alpha = 0.4) +  
    geom_jitter(width = 0, stroke = 0, size = 2) + 
    geom_line(aes(group = subject), color = "grey", size = 1, alpha = 0.5) + 
    ylab(titre) + 
    xlab('') + 
    scale_fill_manual(values = c('LB' = '#5ba300', 'WB' = '#0073e6', 'NB' = '#b51963')) + 
    scale_color_manual(values = c('LB' = '#5ba300', 'WB' = '#0073e6', 'NB' = '#b51963')) + 
    theme_minimal() + 
    theme(axis.title.y = element_text(face = 'bold')) + 
    theme(legend.position = "none") +
    annotate("text", 
             x = 1.5, 
             y = max(data[[var]]) * 1.02,  
             label = text,
             size = 4,
             fontface = "italic")
  
  plots[[i]] <- plot
}

# Affichage des graphiques côte à côte
final_plot <- grid.arrange(grobs = plots, ncol = length(plots))

# ---- Exportation des graphiques ----
# Ajustement de la largeur en fonction du nombre de graphiques
largeur <- 3.5 * length(plots)
ggsave("results.pdf", plot = final_plot, device = "pdf", width = largeur, height = 5)

# ---- Statistiques descriptives ----
cat("\n===== Calcul des gains de force =====\n")

# Extraction des forces
conditions <- c("NB", "LB", "WB")
forces <- list()
for (cond in conditions) {
  forces[[cond]] <- data$max_force[data$condition == cond]
}

# Création du data frame vide
n_subjects <- length(forces$NB)
gains <- data.frame(matrix(nrow = n_subjects, ncol = 0))

# Boucle 
comparisons <- list(c("NB", "LB"), c("NB", "WB"), c("LB", "WB"))
for (comp in comparisons) {
  base_cond <- comp[1]
  target_cond <- comp[2]
  prefix <- paste0(base_cond, "_", target_cond, "_")
  
  # Calculs vectorisés pour chaque paire
  gains[[paste0(prefix, "rel")]] <- (forces[[target_cond]] / forces[[base_cond]] - 1) * 100
  gains[[paste0(prefix, "abs")]] <- forces[[target_cond]] - forces[[base_cond]]
  gains[[paste0(prefix, "abs_kg")]] <- (forces[[target_cond]] - forces[[base_cond]]) / 9.81
}

print(describe(gains))
