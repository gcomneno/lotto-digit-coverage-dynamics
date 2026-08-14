<script lang="ts">
  import { onMount } from 'svelte';
  import { Button, PageIntro, Panel } from 'giadaware-ui-components/studio';
  import type { CurrentContract, LottoBridge } from '../lib/bridge';
  import { consensusPresentation } from '../lib/consensus';
  import { formatLottoNumber } from '../lib/occurrences';

  let { bridge }: { bridge: LottoBridge } = $props();

  let current = $state<CurrentContract | null>(null);
  let loading = $state(true);
  let errorMessage = $state('');

  function digitSet(values: number[]): string {
    return values.length ? `{${values.join(',')}}` : '—';
  }

  function digitAria(values: number[]): string {
    return values.length ? values.join(', ') : 'nessuna cifra';
  }

  function probability(value: number | undefined): string {
    return value === undefined ? '—' : `${(value * 100).toFixed(2)}%`;
  }

  async function refresh(): Promise<void> {
    loading = true;
    errorMessage = '';
    const response = await bridge.current();

    if (!response.ok || !response.data) {
      current = null;
      errorMessage = response.error?.message ?? 'Errore sconosciuto dal bridge Python.';
    } else {
      current = response.data;
    }

    loading = false;
  }

  onMount(() => {
    void refresh();
  });
</script>

<div class="page-heading">
  <div>
    <p class="eyebrow">Stato corrente</p>
    <h1>Research dashboard</h1>
  </div>
  <Button onclick={() => void refresh()} disabled={loading}>
    {loading ? 'Caricamento…' : 'Aggiorna'}
  </Button>
</div>

<PageIntro>
  Quadro descrittivo dello stato osservato. Le probabilità riportate appartengono
  al modello dichiarato; non sono raccomandazioni di gioco. La validazione con
  l'estrazione successiva è separata dal calcolo ex ante.
</PageIntro>

