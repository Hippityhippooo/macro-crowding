# H2 results (dev sample 2005-01-01..2015-12-31)

N with SUE and session class = 38181; crowded_session N = 5558
Raw means: SUE crowded 0.1025 vs uncrowded 0.0893; share SUE<0 crowded 0.4271 vs 0.4243

H2 primary (SUE on crowded, firm+yq FE, 2-way cluster): b=-0.0003 se=0.0302 t=-0.01 n=38181
H2 interaction (crowded x discretion): b_crowded=0.0320 (t=0.64); b_cxd=-0.00267 (t=-0.70); n=37052
H2 secondary (P[SUE<0] on crowded, LPM): b=0.0009 se=0.0085 t=0.11 n=38181
H2 by release crowded_cpi (calendar-day dummy): b=-0.0095 t=-0.20
H2 by release crowded_empsit (calendar-day dummy): b=0.0054 t=0.11
H2 by release crowded_fomc (calendar-day dummy): b=-0.0037 t=-0.07