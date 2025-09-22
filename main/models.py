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
    WEBTITLECHOICE = [
        ('streeteasy', 'streeteasy'),
        ('template', 'template'),
        ('costume', 'costume')
    ]
    url = models.URLField(unique=True)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=CHOICE)
    use_desc = models.CharField(max_length=20, choices=DESCCHOICE, default='template')
    web_title = models.CharField(max_length=20, choices=WEBTITLECHOICE, default='template')
    isProcessing = models.IntegerField(default=0)
    area = models.CharField(max_length=50,default=None,null=True)
    prop_type = models.CharField(max_length=30, default=None, null=True)
    def default_neighbour():
        return {
            "Manhattan": [],
            "Brooklyn": [],
            "Queens": [],
            "Bronx": [],
            "Staten_Island": [],
            "Others": []
        }

    def default_images():
        return {
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
        }

    neighbour = models.JSONField(default=default_neighbour)
    images = models.JSONField(default=default_images)
    upload_img = models.BooleanField(default=False)
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

class WebTitle(models.Model):
    web_title = models.CharField(max_length=124, unique=True)  # Add unique=True here

    def __str__(self):
        return self.web_title


class Unit(models.Model):
    CHOICE = [
        ('new', 'new'),
        ('pending', 'pending'),
        ('scraped', 'scraped'),
    ]
    url = models.URLField()
    title = models.CharField(max_length=100)
    unit = models.CharField(max_length=10,null=True)
    complete_title = models.CharField(max_length=150,null=True)
    beds = models.CharField(max_length=20, null=True)
    baths = models.CharField(max_length=15)
    price = models.CharField(max_length=10)
    listing_id = models.IntegerField(null=True, default=None)
    image_urls = models.TextField(null=True)
    image_paths = models.JSONField(null=True)
    description = models.TextField(null=True)
    amenities = models.JSONField(null=True)
    added_at = models.DateTimeField(auto_now_add=True)
    # property = models.ForeignKey(Property, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=CHOICE)
    # reality_user =  models.JSONField(default=[],null=True)
    isProcessing = models.IntegerField(default=0)
    convertible = models.IntegerField(default=0)
    job = models.ForeignKey('Jobs', on_delete=models.CASCADE, null=True)
    job_status = models.CharField(max_length=20,default="running",null=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    unit_type = models.CharField(max_length=30, default='')
    # sample = models.IntegerField(default=0)


    def __str__(self):
        return f"Unit (id={self.id}, price={self.price}, job_id={self.job_id})"




# class Job(models.Model):
#     user = models.ForeignKey(RealityUser, on_delete=models.CASCADE, null=True)
#     property_urls = models.JSONField(null=True)
#     urls = models.JSONField(null=True)
#     status = models.CharField(max_length=20, default='new')
#     scraped_percentage = models.IntegerField(null=True, default=0)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

class Jobs(models.Model):
    user = models.ForeignKey(RealityUser, on_delete=models.CASCADE, null=True)
    urls = models.JSONField(null=True)
    status = models.CharField(max_length=20, default='new')
    scraped_percentage = models.IntegerField(null=True, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    isProcessing = models.IntegerField(default=0)
    unit_ids = models.JSONField(blank=True, default=list)

class JobPropertyBridge(models.Model):
    job = models.ForeignKey(Jobs, on_delete=models.CASCADE)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    property_status = models.CharField(max_length=20, choices=Property.CHOICE,null=True)
    last_update = models.DateTimeField(auto_now=True)
    property_url = models.URLField(default="")


class Refresh(models.Model):
    CHOICE = [
        ('pending', 'pending'),
        ('scraped', 'scraped')
    ]
    refresh_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=CHOICE)
    reality_user =  models.JSONField(default=list,null=True)



# Create your models here.
class Schedule(models.Model):
    CHOICE = [
        ('pending', 'pending'),
        ('scraped', 'scraped')
    ]
    added_at = models.DateTimeField(auto_now_add=True)
    property_id = models.JSONField(default=list, null=True)
    single_schedule = models.DateTimeField()
    filters = models.JSONField(default=dict, null=True)
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
    reality_user =  models.JSONField(default=list,null=True)
    isProcessing = models.IntegerField(default=0)
    convertible = models.IntegerField(default=0)
    
    


class AutomatedTask(models.Model):
    task_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=50, default="PENDING")
    account = models.JSONField(default=dict, blank=True, null=True)
    neighborhoods = models.JSONField(default=list, blank=True, null=True)
    unit_types = models.JSONField(default=list, blank=True, null=True)
    apartment_types = models.JSONField(default=list, blank=True, null=True)
    ads_per_neighborhood = models.IntegerField(blank=True, null=True)
    building_cap = models.IntegerField(blank=True, null=True)
    logs = models.JSONField(default=dict, blank=True, null=True)  
    result = models.JSONField(default=dict, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_run = models.DateTimeField(blank=True, null=True)
    scheduled = models.DateTimeField(blank=True, null=True)
    no_of_runs = models.IntegerField(default=0)
    last_result = models.JSONField(default=list,null=True,blank=True)
    schedule_interval = models.IntegerField(blank=True, null=True)  
    category = models.CharField(max_length=100, default="Open", blank=True, null=True)
    marketplaces = models.JSONField(default=list, blank=True, null=True)
    def __str__(self):
        return f"Task {self.task_id} - {self.status}"
