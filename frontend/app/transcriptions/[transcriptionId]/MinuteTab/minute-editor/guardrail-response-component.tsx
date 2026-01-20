import {
    GuardrailResultResponse,
} from '@/lib/client'
import {
    AlertTriangle,
    CheckCircle,
    XCircle,
} from 'lucide-react'

export function GuardrailResponseComponent({
    guardrailResults,
}: {
    guardrailResults: GuardrailResultResponse[]
}) {
    if (!guardrailResults || guardrailResults.length === 0) {
        return null
    }

    const warnings = guardrailResults.filter((r) => r.result === 'warning' || r.result === 'fail')

    if (warnings.length === 0) {
        return null
    }

    return (
        <div className="flex flex-col gap-2 p-4 bg-yellow-50 border border-yellow-200 rounded-md">
            <div className="flex items-center gap-2 font-semibold text-yellow-800">
                <AlertTriangle className="h-5 w-5" />
                <span>Guardrail Warnings</span>
            </div>
            <div className="flex flex-col gap-2">
                {warnings.map((result) => (
                    <div key={result.id} className="flex flex-col gap-1 text-sm text-yellow-700">
                        <div className="flex items-center gap-2">
                            {result.result === 'fail' ? <XCircle className="h-4 w-4 text-red-600" /> : <AlertTriangle className="h-4 w-4 text-yellow-600" />}
                            <span className="font-medium capitalize">{result.guardrail_type.replace('_', ' ')}:</span>
                            <span className="uppercase text-xs font-bold border px-1 rounded border-yellow-600">{result.result}</span>
                        </div>
                        {result.reasoning && (
                            <p className="ml-6 text-yellow-800">{result.reasoning}</p>
                        )}
                        {result.score !== null && result.score !== undefined && (
                            <p className="ml-6 text-xs text-yellow-600">Confidence Score: {result.score}</p>
                        )}
                    </div>
                ))}
            </div>
        </div>
    )
}
