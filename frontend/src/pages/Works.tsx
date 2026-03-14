import { useState, useEffect, useCallback } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { entityService } from '../services/entityService';
import type { WorkList } from '../types/entity';
import { Search, ArrowUpDown, Loader2, ChevronLeft, ChevronRight } from 'lucide-react';
import SourceFilter from '../components/SourceFilter';
import { flexRender, getCoreRowModel, getSortedRowModel, useReactTable, type ColumnDef, type SortingState } from "@tanstack/react-table"

const PAGE_SIZE = 100;

function DataTable({ columns, data }: { columns: ColumnDef<WorkList>[], data: WorkList[] }) {
    const [sorting, setSorting] = useState<SortingState>([])
    const table = useReactTable({
        data,
        columns,
        getCoreRowModel: getCoreRowModel(),
        onSortingChange: setSorting,
        getSortedRowModel: getSortedRowModel(),
        state: { sorting },
    })

    return (
        <div className="rounded-md border">
            <table className="w-full text-sm text-left">
                <thead className="bg-gray-50 text-gray-700 uppercase">
                    {table.getHeaderGroups().map((headerGroup) => (
                        <tr key={headerGroup.id}>
                            {headerGroup.headers.map((header) => (
                                <th key={header.id} className="px-6 py-3 font-medium">
                                    {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                                </th>
                            ))}
                        </tr>
                    ))}
                </thead>
                <tbody className="divide-y divide-gray-200">
                    {table.getRowModel().rows?.length ? (
                        table.getRowModel().rows.map((row) => (
                            <tr key={row.id} className="bg-white hover:bg-gray-50 transition-colors">
                                {row.getVisibleCells().map((cell) => (
                                    <td key={cell.id} className="px-6 py-4">
                                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                    </td>
                                ))}
                            </tr>
                        ))
                    ) : (
                        <tr>
                            <td colSpan={columns.length} className="h-24 text-center">No results.</td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
    )
}

function Pagination({ page, totalPages, onPageChange }: { page: number, totalPages: number, onPageChange: (p: number) => void }) {
    if (totalPages <= 1) return null;
    return (
        <div className="flex items-center justify-between px-4 py-3 bg-white border-t border-gray-200 sm:px-6">
            <div className="text-sm text-gray-500">
                Page <strong>{page}</strong> of <strong>{totalPages}</strong>
            </div>
            <div className="flex items-center gap-2">
                <button
                    onClick={() => onPageChange(page - 1)}
                    disabled={page <= 1}
                    className="p-1 rounded border border-gray-300 disabled:opacity-40 hover:bg-gray-50"
                >
                    <ChevronLeft className="h-4 w-4" />
                </button>
                {[...Array(Math.min(totalPages, 7))].map((_, i) => {
                    let p: number;
                    if (totalPages <= 7) {
                        p = i + 1;
                    } else if (page <= 4) {
                        p = i + 1;
                    } else if (page >= totalPages - 3) {
                        p = totalPages - 6 + i;
                    } else {
                        p = page - 3 + i;
                    }
                    return (
                        <button
                            key={p}
                            onClick={() => onPageChange(p)}
                            className={`px-3 py-1 rounded border text-sm ${p === page ? 'bg-indigo-600 text-white border-indigo-600' : 'border-gray-300 hover:bg-gray-50'}`}
                        >
                            {p}
                        </button>
                    );
                })}
                <button
                    onClick={() => onPageChange(page + 1)}
                    disabled={page >= totalPages}
                    className="p-1 rounded border border-gray-300 disabled:opacity-40 hover:bg-gray-50"
                >
                    <ChevronRight className="h-4 w-4" />
                </button>
            </div>
        </div>
    );
}

export default function Works() {
    const [works, setWorks] = useState<WorkList[]>([]);
    const [total, setTotal] = useState(0);
    const [totalPages, setTotalPages] = useState(1);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [page, setPage] = useState(1);
    const [searchParams, setSearchParams] = useSearchParams();

    const selectedSource = searchParams.get('source');

    const handleSourceChange = (source: string | null) => {
        setPage(1);
        if (source) {
            setSearchParams({ source });
        } else {
            setSearchParams({});
        }
    };

    const fetchWorks = useCallback(async () => {
        setLoading(true);
        try {
            const data = await entityService.getWorks(selectedSource || undefined, page, PAGE_SIZE);
            setWorks(data.items);
            setTotal(data.total);
            setTotalPages(data.total_pages);
        } catch (error) {
            console.error("Failed to fetch works", error);
        } finally {
            setLoading(false);
        }
    }, [selectedSource, page]);

    useEffect(() => {
        fetchWorks();
    }, [fetchWorks]);

    const filteredWorks = works.filter(work =>
        work.title.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const columns: ColumnDef<WorkList>[] = [
        {
            accessorKey: "title",
            header: ({ column }) => (
                <button className="flex items-center hover:text-gray-900" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>
                    Title <ArrowUpDown className="ml-2 h-4 w-4" />
                </button>
            ),
            cell: ({ row }) => (
                <Link to={`/works/${row.original.id}`} className="font-medium text-indigo-600 hover:text-indigo-900">
                    {row.original.title}
                </Link>
            ),
        },
        {
            accessorKey: "authors",
            header: "Author",
            cell: ({ row }) => <span className="text-gray-700">{row.original.authors || "-"}</span>,
        },
        {
            accessorKey: "subjects",
            header: "Subject",
            cell: ({ row }) => <span className="text-gray-700">{row.original.subjects || "-"}</span>,
        },
        {
            accessorKey: "languages",
            header: "Language",
            cell: ({ row }) => <span className="text-gray-700">{row.original.languages || "-"}</span>,
        },
    ]

    if (loading) return <div className="flex justify-center p-8"><Loader2 className="h-8 w-8 animate-spin text-indigo-500" /></div>

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 font-sans">Historical Works</h1>
                    <span className="text-sm text-gray-500">Total: {total.toLocaleString()} works</span>
                </div>

                <div className="flex items-center space-x-4">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                        <input
                            type="text"
                            placeholder="Search this page..."
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
                <DataTable columns={columns} data={filteredWorks} />
                <Pagination page={page} totalPages={totalPages} onPageChange={(p) => { setPage(p); setSearchTerm(''); }} />
            </div>
        </div>
    )
}
