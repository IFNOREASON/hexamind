const CATEGORY_COLORS: Record<string, string> = {
  concept: '#60a5fa',
  technology: '#a78bfa',
  framework: '#c084fc',
  language: '#34d399',
  tool: '#fbbf24',
  person: '#f87171',
  organization: '#fb923c',
  event: '#e879f9',
  default: '#94a3b8',
}

export function getCategoryColor(category: string): string {
  return CATEGORY_COLORS[category.toLowerCase()] ?? CATEGORY_COLORS.default
}

export function getConfidenceColor(score: number): string {
  if (score >= 0.8) return '#34d399'
  if (score >= 0.5) return '#fbbf24'
  return '#f87171'
}
