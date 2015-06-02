#!/bin/bash

taskname=$1

scriptdir='/home/sravana/webpy_sandbox'
favedir='/home/sravana/applications/FAVE/FAVE-extract'

#zip for email compatibility
zip -j $taskname.alignments.zip $taskname.mergedtg/*.TextGrid

#run FAVE-extract
mkdir -p $taskname.vowels
for filename in $(ls $taskname.mergedtg); do
    filename=${filename%.*};
    python $favedir/bin/extractFormants.py \
 --means=$favedir/means.txt\
 --covariances=$favedir/covs.txt\
 --phoneset=$favedir/cmu_phoneset.txt\
 --speaker=$taskname.speakers/converted_$filename.speaker\
 $taskname.wav/converted_$filename.wav $taskname.mergedtg/$filename.TextGrid $taskname.vowels/$filename &> $taskname.errors;
done

#aggregate all the vowel files together
cat $taskname.vowels/*_formants.csv > $taskname.aggvowels_formants.csv
head -n1 $taskname.aggvowels_formants.csv > $taskname.aggvowels_formants.header
grep -v "name,sex" $taskname.aggvowels_formants.csv > $taskname.aggvowels_formants.body
cat $taskname.aggvowels_formants.header $taskname.aggvowels_formants.body > $taskname.aggvowels_formants.csv
rm $taskname.aggvowels_formants.header $taskname.aggvowels_formants.body

Rscript $scriptdir/plot_vowels.r $taskname.aggvowels_formants.csv $taskname.fornorm.tsv $taskname.plot.pdf
