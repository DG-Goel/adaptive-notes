import type { SVGProps } from 'react'

type LogoProps = SVGProps<SVGSVGElement> & {
  /** When true, renders only the mark without the wordmark. */
  markOnly?: boolean
  /** Color of the wordmark text. */
  textClassName?: string
}

export function Logo({ markOnly = false, textClassName = '', className, ...props }: LogoProps) {
  return (
    <div className={`inline-flex items-center gap-2.5 ${className ?? ''}`}>
      <svg
        width="32"
        height="32"
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
        {...props}
      >
        {/* Intertwined continuous knot — two ribbons forming an abstract N */}
        <defs>
          <linearGradient id="noetra-mark" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
            <stop stopColor="#E87430" />
            <stop offset="1" stopColor="#C84A10" />
          </linearGradient>
          <clipPath id="noetra-clip">
            <rect width="32" height="32" rx="8" />
          </clipPath>
        </defs>
        <g clipPath="url(#noetra-clip)">
          <rect width="32" height="32" fill="#252525" />
          {/* Ribbon one */}
          <path
            d="M7 24C7 17 11 9 16 9C21 9 25 15 25 24"
            stroke="url(#noetra-mark)"
            strokeWidth="3.2"
            strokeLinecap="round"
          />
          {/* Ribbon two — interlaces under/over */}
          <path
            d="M25 8C25 15 21 23 16 23C11 23 7 17 7 8"
            stroke="#F7F4EF"
            strokeOpacity="0.9"
            strokeWidth="3.2"
            strokeLinecap="round"
          />
          {/* Intersection highlight */}
          <circle cx="16" cy="16" r="2.4" fill="url(#noetra-mark)" />
        </g>
      </svg>
      {!markOnly && (
        <span
          className={`font-serif text-xl tracking-[0.18em] uppercase ${textClassName}`}
        >
          NOETRA
        </span>
      )}
    </div>
  )
}
