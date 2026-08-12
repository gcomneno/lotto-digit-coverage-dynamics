<script lang="ts">
  import { onMount } from 'svelte';
  import { Button, PageIntro, Panel } from 'giadaware-ui-components/studio';
  import type {
    LottoBridge,
    ResearchCatalogItem,
    ResearchReport,
    ResearchTable
  } from '../lib/bridge';
  import {
    filterResearchRows,
    formatResearchValue,
    uniqueResearchValues
  } from '../lib/research';

  let { bridge }: { bridge: LottoBridge } = $props();

  let catalog = $state<ResearchCatalogItem[]>([]);
  let report = $state<ResearchReport | null>(null);
  let selectedId = $state('');
  let loadingCatalog = $state(true);
  let loadingReport = $state(false);
  let errorMessage = $state('');
  let conditionFilter = $state('');
  let twinFilter = $state('');
  let candidatesOnly = $state(false);

  async function loadCatalog(): Promise<void> {
    loadingCatalog = true;
    errorMessage = '';
    const response = await bridge.researchCatalog();

    if (!response.ok || !response.data) {
      catalog = [];
      errorMessage = response.error?.message ?? 'Catalogo ricerca non disponibile.';
    } else {
      catalog = response.data.reports;
    }

    loadingCatalog = false;
  }

  async function loadReport(reportId: string): Promise<void> {
    selectedId = reportId;
    loadingReport = true;
    errorMessage = '';
    report = null;
    conditionFilter = '';
    twinFilter = '';
    candidatesOnly = false;

    const response = await bridge.researchReport(reportId);
    if (!response.ok || !response.data) {
      errorMessage = response.error?.message ?? 'Report di ricerca non disponibile.';
    } else {
      report = response.data;
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

  onMount(() => {
    void loadCatalog();
  });
</script>

<div class="page-heading">
  <div>
    <p class="eyebrow">Analisi storiche</p>
    <h1>Research reports</h1>
  </div>
</div>

<PageIntro>
  I report vengono calcolati on demand dagli stessi application service usati dal
  laboratorio. La GUI visualizza risultati strutturati e non esegue o interpreta
  output CLI. Ogni scheda mantiene la propria natura descrittiva o esplorativa.
</PageIntro>

{#if errorMessage}
  <div class="error" role="alert">{errorMessage}</div>
{/if}

{#if loadingCatalog}
  <p aria-live="polite">Caricamento del catalogo di ricerca…</p>
{:else}
  <div class="research-layout">
    <aside class="research-sidebar" aria-label="Catalogo report">
      <h2>Catalogo</h2>
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
              {loadingReport && selectedId === item.id ? 'Calcolo…' : selectedId === item.id ? 'Ricalcola' : 'Apri'}
            </Button>
          </article>
        {/each}
      </div>
    </aside>

    <section class="research-workspace" aria-live="polite">
      {#if loadingReport}
        <div class="research-placeholder">
          <strong>Calcolo in corso…</strong>
          <span>Il report viene costruito nel core Python.</span>
        </div>
      {:else if report}
        <Panel title={report.title}>
          <PageIntro>{report.interpretation}</PageIntro>
          <p class="source-line">Sorgente: <code>{report.source}</code></p>

          <div class="research-metrics">
            {#each report.metrics as metric (`${metric.label}-${metric.format}`)}
              <div class="research-metric">
                <span>{metric.label}</span>
                <strong>{formatResearchValue(metric.value, metric.format)}</strong>
              </div>
            {/each}
          </div>
        </Panel>

        {#each report.tables as table (table.title)}
          <Panel title={table.title}>
            {#if report.id === 'twins'}
              <div class="research-filters" aria-label="Filtri tabella gemelli">
                <label class="field-stack">
                  <span class="field-label">Condizione</span>
                  <select bind:value={conditionFilter}>
                    <option value="">Tutte</option>
                    {#each conditions(table) as condition}
                      <option value={String(condition)}>{condition}</option>
                    {/each}
                  </select>
                </label>

                <label class="field-stack">
                  <span class="field-label">Gemello</span>
                  <select bind:value={twinFilter}>
                    <option value="">Tutti</option>
                    {#each twins(table) as twin}
                      <option value={String(twin)}>{formatResearchValue(twin, 'lotto-number')}</option>
                    {/each}
                  </select>
                </label>

                <label class="checkbox-field">
                  <input type="checkbox" bind:checked={candidatesOnly} />
                  <span>Solo candidati esplorativi</span>
                </label>

                <p class="filter-count">
                  {visibleRows(table).length} righe visualizzate su {table.rows.length}
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
                            {formatResearchValue(row[column.key] ?? null, column.format)}
                          </th>
                        {:else}
                          <td class:candidate-cell={column.format === 'candidate' && row[column.key] === true}>
                            {formatResearchValue(row[column.key] ?? null, column.format)}
                          </td>
                        {/if}
                      {/each}
                    </tr>
                  {/each}
                </tbody>
              </table>
            </section>

            {#if visibleRows(table).length === 0}
              <p class="empty-state">Nessuna riga corrisponde ai filtri selezionati.</p>
            {/if}
          </Panel>
        {/each}

        {#if report.notes.length}
          <Panel title="Interpretazione e limiti">
            <ul class="plain-list">
              {#each report.notes as note}
                <li>{note}</li>
              {/each}
            </ul>
          </Panel>
        {/if}
      {:else}
        <div class="research-placeholder">
          <strong>Scegli un report dal catalogo</strong>
          <span>Il calcolo parte soltanto quando lo richiedi.</span>
        </div>
      {/if}
    </section>
  </div>
{/if}
