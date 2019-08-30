from Backend.celery import app
from .ML_model.sentence_model.modeldriver import SimilarityMapping

@app.task
def predict_runner(filepath):
    sm = SimilarityMapping(filepath)
    results = sm.driver()
    return results
