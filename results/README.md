# Results

Reported outputs, generated from `runs/` by `analysis/`.

- **`registered/<version>/`** — what the frozen decision code returned. These are the
  results. `v4` is `INCONCLUSIVE`, `v5` is `REVERSE_ONSET_EFFECT`, and both are reported;
  neither supersedes the other.
- **`robustness/<version>/`** — a specification multiverse, enumerated **after** both
  registered verdicts were known. It shows how much of each verdict rode on a single
  analysis choice. It is not a result and cannot become one.

Null and inconclusive results are reported here with the same prominence as positive ones,
each carrying the margin it was weighed against.
