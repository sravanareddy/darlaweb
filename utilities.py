#!/usr/bin/env python

"""Creates intermediate script files based on user options and data
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

class CustomException(Exception):
    pass 

def send_init_email(receiver, filename):
        username = 'darla.dartmouth'
        password = open('/home/sravana/applications/email/info.txt').read().strip()
        sender = username+'@gmail.com'
        subject = 'Task started for '+filename
        
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
        os.chdir('/home/sravana/data/webphonetics/')
        username = 'darla.dartmouth'
        password = open('/home/sravana/applications/email/info.txt').read().strip()
        sender = username+'@gmail.com'
        subject = 'Vowel Analysis Results for '+filename

        body = 'The formant extraction results for your data are attached. (1) formants.csv contains detailed information on bandwidths, phonetic environments, and probabilities, (2) formants.fornorm.tsv can be uploaded to the NORM online tool (http://ncslaap.lib.ncsu.edu/tools/norm/) for additional normalization and plotting options, (3) plot.pdf shows the F1/F2 vowel space of your speakers, and (4) alignments.zip contains the TextGrids of the ASR transcriptions aligned with the audio.\n\n'
        body += 'If you manually correct the transcriptions, you may re-upload your data with the new TextGrids to http://darla.dartmouth.edu/cgi-bin/uploadWavTG.cgi and receive revised formant measurements and plots.\n\n'
        body += 'Thank you for using DARLA. Please e-mail us with questions or suggestions.\n'
        message = MIMEMultipart()
        message['From'] = 'DARLA <'+sender+'>'
        message['To'] = receiver
        message['Subject']=subject
        message['Date'] = formatdate(localtime = True)
        
        message.attach(MIMEText(body, 'plain'))
        for nicename, filename in [('formants.csv', taskname+'.aggvowels_formants.csv'), ('formants.fornorm.tsv', taskname+'.fornorm.tsv'), ('plot.pdf', taskname+'.plot.pdf'), ('alignments.zip', taskname+'.alignments.zip')]:
                part = MIMEBase('application', "octet-stream")
                part.set_payload( open(filename,"rb").read() )
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment; filename='+nicename)
                message.attach(part)
            
        try:
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(username, password)
                server.sendmail(sender, receiver, message.as_string())
                server.quit()
                
        except smtplib.SMTPException:
                print 'Unable to send e-mail '

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
    taskname = randomname(30)
    audiodir = os.path.join(datadir, taskname+'.audio')
    if os.path.exists(audiodir): #check if taskname exists
        make_task(datadir) #make a new taskname
    else:
        os.mkdir(audiodir)
        return taskname, audiodir

def process_audio(audiodir, filename, extension, filecontent):
    #write contents of file
    o = open(os.path.join(audiodir, filename+extension), 'w')
    o.write(filecontent)
    o.close()

    if extension == '.mp3':
        print 'converting', os.path.join(audiodir, filename+extension)
        os.system('lame --decode '+os.path.join(audiodir, filename+extension)+' '+os.path.join(audiodir, filename+'.wav'))  #TODO: use subprocess instead
        extension = '.wav'
        print "converted to", filename+extension
    
    #split and convert frequency
    samprate = soxConversion(filename+extension, audiodir)
    return samprate
                        
def youtube_wav(url,taskname):
    tube = subprocess.Popen(shlex.split('youtube-dl '+url+' --extract-audio --audio-format wav --audio-quality 16k -o /home/sravana/data/webphonetics/'+taskname+'.audio/ytvideo.%(ext)s'), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return "ytvideo.wav"
        
def process_wav(filename, taskname, fileid):
    try:
        samprate,filesize, r = soxConversion(filename+'.wav', taskname)
        print "<div id=\""+fileid+"\">"
        print "Sound file name: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<tt>", filename, "</tt><br>"
        print "<input type=\"hidden\" name=\"filename"+fileid+"\" value=\""+filename+"\">"
        
        if fileid!='0':
            print "<input type=\"checkbox\" class=\"copy\" value=\""+fileid+"\" /> Check if speaker is same as above<br>"
        
        print "Speaker ID: <input type =\"textbox\" name=\"name"+fileid+"\" id=\"name"+fileid+"\" required/>"
        print "Sex:",
        print "<input type=\"radio\" id=\"msex"+fileid+"\" name=\"sex"+fileid+"\" value=\"M\" required/>Male"
        print "<input type=\"radio\" id=\"fsex"+fileid+"\" name=\"sex"+fileid+"\" value=\"F\" required/>Female"
        print "<input type=\"radio\" id=\"csex"+fileid+"\" name=\"sex"+fileid+"\" value=\"F\" required/>Child"
        print "<p>"
        print "</div>"

        return samprate, filesize, r
        
    except IOError:
        print "Error reading file "+filename
    except:
        print "<span class=\"error\" id=\"error_msg\">ERROR: something went wrong while processing the file "+filename+"</span>"

def soxConversion(filename, audiodir):
    sample_rate = 0
    file_size = 0.0
    args = "sox --i "+os.path.join(audiodir, filename)
    sox = subprocess.Popen(shlex.split(args), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in sox.stdout.readlines():
        if "Sample Rate" in line:
            line = line.split(':')
            sample_rate = int(line[1].strip())
        if "Duration" in line:
            m = re.search("(=\s)(.*)(\ssamples)", line)
            file_size = float(m.group(2))
            file_size = file_size / sample_rate #gets duration, in seconds of the file.                  

    retval = sox.wait()

    #converts wav file to 16000kHz sampling rate if sampling rate is more than                            
    if sample_rate >= 16000:
        ratecode = '16k'
        sample_rate = 16000

    elif sample_rate >= 8000:
        ratecode = '8k'
        sample_rate = 8000

    else: 
        # return sample_rate, "sample rate not high enough"
        # raise CustomException("sample rate not high enough")
        return sample_rate, file_size, CustomException("sample rate not high enough")
        #TODO: actually make it work instead of break.                                   

    #convert to 16-bit, signed, little endian as well as downsample                                       
    conv = subprocess.Popen(['sox', os.path.join(audiodir, filename), '-r', ratecode, '-b', '16', '-e', 'signed', '-L', os.path.join(audiodir, 'converted_'+filename), 'channels', '1'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    retval = conv.wait()

    #split into 30sec chunks. TODO: split on silence                          
    if not os.path.isdir(os.path.join(audiodir, 'splits')):
        os.mkdir(os.path.join(audiodir, 'splits'))
    basename, _ = os.path.splitext(filename)
    conv = subprocess.Popen(['sox', os.path.join(audiodir, 'converted_'+filename), os.path.join(audiodir, 'splits', basename+'.split.wav'), 'trim', '0', '20', ':', 'newfile', ':', 'restart'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    retval = conv.wait()

    #os.remove(os.path.join(audiodir, filename))
    
    return sample_rate

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
    options = {'di': taskname+'.audio/splits/',
               'do': taskname+'.mfc',
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
    options['c'] = taskname+'.ctl'
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
    
    options.update({'cepdir': taskname+'.mfc',
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
    options.update({'ctl': taskname+'.ctl',
                    'hyp': taskname+'.hyp',
                    'hypseg': taskname+'.hypseg'})
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

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-taskname', type=str, help='used to name the files and directories', required=True) #for web app, randomly gen. hash
    parser.add_argument('-samprate', type=float, help='sampling rate in Hz', required=True) #can be input by user or derived from wav files
    parser.add_argument('-lw', type=float, help='language model scaling factor', default=6.5)
    args = parser.parse_args()

    gen_argfiles(args.taskname, args.samprate, args.lw)
    
