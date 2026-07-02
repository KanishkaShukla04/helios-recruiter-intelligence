"use client";

import { useState, useRef, useEffect } from "react";
import { AIPipeline } from "@/components/AIPipeline";
import { CandidateCard } from "@/components/CandidateCard";

// ---------------------------------------------------------------------------
// Mock data for demo (replace with actual API calls)
// ---------------------------------------------------------------------------

const MOCK_CANDIDATES = [
  {
    id: "c1",
    name: "Priya Sharma",
    current_title: "Senior ML Engineer",
    current_company: "Flipkart AI Labs",
    years_experience: 6.8,
    skills: ["python", "pytorch", "faiss", "rag", "kubernetes", "aws", "mlflow"],
    location: "Bangalore",
    notice_period_days: 30,
    total_score: 87.4,
    semantic_score: 89.2,
    behavior_score: 84.5,
    fit_label: "Strong Fit",
    confidence: 0.91,
    explanation:
      "Priya is a strong fit — 6.8 years building production ML systems, extensive RAG and retrieval experience, strong GitHub activity, and high recruiter responsiveness. Main concern is a 30-day notice period.",
    strengths: [
      "6.8y meets the 4+ year requirement",
      "skill match on pytorch, faiss, rag, kubernetes, aws",
      "strong GitHub activity score (78/100)",
      "high recruiter engagement and responsiveness",
    ],
    concerns: ["30-day notice period"],
    open_to_work_flag: true,
  },
  {
    id: "c2",
    name: "Arjun Mehta",
    current_title: "ML Platform Engineer",
    current_company: "Swiggy",
    years_experience: 5.2,
    skills: ["python", "pytorch", "kafka", "airflow", "databricks", "mlflow", "aws"],
    location: "Bangalore",
    notice_period_days: 45,
    total_score: 81.1,
    semantic_score: 78.9,
    behavior_score: 84.3,
    fit_label: "Strong Fit",
    confidence: 0.84,
    explanation:
      "Arjun brings 5.2 years of production ML platform experience with strong tooling overlap including MLflow, Airflow, and Databricks. High platform engagement score. 45-day notice is the primary consideration.",
    strengths: [
      "5.2y meets the 4+ year requirement",
      "currently ML Platform Engineer at Swiggy",
      "skill match on pytorch, kafka, mlflow, aws",
      "high recruiter engagement and responsiveness",
    ],
    concerns: ["45-day notice period"],
    open_to_work_flag: true,
  },
  {
    id: "c3",
    name: "Riya Nair",
    current_title: "Staff Data Scientist",
    current_company: "PhonePe",
    years_experience: 8.1,
    skills: ["python", "xgboost", "spark", "sql", "bigquery", "scikit-learn"],
    location: "Bangalore",
    notice_period_days: 60,
    total_score: 68.3,
    semantic_score: 72.1,
    behavior_score: 62.7,
    fit_label: "Good Fit",
    confidence: 0.72,
    explanation:
      "Riya has strong data science foundations with 8.1 years of experience, good overlap on Python and Spark. However, limited deep learning / LLM stack exposure reduces semantic alignment. 60-day notice period.",
    strengths: [
      "8.1y meets the 4+ year requirement",
      "skill match on python, spark, sql",
      "currently Staff Data Scientist at PhonePe",
    ],
    concerns: [
      "limited technology overlap with deep learning stack",
      "60-day notice period",
      "low GitHub activity (22/100)",
    ],
    open_to_work_flag: false,
  },
  {
    id: "c4",
    name: "Karan Bhatia",
    current_title: "NLP Engineer",
    current_company: "Sarvam AI",
    years_experience: 4.0,
    skills: ["python", "transformers", "huggingface", "pytorch", "qdrant", "fastapi"],
    location: "Remote",
    notice_period_days: 0,
    total_score: 79.6,
    semantic_score: 84.7,
    behavior_score: 71.3,
    fit_label: "Strong Fit",
    confidence: 0.79,
    explanation:
      "Karan's transformer and retrieval expertise (HuggingFace, Qdrant) closely aligns with the semantic search requirements. Immediate availability is a strong plus. 4 years just meets the minimum — seniority trajectory to verify.",
    strengths: [
      "skill match on transformers, huggingface, pytorch, qdrant",
      "immediately available",
      "strong semantic alignment with JD (84.7/100)",
      "actively seeking new opportunities",
    ],
    concerns: ["4y experience at minimum threshold"],
    open_to_work_flag: true,
  },
  {
    id: "c5",
    name: "Divya Krishnan",
    current_title: "Backend Engineer",
    current_company: "Razorpay",
    years_experience: 3.5,
    skills: ["python", "golang", "postgresql", "redis", "kubernetes", "grpc"],
    location: "Hyderabad",
    notice_period_days: 30,
    total_score: 42.8,
    semantic_score: 38.4,
    behavior_score: 49.2,
    fit_label: "Weak Fit",
    confidence: 0.61,
    explanation:
      "Divya is primarily a backend systems engineer without ML-specific experience. Golang and systems work does not match the ML/LLM requirements. 3.5 years is below the experience floor.",
    strengths: ["strong platform engagement"],
    concerns: [
      "limited technology overlap with JD requirements",
      "3.5y is below the 4+ year requirement",
      "no ML or LLM stack experience",
    ],
    open_to_work_flag: false,
  },
];

