'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

import { login } from '@/lib/auth'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'

export default function LoginPage() {
  const router = useRouter()
  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }))
    setError('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      await login(form.email, form.password)
      router.push('/dashboard')
    } catch (err) {
      const msg = err.response?.data?.detail || 'Credenciales incorrectas. Intenta de nuevo.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen px-4 py-8">
      <div className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-6xl items-center justify-center">
        <div className="grid w-full items-center gap-8 lg:grid-cols-[0.92fr_0.78fr]">
          <section className="hidden lg:block">
            <Badge variant="info" className="mb-5">Workspace de analytics + AI</Badge>
            <h1 className="max-w-2xl text-5xl font-semibold leading-[1] text-[var(--text-primary)]">
              Inicia sesion y vuelve a tu centro de decisiones.
            </h1>
            <p className="mt-5 max-w-xl text-base leading-7 text-[var(--text-secondary)]">
              Revisa datasets, schema, presentaciones y respuestas de IA desde una experiencia unificada.
            </p>
          </section>

          <Card variant="elevated" className="mx-auto w-full max-w-md">
            <CardHeader>
              <div className="mb-4 flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[var(--surface-dark)] text-sm font-bold text-white">
                  LQ
                </div>
                <div>
                  <p className="text-lg font-semibold text-[var(--text-primary)]">Lumiq</p>
                  <p className="text-xs text-[var(--text-muted)]">Decision Intelligence</p>
                </div>
              </div>
              <CardTitle>Iniciar sesion</CardTitle>
              <CardDescription>Accede a tu workspace analitico.</CardDescription>
            </CardHeader>

            <CardContent className="pt-1">
              <form onSubmit={handleSubmit} className="space-y-4">
                {error ? (
                  <div className="rounded-[var(--radius-md)] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                    {error}
                  </div>
                ) : null}

                <Input
                  type="email"
                  name="email"
                  label="Correo electronico"
                  value={form.email}
                  onChange={handleChange}
                  required
                  placeholder="tu@empresa.com"
                />

                <Input
                  type="password"
                  name="password"
                  label="Contrasena"
                  value={form.password}
                  onChange={handleChange}
                  required
                  placeholder="********"
                />

                <Button type="submit" loading={loading} className="w-full">
                  {loading ? 'Iniciando sesion...' : 'Entrar al workspace'}
                </Button>
              </form>

              <p className="mt-5 text-center text-sm text-[var(--text-secondary)]">
                No tienes cuenta?{' '}
                <Link href="/register" className="font-medium text-[var(--accent-indigo)] transition hover:opacity-85">
                  Crear cuenta gratis
                </Link>
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </main>
  )
}
