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
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders
from collections import defaultdict
import inflect
from textgrid.textgrid import TextGrid
import gdata.youtube
import gdata.youtube.service

ERROR = 0

class CustomException(Exception):
    pass 

def read_textupload(data):
    try:
        return data.decode('utf-8-sig')
    except UnicodeDecodeError:
        try:
            return data.decode('utf-16')
        except UnicodeDecodeError:
            try:
                return data.decode('latin-1')
            except:
                pass
    return

def send_ytupload_email(video_id, taskname, receiver, filename):
    username = 'darla.dartmouth'
    passfile = open('filepaths.txt').readlines()[1].split()[1]
    password = open(passfile).read().strip()
    sender = username+'@gmail.com'

    subject = 'Completely Automated Vowel Extraction with YouTube ASR: Task Started for '+filename
        
    body = 'YouTube video successfully uploaded and processing. Your video ID is '+video_id+' and your taskname ID is '+taskname+' . Please save these IDs, and after about 5 hours, visit our YouTube CC processor (http://darla.dartmouth.edu:8080/main.py/downloadsrttrans) to check if YouTube has generated the ASR captions. You can then run alignment and extraction with these captions.'

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
        return 'Unable to send a confirmation e-mail. Please check your address. '+body
            
def send_init_email(tasktype, receiver, filename):
        username = 'darla.dartmouth'
        passfile = open('filepaths.txt').readlines()[1].split()[1]
        password = open(passfile).read().strip()
        sender = username+'@gmail.com'

        subjectmap = {'asr': 'Completely Automated Vowel Extraction',
                      'txtalign': 'Alignment and Extraction',
                      'boundalign': 'Alignment and Extraction',
                      'extract': 'Formant Extraction',
                      'asredit': 'Alignment and Extraction on Corrected Transcripts'}
        
        subject = subjectmap[tasktype]+': Task Started for '+filename
        
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
                return 'Unable to send e-mail '

def consolidate_hyp(wavlab, outfile):
    basehyps = defaultdict(list)
    for filename in sorted(filter(lambda filename: filename.endswith('.lab'),
                           os.listdir(wavlab))):
        basefile, num = filename[:-4].rsplit('.split', 1)
        basehyps[basefile].append((open(os.path.join(wavlab, filename)).read().replace("\\'", "'"), num))
    o = open(outfile, 'w')
    for basefile in basehyps:
        content = sorted(basehyps[basefile], key=lambda x:int(x[1]))
        for (line, num) in content:
            o.write(line.strip()+' ')
        o.write('('+basefile+')\n')
    o.close()

def send_email(tasktype, receiver, filename, taskname):
        username = 'darla.dartmouth'
        passfile = open('filepaths.txt').readlines()[1].split()[1]
        password = open(passfile).read().strip()
        sender = username+'@gmail.com'

        subjectmap = {'asr': 'Completely Automated Vowel Extraction',
                      'txtalign': 'Alignment and Extraction',
                      'boundalign': 'Alignment and Extraction',
                      'extract': 'Formant Extraction',
                      'asredit': 'Alignment and Extraction on Corrected Transcripts'}
        
        subject = '{0}: Vowel Analysis Results for {1}'.format(subjectmap[tasktype], filename)
        body = 'The formant extraction results for your data are attached. (1) formants.csv contains detailed information on bandwidths, phonetic environments, and probabilities, (2) formants.fornorm.tsv can be uploaded to the NORM online tool (http://lvc.uoregon.edu/norm/index.php) for additional normalization and plotting options, (3) plot.pdf shows the F1/F2 vowel space of your speakers, (4) alignments.zip contains the TextGrids of the ASR transcriptions aligned with the audio'
        if tasktype == 'asr' or tasktype == 'asredit' or tasktype == 'boundalign':
            body += ', and (5) transcription.txt contains the transcriptions.'
            body += 'If you manually correct the transcriptions, you may re-upload your data with the new TextGrids to http://darla.dartmouth.edu/uploadtextgrid and receive revised formant measurements and plots.\n\n'
            body += 'To edit the ASR transcriptions and re-run the alignment and extraction program, go to http://darla.dartmouth.edu:8080/main.py/asredit?taskname={0} '.format(os.path.basename(taskname))
            body += 'Alternately, you may upload corrected plaintext transcriptions to http://darla.dartmouth.edu/uploadtrans'
        else:
            body +='.'
        body += '\n\n'
        body += 'Do not share this e-mail if you need to preserve the privacy of your uploaded data.\n\n'
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
                    part.set_payload( open(filename,"rb").read() ) 
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', 'attachment; filename='+nicename)
                    message.attach(part) 
                except:
                    send_error_email(receiver, filename, "Your job was not completed.")
        if tasktype == 'asr' or tasktype == 'asredit' or tasktype == 'boundalign': #send transcription 
            try:
                consolidate_hyp(taskname+'.wavlab', taskname+'.orderedhyp')
                part = MIMEBase('application', "octet-stream")
                part.set_payload( open(taskname+'.orderedhyp', "rb").read() )
                part.add_header('Content-Disposition', 'attachment; filename=transcription.txt')
                message.attach(part)
            except:
                    send_error_email(receiver, filename, "There was a problem attaching the transcription.")
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
        passfile = open('filepaths.txt').readlines()[1].split()[1]
        password = open(passfile).read().strip()
        sender = username+'@gmail.com'
        subject = 'Error trying to process '+filename        
        body = 'Unfortunately, there was an error running your job for '+filename + ". "+message

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
    
