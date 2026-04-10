'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

import { register } from '@/lib/auth'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'

export default function RegisterPage() {
  const router = useRouter()
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    username: '',
    company: '',
    password: '',
    password_confirm: '',
  })
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }))
    setErrors((prev) => ({ ...prev, [e.target.name]: '' }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setErrors({})

    try {
      await register(form)
      router.push('/dashboard')
    } catch (err) {
      const data = err.response?.data
      if (typeof data === 'object') {
        setErrors(data)
      } else {
        setErrors({ general: 'Error al registrarse. Intenta de nuevo.' })
      }
    } finally {
      setLoading(false)
    }
  }

  const fieldError = (name) => {
    const value = errors[name]
    if (!value) return ''
    return Array.isArray(value) ? value[0] : value
  }

  return (
    <main className="min-h-screen px-4 py-8">
      <div className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-6xl items-center justify-center">
        <div className="grid w-full items-center gap-8 lg:grid-cols-[0.94fr_0.86fr]">
          <section className="hidden lg:block">
            <Badge variant="info" className="mb-5">Onboarding analitico en minutos</Badge>
            <h1 className="max-w-2xl text-5xl font-semibold leading-[1] text-[var(--text-primary)]">
              Crea tu cuenta y empieza a convertir tablas en decisiones.
            </h1>
            <p className="mt-5 max-w-xl text-base leading-7 text-[var(--text-secondary)]">
              Configura tu espacio, carga datasets y obten contexto, insights y presentaciones desde el primer dia.
            </p>
          </section>

          <Card variant="elevated" className="mx-auto w-full max-w-xl">
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
              <CardTitle>Crear cuenta</CardTitle>
              <CardDescription>Activa tu workspace y empieza a explorar tus datos.</CardDescription>
            </CardHeader>

            <CardContent className="pt-1">
              <form onSubmit={handleSubmit} className="space-y-4">
                {errors.general ? (
                  <div className="rounded-[var(--radius-md)] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                    {errors.general}
                  </div>
                ) : null}

                <div className="grid gap-4 sm:grid-cols-2">
                  <Input
                    name="first_name"
                    label="Nombre"
                    value={form.first_name}
                    onChange={handleChange}
                    placeholder="Ana"
                    error={fieldError('first_name')}
                    required
                  />
                  <Input
                    name="last_name"
                    label="Apellido"
                    value={form.last_name}
                    onChange={handleChange}
                    placeholder="Garcia"
                    error={fieldError('last_name')}
                    required
                  />
                </div>

                <Input
                  name="email"
                  type="email"
                  label="Correo electronico"
                  value={form.email}
                  onChange={handleChange}
                  placeholder="ana@empresa.com"
                  error={fieldError('email')}
                  required
                />

                <div className="grid gap-4 sm:grid-cols-2">
                  <Input
                    name="username"
                    label="Usuario"
                    value={form.username}
                    onChange={handleChange}
                    placeholder="anagarcia"
                    error={fieldError('username')}
                    required
                  />
                  <Input
                    name="company"
                    label="Empresa"
                    value={form.company}
                    onChange={handleChange}
                    placeholder="Mi Empresa S.A."
                    error={fieldError('company')}
                    required
                  />
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <Input
                    name="password"
                    type="password"
                    label="Contrasena"
                    value={form.password}
                    onChange={handleChange}
                    placeholder="********"
                    error={fieldError('password')}
                    required
                  />
                  <Input
                    name="password_confirm"
                    type="password"
                    label="Confirmar contrasena"
                    value={form.password_confirm}
                    onChange={handleChange}
                    placeholder="********"
                    error={fieldError('password_confirm')}
                    required
                  />
                </div>

                <Button type="submit" loading={loading} className="w-full">
                  {loading ? 'Creando cuenta...' : 'Crear cuenta gratis'}
                </Button>
              </form>

              <p className="mt-5 text-center text-sm text-[var(--text-secondary)]">
                Ya tienes cuenta?{' '}
                <Link href="/login" className="font-medium text-[var(--accent-indigo)] transition hover:opacity-85">
                  Iniciar sesion
                </Link>
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </main>
  )
}
