from django.db import models


# Language choices for the story
LANGUAGE_CHOICES = [
    ('english', 'English'),
    ('hindi', 'Hindi'),
    ('kannada', 'Kannada'),
    ('tamil', 'Tamil'),
    ('telugu', 'Telugu'),
]


class ImageStory(models.Model):
    """Stores an uploaded image with its generated cartoon story."""

    image = models.ImageField(upload_to='images/')
    cartoon_image = models.ImageField(upload_to='cartoons/', blank=True, null=True)
    story = models.TextField(blank=True)
    audio = models.FileField(upload_to='audio/', blank=True, null=True)
    language = models.CharField(max_length=50, choices=LANGUAGE_CHOICES, default='english')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Image Stories'

    def __str__(self):
        return f"Story ({self.language}) — {self.created_at.strftime('%d %b %Y %H:%M')}"