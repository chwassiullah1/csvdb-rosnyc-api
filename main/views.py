import csv
import os
import re
import time
from django.utils import timezone
from datetime import timedelta
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from edwin_backend import settings
from scrapy import Selector
from .models import Property, Unit, RealityUser, Jobs, TemplateDescription, Refresh, Schedule, Scheduleunits, WebTitle
# from .utils import scrape_property
from .scrapy import scrape_unit,scrape_property, upload_item
from rest_framework import viewsets
from .serializers import UploadURLSerializer, UnitSerializer, GetURLSerializer, RealityUserSerializer, \
    JobSerializer, TemplateDescriptionSerializer, RefreshSerializer, ScheduleSerializer, ScheduleUnitSerializer, \
    JobGetSerializer, WebTitleSerializer, PropertySerializer, UnitFilterSerializer
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
from django.db.models import F, FloatField
from django.db.models.functions import Cast
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist

class CustomPagination(PageNumberPagination):
    page_size = 100  # Set the page size to 500
    page_size_query_param = 'page_size'  # Optional: allow users to override page size via query params
    max_page_size = 1000  # Optional: set a maximum limit for page size
    def get_paginated_response(self, data):
        response = super().get_paginated_response(data)

        # Fix the `next` URL to include '/api/' if missing
        if response.data.get('next'):
            response.data['next'] = response.data['next'].replace('/get_prop/', '/api/get_prop/').replace('http','https').replace('/properties/','/api/properties/')

        # Fix the `previous` URL to include '/api/' if missing
        if response.data.get('previous'):
            response.data['previous'] = response.data['previous'].replace('/get_prop/', '/api/get_prop/').replace('http','https').replace('/properties/','/api/properties/')

        return response


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


# class PropertySearchAPIView(generics.ListAPIView):
#     queryset = Property.objects.all()
#     serializer_class = UploadURLSerializer
#     filter_backends = [SearchFilter]
#     pagination_class = PageNumberPagination  # Add this line
#     pagination_class.page_size = 50
#     search_fields = ['url']

from rest_framework import generics
from django.db.models import Q

from rest_framework import generics
from django.db.models import Q
from .models import Property
from .serializers import UploadURLSerializer


class PropertySearchAPIView(generics.ListAPIView):
    serializer_class = UploadURLSerializer
    filter_backends = [SearchFilter]
    pagination_class = CustomPagination
    # pagination_class.page_size = 100

    def get_queryset(self):
        prop_types = self.request.query_params.getlist('prop_type')  # Fetch list of prop_types
        search_url = self.request.query_params.get('search_url', None)
        search_neighbourhood = self.request.query_params.get('search_neighbourhood', None)


        queryset = Property.objects.all()  # Base query for all properties

        # Filter by property types
        if prop_types:
            query = Q()
            for prop_type in prop_types:
                query |= Q(prop_type__icontains=prop_type)
            queryset = queryset.filter(query)

        # Filter by search URL
        if search_url:
            queryset = queryset.filter(url__icontains=search_url)
            # search_urls = [
            #     re.sub(r'[^\w\s]', '', n).strip() for n in search_url.split(',')
            # ]
            # search_urls = [n for n in search_urls if n]
            # if len(search_urls) == 1:
            #     # Use exact match for a single neighborhood
            #     queryset = queryset.filter(url__icontains=search_urls[0])
            # else:
            #     # Apply an OR condition for each neighbourhood using partial match
            #     query = Q()
            #     for url in search_urls:
            #         query |= Q(url__icontains=url)
            #     queryset = queryset.filter(query)

        # Filter by search neighbourhoods
        if search_neighbourhood:
            # Sanitize by removing any special characters using regex
            neighbourhoods = [
                re.sub(r'[^\w\s]', '', n).strip() for n in search_neighbourhood.split(',')
            ]

            # Remove any empty values after cleaning
            neighbourhoods = [n for n in neighbourhoods if n]

            if len(neighbourhoods) == 1:
                # Use exact match for a single neighborhood
                queryset = queryset.filter(area__icontains=neighbourhoods[0])
            else:
                # Apply an OR condition for each neighbourhood using partial match
                query = Q()
                for neighbourhood in neighbourhoods:
                    query |= Q(area__icontains=neighbourhood)
                queryset = queryset.filter(query)

        return queryset


