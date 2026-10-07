from django.db import models
from django.contrib.auth.models import User


# chat history, following peer practice 6.4.6. That exercise has no sender
# field because its project has no login; this one does.
# There is no ChatRoom table: as in topic 6, a room is just a name in the
# URL and exists because someone joined it
class Message(models.Model):
    room_name = models.CharField(max_length=256, db_index=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message_text = models.TextField(null=False, blank=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        # ascending: a transcript reads oldest first. Per 6.4.6
        ordering = ['timestamp']

    def __str__(self):
        return "["+self.room_name+"] "+self.message_text[:50]
