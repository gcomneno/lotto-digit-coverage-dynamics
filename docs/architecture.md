# Architecture boundaries

Related issues: #9, #10.

## Purpose

The project is moving incrementally from a script-oriented research layout to a presentation-neutral core that can serve both the existing CLI and a future GUI.

This is an architectural refactor only. Mathematical definitions, statistical protocols, cutoffs, no-look-ahead rules and CLI semantics must not change as a side effect of moving code.

## Target package

```text
lotto_digit_coverage/
├── domain/
├── application/
├── infrastructure/
└── interfaces/
    └── cli/
```

A future `interfaces/gui/` package may be added only after the architecture gate described in #9 is satisfied.

## Responsibilities

### `domain`

Owns pure mathematical/statistical concepts and domain value objects.

Examples include coverage states, transitions, probabilities, anomaly definitions and other rules that can be evaluated without knowing how data are stored or displayed.

The domain must not know about SQLite, filesystem database paths, `argparse`, ANSI colors, `less`, subprocesses or GUI frameworks.

### `application`

Owns use-case orchestration and presentation-neutral report/result objects.

Application services may depend on domain objects and abstract contracts. They must not depend on concrete SQLite adapters or CLI/GUI implementations.

A use case should return structured values; formatting percentages, tables or localized explanatory strings is an interface concern.

### `infrastructure`

Owns concrete adapters for persistence and external resources, such as SQLite repositories, archive sources, checkpoints and report storage.

Infrastructure may implement contracts consumed by the application layer. It must not contain CLI/GUI presentation logic.

### `interfaces`

Owns user-facing adapters.

`interfaces/cli` contains argument handling, ANSI/terminal formatting, paging and other command-line presentation helpers. A future GUI will be another adapter over the same application services, never a parser for CLI output.

## Dependency direction

Allowed direction:

```text
interfaces  --->  application  --->  domain
     |                 ^
     +------ wiring ---|--- infrastructure
```

More explicitly:

- `domain` imports neither `application`, `infrastructure` nor `interfaces`;
- `application` may import `domain` and abstract contracts, but not concrete `infrastructure` or `interfaces`;
- `infrastructure` may depend on domain/application types required to implement contracts, but not on `interfaces`;
- `interfaces` may consume application services and presentation helpers; composition code may wire infrastructure implementations into those services.

## Result and value-object placement

Use the narrowest stable layer:

- mathematical/domain identity or invariant -> `domain`;
- immutable result describing one application use case -> `application`;
- SQLite/archive transport representation -> `infrastructure` only and do not leak it across the boundary;
- colors, labels, column widths, localized strings or widgets -> `interfaces`.

Stable JSON-serializable contracts are intentionally deferred to #14 after the first interactive use cases have been migrated.

## Incremental migration

Legacy top-level scripts and the `strategies/` package remain supported during the transition. Compatibility modules are allowed when they preserve existing imports while making the new ownership explicit.

The first concrete move under #10 is the tabular CLI `Column` primitive:

- canonical location: `lotto_digit_coverage.interfaces.cli.table`;
- legacy import: `strategies.cli_table` remains a compatibility shim.

No broad module move is required by #10. Later issues migrate vertical use cases one at a time.

## Automated boundary checks

`tests/test_architecture_boundaries.py` enforces the initial dependency rules using Python AST imports. In particular, domain/application code must not acquire direct SQLite, subprocess, argument-parser or GUI dependencies, and forbidden package-layer imports fail the test suite.

The checks are deliberately small and explicit. They protect architecture direction without introducing a third-party dependency-injection or architecture framework.
