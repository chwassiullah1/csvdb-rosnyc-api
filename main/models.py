from django.db import models


class Property(models.Model):
    CHOICE = [
        ('new', 'new'),
        ('pending', 'pending'),
        ('scraped', 'scraped')
    ]
    DESCCHOICE = [
        ('streeteasy', 'streeteasy'),
        ('template', 'template'),
        ('costume', 'costume')
    ]
    url = models.URLField(unique=True)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=CHOICE)
    use_desc = models.CharField(max_length=20, choices=DESCCHOICE, default='streeteasy')
    isProcessing = models.IntegerField(default=0)
    area = models.CharField(max_length=50,default=None,null=True)
    neighbour = models.JSONField(default={
        "Manhattan": [],
        "Brooklyn": [],
        "Queens": [],
        "Bronx": [],
        "Staten_Island": [],
        "Others": []
    })
    upload_img = models.BooleanField(default=False)
    images = models.JSONField(default={
        'bathroom': {'unfurnished': [], 'furnished': []},
        'bedroom': {'unfurnished': [], 'furnished': []},
        'livingroom': {'unfurnished': [], 'furnished': []},
        'kitchen': {'unfurnished': [], 'furnished': []},
        'more': {'unfurnished': [], 'furnished': []},
        'gym': {'unfurnished': [], 'furnished': []},
        'lobby': {'unfurnished': [], 'furnished': []},
        'lounge': {'unfurnished': [], 'furnished': []},
        'roof_deck': {'unfurnished': [], 'furnished': []},
        'pool': {'unfurnished': [], 'furnished': []},
        'golf_room': {'unfurnished': [], 'furnished': []},
        'others': {'unfurnished': [], 'furnished': []},
    })
    description = models.JSONField(default=list)

# class Images(models.Model):
#     image = models.ImageField(upload_to='property_images/')
#     status = models.CharField(max_length=20)
#     property = models.ForeignKey(Property, on_delete=models.CASCADE)
#     type =  models.CharField(max_length=20)
#     uploadnum = models.IntegerField()


class RealityUser(models.Model):
    username = models.CharField(max_length=30)
    password = models.CharField(max_length=30)


class TemplateDescription(models.Model):
    description = models.CharField(max_length=3000)


class Unit(models.Model):
    CHOICE = [
        ('new', 'new'),
        ('pending', 'pending'),
        ('scraped', 'scraped'),
    ]
    url = models.URLField(unique=True)
    title = models.CharField(max_length=100)
    unit = models.CharField(max_length=10,null=True)
    complete_title = models.CharField(max_length=150,null=True)
    beds = models.CharField(max_length=20)
    baths = models.CharField(max_length=15)
    price = models.CharField(max_length=10)
    listing_id = models.IntegerField(null=True, default=None)
    image_urls = models.TextField(null=True)
    image_paths = models.JSONField(null=True)
    description = models.TextField(null=True)
    amenities = models.JSONField(null=True)
    added_at = models.DateTimeField(auto_now_add=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=CHOICE)
    reality_user =  models.JSONField(default=[],null=True)
    isProcessing = models.IntegerField(default=0)
    convertible = models.IntegerField(default=0)


class Job(models.Model):
    urls = models.JSONField(null=True)

class Refresh(models.Model):
    CHOICE = [
        ('pending', 'pending'),
        ('scraped', 'scraped')
    ]
    refresh_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=CHOICE)
    reality_user =  models.JSONField(default=[],null=True)



# Create your models here.
class Schedule(models.Model):
    CHOICE = [
        ('pending', 'pending'),
        ('scraped', 'scraped')
    ]
    added_at = models.DateTimeField(auto_now_add=True)
    property_id = models.JSONField(default=[], null=True)
    single_schedule = models.DateTimeField()
    filters = models.JSONField(default={}, null=True)
    reality_user = models.IntegerField()
    status = models.CharField(max_length=20, choices=CHOICE)
    day = models.CharField(max_length=20,default='',blank=True)
    interval = models.CharField(max_length=20,default='')


class Scheduleunits(models.Model):
    CHOICE = [
        ('new', 'new'),
        ('pending', 'pending'),
        ('scraped', 'scraped'),
    ]
    url = models.URLField()
    title = models.CharField(max_length=100)
    unit = models.CharField(max_length=10,null=True)
    complete_title = models.CharField(max_length=150,null=True)
    beds = models.CharField(max_length=20)
    baths = models.CharField(max_length=15)
    price = models.CharField(max_length=10)
    listing_id = models.IntegerField(null=True, default=None)
    image_urls = models.TextField(null=True)
    image_paths = models.JSONField(null=True)
    description = models.TextField(null=True)
    amenities = models.JSONField(null=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=CHOICE)
    reality_user =  models.JSONField(default=[],null=True)
    isProcessing = models.IntegerField(default=0)
    convertible = models.IntegerField(default=0)