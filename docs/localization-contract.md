# Localization contract

This document defines the repository-specific localization boundary for issue #51.

## Canonical language

English (`en`) is the single canonical presentation language.

The initial supported locale identifiers are:

- `en` — canonical English;
- `it` — derived Italian presentation.

Locale selection is an interface/presentation concern. Domain and application
services remain locale-independent.

## Semantic invariance

Changing locale must not change:

- structured result values or machine-readable field names;
- report IDs, schema IDs or enum-like identifiers consumed structurally;
- draw numbers, dates, Lotto numbers or wheel-selection semantics;
- ordering, filtering or limits;
- validation outcomes;
- repository inputs, SQL or read/write policy;
- mutations or authorization;
- exit status for the same underlying operation.

CLI and GUI use the same locale identifiers and fallback rules even though their
presentation implementations are separate adapters.

## Static presentation

Normal UI and CLI strings use deterministic catalogs/resources. Runtime LLM
translation is not permitted for ordinary static strings.

Examples include:

- navigation and buttons;
- form labels and hints;
- loading and error messages;
- ARIA labels;
- panel and section headings;
- CLI headings, table headers, help text and explanatory prose.

The English catalog is authoritative. Derived locale catalogs may contain only
presentation-equivalent text.

### Fallback

If a requested locale is unsupported, presentation resolves to canonical
English and exposes fallback evidence.

If a derived catalog lacks a key, that key resolves to canonical English and
exposes fallback evidence.

A key missing from the canonical English catalog is a programmer/configuration
error rather than a translation fallback.

This keeps fallback deterministic and prevents a translation failure from
changing application behavior.

## Dynamic human-readable presentation

GUI research payloads contain presentation prose produced by the Python GUI
adapter, including report titles, summaries, interpretations, metric labels,
table titles, column labels and notes.

These fields are not domain results, but they are also not ordinary static
Svelte strings. They are canonicalized in English and pass through the
provider-independent `DynamicPresentationTranslator` boundary.

The concrete product adapter uses the GiadaWare AI semantic translation
capability. Provider details remain outside domain/application semantics and the
static catalog path never invokes the dynamic translator.

A dynamic translator may translate eligible canonical English prose only. It
must not summarize, enrich, correct, infer or alter the underlying domain data.
On translation failure, presentation remains canonical English and exposes
fallback metadata.

## Documentation localization

Repository documentation follows the separate
[`documentation-localization-policy.md`](documentation-localization-policy.md).

English documentation is authoritative. `README.it.md` and `docs/it/` are
retained as derived Italian presentation and may temporarily lag. If a
translated document conflicts with its English counterpart, English controls.

The September 2026 audit selected **KEEP** for the existing Italian tree:
bulk regeneration and consolidation were rejected because neither provides a
demonstrated semantic or maintenance advantage for this migration.

## Never translate

The following remain language-neutral authoritative or structured data:

- report and schema identifiers;
- machine-readable keys;
- numbers, probabilities, counts and rankings;
- Lotto draw data;
- database paths and repository/query semantics;
- validation rules and error conditions;
- internal values used programmatically.

Human-readable labels describing those values may be localized; the values
and identifiers themselves may not.

## Completed repository audit

The migration established that:

- `README.md` and English documents under `docs/` are the authoritative
  documentation source;
- `README.it.md` and `docs/it/` are derived Italian presentation governed by the
  documentation localization policy;
- static Svelte GUI and CLI presentation use deterministic EN/IT catalogs;
- dynamic research human-readable fields are canonical English and use the
  provider-independent GiadaWare AI translation boundary;
- application/domain computation remains locale-independent;
- CLI/GUI language selection is presentation-only and preserves structured
  results, validation and exit semantics.

## Migration sequence

1. **Foundation** — canonical locale contract, deterministic catalogs, fallback,
   semantic-isolation tests and this document. **Completed.**
2. **CLI migration** — equivalent language selection and localized renderer,
   help and error presentation. **Completed.**
3. **GUI static migration** — language selector and deterministic catalog-backed
   Svelte presentation. **Completed.**
4. **Dynamic presentation** — canonical English research prose and
   provider-independent GiadaWare AI translation. **Completed.**
5. **Documentation policy** — English authority, Italian derived status,
   maintenance/synchronization rules and KEEP decision. **Completed.**

## Design rule

> Maintain one authoritative meaning. Translate its presentation, not its semantics.
