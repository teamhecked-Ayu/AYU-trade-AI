import asyncio
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import numpy as np
from core.sentiment_data import RSSSentimentDataProvider, SentimentDataProvider

class SentimentFusion:
    def __init__(self, data_provider: SentimentDataProvider | None = None):
        # VADER for quick rule-based sentiment
        self.vader = SentimentIntensityAnalyzer()
        self.finbert_model_name = "ProsusAI/finbert"
        self.tokenizer = None
        self.model = None
        self.data_provider = data_provider or RSSSentimentDataProvider()

    def _load_finbert(self):
        if self.tokenizer is None:
            from loguru import logger
            logger.info("Loading FinBERT Transformer model...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.finbert_model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.finbert_model_name)
            logger.success("FinBERT Loaded.")
        
    def get_vader_score(self, text):
        return self.vader.polarity_scores(text)['compound']

    def get_finbert_score(self, text):
        self._load_finbert()
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        outputs = self.model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
        # FinBERT labels: 0: positive, 1: negative, 2: neutral
        scores = probs.detach().numpy()[0]
        return scores[0] - scores[1] # Positive - Negative

    async def analyze_ensemble(self, texts):
        """
        Ensemble scraping & fusion from multiple sources.
        Returns a fused sentiment score between -1 and 1.
        """
        if not texts:
            return 0.0
            
        scores = []
        for text in texts:
            v_score = self.get_vader_score(text)
            f_score = self.get_finbert_score(text)
            # Weighted ensemble: FinBERT (70%) + VADER (30%)
            scores.append(0.7 * f_score + 0.3 * v_score)
            
        return np.mean(scores)

    async def fetch_and_fuse(self, query="crypto"):
        """Fetch real text from the configured provider and fuse sentiment."""
        texts = await self.data_provider.fetch_texts(query)
        return float(await self.analyze_ensemble(texts))
