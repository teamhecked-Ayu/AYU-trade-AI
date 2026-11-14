import asyncio
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from core.sentiment_data import RSSSentimentDataProvider, SentimentDataProvider


class SentimentFusion:
    def __init__(self, data_provider: SentimentDataProvider | None = None):
        self.vader = SentimentIntensityAnalyzer()
        self.finbert_model_name = "ProsusAI/finbert"
        self.tokenizer = None
        self.model = None
        self._torch = None
        self.data_provider = data_provider or RSSSentimentDataProvider()

    def _load_finbert(self):
        if self.tokenizer is None:
            from loguru import logger
            try:
                from transformers import AutoTokenizer, AutoModelForSequenceClassification
                import torch
            except ImportError as exc:
                raise RuntimeError("FinBERT requires optional transformers and torch dependencies") from exc
            logger.info("Loading FinBERT Transformer model...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.finbert_model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.finbert_model_name)
            self._torch = torch
            logger.success("FinBERT Loaded.")

    def get_vader_score(self, text):
        return self.vader.polarity_scores(text)["compound"]

    def get_finbert_score(self, text):
        self._load_finbert()
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        outputs = self.model(**inputs)
        probs = self._torch.nn.functional.softmax(outputs.logits, dim=-1)
        scores = probs.detach().cpu().numpy()[0]
        return float(scores[0] - scores[1])

    async def analyze_ensemble(self, texts):
        if not texts:
            return 0.0
        scores = []
        for text in texts:
            v_score = self.get_vader_score(text)
            f_score = self.get_finbert_score(text)
            scores.append(0.7 * f_score + 0.3 * v_score)
        return float(np.mean(scores))

    async def fetch_and_fuse(self, query="crypto"):
        texts = await self.data_provider.fetch_texts(query)
        return float(await self.analyze_ensemble(texts))
