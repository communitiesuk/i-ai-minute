import { MinuteListItem, TranscriptionGetResponse } from '@/lib/client'
import { MinuteEditor } from '@/app/transcriptions/[transcriptionId]/MinuteTab/minute-editor/minute-editor'

export const DocumentTab = ({
  transcription,
  minute,
  onCitationClicked,
}: {
  transcription: TranscriptionGetResponse
  minute: MinuteListItem
  onCitationClicked?: (citationIndex: number) => void
}) => {
  return (
    <MinuteEditor
      transcription={transcription}
      minute={minute}
      onCitationClicked={onCitationClicked}
    />
  )
}
