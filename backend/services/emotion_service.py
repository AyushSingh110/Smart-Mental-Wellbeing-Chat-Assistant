from backend.config import settings
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification
import torch
class EmotionService:
    def __init__(self):
        self.tokenizer = DistilBertTokenizerFast.from_pretrained(
            "distilbert-base-uncased"
        )
        self.model = DistilBertForSequenceClassification.from_pretrained(
            "distilbert-base-uncased",
            num_labels=6
        )
        self.model.eval()

        self.labels = ["stress", "anxiety", "sadness", "anger", "fear", "neutral"]

    def predict(self, text):
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            logits = self.model(**inputs).logits
            probs = torch.softmax(logits, dim=1).squeeze().tolist()

        return dict(zip(self.labels, probs))