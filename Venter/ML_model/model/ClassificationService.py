import numpy as np
import pandas as pd
from .ImportGraph import ImportGraph
import os
from django.conf import settings


class ClassificationService:
    def __init__(self):

        complaints = pd.read_csv(
            os.path.join(settings.BASE_DIR, "Venter", "ML_model", "dataset", "dataset_mcgm_clean",
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
        return model.run(data)

    def get_top_3_cats_with_prob(self, data):
        prob1 = self.get_probs_graph(0, data, flag=1)

        final_prob = prob1[0]  # + prob2 + prob3 + prob4 + prob5 + prob6 + prob7

        final_sorted = np.argsort(final_prob)

        final_categories = []
        final_probability = []
        # , float(final_prob[final_sorted[-3:][2-i]]/7)
        for i in range(3):
            final_categories.append(self.index_complaint_title_map[final_sorted[-3:][2 - i]])
            final_probability.append(float(final_prob[final_sorted[-3:][2 - i]]))

        result = {}

        for i in range(len(final_categories)):
            result[final_categories[i]] = final_probability[i]
        return result
