<script lang="ts">
  import { onMount } from 'svelte';
  import { Button, PageIntro, Panel } from 'giadaware-ui-components/studio';
  import type {
    LottoBridge,
    PresentationMetadata,
    ResearchCatalogItem,
    ResearchReport,
    ResearchTable
  } from '../lib/bridge';
  import { text, type Locale } from '../lib/localization';
  import {
    filterResearchRows,
    formatResearchValue,
    uniqueResearchValues
  } from '../lib/research';

  let { bridge, locale }: { bridge: LottoBridge; locale: Locale } = $props();

  let catalog = $state<ResearchCatalogItem[]>([]);
  let report = $state<ResearchReport | null>(null);
  let selectedId = $state('');
  let loadingCatalog = $state(true);
  let loadingReport = $state(false);
  let errorMessage = $state('');
  let conditionFilter = $state('');
  let twinFilter = $state('');
  let candidatesOnly = $state(false);
  let catalogPresentation = $state<PresentationMetadata | null>(null);
  let reportPresentation = $state<PresentationMetadata | null>(null);
  let fallbackPresentation = $derived(
    reportPresentation?.fell_back
      ? reportPresentation
      : catalogPresentation?.fell_back
        ? catalogPresentation
        : null
  );

  async function loadCatalog(): Promise<void> {
    loadingCatalog = true;
    errorMessage = '';
    catalogPresentation = null;
    const response = await bridge.researchCatalog(locale);

    if (!response.ok || !response.data) {
      catalog = [];
      errorMessage = response.error?.message ?? text('research.catalog_unavailable', locale);
    } else {
      catalog = response.data.reports;
      catalogPresentation = response.presentation ?? null;
    }

    loadingCatalog = false;
  }

  async function loadReport(reportId: string): Promise<void> {
    selectedId = reportId;
    loadingReport = true;
    errorMessage = '';
    report = null;
    reportPresentation = null;
    conditionFilter = '';
    twinFilter = '';
    candidatesOnly = false;

    const response = await bridge.researchReport(reportId, locale);
    if (!response.ok || !response.data) {
      errorMessage = response.error?.message ?? text('research.report_unavailable', locale);
    } else {
      report = response.data;
      reportPresentation = response.presentation ?? null;
    }

    loadingReport = false;
  }

  function visibleRows(table: ResearchTable) {
    if (report?.id !== 'twins') return table.rows;
    return filterResearchRows(table.rows, {
      condition: conditionFilter || undefined,
      twin: twinFilter ? Number(twinFilter) : null,
      candidatesOnly
    });
  }

  function conditions(table: ResearchTable) {
    return uniqueResearchValues(table.rows, 'condition');
  }

  function twins(table: ResearchTable) {
    return uniqueResearchValues(table.rows, 'twin');
  }

  function displayResearchValue(value: string | number | boolean | null, valueFormat: string): string {
    if (valueFormat === 'candidate' && value === true) {
      return text('research.candidate', locale);
    }
    return formatResearchValue(value, valueFormat);
  }

  onMount(() => {
    void loadCatalog();
  });
</script>

<div class="page-heading">
  <div>
    <p class="eyebrow">{text('research.eyebrow', locale)}</p>
    <h1>{text('research.title', locale)}</h1>
  </div>
</div>

<PageIntro>{text('research.intro', locale)}</PageIntro>

