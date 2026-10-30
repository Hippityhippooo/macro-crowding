# Results (holdout sample 2016-01-01..2025-12-31)

N=91595 firms=2877 crowded_session N=13510 unknown-session N=11716
sigma(CAR[+2,+60])=0.1808; MDE for a difference in mean CAR at 80% power = 0.0048

cell check surprise_rank: crowded top decile=1626, crowded bottom decile=1598 (pre-registered minimum 500)
cell check sue_rank: crowded top decile=1100, crowded bottom decile=1120 (pre-registered minimum 500)

## H1 primary and secondary (coefficient on surprise_rank x crowded_session; firm+yq FE; 2-way clustered)
PRIMARY car_2_60 x surprise_rank: b=0.00748 se=0.00662 t=1.13 95%CI=[-0.00550,0.02045] n=79879; main effects: surprise b=0.01241, crowded b=-0.00169
secondary car_2_60 x sue_rank: b=-0.00967 se=0.00582 t=-1.66 95%CI=[-0.02109,0.00174] n=67503; main effects: surprise b=-0.04608, crowded b=-0.00146
secondary car_2_20 x surprise_rank: b=0.00476 se=0.00390 t=1.22 95%CI=[-0.00288,0.01240] n=79879; main effects: surprise b=0.00778, crowded b=0.00104
secondary car_2_20 x sue_rank: b=-0.00337 se=0.00327 t=-1.03 95%CI=[-0.00979,0.00304] n=67503; main effects: surprise b=-0.01121, crowded b=0.00018

## Immediate reaction and attention channel
CAR[0,+1] x sue_rank: sxc b=-0.00100 t=-0.33; sue main b=0.03204 n=67503
abnormal volume on crowded: b=0.0056 se=0.0086 t=0.65 n=79638
|CAR[0,+1]| on crowded (noise channel): b=0.0001 t=0.11 n=79638

## Robustness grid (interaction coefficient, CAR[+2,+60] x surprise_rank)
calendar-day crowding: b=0.00707 se=0.00656 t=1.08 n=79879
CPI only: b=0.00795 se=0.01457 t=0.55 n=79879
EMPSIT only: b=0.00919 se=0.00902 t=1.02 n=79879
FOMC only: b=0.00059 se=0.00925 t=0.06 n=79879
excl in-session filings: b=0.00781 se=0.00662 t=1.18 n=75682
excl 2008-09 and 2020: b=0.00549 se=0.00696 t=0.79 n=72325
positive surprises only: b=0.03413 se=0.01729 t=1.97 n=39930
negative surprises only: b=-0.00383 se=0.01946 t=-0.20 n=39949
listed-now firms only: b=0.00659 se=0.00656 t=1.01 n=79735

## Placebos
pseudo-macro days shifted -7d: b=-0.00916 t=-1.44 n=79879
pseudo-macro days shifted +7d: b=0.01548 t=1.90 n=79879
random-day placebo (1000 draws): null mean=0.00037 sd=0.00733; actual b=0.00748; share |placebo|>=|actual| = 0.299

## Calendar-time portfolios (top minus bottom market-surprise decile, 60-day hold, equal-weighted)
crowded: daily alpha=2.47bp (t=1.70), net of Corwin-Schultz 74bp half-spread x turnover: -1.88bp (t=-1.27); mean names held=67; mean daily turnover=0.059; n days=2871
uncrowded: daily alpha=0.83bp (t=0.96), net of Corwin-Schultz 68bp half-spread x turnover: -2.87bp (t=-3.33); mean names held=280; mean daily turnover=0.055; n days=2871
difference (crowded minus uncrowded): daily alpha=1.64bp t=1.07 n=2871