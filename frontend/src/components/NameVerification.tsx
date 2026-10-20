import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { isAxiosError } from 'axios'
import { BadgeCheck, ExternalLink, Loader2, X } from 'lucide-react'
import { useAuth } from '../auth/authContext'
import { entityService } from '../services/entityService'
import { ConfirmDialog } from './ConfirmDialog'
import type { PersonDetail, VerifyNameRequest } from '../types/entity'

const viafUrl = (viafId: string) => `https://viaf.org/viaf/${viafId}`

function errorMessage(error: unknown): string {
  if (isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) return detail.map((d) => d.msg).join(', ')
    return error.message
  }
  return String(error)
}

export function NameVerification({ person }: { person: PersonDetail }) {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [name, setName] = useState(person.label)
  const [viafId, setViafId] = useState('')
  const [altNames, setAltNames] = useState(() => [...new Set([...person.alt_names, person.label])])
  const [newAltName, setNewAltName] = useState('')
  const [pendingBody, setPendingBody] = useState<VerifyNameRequest | null>(null)

  const mutation = useMutation({
    mutationFn: (body: VerifyNameRequest) => entityService.verifyPersonName(person.id, body),
    onSuccess: (updated) => {
      queryClient.setQueryData(['person', person.id], updated)
      queryClient.invalidateQueries({ queryKey: ['persons'] })
    },
  })

  if (person.name_verified) {
    return (
      <div className="flex items-center gap-2 text-sm text-green-700">
        <BadgeCheck className="h-4 w-4" aria-hidden="true" />
        Verified name
        {person.viaf_id && (
          <a
            href={viafUrl(person.viaf_id)}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 text-indigo-600 hover:underline"
          >
            VIAF {person.viaf_id}
            <ExternalLink className="h-3 w-3" aria-hidden="true" />
          </a>
        )}
      </div>
    )
  }

  if (!user) return null

  const verify = (body: VerifyNameRequest, newName: string) => {
    const request = { ...body, alt_names: altNames }
    if (newName !== person.label && !altNames.includes(person.label)) setPendingBody(request)
    else mutation.mutate(request)
  }

  const confirmPending = () => {
    if (pendingBody) mutation.mutate(pendingBody)
    setPendingBody(null)
  }

  const submit = (event: FormEvent) => {
    event.preventDefault()
    const trimmedViafId = viafId.trim()
    verify({ name: name.trim(), ...(trimmedViafId ? { viaf_id: trimmedViafId } : {}) }, name.trim())
  }

  const addAltName = () => {
    const trimmed = newAltName.trim()
    if (trimmed && !altNames.includes(trimmed)) setAltNames([...altNames, trimmed])
    setNewAltName('')
  }

  return (
    <div className="rounded-md border border-amber-200 bg-amber-50 p-4 space-y-4">
      <h3 className="font-medium text-gray-900">Verify name</h3>

      {person.viaf_suggestions.length > 0 && (
        <ul className="space-y-2">
          {person.viaf_suggestions.map((suggestion) => (
            <li
              key={suggestion.viaf_id}
              className="flex flex-wrap items-center justify-between gap-2 rounded bg-white px-3 py-2 border border-gray-200"
            >
              <div>
                <div className="font-medium text-gray-900">{suggestion.name}</div>
                <a
                  href={viafUrl(suggestion.viaf_id)}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 text-xs text-indigo-600 hover:underline"
                >
                  {suggestion.viaf_name} · VIAF {suggestion.viaf_id}
                  <ExternalLink className="h-3 w-3" aria-hidden="true" />
                </a>
              </div>
              <button
                type="button"
                disabled={mutation.isPending}
                onClick={() => verify({ viaf_id: suggestion.viaf_id }, suggestion.name)}
                className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                Accept
              </button>
            </li>
          ))}
        </ul>
      )}

      <div className="space-y-2">
        <div className="text-sm text-gray-700">Alternative names</div>
        <div className="flex flex-wrap gap-2">
          {altNames.map((altName) => (
            <span
              key={altName}
              className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-sm ${altName === person.label ? 'border-indigo-300 bg-indigo-50 text-indigo-800' : 'border-gray-300 bg-white text-gray-800'}`}
              title={altName === person.label ? 'Original name' : undefined}
            >
              {altName}
              <button
                type="button"
                onClick={() => setAltNames(altNames.filter((n) => n !== altName))}
                aria-label={`Remove ${altName}`}
                className="text-gray-400 hover:text-red-600"
              >
                <X className="h-3.5 w-3.5" aria-hidden="true" />
              </button>
            </span>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={newAltName}
            onChange={(event) => setNewAltName(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                event.preventDefault()
                addAltName()
              }
            }}
            placeholder="Add alternative name"
            className="flex-1 rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          />
          <button
            type="button"
            onClick={addAltName}
            disabled={!newAltName.trim()}
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            Add
          </button>
        </div>
      </div>

      <form onSubmit={submit} className="flex flex-wrap items-end gap-2">
        <label className="flex-1 min-w-[12rem] text-sm text-gray-700">
          Normalized name
          <input
            type="text"
            required
            value={name}
            onChange={(event) => setName(event.target.value)}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          />
        </label>
        <label className="w-40 text-sm text-gray-700">
          VIAF id (optional)
          <input
            type="text"
            inputMode="numeric"
            pattern="\d+"
            value={viafId}
            onChange={(event) => setViafId(event.target.value)}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          />
        </label>
        <button
          type="submit"
          disabled={mutation.isPending || !name.trim()}
          className="rounded-md border border-indigo-600 px-3 py-1.5 text-sm font-medium text-indigo-700 hover:bg-indigo-50 disabled:opacity-50"
        >
          Submit
        </button>
      </form>

      {mutation.isPending && <Loader2 className="h-4 w-4 animate-spin text-indigo-500" />}
      {mutation.isError && <p className="text-sm text-red-600">{errorMessage(mutation.error)}</p>}

      <ConfirmDialog
        open={pendingBody !== null}
        title="Keep the original name?"
        confirmLabel="Save without it"
        cancelLabel="Go back"
        onConfirm={confirmPending}
        onCancel={() => setPendingBody(null)}
      >
        <p>
          <span className="font-medium text-gray-900">{person.label}</span> was removed from the
          alternative names.
        </p>
        <p>
          Keeping the original spelling helps us recognize this person when it shows up again in
          other sources, imports or automatic matching. Without it, those matches may be missed.
        </p>
      </ConfirmDialog>
    </div>
  )
}
