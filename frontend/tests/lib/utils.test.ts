import { describe, it, expect } from 'vitest'
import { cn, getApiErrorMessage } from '@/lib/utils'

describe('cn', () => {
  it('merges simple classes', () => {
    expect(cn('p-2', 'text-sm')).toBe('p-2 text-sm')
  })

  it('resolves tailwind conflicts', () => {
    expect(cn('p-2', 'p-4')).toBe('p-4')
  })

  it('handles conditional classes', () => {
    expect(cn('p-2', false && 'hidden')).toBe('p-2')
  })
})

describe('getApiErrorMessage', () => {
  it('returns the message from an Error instance', () => {
    expect(getApiErrorMessage(new Error('boom'), 'fallback')).toBe('boom')
  })

  it('returns a string detail field', () => {
    expect(
      getApiErrorMessage({ detail: 'Recording not found' }, 'fallback')
    ).toBe('Recording not found')
  })

  it('joins msg fields from a validation-error detail array', () => {
    expect(
      getApiErrorMessage(
        { detail: [{ msg: 'field required' }, { msg: 'must be a string' }] },
        'fallback'
      )
    ).toBe('field required, must be a string')
  })

  it('returns the fallback for an unrecognized shape', () => {
    expect(getApiErrorMessage({ foo: 'bar' }, 'fallback')).toBe('fallback')
  })

  it('returns the fallback for null/undefined', () => {
    expect(getApiErrorMessage(null, 'fallback')).toBe('fallback')
    expect(getApiErrorMessage(undefined, 'fallback')).toBe('fallback')
  })
})
