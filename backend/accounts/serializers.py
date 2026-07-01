from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    is_admin = serializers.BooleanField(read_only=True)
    employee_id = serializers.SerializerMethodField()
    nama = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "role", "is_admin", "employee_id", "nama"]

    def get_employee_id(self, obj):
        employee = getattr(obj, "employee", None)
        return employee.id if employee else None

    def get_nama(self, obj):
        employee = getattr(obj, "employee", None)
        return employee.nama if employee else obj.email


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # include user identity so the SPA can route without a second request
        data["user"] = UserSerializer(self.user).data
        return data
