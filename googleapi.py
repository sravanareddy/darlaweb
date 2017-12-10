import utilities
import base64
import os
import sys
from googleapiclient import discovery
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import httplib2
from oauth2client.client import GoogleCredentials
import json 
import mimetypes
import random
import web

from celery.task import task
import subprocess
import shlex
import time

import subprocess
# max num wait time is 2 ^ 8 = 256 seconds. 
MAXIMUM_BACKOFF = 8
# max retries for a request. 
NUM_RETRIES = 1000 

# While the api library is still supported via discovery, 
# google suggests trying the newer Cloud Client Library for Cloud Storage JSON, 
# https://cloud.google.com/storage/docs/reference/libraries
# newer one is: pip install --upgrade google-cloud-storage
def get_storage_service(keyloc):
    DISCOVERY_URL = ('https://{api}.googleapis.com/$discovery/rest?'
                     'version={apiVersion}')
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = keyloc
    # Application default credentials provided by env variable

    credentials = GoogleCredentials.get_application_default().create_scoped(
            ['https://www.googleapis.com/auth/cloud-platform'])
    http = httplib2.Http()
    credentials.authorize(http)

    return discovery.build('storage', 'v1', http=http)

def get_speech_service(keyloc):
    # [START authenticating]
    DISCOVERY_URL = ('https://{api}.googleapis.com/$discovery/rest?'
                     'version={apiVersion}')
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = keyloc
    # Application default credentials provided by env variable

    credentials = GoogleCredentials.get_application_default().create_scoped(
            ['https://www.googleapis.com/auth/cloud-platform'])
    http = httplib2.Http()
    credentials.authorize(http)

    return discovery.build('speech',
                           'v1beta1',
                           http=http, discoveryServiceUrl=DISCOVERY_URL)