# @require_POST
class UpdateStatusAPIView(APIView):
    def post(self, request):
        job_id = request.data.get('job_id')
        new_status = request.data.get('status')

        # Validate job_id and status
        if not job_id:
            return Response({'error': 'job_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        if new_status not in ["paused", "pending"]:
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)

        # Update status in Jobs table
        try:
            job = Jobs.objects.get(id=job_id)
            if new_status == "paused":
                job.status = "paused"
            elif new_status == "pending":
                job.status = "pending" if job.scraped_percentage < 100 else "scraped"
            job.save()
        except Jobs.DoesNotExist:
            return Response({'message': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)

        # Update status in Unit table using bulk update
        units = Unit.objects.filter(job_id=job_id)
        if new_status == "paused":
            units.update(job_status="paused")
        elif new_status == "pending":
            units.update(job_status="running")

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

    import re

    def post(self, request, *args, **kwargs):
        data = request.data
        # filters = data.get('filters')  # Get filters from request

        # if data.get('scrapAll'):
        #     if filters:
        #         # Apply filters to properties
        #         search_prop = filters.get('search_prop', '')
        #         search_neighbour = filters.get('search_neighbour', '')
        #         prop_types = filters.get('prop_type', [])  # Expecting a list of property types
        #
        #         # Start with all properties
        #         properties = Property.objects.all()
        #
        #         # Filter by search_prop if provided
        #         if search_prop:
        #             properties = properties.filter(url__icontains=search_prop)
        #
        #         # Filter by search_neighbourhood if provided
        #         if search_neighbour:
        #             # Sanitize by removing any special characters using regex
        #             neighbourhoods = [
        #                 re.sub(r'[^\w\s]', '', n).strip() for n in search_neighbour.split(',')
        #             ]
        #
        #             # Remove any empty values after cleaning
        #             neighbourhoods = [n for n in neighbourhoods if n]
        #
        #             # Apply an OR condition for each neighbourhood
        #             query = Q()
        #             for neighbourhood in neighbourhoods:
        #                 query |= Q(area__icontains=neighbourhood)
        #
        #             # Apply the neighbourhood filtering
        #             properties = properties.filter(query)
        #
        #         # Filter by property types if provided
        #         if prop_types:
        #             # Apply filtering for multiple property types
        #             query = Q()
        #             for prop_type in prop_types:
        #                 query |= Q(prop_type__icontains=prop_type)
        #
        #             # Apply the property type filtering
        #             properties = properties.filter(query)
        #
        #     else:
        #         # No filters, scrape all properties
        #         properties = Property.objects.all()
        #     # Final count after all filters
        #     urls = [prop.url for prop in properties]
        #     job_data = {
        #         'user': data.get('user'),
        #         'urls': urls,
        #         'status': data.get('status', 'pending')
        #     }
        #     serializer = self.get_serializer(data=job_data)
        #
        # else:
        #     # Normal job creation with provided URLs
        #     serializer = self.get_serializer(data=data)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # def post(self, request, *args, **kwargs):
    #     data = request.data
    #     filters = data.get('filters')  # Get filters from request
    #
    #     if data.get('scrapAll'):
    #         if filters:
    #             # Apply filters to properties
    #             search_prop = filters.get('search_prop', '')
    #             search_neighbour = filters.get('search_neighbour', '')
    #             prop_type = filters.get('prop_type', '')
    #
    #             # Filter properties based on the provided filters
    #             properties = Property.objects.all()
    #
    #             if search_prop:
    #                 properties = properties.filter(url__icontains=search_prop)
    #
    #             if search_neighbour:
    #                 properties = properties.filter(area__icontains=search_neighbour)
    #
    #             if prop_type:
    #                 properties = properties.filter(prop_type__icontains=prop_type)
    #
    #         else:
    #             # No filters, scrape all properties
    #             properties = Property.objects.all()
    #
    #         urls = [prop.url for prop in properties]
    #         job_data = {
    #             'user': data.get('user'),
    #             'urls': urls,
    #             'status': data.get('status', 'pending')
    #         }
    #         serializer = self.get_serializer(data=job_data)
    #
    #     else:
    #         # Normal job creation with provided URLs
    #         serializer = self.get_serializer(data=data)
    #
    #     serializer.is_valid(raise_exception=True)
    #     self.perform_create(serializer)
    #     return Response(serializer.data, status=status.HTTP_201_CREATED)
    # def post(self, request, *args, **kwargs):
    #     data = request.data
    #     if data.get('scrapAll'):
    #         # Logic to create a job with all properties from the database
    #         properties = Property.objects.all()
    #         urls = [prop.url for prop in properties]
    #         job_data = {
    #             'user': data.get('user'),
    #             'urls': urls,
    #             'status': data.get('status', 'pending')
    #         }
    #         serializer = self.get_serializer(data=job_data)
    #     else:
    #         # Normal job creation with provided URLs
    #         serializer = self.get_serializer(data=data)
    #
    #     serializer.is_valid(raise_exception=True)
    #     self.perform_create(serializer)
    #     return Response(serializer.data, status=status.HTTP_201_CREATED)


class ConvertiblePatchView(generics.UpdateAPIView):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer


class neighbourPatchView(generics.UpdateAPIView):
    queryset = Property.objects.all()
    serializer_class = UploadURLSerializer


class UnitDetailView(APIView):

    def get(self, request, job_id):
        print('request',job_id)
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

class LargeResultsSetPagination(PageNumberPagination):
    page_size = 5000
    page_size_query_param = 'page_size'
    # max_page_size = 10000


class PropertyListView(generics.ListAPIView):
    queryset = Property.objects.order_by('-added_at')
    serializer_class = UploadURLSerializer
    pagination_class = CustomPagination  # Add this line
    # pagination_class.page_size = 500
    # pagination_class = PageNumberPagination  # Add this line
    # pagination_class = LargeResultsSetPagination
    # pagination_class.page_size = 1000

class JobListView(generics.ListAPIView):
    queryset = Jobs.objects.order_by('-id')
    serializer_class = JobGetSerializer
    pagination_class = PageNumberPagination  # Add this line
    pagination_class.page_size = 100


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


# class UnitsByJobId(APIView):
#
#     def get(self, request, job_id):
#         try:
#             units = Unit.objects.filter(job__id=job_id)
#             serializer = UnitSerializer(units, many=True)
#             return Response(serializer.data)
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UnitsByJobId(generics.ListAPIView):
    serializer_class = UnitSerializer
    pagination_class = CustomPagination
    # pagination_class.page_size = 100

    def get_queryset(self):
        job_id = self.kwargs['job_id']
        return Unit.objects.filter(job__id=job_id).order_by('id')



class UnitJobStatusAPIView(APIView):
    def get(self, request, job_id):
        try:
            units = Unit.objects.filter(job_id=job_id)

            # Count the units based on status
            total_units = units.count()
            uploaded_units = units.filter(status='uploaded').count()
            uploading_error_units = units.filter(status='uploading error').count()
            not_found_units = units.filter(status='not found').count()
            duplicate_listing_units = units.filter(status='duplicate listing').count()
            scraping_error_units = units.filter(status='scraping error').count()

            # Return the counts as a response
            data = {
                'total_units': total_units,
                'uploaded_units': uploaded_units,
                'uploading_error_units': uploading_error_units,
                'not_found_units': not_found_units,
                'duplicate_listing_units': duplicate_listing_units,
                'scraping_error_units': scraping_error_units
            }
            return Response(data, status=status.HTTP_200_OK)

        except Unit.DoesNotExist:
            return Response({'error': 'Units not found for the specified job'}, status=status.HTTP_404_NOT_FOUND)

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
    # def post(self, request):
    #     property_url = next(iter(request.data.keys()))
    #     try:
    #         prop = Unit.objects.get(url=property_url)
    #     except Unit.DoesNotExist:
    #         return Response({"error": "Property not found."}, status=404)
    #     except MultipleObjectsReturned:
    #         return Response({"error": "Multiple properties found for the given URL."}, status=400)
    #
    #     if prop.status == 'scraped':
    #         print('already scraped')
    #         serializer = UnitSerializer(prop)
    #         return Response(serializer.data)
    #
    #     item = scrape_unit(property_url)
    #     updated_reality = None
    #     serializer = UnitSerializer(instance=prop, data=item, partial=True)
    #     if serializer.is_valid():
    #         updated_reality = serializer.save()
    #
    #     serialized_data = UnitSerializer(updated_reality).data
    #     return Response(serialized_data)
    def post(self, request):
        property_url = request.data.get('url')
        job_id = request.data.get('job_id')

        print(job_id)
        # Validate input data
        if not property_url or not job_id:
            print("Error in if not")
            return Response({"error": "Missing url or job_id."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Attempt to get the Unit object
            prop = Unit.objects.get(url=property_url, job_id=job_id)
        except ObjectDoesNotExist:
            return Response({"error": "Property not found."}, status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned:
            return Response({"error": "Multiple properties found for the given URL and job ID."}, status=status.HTTP_400_BAD_REQUEST)

        print(prop.status)
        if prop.status == 'scraped':
            print('already scraped')
            serializer = UnitSerializer(prop)
            return Response(serializer.data)
        else:
            print("Innside else")
            # Scrape the unit
            item = scrape_unit(property_url)
            print(item)
            updated_reality = None
            # Update the Unit object with scraped data
            serializer = UnitSerializer(instance=prop, data=item, partial=True)
            print(serializer)
            if serializer.is_valid():
                try:
                    updated_reality = serializer.save()
                    print(updated_reality)
                except Exception as e:
                    print(f'Exception{e}')
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Serialize and return the updated data
            serialized_data = UnitSerializer(updated_reality).data
            return Response(serialized_data, status=status.HTTP_200_OK)


# class UpdateProperty(APIView):
#     def post(self, request):
#         unit = Unit.objects.get(id=request.data['id'])
#         unit.price = request.data['price']  # Update the price field
#         unit.save()
#         serialized_unit = UnitSerializer(unit)
#         item = upload_item(serialized_unit.data)
#         unit.status = 'uploaded'
#         unit.save()
#         return Response(item)

class UpdateProperty(APIView):
    def post(self, request):
        try:
            # Ensure 'id' and 'price' are present in the request data
            unit_id = request.data.get('id')
            new_price = request.data.get('price')

            if unit_id is None or new_price is None:
                return Response({"error": "ID and price are required"}, status=status.HTTP_400_BAD_REQUEST)

            # Retrieve the Unit object by ID
            unit = Unit.objects.get(id=unit_id)

            # Update the price field
            unit.price = new_price
            unit.save()

            # Serialize the updated unit
            serialized_unit = UnitSerializer(unit)

            # Upload the item
            try:
                item = upload_item(serialized_unit.data)
            except Exception as e:
                return Response({"error": f"Error uploading item: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Update the status field and save
            unit.status = 'uploaded'
            unit.save()

            return Response(item, status=status.HTTP_200_OK)

        except Unit.DoesNotExist:
            return Response({"error": "Unit not found"}, status=status.HTTP_404_NOT_FOUND)
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Log the exception for debugging
            print(f"Server error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            [x for x in response.xpath("//div[@class='swiper-slide']/div//img/@src").getall()])
        item['Image_Path'] = [f"images/{count + 1}.jpg" for count in
                              range(0, len(item['Image_Urls'].split(',')))]
        proxies = {
            scheme: "http://bd362c1973d7411ebcd558337599ce01:@api.zyte.com:8011" for scheme in ("http", "https")
        }
        for index, image_url in enumerate(item.get('Image_Urls', []).split(','), start=1):
            img_data = requests.get(url=image_url, headers=headers,proxies=proxies, verify='zyte-ca.crt')
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

# class MultiUpdateProperty(APIView):
#     def post(self, request):
#         data = request.data
#         print('request.data', request.data)
#
#         first_unit_id = data['ids'][0]
#         first_unit = Unit.objects.get(id=first_unit_id)
#         job_id = first_unit.job_id
#
#         try:
#             job = Jobs.objects.get(id=job_id)
#             job.status = 'pending'
#             job.save()
#         except Jobs.DoesNotExist:
#             # Handle the case where the job with the given ID does not exist
#             return Response({'message': f'Job with ID {job_id} does not exist'}, status=status.HTTP_404_NOT_FOUND)
#
#         for id in data['ids']:
#             prop = Unit.objects.get(id=id)
#             prop.status = 'pending'
#             prop.job_status = 'running'
#             prop.isProcessing = 0
#             # prop.reality_user = data['reality_user']
#             prop.save()
#         return Response('Uploading Started')


class MultiUpdateProperty(APIView):
    def post(self, request):
        data = request.data
        job_id = data.get('jobId')


        if 'ids' not in data or not data['ids']:
            return Response({'error': 'At least one id or scrapAll=true is required'},
                                status=status.HTTP_400_BAD_REQUEST)

            # Process specific units by their IDs
        units = Unit.objects.filter(id__in=data['ids'])

        try:
            job = Jobs.objects.get(id=job_id)
        except Jobs.DoesNotExist:
            return Response({'message': f'Job with ID {job_id} does not exist'}, status=status.HTTP_404_NOT_FOUND)

            # Job Status Update Logic
        if job.status == 'scraped':
                # For 'scraped' status: clear old unit_ids and save new unit_ids
            job.unit_ids = list(units.values_list('id', flat=True))  # Save the new units' IDs
            job.status = 'pending'
            job.scraped_percentage = 0
            job.save()

        elif job.status == 'pending':
                # For 'pending' status: check and update unit_ids without duplicates
            new_unit_ids = set(units.values_list('id', flat=True))
            existing_unit_ids = set(job.unit_ids)
            # print("Total units in request:", units.count())  # Total count of units from the request
            # print("New unit IDs count:", len(new_unit_ids))  # Count of new unit IDs
            # print("Existing unit IDs count:", len(existing_unit_ids))  # Count of existing unit IDs in the job

                # Find the unique units to be saved
            unique_unit_ids = new_unit_ids - existing_unit_ids
            # print("Unique unit IDs to add:", len(unique_unit_ids))
                # Update the job.unit_ids with new unique unit_ids
            job.unit_ids = list(existing_unit_ids | unique_unit_ids)

                # Remove the duplicate units from the original units queryset
            units = units.exclude(id__in=existing_unit_ids)
            job.status = 'pending'
            job.scraped_percentage = 0
            job.save()
        # print("Total Count",units.count())
        # Process each unit
        for unit in units:
            unit.status = 'pending'
            unit.job_status = 'running'
            unit.isProcessing = 4
            unit.save()

        return Response('Uploading Started')
    # def post(self, request):
    #     data = request.data
    #
    #     if data.get('scrapAll', False):
    #         job_id = data.get('jobId')
    #         if job_id is None:
    #             return Response({'error': 'Job ID is required for scrapAll operation'},
    #                             status=status.HTTP_400_BAD_REQUEST)
    #
    #         try:
    #             job = Jobs.objects.get(id=job_id)
    #         except Jobs.DoesNotExist:
    #             return Response({'message': f'Job with ID {job_id} does not exist'}, status=status.HTTP_404_NOT_FOUND)
    #
    #         # If filters are applied, filter the units accordingly
    #         filters = data.get('filters', {})
    #         units = Unit.objects.filter(job_id=job_id)
    #
    #         if filters:
    #             # Handle price filtering
    #             min_price = filters.get('min_price')
    #             max_price = filters.get('max_price')
    #             if min_price and max_price:
    #                 min_price = float(min_price)
    #                 max_price = float(max_price)
    #                 units = units.annotate(
    #                     price_as_float=Cast(F('price'), FloatField())
    #                 ).filter(
    #                     price_as_float__gte=min_price,
    #                     price_as_float__lte=max_price
    #                 ).order_by('price_as_float')
    #
    #             # Handle no_of_beds filtering
    #             no_of_beds = filters.get('no_of_beds')
    #             if no_of_beds:
    #                 if no_of_beds == '0':
    #                     units = units.filter(beds__in=['', '0'])
    #                 elif no_of_beds in ['1', '2', '3']:
    #                     units = units.filter(beds=no_of_beds)
    #                 else:
    #                     units = units.annotate(beds_as_int=Cast('beds', IntegerField()))
    #                     units = units.filter(beds_as_int__gt=3)
    #
    #             # Handle no_of_baths filtering
    #             no_of_baths = filters.get('no_of_baths')
    #             if no_of_baths:
    #                 if no_of_baths == '0':
    #                     units = units.filter(baths__in=['', '0'])
    #                 elif no_of_baths in ['1', '2', '3']:
    #                     units = units.filter(baths=no_of_baths)
    #                 else:
    #                     units = units.annotate(baths_as_int=Cast('baths', IntegerField()))
    #                     units = units.filter(baths_as_int__gt=3)
    #
    #         # Debugging print: show counts and IDs for both units and job.unit_ids
    #         # print(f"Filtered units count: {units.count()}, Unit IDs: {list(units.values_list('id', flat=True))}")
    #         # print(f"Job unit_ids count: {len(job.unit_ids)}, Job unit_ids: {job.unit_ids}")
    #
    #         # Job Status Update Logic
    #         if job.status == 'scraped':
    #             # For 'scraped' status: clear old unit_ids and save new unit_ids
    #             job.unit_ids = list(units.values_list('id', flat=True))  # Save the filtered units' IDs
    #             job.status = 'pending'
    #             job.save()
    #
    #         elif job.status == 'pending':
    #             # For 'pending' status: check and update unit_ids without duplicates
    #             new_unit_ids = set(units.values_list('id', flat=True))
    #             existing_unit_ids = set(job.unit_ids)
    #
    #             # Debugging print: show counts and IDs before the updates
    #             # print(f"New unit_ids count: {len(new_unit_ids)}, New unit_ids: {new_unit_ids}")
    #             # print(f"Existing unit_ids count: {len(existing_unit_ids)}, Existing unit_ids: {existing_unit_ids}")
    #
    #             # Find the unique units to be saved
    #             unique_unit_ids = new_unit_ids - existing_unit_ids
    #
    #             # Debugging print: show unique unit IDs
    #             # print(f"Unique unit_ids to save: {unique_unit_ids}")
    #
    #             # Update the job.unit_ids with new unique unit_ids
    #             job.unit_ids = list(existing_unit_ids | unique_unit_ids)
    #
    #             # Remove the duplicate units from the original units queryset
    #             units = units.exclude(id__in=existing_unit_ids)
    #             job.status = 'pending'
    #             job.save()
    #
    #     else:
    #         # print("ids", data['ids'])
    #         if 'ids' not in data or not data['ids']:
    #             return Response({'error': 'At least one id or scrapAll=true is required'},
    #                             status=status.HTTP_400_BAD_REQUEST)
    #
    #         # Process specific units by their IDs
    #         units = Unit.objects.filter(id__in=data['ids'])
    #
    #         # Get the job_id from the first unit to update the job status
    #         first_unit_id = data['ids'][0]
    #         first_unit = Unit.objects.get(id=first_unit_id)
    #         job_id = first_unit.job_id
    #
    #         try:
    #             job = Jobs.objects.get(id=job_id)
    #         except Jobs.DoesNotExist:
    #             return Response({'message': f'Job with ID {job_id} does not exist'}, status=status.HTTP_404_NOT_FOUND)
    #
    #         # Debugging print: show counts and IDs for both units and job.unit_ids
    #         # print(f"Selected units count: {units.count()}, Unit IDs: {list(units.values_list('id', flat=True))}")
    #         # print(f"Job unit_ids count: {len(job.unit_ids)}, Job unit_ids: {job.unit_ids}")
    #
    #         # Job Status Update Logic
    #         if job.status == 'scraped':
    #             # For 'scraped' status: clear old unit_ids and save new unit_ids
    #             job.unit_ids = list(units.values_list('id', flat=True))  # Save the new units' IDs
    #             job.status = 'pending'
    #             job.save()
    #
    #         elif job.status == 'pending':
    #             # For 'pending' status: check and update unit_ids without duplicates
    #             new_unit_ids = set(units.values_list('id', flat=True))
    #             existing_unit_ids = set(job.unit_ids)
    #
    #             # Debugging print: show counts and IDs before the updates
    #             # print(f"New unit_ids count: {len(new_unit_ids)}, New unit_ids: {new_unit_ids}")
    #             # print(f"Existing unit_ids count: {len(existing_unit_ids)}, Existing unit_ids: {existing_unit_ids}")
    #
    #             # Find the unique units to be saved
    #             unique_unit_ids = new_unit_ids - existing_unit_ids
    #
    #             # Debugging print: show unique unit IDs
    #             # print(f"Unique unit_ids to save: {unique_unit_ids}")
    #
    #             # Update the job.unit_ids with new unique unit_ids
    #             job.unit_ids = list(existing_unit_ids | unique_unit_ids)
    #
    #             # Remove the duplicate units from the original units queryset
    #             units = units.exclude(id__in=existing_unit_ids)
    #             job.status = 'pending'
    #             job.save()
    #     # Process each unit
    #     for unit in units:
    #         unit.status = 'pending'
    #         unit.job_status = 'running'
    #         unit.isProcessing = 0
    #         unit.save()
    #
    #     return Response('Uploading Started')
    # def post(self, request):
    #     data = request.data
    #     # print('request.data', request.data)
    #
    #     if data.get('scrapAll', False):
    #         job_id = data.get('jobId')
    #         if job_id is None:
    #             return Response({'error': 'Job ID is required for scrapAll operation'},
    #                             status=status.HTTP_400_BAD_REQUEST)
    #
    #         try:
    #             job = Jobs.objects.get(id=job_id)
    #         except Jobs.DoesNotExist:
    #             return Response({'message': f'Job with ID {job_id} does not exist'}, status=status.HTTP_404_NOT_FOUND)
    #
    #         job.status = 'pending'
    #         job.save()
    #
    #         # If filters are applied, filter the units accordingly
    #         filters = data.get('filters', {})
    #         units = Unit.objects.filter(job_id=job_id)
    #
    #         if filters:
    #             # Handle price filtering
    #             min_price = filters.get('min_price')
    #             max_price = filters.get('max_price')
    #             if min_price and max_price:
    #                 min_price = float(min_price)
    #                 max_price = float(max_price)
    #                 units = units.annotate(
    #                     price_as_float=Cast(F('price'), FloatField())
    #                 ).filter(
    #                     price_as_float__gte=min_price,
    #                     price_as_float__lte=max_price
    #                 ).order_by('price_as_float')
    #
    #             # Handle no_of_beds filtering
    #             no_of_beds = filters.get('no_of_beds')
    #             if no_of_beds:
    #                 if no_of_beds == '0':
    #                     units = units.filter(beds__in=['', '0'])
    #                 elif no_of_beds in ['1', '2', '3']:
    #                     units = units.filter(beds=no_of_beds)
    #                 else:
    #                     units = units.annotate(beds_as_int=Cast('beds', IntegerField()))
    #                     units = units.filter(beds_as_int__gt=3)
    #
    #             # Handle no_of_baths filtering
    #             no_of_baths = filters.get('no_of_baths')
    #             if no_of_baths:
    #                 if no_of_baths == '0':
    #                     units = units.filter(baths__in=['', '0'])
    #                 elif no_of_baths in ['1', '2', '3']:
    #                     units = units.filter(baths=no_of_baths)
    #                 else:
    #                     units = units.annotate(baths_as_int=Cast('baths', IntegerField()))
    #                     units = units.filter(baths_as_int__gt=3)
    #     else:
    #         print("ids",data['ids'])
    #         if 'ids' not in data or not data['ids']:
    #             return Response({'error': 'At least one id or scrapAll=true is required'},
    #                             status=status.HTTP_400_BAD_REQUEST)
    #
    #         # Process specific units by their IDs
    #         units = Unit.objects.filter(id__in=data['ids'])
    #
    #         # Get the job_id from the first unit to update the job status
    #         first_unit_id = data['ids'][0]
    #         first_unit = Unit.objects.get(id=first_unit_id)
    #         job_id = first_unit.job_id
    #
    #         try:
    #             job = Jobs.objects.get(id=job_id)
    #         except Jobs.DoesNotExist:
    #             return Response({'message': f'Job with ID {job_id} does not exist'}, status=status.HTTP_404_NOT_FOUND)
    #
    #
    #         job.status = 'pending'
    #         job.save()
    #     # print("Units Count",units.count())
    #     # Process each unit
    #     for unit in units:
    #         unit.status = 'pending'
    #         unit.job_status = 'running'
    #         unit.isProcessing = 0
    #         unit.save()
    #
    #     return Response('Uploading Started')


from django.db.models import IntegerField, Value, Case, When
from django.db.models.functions import Cast
class UnitSearchAPIView(generics.ListAPIView):
    serializer_class = UnitSerializer
    pagination_class = CustomPagination
    # pagination_class.page_size = 100

    def get_queryset(self):
        queryset = Unit.objects.all()

        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        no_of_beds = self.request.query_params.get('no_of_beds')
        no_of_baths = self.request.query_params.get('no_of_baths')
        job_id = self.request.query_params.get('job_id')

        # Annotate price_as_float once
        queryset = queryset.annotate(price_as_float=Cast(F('price'), FloatField()))

        # Filter by job_id if provided
        if job_id:
            queryset = queryset.filter(job_id=job_id)

        # Handle price filtering
        if min_price:
            min_price = float(min_price)
            queryset = queryset.filter(price_as_float__gte=min_price)

        if max_price:
            max_price = float(max_price)
            queryset = queryset.filter(price_as_float__lte=max_price)

        # Handle no_of_beds filtering
        if no_of_beds:
            if no_of_beds == '0':
                queryset = queryset.filter(beds__in=['', '0'])
            elif no_of_beds in ['1', '2', '3']:
                queryset = queryset.filter(beds=no_of_beds)
            else:
                queryset = queryset.annotate(beds_as_int=Cast('beds', IntegerField()))
                queryset = queryset.filter(beds_as_int__gt=3)

        # Handle no_of_baths filtering
        if no_of_baths:
            if no_of_baths == '0':
                queryset = queryset.filter(baths__in=['', '0'])
            elif no_of_baths in ['1', '2', '3']:
                queryset = queryset.filter(baths=no_of_baths)
            else:
                queryset = queryset.annotate(baths_as_int=Cast('baths', IntegerField()))
                queryset = queryset.filter(baths_as_int__gt=3)

        return queryset


# List and Create View (GET, POST)
class TemplateDescriptionListCreateView(generics.ListCreateAPIView):
    queryset = TemplateDescription.objects.all().order_by('-id')
    serializer_class = TemplateDescriptionSerializer

# Retrieve, Update, and Delete View (GET, PATCH, DELETE)
class TemplateDescriptionRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TemplateDescription.objects.all()
    serializer_class = TemplateDescriptionSerializer

# List and Create Web Title View (GET, POST)
class WebTitleListCreateView(generics.ListCreateAPIView):
    queryset = WebTitle.objects.all().order_by('-id')  # Adjust model name as needed
    serializer_class = WebTitleSerializer

# Retrieve, Update, and Delete Web Title View (GET, PATCH, DELETE)
class WebTitleRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = WebTitle.objects.all()
    serializer_class = WebTitleSerializer


class PropertyFilterAPI(generics.ListAPIView):
    serializer_class = PropertySerializer

    def get_queryset(self):
        # Start with all properties
        properties = Property.objects.all()

        # Fetch query parameters
        prop_types = self.request.query_params.getlist('prop_type')
        search_prop = self.request.query_params.get('search_prop', None)
        search_neighbour = self.request.query_params.get('search_neighbour', None)

        # Filter by search_prop (URL filter) if provided
        if search_prop:
            properties = properties.filter(url__icontains=search_prop)
            # search_props = [
            #     s.strip() for s in search_prop.split(',') if s.strip()  # Remove empty values
            # ]
            #
            # # Apply OR condition for multiple URL patterns
            # if search_props:
            #     query = Q()
            #     for prop in search_props:
            #         query |= Q(url__icontains=prop)
            #
            #     properties = properties.filter(query)

        # Filter by search_neighbour (neighborhood filter) if provided
        if search_neighbour:
            neighbourhoods = [
                n.strip() for n in search_neighbour.split(',') if n.strip()  # Remove empty values
            ]

            # Apply OR condition for each neighborhood (case-insensitive)
            if neighbourhoods:
                query = Q()
                for neighbourhood in neighbourhoods:
                    query |= Q(area__icontains=neighbourhood)

                properties = properties.filter(query)

        # Filter by property types if provided
        if prop_types:
            query = Q()
            for prop_type in prop_types:
                query |= Q(prop_type__icontains=prop_type)

            properties = properties.filter(query)

        return properties  # Return the filtered queryset

    def post(self, request, *args, **kwargs):
        # Get the filtered queryset
        queryset = self.get_queryset()
        # Serialize the filtered properties
        serializer = self.get_serializer(queryset, many=True)

        # Return the filtered properties with count
        return Response({
            'properties': serializer.data,
            'count': queryset.count()
        }, status=status.HTTP_200_OK)


class UnitFilterAPI(generics.ListAPIView):
    serializer_class = UnitFilterSerializer


    def get_queryset(self):
        filters = self.request.data.get('filters', {})

        min_price = filters.get('min_price')
        max_price = filters.get('max_price')
        no_of_beds = filters.get('no_of_beds')
        no_of_baths = filters.get('no_of_baths')

        job_id = self.request.data.get('job_id')

        units = Unit.objects.filter(job_id=job_id)


        if min_price and max_price:
            min_price = float(min_price)
            max_price = float(max_price)
            units = units.annotate(
                price_as_float=Cast(F('price'), FloatField())
            ).filter(
                price_as_float__gte=min_price,
                price_as_float__lte=max_price
            ).order_by('price_as_float')

        # Handle no_of_beds filtering
        if no_of_beds:
            if no_of_beds == '0':
                units = units.filter(beds__in=['', '0'])
            elif no_of_beds in ['1', '2', '3']:
                units = units.filter(beds=no_of_beds)
            else:
                units = units.annotate(beds_as_int=Cast('beds', IntegerField()))
                units = units.filter(beds_as_int__gt=3)

        # Handle no_of_baths filtering
        if no_of_baths:
            if no_of_baths == '0':
                units = units.filter(baths__in=['', '0'])
            elif no_of_baths in ['1', '2', '3']:
                units = units.filter(baths=no_of_baths)
            else:
                units = units.annotate(baths_as_int=Cast('baths', IntegerField()))
                units = units.filter(baths_as_int__gt=3)

        return units

    def post(self, request, *args, **kwargs):
        # Get the filtered queryset
        queryset = self.get_queryset()
        # Serialize the filtered properties
        serializer = self.get_serializer(queryset, many=True)

        # Return the filtered properties with count
        return Response({
            'units': serializer.data,
            'count': queryset.count()
        }, status=status.HTTP_200_OK)



