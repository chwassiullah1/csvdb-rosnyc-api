from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf.urls.static import static
from django.conf import settings
from . import views

urlpatterns = [
path('', views.FileUploadView.as_view(), name='FileUploadView'),
path('properties/', views.view_properties, name='view_properties'),
path('create_prop/', views.PropertyCreateView.as_view(), name='create_prop'),
path('crawl/', views.CrawlProperty.as_view(), name='crawl'),
path('get_prop/', views.PropertyListView.as_view(), name='getprop'),
path('get_prop_id/', views.PropertyView.as_view(), name='getprop'),
path('get_prop/<int:pk>/', views.PropertyDeleteView.as_view(), name='get_prop'),
path('edit/', views.EditCrawlProperty.as_view(), name='edit'),
path('update/', views.UpdateProperty.as_view(), name='update'),
path('unit/', views.UnitListView.as_view(), name='unit'),
path('multiupdate/', views.MultiUpdateProperty.as_view(), name='multiupdate'),
path('add_user/', views.UploadUser.as_view(), name='add_user'),
path('jobs/', views.JobViewSet.as_view(), name='jobs'),
path('job/<int:job_id>/', views.JobDetailView.as_view(), name='job'),
path('unitview/<int:job_id>/', views.UnitDetailView.as_view(), name='unitview'),
path('convertible/<int:pk>/', views.ConvertiblePatchView.as_view(), name='convertible'),
path('neighbour/<int:pk>/', views.neighbourPatchView.as_view(), name='neighbour'),
path('upload_image/', views.UploadImageView.as_view(), name='upload_image'),
path('del_image/', views.RemoveImageView.as_view(), name='del_image'),
path('update_image/', views.UpdateImageView.as_view(), name='update_image'),
path('get_users/', views.RealityUserListView.as_view(), name='get_users'),
path('del_user/<int:pk>/', views.RealityUserDeleteView.as_view(), name='del_user'),
path('getstreet_img/', views.StreetImageListView.as_view(), name='getstreet_img'),
path('template_desc/', views.TemplateDescriptionViewSet.as_view(), name='template_desc'),
path('refresh/', views.RefreshSerializerViewSet.as_view(), name='refresh'),
path('del_template_desc/<int:pk>/', views.TemplateDescriptionDeleteView.as_view(), name='del_template_desc'),
path('update_allimg/', views.UpdateAllItems.as_view(), name='update_allimg'),
path('update_allconv/', views.UpdateConvertiblesView.as_view(), name='update_allcon'),
path('schedule/', views.ScheduleViewSet.as_view(), name='schedule'),
path('scheduleunit/', views.ScheduleUnitViewSet.as_view(), name='scheduleunit'),
path('del_schedule/<int:pk>/', views.ScheduleDeleteView.as_view(), name='del_schedule'),
path('stop_all_scraper/', views.stop_all_scraper),
path('main_jobs/', views.JobListView.as_view(), name='main_jobs'),
path('properties/search', views.PropertySearchAPIView.as_view(), name='properties-search')
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)