# uploads file from the directory audiodir to gs bucket audiouploads
# https://github.com/GoogleCloudPlatform/storage-file-transfer-json-python/blob/master/chunked_transfer.py
@task(serializer='json')
def gcloudupload(storageservice, audiodir, filename, taskname, email):
    RETRYABLE_ERRORS = (httplib2.HttpLib2Error, IOError)
    CHUNKSIZE = 2 * 1024 * 1024 # 2 MB

    # need to upload as raw file - gspeech does not do wav files
    audio = subprocess.Popen('sox ' + os.path.join(audiodir, 'converted_'+filename+'.wav')                       
            + ' ' + os.path.join(audiodir,filename+'.raw'),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    audio.wait()

    (mime, encoding) = mimetypes.guess_type(os.path.join(audiodir,filename+'.raw'))
    if mime == None:
        mime = "application/octet-stream"
    media = MediaFileUpload(os.path.join(audiodir,filename+'.raw'), chunksize=CHUNKSIZE, mimetype=mime, resumable=True)
    request = storageservice.objects().insert(bucket='audiouploads', name=taskname, media_body=media)

    progressless_iters = 0
    err_msg = 'Audio File Upload failed to Google Cloud Storage'
    response = None

    while response is None:
        error = None
        try:
            progress, response = request.next_chunk()
            if progress:
                sys.stdout.write('Upload %d%% \n' % (100 * progress.progress()))
        except HttpError, err:
            error = err
            if err.resp.status < 410:
                send_error_email(email, filename, err_message, 1)
                send_traceback_email('GStorage Upload Failed', '', taskname, str(error))
                raise # oh i think this just makes everything stop. 
        except RETRYABLE_ERRORS, err:
            error = err

        if error:
            progressless_iters += 1
            if progressless_iters > NUM_RETRIES:
                sys.stderr.write('Failed to make progress for too many consecutive iterations for task {0}'.format(taskname))
                send_error_email(email, filename, err_message, 1)
                send_traceback_email(tasktype, '', taskname, str(error))
                raise error
            else:
                handle_progressless_iter(error, progressless_iters, taskname, 'GStorage Upload Failed')
        else:
            progressless_iters = 0
    
    sys.stdout.write('Upload complete \n')
    sys.stdout.flush()
    return 

# exponential backoff
def handle_progressless_iter(error, progressless_iters, taskname, tasktype):
    sleeptime = random.random() + min((2**progressless_iters), 2**MAXIMUM_BACKOFF)
    sys.stderr.write('Caught exception for task {3} : ({0}). Sleeping for {1} seconds before retry #{2}.'
        .format(str(error), sleeptime, progressless_iters, taskname))
    time.sleep(sleeptime)
    return 

@task(serializer='json')
def syncrec(service, datadir, taskname, audiodir, filename, chunks, samprate, email, phrasehints = []):
    total_msg = []

    for ci, chunk in enumerate(chunks):
        # get the file and read it in

        chunk_file = open(os.path.join(audiodir,'splits',filename+'.split{0:03d}.wav'.format(ci+1)))
        speech_content = base64.b64encode(chunk_file.read())
        service_request = service.speech().syncrecognize(
                    body={
                        'config': {
                            # There are a bunch of config options you can specify. See
                            # https://goo.gl/KPZn97 for the full list.
                            'encoding': 'LINEAR16',  # raw 16-bit signed LE samples
                            'sampleRate': samprate, 
                            # See https://goo.gl/A9KJ1A for a list of supported languages.
                            'languageCode': 'en-US',  # a BCP-47 language tag
                            'speechContext': {
                                'phrases': phrasehints
                            }
                        },
                        'audio': {
                            'content': speech_content.decode('UTF-8')
                            }
                        })
        response = service_request.execute()
        sentences = ' '.join(map(lambda x: x['alternatives'][0]['transcript'], response['results']))
        total_msg.append(sentences)

    # save this as into formants file
    error = utilities.write_hyp(datadir,
                                taskname,
                                filename,
                                ' '.join(total_msg),
                                'cmudict.forhtk.txt')
    # TODO: do something with this error - send email?
    return error

# instead of getting speech on each chunk, get speech rec on file in google storage. 
@task(serializer='json')
def asyncrec(service, datadir, taskname, audiodir, filename, samprate, email, phrasehints = []):
    total_msg = []
    service_request = service.speech().asyncrecognize(
                body={
                    'config': {
                        # There are a bunch of config options you can specify. See
                        # https://goo.gl/KPZn97 for the full list.
                        'encoding': 'LINEAR16',  # FLAC
                        'sampleRate': samprate, 
                        # See https://goo.gl/A9KJ1A for a list of supported languages.
                        'languageCode': 'en-US',  # a BCP-47 language tag
                        'speechContext': {
                            'phrases': phrasehints
                        }
                    },
                    'audio': {
                        'uri': 'gs://audiouploads/' + taskname
                        }
                    })
    response = service_request.execute()
    # from https://github.com/DjangoGirlsSeoul/hackfair-speech/blob/master/speech_async_rest.py
    name = response['name']
    # Construct a GetOperation request.
    service_request = service.operations().get(name=name)
    n = 1 # number of tries
    while True:
        # Get the long running operation with response.
        try:
            response = service_request.execute()

            if 'done' in response and response['done']:
                break
        except HttpError, err:
            # too many requests. exponential backoff
            if err.resp.status == 429 and n < NUM_RETRIES:
                handle_progressless_iter(err, n, taskname, 'Google Speech ASR Failed')
                n += 1
            else: 
                sys.stderr.write('Failed to get audio for task {0}'.format(taskname))
                utilities.send_error_email(email, filename, 'Google Speech ASR API Failed', 1)
                utilities.send_traceback_email('Google Speech ASR Failed', '', taskname, str(error))
                raise

    response = response['response']

    sentences = ' '.join(map(lambda x: x['alternatives'][0]['transcript'], response['results']))
    total_msg.append(sentences)

    # save this as into formants file
    error = utilities.write_hyp(datadir,
                                taskname,
                                filename,
                                ' '.join(total_msg),
                                'cmudict.forhtk.txt')
    # TODO: do something with this error - send email?
    return error
