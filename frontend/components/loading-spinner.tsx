type LoadingSpinnerProps = {
  label?: string
  className?: string
}

export const LoadingSpinner = ({
  label = 'Loading',
  className = '',
}: LoadingSpinnerProps) => (
  <div
    aria-label={label}
    aria-live="polite"
    role="status"
    className={`h-28 w-28 animate-spin rounded-full border-[12px] border-gray-400 border-t-sky-700 ${className}`}
  />
)
