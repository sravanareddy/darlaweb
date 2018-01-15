#from __future__ import absolute_import
from celery.task import task

#app = Celery('featrec', backend="amqp", broker='amqp://')
#app.config_from_object('celeryconfig')

import os
from mail import send_email, send_init_email, send_error_email
import subprocess
import shlex
import json

@task(serializer='json', ignore_result=True)
def featurize_recognize(taskdir):

    alext_args = json.load(open(os.path.join(taskdir, 'alext_args.json')))
    receiver = alext_args['email']
    filename = alext_args['filename']
    send_init_email(alext_args['tasktype'], receiver, filename)
    error_check = True

    args = "/usr/local/bin/sphinx_fe -argfile "+os.path.join(taskdir, "featurize_args")
    audio = os.system(args)
    if audio != 0 and receiver!='none':
        error_check = send_error_email(receiver, filename, "There was a problem extracting acoustic features for ASR. Please check your file and try again.", error_check)
        return False
    args = "/usr/local/bin/pocketsphinx_batch -argfile "+os.path.join(taskdir, "recognize_args")
    audio = os.system(args)
    if audio != 0 and receiver!='none':
        error_check = send_error_email(alext_args['email'], alext_args['filename'], "There was a problem running ASR. Please check your file and try again.", error_check)
        return False
    return True

@task(serializer='json')
def align_extract(taskdir, confirmation_sent = False):

    error_check = True
    alext_args = json.load(open(os.path.join(taskdir, 'alext_args.json')))
    if not confirmation_sent:
        send_init_email(alext_args['tasktype'], alext_args['email'], alext_args['filename'])

    args = ' '.join(["./align_and_extract.sh",
                     taskdir,
                     alext_args['tasktype'],
                     alext_args['delstopwords'],
                     alext_args['maxbandwidth'],
                     alext_args['delunstressedvowels']])

    align = subprocess.Popen(shlex.split(args), stderr=subprocess.STDOUT)
    retval = align.wait()

    if retval != 0:
        send_error_email(alext_args['email'], alext_args['filename'], "Alignment and extraction process failed.", error_check)
        return False
    else:
        send_email(alext_args['tasktype'], alext_args['email'], alext_args['filename'], taskdir, True) #passes in true for no errors so no multiple emails. Will have to change if anything is done before align_extract and before featrec that could send error emails.
    return True
