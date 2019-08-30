import os

import numpy as np
import pandas as pd
from django.conf import settings

from .ImportGraph import ImportGraph


class ClassificationService:
    def __init__(self):

        complaints = pd.read_csv(
            os.path.join(settings.BASE_DIR, "Venter", "ML_model", "ICMC", "dataset", "dataset_mcgm_clean",
                         "complaint_categories.csv"))
        self.index_complaint_title_map = {}

        for i in range(len(complaints)):
            line = complaints['Subcategory-English'][i]

            if isinstance(line, float):
                line = complaints['Subcategory-Marathi'][i]

            line = line.strip('\'').replace("/", " ").replace("(", " ").replace(")", " ")
            self.index_complaint_title_map[i] = line

        self.g0 = ImportGraph.get_instance()

    def get_probs_graph(self, model_id, data, flag):
        if model_id == 0:
            model = self.g0

        data = model.process_query(data, flag)
        print('DATA SHAPE', data.shape)
        return model.run(data)

    def get_top_3_cats_with_prob(self, data):
        prob1 = self.get_probs_graph(0, data, flag=1)

        result_list = []
        for x in range(prob1.shape[0]):
            final_prob = prob1[x]
            final_sorted = np.argsort(final_prob)

            final_categories = []
            final_probabilities = []

            for i in range(3):
                final_categories.append(self.index_complaint_title_map[final_sorted[-3:][2-i]])
                final_probabilities.append(int(float(final_prob[final_sorted[-3:][2-i]])*100))
            result = {}
            for c, p in zip(final_categories, final_probabilities):
                result[c] = p
            result_list.append(result)

        return result_list