from rest_framework import serializers


class ReportSerializer(serializers.Serializer):
    def to_representation(self, instance):
        return instance
