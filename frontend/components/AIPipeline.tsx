"use client";

import { useEffect, useState } from "react";

const PIPELINE_STAGES = [
  {
    id: "read_jd",
    label: "Reading Job Description",
    sub: "Tokenizing and parsing input structure",
    duration: 900,
    icon: "📄",
  },
  {
    id: "intent",
    label: "Understanding Hiring Intent",
    sub: "Inferring role context, seniority, and team fit signals",
    duration: 1100,
    icon: "🧠",
  },
  {
    id: "role_dna",
    label: "Building Role DNA",
    sub: "Extracting skills, technologies, experience range, and behavioral signals",
    duration: 1200,
    icon: "🧬",
  },
  {
    id: "search",
    label: "Searching 100,000 Candidates",
    sub: "Filtering candidate pool from Redrob intelligence graph",
    duration: 1400,
    icon: "🔍",
  },
  {
    id: "embeddings",
    label: "Computing Semantic Embeddings",
    sub: "Running all-MiniLM-L6-v2 across candidate profiles",
    duration: 1600,
    icon: "⚡",
  },
  {
    id: "behavior",
    label: "Evaluating Behavioral Signals",
    sub: "Scoring engagement, responsiveness, and platform activity",
    duration: 1000,
    icon: "📊",
  },
  {
    id: "rank",
    label: "Ranking Candidates",
    sub: "Applying weighted composite scoring model",
    duration: 800,
    icon: "🏆",
  },
  {
    id: "insights",
    label: "Generating Recruiter Insights",
    sub: "Synthesising AI explanations for each top candidate",
    duration: 1300,
    icon: "✨",
  },
];

type Stage = {
  id: string;
  label: string;
  sub: string;
  duration: number;
  icon: string;
};

type StageStatus = "pending" | "running" | "done";

interface PipelineProps {
  onComplete: () => void;
}

