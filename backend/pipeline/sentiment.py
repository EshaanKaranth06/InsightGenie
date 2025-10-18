from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
_analyzer = None

def get_analyzer():
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentIntensityAnalyzer()
    return _analyzer

def analyze_sentiment(text: str) -> dict:
    analyzer = get_analyzer()
    scores = analyzer.polarity_scores(text)
    compound = scores["compound"]
    if compound >= 0.05:
        label = "positive"
    elif compound <= -0.05:
        label = "negative"
    else:
        label = "neutral"
    return {**scores, "label": label}
