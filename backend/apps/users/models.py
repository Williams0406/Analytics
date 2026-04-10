from django.contrib.auth.models import AbstractUser
from django.db import models


class LumiqUser(AbstractUser):
    """
    Usuario extendido de Lumiq.
    Usamos AbstractUser para conservar toda la lógica de Django
    y agregar campos propios del negocio.
    """
    email = models.EmailField(unique=True)
    company = models.CharField(max_length=150, blank=True, default='')
    role = models.CharField(
        max_length=50,
        choices=[
            ('owner', 'Owner'),
            ('admin', 'Admin'),
            ('analyst', 'Analyst'),
            ('viewer', 'Viewer'),
        ],
        default='owner',
    )
    avatar_url = models.URLField(blank=True, default='')
    is_onboarded = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_full_name()} <{self.email}>'

    @property
    def full_name(self):
        return self.get_full_name() or self.email