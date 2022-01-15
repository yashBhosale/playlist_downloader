# -*- coding: utf-8 -*-

# Sample Python code for youtube.playlistItems.list
# See instructions for running these code samples locally:
# https://developers.google.com/explorer-help/guides/code_samples#python

import os

import google_auth_oauthlib.flow

from googleapiclient.discovery import Resource
import googleapiclient.discovery
import googleapiclient.errors
import multiprocessing as mp
from yt_dlp import YoutubeDL
from pprint import pprint
from urllib.parse import urlparse
from typing import Union

scopes = ["https://www.googleapis.com/auth/youtube.readonly"]

class Downloader():

    youtube: Resource
    params = {'format': 'bestaudio'}

    def set_download_path(self, home, temp=None):
        paths = {}
        paths['home'] = home
        if temp:
            paths['temp'] = temp
        self.params['paths'] = paths


    def set_up_youtube(self):
        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "client_secret.json"

        # Get credentials and create an API client
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        credentials = flow.run_local_server()
        youtube = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)

        self.youtube = youtube

    def download_video(self, work_queue):
        info_list = []
        with YoutubeDL(self.params) as yt:
            while not work_queue.empty():
                video = work_queue.get()
                info_list.append(yt.extract_info(video))
        return info_list

    def download_files(self, playlist_ids):
        num_processes = 8
        m = mp.Manager()
        q = m.Queue()

        # TODO: make this into a work queue because this would likely be inefficient in the case of 
        # a playlist where the videos have a significant variance in size
        id_list = ( "https://www.youtube.com/watch?v=" + playlist_id for playlist_id in playlist_ids)
        for vid_id in id_list:
            q.put(vid_id)
        
        pprint(id_list)
        
        p = mp.Pool(num_processes)

        videos = p.map(self.download_video, [q for _ in range(num_processes)])
        
        return videos

    def fetch_playlist_item_ids(self, url):

        # Parse the URL to get the playlist ID
        parsed = urlparse(url)
        query = parsed.query.split("&")

        try:
            playlist_id = next(q.split("=")[1] for q in query if len(q) > 5 and q[:5] == "list=") #parsing urls is the worst
        except Exception as e:
            raise e

        
        request = self.youtube.playlistItems().list(
            part="contentDetails",
            playlistId=playlist_id
        )
        playlist_data = request.execute()
        video_ids = [playlist_item["contentDetails"]["videoId"] 
                        for playlist_item in 
                        playlist_data['items']] # This is pleasantly readable 

        while "nextPageToken" in playlist_data:
            next_page_token = playlist_data["nextPageToken"]
            # fetch the playlist ids
            request = self.youtube.playlistItems().list(
                part = "contentDetails",
                playlistId = playlist_id,
                pageToken = next_page_token
            )
            playlist_data = request.execute()
            pprint(playlist_data)
            video_ids.extend( playlist_item["contentDetails"]["videoId"] 
                            for playlist_item in 
                            playlist_data['items']) # This is pleasantly readable
 
        

        
        pprint(video_ids)

        videos = self.download_files(video_ids)

        #return videos 
