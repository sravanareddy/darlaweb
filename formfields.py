from web import form
import myform

def make_uploadsound(minduration):
    return myform.MyFile('uploadfile',
                       post='Longer recordings (of at least {0} minutes) are recommended. Your uploaded files are stored temporarily on the Dartmouth servers in order to process your job, and deleted after.'.format(minduration),
                       description='Upload a .wav or .mp3 file:')

def make_uploadtxttrans():
    return myform.MyFile('uploadtxtfile',
                                  form.notnull,
                                  post='We recommend creating this file using Notepad or TextEdit (with <a href="http://scttdvd.com/post/65242711516/how-to-get-rid-of-smart-quotes-osx-mavericks" target="_blank">smart replace turned off</a>) or emacs or any other plaintext editor. Transcripts created by "rich text" editors like Word may contain markup that will interfere with your results.',
                                  description='Manual transcription as a .txt file:')


def make_uploadboundtrans():
    return myform.MyFile('uploadboundfile',
                                    form.notnull,
                                    post = 'Textgrid should contain a tier named "sentence" with sentence/breath group intervals.',
                                    description='Manual transcription as a .TextGrid file:')

def make_uploadtgtrans():
    return myform.MyFile('uploadtgfile',
                                    form.notnull,
                                    post = 'Textgrid should contain a manually aligned or corrected phone tier as well as a word tier. The names of these tiers should include the strings "word" and "phone" as appropriate.',
                                    description='Manual alignment as a .TextGrid file:')

def make_email():
    return form.Textbox('email',
                         form.notnull,
                         form.regexp(r'^[\w.+-]+@[\w.+-]+\.[\w.+-]+$',
                                     'Please enter a valid email address.'),
                         post='We will not store or distribute your address.',
                         description='Your e-mail address:')

def make_delstopwords():
    f = myform.MyRadio('delstopwords',
                       [('Y', 'Yes ', 'Y'),
                        ('N', 'No ', 'N')],
                       description='Filter out stop-words? ',
                       post='<a href="stopwords" target="_blank">This is the list</a> of stop-words we remove. (Link opens in a new tab.)')
    f.value = 'Y'  # default
    return f

def make_delunstressedvowels():
    f = myform.MyRadio('delunstressedvowels',
                           [('Y', 'Yes ', 'Y'),
                        ('N', 'No ', 'N')],
                       description='Filter out unstressed vowels? ')
    f.value = 'Y'  # default
    return f

def make_filterbandwidths():
    f = myform.MyRadio('filterbandwidths',
                       [('300', 'Yes ', '300'),
                        ('10000000000', 'No ', '10000000000')],
                       description='Filter out vowels whose F1 or F2 bandwidths are over 300? ')
    f.value = '300'  # default
    return f

def make_audio_validator():
    return [form.Validator('Please upload an audio file.',
                                 lambda x: x.uploadfile)]

def speaker_form(taskdir, job):
    input_list = []
    taskdir = form.Hidden(name="taskdir", value=taskdir)
    job = form.Hidden(name="job", value=job)
    speaker_name = form.Textbox('name', description='Speaker ID: ')
    sex = myform.MyRadio('sex', [('M','Low ', 'M'), ('F','High ', 'F')], description='Voice type: ')
    sex.value = 'M'  # default if not checked

    speakers = myform.MyForm(taskdir,
                             job,
                             speaker_name,
                             sex)

    return speakers()