export function AIPipeline({ onComplete }: PipelineProps) {
  const [stageStatuses, setStageStatuses] = useState<Record<string, StageStatus>>(
    Object.fromEntries(PIPELINE_STAGES.map((s) => [s.id, "pending"]))
  );
  const [currentStageIndex, setCurrentStageIndex] = useState(0);
  const [particles, setParticles] = useState<{ id: number; x: number; y: number; size: number; speed: number }[]>([]);
  const [tick, setTick] = useState(0);
  const [globalProgress, setGlobalProgress] = useState(0);

  // Generate floating particles
  useEffect(() => {
    const ps = Array.from({ length: 30 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: Math.random() * 3 + 1,
      speed: Math.random() * 0.3 + 0.1,
    }));
    setParticles(ps);
  }, []);

  // Animate particles
  useEffect(() => {
    const interval = setInterval(() => setTick((t) => t + 1), 50);
    return () => clearInterval(interval);
  }, []);

  // Stage progression
  useEffect(() => {
    if (currentStageIndex >= PIPELINE_STAGES.length) {
      setTimeout(onComplete, 400);
      return;
    }

    const stage = PIPELINE_STAGES[currentStageIndex];

    setStageStatuses((prev) => ({ ...prev, [stage.id]: "running" }));

    const totalDuration = PIPELINE_STAGES.reduce((acc, s) => acc + s.duration, 0);
    const doneTime = PIPELINE_STAGES.slice(0, currentStageIndex).reduce((acc, s) => acc + s.duration, 0);

    // Animate global progress through this stage
    const startTime = Date.now();
    const progressInterval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const ratio = Math.min(elapsed / stage.duration, 1);
      const stageProgress = (doneTime + elapsed) / totalDuration;
      setGlobalProgress(Math.min(stageProgress * 100, 100));
      if (ratio >= 1) clearInterval(progressInterval);
    }, 30);

    const timer = setTimeout(() => {
      setStageStatuses((prev) => ({ ...prev, [stage.id]: "done" }));
      clearInterval(progressInterval);
      setCurrentStageIndex((i) => i + 1);
    }, stage.duration);

    return () => {
      clearTimeout(timer);
      clearInterval(progressInterval);
    };
  }, [currentStageIndex, onComplete]);

  const completedCount = PIPELINE_STAGES.filter((s) => stageStatuses[s.id] === "done").length;

  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-[#050508] overflow-hidden select-none">
      {/* Ambient background orbs */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full bg-violet-600/10 blur-3xl animate-pulse" />
        <div className="absolute bottom-1/3 right-1/4 w-80 h-80 rounded-full bg-cyan-500/8 blur-3xl animate-pulse" style={{ animationDelay: "1.2s" }} />
        <div className="absolute top-1/2 left-1/2 w-64 h-64 -translate-x-1/2 -translate-y-1/2 rounded-full bg-indigo-500/5 blur-2xl animate-pulse" style={{ animationDelay: "0.6s" }} />
      </div>

      {/* Floating particles */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        {particles.map((p) => (
          <div
            key={p.id}
            className="absolute rounded-full bg-violet-400/20"
            style={{
              width: p.size,
              height: p.size,
              left: `${(p.x + tick * p.speed * 0.1) % 100}%`,
              top: `${(p.y + tick * p.speed * 0.05) % 100}%`,
              transition: "left 0.1s linear, top 0.1s linear",
            }}
          />
        ))}
      </div>

      <div className="relative z-10 w-full max-w-2xl px-6 flex flex-col items-center gap-10">
        {/* Logo + header */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-300 text-xs font-mono tracking-widest uppercase mb-2">
            <span className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-pulse" />
            Helios Intelligence Engine
          </div>
          <h1 className="text-3xl font-semibold text-white tracking-tight">
            Analysing your role
          </h1>
          <p className="text-sm text-gray-500">
            Running {PIPELINE_STAGES.length} intelligence stages across your candidate pool
          </p>
        </div>

        {/* Global progress bar */}
        <div className="w-full space-y-2">
          <div className="flex justify-between text-xs text-gray-600 font-mono">
            <span>{completedCount}/{PIPELINE_STAGES.length} stages</span>
            <span>{Math.round(globalProgress)}%</span>
          </div>
          <div className="h-px w-full bg-white/5 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-violet-500 via-indigo-400 to-cyan-400 rounded-full transition-all duration-300 ease-out"
              style={{ width: `${globalProgress}%` }}
            />
          </div>
        </div>

        {/* Pipeline stages */}
        <div className="w-full space-y-1">
          {PIPELINE_STAGES.map((stage, i) => {
            const status = stageStatuses[stage.id];
            const isRunning = status === "running";
            const isDone = status === "done";
            const isPending = status === "pending";

            return (
              <div
                key={stage.id}
                className={`
                  relative flex items-center gap-4 px-4 py-3 rounded-xl transition-all duration-500
                  ${isRunning ? "bg-violet-500/8 border border-violet-500/20" : "border border-transparent"}
                  ${isDone ? "opacity-50" : ""}
                  ${isPending ? "opacity-25" : ""}
                `}
              >
                {/* Status indicator */}
                <div className="flex-shrink-0 w-7 h-7 flex items-center justify-center">
                  {isDone && (
                    <div className="w-5 h-5 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center">
                      <svg className="w-3 h-3 text-emerald-400" fill="none" viewBox="0 0 12 12">
                        <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    </div>
                  )}
                  {isRunning && (
                    <div className="relative w-5 h-5">
                      <div className="absolute inset-0 rounded-full border border-violet-500/30 animate-ping" />
                      <div className="absolute inset-0 rounded-full border border-violet-400 animate-spin" style={{ borderTopColor: "transparent", borderRightColor: "transparent" }} />
                    </div>
                  )}
                  {isPending && (
                    <div className="w-5 h-5 rounded-full border border-white/10" />
                  )}
                </div>

                {/* Icon */}
                <span className="text-base">{stage.icon}</span>

                {/* Text */}
                <div className="flex-1 min-w-0">
                  <div className={`text-sm font-medium transition-colors duration-300 ${isRunning ? "text-white" : isDone ? "text-gray-400" : "text-gray-600"}`}>
                    {stage.label}
                  </div>
                  {isRunning && (
                    <div className="text-xs text-violet-400/70 mt-0.5 animate-fade-in">
                      {stage.sub}
                    </div>
                  )}
                </div>

                {/* Running shimmer line */}
                {isRunning && (
                  <div className="absolute bottom-0 left-4 right-4 h-px overflow-hidden">
                    <div className="h-full w-1/3 bg-gradient-to-r from-transparent via-violet-400/50 to-transparent animate-shimmer" />
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Bottom label */}
        <p className="text-xs text-gray-700 font-mono tracking-wide animate-pulse">
          Powered by Redrob × Helios Intelligence
        </p>
      </div>

      <style>{`
        @keyframes shimmer {
          from { transform: translateX(-200%); }
          to { transform: translateX(600%); }
        }
        .animate-shimmer {
          animation: shimmer 1.6s ease-in-out infinite;
        }
        @keyframes fade-in {
          from { opacity: 0; transform: translateY(2px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in {
          animation: fade-in 0.25s ease-out;
        }
      `}</style>
    </div>
  );
}
