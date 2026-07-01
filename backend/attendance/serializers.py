from rest_framework import serializers

from .models import Attendance


class AttendanceSerializer(serializers.ModelSerializer):
    nama = serializers.CharField(source="employee.nama", read_only=True)
    email = serializers.EmailField(source="employee.user.email", read_only=True)

    class Meta:
        model = Attendance
        fields = [
            "id",
            "employee",
            "nama",
            "email",
            "tanggal",
            "jam_masuk",
            "jam_keluar",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
