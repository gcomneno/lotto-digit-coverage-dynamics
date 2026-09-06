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

Some GUI payloads currently contain presentation prose produced by the Python
GUI adapter, notably research report titles, summaries, interpretations, metric
labels, table titles, column labels and notes.

These fields are not domain results, but they are also not ordinary static
Svelte strings. They belong behind a distinct provider-independent translation
boundary.

The interface contract is represented by `DynamicPresentationTranslator`.
Concrete GiadaWare AI integration is intentionally deferred to a later issue.
The static catalog path must never invoke that translator.

A dynamic translator may translate eligible canonical English prose only. It
must not summarize, enrich, correct, infer or alter the underlying domain data.
On translation failure, presentation must remain canonical English.

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

## Current repository audit

At the start of the migration:

- `README.md` and English documents under `docs/` already establish an
  English-first documentation shape;
- `README.it.md` and `docs/it/` are existing Italian counterparts and remain in
  place until a later documentation-policy verification;
- Svelte GUI surfaces contain extensive hard-coded Italian presentation and
  several mixed Italian/English headings;
- CLI renderers contain extensive hard-coded Italian presentation;
- application/domain computation is already substantially separated from
  renderers, which is the architectural boundary this migration preserves;
- GUI research view models currently emit dynamic human-readable Italian
  presentation fields and require a later dedicated migration.

## Migration sequence

1. **Foundation** — canonical locale contract, deterministic catalogs, fallback,
   semantic-isolation tests and this document.
2. **CLI migration** — add equivalent language selection and migrate renderer,
   help and error presentation incrementally.
3. **GUI static migration** — add a language selector and deterministic
   catalog-backed Svelte presentation.
4. **Dynamic presentation** — canonicalize eligible research presentation prose
   in English and add provider-independent GiadaWare AI translation only where
   justified.
5. **Documentation policy** — verify how derived documentation translations are
   maintained before deleting, regenerating or otherwise consolidating existing
   Italian counterparts.

## Design rule

> Maintain one authoritative meaning. Translate its presentation, not its semantics.
