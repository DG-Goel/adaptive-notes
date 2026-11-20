import { forwardRef } from 'react'
import { PrimaryButton, type PrimaryButtonProps } from './PrimaryButton'

export type SecondaryButtonProps = PrimaryButtonProps

export const SecondaryButton = forwardRef<HTMLButtonElement, SecondaryButtonProps>(
  ({ variant = 'secondary', ...props }, ref) => (
    <PrimaryButton ref={ref} variant={variant} {...props} />
  ),
)
SecondaryButton.displayName = 'SecondaryButton'
