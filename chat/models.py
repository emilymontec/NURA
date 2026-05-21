from django.db import models


class ChatSession(models.Model):
    session_id = models.CharField(max_length=120, unique=True)
    title = models.CharField(max_length=200, default="Nueva sesión")
    rolling_summary = models.TextField(blank=True, default="")
    dataset_context = models.JSONField(default=dict, blank=True)
    dataset_history = models.JSONField(default=list, blank=True)
    decision_notes = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.session_id


class ChatMessage(models.Model):
    ROLE_CHOICES = (
        ("system", "System"),
        ("user", "User"),
        ("assistant", "Assistant"),
    )

    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"{self.session.session_id}:{self.role}"
