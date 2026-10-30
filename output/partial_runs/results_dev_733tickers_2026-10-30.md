# PARTIAL RUN (733 tickers, Yahoo first pass only; cells below the pre-registered 500 minimum). Diagnostics, not the development result.

N=9912 firms=287 crowded_session N=997 unknown-session N=2901
sigma(CAR[+2,+60])=0.1675; MDE for a difference in mean CAR at 80% power = 0.0160

cell check surprise_rank: crowded top decile=112, crowded bottom decile=99 (pre-registered minimum 500)
cell check sue_rank: crowded top decile=43, crowded bottom decile=48 (pre-registered minimum 500)

## H1 primary and secondary (coefficient on surprise_rank x crowded_session; firm+yq FE; 2-way clustered)
PRIMARY car_2_60 x surprise_rank: b=0.02094 se=0.01943 t=1.08 95%CI=[-0.01715,0.05902] n=7011; main effects: surprise b=0.01989, crowded b=0.00757
secondary car_2_60 x sue_rank: b=-0.00460 se=0.02033 t=-0.23 95%CI=[-0.04445,0.03524] n=2840; main effects: surprise b=-0.02469, crowded b=-0.00276
secondary car_2_20 x surprise_rank: b=0.00087 se=0.00881 t=0.10 95%CI=[-0.01641,0.01814] n=7011; main effects: surprise b=0.01067, crowded b=0.00447
secondary car_2_20 x sue_rank: b=0.00482 se=0.00891 t=0.54 95%CI=[-0.01265,0.02228] n=2840; main effects: surprise b=-0.00243, crowded b=-0.00228

## Immediate reaction and attention channel
CAR[0,+1] x sue_rank: sxc b=-0.00725 t=-0.78; sue main b=0.02380 n=2840
abnormal volume on crowded: b=0.0256 se=0.0258 t=0.99 n=6967
|CAR[0,+1]| on crowded (noise channel): b=-0.0016 t=-0.97 n=6967

## Robustness grid (interaction coefficient, CAR[+2,+60] x surprise_rank)
calendar-day crowding: b=0.01804 se=0.01890 t=0.95 n=7011
CPI only: b=-0.01203 se=0.04002 t=-0.30 n=7011
EMPSIT only: b=0.07014 se=0.02885 t=2.43 n=7011
FOMC only: b=-0.03117 se=0.02637 t=-1.18 n=7011
excl in-session filings: b=0.01999 se=0.02034 t=0.98 n=5662
excl 2008-09 and 2020: b=0.03117 se=0.01967 t=1.58 n=5907
positive surprises only: b=-0.03362 se=0.05429 t=-0.62 n=3515
negative surprises only: b=0.04198 se=0.05852 t=0.72 n=3496
listed-now firms only: b=0.02381 se=0.01971 t=1.21 n=6940

## Placebos
pseudo-macro days shifted -7d: b=-0.00168 t=-0.08 n=7011
pseudo-macro days shifted +7d: b=0.01368 t=0.62 n=7011
random-day placebo (200 draws): null mean=0.00371 sd=0.01857; actual b=0.02094; share |placebo|>=|actual| = 0.280

## Calendar-time portfolios (top minus bottom market-surprise decile, 60-day hold, equal-weighted)
crowded: daily alpha=0.80bp (t=0.19), net of Corwin-Schultz 66bp half-spread x turnover: -1.28bp (t=-0.30); mean names held=4; mean daily turnover=0.031; n days=3126
uncrowded: daily alpha=1.10bp (t=0.62), net of Corwin-Schultz 63bp half-spread x turnover: -2.45bp (t=-1.37); mean names held=25; mean daily turnover=0.056; n days=3126
difference (crowded minus uncrowded): daily alpha=-0.30bp t=-0.06 n=3126