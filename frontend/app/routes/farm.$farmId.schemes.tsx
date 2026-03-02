/**
 * Government Schemes & Subsidies Route — User Story 5 (P3)
 *
 * - Loader is LAZY: does NOT call the backend, so navigating here never
 *   triggers an LLM scan.
 * - On mount, a cache-only check is fired via useFetcher (_intent=load_cache).
 *   This returns immediately if a 7-day cached result exists in Supabase.
 * - "Scan for Schemes" button submits _intent=refresh which runs the LLM.
 * - LLM explanation is rendered as formatted JSX (not raw markdown).
 */

import type { ActionFunctionArgs, LoaderFunctionArgs, MetaFunction } from "@remix-run/node";
import { json } from "@remix-run/node";
import {
  useFetcher,
  useLoaderData,
  useOutletContext,
  useSearchParams,
} from "@remix-run/react";
import { type ElementType, useEffect, useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  BookOpen,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  ClipboardList,
  ExternalLink,
  FileText,
  IndianRupee,
  ListOrdered,
  RefreshCw,
  Shield,
  Sprout,
} from "lucide-react";
import { ConfidenceBar } from "~/components/recommendations/ConfidenceBar";

// ─── Types ────────────────────────────────────────────────────────────────────

interface SchemeItem {
  scheme_id: string;
  name: string;
  authority: string;
  type: string;
  benefit: string;
  description?: string;
  action_plan?: string[];
  eligibility_explanation: string;
  required_documents: string[];
  apply_link: string;
  application_portal: string;
  deadline: string;
  confidence: number;
  tags: string[];
}

interface SchemeMatchData {
  state: string;
  district?: string;
  crops: string[];
  area_acres?: number;
  farmer_category: string;
  schemes: SchemeItem[];
  total_matched: number;
  top_scheme_ids: string[];
  scan_timestamp: string;
}

interface SchemesResponse {
  success: boolean;
  data?: SchemeMatchData;
  metadata?: {
    timestamp: string;
    response_time_ms: number;
    cached: boolean;
    cached_at?: string;
    expires_at?: string;
    confidence: number;
    explanation: string;
    model_version: string;
    human_review_required: boolean;
    tool_calls_count: number;
  };
  error?: string;
}

