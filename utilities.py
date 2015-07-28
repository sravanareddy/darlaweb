#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Creates intermediate argument files, does basic audio processing and conversion.
"""

import argparse
import os
import ntpath
import string
import random
import subprocess
import shlex
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders

ERROR = 0

class CustomException(Exception):
    pass 

def send_init_email(tasktype, receiver, filename):
        username = 'darla.dartmouth'
        password = open('/home/sravana/applications/email/info.txt').read().strip()
        sender = username+'@gmail.com'
        subject = tasktype+' Task started for '+filename
        
        body = 'This is a confirmation to let you know that your job has been submitted. You will receive the results shortly.'

        message = MIMEMultipart()
        message['From'] = 'DARLA <'+sender+'>'
        message['To'] = receiver
        message['Subject']=subject
        message['Date'] = formatdate(localtime = True)

        message.attach(MIMEText(body, 'plain'))

        try:
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(username, password)
                server.sendmail(sender, receiver, message.as_string())
                server.quit()

        except smtplib.SMTPException:
                print 'Unable to send e-mail '

def send_email(receiver, filename, taskname):
        
        username = 'darla.dartmouth'
        password = open('/home/sravana/applications/email/info.txt').read().strip()
        sender = username+'@gmail.com'
        subject = 'Vowel Analysis Results for '+filename

        body = 'The formant extraction results for your data are attached. (1) formants.csv contains detailed information on bandwidths, phonetic environments, and probabilities, (2) formants.fornorm.tsv can be uploaded to the NORM online tool (http://lvc.uoregon.edu/norm/index.php) for additional normalization and plotting options, (3) plot.pdf shows the F1/F2 vowel space of your speakers, and (4) alignments.zip contains the TextGrids of the ASR transcriptions aligned with the audio.\n\n'
        body += 'If you manually correct the transcriptions, you may re-upload your data with the new TextGrids to http://darla.dartmouth.edu/uploadtextgrid and receive revised formant measurements and plots. Alternately, you may upload plaintext transcriptions to http://darla.dartmouth.edu/uploadtrans\n\n'
        body += 'Thank you for using DARLA. Please e-mail us with questions or suggestions.\n'
        message = MIMEMultipart()
        message['From'] = 'DARLA <'+sender+'>'
        message['To'] = receiver
        message['Subject']=subject
        message['Date'] = formatdate(localtime = True)
        
        message.attach(MIMEText(body, 'plain'))
        for nicename, filename in [('formants.csv', taskname+'.aggvowels_formants.csv'), ('formants.fornorm.tsv', taskname+'.fornorm.tsv'), ('plot.pdf', taskname+'.plot.pdf'), ('alignments.zip', taskname+'.alignments.zip')]:
                part = MIMEBase('application', "octet-stream")
                try:
                    with open(filename, "rb") as result:

                        part.set_payload( open(filename,"rb").read() ) #fornorm.tsv? no file 
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', 'attachment; filename='+nicename)
                        message.attach(part)
                except:
                    send_error_email(receiver, filename, "")
            
        try:
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(username, password)
                server.sendmail(sender, receiver, message.as_string())
                server.quit()
                
        except smtplib.SMTPException:
                print 'Unable to send e-mail '


def send_error_email(receiver, filename, message):
    global ERROR;
    
    if ERROR==0:

        username = 'darla.dartmouth'
        password = open('/home/sravana/applications/email/info.txt').read().strip()
        sender = username+'@gmail.com'
        subject = 'Error trying to open '+filename        
        body = 'Unfortunately, there was an error trying to start a file for '+filename + ". We could not "+message

        message = MIMEMultipart()
        message['From'] = 'DARLA <'+sender+'>'
        message['To'] = receiver
        message['Subject']=subject
        message['Date'] = formatdate(localtime = True)

        message.attach(MIMEText(body, 'plain'))

        try:
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(username, password)
                server.sendmail(sender, receiver, message.as_string())
                server.quit()
                ERROR=1

        except smtplib.SMTPException:
                print 'Unable to send e-mail '
    else:
        msg = 'Error email already sent.'

def read_prdict(dictfile):
    spam = map(lambda line: line.split(), open(dictfile).readlines())
    return dict(map(lambda line: (line[0], line[1:]), spam))
    
def g2p(transwords, cmudictfile):
    """Predict pronunciations of words not in dictionary and add"""
    cmudict = read_prdict(cmudictfile)
    oov = filter(lambda word: word not in cmudict, set(transwords))
    if len(oov)==0:
        return
    o = open('OOV.txt', 'w')
    o.write('\n'.join(map(lambda word:word.replace("\\'", "'"), oov))+'\n')
    o.close()
    os.system('/usr/local/bin/g2p.py --model /home/sravana/applications/g2p/model-6 --apply OOV.txt > OOVprons.txt')
    newdict = {}
    for line in open('OOVprons.txt'):
        line = line.split()
        if len(line)<2:
            continue
        newdict[line[0]] = line[1:]
    os.system('rm OOV.txt OOVprons.txt')
    if newdict!={}:
        for word in newdict:
            cmudict[word.replace("'", "\\'")] = newdict[word]
            
        #need to replace \ again for sorting order... argh!
        words = sorted(map(lambda word: word.replace("\\'", "'"), cmudict.keys()))
        
        o = open(cmudictfile+'.tmp', 'w')
        for word in words:
            rword = word.replace("'", "\\'")
            o.write(rword+'  '+' '.join(cmudict[rword])+'\n')
        o.close()
        
    os.system('mv '+cmudictfile+'.tmp '+cmudictfile)
    return

def get_basename(filename):
    basename = ntpath.basename(filename.replace('\\','/').replace(' ', '_'))
    basename, extension = os.path.splitext(basename)
    return basename, extension.lower()

def randomname(fnamelen):
    fname = ''
    for _ in range(fnamelen):
        fname+=random.choice(string.letters)
    return fname

def make_task(datadir):
    try:
        taskname = randomname(30)
        audiodir = os.path.join(datadir, taskname+'.audio')
        if os.path.exists(audiodir): #check if taskname exists
            make_task(datadir) #make a new taskname
        else:
            os.mkdir(audiodir)
            os.system('chown sravana:www-data '+audiodir)
            return taskname, audiodir, ""
    except OSError:
            error_message = "Could not start a job."
            return taskname, audiodir, error_message

def write_transcript(datadir, taskname, reffilecontent, hypfilecontent):
    """Write reference and hypothesis files for evaluation"""
    reffilecontent = string.translate(process_usertext(reffilecontent), 
                                      None, 
                                      string.punctuation).splitlines()
    reffilecontent = filter(lambda line: line!='', reffilecontent)
    hypfilecontent = string.translate(process_usertext(hypfilecontent), 
                                      None, 
                                      string.punctuation).splitlines()
    hypfilecontent = filter(lambda line: line!='', hypfilecontent)
    numreflines = len(reffilecontent)
    numhyplines = len(hypfilecontent)
    if numreflines==numhyplines:
        o = open(os.path.join(datadir, taskname+'.ref'), 'w')
        for li, line in enumerate(reffilecontent):
            o.write(line+' (speaker-'+str(li+1)+')\n')
        o.close()
        o = open(os.path.join(datadir, taskname+'.hyp'), 'w')
        for li, line in enumerate(hypfilecontent):
            o.write(line+' (speaker-'+str(li+1)+')\n')
        o.close()
    return numreflines, numhyplines

def process_usertext(inputstring):
    """clean up unicode, remove punctuation and numbers"""
    transfrom = '\xd5\xd3\xd2\xd0\xd1\xcd\xd4'
    transto = '\'""--\'\''
    unimaketrans = string.maketrans(transfrom, transto)
    #stylized characters that stupid TextEdit inserts. is there an existing module that does this?  
    return string.translate(inputstring.lower(), 
                            unimaketrans, 
                            string.digits).replace("\xe2\x80\x93", " - ").replace('\xe2\x80\x94', " - ").replace('\xe2\x80\x99', "'").strip()

def write_hyp(datadir, taskname, filename, txtfilecontent, cmudictfile):    
    os.system('mkdir -p '+os.path.join(datadir, taskname+'.wavlab'))
    o = open(os.path.join(datadir, taskname+'.wavlab', filename+'.lab'), 'w')

    words = map(lambda word: word.strip(string.punctuation), 
                process_usertext(txtfilecontent).split())
    words = map(lambda word: word.replace("'", "\\'"), words)
    o.write(' '.join(words)+'\n')
    o.close()
    #make dictionary for OOVs
    g2p(words, cmudictfile)

def write_textgrid(datadir, taskname, filename, tgfilecontent):
    #TODO: validate TextGrid
    os.system('mkdir -p '+os.path.join(datadir, taskname+'.mergedtg'))
    o = open(os.path.join(datadir, taskname+'.mergedtg', filename+'.TextGrid'), 'w')
    o.write(tgfilecontent)
    o.close()

def process_audio(audiodir, filename, extension, filecontent, dochunk):
    #write contents of file
    o = open(os.path.join(audiodir, filename+extension), 'w')
    o.write(filecontent)
    o.close()

    if extension == '.mp3':
        # print 'converting', os.path.join(audiodir, filename+extension)  #TODO: try and except here
        os.system("mpg123 "+"-w "+os.path.join(audiodir, filename+'.wav')+' '+os.path.join(audiodir, filename+extension))
        #audio = subprocess.Popen(shlex.split("mpg123 "+"-w "+os.path.join(audiodir, filename+'.wav')+' '+os.path.join(audiodir, filename+extension)), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        #print audio.stdout.readlines()
        #retval = audio.wait()

        #if retval != 0: 
        #    print "Error converting from .mp3 to .wav "
        #    error_message = 'Could not convert from .mp3 to .wav'
        #    return 0, 0, error_message
            
        #os.system('lame --decode '+os.path.join(audiodir, filename+extension)+' '+os.path.join(audiodir, filename+'.wav'))  #TODO: use subprocess instead (it's getting stuck on lame for some reason)
        extension = '.wav'
        # print "converted to", filename+extension
            
    #split and convert frequency
    samprate, filesize, soxerror = soxConversion(filename+extension, audiodir, dochunk)
    return samprate, filesize, soxerror
                        
def youtube_wav(url,audiodir, taskname):
    try:
        tube = subprocess.Popen(shlex.split('youtube-dl '+url+' --extract-audio --audio-format wav --audio-quality 16k -o '+os.path.join(audiodir, 'ytvideo.%(ext)s')), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        # print tube.stdout.readlines()
        return "ytvideo.wav", ""
    except:
        return "ytvideo.wav", "Could not convert youtube video to a .wav file."        

def soxConversion(filename, audiodir, dochunk):
    sample_rate = 0
    file_size = 0.0
    args = "sox --i "+os.path.join(audiodir, filename)
    sox = subprocess.Popen(shlex.split(args), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    # print "I AM HERE"
    # print sox.stdout.readlines()
    retval = sox.wait()

    if retval != 0: 
        error_message = 'Could not do sox conversion '
        # print 'Could not call subprocess '
        return sample_rate, file_size, error_message


    for line in sox.stdout.readlines():
        # print line
        if "Sample Rate" in line:
            line = line.split(':')
            sample_rate = int(line[1].strip())

        if "Duration" in line:
            m = re.search("(=\s)(.*)(\ssamples)", line)
            file_size = float(m.group(2))
            file_size = file_size / sample_rate #gets duration, in seconds of the file.
            file_size /= 60.0

    # print sample_rate
    # print file_size

    #converts wav file to 16000kHz sampling rate if sampling rate is more than
    if sample_rate >= 16000:
        ratecode = '16k'
        sample_rate = 16000
        # print "I AM HERE"                            

    elif sample_rate >= 8000:
        ratecode = '8k'
        sample_rate = 8000
        # print "OR AM I HERE?"

    else:
        # print "OR HERE?"
        error_message = "Sample rate not high enough"
        # return sample_rate, "sample rate not high enough"
        # raise CustomException("sample rate not high enough")
        return sample_rate, file_size, error_message
        #TODO: actually make it work instead of break. Note: this is also a way to catch non-sound files that have been (maliciously?) uploaded using a .wav extension.

    #convert to 16-bit, signed, little endian as well as downsample                                       
    conv = subprocess.Popen(['sox', os.path.join(audiodir, filename), '-r', ratecode, '-b', '16', '-e', 'signed', '-L', os.path.join(audiodir, 'converted_'+filename), 'channels', '1'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    retval = conv.wait()

    if retval != 0:
        error_message = 'Could not downsample file'
        # print error_message
        return sample_rate, file_size, error_message


    # print "retval"
    # print retval

    #split into 20sec chunks. TODO: split on silence
    if dochunk:
        if not os.path.isdir(os.path.join(audiodir, 'splits')):  #need this for multiple files
            os.mkdir(os.path.join(audiodir, 'splits'))

        basename, _ = os.path.splitext(filename)
        conv = subprocess.Popen(['sox', os.path.join(audiodir, 'converted_'+filename), os.path.join(audiodir, 'splits', basename+'.split.wav'), 'trim', '0', '20', ':', 'newfile', ':', 'restart'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        retval = conv.wait()

        if retval != 0:
            error_message = 'Could not split audio file into chunks'
            # print error_message
            return sample_rate, file_size, error_message

    return sample_rate, file_size, ""

def gen_argfiles(datadir, taskname, uploadfilename, samprate, lw, dialect, email):
    """create ctl files"""
    filelist = map(lambda filename: filename[:-4],
                          filter(lambda filename: filename.endswith('.wav'),
                                 os.listdir(os.path.join(datadir, taskname+'.audio', 'splits'))))
    numfiles = len(filelist)
    
    #numsplits = min(numfiles, 8)
    
    #for i in range(numsplits):
    o = open(os.path.join(datadir, taskname+'.ctl'), 'w')
    o.write('\n'.join(filelist))
    o.write('\n')
    o.close()

    """feature extraction"""
    options = {'di': os.path.join(datadir, taskname+'.audio/splits/'),
               'do': os.path.join(datadir, taskname+'.mfc'),
               'ei': 'wav',
               'eo': 'mfc',
               'mswav': 'yes', 
               'raw': 'no',
               'remove_noise': 'no',  #change?
               'remove_silence': 'no',
               'whichchan': '0',
               'samprate': str(samprate),
               'lowerf': '130',    #starting from here, echo the acoustic model
               'feat': '1s_c_d_dd',
               'transform': 'dct',
               'lifter': '22',
               'agc': 'none',
               'cmn': 'current',
               'varnorm': 'no',
               'cmninit': '40'}
    if samprate==8000:
        options.update({'nfilt': '20',
                       'upperf': '3500'})
    else:
        options.update({'nfilt': '25',
                       'upperf': '6800'})

    #for i in range(numsplits):
    o = open(os.path.join(datadir, taskname+'.featurize_args'), 'w')
    options['c'] = os.path.join(datadir, taskname+'.ctl')
    o.write('\n'.join(map(lambda (k, v): '-'+k+' '+v,
                          options.items())))
    o.close()

    os.system('mkdir -p '+os.path.join(datadir, taskname)+'.mfc')
    os.system('chmod g+w '+os.path.join(datadir, taskname)+'.mfc')
    
    """recognition"""
    options = {}
    if samprate==8000:
            hmm = '/home/sravana/acousticmodels/sphinx-8'
            options.update({'nfilt': '20',
                            'upperf': '3500'})
    else:
            hmm = '/home/sravana/acousticmodels/sphinx-16'
            options.update({'nfilt': '25',
                            'upperf': '6800'})
    
    options.update({'cepdir': os.path.join(datadir, taskname+'.mfc'),
                    'cepext': '.mfc',
                    'dict': '/home/sravana/prdicts/cmudict.nostress.txt',
                    'fdict': os.path.join(hmm, 'noisedict'),
                    'hmm': hmm, 
                    'lm': '/home/sravana/languagemodels/en-us.lm.dmp',
                    'lw': str(lw), 
                    'samprate': str(samprate), 
                    'bestpath': 'no',
                    'lowerf': '130',    #starting from here, echo the acoustic model
                    'feat': '1s_c_d_dd',
                    'transform': 'dct',
                    'lifter': '22',
                    'agc': 'none',
                    'cmn': 'current',
                    'varnorm': 'no',
                    'cmninit': '40'})
    
    #for i in range(numsplits):
    o = open(os.path.join(datadir, taskname+'.recognize_args'), 'w')
    options.update({'ctl': os.path.join(datadir, taskname+'.ctl'),
                    'hyp': os.path.join(datadir, taskname+'.hyp'),
                    'hypseg': os.path.join(datadir, taskname+'.hypseg')})
    o.write('\n'.join(map(lambda (k, v): '-'+k+' '+v,
                          options.items())))
    o.close()

    """Align and extract"""
    o = open(os.path.join(datadir, taskname+'.alext_args'), 'w')
    
    o.write(uploadfilename+' ')
    
    if samprate==8000:
            o.write('/home/sravana/acousticmodels/prosodylab-8.zip ')
    else:
            o.write('/home/sravana/acousticmodels/prosodylab-16.zip ')

    if email=="":
        email="none"
    o.write(email)
    o.write('\n')
    o.close()

    return

def gen_txtargfile(datadir, taskname, uploadfilename, samprate, email):
    """Generate alext_args file from uploadtrans task"""
    o = open(os.path.join(datadir, taskname+'.alext_args'), 'w')

    o.write(uploadfilename+' ')

    if samprate==8000:
            o.write('/home/sravana/acousticmodels/prosodylab-8.zip ')
    else:
            o.write('/home/sravana/acousticmodels/prosodylab-16.zip ')

    if email=="":
        email="none"
    o.write(email)
    o.write('\n')
    o.close()

    return

def gen_tgargfile(datadir, taskname, uploadfilename, email):
    """Generate ext_args file for uploadtextgrid task"""
    o = open(os.path.join(datadir, taskname+'.ext_args'), 'w')
    
    o.write(uploadfilename+' ')
    
    if email=="":
        email="none"
    o.write(email)
    o.write('\n')
    o.close()

    return
    
if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-taskname', type=str, help='used to name the files and directories', required=True) #for web app, randomly gen. hash
    parser.add_argument('-samprate', type=float, help='sampling rate in Hz', required=True) #can be input by user or derived from wav files
    parser.add_argument('-lw', type=float, help='language model scaling factor', default=6.5)
    args = parser.parse_args()

    gen_argfiles(args.taskname, args.samprate, args.lw)
    
