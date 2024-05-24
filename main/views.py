import csv
import os
import time
from django.utils import timezone
from datetime import timedelta
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from edwin_backend import settings
from scrapy import Selector
from .models import Property, Unit, RealityUser, Jobs, TemplateDescription, Refresh, Schedule, Scheduleunits
# from .utils import scrape_property
from .scrapy import scrape_unit,scrape_property, upload_item
from rest_framework import viewsets
from .serializers import UploadURLSerializer, UnitSerializer, GetURLSerializer, RealityUserSerializer, \
    JobSerializer, TemplateDescriptionSerializer, RefreshSerializer, ScheduleSerializer, ScheduleUnitSerializer, \
    JobGetSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework.filters import OrderingFilter
from rest_framework import generics
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.views import View
from urllib.parse import unquote
from django.http import FileResponse
import os
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from rest_framework.filters import SearchFilter

class UploadUser(APIView):
    def post(self, request):
        data = request.data
        obj=None
        try:
            obj = RealityUser.objects.get(username=data['username'], password=data['password'])
            return Response('User Already Present')
        except:
             serializer = RealityUserSerializer(data={'username': data['username'], 'password':data['password']})
             if serializer.is_valid():
                reality = serializer.save()
                instance_data = model_to_dict(reality)
                return JsonResponse(instance_data)
        return Response('Some Error occured')


class PropertySearchAPIView(generics.ListAPIView):
    queryset = Property.objects.all()
    serializer_class = UploadURLSerializer
    filter_backends = [SearchFilter]
    pagination_class = PageNumberPagination  # Add this line
    pagination_class.page_size = 50
    search_fields = ['url']


