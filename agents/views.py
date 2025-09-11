from rest_framework import viewsets
from .models import Agent, SyncHistory
from .serializers import AgentSerializer, SyncHistorySerializer


import traceback
from rest_framework.response import Response
from rest_framework import status

class AgentViewSet(viewsets.ModelViewSet):
    queryset = Agent.objects.all()
    serializer_class = AgentSerializer

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            print("❌ Exception occurred during agent creation:")
            print(traceback.format_exc())  # Logs full error stack trace
            return Response({'error': str(e)}, status=500)


class SyncHistoryViewSet(viewsets.ModelViewSet):
    serializer_class = SyncHistorySerializer

    def get_queryset(self):
        queryset = SyncHistory.objects.all().order_by("-started_at")
        agent_id = self.request.query_params.get("agent")
        if agent_id:
            queryset = queryset.filter(agent__id=agent_id)
        return queryset
