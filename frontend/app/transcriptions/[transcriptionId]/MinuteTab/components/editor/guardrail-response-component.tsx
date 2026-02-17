import { useMemo } from 'react'
import { GuardrailResultResponse } from '@/lib/client'
import { HallucinationsList } from './HallucinationsList'
import { VerifiedGuardrailsList } from './VerifiedGuardrailsList'
import { WarningsList } from './WarningsList'

interface GuardrailProps {
  guardrailResults: GuardrailResultResponse[]
  hallucinations?: any[] | null // Assuming type is handled in the sub-component
}

const GUARDRAIL_THRESHOLD = Number(process.env.NEXT_PUBLIC_GUARDRAIL_THRESHOLD) || 0.8

export function GuardrailResponseComponent({
  guardrailResults = [],
  hallucinations = [],
}: GuardrailProps) {
  const { warnings, passes } = useMemo(() => {
    const isWarning = (r: GuardrailResultResponse) => {
      const isLowScore = r.score != null && r.score < GUARDRAIL_THRESHOLD;
      return r.passed === false || isLowScore;
    };

    return {
      warnings: guardrailResults.filter(isWarning),
      passes: guardrailResults.filter((r) => !isWarning(r)),
    };
  }, [guardrailResults]);

  const hasHallucinations = (hallucinations?.length ?? 0) > 0 
  const hasWarnings = warnings.length > 0

  if (!guardrailResults.length && !hasHallucinations) return null

  return (
    <div className="flex flex-col gap-4">
      <HallucinationsList hallucinations={hallucinations} />

      <WarningsList warnings={warnings} />

      <VerifiedGuardrailsList 
        passes={passes} 
        isVisible={!hasWarnings && !hasHallucinations} 
      />
    </div>
  )
}