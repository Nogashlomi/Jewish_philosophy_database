import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Loader2, Pencil, Plus, Trash2 } from 'lucide-react'
import { useAuth } from '../auth/authContext'
import { entityService } from '../services/entityService'
import { errorMessage } from './errorMessage'
import { EntityCombobox } from './EntityCombobox'
import type { EntityOption } from './EntityCombobox'
import { SourceForm } from './SourceForm'
import { CONNECTION_TYPES } from '../types/entity'
import type {
  ConnectionType,
  PersonConnection,
  PersonConnectionInput,
  PersonDetail,
  PlaceList,
  Source,
} from '../types/entity'

interface Draft {
  key: number
  type: ConnectionType
  place: EntityOption | null
  start: string
  end: string
  estimated: boolean
  description: string
  source: EntityOption | null
}

type Creating = { key: number; kind: 'place' | 'source'; name: string } | null

let nextKey = 0

const toDraft = (c: PersonConnection): Draft => ({
  key: nextKey++,
  type: c.type,
  place: c.place_id ? { id: c.place_id, label: c.place_label ?? c.place_id } : null,
  start: c.start?.toString() ?? '',
  end: c.end?.toString() ?? '',
  estimated: c.estimated,
  description: c.description ?? '',
  source: c.source_id ? { id: c.source_id, label: c.source_label ?? c.source_id } : null,
})

const emptyDraft = (): Draft => ({
  key: nextKey++,
  type: 'residence',
  place: null,
  start: '',
  end: '',
  estimated: false,
  description: '',
  source: null,
})

const parseYear = (value: string): number | null | undefined => {
  const trimmed = value.trim()
  if (!trimmed) return null
  return /^-?\d+$/.test(trimmed) ? Number(trimmed) : undefined
}

function draftError(draft: Draft): string | null {
  const start = parseYear(draft.start)
  const end = parseYear(draft.end)
  if (start === undefined || end === undefined)
    return 'Years must be whole numbers (negative for BCE)'
  if (!draft.place && start === null) return 'Choose a place, a start year, or both'
  if (end !== null && start === null) return 'An end year requires a start year'
  if (end !== null && start !== null && end < start) return 'End year must not be before start year'
  return null
}

function toInput(draft: Draft): PersonConnectionInput {
  const start = parseYear(draft.start) ?? null
  return {
    type: draft.type,
    place_id: draft.place?.id ?? null,
    start,
    end: parseYear(draft.end) ?? null,
    estimated: start !== null && draft.estimated,
    description: draft.description.trim() || null,
    source_id: draft.source?.id ?? null,
  }
}

function PlaceForm({
  initialName,
  onSubmit,
  onCancel,
}: {
  initialName: string
  onSubmit: (place: PlaceList) => void
  onCancel: () => void
}) {
  const [name, setName] = useState(initialName)
  const [lat, setLat] = useState('')
  const [long, setLong] = useState('')
  const mutation = useMutation({
    mutationFn: () =>
      entityService.createPlace({ name: name.trim(), lat: Number(lat), long: Number(long) }),
    onSuccess: onSubmit,
  })

  const submit = (event: FormEvent) => {
    event.preventDefault()
    mutation.mutate()
  }

  return (
    <form onSubmit={submit} className="space-y-3">
      <label className="block text-sm text-gray-700">
        Place name
        <input
          type="text"
          required
          value={name}
          onChange={(event) => setName(event.target.value)}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm"
        />
      </label>
      <div className="flex gap-2">
        <label className="flex-1 text-sm text-gray-700">
          Latitude
          <input
            type="number"
            required
            step="any"
            min={-90}
            max={90}
            value={lat}
            onChange={(event) => setLat(event.target.value)}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          />
        </label>
        <label className="flex-1 text-sm text-gray-700">
          Longitude
          <input
            type="number"
            required
            step="any"
            min={-180}
            max={180}
            value={long}
            onChange={(event) => setLong(event.target.value)}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          />
        </label>
      </div>
      {mutation.isError && <p className="text-sm text-red-600">{errorMessage(mutation.error)}</p>}
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
          disabled={mutation.isPending || !name.trim() || !lat || !long}
          className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          Create place
        </button>
      </div>
    </form>
  )
}

