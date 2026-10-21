import { useState } from 'react'
import { Combobox, ComboboxInput, ComboboxOption, ComboboxOptions } from '@headlessui/react'
import { Plus, X } from 'lucide-react'

export interface EntityOption {
  id: string
  label: string
}

const MAX_OPTIONS = 50
const CREATE_ID = '__create__'

export function EntityCombobox({
  value,
  options,
  placeholder,
  createLabel,
  onChange,
  onCreate,
}: {
  value: EntityOption | null
  options: EntityOption[]
  placeholder: string
  createLabel: string
  onChange: (value: EntityOption | null) => void
  onCreate: (query: string) => void
}) {
  const [query, setQuery] = useState('')
  const normalized = query.trim().toLowerCase()
  const matches = (
    normalized
      ? options.filter((option) => option.label.toLowerCase().includes(normalized))
      : options
  ).slice(0, MAX_OPTIONS)
  const exactMatch = options.some((option) => option.label.toLowerCase() === normalized)

  return (
    <div className="relative flex items-center">
      <Combobox
        value={value}
        by="id"
        onChange={(option: EntityOption | null) => {
          setQuery('')
          if (option?.id === CREATE_ID) onCreate(option.label)
          else onChange(option)
        }}
        onClose={() => setQuery('')}
      >
        <ComboboxInput
          className="block w-full rounded-md border border-gray-300 px-3 py-1.5 pr-8 text-sm"
          placeholder={placeholder}
          displayValue={(option: EntityOption | null) => option?.label ?? ''}
          onChange={(event) => setQuery(event.target.value)}
        />
        <ComboboxOptions
          anchor="bottom start"
          className="z-50 max-h-60 w-[var(--input-width)] overflow-auto rounded-md border border-gray-200 bg-white py-1 text-sm shadow-lg empty:invisible [--anchor-gap:4px]"
        >
          {matches.map((option) => (
            <ComboboxOption
              key={option.id}
              value={option}
              className="cursor-pointer px-3 py-1.5 text-gray-800 data-[focus]:bg-indigo-50 data-[selected]:font-medium"
            >
              {option.label}
            </ComboboxOption>
          ))}
          {!exactMatch && (
            <ComboboxOption
              value={{ id: CREATE_ID, label: query.trim() }}
              className="flex cursor-pointer items-center gap-1 px-3 py-1.5 text-indigo-700 data-[focus]:bg-indigo-50"
            >
              <Plus className="h-3.5 w-3.5" aria-hidden="true" />
              {query.trim() ? `${createLabel} "${query.trim()}"` : createLabel}
            </ComboboxOption>
          )}
        </ComboboxOptions>
      </Combobox>
      {value && (
        <button
          type="button"
          onClick={() => onChange(null)}
          aria-label="Clear"
          className="absolute right-2 text-gray-400 hover:text-red-600"
        >
          <X className="h-3.5 w-3.5" aria-hidden="true" />
        </button>
      )}
    </div>
  )
}
