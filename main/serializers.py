# serializers.py
from rest_framework import serializers
from .models import Property, Unit, RealityUser, Job, TemplateDescription


class UploadURLSerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = '__all__'


# class ImageSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Images
#         fields = '__all__'


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = '__all__'



class RealityUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = RealityUser
        fields = '__all__'


class TemplateDescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateDescription
        fields = '__all__'

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = '__all__'


class GetURLSerializer(serializers.ModelSerializer):
    units = serializers.SerializerMethodField()
    class Meta:
        model = Property
        fields = ['url','units','status']

    def get_units(self, obj):
        units = obj.unit_set.all()
        serializer = UnitSerializer(units, many=True)
        return serializer.data

