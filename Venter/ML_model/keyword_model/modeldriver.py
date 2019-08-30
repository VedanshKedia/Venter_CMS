from . import xlsxparser, keywordmodel

class KeywordSimilarityMapping:
    '''
    This class consumes the model and sequences the flow of execution for the given input
    '''
    def __init__(self, path, domain_present, domain_keyword_dict):
        self.filepath = path
        self.domain_present = domain_present
        self.domain_keyword_dict = domain_keyword_dict

    def driver(self):
        #parsing the input file for having sampled input to the model
        self.domain_keyword_dict = {k.lower(): v for k, v in self.domain_keyword_dict.items()}
        print(self.domain_keyword_dict.keys())
        domain_keys = xlsxparser.parse(self.filepath, self.domain_present, self.domain_keyword_dict.keys())

        # final_dict = final_domain_keyword_dict(domain_keys)
        temp_dict = {}
        temp_dict = dict(self.domain_keyword_dict)
        for domain in domain_keys:
            if domain not in temp_dict.keys():
                del temp_dict[domain]
        final_dict = temp_dict

        results = keywordmodel.categorizer(final_dict)
        return results


