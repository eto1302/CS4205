# First TA Meeting — 13/05/2026

## Discussion points

- We can code in Python and have someone run the original algorithm in C to compare performance.
- The assignment focuses on improving an evolutionary algorithm, not on comparing different EAs.
- The optimization problem appears to be a scattering of points where the minimum distance between points is maximized.
- A useful benchmark problem is placing circles in a square.
- Contact the TA by email in case of issues.
- The code was not yet up and running.
- We still need to decide whether to use Python or C, and which algorithm we will optimize.
- Using the C algorithm gives us an existing skeleton and a paper written by Peter for this assignment.
- Writing the algorithm in Python means the whole group will understand the code.
- The TA provided an evolutionary strategy–based algorithm that we can optimize for the assignment.
- TA contact will be through meetings on request for questions, updates, or feedback.
- The TA should be added to the GitHub repository.

## Proposed plan

### Main decisions
- Choose between a Evolutionary Strategy Python or Enhanced Gaussian EDA C algorithm.
- Deadline for this decision: Sunday 24 May.

### Immediate tasks
- Get the code up and running.
- Deadline: Wednesday 20 May.
- Finish the goals of Week 1 by Sunday 24 May.

### Week 1 goals
- Implement the fitness function.
- Benchmark the standard EA.
- Produce graphs or tables with results.
- Define hypotheses about the improvements we want to implement.
- Schedule a meeting with the TA if needed.

## Assignment goal

Improve the baseline performance of an evolutionary algorithm and report the findings.

## Step 0: Baseline selection

Choose one baseline EA to improve.

### Option 1
- AMaLGaM provided by the course in C.

### Option 2
- Use the provided code from the TA: Evolutionary Strategies, can be found on the folder Algorithms (ES)
- Use other starting code from the web for a different real-valued evolutionary algorithm, such as:
  - Differential Evolution
  - Particle Swarm Optimization
  - Classic Evolution Strategies
  - CMA-ES

**Important:** stick with one EA and try different improvements for that same EA. The assignment is not about trying multiple EAs and comparing them.

## Timeline

### Week 1 — Measure baseline
1. Implement the fitness function.
2. Benchmark the standard EA.
3. Produce graphs or tables with results.
4. Define hypotheses about the improvements to make.

### Week 2
1. Implement the proposed changes from Week 1.
2. Run preliminary experiments.
3. Check whether the changes improve performance.

### Week 3
1. Analyse the preliminary experiments from Week 2.
2. Set up final experiments to benchmark the modified EA.
3. Formulate a hypothesis for why the changes should work.
4. Test the final experiment and confirm or reject the hypothesis.
5. Perform statistical analysis.
6. Produce final plots.

### Week 4
1. Prepare the presentation.
2. Final submission.
3. Rehearsal.