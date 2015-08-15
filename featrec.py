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
        
        filename, _, receiver, _ = open(taskname+'.alext_args').read().split()
        send_init_email("Completely Automated Vowel Extraction", receiver, filename)
        
        args = "/usr/local/bin/sphinx_fe -argfile "+taskname+".featurize_args"
        audio = os.system(args)
        if audio != 0 and receiver!='none':
                send_error_email(receiver, "", "sphinx_fe processing")
                return False
        args = "/usr/local/bin/pocketsphinx_batch -argfile "+taskname+".recognize_args"
        audio = os.system(args)
        if audio != 0 and receiver!='none':
                send_error_email(receiver, "", "pocketsphinx_batch processing")
                return False               
        return True

@task(serializer='json')
def align_extract(taskname):
        filename, align_hmm, receiver, task = open(taskname+'.alext_args').read().split()
        args = "./align_and_extract.sh "+taskname+" "+align_hmm+" "+task
        align = subprocess.Popen(shlex.split(args), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        retval = align.wait()

        if retval != 0:
                send_error_email(receiver, filename, "Alignment and extraction process failed.")
        else:
                send_email(receiver, filename, taskname)
        return
