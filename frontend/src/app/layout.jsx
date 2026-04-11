import { IBM_Plex_Mono, Manrope } from 'next/font/google'
import Script from 'next/script'
import './globals.css'

const manrope = Manrope({
  subsets: ['latin'],
  variable: '--font-manrope',
})

const ibmPlexMono = IBM_Plex_Mono({
  subsets: ['latin'],
  variable: '--font-ibm-plex-mono',
  weight: ['400', '500', '600'],
})

export const metadata = {
  title: 'Lumiq | Decision Intelligence',
  description: 'Plataforma SaaS de analytics e insights para convertir datasets en decisiones claras.',
  keywords: ['analytics', 'AI', 'BI', 'SaaS', 'dashboard', 'decisiones'],
}

export default function RootLayout({ children }) {
  return (
    <html lang="es">
      <body className={`${manrope.variable} ${ibmPlexMono.variable}`}>
        <Script id="mathjax-config" strategy="afterInteractive">
          {`window.MathJax = {
            tex: {
              inlineMath: [['\\\\(', '\\\\)']],
              displayMath: [['\\\\[', '\\\\]'], ['$$', '$$']]
            },
            svg: {
              fontCache: 'global'
            }
          };`}
        </Script>
        <Script
          id="mathjax-script"
          strategy="afterInteractive"
          src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"
        />
        {children}
      </body>
    </html>
  )
}
