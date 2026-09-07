# Documentation localization policy

This document defines authority and maintenance rules for multilingual repository documentation.

## Authority

English is the single authoritative documentation source.

The authoritative documentation set consists of:

- `README.md`;
- English documents directly under `docs/`;
- machine-readable artifacts and source-code contracts, which remain language-neutral where applicable.

Italian documentation is derived presentation only:

- `README.it.md`;
- documents under `docs/it/`.

Italian text never creates, changes, or overrides repository semantics. If an Italian document differs from its English counterpart, the English document controls.

## Repository decision

The current Italian documentation is **KEEP**.

It is retained because it remains useful public presentation, but it is not treated as a synchronized second source of truth.

The alternatives are rejected for this migration:

- **REGENERATE** — rejected because bulk regeneration would create large review churn and would not by itself prove semantic equivalence;
- **CONSOLIDATE** — rejected because deleting the Italian tree would remove useful public documentation without a demonstrated maintenance benefit.

The existing Italian documents therefore remain derived snapshots governed by this policy.

## Audit finding

The September 2026 audit found real drift between the English and Italian documentation. For example, the English README reflects newer CLI-tool counts and multi-year database-update behavior that the Italian README does not yet fully mirror.

This drift is acceptable only because authority is explicit: Italian documentation is informational derived presentation and may temporarily lag. It must never be used to resolve ambiguity against canonical English.

## Maintenance contract

For every documentation change:

1. author semantic or normative changes in English first;
2. treat the merged English text as the source of truth;
3. if a corresponding Italian document exists and the change is user-facing, update it in the same change when practical;
4. if the Italian counterpart is not updated, do not block the authoritative English change solely to preserve textual parity;
5. never introduce a semantic rule only in Italian;
6. when correcting drift, translate meaning rather than wording mechanically;
7. preserve commands, identifiers, schemas, paths, numbers, and machine-readable values unless the English source itself changes them.

A future automated translation workflow may assist maintenance, but generated translation remains derived and requires repository-level review before publication.

## Synchronization and conflict handling

No byte-for-byte synchronization requirement exists between language variants.

Synchronization means semantic correspondence for the portions intentionally translated. A translation may change phrasing, examples of natural-language prose, or grammar while preserving the same technical meaning.

When a discrepancy is discovered:

- English remains valid and authoritative;
- the Italian document is classified as stale derived presentation;
- the Italian text may be corrected in a focused documentation change;
- application behavior, structured data, and English documentation are never changed merely to match stale Italian wording.

## Scope boundary

This policy concerns repository documentation only.

Runtime static UI/CLI localization remains governed by deterministic catalogs. Dynamic human-readable research presentation remains governed by the provider-independent GiadaWare AI translation boundary. Neither runtime mechanism makes translated documentation authoritative.

## Design rule

> Maintain one authoritative meaning. Translate its presentation, not its semantics.
