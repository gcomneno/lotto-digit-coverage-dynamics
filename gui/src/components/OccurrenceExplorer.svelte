<script lang="ts">
  import { onMount } from 'svelte';
  import {
    Button,
    FieldLabel,
    PageIntro,
    Panel
  } from 'giadaware-ui-components/studio';
  import type {
    LottoBridge,
    OccurrenceContract,
    OccurrenceGroup
  } from '../lib/bridge';
  import {
    availableWheels,
    drawNumbersForWheel,
    formatLottoNumber,
    referencePosition,
    wheelSummary
  } from '../lib/occurrences';

  let { bridge }: { bridge: LottoBridge } = $props();

  let report = $state<OccurrenceContract | null>(null);
  let loading = $state(true);
  let errorMessage = $state('');
  let groupSize = $state(10);
  let requestedDraw = $state<number | undefined>(undefined);
  let selectedWheel = $state('');

  async function load(): Promise<void> {
    if (!Number.isInteger(groupSize) || groupSize <= 0) {
      errorMessage = 'La dimensione del gruppo deve essere un intero positivo.';
      return;
    }
    if (
      requestedDraw !== undefined &&
      (!Number.isInteger(requestedDraw) || requestedDraw <= 0)
    ) {
      errorMessage = 'Il cutoff deve essere un numero di concorso positivo.';
      return;
    }

    loading = true;
    errorMessage = '';
    const response = await bridge.occurrenceGroups(
      groupSize,
      requestedDraw ?? null
    );

    if (!response.ok || !response.data) {
      report = null;
      errorMessage = response.error?.message ?? 'Errore sconosciuto dal bridge Python.';
    } else {
      report = response.data;
      const wheels = availableWheels(report);
      if (!selectedWheel || !wheels.includes(selectedWheel)) {
        selectedWheel = wheels[0] ?? '';
      }
    }

    loading = false;
  }

  function groupTitle(group: OccurrenceGroup): string {
    return `Rif. ${group.reference.draw_number} · analisi ${group.range.newest.draw_number}–${group.range.oldest.draw_number}`;
  }

  onMount(() => {
    void load();
  });
</script>

<div class="page-heading">
  <div>
    <p class="eyebrow">Database</p>
    <h1>Occurrence explorer</h1>
  </div>
</div>

<PageIntro>
  Esplorazione retrospettiva per gruppi. Ogni gruppo ha una propria estrazione
  di riferimento che identifica i cinque numeri sotto osservazione ma è esclusa
  dai conteggi. Le estrazioni successive nel pannello sono quelle storiche
  effettivamente analizzate sulla stessa ruota. I colori identificano le cinque
  posizioni del riferimento e non rappresentano intensità o probabilità.
</PageIntro>

