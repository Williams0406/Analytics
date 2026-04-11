from rest_framework import serializers
from .models import AIInsight


class AIInsightSerializer(serializers.ModelSerializer):
    insight_type_display = serializers.CharField(
        source='get_insight_type_display', read_only=True
    )
    priority_display = serializers.CharField(
        source='get_priority_display', read_only=True
    )
    presentation = serializers.SerializerMethodField()

    def get_presentation(self, obj):
        if isinstance(obj.metrics_context, dict):
            return obj.metrics_context.get('presentation')
        return None

    class Meta:
        model = AIInsight
        fields = [
            'id', 'insight_type', 'insight_type_display',
            'priority', 'priority_display', 'title', 'content',
            'presentation',
            'is_read', 'is_starred', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']
