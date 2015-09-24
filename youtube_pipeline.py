import os
import gdata.youtube
import gdata.youtube.service
import sys

def convert_to_video(audiofile):
    basename, ext = os.path.splitext(audiofile)
    videofile = basename+'.mp4'
    os.system('ffmpeg -loop 1 -i static/images/shield.jpg -i '+audiofile+' -strict experimental -b:a 192k -shortest '+videofile)
    return videofile

def upload(videofile, password):
    yt_service = gdata.youtube.service.YouTubeService()
    yt_service.ssl = True
    yt_service.developer_key = open('youtubekey.txt').read().strip()
    yt_service.email = 'darla.dartmouth@gmail.com'
    yt_service.password = password
    yt_service.source = 'DARLA'
    yt_service.ProgrammaticLogin()
    
    my_media_group = gdata.media.Group(title=gdata.media.Title(text='Darla sociophonetics sample'),
                                       description=gdata.media.Description(description_type='plain', text='My description'), 
                                       keywords=gdata.media.Keywords(text='sociophonetics'), 
                                       category=[gdata.media.Category(text='Education', scheme='http://gdata.youtube.com/schemas/2007/categories.cat', label='Education')], 
                                       player=None, 
                                       private=gdata.media.Private())

    video_entry = gdata.youtube.YouTubeVideoEntry(media=my_media_group)
    new_entry = yt_service.InsertVideoEntry(video_entry, videofile)

    upload_status = yt_service.CheckUploadStatus(new_entry)

    if upload_status is not None:
        print upload_status
    
    return yt_service, new_entry

if __name__=='__main__':
    videofile = convert_to_video(sys.argv[1])
    yt_service, new_entry = upload(videofile, sys.argv[2])
    print new_entry

def get_captions():
    return

    
