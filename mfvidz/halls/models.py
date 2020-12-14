from django.db import models
from django.contrib.auth.models import User

class Hall(models.Model):
    title = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class Video(models.Model):
    title = models.CharField(max_length=255)
    url = models.URLField()
    youtube_id = models.CharField(max_length=255)
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE)

class Wiki(models.Model):
    title = models.CharField(max_length=255)
    pageid = models.IntegerField()
    wikitext = models.CharField(max_length=5000)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
