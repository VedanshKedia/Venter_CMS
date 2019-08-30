
# # """
# # Created on Mon Jun 10 17:15:22 2019

# # @author: Anushri Arora
# # """

import json
import os
import time

import numpy as np
from gensim.models import KeyedVectors
from nltk.corpus import stopwords

from Backend.settings import BASE_DIR


def similarityIndex(s1, s2, wordmodel):
    
    #To compare the two sentences for their similarity using the gensim wordmodel 
    #and return a similarity index
    
    if s1 == s2:
        return 1.0

    s1words = s1.split()
    s2words = s2.split()

    s1words = set(s1words)
    for word in s1words.copy():
        if word in stopwords.words('english'):
            s1words.remove(word)
    
    s2words = set(s2words)
    for word in s2words.copy():
        if word in stopwords.words('english'):
            s2words.remove(word)

    s1words = list(s1words)
    s2words = list(s2words)

    s1set = set(s1words)
    s2set = set(s2words)

    vocab = wordmodel.vocab
    
    if len(s1set & s2set) == 0:
        return 0.0
    for word in s1set.copy():
        if (word not in vocab):
            s1words.remove(word)
    for word in s2set.copy():
        if (word not in vocab):
            s2words.remove(word)
    
    return wordmodel.n_similarity(s1words, s2words)


def wmd_similarity(single_comment, single_keyword, wordmodel):
    
    cwords = single_comment.split()
    cwords = set(cwords)
    for word in cwords.copy():
        if word in stopwords.words('english'):
            cwords.remove(word)
        
    cwords = list(cwords)

    swords = single_keyword.split()
    swords = set(swords)
    for word in swords.copy():
        if word in stopwords.words('english'):
            swords.remove(word)

    swords = list(swords)
    
    return wordmodel.wmdistance(cwords, swords)

def categorizer(keywords):
    
    #driver function,
    #returns model output mapped on the input corpora as a dict object
    
    stats = open('stats.txt', 'w', encoding='utf-8')

    st = time.time()
    
    wordmodelfile = os.path.join(BASE_DIR, 'Venter/ML_model/sentence_model/MAX.bin')
    wordmodel = KeyedVectors.load_word2vec_format(wordmodelfile, binary = True, limit=200000)
    wordmodel.init_sims(replace=True)
    et = time.time()
    s = 'Word embedding loaded in %f secs.' % (et-st)
    print(s)
    stats.write(s + '\n')

    responsePath = os.path.join(BASE_DIR, 'Venter/ML_model/keyword_model/data/keyword data/')
    responseDomains = os.listdir(responsePath)
    #responseDomains.sort()
    
    #dictionary for populating the json output
    results = {}
    for responseDomain in zip(responseDomains):
        #instantiating the key for the domain
        responseDomain =str(responseDomain)
        domain =responseDomain[2:-7]
        domain =domain.lower()
        responseDomain =responseDomain[2:-3]
        results[domain] = {}

        print('Categorizing %s domain...' % domain)

        responses = open(os.path.join(responsePath, responseDomain), 'r', encoding='unicode-escape').readlines()
        rows=0
        for response in responses:
            num=0
            if response=='\n':
                num+=1
            rows+=(len(response)-num)
            
        categories=keywords[domain]
        columns = len(categories)

        #categories = category
        #saving the scores in a similarity matrix
        #initializing the matrix with -1 to catch dump/false entries
        st = time.time()
        similarity_matrix = [[-1 for c in range(columns)] for r in range(rows)]
        et = time.time()
        s = 'Similarity matrix initialized in %f secs.' % (et-st)
        print(s)
        stats.write(s + '\n')

        row = 0
        st = time.time()
        for response in responses:
            if response=='\n':
                    continue
            else:
                column = 0
                for category in categories:
                    similarity_matrix[row][column] = wmd_similarity(response, category, wordmodel)
                    column += 1
            row += 1
        et = time.time()
        s = 'Similarity matrix populated in %f secs. ' % (et-st)
        print(s)
        stats.write(s + '\n')

        print('Initializing json output...')
        for catName in categories:
            results[domain][catName] = []

        print('Populating category files...')
        
        for score_row, response in zip(similarity_matrix, responses):
            if response!='\n':
                min_sim_index=len(categories)-1
                min_sim_index = np.array(score_row).argmin()
                temp = {}
                temp['response'] = response
                temp_score = np.array(score_row).min()
                if temp_score==np.float64(np.inf):
                    temp_score=10.0
                temp['score'] = temp_score
                results[domain][categories[min_sim_index]].append(temp)
        print('Completed.\n')
        

        #sorting domain wise categorised responses based on scores
        for domain in results:
            for category in results[domain]:                                                                                                                                 
                temp = results[domain][category]
                if len(temp)==0 or category=='Novel':
                    continue
                results[domain][category] = sorted(temp, key=lambda k: k['score'], reverse=False)
    return results
