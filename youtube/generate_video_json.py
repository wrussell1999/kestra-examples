from datetime import datetime
from kestra import Kestra

raw_yt = {{ outputs.fetch_videos.body }}
data = raw_yt['items'][0]
video = {
    "video" : {
        "data": {
            "author": "Kestra",
            "isFeatured": False,
            "category": "Feature Highlight",
            "contentType": "Feature Highlight"
        }
    }
}

video['video']['data']['title'] = data['snippet']['title']
video['video']['data']['url'] = f"https://youtube.com/watch?v={data['id']['videoId']}"
video['video']['data']['description'] = data['snippet']['description']
video['thumbnail'] = data['snippet']['thumbnails']['high']['url']
date_object = datetime.strptime(data['snippet']['publishedAt'], "%Y-%m-%dT%H:%M:%SZ") 
video['video']['data']['publicationDate'] = date_object.strftime("%Y-%m-%d")
Kestra.outputs(video)