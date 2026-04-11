'use client'

import { useEffect, useRef } from 'react'

const TOKEN_PREFIX = '__LUMIQ_TOKEN_'

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function createTokenStore(content) {
  const tokens = []

  const storeToken = (html, block = false) => {
    const marker = `${TOKEN_PREFIX}${tokens.length}__`
    tokens.push({ marker, html, block })
    return marker
  }

  let tokenized = String(content ?? '').replace(/\r\n/g, '\n')

  tokenized = tokenized.replace(/```([\s\S]*?)```/g, (_, code) => (
    storeToken(
      `<pre><code>${escapeHtml(code.trim())}</code></pre>`,
      true,
    )
  ))

  tokenized = tokenized.replace(/\\\[([\s\S]*?)\\\]/g, (_, math) => (
    storeToken(
      `<div class="math-block">\\[${escapeHtml(math.trim())}\\]</div>`,
      true,
    )
  ))

  tokenized = tokenized.replace(/\$\$([\s\S]*?)\$\$/g, (_, math) => (
    storeToken(
      `<div class="math-block">\\[${escapeHtml(math.trim())}\\]</div>`,
      true,
    )
  ))

  tokenized = tokenized.replace(/`([^`\n]+)`/g, (_, code) => (
    storeToken(`<code>${escapeHtml(code)}</code>`)
  ))

  tokenized = tokenized.replace(/\\\((.+?)\\\)/g, (_, math) => (
    storeToken(`<span class="math-inline">\\(${escapeHtml(math.trim())}\\)</span>`)
  ))

  return { tokenized, tokens }
}

function restoreTokens(value, tokens) {
  return tokens.reduce(
    (current, token) => current.split(token.marker).join(token.html),
    value,
  )
}

function renderInlineMarkdown(text, tokens) {
  let html = escapeHtml(text)

  html = html.replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, (_, label, href) => (
    `<a href="${href}" target="_blank" rel="noreferrer">${label}</a>`
  ))
  html = html.replace(/(\*\*|__)(.*?)\1/g, '<strong>$2</strong>')
  html = html.replace(/(^|[\s(])(\*|_)([^*_]+?)\2(?=[\s).,!?:;]|$)/g, '$1<em>$3</em>')
  html = restoreTokens(html, tokens)
  return html
}

function isBlockToken(line, tokens) {
  return tokens.some((token) => token.block && token.marker === line.trim())
}

function renderBlockMarkdown(content) {
  const { tokenized, tokens } = createTokenStore(content)
  const lines = tokenized.split('\n')
  const chunks = []
  let index = 0

  while (index < lines.length) {
    const line = lines[index]
    const trimmed = line.trim()

    if (!trimmed) {
      index += 1
      continue
    }

    if (isBlockToken(line, tokens)) {
      chunks.push(restoreTokens(trimmed, tokens))
      index += 1
      continue
    }

    const headingMatch = trimmed.match(/^(#{1,3})\s+(.*)$/)
    if (headingMatch) {
      const level = headingMatch[1].length
      chunks.push(`<h${level}>${renderInlineMarkdown(headingMatch[2], tokens)}</h${level}>`)
      index += 1
      continue
    }

    if (/^[-*]\s+/.test(trimmed)) {
      const items = []
      while (index < lines.length && /^[-*]\s+/.test(lines[index].trim())) {
        items.push(`<li>${renderInlineMarkdown(lines[index].trim().replace(/^[-*]\s+/, ''), tokens)}</li>`)
        index += 1
      }
      chunks.push(`<ul>${items.join('')}</ul>`)
      continue
    }

    if (/^\d+\.\s+/.test(trimmed)) {
      const items = []
      while (index < lines.length && /^\d+\.\s+/.test(lines[index].trim())) {
        items.push(`<li>${renderInlineMarkdown(lines[index].trim().replace(/^\d+\.\s+/, ''), tokens)}</li>`)
        index += 1
      }
      chunks.push(`<ol>${items.join('')}</ol>`)
      continue
    }

    if (/^>\s?/.test(trimmed)) {
      const quoteLines = []
      while (index < lines.length && /^>\s?/.test(lines[index].trim())) {
        quoteLines.push(renderInlineMarkdown(lines[index].trim().replace(/^>\s?/, ''), tokens))
        index += 1
      }
      chunks.push(`<blockquote><p>${quoteLines.join('<br />')}</p></blockquote>`)
      continue
    }

    const paragraphLines = []
    while (index < lines.length) {
      const current = lines[index]
      const currentTrimmed = current.trim()
      if (!currentTrimmed || isBlockToken(current, tokens) || /^(#{1,3})\s+/.test(currentTrimmed) || /^[-*]\s+/.test(currentTrimmed) || /^\d+\.\s+/.test(currentTrimmed) || /^>\s?/.test(currentTrimmed)) {
        break
      }
      paragraphLines.push(renderInlineMarkdown(currentTrimmed, tokens))
      index += 1
    }

    if (paragraphLines.length) {
      chunks.push(`<p>${paragraphLines.join('<br />')}</p>`)
      continue
    }

    index += 1
  }

  return chunks.join('')
}

function renderInlineOnly(content) {
  const { tokenized, tokens } = createTokenStore(content)
  return restoreTokens(renderInlineMarkdown(tokenized, tokens), tokens)
}

export default function MarkdownMath({
  content = '',
  inline = false,
  className = '',
}) {
  const hostRef = useRef(null)
  const Tag = inline ? 'span' : 'div'
  const html = inline ? renderInlineOnly(content) : renderBlockMarkdown(content)

  useEffect(() => {
    const host = hostRef.current
    if (!host || typeof window === 'undefined') return undefined

    let cancelled = false
    let intervalId = null

    const typeset = () => {
      if (cancelled || !window.MathJax?.typesetPromise) return
      window.MathJax.typesetPromise([host]).catch(() => {})
    }

    if (window.MathJax?.typesetPromise) {
      typeset()
    } else {
      intervalId = window.setInterval(() => {
        if (window.MathJax?.typesetPromise) {
          window.clearInterval(intervalId)
          typeset()
        }
      }, 250)
    }

    return () => {
      cancelled = true
      if (intervalId) {
        window.clearInterval(intervalId)
      }
    }
  }, [html])

  return (
    <Tag
      ref={hostRef}
      className={`md-content ${inline ? 'md-inline' : ''} ${className}`.trim()}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
}
