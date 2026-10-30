# H2 results (holdout sample 2016-01-01..2025-12-31)

N with SUE and session class = 110075; crowded_session N = 18417
Raw means: SUE crowded 0.0531 vs uncrowded 0.0590; share SUE<0 crowded 0.4483 vs 0.4363

H2 primary (SUE on crowded, firm+yq FE, 2-way cluster): b=0.0249 se=0.0206 t=1.21 n=110075
H2 interaction (crowded x discretion): b_crowded=-0.0074 (t=-0.17); b_cxd=0.00166 (t=0.54); n=92097
H2 secondary (P[SUE<0] on crowded, LPM): b=0.0031 se=0.0051 t=0.61 n=110075
H2 by release crowded_cpi (calendar-day dummy): b=0.0352 t=1.07
H2 by release crowded_empsit (calendar-day dummy): b=0.0273 t=0.86
H2 by release crowded_fomc (calendar-day dummy): b=-0.0090 t=-0.27