def g2p(taskname, transwords, cmudictfile):
    """Predict pronunciations of words not in dictionary and add"""
    cmudict = read_prdict(cmudictfile)
    oov = filter(lambda word: word not in cmudict, set(transwords))
    if len(oov)==0:
        return
    o = open(taskname+'.oov', 'w')
    o.write('\n'.join(map(lambda word:word.replace("\\'", "'"), oov))+'\n')
    o.close()
    os.system('/usr/local/bin/g2p.py --model /home/darla/applications/g2p/model-6 --apply '+taskname+'.oov > '+taskname+'.oovprons')
    newdict = {}
    for line in open(taskname+'.oovprons'):
        line = line.split()
        if len(line)<2:
            continue
        newdict[line[0]] = line[1:]
    os.system('rm '+taskname+'.oov '+taskname+'.oovprons')
    if newdict!={}:
        for word in newdict:
            cmudict[word.replace("'", "\\'")] = newdict[word]
            
        #need to replace \ again for sorting order... argh!
        words = sorted(map(lambda word: word.replace("\\'", "'"), cmudict.keys()))
        
        o = open(taskname+'.'+cmudictfile, 'w')
        for word in words:
            rword = word.replace("'", "\\'")
            o.write(rword+'  '+' '.join(cmudict[rword])+'\n')
        o.close()
        
        os.system('mv '+taskname+'.'+cmudictfile+' '+cmudictfile)
    return

def get_basename(filename):
    basename = ntpath.basename(filename.replace('\\','/').replace(' ', '_').replace('&', 'and'))
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
            os.system('chgrp www-data '+audiodir)
            return taskname, audiodir, ""
    except OSError:
            error_message = "Could not start a job."
            return taskname, audiodir, error_message

def write_transcript(datadir, taskname, reffilecontent, hypfilecontent, cmudictfile):
    """Write reference and hypothesis files for evaluation, g2p for OOVs"""
    punct = '!"#$%&\()*+,-./:;<=>?@[\\]^_`{|}~' #same as string.punct but no '
    reffilecontent = string.translate(process_usertext(reffilecontent), 
                                      None, 
                                      punct).splitlines()
    reffilecontent = filter(lambda line: line!='', reffilecontent)
    hypfilecontent = string.translate(process_usertext(hypfilecontent), 
                                      None, 
                                      punct).splitlines()
    hypfilecontent = filter(lambda line: line!='', hypfilecontent)
    numreflines = len(reffilecontent)
    numhyplines = len(hypfilecontent)
    allwords = set()   #for g2p
    if numreflines==numhyplines:
        o = open(os.path.join(datadir, taskname+'.ref'), 'w')
        for li, line in enumerate(reffilecontent):
            words = map(lambda word: word.replace("'", "\\'"), line.split())
            o.write(' '.join(words)+'\n')
            allwords.update(words)
        o.close()
        o = open(os.path.join(datadir, taskname+'.hyp'), 'w')
        for li, line in enumerate(hypfilecontent):
            words = map(lambda word: word.replace("'", "\\'"), line.split())
            o.write(' '.join(words)+'\n')
            allwords.update(words)
        o.close()
    
    g2p(os.path.join(datadir, taskname), allwords, cmudictfile)  #OOVs
    
    return numreflines, numhyplines

