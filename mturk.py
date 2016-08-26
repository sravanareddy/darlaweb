import json
import utilities
import web
from web import form
import myform
import os

noheadrender = web.template.render('templates/', base='simple')

req = '<span class="formrequired">*</span> '

record_post = 'Follow the instructions to record yourself reading this passage and save the file. The passage should be read twice as shown.'

sentences = ['I hope that Mary bought coffee and pizza for the crew.',
             'Susan rode a horse to the farm. The horse likes to kick my foot.',
             'This old bus can easily carry the laundry bin.',
             "I guess that Sherry didn't bother to start my car or lock my bike.",
             'My father sometimes hides his boots by the road in the park.',
             'I see that Larry took the candy heart from your palm.',
             'Steve tried to shout, "Hey! I thought you paid for the boarding passes!"',
             'Pat laughed and laughed at the sound of the shouting. The hoarse voice sounded really odd.',
             "Joe tossed five books into Mary's room - one at a time.",
             'In this hot sunny weather, I could fall down at the drop of a feather.',
             'Mom taught me to be calm, say "thank you," and shake hands.',
             'I doubt that my father actually bought a very nice card.']

recordings = [myform.MyFile('recording',
                          post=record_post,
                          description='<div class="well">{0}<br>{0} {1}</div>'.format(sentences[i], req))
              for i in range(len(sentences))]

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

    locations = [dropheader, 'rural', 'suburban', 'urban']

    info = {}
    info['gender'] = myform.MyDropdown('gender',
                        [dropheader,
                         ('M', 'Male '),
                         ('F', 'Female '),
                         ('O', 'Other ')],
                          description='What is your gender?'+req)
    info['birth'] = form.Textbox('birth',
                         form.regexp(r'\d{4}',
                                     'Please enter a valid 4-digit year.'),
                         description='In which year were you born?'+req,
                         post='Enter in YYYY (4-digit) format.')
    info['childstate'] = myform.MyDropdown('childstate',
                         nestates,
                         description='During ages 0-12, in which New England state did you spend the most time?'+req)
    info['childcity'] = form.Textbox('childcity',
                            form.notnull,
                            description='During ages 0-12, what is the name of the city/town you spent the most time in?'+req,
                            post='Please list the ONE city/town which best answers this question.')
    info['childzip'] = form.Textbox('childzip',
                         form.regexp(r'^(\d{5})?$',
                                     'Please enter a valid 5-digit US zip code or leave blank.'),
                         post='Optional; leave blank if unknown.',
                         description='During ages 0-12, what is the 5 digit zip code in which you spent the most time? ')
    info['childloc'] = myform.MyDropdown('childloc',
                         locations,
                         description='During ages 0-12, which of the following best describes your location?'+req)
    info['teenstate'] = myform.MyDropdown('teenstate',
                         nestates,
                         description='During ages 13-18, in which New England state did you spend the most time?'+req)
    info['teencity'] = form.Textbox('teencity',
                            form.notnull,
                            description='During ages 13-18, what is the name of the city/town you spent the most time in?'+req,
                            post='Please list the ONE city/town which best answers this question.')
    info['teenzip'] = form.Textbox('teenzip',
                         form.regexp(r'^(\d{5})?$',
                                     'Please enter a valid 5-digit US zip code or leave blank.'),
                         post='Optional; leave blank if unknown.',
                         description='During ages 13-18, what is the 5 digit zip code in which you spent the most time? ')
    info['teenloc'] = myform.MyDropdown('teenloc',
                         locations,
                         description='During ages 13-18, which of the following best describes your location?'+req)
    info['adultstate'] = myform.MyDropdown('adultstate',
                         states,
                         description='After age 18, in which US State (or DC) did you spend the most time?'+req)
    info['adultcity'] = form.Textbox('adultcity',
                            form.notnull,
                            description='After age 18, what is the name of the city/town you spent the most time in?'+req,
                            post='Please list the ONE city/town which best answers this question.')
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
             form.Validator('Please select the type of location where you spent most of ages 0-12.',
                                     lambda x: x.childloc!=''),
             form.Validator('Please select the type of location where you spent most of ages 13-18.',
                            lambda x: x.teenloc!=''),
             form.Validator('Please specify your ethnicity.',
                                     lambda x: x.ethnicity!=''),
             form.Validator('Please specify your highest education level.',
                        lambda x: x.education!=''),
             form.Validator('Please specify your gender',
                        lambda x: x.gender!='')
             ]

    datadir = open('filepaths.txt').readline().split()[1]

    fields = ['gender',
              'birth',
              'ethnicity',
              'childstate', 'childcity', 'childzip', 'childloc',
              'teenstate', 'teencity', 'teenzip', 'teenloc',
              'adultstate', 'adultcity', 'adultzip',
              'education', 'occupation',
              'consent']

    formfields = [info[k] for k in fields]
    formfields.append(submit)

    def GET(self):
        mturk = myform.MyForm(*self.formfields)
        mform = mturk()
        return noheadrender.mturk(mform)

    def POST(self):
        mturk = myform.MyForm(*self.formfields,
                              validators = self.valid)
        mform = mturk()
        if not mform.validates(): #not validated
            return noheadrender.mturk(mform)
        else:
            taskname, loc = utilities.store_mturk(self.datadir)

            parameters = {i.name: i.value for i in mform.inputs if i.value!=''}
            parameters['taskname'] = taskname

            with open(os.path.join(loc, 'speakerinfo.json'), 'w') as o:
                json.dump(parameters, o)

            recnum = 1
            recordform = myform.MyForm(recordings[recnum-1],
                                       form.Hidden(name='recnum', value=recnum),
                                       form.Hidden(name='taskname', value=taskname),
                                       form.Hidden(name='loc', value=loc),
                                       myform.MyButton('submit', type='submit', description='Submit'),
                                       )
            return noheadrender.mturksubmit(recordform(), recnum, len(sentences))


class mturksubmit:
    def GET(self):
        pass  #TODO: safety catch
    def POST(self):
        x = web.input(recording={}, taskname={}, loc={}, recnum = {})
        loc = x.loc
        taskname = x.taskname
        recnum = int(x.recnum)

        _, extension = utilities.get_basename(x.recording.filename)  # sanitize
        if extension not in ['.wav', '.mp3', '.m4a', '.wma']:
            recordform = myform.MyForm(recordings[recnum-1],
                                       form.Hidden(name='recnum', value=recnum),
                                       form.Hidden(name='taskname', value=taskname),
                                       form.Hidden(name='loc', value=loc),
                                       myform.MyButton('submit', type='submit', description='Submit'),
                                       )
            rform = recordform()
            recordform.note = "Please upload a .wav, .m4a, .wma, or .mp3 audio file for the first passage."
            return noheadrender.mturksubmit(rform, recnum, len(sentences))

        with open(os.path.join(loc, 'recording'+str(recnum)+extension), 'w') as o:
            o.write(x.recording.file.read())

        if recnum == len(sentences):
            return noheadrender.mturkconf(taskname)
        else:
            recnum += 1
            recordform = myform.MyForm(recordings[recnum-1],
                                       form.Hidden(name='recnum', value=recnum),
                                       form.Hidden(name='taskname', value=taskname),
                                       form.Hidden(name='loc', value=loc),
                                       myform.MyButton('submit', type='submit', description='Submit'),
                                       )
            rform = recordform()
            return noheadrender.mturksubmit(rform, recnum, len(sentences))
