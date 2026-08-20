/**
 * apps/web/types/version.ts
 * Contratos tipados para el sistema de versionado del modelo y motor cuantitativo.
 */

export interface VersionHistoryItem {
  version: string;
  name: string;
  released_at: string;
  status: 'CURRENT_RECOMMENDED' | 'INTERMEDIATE' | 'LEGACY_DEPRECATED';
  status_label: string;
  description: string;
  ruleset_hash?: string;
  strategy_count?: number;
  changes?: string[];
}

export interface EngineVersionsSummary {
  current_version: string;
  current_name: string;
  pipeline_version: string;
  history: VersionHistoryItem[];
  version_distribution?: Record<string, number>;
}
