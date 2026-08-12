# Architecture boundaries

Related issues: #9, #10, #11, #17.

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

A future `interfaces/gui/` package may be added only after the architecture gate described in #9 is satisfied. When graphical work starts, GIADA UI is the canonical reusable design-system/component foundation rather than a visual reference or optional inspiration.

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

## Future GUI and GIADA UI

If a graphical interface is introduced, this repository must not grow an independent general-purpose design system.

GIADA UI is the primary source for reusable graphical concerns:

- components and interaction patterns;
- design tokens, theming and visual language;
- accessibility and keyboard-navigation conventions;
- reusable table, filtering, navigation and feedback primitives where available.

This repository owns Lotto-specific composition, view-model mapping and research workflows. When a reusable graphical primitive is missing, adding or evolving it in GIADA UI should be considered before introducing a project-local duplicate.

GUI framework selection is therefore constrained by GIADA UI reuse. A stack that prevents substantial GIADA UI reuse requires explicit architectural justification and must not silently create a parallel UI foundation.

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
- `interfaces` may consume application services and presentation helpers; composition code may wire infrastructure implementations into those services;
- future GUI code may depend on GIADA UI at the interface layer, but domain/application code must remain independent of both GIADA UI and any selected GUI framework.

## Result and value-object placement

Use the narrowest stable layer:

- mathematical/domain identity or invariant -> `domain`;
- immutable result describing one application use case -> `application`;
- SQLite/archive transport representation -> `infrastructure` only and do not leak it across the boundary;
- colors, labels, column widths, localized strings or widgets -> `interfaces`.

Stable JSON-serializable contracts are intentionally deferred to #14 after the first interactive use cases have been migrated.

## Data-access boundary

Issue #11 establishes the first explicit persistence contract for draw-based analysis:

- `lotto_digit_coverage.domain.draws.DrawSnapshot` is the canonical immutable draw value; two-digit formatting and leading-zero digit splitting are domain primitives because their semantics do not depend on storage;
- `lotto_digit_coverage.application.repositories.DrawRepository` defines the read operations required by analysis code and returns only structured domain values;
- `lotto_digit_coverage.infrastructure.sqlite_lotto_repository.SQLiteLottoRepository` implements that contract against SQLite;
- analysis code must not execute SQL through a repository connection or receive `sqlite3.Row`, cursors or other SQLite-specific values;
- the SQLite analysis adapter opens databases with `mode=ro`, so read-only use cases cannot mutate an archive accidentally;
- database paths remain constructor inputs rather than CLI- or GUI-specific global assumptions;
- repository failures that describe schema or stored-data invariants are normalized into application-facing repository errors.

The legacy `strategies.lotto_repository` module remains a compatibility shim during migration. `LottoRepository` is an alias for the SQLite adapter, while `DrawSnapshot`, `format_number` and `split_digits` are re-exported from their canonical domain location.

Import/update commands remain separate write-oriented infrastructure paths. Issue #11 does not change their schema or write semantics.

## Incremental migration

Legacy top-level scripts and the `strategies/` package remain supported during the transition. Compatibility modules are allowed when they preserve existing imports while making the new ownership explicit.

The first concrete move under #10 is the tabular CLI `Column` primitive:

- canonical location: `lotto_digit_coverage.interfaces.cli.table`;
- legacy import: `strategies.cli_table` remains a compatibility shim.

Issue #11 adds the draw repository boundary without requiring a broad migration of all historical tools. Later issues migrate vertical use cases one at a time.

Graphical implementation remains deferred to #17. That issue must preserve the same application/domain boundaries while treating GIADA UI as the canonical reusable UI layer.

## Automated boundary checks

`tests/test_architecture_boundaries.py` enforces the initial dependency rules using Python AST imports. In particular, domain/application code must not acquire direct SQLite, subprocess, argument-parser or GUI dependencies, and forbidden package-layer imports fail the test suite.

`tests/test_sqlite_lotto_repository.py` exercises the concrete read contract against temporary SQLite fixtures, including wheel ordering, chronology across annual draw-number resets, incomplete data, schema errors, leading-zero semantics and read-only enforcement.

The checks are deliberately small and explicit. They protect architecture direction without introducing a third-party dependency-injection, ORM or architecture framework.
