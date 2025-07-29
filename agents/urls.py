from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AgentViewSet, SyncHistoryViewSet

router = DefaultRouter()
router.register(r"agents", AgentViewSet, basename="agent")
router.register(r"sync-history", SyncHistoryViewSet, basename="sync-history")

urlpatterns = [
    path("", include(router.urls)),
]
