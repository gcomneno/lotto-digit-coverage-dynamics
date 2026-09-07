import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const source = readFileSync(
  new URL('../components/ResearchReports.svelte', import.meta.url),
  'utf8',
);

describe('ResearchReports localization boundary', () => {
  it('keeps locale out of researchCatalog and researchReport requests', () => {
    expect(source).toContain('const response = await bridge.researchCatalog();');
    expect(source).toContain('const response = await bridge.researchReport(reportId);');
    expect(source).not.toContain('bridge.researchCatalog(locale');
    expect(source).not.toContain('bridge.researchReport(reportId, locale');
  });

  it('preserves twins filtering semantics and report id checks', () => {
    expect(source).toContain("if (report?.id !== 'twins') return table.rows;");
    expect(source).toContain('condition: conditionFilter || undefined');
    expect(source).toContain('twin: twinFilter ? Number(twinFilter) : null');
    expect(source).toContain('candidatesOnly');
    expect(source).toContain("{#if report.id === 'twins'}");
  });

  it('renders dynamic research prose and structured labels directly from the report', () => {
    for (const expression of [
      'item.id',
      'item.title',
      'item.summary',
      'item.interpretation',
      'report.id',
      'report.title',
      'report.interpretation',
      'report.source',
      'metric.label',
      'metric.value',
      'metric.format',
      'table.title',
      'column.key',
      'column.label',
      'column.format',
      'report.notes',
      'note',
    ]) {
      expect(source).toContain(expression);
    }
  });

  it('localizes only the static candidate marker while preserving candidate truth semantics', () => {
    expect(source).toContain("valueFormat === 'candidate' && value === true");
    expect(source).toContain("text('research.candidate', locale)");
    expect(source).toContain("column.format === 'candidate' && row[column.key] === true");
  });
});
