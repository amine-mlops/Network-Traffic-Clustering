# 01 - EDA key facts

- train shape: (82332, 45), test shape: (175341, 45)
- identifier: ['id'] (dropped)
- reference labels: ['attack_cat', 'label'] (kept separate)
- numerical features: 39
- categorical features: 3 -> ['proto', 'service', 'state']
- missing / duplicates / infinities / negatives: 0 in both splits
- proto cardinality: 131 (train), top-10 coverage 0.9513
- service cardinality: 13, state cardinality: 7
- attack rate: train 0.5506, test 0.6806
- normal flows in training set (Chapter B pool): 37000

See results/metrics/01_*.csv for full tables and results/figures/01_*.png for plots.