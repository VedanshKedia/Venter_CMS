import os
from Backend.settings import BASE_DIR

class Dos2Unix:
    '''
    STRING opcode argument must be quoted | Hack
    '''
    
    def unixencode():
        '''
        This function encodes the pickles for dos across unix
        '''
        original1 =  os.path.join(BASE_DIR, "Venter/ML_model/ICMC/dataset/dataset_mcgm_clean/word_index_map_mcgm.pickle")
        destination1 =  os.path.join(BASE_DIR, "Venter/ML_model/ICMC/dataset/dataset_mcgm_clean/word_index_map_mcgm_.pickle")
        original2 =  os.path.join(BASE_DIR, "Venter/ML_model/ICMC/dataset/dataset_mcgm_clean/word_vectors_mcgm.pickle")
        destination2 =  os.path.join(BASE_DIR, "Venter/ML_model/ICMC/dataset/dataset_mcgm_clean/word_vectors_mcgm_.pickle")

        content = ''
        outsize = 0
        with open(original1, 'rb') as infile:
            content = infile.read()
        with open(destination1, 'wb') as output:
            for line in content.splitlines():
                outsize += len(line) + 1
                output.write(line + str.encode('\n'))

        with open(original2, 'rb') as infile:
            content = infile.read()
        with open(destination2, 'wb') as output:
            for line in content.splitlines():
                outsize += len(line) + 1
                output.write(line + str.encode('\n'))
