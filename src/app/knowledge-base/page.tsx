"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  BookOpen,
  ChevronLeft,
  ChevronRight,
  Database,
  FileText,
  LoaderCircle,
  Search,
  Trash2,
  UploadCloud,
} from "lucide-react";

import {
  deleteKnowledgeBaseDocument,
  getKnowledgeBaseDatasets,
  getKnowledgeBaseDocuments,
  getKnowledgeBaseFileUrl,
  queryKnowledgeBase,
  seedKnowledgeBase,
  uploadKnowledgeBaseDocument,
  type KnowledgeBaseChunkResult,
  type KnowledgeBaseDocument,
} from "@/lib/api";
import { cn } from "@/lib/utils";

export default function KnowledgeBasePage() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string | null>(null);
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<KnowledgeBaseChunkResult[]>([]);

  const datasetsQuery = useQuery({
    queryKey: ["knowledge-base-datasets"],
    queryFn: getKnowledgeBaseDatasets,
  });

  const documentsQuery = useQuery({
    queryKey: ["knowledge-base-documents", selectedDatasetId, page],
    queryFn: () => getKnowledgeBaseDocuments(selectedDatasetId!, page, 10),
    enabled: Boolean(selectedDatasetId),
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) {
        return false;
      }
      return data.documents.some((document) => document.status === "processing")
        ? 2500
        : false;
    },
  });

  useEffect(() => {
    if (!selectedDatasetId && datasetsQuery.data?.datasets.length) {
      setSelectedDatasetId(datasetsQuery.data.datasets[0].id);
    }
  }, [datasetsQuery.data, selectedDatasetId]);

  useEffect(() => {
    setPage(1);
    setSelectedDocumentId(null);
    setResults([]);
  }, [selectedDatasetId]);

  useEffect(() => {
    const docs = documentsQuery.data?.documents ?? [];
    if (!docs.length) {
      setSelectedDocumentId(null);
      return;
    }
    const currentExists = docs.some((document) => document.id === selectedDocumentId);
    if (!currentExists) {
      setSelectedDocumentId(docs[0].id);
    }
  }, [documentsQuery.data, selectedDocumentId]);

  const selectedDocument = useMemo(() => {
    return (
      documentsQuery.data?.documents.find(
        (document) => document.id === selectedDocumentId,
      ) ?? null
    );
  }, [documentsQuery.data, selectedDocumentId]);

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      if (!selectedDatasetId) {
        throw new Error("Select a dataset first.");
      }
      return uploadKnowledgeBaseDocument(selectedDatasetId, file);
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["knowledge-base-datasets"] }),
        queryClient.invalidateQueries({ queryKey: ["knowledge-base-documents"] }),
      ]);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (document: KnowledgeBaseDocument) => {
      return deleteKnowledgeBaseDocument(document.dataset_id, document.id);
    },
    onSuccess: async (_, document) => {
      if (document.id === selectedDocumentId) {
        setSelectedDocumentId(null);
      }
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["knowledge-base-datasets"] }),
        queryClient.invalidateQueries({ queryKey: ["knowledge-base-documents"] }),
      ]);
    },
  });

  const queryMutation = useMutation({
    mutationFn: async () => {
      if (!selectedDatasetId) {
        throw new Error("Select a dataset first.");
      }
      return queryKnowledgeBase(selectedDatasetId, query, 5);
    },
    onSuccess: (response) => {
      setResults(response.results);
    },
  });

  const seedMutation = useMutation({
    mutationFn: seedKnowledgeBase,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["knowledge-base-datasets"] }),
        queryClient.invalidateQueries({ queryKey: ["knowledge-base-documents"] }),
      ]);
    },
  });

  const totalPages = documentsQuery.data
    ? Math.max(1, Math.ceil(documentsQuery.data.total / documentsQuery.data.limit))
    : 1;

  return (
    <div className="space-y-8">
      <section className="rounded-[2rem] border border-border bg-[radial-gradient(circle_at_top_left,_rgba(56,189,248,0.16),_transparent_35%),linear-gradient(135deg,rgba(255,255,255,0.04),rgba(255,255,255,0.01))] p-8">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl">
            <p className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2 text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">
              <Database className="h-4 w-4 text-sky-400" />
              Knowledge Base
            </p>
            <h1 className="mt-5 text-4xl font-semibold tracking-tight sm:text-5xl">
              Browse datasets, preview PDFs, and query indexed chunks.
            </h1>
            <p className="mt-4 text-base leading-7 text-muted-foreground">
              AuraFlow now supports dataset-level document management, async PDF
              ingestion, secure previews, and real chunk-based retrieval.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">

            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={!selectedDatasetId || uploadMutation.isPending}
              className="inline-flex items-center gap-2 rounded-full bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground transition-transform hover:-translate-y-0.5 disabled:opacity-60"
            >
              <UploadCloud className="h-4 w-4" />
              Upload PDF
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf"
              className="hidden"
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) {
                  uploadMutation.mutate(file);
                }
                event.currentTarget.value = "";
              }}
            />
          </div>
        </div>

        <div className="mt-8 grid gap-4 md:grid-cols-2">
          <SummaryCard
            label="Documents"
            value={datasetsQuery.data?.summary.total_documents ?? 0}
          />
          <SummaryCard
            label="Chunks"
            value={datasetsQuery.data?.summary.total_chunks ?? 0}
          />
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1fr_1.1fr]">

        <div className="space-y-6">
          <section className="rounded-[2rem] border border-border bg-card/70 p-5">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold">
                  Knowledge Base Documents
                </h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  Upload PDFs, monitor ingestion, and manage the selected corpus.
                </p>
              </div>
              {documentsQuery.isFetching ? (
                <LoaderCircle className="h-5 w-5 animate-spin text-muted-foreground" />
              ) : null}
            </div>

            <div className="mt-5 space-y-3">
              {documentsQuery.data?.documents.length ? (
                documentsQuery.data.documents.map((document) => (
                  <div
                    key={document.id}
                    className={cn(
                      "flex items-center justify-between gap-4 rounded-[1.25rem] border p-4 transition-all",
                      selectedDocumentId === document.id
                        ? "border-primary/40 bg-primary/10"
                        : "border-border bg-background/80",
                    )}
                  >
                    <button
                      onClick={() => setSelectedDocumentId(document.id)}
                      className="flex min-w-0 flex-1 items-center gap-3 text-left"
                    >
                      <div className="flex h-10 w-10 items-center justify-center rounded-2xl border border-border bg-card">
                        <FileText className="h-4 w-4 text-sky-400" />
                      </div>
                      <div className="min-w-0">
                        <p className="truncate font-semibold">{document.file_name}</p>
                        <p className="mt-1 text-xs text-muted-foreground">
                          {document.page_count} pages • {document.chunk_count} chunks
                        </p>
                        {document.error_message ? (
                          <p className="mt-1 text-xs text-destructive">
                            {document.error_message}
                          </p>
                        ) : null}
                      </div>
                    </button>

                    <div className="flex items-center gap-3">
                      <span
                        className={cn(
                          "rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em]",
                          document.status === "ready" &&
                            "border-emerald-400/30 bg-emerald-500/10 text-emerald-400",
                          document.status === "processing" &&
                            "border-sky-400/30 bg-sky-500/10 text-sky-400",
                          document.status === "failed" &&
                            "border-destructive/30 bg-destructive/10 text-destructive",
                        )}
                      >
                        {document.status}
                      </span>
                      <button
                        onClick={() => deleteMutation.mutate(document)}
                        className="rounded-full border border-border p-2 text-muted-foreground transition-colors hover:text-destructive"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                ))
              ) : (
                <div className="rounded-[1.25rem] border border-dashed border-border bg-background/60 p-8 text-center text-sm text-muted-foreground">
                  Upload a PDF or seed the sample corpus to populate this dataset.
                </div>
              )}
            </div>

            <div className="mt-5 flex items-center justify-between">
              <button
                onClick={() => setPage((current) => Math.max(1, current - 1))}
                disabled={page <= 1}
                className="inline-flex items-center gap-2 rounded-full border border-border px-4 py-2 text-sm font-medium disabled:opacity-50"
              >
                <ChevronLeft className="h-4 w-4" />
                Previous
              </button>
              <span className="text-sm text-muted-foreground">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
                disabled={page >= totalPages}
                className="inline-flex items-center gap-2 rounded-full border border-border px-4 py-2 text-sm font-medium disabled:opacity-50"
              >
                Next
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </section>

          <section className="rounded-[2rem] border border-border bg-card/70 p-5">
            <div className="flex items-center gap-3">
              <Search className="h-5 w-5 text-amber-400" />
              <div>
                <h2 className="text-xl font-semibold">Chunk Retrieval</h2>
                <p className="text-sm text-muted-foreground">
                  Search the selected dataset and inspect the highest-similarity chunks.
                </p>
              </div>
            </div>

            <div className="mt-5 flex flex-col gap-3 md:flex-row">
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Ask a question about the selected dataset..."
                className="flex-1 rounded-full border border-border bg-background px-5 py-3 text-sm outline-none transition-colors focus:border-primary"
              />
              <button
                onClick={() => queryMutation.mutate()}
                disabled={!selectedDatasetId || !query.trim() || queryMutation.isPending}
                className="rounded-full bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground disabled:opacity-60"
              >
                {queryMutation.isPending ? "Searching..." : "Run Retrieval"}
              </button>
            </div>

            <div className="mt-5 space-y-3">
              {results.length ? (
                results.map((result) => (
                  <div
                    key={result.chunk_id}
                    className="rounded-[1.25rem] border border-border bg-background/80 p-4"
                  >
                    <div className="flex flex-wrap items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                      <span>{result.document_title}</span>
                      <span>Page {result.page_number}</span>
                      <span>
                        {result.start_char}-{result.end_char}
                      </span>
                      <span>Score {result.score.toFixed(3)}</span>
                    </div>
                    <p className="mt-3 text-sm leading-6 text-foreground/90">
                      {result.text}
                    </p>
                  </div>
                ))
              ) : (
                <div className="rounded-[1.25rem] border border-dashed border-border bg-background/60 p-6 text-sm text-muted-foreground">
                  Retrieval results will appear here once you run a query.
                </div>
              )}
            </div>
          </section>
        </div>

        <section className="rounded-[2rem] border border-border bg-card/70 p-5">
          <div>
            <h2 className="text-xl font-semibold">PDF Preview</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Secure preview for the selected document in the active dataset.
            </p>
          </div>
          <div className="mt-5 overflow-hidden rounded-[1.5rem] border border-border bg-background">
            {selectedDatasetId && selectedDocument ? (
              <iframe
                title={selectedDocument.file_name}
                src={getKnowledgeBaseFileUrl(selectedDatasetId, selectedDocument.id)}
                className="h-[760px] w-full bg-white"
              />
            ) : (
              <div className="flex h-[760px] items-center justify-center text-sm text-muted-foreground">
                Select a ready document to preview it here.
              </div>
            )}
          </div>
        </section>
      </section>
    </div>
  );
}

function SummaryCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-[1.5rem] border border-border bg-card p-5">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
        {label}
      </p>
      <p className="mt-3 text-3xl font-semibold">{value}</p>
    </div>
  );
}
