"""E-mail utilities"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders
from utilities import read_filepaths
from hyp2mfa import extract_trans_from_tg
from collections import defaultdict
import json
import sys
import os


def send_init_email(tasktype, receiver, filename):
    filepaths = read_filepaths()
    password = open(filepaths['PASSWORD']).read().strip()
    username = 'darla.dartmouth'
    sender = username+'@gmail.com'

    subjectmap = {'asr': 'Completely Automated Vowel Extraction',
                      'googleasr': 'Completely Automated Vowel Extraction',
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
        return 'Unable to send e-mail \n {0} \n to {1}'.format(body, receiver)

def send_email(tasktype, receiver, filename, taskdir, error_check):
        filepaths = read_filepaths()
        password = open(filepaths['PASSWORD']).read().strip()
        username = 'darla.dartmouth'
        sender = username+'@gmail.com'

        alext_args = json.load(open(os.path.join(taskdir, 'alext_args.json')))

        subjectmap = {'asr': 'Completely Automated Vowel Extraction',
                      'googleasr': 'Completely Automated Vowel Extraction',
                      'txtalign': 'Alignment and Extraction',
                      'boundalign': 'Alignment and Extraction',
                      'extract': 'Formant Extraction',
                      'asredit': 'Alignment and Extraction on Corrected Transcripts'}

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
        body += '(2) formants.fornorm.tsv can be uploaded to the NORM online tool (http://lvc.uoregon.edu/norm/index.php) for additional normalization and plotting options\n'
        body += '(3) plot.pdf shows the F1/F2 (stressed) vowel space of your speakers\n'
        body += '(4) The .TextGrid file contains the transcription aligned with the audio\n'
        if tasktype == 'asr' or tasktype == 'googleasr' or tasktype == 'asredit' or tasktype == 'boundalign':
            body += '(5) transcription.txt contains the transcriptions.\n\n'
            body += 'If you manually correct the alignments in the TextGrid, you may re-upload your data with the new TextGrid to '
            body += filepaths['URLBASE']+'/uploadtextgrid and receive revised formant measurements and plots.\n'

            body += '\nTo use our online playback tool to edit the ASR transcriptions and then re-run alignment and extraction, go to '
            body += filepaths['URLBASE']+'/asredit?taskname={0} \n'.format(os.path.basename(taskdir))
            body += 'Note that this link is only guaranteed to work for 72 hours since we periodically delete user files.\n\n'
            body += 'Alternately, you may upload corrected plaintext transcriptions to '+filepaths['URLBASE']+'/upload/txtalign \n'

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
                                       (filename+'.TextGrid', os.path.join(taskdir, 'aligned', 'audio.TextGrid'))]
        for nicename, realfilename in filelist:
                part = MIMEBase('application', "octet-stream")
                try:
                    part.set_payload( open(realfilename,"rb").read() )
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', 'attachment; filename='+nicename)
                    message.attach(part)
                except:
                    error_check = send_error_email(receiver, filename, "Your job was not completed.", error_check) # returns false after error sends
        if tasktype == 'asr' or tasktype == 'googleasr' or tasktype == 'asredit' or tasktype == 'boundalign': #send transcription
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
        body += '\nTo help us try and identify what exactly the problem is, please message us with attached file(s) at darla.dartmouth@gmail.com.'
        body += '\nSorry about the inconvenience. We will try to identify and solve the problem shortly.'
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
