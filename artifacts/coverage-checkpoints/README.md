# Historical coverage checkpoints

This directory preserves resumable states of the natural digit-coverage
cycles at the end of complete historical years.

The generator derives the checkpoint year dynamically:

```text
checkpoint year = current year - 1
```

The checkpoint date is not assumed to be December 31. It is the actual
date of the final valid draw found in the selected historical archive.

Each wheel state contains:

- the last applied draw and date;
- whether historical synchronization has been reached;
- the number of completed cycles;
- the length and beginning of the currently open cycle;
- covered and missing digits;
- occurrence counts for all ten digits;
- the most frequent digits in the open cycle.

The occurrence vector is necessary to resume current-state analysis
without replaying the complete archive.

Source archives and their SHA-256 checksums are embedded in each JSON
checkpoint. A checkpoint must be regenerated when its historical source
archives or state schema change.

Generate the checkpoint for the current system year:

```bash
./generate_coverage_checkpoint.py
```

Generate a reproducible checkpoint for another reference year:

```bash
./generate_coverage_checkpoint.py --current-year 2027
```

The resulting state can be loaded through
`strategies.coverage_checkpoint.read_checkpoint()` and converted into
mutable accumulators through
`strategies.coverage_checkpoint.states_from_checkpoint()`.

## Draw-number semantics

`latest_draw` and `cycle_start_draw` preserve the draw numbers exposed by
the source archive used to build the checkpoint.

Those numbers are descriptive metadata, not stable historical
identifiers. Annual databases restart numbering each year, partial
consolidated databases number within their own interval, and the overall
historical database uses a global progressive number.

Checkpoint continuity and semantic equivalence therefore use draw dates
plus the complete cycle state. Source-local draw numbers are deliberately
excluded from cross-archive equivalence checks.
