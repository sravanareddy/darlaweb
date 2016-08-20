import json
import utilities
import web
from web import form
import myform
import os

noheadrender = web.template.render('templates/', base='simple')

taskname = None
loc = None

req = '<span class="formrequired">*</span> '

record_post = 'Follow the instructions to record yourself reading this passage and save the file.'

passage1 = "I hope that Mary bought coffee and pizza for the whole company. The horse likes to kick the football. The horse can easily carry the laundry bin around the farm. I guess that Sherry didn't bother to start the car or lock the door."
passage2 = "My father sometimes hides his hiking boots in a hole in the park. I see that Larry took the candy heart from your palm. Steve shouted, 'Hey! I thought you paid for the boarding passes!' Pat just laughed at the sound of the shouting."
passage3 = "Joe tossed the books into Mary's room. In this hot weather, I could fall down at the drop of a feather. I taught you to say 'thank you' and shake hands. I found out that my father actually bought a very nice card."

recording1 = myform.MyFile('recording1',
                          post=record_post,
                          description='<div class="well">{0}{1}</div>'.format(passage1, req))
recording2 = myform.MyFile('recording2',
                          post=record_post,
                          description='<div class="well">{0}{1}</div>'.format(passage2, req))
recording3 = myform.MyFile('recording3',
                          post=record_post,
                          description='<div class="well">{0}{1}</div>'.format(passage3, req))

class mturk:
    dropheader = ('', 'drop down to select')
    states = json.load(open('us_states.json'))

    ne = set(['CT', 'ME', 'MA', 'NH', 'RI', 'VT'])
    nestates = [(abbrev, full) for (abbrev, full) in states if abbrev in ne]
    nestates.insert(0, dropheader)
    nestates.append(('NotNE', 'Not in New England'))

    states.insert(0, dropheader)
    states.append(('NotUS', 'Not in the US'))

    ethnicity_data = json.load(open('ethnicity.json'))
    ethnicity_data.insert(0, dropheader)

    education_data = json.load(open('education.json'))
    education_data.insert(0, dropheader)

    info = {}
    info['gender'] = myform.MyDropdown('gender',
                        [dropheader,
                         ('M', 'Male '),
                         ('F', 'Female '),
                         ('O', 'Other ')],
                          description='What is your gender?'+req)
    info['childstate'] = myform.MyDropdown('childstate',
                         nestates,
                         description='During ages 0-12, in which New England State did you spend the most time?'+req)
    info['childcity'] = form.Textbox('childcity',
                            form.notnull,
                            description='During ages 0-12, what is the name of the city/town you spent the most time in?'+req)
    info['childzip'] = form.Textbox('childzip',
                         form.regexp(r'^(\d{5})?$',
                                     'Please enter a valid 5-digit US zip code or leave blank.'),
                         post='Optional; leave blank if unknown.',
                         description='During ages 0-12, what is the 5 digit zip code in which you spent the most time? ')
    info['teenstate'] = myform.MyDropdown('teenstate',
                         nestates,
                         description='During ages 13-18, in which New England State did you spend the most time?'+req)
    info['teencity'] = form.Textbox('teencity',
                            form.notnull,
                            description='During ages 13-18, what is the name of the city/town you spent the most time in?'+req)
    info['teenzip'] = form.Textbox('teenzip',
                         form.regexp(r'^(\d{5})?$',
                                     'Please enter a valid 5-digit US zip code or leave blank.'),
                         post='Optional; leave blank if unknown.',
                         description='During ages 13-18, what is the 5 digit zip code in which you spent the most time? ')
    info['adultstate'] = myform.MyDropdown('adultstate',
                         states,
                         description='After age 18, in which US State (or DC) did you spend the most time?'+req)
    info['adultcity'] = form.Textbox('adultcity',
                            form.notnull,
                            description='After age 18, what is the name of the city/town you spent the most time in?'+req)
    info['adultzip'] = form.Textbox('adultzip',
                         form.regexp(r'^(\d{5})?$',
                                     'Please enter a valid 5-digit US zip code or leave blank.'),
                         post='Leave blank if unknown.',
                         description='After age 18, what is the 5 digit zip code in which you spent the most time? ')
    info['ethnicity'] = myform.MyDropdown('ethnicity',
                         ethnicity_data,
                         description='Which of the following US Census categories best represents your ethnicity?'+req)
    info['education'] = myform.MyDropdown('education',
                       education_data,
                       description='Which of the following best describes your highest achieved education level?'+req)
    info['occupation'] = form.Textbox('occupation',
                         form.notnull,
                         description='Please enter your occupation. If currently unemployed, please enter your most recent occupation.'+req,
                         post='If you are a student, enter the occupation of the primary income source in your household when growing up.')
    info['consent'] = form.Radio('consent',
                         [('Yes', 'Yes, you may provide my recordings to the public, such as media releases or online samples.\n'),
                          ('No', 'No, you may not release my recordings.')],
                         description='<b>Consent for data release:</b> This is a research study about how people talk in this region, and includes survey information and brief audio recordings of your voice. No personally identifiable information about the recordings or surveys will ever be used in this study or released to the public. But since people are often interested in dialects, we may want to provide recordings for the general public, such as media releases or online dialect samples. You have the option to give us permission or to decline. Your choice will not affect your ability to participate in the survey activities.'+req+'<br>')
    submit = myform.MyButton('submit', type='submit', description='Submit')

    valid = [form.Validator('Please select the state where you spent most of ages 0-12.',
                                     lambda x: x.childstate!=''),
             form.Validator('Please select the state where you spent most of ages 13-18.',
                                     lambda x: x.teenstate!=''),
             form.Validator('Please select the state where you spent most of your adulthood after 18.',
                                     lambda x: x.adultstate!=''),
             form.Validator('Please specify your ethnicity.',
                                     lambda x: x.ethnicity!=''),
             form.Validator('Please specify your highest education level.',
                        lambda x: x.education!=''),
             form.Validator('Please specify your gender',
                        lambda x: x.gender!='')
             ]

    datadir = open('filepaths.txt').readline().split()[1]

    fields = ['gender',
              'ethnicity',
              'childstate', 'childcity', 'childzip',
              'teenstate', 'teencity', 'teenzip',
              'adultstate', 'adultcity', 'adultzip',
              'education', 'occupation',
              'consent']

    formfields = [info[k] for k in fields]
    formfields.append(submit)

    def GET(self):
        mturk = myform.MyForm(*self.formfields)
        form = mturk()
        return noheadrender.mturk(form)

    def POST(self):
        mturk = myform.MyForm(*self.formfields,
                              validators = self.valid)
        form = mturk()
        if not form.validates(): #not validated
            return noheadrender.mturk(form)
        else:
            taskname, loc = utilities.store_mturk(self.datadir)

            parameters = {i.name: i.value for i in form.inputs if i.value!=''}
            parameters['taskname'] = taskname

            with open(os.path.join(loc, 'speakerinfo.json'), 'w') as o:
                json.dump(parameters, o)

            recordform = myform.MyForm(recording1, recording2, recording3,
                                       myform.MyButton('submit', type='submit', description='Submit'),
                                       )
            return noheadrender.mturksubmit(recordform())


