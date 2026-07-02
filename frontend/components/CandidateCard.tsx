"use client";

import { useState } from "react";

interface Candidate {
  id: string;
  name: string;
  current_title?: string;
  current_company?: string;
  years_experience?: number;
  skills: string[];
  location?: string;
  notice_period_days?: number;
  total_score: number;
  semantic_score: number;
  behavior_score: number;
  fit_label: string;
  confidence: number;
  explanation?: string;
  strengths: string[];
  concerns: string[];
  open_to_work_flag?: boolean;
}

interface CandidateCardProps {
  candidate: Candidate;
  rank: number;
}

function ScoreRing({ value, label, color }: { value: number; label: string; color: string }) {
  const radius = 20;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative w-14 h-14">
        <svg className="w-14 h-14 -rotate-90" viewBox="0 0 56 56">
          <circle cx="28" cy="28" r={radius} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="3" />
          <circle
            cx="28"
            cy="28"
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth="3"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            style={{ transition: "stroke-dashoffset 1s ease-out" }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-xs font-bold text-white">{Math.round(value)}</span>
        </div>
      </div>
      <span className="text-[10px] text-gray-500 font-medium tracking-wide uppercase">{label}</span>
    </div>
  );
}

function FitBadge({ label }: { label: string }) {
  const colors: Record<string, string> = {
    "Strong Fit": "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
    "Good Fit": "bg-blue-500/15 text-blue-300 border-blue-500/30",
    "Partial Fit": "bg-amber-500/15 text-amber-300 border-amber-500/30",
    "Weak Fit": "bg-red-500/15 text-red-400 border-red-500/30",
  };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${colors[label] ?? "bg-gray-500/15 text-gray-300 border-gray-500/30"}`}>
      {label}
    </span>
  );
}

export function CandidateCard({ candidate, rank }: CandidateCardProps) {
  const [expanded, setExpanded] = useState(false);

  const matchPercent = Math.round(candidate.total_score);

  return (
    <div
      className={`
        group relative rounded-2xl border transition-all duration-300 cursor-pointer overflow-hidden
        bg-gradient-to-b from-white/[0.04] to-white/[0.01]
        backdrop-blur-sm
        ${expanded
          ? "border-violet-500/30 shadow-[0_0_40px_rgba(139,92,246,0.08)]"
          : "border-white/[0.07] hover:border-white/[0.14] hover:shadow-[0_0_30px_rgba(139,92,246,0.06)]"
        }
      `}
      onClick={() => setExpanded(!expanded)}
    >
      {/* Rank indicator */}
      <div className="absolute top-0 left-0 w-px h-full bg-gradient-to-b from-violet-500/50 via-violet-500/20 to-transparent" />

      <div className="p-5">
        {/* Header row */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            {/* Avatar */}
            <div className="relative flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500/30 to-indigo-500/20 border border-white/10 flex items-center justify-center">
              <span className="text-sm font-bold text-violet-300">
                {candidate.name.split(" ").map((n) => n[0]).join("").slice(0, 2)}
              </span>
              {candidate.open_to_work_flag && (
                <div className="absolute -bottom-1 -right-1 w-3.5 h-3.5 rounded-full bg-emerald-500 border-2 border-[#050508] flex items-center justify-center">
                  <div className="w-1.5 h-1.5 rounded-full bg-white" />
                </div>
              )}
            </div>

            {/* Name + role */}
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="text-sm font-semibold text-white">{candidate.name}</h3>
                <FitBadge label={candidate.fit_label} />
              </div>
              <p className="text-xs text-gray-400 mt-0.5">
                {[candidate.current_title, candidate.current_company]
                  .filter(Boolean)
                  .join(" · ")}
              </p>
            </div>
          </div>

          {/* Match score */}
          <div className="flex-shrink-0 text-right">
            <div className="text-2xl font-bold text-white tabular-nums">{matchPercent}
              <span className="text-sm text-gray-500 font-normal">%</span>
            </div>
            <div className="text-[10px] text-gray-600 uppercase tracking-wider">match</div>
          </div>
        </div>

        {/* Meta row */}
        <div className="flex flex-wrap gap-x-4 gap-y-1 mt-3 text-xs text-gray-500">
          {candidate.years_experience != null && (
            <span className="flex items-center gap-1">
              <svg className="w-3 h-3" fill="none" viewBox="0 0 12 12"><circle cx="6" cy="6" r="5" stroke="currentColor" strokeWidth="1.2" /><path d="M6 3.5v2.5l1.5 1.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" /></svg>
              {candidate.years_experience}y exp
            </span>
          )}
          {candidate.location && (
            <span className="flex items-center gap-1">
              <svg className="w-3 h-3" fill="none" viewBox="0 0 12 12"><path d="M6 1C4.343 1 3 2.343 3 4c0 2.5 3 7 3 7s3-4.5 3-7c0-1.657-1.343-3-3-3z" stroke="currentColor" strokeWidth="1.2" /><circle cx="6" cy="4" r="1" stroke="currentColor" strokeWidth="1.2" /></svg>
              {candidate.location}
            </span>
          )}
          {candidate.notice_period_days != null && (
            <span className="flex items-center gap-1">
              <svg className="w-3 h-3" fill="none" viewBox="0 0 12 12"><rect x="1" y="2" width="10" height="9" rx="1.5" stroke="currentColor" strokeWidth="1.2" /><path d="M4 1v2M8 1v2M1 5h10" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" /></svg>
              {candidate.notice_period_days === 0 ? "Immediate" : `${candidate.notice_period_days}d notice`}
            </span>
          )}
          <span className="flex items-center gap-1 ml-auto">
            Confidence: {Math.round(candidate.confidence * 100)}%
          </span>
        </div>

        {/* Score rings */}
        <div className="flex items-center gap-4 mt-4 pt-4 border-t border-white/5">
          <ScoreRing value={candidate.total_score} label="Overall" color="#8b5cf6" />
          <ScoreRing value={candidate.semantic_score} label="Semantic" color="#6366f1" />
          <ScoreRing value={candidate.behavior_score} label="Behavior" color="#06b6d4" />

          {/* Skills */}
          <div className="flex-1 flex flex-wrap gap-1.5 pl-2">
            {candidate.skills.slice(0, 6).map((skill) => (
              <span
                key={skill}
                className="px-2 py-0.5 rounded-md bg-white/5 border border-white/8 text-[11px] text-gray-400 font-mono"
              >
                {skill}
              </span>
            ))}
            {candidate.skills.length > 6 && (
              <span className="px-2 py-0.5 rounded-md bg-white/5 border border-white/8 text-[11px] text-gray-600 font-mono">
                +{candidate.skills.length - 6}
              </span>
            )}
          </div>
        </div>

        {/* Expanded: reasoning panel */}
        {expanded && (
          <div className="mt-4 pt-4 border-t border-white/5 space-y-4 animate-fade-in">
            {/* AI Reasoning */}
            {candidate.explanation && (
              <div className="rounded-xl bg-violet-500/5 border border-violet-500/15 p-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-4 h-4 rounded-full bg-violet-500/20 border border-violet-500/40 flex items-center justify-center">
                    <span className="text-[8px]">✨</span>
                  </div>
                  <span className="text-xs font-medium text-violet-300 uppercase tracking-wider">AI Reasoning</span>
                </div>
                <p className="text-sm text-gray-300 leading-relaxed">{candidate.explanation}</p>
              </div>
            )}

            {/* Strengths & Concerns */}
            <div className="grid grid-cols-2 gap-3">
              {candidate.strengths.length > 0 && (
                <div>
                  <div className="text-[10px] font-medium text-emerald-400 uppercase tracking-wider mb-2">Strengths</div>
                  <ul className="space-y-1.5">
                    {candidate.strengths.slice(0, 4).map((s, i) => (
                      <li key={i} className="flex items-start gap-1.5 text-xs text-gray-400">
                        <span className="text-emerald-500 flex-shrink-0 mt-0.5">+</span>
                        {s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {candidate.concerns.length > 0 && (
                <div>
                  <div className="text-[10px] font-medium text-amber-400 uppercase tracking-wider mb-2">Concerns</div>
                  <ul className="space-y-1.5">
                    {candidate.concerns.slice(0, 3).map((c, i) => (
                      <li key={i} className="flex items-start gap-1.5 text-xs text-gray-400">
                        <span className="text-amber-500 flex-shrink-0 mt-0.5">—</span>
                        {c}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Semantic similarity bar */}
            <div>
              <div className="flex justify-between text-[10px] text-gray-600 mb-1.5">
                <span className="uppercase tracking-wider">Semantic Similarity</span>
                <span className="font-mono">{candidate.semantic_score.toFixed(1)}%</span>
              </div>
              <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-indigo-500 to-violet-400 rounded-full transition-all duration-700"
                  style={{ width: `${candidate.semantic_score}%` }}
                />
              </div>
            </div>
          </div>
        )}

        {/* Expand hint */}
        <div className={`mt-3 flex items-center justify-center text-gray-700 transition-transform duration-300 ${expanded ? "rotate-180" : ""}`}>
          <svg className="w-4 h-4" fill="none" viewBox="0 0 16 16">
            <path d="M4 6l4 4 4-4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
      </div>

      <style>{`
        @keyframes fade-in { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }
        .animate-fade-in { animation: fade-in 0.25s ease-out; }
      `}</style>
    </div>
  );
}
