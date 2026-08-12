<script lang="ts">
  import { onMount } from 'svelte';
  import {
    Button,
    PageIntro,
    Panel,
    Surface
  } from 'giadaware-ui-components/studio';
  import {
    desktopBridge,
    type CurrentContract,
    type LottoBridge
  } from './lib/bridge';

  let bridge: LottoBridge | null = null;
  let current: CurrentContract | null = null;
  let loading = true;
  let errorMessage = '';

  function digitSet(values: number[]): string {
    return values.length ? `{${values.join(',')}}` : '—';
  }

  function probability(value: number | undefined): string {
    return value === undefined ? '—' : `${(value * 100).toFixed(2)}%`;
  }

  async function refreshCurrent(): Promise<void> {
    if (!bridge) return;

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

  async function connect(): Promise<void> {
    try {
      bridge = await desktopBridge();
      await refreshCurrent();
    } catch (error) {
      loading = false;
      errorMessage = error instanceof Error ? error.message : String(error);
    }
  }

  onMount(() => {
    void connect();
  });
</script>

<main class="app-shell">
  <Surface>
    <div class="page-heading">
      <div>
        <p class="eyebrow">Lotto digit coverage dynamics</p>
        <h1>Research dashboard</h1>
      </div>
      <Button onclick={() => void refreshCurrent()} disabled={!bridge || loading}>
        {loading ? 'Caricamento…' : 'Aggiorna'}
      </Button>
    </div>

    <PageIntro>
      Interfaccia locale di ricerca descrittiva. Nessuna raccomandazione di gioco:
      stato, probabilità teoriche e verifiche successive restano concetti separati.
    </PageIntro>

    {#if errorMessage}
      <div class="error" role="alert">{errorMessage}</div>
    {:else if loading}
      <p aria-live="polite">Connessione al core Python e caricamento del report corrente…</p>
    {:else if current}
      <div class="dashboard-grid">
        <Panel title="Target di analisi">
          <dl class="metric-list">
            <div>
              <dt>Concorso</dt>
              <dd>{current.target.draw_number}</dd>
            </div>
            <div>
              <dt>Data</dt>
              <dd>{current.target.draw_date}</dd>
            </div>
            <div>
              <dt>Contratto</dt>
              <dd>{current.schema} v{current.schema_version}</dd>
            </div>
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
                  <dd>{digitSet(state.most_present_digits)}</dd>
                </div>
                <div>
                  <dt>Mancanti</dt>
                  <dd>{digitSet(state.missing_digits)}</dd>
                </div>
                <div>
                  <dt>Cicli completi</dt>
                  <dd>{state.completed_cycles}</dd>
                </div>
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

      <Panel title="Validazione successiva — fuori dal calcolo">
        {#if current.next_draw_validation.length === 0}
          <p class="muted">Nessuna estrazione successiva presente nel database.</p>
        {:else}
          <p>
            Sono disponibili {current.next_draw_validation.length} risultati di ruota della
            successiva estrazione. Questa sezione è deliberatamente separata: i dati non
            partecipano allo stato o alle classifiche mostrati sopra.
          </p>
        {/if}
      </Panel>
    {/if}
  </Surface>
</main>