{#if errorMessage}
  <div class="error" role="alert">{errorMessage}</div>
{/if}

{#if fallbackPresentation}
  <p class="muted" role="status">
    <code>{fallbackPresentation.requested_locale} → {fallbackPresentation.resolved_locale} · {fallbackPresentation.fallback_reason}</code>
  </p>
{/if}

{#if loadingCatalog}
  <p aria-live="polite">{text('research.loading_catalog', locale)}</p>
{:else}
  <div class="research-layout">
    <aside class="research-sidebar" aria-label={text('research.catalog_label', locale)}>
      <h2>{text('research.catalog', locale)}</h2>
      <div class="research-catalog">
        {#each catalog as item (item.id)}
          <article class:selected-research={selectedId === item.id} class="research-card">
            <div>
              <h3>{item.title}</h3>
              <p>{item.summary}</p>
              <p class="muted research-kind">{item.interpretation}</p>
            </div>
            <Button
              variant={selectedId === item.id ? 'primary' : 'secondary'}
              disabled={loadingReport}
              onclick={() => void loadReport(item.id)}
            >
              {loadingReport && selectedId === item.id
                ? text('research.calculating', locale)
                : selectedId === item.id
                  ? text('research.recalculate', locale)
                  : text('research.open', locale)}
            </Button>
          </article>
        {/each}
      </div>
    </aside>

    <section class="research-workspace" aria-live="polite">
      {#if loadingReport}
        <div class="research-placeholder">
          <strong>{text('research.calculation_in_progress', locale)}</strong>
          <span>{text('research.calculation_core', locale)}</span>
        </div>
      {:else if report}
        <Panel title={report.title}>
          <PageIntro>{report.interpretation}</PageIntro>
          <p class="source-line">{text('research.source', locale)}: <code>{report.source}</code></p>

          <div class="research-metrics">
            {#each report.metrics as metric (`${metric.label}-${metric.format}`)}
              <div class="research-metric">
                <span>{metric.label}</span>
                <strong>{displayResearchValue(metric.value, metric.format)}</strong>
              </div>
            {/each}
          </div>
        </Panel>

        {#each report.tables as table (table.title)}
          <Panel title={table.title}>
            {#if report.id === 'twins'}
              <div class="research-filters" aria-label={text('research.twins_filters', locale)}>
                <label class="field-stack">
                  <span class="field-label">{text('research.condition', locale)}</span>
                  <select bind:value={conditionFilter}>
                    <option value="">{text('research.all_feminine', locale)}</option>
                    {#each conditions(table) as condition}
                      <option value={String(condition)}>{condition}</option>
                    {/each}
                  </select>
                </label>

                <label class="field-stack">
                  <span class="field-label">{text('research.twin', locale)}</span>
                  <select bind:value={twinFilter}>
                    <option value="">{text('research.all_masculine', locale)}</option>
                    {#each twins(table) as twin}
                      <option value={String(twin)}>{formatResearchValue(twin, 'lotto-number')}</option>
                    {/each}
                  </select>
                </label>

                <label class="checkbox-field">
                  <input type="checkbox" bind:checked={candidatesOnly} />
                  <span>{text('research.candidates_only', locale)}</span>
                </label>

                <p class="filter-count">
                  {visibleRows(table).length} {text('research.rows_shown_out_of', locale)} {table.rows.length}
                </p>
              </div>
            {/if}

            <section class="responsive-table" aria-label={table.title}>
              <table>
                <thead>
                  <tr>
                    {#each table.columns as column (column.key)}
                      <th scope="col">{column.label}</th>
                    {/each}
                  </tr>
                </thead>
                <tbody>
                  {#each visibleRows(table) as row, rowIndex (rowIndex)}
                    <tr>
                      {#each table.columns as column, columnIndex (column.key)}
                        {#if columnIndex === 0}
                          <th scope="row">
                            {displayResearchValue(row[column.key] ?? null, column.format)}
                          </th>
                        {:else}
                          <td class:candidate-cell={column.format === 'candidate' && row[column.key] === true}>
                            {displayResearchValue(row[column.key] ?? null, column.format)}
                          </td>
                        {/if}
                      {/each}
                    </tr>
                  {/each}
                </tbody>
              </table>
            </section>

            {#if visibleRows(table).length === 0}
              <p class="empty-state">{text('research.no_filtered_rows', locale)}</p>
            {/if}
          </Panel>
        {/each}

        {#if report.notes.length}
          <Panel title={text('research.interpretation_limits', locale)}>
            <ul class="plain-list">
              {#each report.notes as note}
                <li>{note}</li>
              {/each}
            </ul>
          </Panel>
        {/if}
      {:else}
        <div class="research-placeholder">
          <strong>{text('research.choose_report', locale)}</strong>
          <span>{text('research.on_demand', locale)}</span>
        </div>
      {/if}
    </section>
  </div>
{/if}
