import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { entityService } from '../services/entityService'
import { Database, ExternalLink, Loader2, Pencil, Plus, Trash2 } from 'lucide-react'
import { useAuth } from '../auth/authContext'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { errorMessage } from '../components/errorMessage'
import { SourceForm } from '../components/SourceForm'
import type { Source, SourceInput } from '../types/entity'

export default function Sources() {
  const { user } = useAuth()
  const [creating, setCreating] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [deleting, setDeleting] = useState<Source | null>(null)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  const {
    data: sources = [],
    isLoading: loading,
    refetch: fetchSources,
  } = useQuery<Source[]>({
    queryKey: ['sources'],
    queryFn: () => entityService.getSources(),
  })

  const createSource = async (body: SourceInput) => {
    await entityService.createSource(body)
    setCreating(false)
    await fetchSources()
  }

  const updateSource = async (id: string, body: SourceInput) => {
    await entityService.updateSource(id, body)
    setEditingId(null)
    await fetchSources()
  }

  const confirmDelete = async () => {
    if (!deleting) return
    const source = deleting
    setDeleting(null)
    setDeleteError(null)
    try {
      await entityService.deleteSource(source.id)
      await fetchSources()
    } catch (error) {
      setDeleteError(`Could not delete ${source.label}: ${errorMessage(error)}`)
    }
  }

  if (loading)
    return (
      <div className="flex justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
      </div>
    )

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Data Sources / Research Projects / Collaborators
          </h1>
          <p className="text-gray-500 mt-1">
            Research projects and data sources powering the knowledge graph.
          </p>
        </div>
        {user && !creating && (
          <button
            type="button"
            onClick={() => setCreating(true)}
            className="inline-flex items-center gap-1 rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
          >
            <Plus className="h-4 w-4" aria-hidden="true" />
            Add source
          </button>
        )}
      </div>

      {deleteError && (
        <p className="rounded-md border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700">
          {deleteError}
        </p>
      )}

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {user && creating && (
          <div className="bg-white rounded-lg shadow border border-indigo-200 p-5">
            <SourceForm
              initial={{ name: '' }}
              submitLabel="Create"
              onSubmit={createSource}
              onCancel={() => setCreating(false)}
            />
          </div>
        )}

        {sources.map((source) => (
          <div
            key={source.id}
            className="bg-white rounded-lg shadow border border-gray-100 overflow-hidden flex flex-col transition-all hover:shadow-md"
          >
            {user && editingId === source.id ? (
              <div className="p-5">
                <SourceForm
                  initial={{ name: source.label, shelfmark: source.shelfmark, url: source.url }}
                  submitLabel="Save"
                  onSubmit={(body) => updateSource(source.id, body)}
                  onCancel={() => setEditingId(null)}
                />
              </div>
            ) : (
              <div className="p-5 flex-grow">
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
                    <Database className="h-5 w-5" />
                  </div>
                  <h3 className="font-semibold text-gray-900 flex-grow">{source.label}</h3>
                  {user && (
                    <div className="flex gap-1">
                      <button
                        type="button"
                        onClick={() => setEditingId(source.id)}
                        aria-label={`Edit ${source.label}`}
                        className="p-1 text-gray-400 hover:text-indigo-600"
                      >
                        <Pencil className="h-4 w-4" aria-hidden="true" />
                      </button>
                      <button
                        type="button"
                        onClick={() => setDeleting(source)}
                        aria-label={`Delete ${source.label}`}
                        className="p-1 text-gray-400 hover:text-red-600"
                      >
                        <Trash2 className="h-4 w-4" aria-hidden="true" />
                      </button>
                    </div>
                  )}
                </div>
                {source.shelfmark && (
                  <p className="text-sm text-gray-500 mb-1">Shelfmark: {source.shelfmark}</p>
                )}
                {source.url && (
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noreferrer"
                    className="mb-1 inline-flex items-center gap-1 text-sm text-indigo-600 hover:underline break-all"
                  >
                    {source.url}
                    <ExternalLink className="h-3 w-3 flex-shrink-0" aria-hidden="true" />
                  </a>
                )}
                <p className="text-sm text-gray-600">{source.description}</p>

                <div className="mt-4 pt-4 border-t border-gray-50 flex justify-between items-center text-sm">
                  <span className="text-gray-500">Entities</span>
                  <span className="font-medium text-gray-900 bg-gray-100 px-2 py-1 rounded">
                    {source.count}
                  </span>
                </div>
              </div>
            )}
          </div>
        ))}

        {sources.length === 0 && !creating && (
          <div className="col-span-full py-12 text-center text-gray-500 bg-white rounded-lg border border-dashed border-gray-300">
            No data sources found.
          </div>
        )}
      </div>

      <ConfirmDialog
        open={deleting !== null}
        title="Delete source?"
        confirmLabel="Delete"
        onConfirm={confirmDelete}
        onCancel={() => setDeleting(null)}
      >
        <p>
          <span className="font-medium text-gray-900">{deleting?.label}</span> will be permanently
          deleted. Sources that are linked to other records cannot be deleted.
        </p>
      </ConfirmDialog>
    </div>
  )
}
