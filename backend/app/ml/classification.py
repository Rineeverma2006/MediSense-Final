"""Maps a question to a topic using TF-IDF + logistic regression on a small labeled seed set."""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

_DATA = [
 ("what does haemoglobin mean","blood"),("explain my cbc report","blood"),("low hemoglobin anemia","blood"),
 ("explain my cholesterol results","lipid"),("ldl hdl triglycerides high","lipid"),("lipid profile meaning","lipid"),
 ("liver function sgpt sgot","liver"),("what is bilirubin","liver"),
 ("blood sugar glucose hba1c","diabetes"),("fasting glucose high","diabetes"),
 ("help me prepare questions for my doctor","doctor"),("what should i ask my doctor","doctor"),
]
_model = make_pipeline(TfidfVectorizer(ngram_range=(1, 2)), LogisticRegression(max_iter=500)).fit(
    [t for t, _ in _DATA], [l for _, l in _DATA])

def topic(question: str) -> str:
    return _model.predict([question])[0]
