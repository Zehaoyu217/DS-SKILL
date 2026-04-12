# Checklist: Statistical Assumption Tests

Gate for any parametric inference in `findings/`. Iron Law #8.

## Per-test assumption map

| Test | Required assumptions | Check | Non-parametric fallback |
|---|---|---|---|
| Student's t-test | Normality (each group), equal variance | Shapiro-Wilk (n<5000) / QQ-plot; Levene | Mann-Whitney U |
| Paired t-test | Normality of differences | Shapiro-Wilk on diff | Wilcoxon signed-rank |
| One-way ANOVA | Normality per group, homoscedasticity, independence | Shapiro-Wilk + Levene | Kruskal-Wallis |
| Pearson correlation | Linearity + bivariate normal | Scatter + Shapiro | Spearman rank |
| Linear regression inference | Linearity, normal residuals, homoscedasticity, independence | Residual plot, Shapiro on residuals, Breusch-Pagan, Durbin-Watson | Robust SE / quantile regression |
| Chi-square | Expected cell count ≥ 5 | Expected counts table | Fisher's exact |

## Multiple-comparison handling
- Declare family of tests before running.
- Apply Holm-Bonferroni or Benjamini-Hochberg correction.
- Report both raw and adjusted p-values in finding-cards.

## Power
- Document n, effect size (estimated), power before the test.
- Underpowered tests must be flagged in the finding-card.

## Persona
Statistician signs. Unsigned blocks VALIDATE exit for parametric claims.
