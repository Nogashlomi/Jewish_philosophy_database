import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { isAxiosError } from 'axios'
import { BadgeCheck, ExternalLink, Loader2 } from 'lucide-react'
import { useAuth } from '../auth/authContext'
import { entityService } from '../services/entityService'
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

  const submit = (event: FormEvent) => {
    event.preventDefault()
    const trimmedViafId = viafId.trim()
    mutation.mutate({ name: name.trim(), ...(trimmedViafId ? { viaf_id: trimmedViafId } : {}) })
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
                onClick={() => mutation.mutate({ viaf_id: suggestion.viaf_id })}
                className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                Accept
              </button>
            </li>
          ))}
        </ul>
      )}

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
    </div>
  )
}
