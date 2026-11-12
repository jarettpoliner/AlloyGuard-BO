# Model card

**Use:** CPU-only, finite-pool retrospective selection among nine-element atomic-fraction compositions. Recommend the next existing candidate using only revealed observations. Not validated for synthesis, engineering deployment, safety certification, or out-of-pool alloy generation.

**Targets:** hardness in GPa; probability of experimental ordinal ductility rank >=3. Input coordinates Hf, Mo, Nb, Re, Ru, Ta, Ti, W, Zr. Predicted solidus is metadata, not a hardness fidelity. Rank is not physical tensile elongation.

**Architecture:** separate observed-only GP regression and GP classification, optional observed-group cross-fit temperature, approximate EI·probability acquisition. See SCIENTIFIC_METHOD.md for exact parameters and noise treatment. Feasibility heads are not a joint model of correlated mechanical outcomes. Raw/simplex geometry and Euclidean kernels may poorly capture compositional physics.

**Data support:** 82 unique experimentally characterized compositions; seven pass screening. Real-data calibration is disabled by the predeclared support gate. No experimentally validated calibrated model is delivered; the calibration code exists and passes software tests. Single-class observations produce an explicit smoothed class prior. No silently fit single-class GPC.

**Uncertainty:** EI uses latent SD; observation intervals add assumed 0.15 GPa noise. Probabilities and Gaussian intervals are model forecasts, not physical certainty or guaranteed coverage. StandardScaler fits only revealed observations. Sparse initial chemistry and class imbalance can yield overconfident extrapolation. Recorded distance flag is a heuristic.

**Validation:** real file checksums/schema; 38 initial unit/integration tests; deterministic toy; one-seed and five-seed smoke; 30-seed real-data benchmark; raw-outcome audit and a complete deterministic reproduction. Current exact outcomes and interval coverage are in results/summary.csv and REPORT.md. No prospective laboratory validation.

**Failure modes:** few positive labels, initially single-class training, kernel bound optima, assumed homoscedastic noise, ordinal aggregation, outcome-dependent selection populations, correlated replay seeds, narrow pool. Report includes a real high-predicted-hardness/infeasible selected case and low/no calibration efficacy support. A low feasibility probability is a preference, not a hard filter; even CBO may select an infeasible candidate.

**Output contract:** frozen Decision fields include ID/composition, mean/latent and observation SD, approximate observation interval, raw/calibrated probabilities, status/temperature, EI/product/acquisition score, chemistry-distance diagnostic, constraints/rationale, training count, policy/step, config/data hashes and fit diagnostics. Full decision JSONL retains observed IDs and warning/fallback evidence. No confidence score is represented as laboratory certainty.
