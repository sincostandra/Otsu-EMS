import secrets

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from .models import Employee

User = get_user_model()


class EmployeeSerializer(serializers.ModelSerializer):
    """Serialize an Employee, provisioning/updating its login account.

    ``email`` and ``password`` live on the User; everything else on Employee.
    On create, if no password is given we generate a temp one and surface it
    once (as ``temp_password``) so the admin can hand it to the new hire.
    """

    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True, required=False, allow_blank=True, min_length=8
    )

    class Meta:
        model = Employee
        fields = [
            "id",
            "nama",
            "email",
            "jabatan",
            "tanggal_masuk",
            "status_aktif",
            "password",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_email(self, value):
        qs = User.objects.filter(email__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.user_id)
        if qs.exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        email = validated_data.pop("email")
        password = validated_data.pop("password", "") or secrets.token_urlsafe(9)
        user = User.objects.create_user(
            email=email, password=password, role=User.Role.EMPLOYEE
        )
        employee = Employee.objects.create(user=user, **validated_data)
        # Stashed so to_representation can reveal it once (create only).
        employee._temp_password = password
        return employee

    @transaction.atomic
    def update(self, instance, validated_data):
        email = validated_data.pop("email", None)
        password = validated_data.pop("password", None)
        user = instance.user
        if email and email != user.email:
            user.email = email
        if password:
            user.set_password(password)
        user.save()
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        temp = getattr(instance, "_temp_password", None)
        if temp:
            data["temp_password"] = temp
        return data
