<script lang="ts">
  import { onMount } from 'svelte';
  import { Button, Surface } from 'giadaware-ui-components/studio';
  import CurrentDashboard from './components/CurrentDashboard.svelte';
  import OccurrenceExplorer from './components/OccurrenceExplorer.svelte';
  import ResearchReports from './components/ResearchReports.svelte';
  import { desktopBridge, type LottoBridge } from './lib/bridge';

  type View = 'dashboard' | 'occurrences' | 'research';

  let bridge = $state<LottoBridge | null>(null);
  let activeView = $state<View>('dashboard');
  let connecting = $state(true);
  let errorMessage = $state('');

  async function connect(): Promise<void> {
    try {
      bridge = await desktopBridge();
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : String(error);
    } finally {
      connecting = false;
    }
  }

  onMount(() => {
    void connect();
  });
</script>

<main class="app-shell">
  <Surface>
    <nav class="primary-nav" aria-label="Sezioni ricerca">
      <Button
        variant={activeView === 'dashboard' ? 'primary' : 'secondary'}
        onclick={() => (activeView = 'dashboard')}
        aria-current={activeView === 'dashboard' ? 'page' : undefined}
      >
        Dashboard
      </Button>
      <Button
        variant={activeView === 'occurrences' ? 'primary' : 'secondary'}
        onclick={() => (activeView = 'occurrences')}
        aria-current={activeView === 'occurrences' ? 'page' : undefined}
      >
        Occorrenze
      </Button>
      <Button
        variant={activeView === 'research' ? 'primary' : 'secondary'}
        onclick={() => (activeView = 'research')}
        aria-current={activeView === 'research' ? 'page' : undefined}
      >
        Ricerca
      </Button>
    </nav>

    {#if errorMessage}
      <div class="error" role="alert">{errorMessage}</div>
    {:else if connecting}
      <p aria-live="polite">Connessione al core Python…</p>
    {:else if bridge}
      {#if activeView === 'dashboard'}
        <CurrentDashboard {bridge} />
      {:else if activeView === 'occurrences'}
        <OccurrenceExplorer {bridge} />
      {:else}
        <ResearchReports {bridge} />
      {/if}
    {/if}
  </Surface>
</main>
