import json
from common import *
# A list of punctuation that appears in titles
title_punctuation = ['!', '#', '&','"', "'", '(', ')', ',', '-', '.', '/', ':', '?', '_', '–']

def create_punctuationless_titles(subjects):
    for code in subjects:
        subject = subjects[code]
        new_title = subject['title']
        for punctuation in title_punctuation:
            new_title = new_title.replace(punctuation, " ")
        new_title = " ".join([i.strip() for i in new_title.split()])
        subject["punctuationless_title"] = new_title

def clean_subjects(subjects):
    for code in subjects:
        subject = subjects[code]
        # remove duplicates in prereq_for
        unique_dict = {}
        for code in subject["prereq_for"]:
            unique_dict[code] = 0
        subject["prereq_for"] = [code for code in unique_dict]

funcs = [clean_subjects, create_punctuationless_titles]
def process_everything(subjects):
    for f in funcs:
        f(subjects)

if __name__ == '__main__':
    subjects = load_subjects()
    process_everything(subjects)
    dump_subjects(subjects,"data/subjects_test")        