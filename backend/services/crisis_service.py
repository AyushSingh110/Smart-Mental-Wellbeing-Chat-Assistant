import torch
import re
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification

CRISIS_PATTERNS = {
    r"\bi want to die\b": 0.9,
    r"\bkill myself\b": 0.95,
    r"\bend it all\b": 0.7,
    r"\bno reason to live\b": 0.85
}

class CrisisService:
    def __init__(self, model_path="backend/models/crisis_model"):
        self.tokenizer = DistilBertTokenizerFast.from_pretrained(model_path)
        self.model = DistilBertForSequenceClassification.from_pretrained(model_path)
        self.model.eval()

    def rule_score(self, text):
        score = 0.0
        for pattern, weight in CRISIS_PATTERNS.items():
            if re.search(pattern, text.lower()):
                score = max(score, weight)
        return score

    def model_score(self, text):
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            logits = self.model(**inputs).logits
            probs = torch.softmax(logits, dim=1)
            return probs[0][1].item()

    def predict(self, text):
        ml = self.model_score(text)
        rule = self.rule_score(text)
        return max(ml, rule)