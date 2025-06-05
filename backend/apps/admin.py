from django.contrib import admin
from .models import Person, PersonImage, PersonVisiting, Camera, LoginHistory

admin.site.register(Person)
admin.site.register(PersonImage)
admin.site.register(PersonVisiting)
admin.site.register(Camera)
admin.site.register(LoginHistory)