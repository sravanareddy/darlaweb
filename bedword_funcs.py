import bedword_format_conversions
import time
import sys
import json
import os
import re
import mail
import asyncio, json
import subprocess
import shlex
from hyp2mfa import boundjob_mfa

"""
NOTE: We are no longer using Microsoft Azure to transcribe, but we'll
keep the code in case we want to switch back.
"""
# # clean Azure output to linguistic-friendly format
# def clean_text(text):
#     text = re.sub(r',', '', text)
#     return text

# def transcribe_azure(api_key, service_region, language, audio_file, output_loc):
#     import azure.cognitiveservices.speech as azure_speech
#     speech_config = azure_speech.SpeechConfig(subscription=api_key, region=service_region)
#     audio_config = azure_speech.audio.AudioConfig(filename=audio_file)
#     speech_recognizer = azure_speech.SpeechRecognizer(speech_config=speech_config, language=language, audio_config=audio_config)

#     done = False
#     error = False
#     out_file = open(output_loc, 'w')

#     def error_callback():
#         nonlocal done
#         nonlocal error
#         done = True
#         error = True
#         out_file.close()

#     def stop_callback(evt: azure_speech.SessionEventArgs):
#         nonlocal done
#         nonlocal out_file
#         out_file.close()
#         done = True
    
#     def recognized_callback(evt: azure_speech.SessionEventArgs):
#         result = evt.result
#         if result.error_json:
#             error_callback()

#         nonlocal output_loc

#         text = clean_text(result.text)
#         start_time = str(result._offset / 10000000) # convert to seconds
#         end_time = str((result._offset + result._duration) / 10000000)
#         entry = ','.join([start_time, end_time, text]) + '\n'
#         out_file.write(entry)

#     # Connect callbacks to the events fired by the speech recognizer
#     speech_recognizer.recognized.connect(recognized_callback)
#     speech_recognizer.session_stopped.connect(stop_callback)

#     # Start continuous speech recognition
#     speech_recognizer.start_continuous_recognition()
#     while not done:
#         time.sleep(.5)
#     speech_recognizer.stop_continuous_recognition()
#     return not error

async def transcribe_deepgram(api_key, audio_file, punctuate, diarize, output_loc):
    try:
        from deepgram import Deepgram
        transcriber = Deepgram(api_key)
        audio = open(audio_file, 'rb')
        mimetype = 'audio/wav' if audio_file.endswith('.wav') else 'audio/mpeg'
        source = {
            'buffer': audio,
            'mimetype': mimetype
        }
        response = await asyncio.create_task(
                transcriber.transcription.prerecorded(
                    source,
                    {
                        'punctuate': True,
                        'utterances': True,
                        'diarize': diarize
                    }
            ))
        utterances = response['results']['utterances']

        # if we are diarizing, we will find the ID of the interviewee and only keep their utterances
        # we are assuming that the person who speaks the most is the interviewee
        if diarize:
            speaker_durations = {} # key is speaker ID
            speaker_utterances = {}
            for utterance in utterances:
                id = utterance['speaker']
                if id in speaker_durations:
                    speaker_durations[id] += utterance['end'] - utterance['start']
                    speaker_utterances[id].append(utterance)
                else:
                    speaker_durations[id] = utterance['end'] - utterance['start']
                    speaker_utterances[id] = [utterance]
            
            interviewee_id = max(speaker_durations, key=speaker_durations.get)
            # only keep utterances made by interviewee
            utterances = speaker_utterances[interviewee_id]
                
        # write to csv_output now
        out_file = open(output_loc, 'w')
        for utterance in utterances:
            start, end = utterance['start'], utterance['end']
            words = []
            for word in utterance['words']:
                words.append(word['punctuated_word'] if punctuate else word['word'])
            # for CSV compatability, wrap text in quotation marks
            text = ' '.join(words)
            text.replace('"', "'")
            text = '"' + text + '"'
            csv_line = ','.join([str(start), str(end), text]) + '\n'
            out_file.write(csv_line)
        return True
    except Exception as e:
        print(e)
        return False

async def main():
    taskdir = sys.argv[1]
    api_key = sys.argv[2]

    # now retrieve arguments from arg file
    bedword_args = json.load(open(os.path.join(taskdir, 'bedword_args.json')))
    email = bedword_args['email']
    filename = bedword_args['filename']
    extension = bedword_args['extension']
    audio_length = bedword_args['audio_length']
    diarize = bedword_args['diarize']
    punctuate = bedword_args['punctuate']
    output_formats = bedword_args['output_formats']
    send_to_darla = bedword_args['send_to_darla']

    audio_file = os.path.join(taskdir, filename + extension)
    csv_transcription = os.path.join(taskdir, 'bedword_transcription.csv')
    try:
        success = await transcribe_deepgram(api_key, audio_file, punctuate, diarize, csv_transcription)
        if success:
            formats_dir = os.path.join(taskdir, 'output_formats')
            os.system('mkdir -p ' + formats_dir)
            os.system('chmod g+w '+ formats_dir)
            bedword_format_conversions.convert(csv_transcription, output_formats, formats_dir, filename, audio_length, extension)
            mail.send_bedword_email(email, filename, taskdir, output_formats, punctuate, diarize, send_to_darla)
            if send_to_darla:
                bedword_format_conversions.convert(csv_transcription, ['.TextGrid'], taskdir, filename, audio_length, extension, for_darla=True)
                boundjob_mfa(taskdir, clean_text=False)
                # mostly copying the functionality of backend.align_extract
                alext_args = json.load(open(os.path.join(taskdir, 'alext_args.json')))
                args = ' '.join(["./align_and_extract.sh",
                        taskdir,
                        alext_args['tasktype'],
                        alext_args['delstopwords'],
                        alext_args['maxbandwidth'],
                        alext_args['delunstressedvowels']])
                align = subprocess.Popen(shlex.split(args), stderr=subprocess.STDOUT)
                retval = align.wait()
                if retval != 0:
                    mail.send_error_email(alext_args['email'], alext_args['filename'], "Alignment and extraction process failed.", True)
                else:
                    mail.send_email(alext_args['tasktype'], alext_args['email'], alext_args['filename'], taskdir, True)
    except Exception as e:
            print(e)
            mail.send_error_email(email, filename, "Bed Word Automatic Transcription process failed.", True)

if __name__ == "__main__":
    asyncio.run(main())