/**
 * memQrag demo UI shell.
 *
 * This is a placeholder shell with no product workflow logic. It only
 * proves the React + Tailwind build works end to end. The chat interface,
 * upload panel, memory panel, and side-by-side standard RAG vs memQrag
 * comparison are built in Phase 8 per docs/PRODUCT_TIMELINE.md.
 */
function App() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-950 px-6 py-16 text-slate-100">
      <div className="max-w-xl text-center">
        <p className="text-sm font-medium uppercase tracking-widest text-violet-400">
          Demo UI Shell
        </p>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight">memQrag</h1>
        <p className="mt-4 text-base text-slate-400">
          Production RAG with persistent retrieval memory. This shell has no
          product workflow logic yet. Ingestion, retrieval, memory, and the
          standard RAG vs. memQrag comparison panel are built in later
          phases of the project timeline.
        </p>
        <div className="mt-8 inline-flex items-center gap-2 rounded-full border border-slate-800 bg-slate-900 px-4 py-2 text-sm text-slate-300">
          <span
            className="h-2 w-2 rounded-full bg-emerald-500"
            aria-hidden="true"
          />
          UI shell running
        </div>
      </div>
    </div>
  )
}

export default App
