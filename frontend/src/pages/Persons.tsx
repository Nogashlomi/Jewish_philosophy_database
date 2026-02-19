import { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { entityService } from '../services/entityService';
import type { PersonList } from '../types/entity';
import { Search, ArrowUpDown, Loader2 } from 'lucide-react';
import SourceFilter from '../components/SourceFilter';
import { flexRender, getCoreRowModel, getSortedRowModel, useReactTable, type ColumnDef, type SortingState } from "@tanstack/react-table"

// Simple DataTable component
function DataTable({ columns, data }: { columns: ColumnDef<PersonList>[], data: PersonList[] }) {
    const [sorting, setSorting] = useState<SortingState>([])
    const table = useReactTable({
        data,
        columns,
        getCoreRowModel: getCoreRowModel(),
        onSortingChange: setSorting,
        getSortedRowModel: getSortedRowModel(),
        state: {
            sorting,
        },
    })

    return (
        <div className="rounded-md border">
            <table className="w-full text-sm text-left">
                <thead className="bg-gray-50 text-gray-700 uppercase">
                    {table.getHeaderGroups().map((headerGroup) => (
                        <tr key={headerGroup.id}>
                            {headerGroup.headers.map((header) => (
                                <th key={header.id} className="px-6 py-3 font-medium">
                                    {header.isPlaceholder
                                        ? null
                                        : flexRender(
                                            header.column.columnDef.header,
                                            header.getContext()
                                        )}
                                </th>
                            ))}
                        </tr>
                    ))}
                </thead>
                <tbody className="divide-y divide-gray-200">
                    {table.getRowModel().rows?.length ? (
                        table.getRowModel().rows.map((row) => (
                            <tr
                                key={row.id}
                                className="bg-white hover:bg-gray-50 transition-colors"
                            >
                                {row.getVisibleCells().map((cell) => (
                                    <td key={cell.id} className="px-6 py-4">
                                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                    </td>
                                ))}
                            </tr>
                        ))
                    ) : (
                        <tr>
                            <td colSpan={columns.length} className="h-24 text-center">
                                No results.
                            </td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
    )
}

export default function Persons() {
    const [persons, setPersons] = useState<PersonList[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [searchParams, setSearchParams] = useSearchParams();

    const selectedSource = searchParams.get('source');

    const handleSourceChange = (source: string | null) => {
        if (source) {
            setSearchParams({ source });
        } else {
            setSearchParams({});
        }
    };

    useEffect(() => {
        const fetchPersons = async () => {
            setLoading(true);
            try {
                const data = await entityService.getPersons(selectedSource || undefined);
                setPersons(data);
            } catch (error) {
                console.error("Failed to fetch persons", error);
            } finally {
                setLoading(false);
            }
        };
        fetchPersons();
    }, [selectedSource]);

    const filteredPersons = persons.filter(person =>
        person.label.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const columns: ColumnDef<PersonList>[] = [
        {
            accessorKey: "label",
            header: ({ column }) => {
                return (
                    <button
                        className="flex items-center hover:text-gray-900"
                        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
                    >
                        Name
                        <ArrowUpDown className="ml-2 h-4 w-4" />
                    </button>
                )
            },
            cell: ({ row }) => (
                <Link to={`/persons/${row.original.id}`} className="font-medium text-indigo-600 hover:text-indigo-900">
                    {row.original.label}
                </Link>
            ),
        },
        {
            accessorKey: "source",
            header: "Source",
            cell: ({ row }) => <span className="text-xs font-semibold text-gray-500 bg-gray-100 px-2 py-1 rounded">{row.original.source?.label || "-"}</span>,
        },
        {
            accessorKey: "birth_year",
            header: ({ column }) => {
                return (
                    <button
                        className="flex items-center hover:text-gray-900"
                        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
                    >
                        Birth Year
                        <ArrowUpDown className="ml-2 h-4 w-4" />
                    </button>
                )
            },
            cell: ({ row }) => <span className="text-gray-500">{row.original.birth_year || "-"}</span>,
        },
        {
            accessorKey: "death_year",
            header: ({ column }) => {
                return (
                    <button
                        className="flex items-center hover:text-gray-900"
                        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
                    >
                        Death Year
                        <ArrowUpDown className="ml-2 h-4 w-4" />
                    </button>
                )
            },
            cell: ({ row }) => <span className="text-gray-500">{row.original.death_year || "-"}</span>,
        },
    ]

    if (loading) return <div className="flex justify-center p-8"><Loader2 className="h-8 w-8 animate-spin text-indigo-500" /></div>

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 font-sans">Historical Persons</h1>
                    <span className="text-sm text-gray-500">Total: {filteredPersons.length}</span>
                </div>

                <div className="flex items-center space-x-4">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                        <input
                            type="text"
                            placeholder="Search persons..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                        />
                    </div>
                    <SourceFilter
                        selectedSource={selectedSource}
                        onSourceChange={handleSourceChange}
                    />
                </div>
            </div>

            <div className="bg-white rounded-lg shadow overflow-hidden">
                <DataTable columns={columns} data={filteredPersons} />
            </div>
        </div>
    )
}
