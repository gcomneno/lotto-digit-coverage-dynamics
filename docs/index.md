
Documentation
Project overview

Lotto Digit Coverage Dynamics studies the accumulation of decimal digits across
successive Italian Lotto draws.

The project separates three questions that are often confused:

Does digit coverage become nearly complete after a few draws?
Does an individually delayed digit become more likely to appear?
Can the current coverage state quantify how close the cycle is to
completion?

The answers found so far are:

yes, as a combinatorial phenomenon;
no replicable evidence;
yes, through an exact Markov model.
Documents
Foundations
Research question
Mathematical model
Methodology
Glossary
Evidence
Validation results
Historical walk-forward replay
Earlier research findings
Operations
Live prequential protocol
Reproducibility
Limitations
Terminology

A cycle starts with no covered digits and ends when all digits from 0 to
9 have appeared at least once on the same wheel.

The state of a cycle is represented by the digits still missing.

Examples:

{9}
{3,9}
{0,1,7,9}

The empty set {} is the absorbing completed state.
