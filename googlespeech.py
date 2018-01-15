"""
class googlespeech:
    speaker_name = form.Textbox('name', description='Speaker ID: ')
    sex = myform.MyRadio('sex', [('M','Male ', 'M'), ('F','Female ', 'F'), ('F','Child ', 'C')], description='Speaker Sex: ')
    sex.value = 'M'  # default if not checked
    filepaths = utilities.read_filepaths()
    appdir = '.'
    datadir = filepaths['DATA']

    uploadfile = make_uploadfile()
    delstopwords = make_delstopwords()
    delunstressedvowels = make_delunstressedvowels()
    filterbandwidths = make_filterbandwidths()
    email = make_email()
    taskname = form.Hidden('taskname')
    submit = form.Button('submit', type='submit', description='Submit')

    soundvalid = [form.Validator('Please upload a sound file.',
                                 lambda x:x.uploadfile)]

    def GET(self):

        googlespeech = myform.MyForm(self.uploadfile,
                                     self.delstopwords,
                                     self.delunstressedvowels,
                                     self.filterbandwidths,
                                     self.email,
                                     self.taskname,
                                     self.speaker_name,
                                     self.sex,
                                     self.submit)
        form = googlespeech()
        return render.googlespeech(form)

    def POST(self):
        googlespeech = myform.MyForm(self.uploadfile,
                                     self.delstopwords,
                                     self.delunstressedvowels,
                                     self.filterbandwidths,
                                     self.email,
                                     self.taskname,
                                     self.sex,
                                     self.speaker_name,
                                     self.submit)
        form = googlespeech()
        x = web.input(uploadfile={})

        #sanitize filename
        filename, extension = utilities.get_basename(x.uploadfile.filename)
        if extension not in ['.wav', '.mp3']:
            form.note = "Please upload a .wav or .mp3 file."
            return render.speakersyt(form)
        else:
            gstorage = get_storage_service(self.filepaths['GOOGLESPEECH'])
            service = get_speech_service(self.filepaths['GOOGLESPEECH'])
            taskname, audiodir, error = utilities.make_task(self.datadir)
            filename, extension = utilities.get_basename(x.uploadfile.filename)

            utilities.write_speaker_info(os.path.join(self.datadir, taskname+'.speaker'), x.name, x.sex)

            utilities.send_init_email('googleasr', x.email, filename)
            # upload entire file onto google cloud storage
            samprate, total_size, chunks, error = utilities.process_audio(audiodir,
                                                                  filename,
                                                                  extension,
                                                                  x.uploadfile.file.read(),
                                                                  dochunk=None)
            result = gcloudupload.delay(gstorage,
                                            audiodir,
                                            filename,
                                            taskname,
                                            x.email)
            while not result.ready():
                pass

            # uncomment to test throttle by sending 4 speech reqs
            # for i in range(4):
            result = asyncrec.delay(service,
                                       self.datadir,
                                       taskname,
                                       audiodir,
                                       filename,
                                       samprate,
                                       x.email)
            while not result.ready():
                pass

            #TODO: why do we need datadir, audiodir, etc? Reduce redundancy in these filenames

            utilities.gen_argfiles(self.datadir, taskname, filename, 'googleasr', x.email, samprate, x.delstopwords, x.filterbandwidths, x.delunstressedvowels)

            result = align_extract.delay(os.path.join(self.datadir, taskname), self.appdir)
            while not result.ready():
                pass

            return render.success("You may now close this window. We will email you the results.")
"""