def process_usertext(inputstring):
    """clean up unicode, translate numbers"""
    transfrom = '\xd5\xd3\xd2\xd0\xd1\xcd\xd4'
    transto = '\'""--\'\''
    unimaketrans = string.maketrans(transfrom, transto)
    #MS line breaks and stylized characters that stupid TextEdit inserts. (is there an existing module that does this?)
    cleaned = string.translate(inputstring.lower(), 
                            unimaketrans).replace("\xe2\x80\x93", " - ").replace('\xe2\x80\x94', " - ").replace('\xe2\x80\x99', "'").replace('\xe2\x80\x9c', '"').replace('\xe2\x80\x9d', '"').replace('\r\n', '\n').replace('\r', '\n').strip()
    digitconverter = inflect.engine()
    returnstr = ''
    for line in cleaned.splitlines():
        returnstr += ' '.join(map(lambda word:
                        digitconverter.number_to_words(word).replace('-', ' ').replace(',', '') if word[0].isdigit() or (word[0]=="'" and len(word)>1 and word[1].isdigit()) else word, 
                        line.split()))+'\n'
    return returnstr

def write_hyp(datadir, taskname, filename, txtfilecontent, cmudictfile):    
    os.system('mkdir -p '+os.path.join(datadir, taskname+'.wavlab'))
    try:
        o = open(os.path.join(datadir, taskname+'.wavlab', filename+'.lab'), 'w')
        words = map(lambda word: word.strip(string.punctuation), 
                    process_usertext(txtfilecontent).split())
        words = map(lambda word: word.replace("'", "\\'"), words)
        o.write(' '.join(words)+'\n')
        o.close()
        #make dictionary for OOVs
        g2p(os.path.join(datadir, taskname), set(words), cmudictfile)
        return ""
    except:
        return "Error processing transcript file. Please check plaintext format and try again."

def write_sentgrid_as_lab(datadir, taskname, filename, txtfile, cmudictfile):
    os.system('mkdir -p '+os.path.join(datadir, taskname+'.wavlab'))
    #parse textgrid, extracting sentence boundaries
    tg = TextGrid()
    try:
        tg.read(os.path.join(datadir, txtfile))
    except:
        error = 'Not a valid TextGrid file. Please correct it and upload again.'
        return [], error
    
    os.system('rm '+os.path.join(datadir, txtfile))
    
    sent_tier = tg.getFirst('sentence')  
    if not sent_tier:  #something wrong with the tier name
        error = 'Please upload a TextGrid with a tier named "sentence" containing breath groups or utterances.' 
        return [], error
    
    chunks = []
    allwords = set()
    #prosodylab aligner strips out silences from ends, so let's attach them to adjacent. TODO: fix the PL aligner code
    ctr = 1
    for i, interval in enumerate(sent_tier.intervals):
        if interval.mark:
            o = open(os.path.join(datadir,
                              taskname+'.wavlab',
                                  filename+'.split{0:03d}.lab'.format(ctr)),
                 'w')
            words = map(lambda word: word.strip(string.punctuation),
                    process_usertext(interval.mark.encode('utf8')).split())
            words = map(lambda word: word.replace("'", "\\'"), words)
            for word in words:
                allwords.add(word)
                o.write(word+' ')
            o.write('\n')
            if chunks==[]:
                chunks.append([0, interval.maxTime])
            else:
                chunks.append([interval.minTime, interval.maxTime])
            o.close()
            ctr+=1
        elif len(chunks)>0:
            chunks[-1][1] = interval.maxTime
        
    g2p(os.path.join(datadir, taskname), allwords, cmudictfile)
    return chunks, ""

def convert_to_video(audiodir, filename, extension, audiofilecontent):
    #write contents
    try:
        audiofile = os.path.join(audiodir, filename+extension)
        o = open(audiofile, 'w')
        o.write(audiofilecontent)
        o.close()
    
        videofile = os.path.join(audiodir, filename+'.mp4')
        os.system('ffmpeg -loop 1 -i static/images/shield.jpg -i '+audiofile+' -strict experimental -b:a 192k -shortest '+videofile)
    except:
        return "Error reading or converting your audio file."

