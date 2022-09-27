import os
import re
import datetime

# this file converts an audio transcription to a given output format.
# the assumed input is always a CSV, where each line is the tuple:
#  (start time of phrase, end time of phrase, text of phrase)

def convert(csv_input, formats, out_loc, filename, audio_length, file_extension, for_darla=False):
    intervals = []
    for line in open(csv_input).readlines():
        comma_splits = line.split(',')
        # we need to account for if the text itself has a comma
        start = comma_splits[0]
        end = comma_splits[1]
        text = ''.join(comma_splits[2:])
        text = text.replace('\n', '').replace('"', '').replace('-', ' ')
        if for_darla:
            text = re.sub(r"[^A-Za-z' ]+", '', text).lower()
        intervals.append((float(start), float(end), text))
    if '.TextGrid' in formats:
        to_textgrid(intervals, out_loc, filename, audio_length, for_darla=for_darla)
    if '.eaf' in formats:
        to_eaf(intervals, out_loc, filename, file_extension)
    if '.txt' in formats:
        to_txt(intervals, out_loc, filename)
    if '.csv' in formats:
        to_csv(intervals, out_loc, filename)

def to_textgrid(intervals, out_loc, filename, audio_length, for_darla=False):
    interval_buffer = 0.2
    intervals = add_interval_breaks(intervals, interval_buffer, audio_length, True)
    if not for_darla:
        out_file = os.path.join(out_loc, filename + '.TextGrid')
    else:
        out_file = os.path.join(out_loc, 'raw.TextGrid')
    with open(out_file, 'w') as o:
        # add header information
        o.write(f"""File type = "ooTextFile"
Object class = "TextGrid"

xmin = 0
xmax = {audio_length}
tiers? <exists>
size = 1
item []:
    item [1]:
        class = "IntervalTier"
        name = "sentence"
        xmin = 0
        xmax = {audio_length}
        intervals: size = {len(intervals)}\n""")
        for i, interval in enumerate(intervals):
            start, end, text = interval
            o.write(f"""        intervals[{i + 1}]:
            xmin = {start}
            xmax = {end}
            text = "{text}"\n""")

def to_txt(intervals, out_loc, filename):
    with open(os.path.join(out_loc, filename + '.txt'), 'w') as o:
        for interval in intervals:
            start, end, text = interval
            o.write(text + '\n')

def to_eaf(intervals, out_loc, filename, file_extension):
    interval_buffer = 0.2
    intervals = add_interval_breaks(intervals, interval_buffer, None, False)
    date = datetime.date.today().isoformat()
    out_file = os.path.join(out_loc, filename + '.eaf')
    with open(out_file, 'w') as o:
        # add header information
        o.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<ANNOTATION_DOCUMENT AUTHOR="" DATE="{date}"
    FORMAT="3.0" VERSION="3.0"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://www.mpi.nl/tools/elan/EAFv3.0.xsd">
    <HEADER MEDIA_FILE="" TIME_UNITS="milliseconds">
        <MEDIA_DESCRIPTOR MEDIA_URL="{filename + file_extension}" />
        <PROPERTY NAME="URN">urn:nl-mpi-tools-elan-eaf:f1c984f0-9484-44ee-9e94-4d61c5d25a11</PROPERTY>
        <PROPERTY NAME="lastUsedAnnotationId">{len(intervals)}</PROPERTY>
    </HEADER>\n""")
        time_orders = []
        tier = []
        # time order and tier headers
        time_orders.append('    <TIME_ORDER>\n')
        tier.append('    <TIER LINGUISTIC_TYPE_REF="default-lt" TIER_ID="default">\n')
        # iterate through all the intervals
        for i, interval in enumerate(intervals):
            start, end, text = interval
            # convert to milliseconds
            start = str(int(start) * 1000)
            end = str(int(end) * 1000)
            first_index, second_index = str(2 * i + 1), str(2 * i + 2)
            time_orders.append(f'        <TIME_SLOT TIME_SLOT_ID="ts{first_index}" TIME_VALUE="{start}"/>\n')
            time_orders.append(f'        <TIME_SLOT TIME_SLOT_ID="ts{second_index}" TIME_VALUE="{end}"/>\n')
            tier.append(f"""        <ANNOTATION>
            <ALIGNABLE_ANNOTATION ANNOTATION_ID="a{i + 1}"
                TIME_SLOT_REF1="ts{first_index}" TIME_SLOT_REF2="ts{second_index}">
                <ANNOTATION_VALUE>{text}</ANNOTATION_VALUE>
            </ALIGNABLE_ANNOTATION>
        </ANNOTATION>\n""")
        # time order and tier footers
        time_orders.append('    </TIME_ORDER>\n')
        tier.append('    </TIER>\n')
        # write to file
        for text in time_orders:
            o.write(text)
        for text in tier:
            o.write(text)
        # add footer information
        o.write("""    <LINGUISTIC_TYPE GRAPHIC_REFERENCES="false"
        LINGUISTIC_TYPE_ID="default-lt" TIME_ALIGNABLE="true"/>
    <CONSTRAINT
        DESCRIPTION="Time subdivision of parent annotation's time interval, no time gaps allowed within this interval" STEREOTYPE="Time_Subdivision"/>
    <CONSTRAINT
        DESCRIPTION="Symbolic subdivision of a parent annotation. Annotations refering to the same parent are ordered" STEREOTYPE="Symbolic_Subdivision"/>
    <CONSTRAINT DESCRIPTION="1-1 association with a parent annotation" STEREOTYPE="Symbolic_Association"/>
    <CONSTRAINT
        DESCRIPTION="Time alignable annotations within the parent annotation's time interval, gaps are allowed" STEREOTYPE="Included_In"/>
