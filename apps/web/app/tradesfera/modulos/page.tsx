"use client";

import React, { useState, useEffect } from "react";
import {
  BookOpen,
  Search,
  FileText,
  Clock,
  ChevronRight,
  Sparkles,
  Download,
  CheckCircle2,
  Bookmark,
  Layers,
} from "lucide-react";

interface ModuleMeta {
  id: string;
  slug: string;
  filename: string;
  title: string;
  category: string;
  sizeBytes: number;
}

interface ModuleDetail {
  id: string;
  filename: string;
  title: string;
  category: string;
  content: string;
}

export default function TradesferaModulosPage() {
  const [modules, setModules] = useState<ModuleMeta[]>([]);
  const [selectedId, setSelectedId] = useState<string>("01");
  const [selectedDetail, setSelectedDetail] = useState<ModuleDetail | null>(null);
  const [loadingList, setLoadingList] = useState<boolean>(true);
  const [loadingDetail, setLoadingDetail] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [filterCategory, setFilterCategory] = useState<string>("ALL");

  // Cargar lista de módulos
  useEffect(() => {
    const loadModules = async () => {
      try {
        const res = await fetch("/api/tradesfera/modulos");
        if (res.ok) {
          const data = await res.json();
          setModules(data.modules || []);
        }
      } catch (err) {
        console.error("Error al cargar módulos:", err);
      } finally {
        setLoadingList(false);
      }
    };
    loadModules();
  }, []);

  // Cargar contenido del módulo seleccionado
  useEffect(() => {
    if (!selectedId) return;
    const loadDetail = async () => {
      setLoadingDetail(true);
      try {
        const res = await fetch(`/api/tradesfera/modulos?slug=${selectedId}`);
        if (res.ok) {
          const data = await res.json();
          setSelectedDetail(data);
        }
      } catch (err) {
        console.error("Error al cargar detalle del módulo:", err);
      } finally {
        setLoadingDetail(false);
      }
    };
    loadDetail();
  }, [selectedId]);

  // Categorías disponibles
  const categories = Array.from(new Set(modules.map((m) => m.category))).sort();

  // Filtrado
  const filteredModules = modules.filter((m) => {
    if (filterCategory !== "ALL" && m.category !== filterCategory) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchTitle = m.title.toLowerCase().includes(q);
      const matchFile = m.filename.toLowerCase().includes(q);
      const matchId = m.id.includes(q);
      return matchTitle || matchFile || matchId;
    }
    return true;
  });

  return (
    <div className="w-full space-y-3 pb-8 text-[var(--text-1)] font-sans">
      {/* Header Banner */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-1">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-md bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center text-[var(--profit)]">
            <BookOpen className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-lg md:text-xl font-bold tracking-tight text-[var(--text-1)] flex items-center gap-2">
              <span>Biblioteca de Manuales Técnicos de Tradesfera</span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-2)] font-mono">
                16 Módulos en Disco
              </span>
            </h1>
            <p className="text-xs text-[var(--text-2)] font-mono mt-0.5">
              Corpus documental exhaustivo de fondeo de futuros CME · Leído en tiempo real desde <code>docs/tradesfera/</code>
            </p>
          </div>
        </div>
      </div>

      {/* Main Layout: Sidebar Selector + Reader View */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Sidebar: Lista de Módulos */}
        <div className="lg:col-span-4 space-y-3 font-mono text-xs">
          {/* Buscador y Filtro */}
          <div className="p-3 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg space-y-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-[var(--text-3)]" />
              <input
                type="text"
                placeholder="Buscar en los 16 manuales..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 bg-[var(--surface-2)] border border-[var(--border)] rounded-md text-xs text-[var(--text-1)] placeholder-[var(--text-3)] focus:outline-none focus:border-[var(--border-strong)]"
              />
            </div>
            <div className="flex items-center gap-1.5 overflow-x-auto text-[10.5px]">
              <button
                onClick={() => setFilterCategory("ALL")}
                className={`px-2 py-0.5 rounded border transition cursor-pointer ${
                  filterCategory === "ALL"
                    ? "bg-[var(--surface-3)] border-[var(--border-strong)] text-[var(--text-1)] font-bold"
                    : "bg-[var(--surface-2)] border-transparent text-[var(--text-3)] hover:text-[var(--text-1)]"
                }`}
              >
                Todas
              </button>
              {categories.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setFilterCategory(cat)}
                  className={`px-2 py-0.5 rounded border transition cursor-pointer whitespace-nowrap ${
                    filterCategory === cat
                      ? "bg-[var(--surface-3)] border-[var(--border-strong)] text-[var(--text-1)] font-bold"
                      : "bg-[var(--surface-2)] border-transparent text-[var(--text-3)] hover:text-[var(--text-1)]"
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          {/* Lista scrolleable de manuales */}
          <div className="space-y-1.5 max-h-[620px] overflow-y-auto pr-1">
            {filteredModules.map((m) => {
              const isSelected = selectedId === m.id;
              const kbSize = (m.sizeBytes / 1024).toFixed(0);

              return (
                <div
                  key={m.id}
                  onClick={() => setSelectedId(m.id)}
                  className={`p-3 rounded-lg border transition cursor-pointer ${
                    isSelected
                      ? "bg-[var(--surface-3)] border-[var(--border-strong)] text-[var(--text-1)]"
                      : "bg-[var(--surface-1)] border-[var(--border)] text-[var(--text-2)] hover:bg-[var(--surface-2)] hover:text-[var(--text-1)]"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-3)] font-mono">
                      M{m.id}
                    </span>
                    <span className="text-[9.5px] text-[var(--text-3)]">{m.category}</span>
                  </div>
                  <h3 className="text-xs font-bold text-[var(--text-1)] mt-1 tracking-tight">
                    {m.title}
                  </h3>
                  <div className="flex items-center justify-between text-[10px] text-[var(--text-3)] mt-2 font-mono">
                    <span>{kbSize} KB</span>
                    <span>docs/tradesfera/{m.filename}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Reader View: Contenido del Manual */}
        <div className="lg:col-span-8">
          <div className="p-5 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg space-y-4 min-h-[680px]">
            {loadingDetail ? (
              <div className="p-12 text-center text-xs font-mono text-[var(--text-3)]">
                Cargando contenido del módulo M{selectedId}...
              </div>
            ) : selectedDetail ? (
              <div className="space-y-4">
                {/* Cabecera del lector */}
                <div className="border-b border-[var(--border)] pb-3 flex items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2 font-mono text-xs text-[var(--text-3)]">
                      <span className="px-1.5 py-0.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--profit)] font-bold">
                        MÓDULO M{selectedDetail.id}
                      </span>
                      <span>{selectedDetail.category}</span>
                    </div>
                    <h2 className="text-lg font-bold text-[var(--text-1)] tracking-tight mt-1">
                      {selectedDetail.title}
                    </h2>
                    <p className="text-[11px] font-mono text-[var(--text-3)] mt-0.5">
                      Fichero físico: <code>docs/tradesfera/{selectedDetail.filename}</code>
                    </p>
                  </div>
                </div>

                {/* Contenido en bloque legible con estilo de código/texto enriquecido */}
                <div className="font-mono text-xs text-[var(--text-2)] leading-relaxed whitespace-pre-wrap max-h-[600px] overflow-y-auto p-3.5 bg-[var(--surface-2)] rounded-md border border-[var(--border)]">
                  {selectedDetail.content}
                </div>
              </div>
            ) : (
              <div className="p-12 text-center text-xs font-mono text-[var(--text-3)]">
                Selecciona un manual del listado para comenzar la lectura.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