def get_entry_id(url):
        """YouTube video id from a URL"""
        return str(url).split('/')[-2][:-1]

def upload_youtube(taskname, videofile):
        passfile = open('filepaths.txt').readlines()[1].split()[1]
        
        try:
                yt_service = gdata.youtube.service.YouTubeService()
                yt_service.ssl = True
                yt_service.developer_key = open('youtubekey.txt').read().strip()
                yt_service.email = 'darla.dartmouth@gmail.com'
                yt_service.password = open(passfile).read().strip()
                yt_service.source = 'DARLA'
                yt_service.ProgrammaticLogin()

                my_media_group = gdata.media.Group(title=gdata.media.Title(text='Darla sociophonetics sample '+taskname),
                                        description=gdata.media.Description(description_type='plain',
                                                                            text='My description '+taskname), 
                                       keywords=gdata.media.Keywords(text='sociophonetics'), 
                                       category=[gdata.media.Category(text='Education', scheme='http://gdata.youtube.com/schemas/2007/categories.cat', label='Education')], 
                                       player=None, 
                                      private=gdata.media.Private())

                video_entry = gdata.youtube.YouTubeVideoEntry(media=my_media_group)
                new_entry = yt_service.InsertVideoEntry(video_entry, videofile)

                upload_status = yt_service.CheckUploadStatus(new_entry)
                if "duplicate" in upload_status:
                    return 0, "Failed to upload to YouTube. If you tried uploading the same or similar file recently, YouTube's spam detector probably rejected your upload." 
                
                return get_entry_id(new_entry.id), None
        except:
                return 0, "Failed to upload to YouTube. Check your file and try again. If you tried uploading the same or similar file recently, YouTube's spam detector probably rejected your upload."