</ANNOTATION_DOCUMENT>""")

def to_csv(intervals, out_loc, filename):
    with open(os.path.join(out_loc, filename + '.csv'), 'w') as o:
        for interval in intervals:
            start, end, text = interval
            o.write(','.join([str(start), str(end), text]) + '\n')

# add_interval_breaks is the preprocessing function for TextGrid and eaf file conversions
# since the Azure transcriptions begin their phrase time immediately as words are spoken,
# most of the time we want to "buffer" the start time of the phrase, basically move back
# the start time of the phrase by a fraction of a second so that there is some silence before
# the speaker starts talking.
def add_interval_breaks(intervals, buffer, audio_length, fill_empty_intervals):
    # remove all empty intervals
    intervals = list(filter(lambda interval: interval[2] != '', intervals))

    # try to shift each interval back by buffer
    intervals[0] = (max(0, intervals[0][0] - buffer), intervals[0][1], intervals[0][2])
    for i in range(1, len(intervals)):
        curr_start, curr_end, curr_text = intervals[i]
        prev_start, prev_end, prev_text = intervals[i - 1]
        if curr_start - prev_end > buffer * 2:
            curr_start -= buffer
        elif curr_start - prev_end > buffer:
            # we also don't want to leave a silence of length less than buffer,
            # so we will push prev_end forward
            curr_start -= buffer
            prev_end = curr_start
        else:
            # split the difference if there is not enough room for buffer
            curr_start = (curr_start + prev_end) / 2
            prev_end = curr_start
        intervals[i] = (curr_start, curr_end, curr_text)
        intervals[i - 1] = (prev_start, prev_end, prev_text)

    max_interval_length = 15
    combine_interval_length = 0.5
    # if two intervals are close to each other, we will combine them
    new_intervals = []
    for i in range(len(intervals) - 1):
        if intervals[i + 1][0] - intervals[i][1] < combine_interval_length \
                and intervals[i + 1][1] - intervals[i][0] < max_interval_length:
            intervals[i + 1] = (intervals[i][0], intervals[i + 1][1], intervals[i][2] + ' ' + intervals[i + 1][2])
        else:
            new_intervals.append(intervals[i])
    new_intervals.append(intervals[-1])

    intervals = new_intervals

    # fill empty intervals back in
    if fill_empty_intervals:
        new_intervals = []
        # add first interval
        if intervals[0][0] > 0:
            new_intervals.append((0, intervals[0][0], ''))
        # add middle intervals
        for curr_interval, next_interval in zip(intervals[0:-1], intervals[1:]):
            new_intervals.append(curr_interval)
            if curr_interval[1] != next_interval[0]:
                new_intervals.append((curr_interval[1], next_interval[0], ''))
        # add last interval and its gap
        new_intervals.append(intervals[-1])
        if intervals[-1][1] != audio_length:
            new_intervals.append((intervals[-1][1], audio_length, ''))
        intervals = new_intervals
    
    return intervals