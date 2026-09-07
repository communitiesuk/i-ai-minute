'use client'

import {
  GovukBody,
  GovukButton,
  GovukButtonGroup,
  GovukButtonLink,
  GovukErrorSummary,
  GovukHeading,
  GovukList,
  GovukListItem,
} from '@/components/govuk'
import {
  acceptTermsOfUseUsersTermsOfUsePostMutation,
  getUserUsersMeGetOptions,
} from '@/lib/client/@tanstack/react-query.gen'
import { API_PROXY_PATH } from '@/lib/constants'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Loader2 } from 'lucide-react'
import { useState } from 'react'

export default function TermsOfUsePage() {
  const queryClient = useQueryClient()
  const userQueryOptions = getUserUsersMeGetOptions()
  const [hasSubmissionError, setHasSubmissionError] = useState(false)
  const { data: user } = useQuery({
    ...userQueryOptions,
    refetchOnMount: 'always',
  })
  const { mutate: acceptTerms, isPending } = useMutation({
    ...acceptTermsOfUseUsersTermsOfUsePostMutation(),
    async onSuccess(updatedUser) {
      queryClient.setQueryData(userQueryOptions.queryKey, updatedUser)
      await queryClient.invalidateQueries({
        queryKey: userQueryOptions.queryKey,
      })
      window.location.replace('/')
    },
    onError(error) {
      console.error('Failed to accept terms of use:', error)
      setHasSubmissionError(true)
    },
  })

  return (
    <div className="govuk-grid-row">
      <div className="govuk-grid-column-two-thirds">
        {hasSubmissionError && (
          <GovukErrorSummary
            errorList={[
              {
                href: '#accept-terms',
                text: 'Accept the terms of use to continue',
              },
            ]}
          />
        )}

        <GovukHeading as="h1" size="xl">
          Terms of use
        </GovukHeading>

        <GovukBody>
          You must accept these terms before using Local Transcribe.
        </GovukBody>

        <GovukHeading as="h2" size="m">
          By using Local Transcribe, you agree that you will:
        </GovukHeading>

        <GovukList type="bullet" spaced>
          <GovukListItem>
            only use the service for work that you are authorised to do
          </GovukListItem>
          <GovukListItem>
            follow your organisation&apos;s policies for handling recordings,
            transcripts, minutes and personal information
          </GovukListItem>
          <GovukListItem>
            check transcripts, minutes and AI-generated content before relying
            on or sharing them
          </GovukListItem>
          <GovukListItem>
            not upload content that you do not have permission to process
          </GovukListItem>
        </GovukList>

        <GovukBody>
          Read the{' '}
          <a className="govuk-link" href="/privacy">
            Local Transcribe privacy notice
          </a>{' '}
          to understand how the service uses personal information.
        </GovukBody>

        <GovukButtonGroup>
          <GovukButton
            id="accept-terms"
            type="button"
            disabled={isPending || user?.accepted_tou}
            onClick={() => {
              setHasSubmissionError(false)
              acceptTerms({})
            }}
          >
            {isPending ? (
              <span className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                Accepting...
              </span>
            ) : user?.accepted_tou ? (
              'Accepted'
            ) : (
              'Accept and continue'
            )}
          </GovukButton>
          <GovukButtonLink
            href={`${API_PROXY_PATH}/signout`}
            variant="secondary"
          >
            I do not accept
          </GovukButtonLink>
        </GovukButtonGroup>
      </div>
    </div>
  )
}