interface OutletContext {
  farmId: string;
  farmName: string;
  district: string | null;
  mainCrop: string | null;
  areaAcres: number | null;
  lat: number | null;
  lon: number | null;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const BACKEND_URL =
  typeof process !== "undefined"
    ? process.env.BACKEND_URL || "http://farmops-backend-dev:8000"
    : "";

const TYPE_COLORS: Record<string, string> = {
  subsidy:       "bg-green-100 text-green-800",
  insurance:     "bg-blue-100 text-blue-800",
  credit:        "bg-purple-100 text-purple-800",
  price_support: "bg-orange-100 text-orange-800",
  input_support: "bg-yellow-100 text-yellow-800",
  technology:    "bg-teal-100 text-teal-800",
  training:      "bg-pink-100 text-pink-800",
};

const TYPE_ICONS: Record<string, ElementType> = {
  subsidy:       IndianRupee,
  insurance:     Shield,
  credit:        IndianRupee,
  price_support: IndianRupee,
  input_support: Sprout,
  technology:    BookOpen,
  training:      BookOpen,
};

function acresToCategory(acres: number): string {
  const ha = acres * 0.404686;
  if (ha < 1)  return "marginal";
  if (ha < 2)  return "small";
  if (ha < 10) return "medium";
  return "large";
}

function formatTs(ts?: string): string {
  if (!ts) return "Unknown";
  const d = new Date(ts);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

// ─── Meta ─────────────────────────────────────────────────────────────────────

export const meta: MetaFunction = () => [
  { title: "Government Schemes & Subsidies - FarmOps" },
  { name: "description", content: "Eligible government schemes and subsidies for your farm" },
];

// ─── Loader — lazy, no backend call on navigation ────────────────────────────

export async function loader({ params, request }: LoaderFunctionArgs) {
  const farmId    = params.farmId || "00000000-0000-0000-0000-000000000000";
  const url       = new URL(request.url);
  const district  = url.searchParams.get("district")  ?? null;
  const mainCrop  = url.searchParams.get("main_crop") ?? null;
  const areaAcres = parseFloat(url.searchParams.get("area_acres") ?? "0") || null;
  return json({ farmId, district, mainCrop, areaAcres });
}

// ─── Action — _intent=load_cache (fast) or _intent=refresh (LLM) ─────────────

export async function action({ request, params }: ActionFunctionArgs) {
  const farmId   = params.farmId || "00000000-0000-0000-0000-000000000000";
  const formData = await request.formData();
  const intent   = (formData.get("_intent") as string) || "refresh";

  const district       = (formData.get("district")   as string) || null;
  const mainCrop       = (formData.get("main_crop")  as string) || null;
  const areaAcres      = parseFloat((formData.get("area_acres") as string) || "0") || null;
  const farmerCategory = areaAcres ? acresToCategory(areaAcres) : "small";

  try {
    if (intent === "load_cache") {
      const qp = new URLSearchParams({
        farm_id:         farmId,
        state:           "Tamil Nadu",
        farmer_category: farmerCategory,
        force_refresh:   "false",
      });
      if (district)  qp.set("district",   district);
      if (mainCrop)  qp.set("crops",      mainCrop);
      if (areaAcres) qp.set("area_acres", String(areaAcres));
      const res = await fetch(`${BACKEND_URL}/api/v1/farm/schemes?${qp.toString()}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return json(await res.json() as SchemesResponse);
    }
    // intent === "refresh" — run fresh LLM scan
    const res = await fetch(`${BACKEND_URL}/api/v1/farm/schemes/refresh`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        farm_id:         farmId,
        state:           "Tamil Nadu",
        district,
        crops:           mainCrop ? [mainCrop] : [],
        area_acres:      areaAcres,
        farmer_category: farmerCategory,
        language:        "en",
      }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return json(await res.json() as SchemesResponse);
  } catch (err) {
    return json({ success: false, error: err instanceof Error ? err.message : "Request failed" } as SchemesResponse);
  }
}

// ─── ExplanationBlock — renders LLM text without raw markdown ─────────────────

function ExplanationBlock({ text }: { text: string }) {
  if (!text.trim()) return null;
  const nodes: JSX.Element[] = [];
  let k = 0;
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    if (!line) { k++; continue; }
    if (/^#{1,3}\s+/.test(line)) {
      const content = line.replace(/^#{1,3}\s+/, "").replace(/\*\*/g, "");
      nodes.push(<p key={k++} className="font-bold text-amber-900 text-sm mt-3 mb-1">{content}</p>);
      continue;
    }
    if (/^---+$/.test(line)) {
      nodes.push(<hr key={k++} className="border-amber-200 my-2" />);
      continue;
    }
    if (/^[-*•]\s+/.test(line) || /^\d+\.\s+/.test(line)) {
      const content = line.replace(/^[-*•\d.]+\s+/, "");
      const html = content.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
      nodes.push(
        <div key={k++} className="flex items-start gap-1.5 text-sm text-amber-900">
          <CheckCircle2 className="w-3.5 h-3.5 mt-0.5 text-amber-600 shrink-0" />
          <span dangerouslySetInnerHTML={{ __html: html }} />
        </div>
      );
      continue;
    }
    const html = line.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    nodes.push(
      <p key={k++} className="text-sm text-amber-900 leading-relaxed"
        dangerouslySetInnerHTML={{ __html: html }} />
    );
  }
  return <div className="space-y-1">{nodes}</div>;
}

// ─── Scheme Card ──────────────────────────────────────────────────────────────

function SchemeCard({ scheme, isTop }: { scheme: SchemeItem; isTop: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const TypeIcon = TYPE_ICONS[scheme.type] || Shield;
  const typeColor = TYPE_COLORS[scheme.type] || "bg-gray-100 text-gray-700";
  const confidenceColor =
    scheme.confidence >= 80
      ? "border-green-200"
      : scheme.confidence >= 60
      ? "border-blue-200"
      : "border-yellow-200";

  return (
    <div
      className={`border rounded-2xl p-5 transition-all bg-white ${
        isTop ? "border-farm-green shadow-sm" : `border-gray-200 hover:${confidenceColor}`
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-start gap-3 min-w-0">
          <div className="shrink-0 w-9 h-9 rounded-xl bg-gray-50 flex items-center justify-center">
            <TypeIcon className="w-5 h-5 text-farm-green" />
          </div>
          <div className="min-w-0">
            <h4 className="font-bold text-gray-900 text-base leading-tight">{scheme.name}</h4>
            <p className="text-xs text-gray-500 mt-0.5">{scheme.authority}</p>
          </div>
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          {isTop && (
            <span className="text-[10px] font-bold bg-farm-green text-white px-2 py-0.5 rounded-full">
              TOP PICK
            </span>
          )}
          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full capitalize ${typeColor}`}>
            {scheme.type.replace("_", " ")}
          </span>
        </div>
      </div>

      {/* Benefit */}
      <p className="text-sm text-farm-green font-semibold mb-2">{scheme.benefit}</p>

      {/* Eligibility */}
      <p className="text-xs text-gray-600 mb-3 leading-relaxed">
        {scheme.eligibility_explanation}
      </p>

      {/* Confidence */}
      <div className="mb-3">
        <ConfidenceBar confidence={scheme.confidence} label="Eligibility confidence" size="sm" />
      </div>

      {/* Deadline */}
      <div className="text-xs text-gray-500 mb-3 flex items-center gap-1">
        <span className="font-medium">Deadline:</span> {scheme.deadline}
      </div>

      {/* Expandable details */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1 text-xs font-medium text-gray-500 hover:text-farm-green transition-colors mb-2"
      >
        {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        {expanded ? "Hide details" : "View full details & how to apply"}
      </button>

      {expanded && (
        <div className="border-t border-gray-100 pt-3 space-y-4">

          {/* Description + Important Notes */}
          {scheme.description && (() => {
            const parts = scheme.description.split(/(⚠️[^]*$)/);
            const mainDesc = parts[0].trim();
            const warningBlock = parts[1]?.trim();
            return (
              <div className="space-y-2">
                {mainDesc && (
                  <div>
                    <p className="text-xs font-bold text-gray-700 mb-1 flex items-center gap-1">
                      <BookOpen className="w-3.5 h-3.5" /> About this Scheme
                    </p>
                    <p className="text-xs text-gray-600 leading-relaxed">{mainDesc}</p>
                  </div>
                )}
                {warningBlock && (
                  <div className="bg-amber-50 border border-amber-200 rounded-xl p-3">
                    <p className="text-xs font-bold text-amber-800 mb-1.5 flex items-center gap-1">
                      <AlertTriangle className="w-3.5 h-3.5" /> Important Notes
                    </p>
                    <ul className="space-y-1">
                      {warningBlock
                        .replace(/^⚠️\s*Important notes:\s*/i, "")
                        .split(/(?=⚠️)|(?<=\.\s)(?=[A-Z])/)
                        .flatMap(s => s.split("\n"))
                        .map(s => s.replace(/^⚠️\s*/, "").trim())
                        .filter(Boolean)
                        .map((note, i) => (
                          <li key={i} className="flex items-start gap-1.5 text-xs text-amber-800">
                            <AlertTriangle className="w-3 h-3 mt-0.5 text-amber-500 shrink-0" />
                            {note}
                          </li>
                        ))}
                    </ul>
                  </div>
                )}
              </div>
            );
          })()}

          {/* Action Plan */}
          {scheme.action_plan && scheme.action_plan.length > 0 && (
            <div>
              <p className="text-xs font-bold text-gray-700 mb-1.5 flex items-center gap-1">
                <ListOrdered className="w-3.5 h-3.5" /> How to Apply (Step-by-Step)
              </p>
              <ol className="space-y-1.5">
                {scheme.action_plan.map((step, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-gray-700">
                    <span className="shrink-0 w-4 h-4 rounded-full bg-farm-green/10 text-farm-green font-bold flex items-center justify-center text-[10px] mt-0.5">
                      {i + 1}
                    </span>
                    {step}
                  </li>
                ))}
              </ol>
            </div>
          )}

          {/* Required documents */}
          <div>
            <p className="text-xs font-bold text-gray-700 mb-1.5 flex items-center gap-1">
              <FileText className="w-3.5 h-3.5" /> Documents Needed
            </p>
            <ul className="space-y-1">
              {scheme.required_documents.map((doc, i) => (
                <li key={i} className="flex items-start gap-1.5 text-xs text-gray-600">
                  <CheckCircle2 className="w-3.5 h-3.5 mt-0.5 text-green-500 shrink-0" />
                  {doc}
                </li>
              ))}
            </ul>
          </div>

          {/* Eligibility breakdown */}
          {scheme.eligibility_explanation && (
            <div>
              <p className="text-xs font-bold text-gray-700 mb-1.5 flex items-center gap-1">
                <ClipboardList className="w-3.5 h-3.5" /> Eligibility Check
              </p>
              <ul className="space-y-1">
                {scheme.eligibility_explanation.split(" | ").map((item, i) => (
                  <li key={i} className="flex items-start gap-1.5 text-xs text-gray-600">
                    <CheckCircle2 className="w-3.5 h-3.5 mt-0.5 text-blue-400 shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Apply link */}
          <a
            href={scheme.apply_link}
            target="_blank"
            rel="noreferrer"
            className="flex items-center justify-center gap-2 w-full py-2.5 bg-farm-green hover:bg-farm-green/90 text-white rounded-xl text-sm font-semibold transition-colors"
          >
            Apply Now
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
          {scheme.application_portal !== scheme.apply_link && (
            <a
              href={scheme.application_portal}
              target="_blank"
              rel="noreferrer"
              className="flex items-center justify-center gap-2 w-full py-2 bg-gray-50 hover:bg-gray-100 text-gray-800 rounded-xl text-xs font-medium transition-colors"
            >
              Official Portal
              <ExternalLink className="w-3 h-3" />
            </a>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Main Route ───────────────────────────────────────────────────────────────

export default function SchemesRoute() {
  const { farmId, district: loaderDistrict, mainCrop: loaderCrop, areaAcres: loaderArea } =
    useLoaderData<typeof loader>();
  const ctx            = useOutletContext<OutletContext>();
  const [searchParams] = useSearchParams();
  const fetcher        = useFetcher<SchemesResponse>();

  // Prefer outlet context (parent layout has real values) then loader URL params
  const district  = ctx?.district  ?? loaderDistrict  ?? searchParams.get("district")  ?? "";
  const mainCrop  = ctx?.mainCrop  ?? loaderCrop       ?? searchParams.get("main_crop") ?? "";
  const areaAcres = ctx?.areaAcres ?? loaderArea       ?? null;

  // On mount: fast cache-only check — never triggers LLM
  useEffect(() => {
    const fd = new FormData();
    fd.append("_intent",    "load_cache");
    fd.append("district",   district);
    fd.append("main_crop",  mainCrop);
    fd.append("area_acres", String(areaAcres ?? ""));
    fetcher.submit(fd, { method: "post" });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function submitScan() {
    const fd = new FormData();
    fd.append("_intent",    "refresh");
    fd.append("district",   district);
    fd.append("main_crop",  mainCrop);
    fd.append("area_acres", String(areaAcres ?? ""));
    fetcher.submit(fd, { method: "post" });
  }

  const isBusy     = fetcher.state !== "idle";
  const isScanning = isBusy && fetcher.formData?.get("_intent") === "refresh";
  const isChecking = isBusy && fetcher.formData?.get("_intent") === "load_cache";
  const result     = fetcher.data;
  const schemes    = result?.data?.schemes ?? [];
  const meta       = result?.metadata;
  const explanation = meta?.explanation ?? "";
  const topIds     = new Set(result?.data?.top_scheme_ids ?? []);
  const hasCached  = result?.success && schemes.length > 0;

  return (
    <div className="space-y-6 pb-24">

      {/* ── Header card ── */}
      <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div>
            <h3 className="font-serif font-bold text-xl text-gray-900">
              Government Schemes &amp; Subsidies
            </h3>
            <p className="text-sm text-gray-500 mt-1">
              {isChecking && "Checking for saved results…"}
              {isScanning && "Running AI scan…"}
              {!isBusy && hasCached && meta?.cached &&
                `Cached · ${formatTs(meta.cached_at)} · expires ${formatTs(meta.expires_at)}`}
              {!isBusy && hasCached && !meta?.cached &&
                `Fresh scan · ${formatTs(result?.data?.scan_timestamp)}`}
              {!isBusy && !hasCached && !result && "Tap 'Scan for Schemes' to find eligible programs."}
              {!isBusy && result && !result.success && "Scan failed — try again."}
            </p>
          </div>
          <button
            onClick={submitScan}
            disabled={isBusy}
            className="flex items-center gap-2 px-4 py-2 bg-farm-green hover:bg-farm-green/90 disabled:opacity-50 text-white rounded-xl text-sm font-semibold transition-colors shrink-0"
          >
            <RefreshCw className={`w-4 h-4 ${isScanning ? "animate-spin" : ""}`} />
            {isScanning ? "Scanning…" : hasCached ? "Re-scan" : "Scan for Schemes"}
          </button>
        </div>

        {meta && !isBusy && (
          <div className="mt-4 pt-4 border-t border-gray-100 flex flex-wrap items-center gap-4">
            <div className="flex-1 min-w-[160px]">
              <ConfidenceBar confidence={meta.confidence} label="Scan confidence" size="sm" showPercentage />
            </div>
            {meta.human_review_required && (
              <span className="flex items-center gap-1 text-xs text-yellow-700 font-medium">
                <AlertCircle className="w-3.5 h-3.5" /> Needs extension review
              </span>
            )}
            <span className="text-xs text-gray-400 ml-auto">{meta.model_version}</span>
          </div>
        )}
      </div>

      {/* ── Error ── */}
      {!isBusy && result && !result.success && (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-red-800 text-sm">Could not load schemes</p>
            <p className="text-xs text-red-600 mt-1">{result.error ?? "Unexpected error."}</p>
          </div>
        </div>
      )}

      {/* ── Scanning spinner ── */}
      {isScanning && (
        <div className="bg-white rounded-3xl p-10 shadow-sm border border-gray-100 text-center">
          <RefreshCw className="w-9 h-9 animate-spin text-farm-green mx-auto mb-4" />
          <p className="font-semibold text-gray-800">Scanning for eligible schemes…</p>
          <p className="text-xs text-gray-500 mt-1">
            AI is checking central and Tamil Nadu state programs against your farm profile.
          </p>
        </div>
      )}

      {/* ── Empty state ── */}
      {!isBusy && result?.success && schemes.length === 0 && (
        <div className="bg-white rounded-3xl p-10 shadow-sm border border-gray-100 text-center">
          <Sprout className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="font-semibold text-gray-800">No cached results</p>
          <p className="text-sm text-gray-500 mt-2">
            Tap <strong>Scan for Schemes</strong> to run an AI-powered eligibility check.
          </p>
        </div>
      )}

      {/* ── Count summary ── */}
      {!isScanning && schemes.length > 0 && (
        <p className="text-sm text-gray-600 font-medium px-1">
          {schemes.length} scheme{schemes.length !== 1 ? "s" : ""} found
          {result?.data?.district ? ` for ${result.data.district}` : ""}
          {result?.data?.farmer_category ? ` · ${result.data.farmer_category} farmer` : ""}
        </p>
      )}

      {/* ── Scheme cards ── */}
      {!isScanning && schemes.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {schemes.map((scheme) => (
            <SchemeCard key={scheme.scheme_id} scheme={scheme} isTop={topIds.has(scheme.scheme_id)} />
          ))}
        </div>
      )}

      {/* ── AI Explanation ── */}
      {!isScanning && explanation && (
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5">
          <p className="text-xs font-bold text-amber-800 mb-3 flex items-center gap-1.5">
            <BookOpen className="w-3.5 h-3.5" /> AI Analysis
          </p>
          <ExplanationBlock text={explanation} />
          <p className="text-[11px] text-amber-600 mt-4 pt-3 border-t border-amber-200">
            Verify eligibility with official portals before applying. Benefit amounts may change.
            {result?.data?.scan_timestamp && <> Data as of {formatTs(result.data.scan_timestamp)}.</>}
          </p>
        </div>
      )}
    </div>
  );
}
