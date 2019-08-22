"""
Author: Meet Shah, Shivam Sharma
After validating post request, control will transfer to this class to read uploaded csv and append category column in it.
This code assumes that column number 4{ column 0 being base column} is always going to be complaint title.

source :  Read only headers from csv file
            => https://stackoverflow.com/questions/24962908/how-can-i-read-only-the-header-column-of-a-csv-file-using-python

Structure of Dict_List which will be sent to the frontend:

            dict_list = [
                dict = {
                    'index' = index1,
                    'problem_description' = complaint_description1,
                    'category': {
                        'category1': 80,
                        'category2': 10,
                        'category3': 10
                    }
                },
                dict = {
                    'index' = index2,
                    'problem_description' = complaint_description2,
                    'category': {
                        'category1': 80,
                        'category2': 10,
                        'category3': 10
                    }
                },
                .
                .
                .
            ]
"""

import operator
import os

import pandas as pd
from django.conf import settings

from Venter.ML_model.model.ClassificationService import ClassificationService
from Venter.ML_model.SpeakUp.Model.SpeakupClassificationService import \
    ClassificationService_speakup


class EditCsv:
    filename = ''
    username = ''
    group = ''

    def __init__(self, file_name, user_name, company):
        self.filename = file_name
        self.username = user_name
        self.group = company

    def check_csvfile_header(self):
        """
        This check is important because of two reasons:

        1. We are assuming that the 4th column (0 being the base) will always be complaint_title which will be sent to the model.

        2. To get the category list which will be used during auto completion in the frontend HTML.
        """
        path = os.path.join(settings.MEDIA_ROOT, self.username, "CSV", "input", self.filename)
        try:
            csv_file = pd.read_csv(path, nrows=1, encoding="utf-8").columns
        except Exception as e:
            print("Error in checking header")
            print(e)
        company_columns = []
        category_list = []
        if self.group == "ICMC":
            try:
                # Here we need to check whether an object of ClassificationService is already been created or not.
                # So we are creating the object of ClassificationService class each time when we upload the file.
                # This object can have the reference for ICMC model class or SpeakUp model class depending upon the group of the user.
                # To reduce the redundancy of the objects we are checking whether it has the attribute 'get_top_3_cats_with_prob' which is the function used to call the model.
                if not hasattr(self.cs, 'get_top_3_cats_with_prob'):
                    self.cs = ClassificationService()
                    # if the object is already been created, do nothing
            except Exception as e:
                print(e)
                self.cs = ClassificationService()
            company_columns = settings.ICMC_HEADERS
            category_list = settings.ICMC_CATEGORY_LIST

        elif self.group == "SpeakUP":
            try:
                if not hasattr(self.cs, 'get_top_3_cats_with_prob'):
                    self.cs = ClassificationService_speakup()

            except Exception as e:
                print(e)
                self.cs = ClassificationService_speakup()
            company_columns = settings.SPEAKUP_HEADERS
            category_list = settings.SPEAKUP_CATEGORY_LIST

        if len(csv_file) == len(company_columns):
            # Checking the Headers of the csv file whether they are in order or not
            for i in range(len(company_columns)):
                if company_columns[i].strip() == csv_file[i].strip():
                    # If the headers match, return True as header_flag and category_list as the list
                    continue
                else:
                    # If the headers doesn't match, raise an error message
                    return False, []
            return True, category_list
        else:
            # If the header's count doesn't matches with the csv one, raise an error message
            return False, []

    def delete(self):
        # After Downloading, Delete the uploaded file from the input folder
        PATH = os.path.join(settings.MEDIA_ROOT, self.username, "CSV", "input", self.filename)
        os.remove(PATH)

    def write_file(self, correct_category):
        # This function will write the input file into output csvfile and append the predicted categories from the user
        csvfile = pd.read_csv(os.path.join(settings.MEDIA_ROOT, self.username, "CSV", "input", self.filename), sep=',',
                              header=0)
        csvfile.insert(loc=0, column='Predicted_Category', value=correct_category)

        csvfile.to_csv(os.path.join(settings.MEDIA_ROOT, self.username, "CSV", "output", self.filename), sep=',',
                       encoding='utf-8', index=False)

        # Making difference file to upload to the Google drive
        csvfile = pd.read_csv(os.path.join(settings.MEDIA_ROOT, self.username, "CSV", "output", "Difference.csv"),
                              sep=',',
                              header=0)
        csvfile.insert(loc=0, column='Chosen_category', value=correct_category)

        csvfile.to_csv(
            os.path.join(settings.MEDIA_ROOT, self.username, "CSV", "output", "Difference of " + self.filename),
            sep=',',
            encoding='utf-8', index=False)

    def read_file(self):
        """This method will predict the categories from the data of the csv file with encoding='utf-8' for MCGM"""
        # Reading the csvfile through pandas
        csvfile = pd.read_csv(settings.MEDIA_ROOT + "/" + self.username + "/CSV/input" + "/" + self.filename, sep=',',
                              header=0, encoding='utf-8')

        dict_list = []  # Structure is given at the top.
        description = []  # To check if there is a description in the file/row or not
        # These lists will be used for creating the difference file
        cat1 = []
        cat2 = []
        cat3 = []

        for row in csvfile.iterrows():
            # Iterate to each row of the file to separate the categories, title and description with the rest of the data
            dict = {}  # Each row will be a dictionary (See above mentioned structure for reference
            index, data = row  # Separating Index and data from the rows, Index will be used to map the category corresponding to which row
            dict['index'] = index
            if self.group == "ICMC":
                # Categories (as mentioned earlier) will be different for each group
                complaint_title = data['complaint_title']
                # We are separating description to show it in the frontend for the clients
                complaint_description = data['complaint_description']
                description.append(complaint_description)
                dict['problem_description'] = complaint_description
                try:
                    # The ML model will take complaint_title which is a list as an input
                    # and gives categories in an dictionary format like:
                    # cats = {'category1':80, 'category2':10, 'category3':10}
                    cats = self.cs.get_top_3_cats_with_prob(complaint_title)
                except Exception as e:
                    break

            elif self.group == "SpeakUP":
                # Just like ICMC, SpeakUp will have different categories.
                # The ML model will get 'text' field as a list in input
                complaint_title = str(data['text'])
                if complaint_title != 'nan':
                    dict['problem_description'] = complaint_title
                    description.append(complaint_title)
                    cats = self.cs.get_top_3_cats_with_prob(complaint_title)
                else:
                    # There maybe a case where there is nothing in the text field, in that case the ML model will not predict for that row
                    description.append("Problem description not found")
                    dict['problem_description'] = "Problem description not found"
                    cats = {'None': 1}

            for k in cats:
                # In ICMC, there are 2 categories which are being prdicted in marathi.
                # This iteration replaces marathi with english
                # Source: https://stackoverflow.com/questions/4406501/change-the-name-of-a-key-in-dictionary
                cats[k] = int(cats[k] * 100)
                if k == 'मॅनहोलमध्ये व्यक्ती पडणे':
                    temp = cats[k]
                    cats["Person falling in Manhole"] = temp / 100
                    del cats['मॅनहोलमध्ये व्यक्ती पडणे']

                elif k == 'थकबाकी येणे बाकी':
                    temp = cats[k]
                    cats["Outstanding dues pending"] = temp / 100
                    del cats['थकबाकी येणे बाकी']

            # The dictionary (cats) from the ML model was not sorted based it's values (accuracy percentage)
            sorted_cats = sorted(cats.items(), key=operator.itemgetter(1), reverse=True)

            # Lists for Difference File
            cat1.append(sorted_cats[0][0])
            cat2.append(sorted_cats[1][0])
            cat3.append(sorted_cats[2][0])

            dict['category'] = sorted_cats
            dict_list.append(dict)

        df = pd.DataFrame({'Predicted category 1': cat1, 'Predicted category 2': cat2, 'Predicted category 3': cat3,
                           'Complaint Description': description})

        df.to_csv(os.path.join(settings.MEDIA_ROOT, self.username, "CSV", "output", "Difference.csv"), sep=',',
                  encoding='utf-8', index=False)

        # After doing everything, don't forget to delete the object reference of the ClassificationService class
        del self.cs
        return dict_list, csvfile.shape[0]
