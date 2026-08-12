# GUI architecture decision

Related issue: #17.
Architecture gate: #9 / #10–#16 complete.

## Decision

The first graphical interface uses:

- **Svelte 5 + Vite** for the presentation layer;
- **GIADA UI** as the canonical reusable component, token and interaction foundation;
- **pywebview 6.2.1** as the Linux-first desktop host and JavaScript–Python bridge;
- the existing Python `domain`, `application` and `infrastructure` layers as the only source of Lotto calculations.

The GUI is a local/offline adapter. It does not execute CLI commands, parse terminal output or introduce an HTTP application API.

## Why this stack

### GIADA UI reuse

GIADA UI is a Svelte 5 component library. A Svelte frontend can consume its real package exports directly, including Studio components and styles, instead of reproducing them in another toolkit.

During private incubation the dependency is pinned to an exact reviewed Git commit. The packaging path was enabled upstream by `giadaware-ui-components` PR #47; registry publication remains disabled.

Pinned foundation commit:

```text
gcomneno/giadaware-ui-components@1000288190ad1e4869810514edf4bea34c867770
```

Initial reusable primitives:

- `PageIntro` — screen framing and interpretation text;
- `Panel` — research sections and result groups;
- `Surface` — page/screen surfaces;
- `Button` — actions and navigation;
- `AsyncOperationPanel` — asynchronous bridge operations where useful.

A generic research data table is not currently exported by GIADA UI. The occurrence explorer must evaluate that gap upstream before adding any project-local reusable table abstraction. Native semantic HTML may be used for Lotto-specific tabular composition, but a general reusable grid/table component belongs upstream.

## Python bridge

pywebview exposes a JavaScript–Python bridge through `js_api`. The browser-facing adapter returns JSON-compatible dictionaries built from the existing stable application contracts.

Initial bridge calls:

- `get_current(...)` → `lotto.current` schema v1;
- `get_occurrence_groups(...)` → `lotto.occurrence-groups` schema v1;
- `get_capabilities()` → interface metadata only.

Errors cross the interface as a small `{ok, data?, error?}` envelope. Application reports themselves remain unchanged.

The bridge is testable without importing or launching pywebview. pywebview is imported only by the optional desktop launcher, so the CLI and core test suite remain independent from graphical system libraries.

## Desktop host

pywebview is preferred over the alternatives for v1 because its official bridge supports Python↔JavaScript calls without an application HTTP API, while static frontend assets can be served by its built-in local server.

Reference:

- https://pywebview.flowrl.com/guide/interdomain
- https://pywebview.flowrl.com/guide/architecture
- https://pypi.org/project/pywebview/6.2.1/

## Rejected alternatives for v1

### PySide / Qt widgets

It would keep Python integration simple, but it cannot reuse GIADA UI's Svelte components as the primary component layer. That directly conflicts with #17.

### Tauri + Svelte

Tauri would preserve Svelte/GIADA UI reuse, but the existing Python research core would need to be packaged and managed as a sidecar/external binary. Tauri's official sidecar model requires platform-specific target-triple binaries, increasing packaging and maintenance complexity before the research GUI needs it.

Reference:

- https://v2.tauri.app/develop/sidecar/
- https://v2.tauri.app/start/frontend/sveltekit/

Tauri remains a possible future packaging evolution if distribution requirements justify that cost.

### Browser-only local web application

A separate local HTTP API would add a server/security/deployment boundary solely to reach code that already lives in the same local Python process. That is unnecessary for the first offline desktop interface.

## UX scope

### 1. Current dashboard

The first usable screen exposes the existing `lotto.current` contract:

- analysis target/cutoff;
- per-wheel TOP and missing digits;
- Markov ranking and maturity values;
- coverage-hit ranking;
- cross-wheel consensus;
- active anomalies;
- next-draw validation visually separated from the state used for the analysis.

### 2. Occurrence explorer

The second screen consumes `lotto.occurrence-groups`:

- database/reference cutoff;
- configurable group size;
- same-wheel reference numbers;
- positional occurrence counts;
- readable grouped history without terminal-width constraints.

### 3. Research reports

Historical application services completed by #16 are added incrementally after the two primary interactive screens. The GUI must preserve each report's historical/exploratory/held-out interpretation instead of flattening them into a generic "signal" view.

## Scientific UX boundary

Every graphical screen must preserve the repository framing:

- descriptive research tool, not a betting recommender;
- consensus is descriptive and generates no candidate numbers;
- historical lift does not imply altered future draw probabilities;
- next-draw data is validation-only and visually separated from the analysis state;
- twin-number findings remain unsupported unless an independent protocol says otherwise;
- no stakes, payout calculators or automatic betting slips.

## Dependency direction

```text
Svelte + GIADA UI
        |
        v
interfaces/gui (JS bridge + desktop launcher)
        |
        v
application reports / stable serializers
        |
        v
      domain
        ^
        |
infrastructure (read-only SQLite/checkpoints)
```

Neither `domain` nor `application` imports pywebview, Svelte or GIADA UI.

## Testing gate

GUI work must preserve:

- the complete Python suite;
- architecture-boundary tests;
- bridge tests with temporary/in-memory fixtures where possible;
- Svelte type checking;
- frontend unit tests;
- production frontend build;
- explicit tests that the browser adapter consumes structured contracts rather than CLI output.
