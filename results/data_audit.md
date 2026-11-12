# Dataset audit

86 raw records; 82 unique compositions. Rank >=3: **7 feasible / 75 infeasible** after grouping. Raw feasible records: 9.

Exact reported at% keys; mean hardness, minimum rank, preserve replicate metadata. Conservative any-replicate screening failure. Duplicate ranks 4/4/5 are all feasible.

Divide by 100; no renormalization or imputation.

Missing values: 0. Hardness range: [2.5380516, 12.8586115] GPa. Predicted solidus: [1801.041279, 3112.077133] °C. Maximum sum error: 1e-08 at%; tolerance 1e-6 at%.

Raw rank counts: {'0': 27, '1': 45, '2': 5, '3': 1, '4': 5, '5': 3}. Group counts: {'0': 27, '1': 43, '2': 5, '3': 1, '4': 4, '5': 2}.

**Calibration support insufficient.** The original plan prefers at least 15 of each class. The threshold stays fixed and calibration is disabled on real data; its code is verified separately. RC-CBO must therefore reduce to ordinary CBO. Calibration efficacy cannot be established here.

Rank is ordinal screening, not tensile strain; solidus is computational Thermo-Calc, not measured hardness. Successfully characterized compositions only.

Local bytes match user-supplied official file MD5 and size. Source publisher metadata/license not independently retrieved due network policy; no new download attempted.

Raw SHA-256: `a9f2b7aaf4b7305535c321bf1354115ac0c157ef1159b23829dff850212ceacd`. Processed SHA-256: `9f92eae22b0f957625b58d78372db7acbc9579f33132376c899f261135690ce0`.
