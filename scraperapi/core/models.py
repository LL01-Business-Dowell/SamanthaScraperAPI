from django.db import models

# Create your models here.

class ScraperFile(models.Model):
    owner = models.IntegerField()
    document = models.IntegerField()
    file_id = models.SlugField(blank= True, max_length= 25, primary_key= True)
    name = models.CharField(max_length=50, blank= True)
    download_file = models.FileField(upload_to= '#CLOUD UPLOAD URL FOR DOWNLOAD LINK RETRIEVAL or UPLOAD FOLDER', blank= True)
    created_on = models.DateTimeField(auto_now= True)
    modified_on = models.DateField(auto_now_add= True)

    def get_dl_url(self):
        return str(self.download_file.url)
    
