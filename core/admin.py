from django.contrib import admin
from .models import User, Property, PropertyImage, UserProperty, PropertyDocument

# Register your models here.
admin.site.register(User)
admin.site.register(Property)
admin.site.register(PropertyImage)
admin.site.register(UserProperty)
admin.site.register(PropertyDocument)
