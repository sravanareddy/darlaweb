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

def make_format_checkbox(format):
    f = myform.MyRadio(format,[('Y', 'Yes ', 'Y'),
                        ('N', 'No ', 'N')],
                       description='Transcribe to ' + format + ' format? ')
    f.value = 'N'
    return f

def make_diarize():
    f = myform.MyRadio('diarize', [('Y', 'Yes ', 'Y'),
                        ('N', 'No ', 'N')],
                       description='Remove interviewer transcription? ',
                       post='By default, Deepgram will transcribe everything and will not identify speakers. <br>' +
                       'If \'Yes\' is selected, Deepgram will try to identify two separate speakers in the audio, and only keep'
                        + ' the interviewee (assumed to be the person who speaks more). <br> In the future, we hope to add features to transcribe and separate both speakers. <br> Deepgram charges $1.25 per audio hour for this service instead of the usual $0.75 per hour.')
    f.value = 'N'
    return f

def make_punctuate():
    f = myform.MyRadio('punctuate',
                       [('Y', 'Yes ', 'Y'),
                        ('N', 'No ', 'N')],
                       description='Include punctuation in output? ',
                       post='This includes commas, periods, and capitalizaation.')
    f.value = 'N'  # default
    return f

def make_send_to_darla():
    # need to make custom radio button that hides and shows fields based on selection
    class DarlaRadio(form.Radio):
        def get_type(self):
            return 'radio'
        def render(self):
            x = """<script type="text/javascript">
            window.onload = function() {
                document.getElementById('delstopwords').style.display = 'none';
                document.getElementById('delunstressedvowels').style.display = 'none';
                document.getElementById('filterbandwidths').style.display = 'none';
                document.getElementById('sex').style.display = 'none';
            }
            function toggleVisibility() {
                if (document.getElementById('delstopwords').style.display == 'none') {
                    document.getElementById('delstopwords').style.display = 'block';
                    document.getElementById('delunstressedvowels').style.display = 'block';
                    document.getElementById('filterbandwidths').style.display = 'block';
                    document.getElementById('sex').style.display = 'block';
                } 
                else  {
                    document.getElementById('delstopwords').style.display = 'none';
                    document.getElementById('delunstressedvowels').style.display = 'none';
                    document.getElementById('filterbandwidths').style.display = 'none';
                    document.getElementById('sex').style.display = 'none';
            }
            } </script> """
            x += '<span>'
            for arg in self.args:
                if isinstance(arg, (tuple, list)):
                    value, desc, id= arg
                else:
                    value, desc, id= arg, arg, arg
                attrs = self.attrs.copy()
                attrs['name'] = self.name
                attrs['type'] = 'radio'
                attrs['value'] = value
                attrs['id'] = id #add id
                attrs['onclick'] = 'javascript:toggleVisibility();'
                if self.value == value:
                    attrs['checked'] = 'checked'
                x += '<input %s/> %s' % (attrs, desc)
            x += '</span>'
            return x  

    f = DarlaRadio('send_to_darla',
                       [('Y', 'Yes ', 'Y'),
                        ('N', 'No ', 'N')],
                       description="Send results through DARLA's Alignment and Vowel Extraction system after? ",
                       post="This will happen after your transcription and you'll automatically be emailed the results.")
    f.value = 'N'  # default
    return f