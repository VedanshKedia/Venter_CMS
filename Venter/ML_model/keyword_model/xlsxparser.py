# -*- coding: utf-8 -*-
"""
Created on Tue June 25 2019

@author: Anushri Arora
"""

import os
import re

import numpy as np
import pandas as pd
from nltk.tokenize import sent_tokenize, word_tokenize

from Backend.settings import BASE_DIR


def parse(filepath, domain_present, domain_keyword_dict_keys):
    '''
    This function parses the fed xlsx file and saves them separately,
    segregating the categories
    Args(1) - xlsx filepath
    '''
    final_domain_names = []

    if domain_present:
        xls = pd.ExcelFile(filepath)
        df = pd.read_excel(xls, 'Form responses 1', header=[0, 1])

        headers = df.keys()[1:]
        headers = headers[:len(headers)-3]
        
        for h in headers[1::2]:
            filename = str(h).split(',')[0].split('\'')[1] + '.txt'
            domain_name = filename[:-4]
            domain_name = domain_name.lower()
            
            if domain_name in domain_keyword_dict_keys:
                file = open(os.path.join(BASE_DIR, 'Venter/ML_model/keyword_model/data/keyword data/') + filename, 'w', encoding='utf-8')
                index = 1
                print("Parsing " + filename + '...')
                for sentence in df[h]:
                    if type(sentence) == str:
                        file.write(str(index) + '- ' + sentence.lstrip().replace('\n', ' ') + '\n')
                        index += 1
                final_domain_names.append(domain_name)
    else:
        domain_keyword_dict_keys = list(domain_keyword_dict_keys)
        domain_name=domain_keyword_dict_keys[0]
        final_domain_names.append(domain_name)

        raw_data = pd.read_excel(filepath, skiprows=1)
        response = raw_data['Feedback']
        response=response.dropna()
        tokenized_text=[]
        for item in response:
            tokenized_text+=sent_tokenize(item)
        name = domain_name+'.txt'
        path = 'Venter/ML_model/keyword_model/data/keyword data/'+name
        file1 = open(path,'w')
        for sent in tokenized_text:
            file1.write(sent)
            file1.write('\n')
        file1.close()

    return final_domain_names
