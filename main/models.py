from django.db import models
from django.contrib.auth.models import User


from django.db import models

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default="#FFFFFF")  # Hex цветен код

    def __str__(self):
        return self.name



class Contact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Връзка с потребителя
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    company_name = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    comment = models.TextField(blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="contacts")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"




