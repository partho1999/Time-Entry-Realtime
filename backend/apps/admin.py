from django.contrib import admin
from .models import Person, PersonImage, PersonVisiting, Camera

admin.site.register(Person)
admin.site.register(PersonImage)
admin.site.register(PersonVisiting)
admin.site.register(Camera)