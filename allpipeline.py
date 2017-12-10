import utilities
import os
from featrec import featurize_recognize, align_extract
from flask import render_template

def allpipeline(datadir, taskname, filename, speaker_name, speaker_sex, passwordfile, urlbase):
	try:
		utilities.write_speaker_info(os.path.join(datadir, taskname+'.speaker'),
									 speaker_name,
									 speaker_sex)
	except IOError:
		return render_template("error.html",
							   error = "Error creating a CAVE job for "+filename,
							   uploadlink = "cavejob")

	result = featurize_recognize.delay(os.path.join(datadir, taskname), passwordfile, urlbase)
	while not result.ready():
		pass

	if result.get() == False:
		return render_template("error.html",
							   error = "There is something wrong with your audio file. We could not extract acoustic features or run ASR.",
							   uploadlink = "cavejob")

	result = align_extract.delay(os.path.join(datadir, taskname), passwordfile, urlbase)
	while not result.ready():
		pass

	return render_template("success.html", message='')