{#if errorMessage}
  <div class="error" role="alert">{errorMessage}</div>
{:else if loading}
  <p aria-live="polite">Caricamento del report corrente dal core Python…</p>
{:else if current}
  <div class="dashboard-grid">
    <Panel title="Target di analisi">
      <dl class="metric-list">
        <div><dt>Concorso</dt><dd>{current.target.draw_number}</dd></div>
        <div><dt>Data</dt><dd>{current.target.draw_date}</dd></div>
        <div><dt>Contratto</dt><dd>{current.schema} v{current.schema_version}</dd></div>
      </dl>
    </Panel>

    <Panel title="Anomalie attive">
      <p class="metric-value">{current.anomalies.active.length}</p>
      <p class="muted">
        {current.anomalies.transition_count} transizioni valide nella storia analizzata.
      </p>
    </Panel>
  </div>

  <Panel title="Stato corrente per ruota">
    <div class="wheel-grid">
      {#each current.states as state (state.wheel)}
        <article class="wheel-card">
          <div class="wheel-card__heading">
            <strong>{state.wheel}</strong>
            <span>età {state.draws_in_cycle}</span>
          </div>
          <dl class="compact-list">
            <div>
              <dt>TOP</dt>
              <dd class="digit-strip digit-strip--top" aria-label={`TOP: ${digitAria(state.most_present_digits)}`}>
                {#if state.most_present_digits.length}
                  {#each state.most_present_digits as digit (digit)}
                    <span class="digit-chip">{digit}</span>
                  {/each}
                {:else}
                  <span class="digit-empty">—</span>
                {/if}
              </dd>
            </div>
            <div>
              <dt>Mancanti</dt>
              <dd class="digit-strip digit-strip--missing" aria-label={`Mancanti: ${digitAria(state.missing_digits)}`}>
                {#if state.missing_digits.length}
                  {#each state.missing_digits as digit (digit)}
                    <span class="digit-chip">{digit}</span>
                  {/each}
                {:else}
                  <span class="digit-empty">—</span>
                {/if}
              </dd>
            </div>
            <div><dt>Cicli completi</dt><dd>{state.completed_cycles}</dd></div>
          </dl>
        </article>
      {/each}
    </div>
  </Panel>

  <Panel title="Classifica Markov">
    <section class="responsive-table" aria-label="Classifica Markov">
      <table>
        <thead>
          <tr>
            <th scope="col">Pos.</th>
            <th scope="col">Ruota</th>
            <th scope="col">Entro 1</th>
            <th scope="col">Entro 3</th>
            <th scope="col">Attesa residua</th>
          </tr>
        </thead>
        <tbody>
          {#each current.markov_ranking as row (row.wheel)}
            <tr>
              <td>{row.position}</td>
              <th scope="row">{row.wheel}</th>
              <td>{probability(row.completion_within['1'])}</td>
              <td>{probability(row.completion_within['3'])}</td>
              <td>{row.expected_remaining_draws.toFixed(3)}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </section>
  </Panel>

  <Panel title="Coverage-hits — classifica descrittiva">
    <PageIntro>
      L'evento conta le cifre mancanti intercettate sulla stessa ruota. Il successo
      dell'evento sulle cifre non equivale a una vincita su numeri Lotto completi.
    </PageIntro>
    <section class="responsive-table" aria-label="Classifica coverage-hits">
      <table>
        <thead>
          <tr>
            <th scope="col">Pos.</th>
            <th scope="col">Ruota</th>
            <th scope="col">TOP</th>
            <th scope="col">Mancanti</th>
            <th scope="col">P evento</th>
            <th scope="col">Stima95-</th>
            <th scope="col">Casi storici</th>
          </tr>
        </thead>
        <tbody>
          {#each current.coverage_hit_ranking as row (row.wheel)}
            <tr>
              <td>{row.position}</td>
              <th scope="row">{row.wheel}</th>
              <td>{digitSet(row.most_present_digits)}</td>
              <td>{digitSet(row.missing_digits)}</td>
              <td>{probability(row.current_event_probability)}</td>
              <td>{probability(row.conservative_probability)}</td>
              <td>{row.historical.cases}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </section>
  </Panel>

  <div class="dashboard-grid">
    <Panel title="Consensus trasversale">
      <PageIntro>
        Descrittivo: per ogni cifra conta in quante ruote con ciclo attivo è ancora
        assente e in quante è tra le più presenti nel ciclo corrente. Non combina
        cifre in numeri e non rappresenta un vantaggio sul gioco.
      </PageIntro>
      <section class="responsive-table" aria-label="Consensus trasversale">
        <table>
          <thead>
            <tr>
              <th scope="col">Cifra</th>
              <th scope="col">Ruote in deficit</th>
              <th scope="col">Ruote in predominanza</th>
              <th scope="col">Dove in deficit</th>
              <th scope="col">Dove predominante</th>
            </tr>
          </thead>
          <tbody>
            {#each current.consensus as row (row.digit)}
              {@const presentation = consensusPresentation(row)}
              <tr>
                <th scope="row">{row.digit}</th>
                <td>{row.missing_count}</td>
                <td>{row.top_count}</td>
                <td>{presentation.missingWheels}</td>
                <td>{presentation.topWheels}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </section>
    </Panel>

    <Panel title="Dettaglio anomalie attive">
      {#if current.anomalies.active.length === 0}
        <p class="muted">Nessuna anomalia attiva al cutoff.</p>
      {:else}
        <ul class="plain-list">
          {#each current.anomalies.active as anomaly (anomaly.signature)}
            <li>
              <strong>{anomaly.category} · {anomaly.wheel}</strong><br />
              <span>{anomaly.source_state} → {anomaly.target_state}</span><br />
              <span class="muted">P={probability(anomaly.conditional_probability)} · {anomaly.severity}</span>
            </li>
          {/each}
        </ul>
      {/if}
    </Panel>
  </div>

  <Panel title="Validazione successiva — fuori dal calcolo">
    {#if current.next_draw_validation.length === 0}
      <p class="muted">Nessuna estrazione successiva presente nel database.</p>
    {:else}
      <p>
        La sezione seguente usa soltanto dati successivi al target per verifica ex post.
        Questi numeri non partecipano allo stato, alle probabilità o alle classifiche sopra.
      </p>
      <div class="validation-grid">
        {#each current.next_draw_validation as draw (draw.wheel)}
          <div class="validation-row">
            <strong>{draw.wheel}</strong>
            <span>{draw.numbers.map(formatLottoNumber).join(' ')}</span>
          </div>
        {/each}
      </div>
    {/if}
  </Panel>
{/if}
