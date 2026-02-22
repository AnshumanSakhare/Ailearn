"use client";

import { Brain, Github } from "lucide-react";

export default function Navbar({ title }: { title?: string }) {
  return (
    <nav className="sticky top-0 z-50 border-b border-slate-800 bg-slate-900/80 backdrop-blur">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-1.5 rounded-xl bg-brand-600">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <span className="font-bold text-xl text-white tracking-tight">
            AI Learning Assistant
          </span>
          {title && (
            <span className="hidden sm:inline text-slate-500 text-sm ml-2 truncate max-w-[200px]">
              — {title}
            </span>
          )}
        </div>
        <a
          href="https://github.com"
          target="_blank"
          rel="noreferrer"
          className="btn-ghost text-sm"
        >
          <Github className="w-4 h-4" />
          <span className="hidden sm:inline">GitHub</span>
        </a>
      </div>
    </nav>
  );
}
