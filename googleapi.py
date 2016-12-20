import utilities
import base64
import os
from googleapiclient import discovery
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import httplib2
from oauth2client.client import GoogleCredentials

from celery.task import task
import subprocess
import shlex
import time

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
def gcloudupload(storageservice, audiodir, filename, uploadfilecontents):
    RETRYABLE_ERRORS = (httplib2.HttpLib2Error, IOError)
    CHUNKSIZE = 2 * 1024 * 1024 # 2 MB

    media = MediaFileUpload(os.path.join(audiodir,filename+'.wav'), chunksize=CHUNKSIZE, resumable=True)
    request = storageservice.objects().insert(bucket='audiouploads', name=taskname, media_body=media)
    # https://github.com/GoogleCloudPlatform/storage-file-transfer-json-python/blob/master/chunked_transfer.py
    progressless_iters = 0
    response = None
    while response is None:
        error = None
        try:
            progress, response = request.next_chunk()
            if progress:
                sys.stdout.write('Upload %d%% \n' % (100 * progress.progress()))
        except HttpError, err:
            error = err
            if err.resp.status < 500:
                raise
        except RETRYABLE_ERRORS, err:
            error = err

        if error:
            progressless_iters += 1
            handle_progressless_iter(error, progressless_iters, taskname)
        else:
            progressless_iters = 0
    return 


def handle_progressless_iter(error, progressless_iters, taskname):
    if progressless_iters > NUM_RETRIES:
        sys.stderr.write('Failed to make progress for too many consecutive iterations for task {0}'.format(taskname))
        raise error

    sleeptime = random.random() * (2**progressless_iters)
    sys.stderr.write('Caught exception for task {3} : ({0}). Sleeping for {1} seconds before retry #{2}.'
        .format(str(error), sleeptime, progressless_iters, taskname))
    time.sleep(sleeptime)

@task(serializer='json')
def syncrec(service, datadir, taskname, audiodir, filename, extension, uploadfilecontents, phrasehints = []):
    samprate, total_size, chunks, error = utilities.process_audio(audiodir,
                                                                  filename,
                                                                  extension,
                                                                  uploadfilecontents,
                                                                  dochunk=50)

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
                            'sampleRate': samprate,  # 16 khz
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
        sentences = ''.join(map(lambda x: x['alternatives'][0]['transcript'], response['results']))
        total_msg.append(sentences)

    # save this as into formants file
    error = utilities.write_hyp(datadir,
                                taskname,
                                filename,
                                ' '.join(total_msg),
                                'cmudict.forhtk.txt')
    # TODO: do something with this error - send email?

    return samprate

@task(serializer='json')
def asyncrec(service, datadir, taskname, audiodir, filename, extension, uploadfilecontents, phrasehints = []):
    samprate, total_size, chunks, error = utilities.process_audio(audiodir,
                                                                  filename,
                                                                  extension,
                                                                  uploadfilecontents,
                                                                  dochunk=None)

    total_msg = []

    for ci, chunk in enumerate(chunks):
        # get the file and read it in

        chunk_file = open(os.path.join(audiodir,'splits',filename+'.split{0:03d}.wav'.format(ci+1)))
        speech_content = base64.b64encode(chunk_file.read())
        service_request = service.speech().asyncrecognize(
                    body={
                        'config': {
                            # There are a bunch of config options you can specify. See
                            # https://goo.gl/KPZn97 for the full list.
                            'encoding': 'LINEAR16',  # raw 16-bit signed LE samples
                            'sampleRate': samprate,  # 16 khz
                            # See https://goo.gl/A9KJ1A for a list of supported languages.
                            'languageCode': 'en-US',  # a BCP-47 language tag
                            'speechContext': {
                                'phrases': phrasehints
                            }
                        },
                        'audio': {
                            'content': speech_content.decode('UTF-8')
                            # 'uri': 'gs://audiouploads/' + taskname
                            }
                        })
        response = service_request.execute()
        # from https://github.com/DjangoGirlsSeoul/hackfair-speech/blob/master/speech_async_rest.py
        name = response['name']
        # Construct a GetOperation request.
        service_request = service.operations().get(name=name)

        while True:
            # Give the server a few seconds to process.
            #print('Waiting for server processing...')
            time.sleep(1)
            # Get the long running operation with response.
            response = service_request.execute()

            if 'done' in response and response['done']:
                break

        response = response['response']

        sentences = ''.join(map(lambda x: x['alternatives'][0]['transcript'], response['results']))
        total_msg.append(sentences)

    # save this as into formants file
    error = utilities.write_hyp(datadir,
                                taskname,
                                filename,
                                ' '.join(total_msg),
                                'cmudict.forhtk.txt')
    # TODO: do something with this error - send email?

    return samprate
