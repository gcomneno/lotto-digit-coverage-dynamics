<script lang="ts">
  import { onMount } from 'svelte';
  import { Button, PageIntro, Panel } from 'giadaware-ui-components/studio';
  import type {
    LottoBridge,
    ResearchCatalogItem,
    ResearchReport
  } from '../lib/bridge';
  import { formatResearchValue } from '../lib/research';

  let { bridge }: { bridge: LottoBridge } = $props();

  let catalog = $state<ResearchCatalogItem[]>([]);
  let report = $state<ResearchReport | null>(null);
  let selectedId = $state('');
  let loadingCatalog = $state(true);
  let loadingReport = $state(false);
  let errorMessage = $state('');

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

    const response = await bridge.researchReport(reportId);
    if (!response.ok || !response.data) {
      errorMessage = response.error?.message ?? 'Report di ricerca non disponibile.';
    } else {
      report = response.data;
    }

    loadingReport = false;
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
  <div class="research-catalog">
    {#each catalog as item (item.id)}
      <article class:selected-research={selectedId === item.id} class="research-card">
        <div>
          <h2>{item.title}</h2>
          <p>{item.summary}</p>
          <p class="muted">{item.interpretation}</p>
        </div>
        <Button
          variant={selectedId === item.id ? 'primary' : 'secondary'}
          disabled={loadingReport}
          onclick={() => void loadReport(item.id)}
        >
          {loadingReport && selectedId === item.id ? 'Calcolo…' : 'Apri report'}
        </Button>
      </article>
    {/each}
  </div>
{/if}

{#if loadingReport}
  <p aria-live="polite">Calcolo del report storico nel core Python…</p>
{:else if report}
  <Panel title={report.title}>
    <PageIntro>{report.interpretation}</PageIntro>
    <p class="muted">Sorgente: {report.source}</p>

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
            {#each table.rows as row, rowIndex (rowIndex)}
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
{/if}
