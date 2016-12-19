import utilities
import base64
import os
from googleapiclient import discovery
import httplib2
from oauth2client.client import GoogleCredentials

from celery.task import task
import subprocess
import shlex
import time

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


@task(serializer='json')
def syncrec(service, datadir, taskname, audiodir, filename, extension, uploadfilecontents):
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
def asyncrec(service, datadir, taskname, audiodir, filename, extension, uploadfilecontents):
    samprate, total_size, chunks, error = utilities.process_audio(audiodir,
                                                                  filename,
                                                                  extension,
                                                                  uploadfilecontents,
                                                                  dochunk=79*60)

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
                        },
                        'audio': {
                            'content': speech_content.decode('UTF-8')
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
