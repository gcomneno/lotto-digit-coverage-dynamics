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
  import { text, type Locale } from '../lib/localization';
  import {
    availableWheels,
    drawNumbersForWheel,
    formatLottoNumber,
    referencePosition,
    wheelSummary
  } from '../lib/occurrences';

  let { bridge, locale }: { bridge: LottoBridge; locale: Locale } = $props();

  let report = $state<OccurrenceContract | null>(null);
  let loading = $state(true);
  let errorMessage = $state('');
  let groupSize = $state(10);
  let occurrenceLimit = $state<number | undefined>(undefined);
  let requestedDraw = $state<number | undefined>(undefined);
  let selectedWheel = $state('');

  async function load(): Promise<void> {
    if (!Number.isInteger(groupSize) || groupSize <= 0) {
      errorMessage = text('occurrence.invalid_group_size', locale);
      return;
    }
    if (
      occurrenceLimit !== undefined &&
      (!Number.isInteger(occurrenceLimit) || occurrenceLimit <= 0)
    ) {
      errorMessage = text('occurrence.invalid_global_limit', locale);
      return;
    }
    if (
      requestedDraw !== undefined &&
      (!Number.isInteger(requestedDraw) || requestedDraw <= 0)
    ) {
      errorMessage = text('occurrence.invalid_cutoff', locale);
      return;
    }

    loading = true;
    errorMessage = '';
    const response = await bridge.occurrenceGroups(
      groupSize,
      requestedDraw ?? null,
      occurrenceLimit ?? null
    );

    if (!response.ok || !response.data) {
      report = null;
      errorMessage = response.error?.message ?? text('occurrence.unknown_bridge_error', locale);
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
    return `${text('occurrence.reference_abbrev', locale)} ${group.reference.draw_number} · ${text('occurrence.analysis', locale)} ${group.range.newest.draw_number}–${group.range.oldest.draw_number}`;
  }

  onMount(() => {
    void load();
  });
</script>

<div class="page-heading">
  <div>
    <p class="eyebrow">{text('occurrence.eyebrow', locale)}</p>
    <h1>{text('occurrence.title', locale)}</h1>
  </div>
</div>

<PageIntro>{text('occurrence.intro', locale)}</PageIntro>

<Panel title={text('occurrence.controls', locale)}>
  <form class="control-grid" onsubmit={(event) => { event.preventDefault(); void load(); }}>
    <label class="field-stack">
      <FieldLabel
        label={text('occurrence.group_size', locale)}
        hint={text('occurrence.group_size_hint', locale)}
      />
      <input type="number" min="1" step="1" bind:value={groupSize} />
    </label>

    <label class="field-stack">
      <FieldLabel
        label={text('occurrence.global_limit', locale)}
        hint={text('occurrence.global_limit_hint', locale)}
        optional={true}
        optionalLabel={text('occurrence.optional', locale)}
      />
      <input type="number" min="1" step="1" bind:value={occurrenceLimit} />
    </label>

    <label class="field-stack">
      <FieldLabel
        label={text('occurrence.cutoff', locale)}
        hint={text('occurrence.cutoff_hint', locale)}
        optional={true}
        optionalLabel={text('occurrence.optional', locale)}
      />
      <input type="number" min="1" step="1" bind:value={requestedDraw} />
    </label>

    {#if report}
      <label class="field-stack">
        <FieldLabel
          label={text('occurrence.wheel', locale)}
          hint={text('occurrence.wheel_hint', locale)}
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
        {loading ? text('occurrence.loading', locale) : text('occurrence.apply', locale)}
      </Button>
    </div>
  </form>
</Panel>

{#if errorMessage}
  <div class="error" role="alert">{errorMessage}</div>
{:else if loading}
  <p aria-live="polite">{text('occurrence.building', locale)}</p>
{:else if report}
  <div class="dashboard-grid">
    <Panel title={text('occurrence.global_reference', locale)}>
      <dl class="metric-list">
        <div><dt>{text('occurrence.draw', locale)}</dt><dd>{report.reference.draw_number}</dd></div>
        <div><dt>{text('occurrence.date', locale)}</dt><dd>{report.reference.draw_date}</dd></div>
        <div><dt>{text('occurrence.selection', locale)}</dt><dd>{report.reference.kind}</dd></div>
      </dl>
    </Panel>

    <Panel title={text('occurrence.configuration', locale)}>
      <dl class="metric-list">
        <div><dt>{text('occurrence.counted_draws', locale)}</dt><dd>{report.group_size}</dd></div>
        <div><dt>{text('occurrence.global_limit', locale)}</dt><dd>{report.occurrence_limit ?? '—'}</dd></div>
        <div><dt>{text('occurrence.examined_draws', locale)}</dt><dd>{report.examined_draw_count}</dd></div>
        <div><dt>{text('occurrence.groups', locale)}</dt><dd>{report.groups.length}</dd></div>
        <div><dt>{text('occurrence.visible_wheel', locale)}</dt><dd>{selectedWheel || '—'}</dd></div>
      </dl>
    </Panel>
  </div>

  {#if selectedWheel}
    {#each report.groups as group (`${group.reference.draw_date}-${group.reference.draw_number}`)}
      {@const summary = wheelSummary(group, selectedWheel)}
      {@const referenceNumbers = drawNumbersForWheel(group.reference, selectedWheel)}
      <Panel title={groupTitle(group)}>
        <div class="group-meta">
          <span>
            {text('occurrence.reference', locale)} <strong>{group.reference.draw_number}</strong>
            · {group.reference.draw_date} — {text('occurrence.excluded_from_counts', locale)}
          </span>
          <span>{group.actual_size} {text('occurrence.draws_counted', locale)}</span>
        </div>

        {#if summary}
          <div class="reference-strip" aria-label={`${text('occurrence.references', locale)} ${selectedWheel}`}>
            {#each summary.reference_numbers as number, index}
              <div class={`reference-slot position-${index}`}>
                <span class="reference-number">{formatLottoNumber(number)}</span>
                <span class="reference-count">{summary.occurrence_counts[index]} {text('occurrence.occurrence_abbrev', locale)}</span>
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
                  <th scope="col">{text('occurrence.use', locale)}</th>
                  <th scope="col">{text('occurrence.draw', locale)}</th>
                  <th scope="col">{text('occurrence.date', locale)}</th>
                  <th scope="col" colspan="5">{selectedWheel}</th>
                  <th scope="col">Σ</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong>{text('occurrence.reference_abbrev', locale)}</strong></td>
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
                  <td>—</td>
                </tr>
                {#each group.draws as draw (`${draw.draw_date}-${draw.draw_number}`)}
                  {@const numbers = drawNumbersForWheel(draw, selectedWheel)}
                  <tr>
                    <td>{text('occurrence.count', locale)}</td>
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
                    <td></td>
                  </tr>
                {/each}
              </tbody>
              <tfoot>
                <tr>
                  <th scope="row" colspan="3">{text('occurrence.total', locale)}</th>
                  {#each summary.occurrence_counts as count}
                    <td><strong>{count}</strong></td>
                  {/each}
                  <td><strong>{summary.total_occurrences}</strong></td>
                </tr>
              </tfoot>
            </table>
          </section>
        {:else}
          <p class="muted">{text('occurrence.wheel_missing', locale)}</p>
        {/if}
      </Panel>
    {/each}
  {/if}

  <Panel title={text('occurrence.global_total', locale)}>
    <dl class="metric-list">
      <div>
        <dt>{text('occurrence.sum_of_sums', locale)}</dt>
        <dd>{report.grand_total_occurrences}</dd>
      </div>
    </dl>
  </Panel>
{/if}
