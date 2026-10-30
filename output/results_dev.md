# Results (dev sample 2005-01-01..2015-12-31)

N=63042 firms=1814 crowded_session N=6003 unknown-session N=17662
sigma(CAR[+2,+60])=0.1614; MDE for a difference in mean CAR at 80% power = 0.0063

cell check surprise_rank: crowded top decile=676, crowded bottom decile=683 (pre-registered minimum 500)
cell check sue_rank: crowded top decile=266, crowded bottom decile=243 (pre-registered minimum 500)

## H1 primary and secondary (coefficient on surprise_rank x crowded_session; firm+yq FE; 2-way clustered)
PRIMARY car_2_60 x surprise_rank: b=-0.01482 se=0.00714 t=-2.07 95%CI=[-0.02882,-0.00082] n=45380; main effects: surprise b=0.01995, crowded b=0.00163
secondary car_2_60 x sue_rank: b=-0.01059 se=0.00864 t=-1.23 95%CI=[-0.02753,0.00634] n=18376; main effects: surprise b=-0.02340, crowded b=0.00428
secondary car_2_20 x surprise_rank: b=-0.00757 se=0.00387 t=-1.96 95%CI=[-0.01515,0.00001] n=45380; main effects: surprise b=0.00986, crowded b=0.00132
secondary car_2_20 x sue_rank: b=-0.00020 se=0.00373 t=-0.05 95%CI=[-0.00751,0.00711] n=18376; main effects: surprise b=-0.00390, crowded b=0.00193

## Immediate reaction and attention channel
CAR[0,+1] x sue_rank: sxc b=-0.00006 t=-0.02; sue main b=0.02852 n=18376
abnormal volume on crowded: b=-0.0058 se=0.0114 t=-0.51 n=45138
|CAR[0,+1]| on crowded (noise channel): b=-0.0006 t=-0.86 n=45138

## Robustness grid (interaction coefficient, CAR[+2,+60] x surprise_rank)
calendar-day crowding: b=-0.01314 se=0.00693 t=-1.90 n=45380
CPI only: b=0.00347 se=0.01303 t=0.27 n=45380
EMPSIT only: b=0.00164 se=0.01067 t=0.15 n=45380
FOMC only: b=-0.03838 se=0.00901 t=-4.26 n=45380
excl in-session filings: b=-0.01451 se=0.00740 t=-1.96 n=37509
excl 2008-09 and 2020: b=-0.00984 se=0.00705 t=-1.40 n=38294
positive surprises only: b=-0.01692 se=0.02002 t=-0.85 n=22761
negative surprises only: b=-0.03655 se=0.02477 t=-1.48 n=22619
listed-now firms only: b=-0.01440 se=0.00717 t=-2.01 n=45309

## Placebos
pseudo-macro days shifted -7d: b=-0.01052 t=-1.29 n=45380
pseudo-macro days shifted +7d: b=0.01301 t=1.58 n=45380
random-day placebo (1000 draws): null mean=-0.00083 sd=0.00882; actual b=-0.01482; share |placebo|>=|actual| = 0.090

## Calendar-time portfolios (top minus bottom market-surprise decile, 60-day hold, equal-weighted)
crowded: daily alpha=-1.16bp (t=-0.58), net of Corwin-Schultz 66bp half-spread x turnover: -5.00bp (t=-2.44); mean names held=26; mean daily turnover=0.059; n days=3126
uncrowded: daily alpha=1.64bp (t=2.02), net of Corwin-Schultz 65bp half-spread x turnover: -1.76bp (t=-2.10); mean names held=160; mean daily turnover=0.052; n days=3126
difference (crowded minus uncrowded): daily alpha=-2.81bp t=-1.38 n=3126