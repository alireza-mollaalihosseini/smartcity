import numpy as np
from sklearn.linear_model import LogisticRegression

def train_predictive_model(X, y):
    model = LogisticRegression()
    model.fit(X, y)
    return model
