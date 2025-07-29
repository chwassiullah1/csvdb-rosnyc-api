from rest_framework import viewsets
from .models import Agent, SyncHistory
from .serializers import AgentSerializer, SyncHistorySerializer


class AgentViewSet(viewsets.ModelViewSet):
    queryset = Agent.objects.all()
    serializer_class = AgentSerializer


class SyncHistoryViewSet(viewsets.ModelViewSet):
    serializer_class = SyncHistorySerializer

    def get_queryset(self):
        queryset = SyncHistory.objects.all().order_by("-started_at")
        agent_id = self.request.query_params.get("agent")
        if agent_id:
            queryset = queryset.filter(agent__id=agent_id)
        return queryset
