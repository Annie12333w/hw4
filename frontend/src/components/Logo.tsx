/** Campus Customs crest: a shield with two interlocking Cs under a star. */
export default function Logo({ size = 48, inverted = false }: { size?: number; inverted?: boolean }) {
  const shield = inverted ? '#ffffff' : '#00356b'
  const trim = inverted ? '#00356b' : '#ffffff'
  const accent = inverted ? '#286dc0' : '#9cc3ee'
  return (
    <svg
      width={size * (44 / 52)}
      height={size}
      viewBox="0 0 44 52"
      role="img"
      aria-label="Campus Customs crest"
      className="logo"
    >
      <path d="M3 2h38v22c0 14-10 22.5-19 26.5C13 46.5 3 38 3 24V2Z" fill={shield} />
      <path
        d="M6.5 5.5h31V24c0 11.5-8 18.8-15.5 22.6C14.5 42.8 6.5 35.5 6.5 24V5.5Z"
        fill="none"
        stroke={trim}
        strokeWidth="1.2"
        opacity="0.85"
      />
      <polygon
        points="22,6.4 22.9,8.8 25.4,8.9 23.4,10.4 24.1,12.8 22,11.4 19.9,12.8 20.6,10.4 18.6,8.9 21.1,8.8"
        fill={trim}
      />
      <path d="M31.2 21.3A7.5 7.5 0 1 0 31.2 32.7" fill="none" stroke={accent} strokeWidth="3.4" strokeLinecap="round" />
      <path d="M23.2 21.3A7.5 7.5 0 1 0 23.2 32.7" fill="none" stroke={trim} strokeWidth="3.4" strokeLinecap="round" />
      <path d="M12 40.5h20" stroke={trim} strokeWidth="1" opacity="0.6" />
    </svg>
  )
}
