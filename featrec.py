#from __future__ import absolute_import
from celery.task import task

#app = Celery('featrec', backend="amqp", broker='amqp://')
#app.config_from_object('celeryconfig')

import os
from utilities import send_email, send_init_email, send_error_email
import subprocess
import shlex

@task(serializer='json', ignore_result=True)
def featurize_recognize(taskname):
        
        filename, _, receiver = open(taskname+'.alext_args').read().split()
        send_init_email("Completely Automated Vowel Extraction", receiver, filename)
        
        args = "/usr/local/bin/sphinx_fe -argfile "+taskname+".featurize_args"
        audio = subprocess.Popen(shlex.split(args), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        retval = audio.wait()

        if retval != 0 and receiver!='none':
                send_error_email(receiver, "", "sphinx_fe processing")
                #return - only one email, or a value to show that an error occured
        args = "/usr/local/bin/pocketsphinx_batch -argfile "+taskname+".recognize_args"
        audio = subprocess.Popen(shlex.split(args), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        retval = audio.wait()
        if retval != 0 and receiver!='none':
                send_error_email(receiver, "", "pocketsphinx_batch processing")
                #return - only one email                
        return

@task(serializer='json')
def align_extract(taskname):
        filename, align_hmm, receiver = open(taskname+'.alext_args').read().split()
        args = "/home/sravana/webpy_sandbox/align_extract.sh "+taskname+" "+align_hmm
        align = subprocess.Popen(shlex.split(args), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        retval = align.wait()

        if retval != 0:
                send_error_email(receiver, "", "align_extract shell script")

        else:
                send_email(receiver, filename, taskname)
        
        return

@task(serializer='json')
def just_align_extract(taskname):
        filename, hmm, receiver = open(taskname+'.alext_args').read().split()
        send_init_email("Alignment and Extraction", receiver, filename)

        args = "/home/sravana/webpy_sandbox/just_align_extract.sh "+taskname+' '+hmm
        alignextract = subprocess.Popen(shlex.split(args), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        retval = alignextract.wait()

        if retval != 0:
                send_error_email(receiver, "", "just_align_extract shell script")
        else:
                send_email(receiver, filename, taskname)

        if receiver!='none':
                send_email(receiver, filename, taskname)

        return

@task(serializer='json')
def just_extract(taskname):
        filename, receiver = open(taskname+'.ext_args').read().split()
        send_init_email("Extract-Only", receiver, filename)

        args = "/home/sravana/webpy_sandbox/just_extract.sh "+taskname
        extract = subprocess.Popen(shlex.split(args), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        retval = extract.wait()

        if retval != 0:
                send_error_email(receiver, "", "just_extract shell script")
        else:
                send_email(receiver, filename, taskname)
        
        if receiver!='none':
                send_email(receiver, filename, taskname)

        return

