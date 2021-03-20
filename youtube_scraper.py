import os

import googleapiclient.discovery
import googleapiclient.errors
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle


class YoutubeScraper:
    def __init__(self):
        self.scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        self.base = "https://www.youtube.com/watch?v="
        self.use_second_credentials = False

    def get_video_url(self, query, latest=False):
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"

        # Get credentials and create an API client
        creds = self.get_credentials()
        youtube = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=creds)

        if latest:
            request = youtube.search().list(
                part="snippet",
                type=["video"],
                order="date",
                channelId="UCQKVhuasCQ1uGw2dmZscSVQ"
            )
        else:
            request = youtube.search().list(
                part="snippet",
                q=query,
                maxResults=10,
                type=["video"]
            )
        try:
            response = request.execute()["items"][0]
            video_url = self.base + response["id"]["videoId"]
            video_name = response["snippet"]["title"]

            video_details = [video_url, video_name]
            return video_details
        except googleapiclient.errors.HttpError:
            self.use_second_credentials = True
            return self.get_video_url(query)

    def get_credentials(self):
        creds = None
        token_path = "token.pickle"
        cred_path = "credentials.json"
        if self.use_second_credentials:
            token_path = "token2.pickle"
            cred_path = "credentials2.json"
        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    cred_path, self.scopes)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
        return creds
