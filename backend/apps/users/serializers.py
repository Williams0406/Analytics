from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import LumiqUser


class LumiqTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extiende el JWT para incluir datos del usuario en el token.
    El frontend puede decodificar el token y obtener info básica
    sin hacer un request extra.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Claims personalizados dentro del JWT
        token['email'] = user.email
        token['full_name'] = user.full_name
        token['role'] = user.role
        token['company'] = user.company
        token['is_onboarded'] = user.is_onboarded
        return token


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer para el registro de nuevos usuarios."""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
    )
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = LumiqUser
        fields = [
            'email', 'username', 'first_name', 'last_name',
            'password', 'password_confirm', 'company',
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password': 'Las contraseñas no coinciden.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = LumiqUser(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer para ver y actualizar el perfil."""
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = LumiqUser
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'full_name', 'company', 'role', 'avatar_url',
            'is_onboarded', 'created_at',
        ]
        read_only_fields = ['id', 'email', 'role', 'created_at']


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer para cambio de contraseña."""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('La contraseña actual es incorrecta.')
        return value