class mturksubmit:
    def GET(self):
        pass  #TODO: safety catch
    def POST(self):
        recordform = myform.MyForm(recording1, recording2, recording3,
                                   myform.MyButton('submit', type='submit', description='Submit'),
                                   )
        x = web.input(recording1={}, recording2={}, recording3={})

        #TODO: clean up this copy-pasta
        """
        if not x.recording1:
            recordform.note = "Please upload a .wav or .mp3 audio file for the first passage."
            return noheadrender.mturksubmit(recordform())
        if not x.recording2:
            recordform.note = "Please upload a .wav or .mp3 audio file for the second passage."
            return noheadrender.mturksubmit(recordform())
        if not x.recording3:
            recordform.note = "Please upload a .wav or .mp3 audio file for the third passage."
            return noheadrender.mturksubmit(recordform())
        """

        print x.recording1
        _, extension1 = utilities.get_basename(x.recording1.filename)  # sanitize
        if extension1 not in ['.wav', '.mp3']:
            recordform.note = "Please upload a .wav or .mp3 audio file for the first passage."
            return noheadrender.mturksubmit(recordform())
        _, extension2 = utilities.get_basename(x.recording2.filename)  # sanitize
        if extension2 not in ['.wav', '.mp3']:
            recordform.note = "Please upload a .wav or .mp3 audio file for the second passage."
            return noheadrender.mturksubmit(recordform())
        _, extension3 = utilities.get_basename(x.recording3.filename)  # sanitize
        if extension3 not in ['.wav', '.mp3']:
            recordform.note = "Please upload a .wav or .mp3 audio file for the third passage."
            return noheadrender.mturksubmit(recordform())

        with open(os.path.join(loc, 'recording1'+extension1), 'w') as o:
            o.write(x.recording1.file.read())
        with open(os.path.join(loc, 'recording2'+extension2), 'w') as o:
            o.write(x.recording2.file.read())
        with open(os.path.join(loc, 'recording3'+extension3), 'w') as o:
            o.write(x.recording3.file.read())

        return noheadrender.success('Thank you. Please enter this code in the Mechanical Turk site in order to confirm that you completed this task so that you can be compensated.<br><br><h3>{0}</h3>'.format(self.taskname))
