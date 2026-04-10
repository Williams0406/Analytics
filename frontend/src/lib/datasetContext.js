'use client'

function buildFieldRoleLookup(tableSummary) {
  const roleLookup = {}

  const pushRole = (columnName, role) => {
    if (!columnName) return
    roleLookup[columnName] = roleLookup[columnName] || []
    if (!roleLookup[columnName].includes(role)) {
      roleLookup[columnName].push(role)
    }
  }

  pushRole(tableSummary?.primary_key_name, 'primary_key')
  pushRole(tableSummary?.focus_measure_column, 'measure')
  pushRole(tableSummary?.focus_date_column, 'date')

  ;(tableSummary?.top_dimensions || []).slice(0, 2).forEach((dimension) => {
    pushRole(dimension?.column, 'dimension')
  })

  ;(tableSummary?.quality_watchlist || []).slice(0, 3).forEach((issue) => {
    pushRole(issue?.column, 'quality')
  })

  return roleLookup
}

export function buildDatasetContextFromImport(datasetImport) {
  if (!datasetImport) return null

  const summary = datasetImport.analysis_summary || {}
  const tableSummaries = Object.fromEntries(
    (summary.tables || []).map((tableSummary) => [tableSummary.name, tableSummary])
  )

  const tables = [...(datasetImport.tables || [])]
    .sort((left, right) => (right.row_count || 0) - (left.row_count || 0))
    .map((table) => {
      const tableSummary = tableSummaries[table.name] || {}
      const fieldRoleLookup = buildFieldRoleLookup(tableSummary)

      return {
        name: table.name,
        source_file: table.source_file,
        row_count: table.row_count,
        column_count: table.column_count,
        primary_key_name: table.primary_key_name,
        focus_measure_column: tableSummary.focus_measure_column || '',
        focus_date_column: tableSummary.focus_date_column || '',
        analysis_modes: tableSummary.analysis_modes || [],
        recommended_analyses: (tableSummary.recommended_analyses || []).slice(0, 3),
        field_highlights: (tableSummary.field_highlights || []).slice(0, 4),
        fields: (table.columns || []).map((column) => ({
          name: column.name,
          inferred_type: column.inferred_type,
          is_nullable: column.is_nullable,
          is_primary_key: column.is_primary_key,
          uniqueness_ratio: column.uniqueness_ratio,
          null_count: column.null_count,
          sample_values: (column.sample_values || []).slice(0, 2),
          roles: fieldRoleLookup[column.name] || [],
        })),
      }
    })

  return {
    dataset_name: datasetImport.name,
    summary: summary.overview || {},
    tables,
    relationships: summary.relationships || datasetImport.relationships || [],
  }
}