def download_youtube(audiodir, filename, video_id):
        passfile = open('filepaths.txt').readlines()[1].split()[1]
        
        try:
                email = 'darla.dartmouth@gmail.com'
                password = open(passfile).read().strip()
                dl = subprocess.Popen(shlex.split('youtube-dl --write-auto-sub --skip-download https://www.youtube.com/watch?v='+str(video_id)+' -u '+email+' -p '+password+' -o '+os.path.join(audiodir, filename+'.srt')), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                r = dl.wait()
                
                if os.path.exists(os.path.join(audiodir, filename+'.en.srt')):
                    return None
                else:
                    return 'YouTube did not generate ASR transcriptions for your file. Wait a bit longer and try again. If it has been at least 4-5 hours after your uploaded your audio, the file may be too long or noisy.'
        
        except:
                return 'YouTube did not generate ASR transcriptions for your file. Wait a bit longer and try again. If it has been at least 4-5 hours after your uploaded your audio, the file may be too long or noisy.'
         
def write_textgrid(datadir, taskname, filename, tgfilecontent):
    #TODO: validate TextGrid
    os.system('mkdir -p '+os.path.join(datadir, taskname+'.mergedtg'))
    o = open(os.path.join(datadir, taskname+'.mergedtg', filename+'.TextGrid'), 'w')
    o.write(tgfilecontent)
    o.close()

def write_chunks(chunks, filepath):
    o = open(filepath, 'w')
    for chunk in chunks:
        o.write('{0} {1}\n'.format(chunk[0], chunk[1]))
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
        #retval = audio.wait()

        extension = '.wav'
            
    #split and convert frequency
    samprate, filesize, chunks, soxerror = soxConversion(filename+extension, audiodir, dochunk)
    return samprate, filesize, chunks, soxerror
                        
def youtube_wav(url,audiodir, taskname):
    try:
        yt_command = 'youtube-dl '+url+' --extract-audio --audio-format wav --audio-quality 16k -o '+os.path.join(audiodir, 'ytvideo.%(ext)s')
        tube = subprocess.Popen(shlex.split(yt_command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        tube.wait()
        return "ytvideo.wav", ""
    except:
        return "ytvideo.wav", "Could not convert youtube video to a .wav file."        

def soxConversion(filename, audiodir, dochunk=None):
    sample_rate = 0
    file_size = 0.0
    args = "sox --i "+os.path.join(audiodir, filename)
    sox = subprocess.Popen(shlex.split(args), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    #print "I AM HERE"
    #print sox.stdout.readlines()
    retval = sox.wait()

    if retval != 0: 
        error_message = 'Could not process your audio file. Please check that the file is valid and not blank.'
        # print 'Could not call subprocess '
        return sample_rate, file_size, 0, error_message

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

    #converts wav file to 16000kHz sampling rate if sampling rate is more than
    if sample_rate >= 16000:
        ratecode = '16k'
        sample_rate = 16000

    elif sample_rate >= 8000:
        ratecode = '8k'
        sample_rate = 8000
        
    else:
        error_message = "Sample rate not high enough. Please upload files with minimum 8kHz sample rate."
        # return sample_rate, "sample rate not high enough"
        # raise CustomException("sample rate not high enough")
        return sample_rate, file_size, 0, error_message
        #TODO: actually make it work instead of break. Note: this is also a way to catch non-sound files that have been (maliciously?) uploaded using a .wav extension.
    
    #convert to 16-bit, signed, little endian as well as downsample                        
    conv = subprocess.Popen(['sox', os.path.join(audiodir, filename), '-r', ratecode, '-b', '16', '-e', 'signed', '-L', os.path.join(audiodir, 'converted_'+filename), 'channels', '1'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    retval = conv.wait()
    #print 'Converted', retval
    
    if retval != 0:
        error_message = 'Could not downsample file'
        # print error_message
        return sample_rate, file_size, error_message
    
    #split into chunks as specified. TODO: split on silence
    chunks = []
    if dochunk:
        if not os.path.isdir(os.path.join(audiodir, 'splits')):  #need this for multiple files
            os.mkdir(os.path.join(audiodir, 'splits'))

        basename, _ = os.path.splitext(filename)
        
        if type(dochunk) is int:
            chunks = map(lambda i: (i, i+20), range(0, int(file_size*60), 20))
                
            conv = subprocess.Popen(['sox', os.path.join(audiodir, 'converted_'+filename), os.path.join(audiodir, 'splits', basename+'.split.wav'), 'trim', '0', str(dochunk), ':', 'newfile', ':', 'restart'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            retval = conv.wait()
            if retval != 0:
                error_message = 'Could not split audio file into chunks.'
                return sample_rate, file_size, chunks, error_message

        elif type(dochunk) is list:
            chunks = dochunk
            for ci, chunk in enumerate(dochunk):
                conv = subprocess.Popen(['sox', os.path.join(audiodir, 'converted_'+filename), os.path.join(audiodir, 'splits', basename+'.split{0:03d}.wav'.format(ci+1)), 'trim', str(chunk[0]), str(chunk[1]-chunk[0])], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                retval = conv.wait()
                if retval != 0:
                    error_message = 'Could not split audio file into chunks given by TextGrid.'
                    return sample_rate, file_size, chunks, error_message
            
    return sample_rate, file_size, chunks, ""

def gen_argfiles(datadir, taskname, uploadfilename, task, email, samprate=None, lw=None, dialect=None):
    """create ctl files if applicable"""
    if task=='asr':
        filelist = map(lambda filename: filename[:-4],
                          filter(lambda filename: filename.endswith('.wav'),
                                 os.listdir(os.path.join(datadir, taskname+'.audio', 'splits'))))
        numfiles = len(filelist)
    
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
            hmm = '/home/darla/acousticmodels/sphinx-8'
            options.update({'nfilt': '20',
                            'upperf': '3500'})
        else:
            hmm = '/home/darla/acousticmodels/sphinx-16'
            options.update({'nfilt': '25',
                            'upperf': '6800'})
    
        options.update({'cepdir': os.path.join(datadir, taskname+'.mfc'),
                        'cepext': '.mfc',
                        'dict': '/home/darla/prdicts/cmudict.nostress.txt',
                        'fdict': os.path.join(hmm, 'noisedict'),
                        'hmm': hmm, 
                        'lm': '/home/darla/languagemodels/en-us.lm.dmp',
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
        o.write('/home/darla/acousticmodels/htkpenn8kplp ')
    else:
        o.write('/home/darla/acousticmodels/htkpenn16kplp ')
    
    o.write(email+' ')
    o.write(task+'\n')
    o.close()
    return