function DraftRow({
  draft,
  places,
  sources,
  creating,
  onChange,
  onRemove,
  onCreate,
  onCreated,
  onCancelCreate,
}: {
  draft: Draft
  places: EntityOption[]
  sources: EntityOption[]
  creating: Creating
  onChange: (draft: Draft) => void
  onRemove: () => void
  onCreate: (kind: 'place' | 'source', name: string) => void
  onCreated: (kind: 'place' | 'source', option: EntityOption) => void
  onCancelCreate: () => void
}) {
  const error = draftError(draft)
  const hasStart = draft.start.trim() !== ''

  return (
    <li className="rounded-md border border-gray-200 bg-white p-4 space-y-3">
      <div className="flex flex-wrap items-end gap-3">
        <label className="w-36 text-sm text-gray-700">
          Type
          <select
            value={draft.type}
            onChange={(event) => onChange({ ...draft, type: event.target.value as ConnectionType })}
            className="mt-1 block w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm capitalize"
          >
            {CONNECTION_TYPES.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </label>
        <div className="flex-1 min-w-[12rem] text-sm text-gray-700">
          Place
          <div className="mt-1">
            <EntityCombobox
              value={draft.place}
              options={places}
              placeholder="No place"
              createLabel="New place"
              onChange={(place) => onChange({ ...draft, place })}
              onCreate={(name) => onCreate('place', name)}
            />
          </div>
        </div>
        <button
          type="button"
          onClick={onRemove}
          aria-label="Remove row"
          className="p-1.5 text-gray-400 hover:text-red-600"
        >
          <Trash2 className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>

      {creating?.kind === 'place' && (
        <div className="rounded-md border border-indigo-200 bg-indigo-50 p-3">
          <PlaceForm
            initialName={creating.name}
            onSubmit={(place) => onCreated('place', { id: place.id, label: place.label })}
            onCancel={onCancelCreate}
          />
        </div>
      )}

      <div className="flex flex-wrap items-end gap-3">
        <label className="w-28 text-sm text-gray-700">
          From year
          <input
            type="text"
            inputMode="numeric"
            value={draft.start}
            onChange={(event) => onChange({ ...draft, start: event.target.value })}
            placeholder="e.g. 1138"
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          />
        </label>
        <label className="w-28 text-sm text-gray-700">
          Until year
          <input
            type="text"
            inputMode="numeric"
            value={draft.end}
            onChange={(event) => onChange({ ...draft, end: event.target.value })}
            placeholder="optional"
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          />
        </label>
        <label className="flex items-center gap-2 pb-2 text-sm text-gray-700">
          <input
            type="checkbox"
            checked={draft.estimated}
            disabled={!hasStart}
            onChange={(event) => onChange({ ...draft, estimated: event.target.checked })}
          />
          Estimate
        </label>
      </div>

      <label className="block text-sm text-gray-700">
        Description
        <textarea
          rows={2}
          value={draft.description}
          onChange={(event) => onChange({ ...draft, description: event.target.value })}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm"
        />
      </label>

      <div className="text-sm text-gray-700">
        Source
        <div className="mt-1">
          <EntityCombobox
            value={draft.source}
            options={sources}
            placeholder="No source"
            createLabel="New source"
            onChange={(source) => onChange({ ...draft, source })}
            onCreate={(name) => onCreate('source', name)}
          />
        </div>
      </div>

      {creating?.kind === 'source' && (
        <div className="rounded-md border border-indigo-200 bg-indigo-50 p-3">
          <SourceForm
            initial={{ name: creating.name }}
            submitLabel="Create source"
            onSubmit={async (body) => {
              const source = await entityService.createSource(body)
              onCreated('source', { id: source.id, label: source.label })
            }}
            onCancel={onCancelCreate}
          />
        </div>
      )}

      {error && <p className="text-sm text-red-600">{error}</p>}
    </li>
  )
}

export function PersonConnections({ person }: { person: PersonDetail }) {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [drafts, setDrafts] = useState<Draft[] | null>(null)
  const [creating, setCreating] = useState<Creating>(null)
  const editing = drafts !== null

  const { data: places = [] } = useQuery({
    queryKey: ['places'],
    queryFn: entityService.getPlaces,
    enabled: editing,
  })
  const { data: sources = [] } = useQuery({
    queryKey: ['sources'],
    queryFn: entityService.getSources,
    enabled: editing,
  })

  const mutation = useMutation({
    mutationFn: (connections: PersonConnectionInput[]) =>
      entityService.updatePersonConnections(person.id, connections),
    onSuccess: (updated) => {
      queryClient.setQueryData(['person', person.id], updated)
      queryClient.invalidateQueries({ queryKey: ['persons'] })
      queryClient.invalidateQueries({ queryKey: ['places'] })
      setDrafts(null)
      setCreating(null)
    },
  })

  if (!user) return null

  if (!drafts)
    return (
      <button
        type="button"
        onClick={() => {
          mutation.reset()
          setDrafts(person.connections.map(toDraft))
        }}
        className="inline-flex items-center gap-1 rounded-md border border-indigo-600 px-3 py-1.5 text-sm font-medium text-indigo-700 hover:bg-indigo-50"
      >
        <Pencil className="h-4 w-4" aria-hidden="true" />
        Edit times & places
      </button>
    )

  const placeOptions = places.map((p) => ({ id: p.id, label: p.label }))
  const sourceOptions = sources.map((s) => ({ id: s.id, label: s.label }))
  const hasErrors = drafts.some((draft) => draftError(draft) !== null)

  const updateDraft = (key: number, changes: Partial<Draft>) =>
    setDrafts(
      (current) => current && current.map((d) => (d.key === key ? { ...d, ...changes } : d)),
    )

  const created = (key: number, kind: 'place' | 'source', option: EntityOption) => {
    if (kind === 'place') {
      queryClient.setQueryData<PlaceList[]>(['places'], (current = []) => [
        ...current,
        { id: option.id, label: option.label, personCount: 0 },
      ])
      updateDraft(key, { place: option })
    } else {
      queryClient.invalidateQueries({ queryKey: ['sources'] })
      queryClient.setQueryData<Source[]>(['sources'], (current = []) => [
        ...current,
        {
          id: option.id,
          label: option.label,
          shelfmark: null,
          url: null,
          description: '',
          count: 0,
        },
      ])
      updateDraft(key, { source: option })
    }
    setCreating(null)
  }

  return (
    <div className="rounded-md border border-indigo-200 bg-indigo-50/40 p-4 space-y-4">
      <div>
        <h3 className="font-medium text-gray-900">Times & places</h3>
        <p className="text-sm text-gray-500">
          Each row links {person.label} to a place, a time, or both.
        </p>
      </div>

      <ul className="space-y-3">
        {drafts.map((draft) => (
          <DraftRow
            key={draft.key}
            draft={draft}
            places={placeOptions}
            sources={sourceOptions}
            creating={creating?.key === draft.key ? creating : null}
            onChange={(updated) => updateDraft(draft.key, updated)}
            onRemove={() => setDrafts(drafts.filter((d) => d.key !== draft.key))}
            onCreate={(kind, name) => setCreating({ key: draft.key, kind, name })}
            onCreated={(kind, option) => created(draft.key, kind, option)}
            onCancelCreate={() => setCreating(null)}
          />
        ))}
      </ul>

      <button
        type="button"
        onClick={() => setDrafts([...drafts, emptyDraft()])}
        className="inline-flex items-center gap-1 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
      >
        <Plus className="h-4 w-4" aria-hidden="true" />
        Add row
      </button>

      {mutation.isError && <p className="text-sm text-red-600">{errorMessage(mutation.error)}</p>}

      <div className="flex items-center justify-end gap-2">
        {mutation.isPending && <Loader2 className="h-4 w-4 animate-spin text-indigo-500" />}
        <button
          type="button"
          onClick={() => {
            setDrafts(null)
            setCreating(null)
          }}
          className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          type="button"
          disabled={mutation.isPending || hasErrors || creating !== null}
          onClick={() => mutation.mutate(drafts.map(toInput))}
          className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          Save
        </button>
      </div>
    </div>
  )
}
