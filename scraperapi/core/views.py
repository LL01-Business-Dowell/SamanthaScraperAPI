from django.shortcuts import render
from django.http.response import HttpResponse
from rest_framework.views import APIView
import pandas as pd
import requests
from .models import ScraperFile
# Create your views here.

class CreateProcessView(APIView):
    def post(self, request):
        # receives csv containing postal code data file from client frontend
        csv_file = request.FILES.get('csv_file')
        request_dict = request.POST.dict()

        alert_url = 'FRONTEND-DOMAIN-NAME/alerts'
        download_link_url = 'FRONTEND-DOMAIN-NAME/download'
        
        time_duration = 0  

        #send notification to file owner after successfully recieving request
        alert_dict = {
            "owner": request_dict["owner"],
            "document": request_dict["document"],
            "file_id": request_dict["file_id"],
            "header": "Scraping Started",
            "body": f"Your file has successfully been uploaded, and is now enqueued for processing.\nYour file will be ready in approximately {time_duration}"
        }

        new_task = ScraperFile.objects.create(
            owner= request_dict["owner"],
            document= request_dict["document"],
            file_id= request_dict["file_id"],
            name= csv_file.name
        )

        alert = requests.post(url= alert_url, json= alert_dict)

        # initiate scraper instance to handle post codes and create an output file with client file hash id as name
        # scraper function retrieves ScraperFile object instance using file_id and adds output file to said model instance

        scraped_file_link = '' #WEB-SCRAPER-FUCNTION THAT TAKES CSV DATA FROM USER_FILE & RETURNS FILE DOWNLOAD LINK URL
        download_link_json =  {"download_link": scraped_file_link, "file_id": request_dict["file_id"]}

        finished_link = requests.post(url= download_link_url, json= download_link_json)

        return HttpResponse({"message": "success"}, status= 200)