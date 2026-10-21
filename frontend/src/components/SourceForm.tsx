import { useState } from 'react'
import type { FormEvent } from 'react'
import { errorMessage } from './errorMessage'
import type { SourceInput } from '../types/entity'

export function SourceForm({
  initial,
  submitLabel,
  onSubmit,
  onCancel,
}: {
  initial: SourceInput
  submitLabel: string
  onSubmit: (body: SourceInput) => Promise<void>
  onCancel: () => void
}) {
  const [name, setName] = useState(initial.name)
  const [shelfmark, setShelfmark] = useState(initial.shelfmark ?? '')
  const [url, setUrl] = useState(initial.url ?? '')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setSaving(true)
    setError(null)
    try {
      await onSubmit({
        name: name.trim(),
        shelfmark: shelfmark.trim() || null,
        url: url.trim() || null,
      })
    } catch (err) {
      setError(errorMessage(err))
      setSaving(false)
    }
  }

  return (
    <form onSubmit={submit} className="space-y-3">
      <label className="block text-sm text-gray-700">
        Name
        <input
          type="text"
          required
          value={name}
          onChange={(event) => setName(event.target.value)}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm"
        />
      </label>
      <label className="block text-sm text-gray-700">
        Shelfmark (optional)
        <input
          type="text"
          value={shelfmark}
          onChange={(event) => setShelfmark(event.target.value)}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm"
        />
      </label>
      <label className="block text-sm text-gray-700">
        Link (optional)
        <input
          type="url"
          value={url}
          onChange={(event) => setUrl(event.target.value)}
          placeholder="https://"
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm"
        />
      </label>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="flex justify-end gap-2">
        <button
          type="button"
          onClick={onCancel}
          className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={saving || !name.trim()}
          className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {submitLabel}
        </button>
      </div>
    </form>
  )
}
