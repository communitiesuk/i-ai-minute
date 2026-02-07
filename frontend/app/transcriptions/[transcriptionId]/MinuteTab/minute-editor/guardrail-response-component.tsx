import { GuardrailResultResponse } from '@/lib/client'
import { AlertTriangle, CheckCircle, XCircle } from 'lucide-react'

export type LLMHallucination = {
  hallucination_type: string
  hallucination_text: string
  hallucination_reason: string
}

export function GuardrailResponseComponent({
  guardrailResults,
  hallucinations,
}: {
  guardrailResults: GuardrailResultResponse[]
  hallucinations?: LLMHallucination[] | null
}) {
  const GUARDRAIL_THRESHOLD =
    Number(process.env.NEXT_PUBLIC_GUARDRAIL_THRESHOLD) || 0.8;


  const hasGuardrails = guardrailResults && guardrailResults.length > 0
  const hasHallucinations = hallucinations && hallucinations.length > 0


  if (!hasGuardrails && !hasHallucinations) {
      return null
    }



    // 2. Robust Filter Logic (Handles 'FAIL', 'Fail', 'fail')
  const warnings = guardrailResults.filter((r) => {
      return (
          r.passed === false ||
          (r.score !== null && r.score !== undefined && r.score < GUARDRAIL_THRESHOLD)
        )
    })

    const passes = guardrailResults.filter((r) => {
        return (
            r.passed === true &&
            (r.score === null || r.score === undefined || r.score >= GUARDRAIL_THRESHOLD)
        )
    })

    // 5. Render All Content
    return (
        <>
            {/* Render Hallucinations */}
          {hasHallucinations && hallucinations && (
              <div className="flex flex-col gap-2 p-4 bg-red-50 border border-red-200 rounded-md mb-4">
                  <div className="flex items-center gap-2 font-semibold text-red-800">
                      <XCircle className="h-5 w-5" />
                      <span>Hallucinations Detected</span>
                  </div>
                  <div className="flex flex-col gap-2">
                      {hallucinations.map((h, i) => (
                            <div key={i} className="flex flex-col gap-1 text-sm p-2 rounded border bg-white/50 border-red-100">
                                <div className="flex items-center gap-2">
                                    <span className="font-medium capitalize text-red-800">
                                        {(h as any).hallucination_type.replace('_', ' ')}:
                                    </span>
                                </div>
                                {(h as any).hallucination_text && (
                                    <p className="text-red-900 italic">
                                        "{(h as any).hallucination_text}"
                                    </p>
                                )}
                                {(h as any).hallucination_reason && (
                                    <p className="text-xs text-red-700">
                                        Reason: {(h as any).hallucination_reason}
                                    </p>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Render Warnings */}
            {warnings.length > 0 && (
                <div className="flex flex-col gap-2 p-4 bg-yellow-50 border border-yellow-200 rounded-md mb-4">
                    <div className="flex items-center gap-2 font-semibold text-yellow-800">
                        <AlertTriangle className="h-5 w-5" />
                        <span>Guardrail Warnings</span>
                    </div>
                    <div className="flex flex-col gap-2">
                        {warnings.map((result) => {
                            return (
                                <div key={result.id} className={`flex flex-col gap-1 text-sm p-2 rounded border ${result.passed === false ? 'bg-red-50 border-red-100' : 'bg-white/50 border-yellow-100'}`}>
                                    <div className="flex items-center gap-2">
                                        {result.passed === false ? <XCircle className="h-4 w-4 text-red-600" /> : <AlertTriangle className="h-4 w-4 text-yellow-600" />}
                                        <span className={`font-medium capitalize ${result.passed === false ? 'text-red-800' : 'text-yellow-800'}`}>
                                            {result.guardrail_type.replace('_', ' ')}:
                                        </span>
                                        <span className={`uppercase text-xs font-bold border px-1 rounded ${result.passed === false ? 'border-red-600 text-red-700 bg-red-100' : 'border-yellow-600 text-yellow-800 bg-yellow-100'}`}>
                                            {result.passed ? 'PASSED (LOW SCORE)' : 'FAILED'}
                                        </span>
                                    </div>
                                    {result.reasoning && (
                                        <p className={`${result.passed === false ? 'text-red-900' : 'text-yellow-900'} italic`}>
                                            "{result.reasoning}"
                                        </p>
                                    )}
                                    {result.score !== null && result.score !== undefined && (
                                        <p className="ml-6 text-xs opacity-75">
                                            Confidence Score: {(result.score * 100).toFixed(0)}%
                                        </p>
                                    )}
                                </div>
                            )
                        })}
                    </div>
                </div>
            )}

            {/* Render Passes (only if no warnings and no hallucinations, or maybe always?) */}
            {/* Let's show passes only if there are no warnings or hallucinations to keep it clean, or keep previous logic? */}
            {/* Previous logic was: if warnings, show warnings. Else if passes, show passes. */}
            {/* New logic: if hallucinations, show them. If warnings, show them. If neither, show passes if any. */}
            {!hasHallucinations && warnings.length === 0 && passes.length > 0 && (
                <div className="flex flex-col gap-2 p-4 bg-green-50 border border-green-200 rounded-md mb-4">
                    <div className="flex items-center gap-2 font-semibold text-green-800">
                        <CheckCircle className="h-5 w-5" />
                        <span>AI Verified</span>
                    </div>
                    <div className="flex flex-col gap-1 pl-7">
                        {passes.map((result) => (
                            <div key={result.id} className="text-xs text-green-700 flex items-center gap-2">
                                <span className="capitalize">{result.guardrail_type.replace('_', ' ')}</span>
                                <span className="opacity-50">•</span>
                                <span>Pass</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </>
    )
}