<Panel title="Controlli">
  <form class="control-grid" onsubmit={(event) => { event.preventDefault(); void load(); }}>
    <label class="field-stack">
      <FieldLabel
        label="Dimensione gruppo"
        hint="Numero di estrazioni storiche conteggiate; il riferimento è aggiuntivo ed escluso."
      />
      <input type="number" min="1" step="1" bind:value={groupSize} />
    </label>

    <label class="field-stack">
      <FieldLabel
        label="Cutoff"
        hint="Concorso da usare come primo riferimento; vuoto = ultimo completo."
        optional={true}
        optionalLabel="opzionale"
      />
      <input type="number" min="1" step="1" bind:value={requestedDraw} />
    </label>

    {#if report}
      <label class="field-stack">
        <FieldLabel
          label="Ruota"
          hint="Il filtro è solo grafico: il report contiene tutte le ruote."
        />
        <select bind:value={selectedWheel}>
          {#each availableWheels(report) as wheel}
            <option value={wheel}>{wheel}</option>
          {/each}
        </select>
      </label>
    {/if}

    <div class="control-actions">
      <Button type="submit" disabled={loading}>
        {loading ? 'Caricamento…' : 'Applica'}
      </Button>
    </div>
  </form>
</Panel>

{#if errorMessage}
  <div class="error" role="alert">{errorMessage}</div>
{:else if loading}
  <p aria-live="polite">Costruzione dei gruppi dal database read-only…</p>
{:else if report}
  <div class="dashboard-grid">
    <Panel title="Riferimento globale">
      <dl class="metric-list">
        <div><dt>Concorso</dt><dd>{report.reference.draw_number}</dd></div>
        <div><dt>Data</dt><dd>{report.reference.draw_date}</dd></div>
        <div><dt>Selezione</dt><dd>{report.reference.kind}</dd></div>
      </dl>
    </Panel>

    <Panel title="Configurazione">
      <dl class="metric-list">
        <div><dt>Estratti conteggiati</dt><dd>{report.group_size}</dd></div>
        <div><dt>Gruppi</dt><dd>{report.groups.length}</dd></div>
        <div><dt>Ruota visibile</dt><dd>{selectedWheel || '—'}</dd></div>
      </dl>
    </Panel>
  </div>

  {#if selectedWheel}
    {#each report.groups as group (`${group.reference.draw_date}-${group.reference.draw_number}`)}
      {@const summary = wheelSummary(group, selectedWheel)}
      <Panel title={groupTitle(group)}>
        <div class="group-meta">
          <span>
            riferimento <strong>{group.reference.draw_number}</strong>
            del {group.reference.draw_date} — escluso dai conteggi
          </span>
          <span>{group.actual_size} estrazioni conteggiate</span>
        </div>

        {#if summary}
          <div class="reference-strip" aria-label={`Riferimenti ${selectedWheel}`}>
            {#each summary.reference_numbers as number, index}
              <div class={`reference-slot position-${index}`}>
                <span class="reference-number">{formatLottoNumber(number)}</span>
                <span class="reference-count">{summary.occurrence_counts[index]} occ.</span>
              </div>
            {/each}
          </div>

          <section
            class="responsive-table"
            aria-label={`${groupTitle(group)} — ${selectedWheel}`}
          >
            <table class="occurrence-table">
              <thead>
                <tr>
                  <th scope="col">Uso</th>
                  <th scope="col">Concorso</th>
                  <th scope="col">Data</th>
                  <th scope="col" colspan="5">{selectedWheel}</th>
                </tr>
              </thead>
              <tbody>
                {@const referenceNumbers = drawNumbersForWheel(group.reference, selectedWheel)}
                <tr>
                  <td><strong>Rif.</strong></td>
                  <th scope="row">{group.reference.draw_number}</th>
                  <td>{group.reference.draw_date}</td>
                  {#if referenceNumbers}
                    {#each referenceNumbers as number}
                      {@const position = referencePosition(number, summary.reference_numbers)}
                      <td>
                        <span
                          class:occurrence-hit={position !== null}
                          class:position-0={position === 0}
                          class:position-1={position === 1}
                          class:position-2={position === 2}
                          class:position-3={position === 3}
                          class:position-4={position === 4}
                        >
                          {formatLottoNumber(number)}
                        </span>
                      </td>
                    {/each}
                  {:else}
                    <td colspan="5">—</td>
                  {/if}
                </tr>
                {#each group.draws as draw (`${draw.draw_date}-${draw.draw_number}`)}
                  {@const numbers = drawNumbersForWheel(draw, selectedWheel)}
                  <tr>
                    <td>Conta</td>
                    <th scope="row">{draw.draw_number}</th>
                    <td>{draw.draw_date}</td>
                    {#if numbers}
                      {#each numbers as number}
                        {@const position = referencePosition(number, summary.reference_numbers)}
                        <td>
                          <span
                            class:occurrence-hit={position !== null}
                            class:position-0={position === 0}
                            class:position-1={position === 1}
                            class:position-2={position === 2}
                            class:position-3={position === 3}
                            class:position-4={position === 4}
                          >
                            {formatLottoNumber(number)}
                          </span>
                        </td>
                      {/each}
                    {:else}
                      <td colspan="5">—</td>
                    {/if}
                  </tr>
                {/each}
              </tbody>
            </table>
          </section>
        {:else}
          <p class="muted">Ruota non presente nel gruppo.</p>
        {/if}
      </Panel>
    {/each}
  {/if}
{/if}
