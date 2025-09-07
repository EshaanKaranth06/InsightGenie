
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = None

def get_analyzer():
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentIntensityAnalyzer()
    return _analyzer

def analyze_sentiment(text: str) -> dict:
    """
    Returns {'compound': float, 'neg': float, 'neu': float, 'pos': float, 'label': 'pos'/'neg'/'neu'}
    """
    analyzer = get_analyzer()
    scores = analyzer.polarity_scores(text)
    compound = scores["compound"]
    if compound >= 0.05:
        label = "positive"
    elif compound <= -0.05:
        label = "negative"
    else:
        label = "neutral"
    scores["label"] = label
    return scores