# @require_POST
class UpdateStatusAPIView(APIView):
    # def post(self, request):
    #     # Get job ID and status from the request data
    #     job_id = request.data.get('job_id')
    #     new_status = request.data.get('status')
    #
    #     # Update status in Jobs table
    #     try:
    #         job = Jobs.objects.get(id=job_id)
    #         job.status = new_status
    #         job.save()
    #     except Jobs.DoesNotExist:
    #         return Response({'message': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)
    #
    #     # Update status in Unit table
    #     units = Unit.objects.filter(job_id=job_id)
    #     for unit in units:
    #         unit.status = new_status
    #         # unit.isProcessing = True
    #         unit.save()
    #
    #     return Response({'message': 'Status updated successfully'})
    def post(self, request):
        # Get job ID and status from the request data
        job_id = request.data.get('job_id')
        new_status = request.data.get('status')


        # Update status in Jobs table
        try:
            job = Jobs.objects.get(id=job_id)
            if new_status == "paused":
                job.status = "paused"
            elif new_status == "pending":
                if job.scraped_percentage < 100:
                    job.status = "pending"
                else:
                    job.status = "scraped"
            job.save()
        except Jobs.DoesNotExist:
            return Response({'message': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)

        # Update status in Unit table
        units = Unit.objects.filter(job_id=job_id)
        for unit in units:
            if new_status == "paused":
                unit.job_status = "paused"
            elif new_status == "pending":
                unit.job_status = "running"
            unit.save()


        return Response({'message': 'Status updated successfully'})
class RefreshSerializerViewSet(generics.ListCreateAPIView):
    queryset = Refresh.objects.all().order_by('-id')
    serializer_class = RefreshSerializer


class ScheduleViewSet(generics.ListCreateAPIView):
    queryset = Schedule.objects.all().order_by('-id')
    serializer_class = ScheduleSerializer


class ScheduleUnitViewSet(generics.ListAPIView):
    serializer_class = ScheduleUnitSerializer

    def get_queryset(self):
        schedule_id = self.request.query_params.get('schedule_id')
        if schedule_id:
            return Scheduleunits.objects.filter(schedule_id=schedule_id).order_by('-id')
        else:
            return Scheduleunits.objects.all().order_by('-id')


class ScheduleDeleteView(generics.DestroyAPIView):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer


class UpdateAllItems(APIView):
    def patch(self, request):
        # Get the data to update all items
        data = request.data
        Property.objects.update(**data)
        return Response({'message': 'All items updated successfully'})


class UpdateConvertiblesView(APIView):
    def post(self, request):
        # Get the list of IDs and the new field value from the request data
        ids = request.data.get('ids', [])
        new_field_value = request.data.get('value', '')
        # Update the objects based on the received IDs
        Unit.objects.filter(id__in=ids).update(convertible=new_field_value)
        # Serialize and return the updated objects
        updated_objects = Unit.objects.filter(id__in=ids)
        serializer = UnitSerializer(updated_objects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class TemplateDescriptionViewSet(generics.ListCreateAPIView):
    queryset = TemplateDescription.objects.all().order_by('-id')
    serializer_class = TemplateDescriptionSerializer

class TemplateDescriptionDeleteView(generics.DestroyAPIView):
    queryset = TemplateDescription.objects.all()
    serializer_class = TemplateDescriptionSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class UploadImageView(APIView):
    def post(self, request):
        image = request.FILES.get('image')
        status = request.POST.get('status')
        property_id = request.POST.get('property')
        image_type = request.POST.get('type')
        # Save the image to a location
        image_path = default_storage.save('uploads/' + image.name, image)

        # Retrieve the instance of your model based on property_id
        try:
            instance = Property.objects.get(pk=property_id)
        except Property.DoesNotExist:
            return JsonResponse({'error': 'Property not found'}, status=404)

        # Access and update the 'images' JSONField based on status and image_type
        if status in instance.images and image_type in instance.images[status]:
            if(status == 'more'):
                new_object = {'url':image_path, 'key': 1}
                instance.images[status][image_type].append(new_object)
                instance.save()
            else:
                instance.images[status][image_type].append(image_path)
                instance.save()

        # Serialize the instance to a dictionary
        instance_data = model_to_dict(instance)

        return JsonResponse(instance_data)

class UpdateImageView(APIView):
    def post(self,request):
        data = request.data.get('update')
        status = request.data.get('name')
        type = request.data.get('type')
        property_id = request.data.get('property')
        instance = Property.objects.get(pk=property_id)
        instance.images[status][type] = data
        instance.save()
        instance_data = model_to_dict(instance)
        return JsonResponse(instance_data)


class RemoveImageView(APIView):
    def post(self,request):

        status = request.data.get('status')
        property_id = request.data.get('property')
        image_type = request.data.get('type')
        image = request.data.get('url')
        image_path = 'uploads/' + image
        default_storage.delete(image_path)
        instance = Property.objects.get(pk=property_id)
        json_data = instance.images

        if image in json_data[status][image_type]:
            json_data[status][image_type].remove(image)

        # Step 4: Save the updated JSON data back to the model
        instance.images = json_data
        instance.save()
        instance_data = model_to_dict(instance)

        return JsonResponse(instance_data)

class StreetImageListView(generics.ListAPIView):
    serializer_class = UnitSerializer

    def get_queryset(self):
        property_id = self.request.query_params.get('property_id')
        queryset = Unit.objects.filter(property_id=property_id)
        return queryset

# class ImageDeleteView(generics.DestroyAPIView):
#     queryset = Images.objects.all()
#     serializer_class = ImageSerializer

    # def perform_destroy(self, instance):
    #     # Get the image file path
    #     image_path = instance.image.path
    #
    #     # Delete the image record from the database
    #     instance.delete()
    #
    #     # Delete the image file from the folder
    #     if os.path.exists(image_path):
    #         os.remove(image_path)

class JobDetailView(APIView):

    def get(self, request, job_id):
        print('request')
        try:
            job_instance = Jobs.objects.get(id=job_id)
        except Jobs.DoesNotExist:
            return Response({'error': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)

        serialized_data = JobSerializer(job_instance).data
        return Response(serialized_data)


# class JobViewSet(APIView):
#
#     def post(self, request):
#         print('data',request.data)
#         id = None
#         serializer = JobSerializer(data={'urls':request.data})
#         if serializer.is_valid():
#             id = serializer.save()
#         serialized_data = JobSerializer(id).data
#         return Response(serialized_data)

class JobViewSet(generics.ListCreateAPIView, generics.DestroyAPIView):
    queryset = Jobs.objects.all().order_by('-id')

    def get_serializer_class(self):
        # Use different serializer for different actions
        if self.request.method == 'GET':
            return JobGetSerializer  # Serializer for GET requests
        else:
            return JobSerializer
    # serializer_class = JobSerializer

    def get(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        if pk:
            # Retrieve a single object
            job = get_object_or_404(self.get_queryset(), pk=pk)
            serializer = self.get_serializer(job)
            return Response(serializer.data)
        # Otherwise list all objects
        return super().get(request, *args, **kwargs)


class ConvertiblePatchView(generics.UpdateAPIView):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer


class neighbourPatchView(generics.UpdateAPIView):
    queryset = Property.objects.all()
    serializer_class = UploadURLSerializer


class UnitDetailView(APIView):

    def get(self, request, job_id):
        print('request')
        try:
            job_instance = Unit.objects.get(id=job_id)
        except Job.DoesNotExist:
            return Response({'error': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)

        serialized_data = UnitSerializer(job_instance).data
        return Response(serialized_data)

class PropertyCreateView(generics.CreateAPIView):
    def post(self, request):
        serializer = UploadURLSerializer(data={'url': request.data['url'], 'status': request.data['status']})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FileUploadView(APIView):
    def get(self, request):
        properties = Property.objects.order_by('-added_at')
        serializer = UploadURLSerializer(properties, many=True)
        return Response(serializer.data)

    def post(self, request):
        uploaded_file = request.FILES.get('file')
        file_name = uploaded_file.name
        reader = uploaded_file.read().decode('utf-8')
        links = reader.split('\n')

        # Print the individual links
        for link in links:

            serializer = UploadURLSerializer(data={'file': file_name, 'url': link})
            if serializer.is_valid():
                print('hell', link)
                serializer.save()
            else:
                print('not saved',link)
                pass

        return Response({'message': 'File uploaded successfully'})


class PropertyListView(generics.ListAPIView):
    queryset = Property.objects.order_by('-added_at')
    serializer_class = UploadURLSerializer
    pagination_class = PageNumberPagination  # Add this line
    pagination_class.page_size = 50

class JobListView(generics.ListAPIView):
    queryset = Jobs.objects.order_by('-id')
    serializer_class = JobGetSerializer
    pagination_class = PageNumberPagination  # Add this line
    pagination_class.page_size = 50


@api_view(['GET'])
def stop_all_scraper(request):
    props = Property.objects.filter(status='pending')
    for prop in props:
        prop.status = 'stopped'
        prop.isProcessing = 0
        prop.save()
    units = Unit.objects.filter(Q(status='pending') | Q(status='scraped'))
    for unit in units:
        unit.status = 'stopped'
        prop.isProcessing = 0
        unit.save()
    return Response('All scrapers stopped!')

class PropertyView(APIView):
    serializer_class = UploadURLSerializer

    def post(self, request, *args, **kwargs):
        # Get the list of IDs from the request data
        ids = request.data.get('ids', [])
        print('ids',ids)

        if not ids:
            # If no specific IDs are provided, return all properties
            queryset = Property.objects.all().order_by('-added_at')
        else:
            # Filter the queryset based on the provided IDs
            queryset = Property.objects.filter(id__in=ids).order_by('-added_at')

        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

class RealityUserListView(generics.ListAPIView):
    queryset = RealityUser.objects.all()
    serializer_class = RealityUserSerializer

class RealityUserDeleteView(generics.DestroyAPIView):
    queryset = RealityUser.objects.all()
    serializer_class = RealityUserSerializer


class PropertyDeleteView(generics.DestroyAPIView):
    queryset = Property.objects.all()
    serializer_class = UploadURLSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# class UnitListView(APIView):
#     # queryset = Property.objects.order_by('-added_at')[:10]
#     # serializer_class = GetURLSerializer
#
#     def post(self, request):
#         # Access the POST request data using request.data
#         queryset = Property.objects.filter(url__in=request.data)
#         serializer  = GetURLSerializer(queryset, many=True)
#
#         return Response(serializer.data,status=status.HTTP_200_OK)


class UnitsByJobId(APIView):
    def get(self, request, job_id):
        try:
            units = Unit.objects.filter(job__id=job_id)
            serializer = UnitSerializer(units, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class CrawlProperty(APIView):
    def post(self, request):
        for url in request.data:
            if (url['status'] == 'pending'):
                try:
                    prop = Property.objects.get(url=url['url'])
                    # one_day_ago = timezone.now() - timedelta(days=1)
                    # if prop.updated_at < one_day_ago:
                    prop.status = 'pending'
                    prop.isProcessing = 0
                    prop.save()
                    # units = Unit.objects.filter(property_id=url['id'])
                    # units.delete()
                except:
                    serializer = UploadURLSerializer(data={'url': url['url'], 'status': url['status']})
                    if serializer.is_valid():
                        serializer.save()
            if (url['status'] == 'scraped'):
                prop = Property.objects.get(url=url['url'])
                # one_day_ago = timezone.now() - timedelta(days=1)
                # if prop.updated_at < one_day_ago:
                prop.status = 'pending'
                prop.isProcessing = 0
                prop.save()

        return Response('Working')

class EditCrawlProperty(APIView):
    def post(self, request):
        property_url = next(iter(request.data.keys()))
        prop = Unit.objects.get(url=property_url)
        if (prop.status == 'scraped'):
            print('already scraped')
            serializer = UnitSerializer(prop)
            return Response(serializer.data)
        item = scrape_unit(property_url)
        updated_reality =None
        # item['status'] = 'scraped'
        serializer = UnitSerializer(instance=prop, data=item,partial=True)
        if serializer.is_valid():
            updated_reality = serializer.save()
        # prop.status = 'scraped'
        # prop.__dict__.update(**item)
        # data = prop.save()
        serialized_data = UnitSerializer(updated_reality).data
        return Response(serialized_data)


class UpdateProperty(APIView):
    def post(self, request):
        unit = Unit.objects.get(id=request.data['id'])
        unit.price = request.data['price']  # Update the price field
        unit.save()
        serialized_unit = UnitSerializer(unit)
        item = upload_item(serialized_unit.data)
        unit.status = 'uploaded'
        unit.save()
        return Response(item)


def view_properties(request):
    raw_properties = Property.objects.order_by('-added_at')
    properties = []
    for raw_property in raw_properties:
        properties.append({
            'id': raw_property.id,
            'url': raw_property.url,
            'title': raw_property.url.split('/')[-1].replace('-', ' ').replace('_', ' '),
            'file':raw_property.file,
            'added_at':raw_property.added_at,

        })

    return render(request, 'view_properties.html', {'properties': properties})


def crawl_property(request, property_url):
    if request.method == 'POST':
        Unit.objects.all().delete()

        units = scrape_property(property_url)
        for unit in units:
            Unit.objects.get_or_create(url=unit['url'])

        context = {
            'property_url': property_url,
            'units': units
        }
        return render(request, "crawl_property.html", context)

    return render(request, "crawl_property.html", {'property_url': property_url})


def edit_property(request, web_unit_url):
    if request.method == "POST":
        property = Unit.objects.get(url=web_unit_url)
        headers = {
            'authority': 'streeteasy.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        }
        response = requests.get(property.url, headers=headers)
        response = Selector(text=response.text)
        item = {'title': response.css(".building-title a::text").get('').split(" #")[0],
                'unit': response.css(".building-title a::text").get('').split(" #")[-1],
                'complete_title': response.css(".building-title a::text").get('')}
        raw_price = " ".join([i.strip() for i in response.css(".price *::text").extract() if i.strip()])
        beds = response.css(".detail_cell:nth-child(4)::text").get()
        item['beds'] = 0
        if "beds" in beds:
            item['beds'] = beds.split(" ")[0]

        baths = response.css(".last_detail_cell::text").get('').split(" ")[0]
        item['baths'] = baths
        item['price'] = raw_price.split(" $")[-1].split(" ")[0]
        item['Image_Urls'] = ','.join(
            [x for x in response.css('.jsFlickityImageWrapper img::attr(data-src-original)').extract()])
        item['Image_Path'] = [f"images/{count + 1}.jpg" for count in
                              range(0, len(item['Image_Urls'].split(',')))]
        for index, image_url in enumerate(item.get('Image_Urls', []).split(','), start=1):
            img_data = requests.get(url=image_url, headers=headers)
            if img_data.status_code == 200:
                if not os.path.exists(f"images/{item['complete_title']}"):
                    os.makedirs(f"images/{item['complete_title']}")
                with open(f"images/{item['complete_title']}/{index}.jpg", 'wb') as handler:
                    handler.write(img_data.content)
            else:
                print('Unable to get Response')
        return render(request, 'edit_property.html', {'item': item, 'url':property.url })
        # return render(request, 'edit_property.html')
    return render(request, 'edit_property.html', {'property_url': web_unit_url})

class MultiUpdateProperty(APIView):
    def post(self, request):
        data = request.data
        print('request.data', request.data)

        first_unit_id = data['ids'][0]
        first_unit = Unit.objects.get(id=first_unit_id)
        job_id = first_unit.job_id

        try:
            job = Jobs.objects.get(id=job_id)
            job.status = 'pending'
            job.save()
        except Jobs.DoesNotExist:
            # Handle the case where the job with the given ID does not exist
            return Response({'message': f'Job with ID {job_id} does not exist'}, status=status.HTTP_404_NOT_FOUND)

        for id in data['ids']:
            prop = Unit.objects.get(id=id)
            prop.status = 'pending'
            prop.job_status = 'running'
            prop.isProcessing = 0
            # prop.reality_user = data['reality_user']
            prop.save()
        return Response('Uploading Started')

