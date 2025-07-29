from rest_framework import serializers
from .models import Agent, SyncHistory


class SyncHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncHistory
        fields = "__all__"


class AgentSerializer(serializers.ModelSerializer):
    sync_history = SyncHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Agent
        fields = "__all__"
