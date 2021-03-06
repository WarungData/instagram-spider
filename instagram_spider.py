# -*- coding: utf-8 -*-
import scrapy
import json
import urllib
import os
import sys

class InstagramSpider(scrapy.Spider):
    name = "Instagram"  # Name of the Spider, required value

    def __init__(self, account='', videos=''):
        self.videos = videos
        self.account = account

        if account == '':
            self.account = raw_input("Name of the account ?")
        if videos == '':
            self.videos = raw_input("Download videos ? (y/n) ")

        self.start_urls = ["https://www.instagram.com/"+self.account]
        
         #Create the folder for the instagram account if it doesn't exist
        if not os.path.exists(self.account):
            os.makedirs(self.account)

    # Entry point for the spider
    def parse(self, response):

        request = scrapy.Request(response.url, callback=self.parse_page)
        return request


    # Method for parsing a page
    def parse_page(self, response):
        #We get the json containing the photos's path
        js = response.selector.xpath('//script[contains(., "window._sharedData")]/text()').extract()
        js = js[0].replace("window._sharedData = ", "")
        jscleaned = js[:-1]

        #Load it as a json object
        locations = json.loads(jscleaned)
        #We check if there is a next page
        has_next = locations['entry_data']['ProfilePage'][0]['user']['media']['page_info']['has_next_page']

        media = locations['entry_data']['ProfilePage'][0]['user']['media']['nodes']
        
        #We parse the photos
        for photo in media:
            url = photo['display_src']
            id =  photo['id']
            is_video =  photo['is_video']
            #If the media is a video
            if is_video and self.videos=='y':
                #Get the code and download it
                code =  photo['code']
                yield scrapy.Request("https://www.instagram.com/p/"+code, callback=self.parse_page_video)
               
            yield scrapy.Request(url, 
                    meta={'id': id, 'extension' :'.jpg'},
                    callback=self.save_media)
            
        #If there is a next page, we crawl it
        if has_next:
            url="https://www.instagram.com/"+self.account+"/?max_id="+media[-1]['id']
            yield scrapy.Request(url, callback=self.parse_page)


    # Method for parsing a video_page
    def parse_page_video(self, response):
       #Get the id from the last part of the url
       id=response.url.split("/")[-2]
       #We get the link of the video file
       js = response.selector.xpath('//meta[@property="og:video"]/@content').extract()
       url = js[0]
       #We save the video
       yield scrapy.Request(url, 
                    meta={'id': id, 'extension' :'.mp4'},
                    callback=self.save_media)
        

    @staticmethod
    def pwrite(text):
        with open('comments.txt', 'a') as f:        
                f.write(str(text))

    
    #We grab the photo with urllib          
    def save_media(self, response):
        print(response.url)
        fullfilename = os.path.join(self.account, response.meta['id']+response.meta['extension'])
        urllib.urlretrieve(response.url, fullfilename)

