# serializers.py
from rest_framework import serializers
from .models import Property, Unit, RealityUser, Jobs, TemplateDescription, Refresh, Schedule, Scheduleunits, WebTitle


class UploadURLSerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = '__all__'


class RefreshSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refresh
        fields = '__all__'


class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = '__all__'


class ScheduleUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scheduleunits
        fields = '__all__'


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
    # user = RealityUserSerializer()
    class Meta:
        model = Jobs
        fields = '__all__'

# class JobGetSerializer(serializers.ModelSerializer):
#     user = RealityUserSerializer(read_only=True)
#     class Meta:
#         model = Jobs
#         fields = '__all__'

class JobGetSerializer(serializers.ModelSerializer):
    user = RealityUserSerializer(read_only=True)
    urls = serializers.SerializerMethodField()

    class Meta:
        model = Jobs
        fields = '__all__'

    def get_urls(self, obj):
        urls = obj.urls
        if len(urls) > 10:
            summary_sentence = f"There are {len(urls)} property urls in this job"
            return urls[:10] + [summary_sentence]
        return urls


class GetURLSerializer(serializers.ModelSerializer):
    units = serializers.SerializerMethodField()
    class Meta:
        model = Property
        fields = ['url','units','status']

    def get_units(self, obj):
        units = obj.unit_set.all()
        serializer = UnitSerializer(units, many=True)
        return serializer.data

class WebTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebTitle
        fields = ['id', 'web_title']

class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = ['id', 'url']

class UnitFilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ['id']
