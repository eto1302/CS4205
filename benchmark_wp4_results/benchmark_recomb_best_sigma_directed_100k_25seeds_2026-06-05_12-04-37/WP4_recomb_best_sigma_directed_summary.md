# Directed recombination benchmark — best sigma strategies

- runtime: 2399.7s

- output folder: C:\Users\agata\OneDrive\Pulpit\uni\! Master - StudyGuides\Q4\Evolutionary Algorithms\Assignment\CS4205\benchmark_wp4_results\benchmark_recomb_best_sigma_directed_100k_25seeds_2026-06-05_12-04-37

- rows in per_run.csv: 450


## Median final_gap by n, strategy, treatment

|   n | strategy          | treatment   |   median_final_gap |        q1 |        q3 |
|----:|:------------------|:------------|-------------------:|----------:|----------:|
|   7 | MULTIPLE_VARIANCE | baseline    |          0.0491411 | 0.0291786 | 0.0682261 |
|   7 | MULTIPLE_VARIANCE | circle_pair |          0.479215  | 0.427725  | 0.497291  |
|   7 | MULTIPLE_VARIANCE | coordinate  |          0.46054   | 0.427725  | 0.479677  |
|   7 | SINGLE_VARIANCE   | baseline    |          0.0522277 | 0.0347304 | 0.0611696 |
|   7 | SINGLE_VARIANCE   | circle_pair |          0.461352  | 0.437013  | 0.495817  |
|   7 | SINGLE_VARIANCE   | coordinate  |          0.437715  | 0.396284  | 0.480222  |
|  10 | MULTIPLE_VARIANCE | baseline    |          0.136092  | 0.128089  | 0.153802  |
|  10 | MULTIPLE_VARIANCE | circle_pair |          0.536086  | 0.511883  | 0.558071  |
|  10 | MULTIPLE_VARIANCE | coordinate  |          0.522065  | 0.506516  | 0.556403  |
|  10 | SINGLE_VARIANCE   | baseline    |          0.133756  | 0.101818  | 0.177838  |
|  10 | SINGLE_VARIANCE   | circle_pair |          0.530005  | 0.503448  | 0.544904  |
|  10 | SINGLE_VARIANCE   | coordinate  |          0.546204  | 0.501804  | 0.563793  |
|  15 | MULTIPLE_VARIANCE | baseline    |          0.290562  | 0.272994  | 0.323211  |
|  15 | MULTIPLE_VARIANCE | circle_pair |          0.620374  | 0.607986  | 0.641616  |
|  15 | MULTIPLE_VARIANCE | coordinate  |          0.607986  | 0.547966  | 0.627766  |
|  20 | MULTIPLE_VARIANCE | baseline    |          0.387672  | 0.324788  | 0.442751  |
|  20 | MULTIPLE_VARIANCE | circle_pair |          0.65923   | 0.635456  | 0.675074  |
|  20 | MULTIPLE_VARIANCE | coordinate  |          0.668251  | 0.638249  | 0.672374  |


## Comparisons (from stats.py)

| treatment   | wp   |   n_circles | metric         |   n_base |   n_arm |   base_median |   arm_median |     effect |      ci_lo |      ci_hi |     a12 |    p_value | marker   | note                                        |
|:------------|:-----|------------:|:---------------|---------:|--------:|--------------:|-------------:|-----------:|-----------:|-----------:|--------:|-----------:|:---------|:--------------------------------------------|
| circle_pair | WP4  |           7 | final_gap      |       50 |      50 |      0.051832 |     0.471097 |  -0.419265 |  -0.437732 |  -0.394494 |   0     |   7.07e-18 | ***      | nan                                         |
| circle_pair | WP4  |           7 | evals_to_1e-02 |        2 |       0 |    nan        |   nan        | nan        | nan        | nan        | nan     | nan        | nan      | insufficient data (few runs reached target) |
| circle_pair | WP4  |          10 | final_gap      |       50 |      50 |      0.135841 |     0.531469 |  -0.395629 |  -0.408414 |  -0.378116 |   0.04  |   2.42e-15 | ***      | nan                                         |
| circle_pair | WP4  |          10 | evals_to_1e-02 |        0 |       0 |    nan        |   nan        | nan        | nan        | nan        | nan     | nan        | nan      | insufficient data (few runs reached target) |
| circle_pair | WP4  |          15 | final_gap      |       25 |      25 |      0.290562 |     0.620374 |  -0.329812 |  -0.34738  |  -0.299269 |   0     |   1.42e-09 | ***      | nan                                         |
| circle_pair | WP4  |          15 | evals_to_1e-02 |        0 |       0 |    nan        |   nan        | nan        | nan        | nan        | nan     | nan        | nan      | insufficient data (few runs reached target) |
| circle_pair | WP4  |          20 | final_gap      |       25 |      25 |      0.387672 |     0.65923  |  -0.271558 |  -0.326394 |  -0.237726 |   0.006 |   2.29e-09 | ***      | nan                                         |
| circle_pair | WP4  |          20 | evals_to_1e-02 |        0 |       0 |    nan        |   nan        | nan        | nan        | nan        | nan     | nan        | nan      | insufficient data (few runs reached target) |
| coordinate  | WP4  |           7 | final_gap      |       50 |      50 |      0.051832 |     0.451508 |  -0.399675 |  -0.425479 |  -0.379452 |   0     |   7.07e-18 | ***      | nan                                         |
| coordinate  | WP4  |           7 | evals_to_1e-02 |        2 |       0 |    nan        |   nan        | nan        | nan        | nan        | nan     | nan        | nan      | insufficient data (few runs reached target) |
| coordinate  | WP4  |          10 | final_gap      |       50 |      50 |      0.135841 |     0.531503 |  -0.395662 |  -0.419453 |  -0.373661 |   0.036 |   1.24e-15 | ***      | nan                                         |
| coordinate  | WP4  |          10 | evals_to_1e-02 |        0 |       0 |    nan        |   nan        | nan        | nan        | nan        | nan     | nan        | nan      | insufficient data (few runs reached target) |
| coordinate  | WP4  |          15 | final_gap      |       25 |      25 |      0.290562 |     0.607986 |  -0.317424 |  -0.337455 |  -0.26733  |   0     |   1.42e-09 | ***      | nan                                         |
| coordinate  | WP4  |          15 | evals_to_1e-02 |        0 |       0 |    nan        |   nan        | nan        | nan        | nan        | nan     | nan        | nan      | insufficient data (few runs reached target) |
| coordinate  | WP4  |          20 | final_gap      |       25 |      25 |      0.387672 |     0.668251 |  -0.280579 |  -0.329391 |  -0.251904 |   0.002 |   1.6e-09  | ***      | nan                                         |
| coordinate  | WP4  |          20 | evals_to_1e-02 |        0 |       0 |    nan        |   nan        | nan        | nan        | nan        | nan     | nan        | nan      | insufficient data (few runs reached target) |