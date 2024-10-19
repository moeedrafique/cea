# resources.py
from import_export import resources
from .models import Tehsil, District


class TehsilResource(resources.ModelResource):
    class Meta:
        model = Tehsil
        # You can specify fields to include or exclude here
        # fields = ('id', 'name', 'district', 'latitude', 'longitude')  # Include only specified fields

class DistrictResource(resources.ModelResource):
    class Meta:
        model = District
        # Optionally specify fields to include or exclude
        # fields = ('id', 'name')  # Include only specified fields