const SAMPLE_JD = `Senior Machine Learning Engineer — Search & Retrieval

We are looking for a Senior ML Engineer to join our Search Intelligence team in Bangalore (hybrid). You will build and scale production retrieval systems serving 50M+ daily queries.

Requirements
- 4–8 years of professional experience in machine learning or software engineering
- Strong Python skills with PyTorch or TensorFlow
- Hands-on experience with vector databases: Faiss, Pinecone, or Weaviate
- Production-level experience deploying models on AWS or GCP using Kubernetes
- Experience building RAG or semantic search pipelines

Nice to Have
- LangChain or LlamaIndex experience
- MLflow or Weights & Biases
- Open-source ML contributions

We are a fast-paced, mission-driven team. We value ownership, bias toward action, and data-driven decisions.`;

// ---------------------------------------------------------------------------
// Stats bar
// ---------------------------------------------------------------------------
function StatBar({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-2xl font-bold text-white tabular-nums">{value}</span>
      <span className="text-xs text-gray-600 uppercase tracking-wider">{label}</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------
export default function Home() {
  const [jdText, setJdText] = useState("");
  const [phase, setPhase] = useState<"hero" | "pipeline" | "results">("hero");
  const [candidates, setCandidates] = useState(MOCK_CANDIDATES);
  const [jdCharCount, setJdCharCount] = useState(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  const handleJdChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setJdText(e.target.value);
    setJdCharCount(e.target.value.length);
  };

  const handleAnalyse = () => {
    if (!jdText.trim() || jdText.length < 50) return;
    setPhase("pipeline");
  };

  const handlePipelineComplete = () => {
    setPhase("results");
    setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
  };

  const handleUseSample = () => {
    setJdText(SAMPLE_JD);
    setJdCharCount(SAMPLE_JD.length);
    textareaRef.current?.focus();
  };

  const topScore = candidates[0]?.total_score ?? 0;
  const strongFits = candidates.filter((c) => c.total_score >= 75).length;

  return (
    <div className="min-h-screen bg-[#050508] text-white font-sans">
      {/* AI Pipeline overlay */}
      {phase === "pipeline" && <AIPipeline onComplete={handlePipelineComplete} />}

      {/* ─── Hero ─── */}
      <section className="relative min-h-screen flex flex-col items-center justify-center px-6 overflow-hidden">
        {/* Background */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[700px] h-[400px] bg-violet-600/8 blur-[120px] rounded-full" />
          <div className="absolute bottom-0 right-0 w-[400px] h-[300px] bg-indigo-500/6 blur-[100px] rounded-full" />
          {/* Grid */}
          <div
            className="absolute inset-0 opacity-[0.025]"
            style={{
              backgroundImage: `linear-gradient(rgba(139,92,246,0.4) 1px, transparent 1px), linear-gradient(90deg, rgba(139,92,246,0.4) 1px, transparent 1px)`,
              backgroundSize: "60px 60px",
            }}
          />
        </div>

        <div className="relative z-10 w-full max-w-4xl mx-auto text-center space-y-8">
          {/* Eyebrow */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-300 text-xs font-mono tracking-widest uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Redrob Data & AI Challenge 2025
          </div>

          {/* Headline */}
          <div>
            <h1 className="text-6xl md:text-7xl font-bold tracking-tight leading-[0.95] mb-4">
              <span className="text-white">Helios</span>
              <br />
              <span className="bg-gradient-to-r from-violet-400 via-indigo-300 to-cyan-300 bg-clip-text text-transparent">
                Recruiter Intelligence
              </span>
            </h1>
            <p className="text-gray-400 text-lg max-w-xl mx-auto leading-relaxed">
              Paste a job description. Watch AI rank your entire candidate pool by semantic alignment and behavioral fit — in seconds.
            </p>
          </div>

          {/* Stats */}
          <div className="flex items-center justify-center gap-10 py-4">
            <StatBar label="Candidates scored" value="100K+" />
            <div className="w-px h-10 bg-white/10" />
            <StatBar label="Scoring signals" value="12" />
            <div className="w-px h-10 bg-white/10" />
            <StatBar label="Avg rank time" value="<3s" />
          </div>

          {/* JD Input */}
          <div className="relative">
            <div className="relative rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-sm overflow-hidden focus-within:border-violet-500/40 transition-colors duration-300 shadow-[0_0_60px_rgba(139,92,246,0.05)]">
              <textarea
                ref={textareaRef}
                value={jdText}
                onChange={handleJdChange}
                placeholder="Paste your job description here — the AI will extract role requirements, analyse 100K candidates, and surface the best fits with explainable reasoning…"
                className="w-full bg-transparent text-gray-200 placeholder-gray-600 text-sm leading-relaxed p-5 pb-14 outline-none resize-none min-h-[180px] max-h-[340px]"
                style={{ scrollbarWidth: "thin", scrollbarColor: "rgba(139,92,246,0.3) transparent" }}
              />

              {/* Bottom bar inside textarea */}
              <div className="absolute bottom-0 left-0 right-0 flex items-center justify-between px-4 py-3 bg-gradient-to-t from-black/30 to-transparent border-t border-white/5">
                <div className="flex items-center gap-3">
                  <span className="text-xs text-gray-600 font-mono">{jdCharCount} chars</span>
                  <button
                    onClick={handleUseSample}
                    className="text-xs text-violet-400/70 hover:text-violet-300 transition-colors"
                  >
                    Use sample JD →
                  </button>
                </div>

                <button
                  onClick={handleAnalyse}
                  disabled={jdText.length < 50}
                  className={`
                    flex items-center gap-2 px-5 py-2 rounded-xl text-sm font-semibold transition-all duration-200
                    ${jdText.length >= 50
                      ? "bg-violet-600 hover:bg-violet-500 text-white shadow-[0_0_20px_rgba(139,92,246,0.3)] hover:shadow-[0_0_30px_rgba(139,92,246,0.45)] scale-100 hover:scale-[1.02]"
                      : "bg-white/5 text-gray-600 cursor-not-allowed"
                    }
                  `}
                >
                  <span>Analyse Role</span>
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 16 16">
                    <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </button>
              </div>
            </div>

            {jdText.length >= 50 && jdText.length < 100 && (
              <p className="mt-2 text-xs text-amber-400/60 text-left pl-1">
                Add more context for better results
              </p>
            )}
          </div>
        </div>
      </section>

      {/* ─── Results ─── */}
      {phase === "results" && (
        <section ref={resultsRef} className="px-6 py-16 max-w-4xl mx-auto">
          {/* Results header */}
          <div className="mb-8">
            <div className="flex items-start justify-between flex-wrap gap-4">
              <div>
                <h2 className="text-2xl font-bold text-white">Ranking Complete</h2>
                <p className="text-sm text-gray-500 mt-1">
                  {candidates.length} candidates processed · {strongFits} strong fits identified
                </p>
              </div>
              <div className="flex items-center gap-3">
                <div className="px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                  <span className="text-xs text-emerald-300 font-mono">
                    Top score: {topScore.toFixed(1)}%
                  </span>
                </div>
                <button
                  onClick={() => { setPhase("hero"); setJdText(""); setJdCharCount(0); }}
                  className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-xs text-gray-400 hover:text-white hover:border-white/20 transition-colors"
                >
                  New search
                </button>
              </div>
            </div>

            {/* Score distribution */}
            <div className="mt-5 p-4 rounded-xl bg-white/[0.02] border border-white/5">
              <div className="text-xs text-gray-600 uppercase tracking-wider mb-3">Score Distribution</div>
              <div className="flex items-end gap-1 h-12">
                {candidates.map((c) => (
                  <div
                    key={c.id}
                    className="flex-1 rounded-sm bg-violet-500/20 hover:bg-violet-500/40 transition-colors cursor-default"
                    style={{ height: `${c.total_score}%` }}
                    title={`${c.name}: ${c.total_score.toFixed(1)}`}
                  />
                ))}
              </div>
              <div className="flex justify-between text-[10px] text-gray-700 mt-1">
                <span>0</span>
                <span>100</span>
              </div>
            </div>
          </div>

          {/* Candidate cards */}
          <div className="space-y-3">
            {candidates
              .sort((a, b) => b.total_score - a.total_score)
              .map((candidate, i) => (
                <div
                  key={candidate.id}
                  style={{ animationDelay: `${i * 60}ms` }}
                  className="animate-slide-up"
                >
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-6 text-right mt-5">
                      <span className="text-xs font-mono text-gray-700">#{i + 1}</span>
                    </div>
                    <div className="flex-1">
                      <CandidateCard candidate={candidate} rank={i + 1} />
                    </div>
                  </div>
                </div>
              ))}
          </div>

          <p className="mt-8 text-center text-xs text-gray-700">
            Powered by Redrob Intelligence · Helios v1.0
          </p>
        </section>
      )}

      <style>{`
        @keyframes slide-up {
          from { opacity: 0; transform: translateY(16px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-slide-up {
          animation: slide-up 0.4s ease-out both;
        }
      `}</style>
    </div>
  );
}
