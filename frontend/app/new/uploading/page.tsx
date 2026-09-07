'use client'

import { useBannerStore } from '@/stores/use-banner-store'
import { useUploadRecordingStore } from '@/stores/use-upload-recording-store'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { LoadingSpinner } from '@/components/loading-spinner'

export default function TranscriptionLoadingPage() {
  const router = useRouter()
  const setBanner = useBannerStore((store) => store.setBanner)

  const { status, transcriptionId, uploadingFrom, error, reset } =
    useUploadRecordingStore()

  useEffect(() => {
    if (status === 'success' && transcriptionId) {
      setBanner({
        variant: 'success',
        title: 'Success',
        message: 'Recording saved - ',
        link: {
          text: 'click to view',
          href: `/transcriptions/${transcriptionId}`,
        },
      })

      reset()
      router.push('/')
    }

    if (status === 'idle') {
      router.replace('/')
    }
  }, [status, transcriptionId, setBanner, reset, router])

  if (status === 'error') {
    throw new Error(error || 'Upload failed')
  }

  return (
    <div className="flex flex-col items-center">
      <LoadingSpinner
        label={uploadingFrom === 'upload' ? 'Uploading' : 'Processing'}
      />
      <p className="govuk-body">
        {uploadingFrom === 'upload' ? 'Uploading File' : 'Processing recording'}
        &hellip;
      </p>
    </div>
  )
}
