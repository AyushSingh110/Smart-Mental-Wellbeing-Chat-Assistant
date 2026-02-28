import torch
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification

class EmotionService:
    def __init__(self, model_path="backend/models/emotion_model"):
        self.tokenizer = DistilBertTokenizerFast.from_pretrained(model_path)
        self.model = DistilBertForSequenceClassification.from_pretrained(model_path)
        self.model.eval()
        self.labels = ["stress", "anxiety", "sadness", "anger", "fear", "neutral"]

    def predict(self, text):
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            logits = self.model(**inputs).logits
            probs = torch.softmax(logits, dim=1).squeeze().tolist()

        return dict(zip(self.labels, probs))