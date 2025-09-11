from django.db import models

class Agent(models.Model):
    name = models.CharField(max_length=100)
    last_update = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=50, default="idle")
    realtymx_username = models.CharField(max_length=100, blank=True, null=True)
    realtymx_password = models.CharField(max_length=100, blank=True, null=True)
    limit = models.IntegerField(default=10)
    total = models.IntegerField(default=0)
    progress = models.IntegerField(default=0)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    scheduled = models.DateTimeField(null=True, blank=True)
    interval = models.IntegerField(null=True,blank=True)  

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'agent_data' 


class SyncHistory(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='history')
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    listings_processed = models.IntegerField(default=0)
    status = models.CharField(max_length=50, choices=[
        ("success", "Success"),
        ("failed", "Failed"),
        ("paused", "Paused")
    ])

    def __str__(self):
        return f"{self.agent.name} - {self.status} on {self.started_at.strftime('%Y-%m-%d %H:%M')}"
