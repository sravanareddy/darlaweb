"""E-mail utilities"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders
from utilities import read_filepaths
from textgrid import TextGrid
from collections import defaultdict
import json
import sys
import os

def extract_trans_from_tg(tgfile, outfile):
    """extract transcript from TextGrid"""
    with open(outfile, 'w') as o:
        tg = TextGrid()
        tg.read(tgfile)
        o.write(' '.join(map(lambda interval: interval.mark, tg.tiers[0])))

def send_init_email(tasktype, receiver, filename):
    filepaths = read_filepaths()
    password = open(filepaths['PASSWORD']).read().strip()
    username = 'darla.dartmouth'
    sender = username+'@gmail.com'

    subjectmap = {'asr': 'Completely Automated Vowel Extraction',
                      'azure': 'Azure-Based Automated Vowel Extraction',
                      'googleasr': 'Completely Automated Vowel Extraction',
                      'txt': 'Alignment and Extraction',
                      'bound': 'Alignment and Extraction',
                      'extract': 'Formant Extraction',
                      'bedword': 'Bed Word: Automated Transcription via Deepgram'}
#                      'asredit': 'Alignment and Extraction on Corrected Transcripts'}

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
        return 'Unable to send e-mail \n {0} \n to {1}'.format(body, receiver)

def send_email(tasktype, receiver, filename, taskdir, error_check):
        filepaths = read_filepaths()
        password = open(filepaths['PASSWORD']).read().strip()
        username = 'darla.dartmouth'
        sender = username+'@gmail.com'

        alext_args = json.load(open(os.path.join(taskdir, 'alext_args.json')))

        subjectmap = {'asr': 'Completely Automated Vowel Extraction',
                      'googleasr': 'Completely Automated Vowel Extraction',
                      'txt': 'Alignment and Extraction',
                      'bound': 'Alignment and Extraction',
                      'extract': 'Formant Extraction'}
                      #  'asredit': 'Alignment and Extraction on Corrected Transcripts'}

        subject = '{0}: Vowel Analysis Results for {1}'.format(subjectmap[tasktype], filename)
        body = 'The formant extraction results for your data are attached:\n\n'
        body += '(1) formants.csv contains detailed information on bandwidths and phonetic environments. '
        if alext_args['delstopwords'] == 'Y':
            body += 'You elected to remove stop-words ({0}/stopwords). '.format(filepaths['URLBASE'])
        else:
            body += 'You elected to retain stop-words. '
        if int(alext_args['maxbandwidth']) < 1e10:
            body += 'You elected to filter our tokens with F1 or F2 bandwidths over {0} Hz. '.format(alext_args['maxbandwidth'])
        else:
            body += 'You elected not to filter out high bandwidth tokens. '
        if alext_args['delunstressedvowels']=='Y':
            body += 'You elected to ignore unstressed vowels. '
        else:
            body += 'You elected to retain unstressed vowels. '
        body += '\n'
        body += '(2) formants.fornorm.tsv can be uploaded to the NORM online tool (http://lingtools.uoregon.edu/norm/) for additional normalization and plotting options\n'
        body += '(3) plot.pdf shows the F1/F2 vowel space of your speakers\n'
        body += '(4) The .TextGrid file contains the transcription aligned with the audio\n'
        if tasktype == 'asr' or tasktype == 'azure' or tasktype == 'googleasr' or tasktype == 'asredit' or tasktype == 'bound':
            body += '(5) transcription.txt contains the transcriptions.\n\n'
            body += 'If you manually correct the alignments in the TextGrid, you may re-upload your data with the new TextGrid to '
            body += filepaths['URLBASE']+'/uploadextract and receive revised formant measurements and plots.\n'

            """
            body += '\nTo use our online playback tool to edit the ASR transcriptions and then re-run alignment and extraction, go to '
            body += filepaths['URLBASE']+'/asredit?taskname={0} \n'.format(os.path.basename(taskdir))
            body += 'Note that this link is only guaranteed to work for 72 hours since we periodically delete user files.\n\n'
            """
            body += '\nYou may upload corrected plaintext transcriptions to '+filepaths['URLBASE']+'/uploadtxt and rerun your job \n'

        body += '\n'
        body += 'Do not share this e-mail if you need to preserve the privacy of your uploaded data.\n\n'
        body += 'Thank you for using DARLA. Please e-mail us with questions or suggestions.\n'

        message = MIMEMultipart()
        message['From'] = 'DARLA <'+sender+'>'
        message['To'] = receiver
        message['Subject']=subject
        message['Date'] = formatdate(localtime = True)

        message.attach(MIMEText(body, 'plain'))
        filelist = [('formants.csv', os.path.join(taskdir, 'aggvowels_formants.csv')),
                                       ('formants.fornorm.tsv', os.path.join(taskdir, 'fornorm.tsv')),
                                       ('plot.pdf', os.path.join(taskdir, 'plot.pdf')),
                                       (filename+'.TextGrid', os.path.join(taskdir, 'aligned', 'audio.ordered.TextGrid'))]
        for nicename, realfilename in filelist:
                part = MIMEBase('application', "octet-stream")
                try:
                    part.set_payload( open(realfilename,"rb").read() )
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', 'attachment; filename='+nicename)
                    message.attach(part)
                except:
                    error_check = send_error_email(receiver, filename, "Your job was not completed.", error_check) # returns false after error sends
        if tasktype == 'asr' or tasktype == 'azure' or tasktype == 'googleasr' or tasktype == 'asredit' or tasktype == 'bound': #send transcription
            try:
                part = MIMEBase('application', "octet-stream")
                extract_trans_from_tg(os.path.join(taskdir, 'audio.TextGrid'), os.path.join(taskdir, 'transcript.txt'))
                part.set_payload( open(os.path.join(taskdir, 'transcript.txt'), "rb").read() )
                part.add_header('Content-Disposition', 'attachment; filename=transcription.txt')
                message.attach(part)
            except:
                error_check = send_error_email(receiver, filename, "There was a problem attaching the transcription.", error_check)
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(username, password)
            server.sendmail(sender, receiver, message.as_string())
            server.quit()

        except smtplib.SMTPException:
            sys.stderr.write('Unable to send e-mail \n {0} \n to {1}'.format(body, receiver))

def send_error_email(receiver, filename, message, first):
    # sends error email, returns false so can use this return value to send again for "first" so task
    # global ERROR;

    if first:

        sys.stderr.write('First and only error email sent')

        filepaths = read_filepaths()
        password = open(filepaths['PASSWORD']).read().strip()
        username = 'darla.dartmouth'
        sender = username+'@gmail.com'
        subject = 'Error trying to process '+filename
        body = 'Unfortunately, there was an error running your job for '+filename + ". "+message
        body += '\nTo help us identify the problem, you are welcome to message us with attached file(s) at darla.dartmouth@gmail.com.'
        body += '\nYou might also want to look over our Helpful Hints page (http://jstanford.host.dartmouth.edu/DARLA_Helpful_Hints_page.html), which includes a discussion of common problems when using the semi-automated tool.'
        body += '\nSorry about the inconvenience.'
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
            return False

        except smtplib.SMTPException:
            sys.stderr.write('Unable to send error e-mail message: \n {0} \n to {1}'.format(body, receiver))
    else:
        sys.stderr.write('Error email already sent')
        return False

def send_unicode_warning_email(receiver, filename, warning):
    # sends unicode warning email
    
    sys.stderr.write('Unicode warning email sent: ' + warning)

    filepaths = read_filepaths()
    password = open(filepaths['PASSWORD']).read().strip()
    username = 'darla.dartmouth'
    sender = username+'@gmail.com'
    subject = 'WARNING: Invalid (non-ASCII) character found when trying to process ' + filename
    body = 'The following encoding error was caught when running your job for ' + filename + '.\n'
    body += warning
    body += unicode(u'\nThe error was caught and the job was completed by omitting non-ASCII characters in your transcription, but the output may not be accurate; for accurate results, please remove these characters and reupload. For example, if you spell "caf\u00e9" with an acute accent instead of pure ASCII ("cafe"), it would be filtered as "caf", which will result in the misalignment of the second vowel.')
    body += '\nYou might also want to look over our Helpful Hints page (http://jstanford.host.dartmouth.edu/DARLA_Helpful_Hints_page.html), which includes a discussion of common problems when using the semi-automated tool.'
    message = MIMEMultipart()
    message['From'] = 'DARLA <'+sender+'>'
    message['To'] = receiver
    message['Subject']=subject
    message['Date'] = formatdate(localtime = True)

    message.attach(MIMEText(body, _charset='utf-8'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(username, password)
        server.sendmail(sender, receiver, message.as_string())
        server.quit()
        return False

    except smtplib.SMTPException:
        sys.stderr.write('Unable to send error e-mail message: \n {0} \n to {1}'.format(body, receiver))

def send_bedword_email(receiver, filename, taskdir, formats, punctuate, diarize, using_darla):
        filepaths = read_filepaths()
        password = open(filepaths['PASSWORD']).read().strip()
        username = 'darla.dartmouth'
        sender = username+'@gmail.com'

        subject = 'Bed Word Automated Transcription Results for {0}'.format(filename)
        body = 'The automated transcription results for your data are attached.\n\n'
        
        body += 'We have provided transcriptions in the following formats:\n'
        for format in formats:
            body += format + '\n'

        if punctuate:
            body += '\nYou requested that the outputs include punctuation.\n'
        else:
            body += '\nYou requested that the outputs do not include punctuation.\n'

        if diarize:
            body += '\nYou requested for the interviewer transcription to be removed. We have assumed that' + \
            ' there are two speakers, and that the interviewee is the person who speaks more and the interviewer is the person who speaks less.\n'

        if using_darla:
            body += '\n'
            body += 'You requested to use DARLA\'s Alignment and Extraction tool on the automated transcription. They are currently running and you will receive an email shortly.' 
        body += '\n\n'
        body += 'Do not share this e-mail if you need to preserve the privacy of your uploaded data.\n'
        body += 'Thank you for using DARLA. Please e-mail us with questions or suggestions.\n'

        message = MIMEMultipart()
        message['From'] = 'DARLA <'+sender+'>'
        message['To'] = receiver
        message['Subject']=subject
        message['Date'] = formatdate(localtime = True)

        message.attach(MIMEText(body, 'plain'))
        filelist = []
        for format in formats:
            filelist.append((filename + format, os.path.join(taskdir, 'output_formats', filename + format)))
        for nicename, realfilename in filelist:
                part = MIMEBase('application', "octet-stream")
                try:
                    part.set_payload( open(realfilename,"rb").read() )
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', 'attachment; filename='+nicename)
                    message.attach(part)
                except:
                    error_check = send_error_email(receiver, filename, "Your job was not completed.", error_check) # returns false after error sends
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(username, password)
            server.sendmail(sender, receiver, message.as_string())
            server.quit()

        except smtplib.SMTPException:
            sys.stderr.write('Unable to send e-mail \n {0} \n to {1}'.format(body, receiver))