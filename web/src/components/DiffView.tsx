function lineClass(line: string): string {
  if (line.startsWith('+++') || line.startsWith('---')) return 'diff__line--file'
  if (line.startsWith('@@')) return 'diff__line--hunk'
  if (line.startsWith('+')) return 'diff__line--add'
  if (line.startsWith('-')) return 'diff__line--del'
  return 'diff__line--ctx'
}

export function DiffView({ patch }: { patch: string }) {
  if (!patch) return <p className="muted">No changes drafted for this page.</p>
  const lines = patch.replace(/\n$/, '').split('\n')
  return (
    <pre className="diff" aria-label="Suggested patch">
      {lines.map((line, i) => (
        <div key={i} className={`diff__line ${lineClass(line)}`}>
          {line}
        </div>
      ))}
    </pre>
  )
}
