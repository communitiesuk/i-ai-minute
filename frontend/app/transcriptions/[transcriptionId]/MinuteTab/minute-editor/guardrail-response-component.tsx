import { useMemo } from 'react'
import { GuardrailResultResponse } from '@/lib/client'
import { AlertTriangle, CheckCircle, XCircle, LucideIcon } from 'lucide-react'

// --- Types ---

export type LLMHallucination = {
  hallucination_type: string
  hallucination_text: string
  hallucination_reason: string
}

interface GuardrailProps {
  guardrailResults: GuardrailResultResponse[]
  hallucinations?: LLMHallucination[] | null
}

// --- Constants & Helpers ---

const GUARDRAIL_THRESHOLD =
  Number(process.env.NEXT_PUBLIC_GUARDRAIL_THRESHOLD) || 0.8
const formatLabel = (str: string) => str.replace(/_/g, ' ')

// --- Reusable Sub-component ---

const StatusSection = ({ 
  title, 
  icon: Icon, 
  variant, 
  children, 
}: { 
  title: string 
  icon: LucideIcon 
  variant: 'error' | 'warning' | 'success' 
  children: React.ReactNode 
}) => {
  const styles = {
    error: 'bg-red-50 border-red-200 text-red-800',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    success: 'bg-green-50 border-green-200 text-green-800',
  }

  return (
    <div
      className={`mb-4 flex flex-col gap-2 rounded-md border p-4 ${styles[variant]}`}
    >
      <div className="flex items-center gap-2 font-semibold">
        <Icon className="h-5 w-5" />
        <span>{title}</span>
      </div>
      <div className="flex flex-col gap-2">{children}</div>
    </div>
  )
}

// --- Main Component ---

export function GuardrailResponseComponent({
  guardrailResults = [],
  hallucinations = [],
}: GuardrailProps) {
  
  // Logic: Separate results into warnings and passes
  const { warnings, passes } = useMemo(() => {
    const w: GuardrailResultResponse[] = []
    const p: GuardrailResultResponse[] = []

    guardrailResults.forEach((r) => {
      const isLowScore =
        r.score !== null &&
        r.score !== undefined &&
        r.score < GUARDRAIL_THRESHOLD
      if (r.passed === false || isLowScore) {
        w.push(r)
      } else {
        p.push(r)
      }
    })
    return { warnings: w, passes: p }
  }, [guardrailResults])

  const hasHallucinations = !!(hallucinations && hallucinations.length > 0)
  const hasWarnings = warnings.length > 0
  const hasPasses = passes.length > 0

  if (!guardrailResults.length && !hasHallucinations) return null

  return (
    <div>
      {/* 1. Hallucinations (Highest Priority) */}
      {hasHallucinations && (
        <StatusSection
          title="Hallucinations Detected"
          icon={XCircle}
          variant="error"
        >
          {hallucinations?.map((h, i) => (
            <div
              key={i}
              className="flex flex-col gap-1 rounded border border-red-100 bg-white/50 p-2 text-sm"
            >
              <span className="font-medium capitalize">
                {formatLabel(h.hallucination_type)}:
              </span>
              {h.hallucination_text && (
                <p className="text-red-900 italic">"{h.hallucination_text}"</p>
              )}
              {h.hallucination_reason && (
                <p className="text-xs text-red-700">
                  Reason: {h.hallucination_reason}
                </p>
              )}
            </div>
          ))}
        </StatusSection>
      )}

      {/* 2. Warnings / Hard Fails */}
      {hasWarnings && (
        <StatusSection
          title="Guardrail Warnings"
          icon={AlertTriangle}
          variant="warning"
        >
          {warnings.map((result) => {
            const isHardFail = result.passed === false
            return (
              <div 
                key={result.id} 
                className={`flex flex-col gap-1 rounded border p-2 text-sm ${
                  isHardFail
                    ? 'border-red-100 bg-red-50'
                    : 'border-yellow-100 bg-white/50'
                }`}
              >
                <div className="flex items-center gap-2">
                  {isHardFail ? (
                    <XCircle className="h-4 w-4 text-red-600" />
                   ) : (
                    <AlertTriangle className="h-4 w-4 text-yellow-600" />
                  )}
                  <span
                    className={`font-medium capitalize ${isHardFail ? 'text-red-800' : 'text-yellow-800'}`}
                  >
                    {formatLabel(result.guardrail_type)}:
                  </span>
                  <span
                    className={`rounded border px-1 text-xs font-bold uppercase ${
                      isHardFail
                        ? 'border-red-600 bg-red-100 text-red-700'
                        : 'border-yellow-600 bg-yellow-100 text-yellow-800'
                    }`}
                  >
                    {isHardFail ? 'FAILED' : 'WARNING'}
                  </span>
                </div>
                {result.reasoning && (
                  <p className="italic opacity-90">"{result.reasoning}"</p>
                )}
                {result.score !== null && (
                  <p className="ml-6 text-xs opacity-75">
                    Confidence: {(result.score * 100).toFixed(0)}%
                  </p>
                )}
              </div>
            )
          })}
        </StatusSection>
      )}

      {/* 3. Successes (Only show if no critical issues or if desired) */}
      {!hasHallucinations && !hasWarnings && hasPasses && (
        <StatusSection title="AI Verified" icon={CheckCircle} variant="success">
          <div className="flex flex-col gap-1 pl-7">
            {passes.map((result) => (
              <div
                key={result.id}
                className="flex items-center gap-2 text-xs opacity-90"
              >
                <span className="capitalize">
                  {formatLabel(result.guardrail_type)}
                </span>
                <span className="opacity-50">•</span>
                <span>Pass</span>
              </div>
            ))}
          </div>
        </StatusSection>
      )}
    </div>
  )
}