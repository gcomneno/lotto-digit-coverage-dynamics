<script lang="ts">
  import { onMount } from 'svelte';
  import { Button, Surface } from 'giadaware-ui-components/studio';
  import CurrentDashboard from './components/CurrentDashboard.svelte';
  import OccurrenceExplorer from './components/OccurrenceExplorer.svelte';
  import ResearchReports from './components/ResearchReports.svelte';
  import { desktopBridge, type LottoBridge } from './lib/bridge';
  import {
    CANONICAL_LOCALE,
    SUPPORTED_LOCALES,
    text,
    type Locale,
  } from './lib/localization';

  type View = 'dashboard' | 'occurrences' | 'research';

  let bridge = $state<LottoBridge | null>(null);
  let activeView = $state<View>('dashboard');
  let locale = $state<Locale>(CANONICAL_LOCALE);
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
    <div class="primary-nav">
      <nav aria-label={text('app.nav_label', locale)}>
        <Button
          variant={activeView === 'dashboard' ? 'primary' : 'secondary'}
          onclick={() => (activeView = 'dashboard')}
          aria-current={activeView === 'dashboard' ? 'page' : undefined}
        >
          {text('app.nav.dashboard', locale)}
        </Button>
        <Button
          variant={activeView === 'occurrences' ? 'primary' : 'secondary'}
          onclick={() => (activeView = 'occurrences')}
          aria-current={activeView === 'occurrences' ? 'page' : undefined}
        >
          {text('app.nav.occurrences', locale)}
        </Button>
        <Button
          variant={activeView === 'research' ? 'primary' : 'secondary'}
          onclick={() => (activeView = 'research')}
          aria-current={activeView === 'research' ? 'page' : undefined}
        >
          {text('app.nav.research', locale)}
        </Button>
      </nav>

      <label>
        {text('app.language_label', locale)}
        <select bind:value={locale} aria-label={text('app.language_label', locale)}>
          {#each SUPPORTED_LOCALES as supportedLocale}
            <option value={supportedLocale}>{supportedLocale.toUpperCase()}</option>
          {/each}
        </select>
      </label>
    </div>

    {#if errorMessage}
      <div class="error" role="alert">{errorMessage}</div>
    {:else if connecting}
      <p aria-live="polite">{text('app.connecting', locale)}</p>
    {:else if bridge}
      {#if activeView === 'dashboard'}
        <CurrentDashboard {bridge} {locale} />
      {:else if activeView === 'occurrences'}
        <OccurrenceExplorer {bridge} {locale} />
      {:else}
        <ResearchReports {bridge} />
      {/if}
    {/if}
  </Surface>
</main>
