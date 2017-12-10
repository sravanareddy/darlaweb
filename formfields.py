from wtforms import StringField, validators, RadioField, FileField
import utilities
from werkzeug.utils import secure_filename
import os

def make_uploadfile():
    return FileField('audio',
                     description = 'Upload a .wav or .mp3 file: ')

def make_email():
    return StringField('email',
                        validators = [validators.DataRequired(), validators.Email(message='Enter a valid e-mail address.')],
                        description = 'Your e-mail address: ')

def make_speaker():
    return StringField('name',
                       validators = [validators.DataRequired()],
                       description = 'Speaker Name or ID: '), \
           RadioField('sex',
                       choices = [('M','Male '), ('F','Female '), ('F','Child ')],
                       default = 'M',
                       description = 'Speaker Sex: ')

def make_filteropts():
    return RadioField('delstopwords',
                       choices = [('Y', 'Yes '), ('N', 'No ')],
                       default = 'Y',
                       description = 'Filter out stop-words? '), \
           RadioField('delunstressedvowels',
                      choices = [('Y', 'Yes '), ('N', 'No ')],
                      default = 'Y',
                      description = 'Filter out unstressed vowels? '), \
           RadioField('filterbandwidths',
                       choices = [('300', 'Yes '), ('10000000000', 'No ')],
                       default = '300',
                       description='Filter out vowels whose F1 or F2 bandwidths are over 300? ')

def validate_upload(f, formfield, allowed_extensions):
    if f:
        if f.filename.split('.')[-1] in allowed_extensions:
            return True
        formfield.errors.append('Only '+', '.join(allowed_extensions)+' files are allowed.')
        return False
    else:
        formfield.errors.append('A file is required.')
        return False

def process_audio_upload(f, datadir):
    filename, extension = utilities.get_basename(secure_filename(f.filename))
    taskname, audiodir, error = utilities.make_task(datadir)
    f.save(os.path.join(datadir, audiodir, filename+extension))
    samprate, total_size, chunks, error = utilities.process_audio(os.path.join(datadir, audiodir),
                                                                          filename,
                                                                          extension,
                                                                          dochunk=20)
    return taskname, filename, samprate, chunks, error
