import { GuardrailResultResponse } from '@/lib/client'
import { AlertTriangle, CheckCircle, XCircle } from 'lucide-react'

export function GuardrailResponseComponent({
    guardrailResults,
}: {
    guardrailResults: GuardrailResultResponse[]
}) {

    if (!guardrailResults || guardrailResults.length === 0) {
        return null
    }



    // 2. Robust Filter Logic (Handles 'FAIL', 'Fail', 'fail')
    const warnings = guardrailResults.filter((r) => {
        const status = (r.result || '').toLowerCase()
        return (
            status === 'warning' ||
            status === 'fail' ||
            (r.score !== null && r.score !== undefined && r.score < 0.8)
        )
    })

    const passes = guardrailResults.filter((r) => {
        const status = (r.result || '').toLowerCase()
        return (
            status === 'pass' &&
            (r.score === null || r.score === undefined || r.score >= 0.8)
        )
    })

    // 3. Render Warnings/Failures
    if (warnings.length > 0) {
        return (
            <div className="flex flex-col gap-2 p-4 bg-yellow-50 border border-yellow-200 rounded-md mb-4">
                <div className="flex items-center gap-2 font-semibold text-yellow-800">
                    <AlertTriangle className="h-5 w-5" />
                    <span>Guardrail Warnings</span>
                </div>
                <div className="flex flex-col gap-2">
                    {warnings.map((result) => {
                        // Normalize status for styling checks
                        const statusLower = (result.result || '').toLowerCase();
                        const isFail = statusLower === 'fail';

                        return (
                            <div key={result.id} className={`flex flex-col gap-1 text-sm p-2 rounded border ${isFail ? 'bg-red-50 border-red-100' : 'bg-white/50 border-yellow-100'}`}>
                                <div className="flex items-center gap-2">
                                    {/* Icon Logic */}
                                    {isFail ? (
                                        <XCircle className="h-4 w-4 text-red-600" />
                                    ) : (
                                        <AlertTriangle className="h-4 w-4 text-yellow-600" />
                                    )}
                                    
                                    {/* Title */}
                                    <span className={`font-medium capitalize ${isFail ? 'text-red-800' : 'text-yellow-800'}`}>
                                        {result.guardrail_type.replace('_', ' ')}:
                                    </span>
                                    
                                    {/* Badge */}
                                    <span className={`uppercase text-xs font-bold border px-1 rounded ${
                                        isFail ? 'border-red-600 text-red-700 bg-red-100' : 'border-yellow-600 text-yellow-800 bg-yellow-100'
                                    }`}>
                                        {result.result}
                                    </span>
                                </div>
                                
                                {result.reasoning && (
                                    <p className={`${isFail ? 'text-red-900' : 'text-yellow-900'} italic`}>
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
        )
    }

    // 4. Render Passes
    if (passes.length > 0) {
        return (
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
        )
    }

    return null
}