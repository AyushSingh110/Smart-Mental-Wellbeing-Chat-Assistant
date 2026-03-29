import pandas as pd
from sklearn.model_selection import train_test_split
from transformers import (
    DistilBertTokenizerFast,
    DistilBertForSequenceClassification,
    Trainer,
    TrainingArguments
)
from dataset_utils import TextDataset
import torch
from torch.nn import BCEWithLogitsLoss

MODEL = "models/emotion"
NUM_LABELS = 6

def load_data(path):
    df = pd.read_csv(path)
    texts = df["text"].tolist()
    labels = df[[
        "stress", "anxiety", "sadness",
        "anger", "fear", "neutral"
    ]].values.tolist()
    return train_test_split(texts, labels, test_size=0.1, random_state=42)

class WeightedTrainer(Trainer):
    def __init__(self, pos_weight, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loss_fct = BCEWithLogitsLoss(pos_weight=pos_weight)

    def compute_loss(self, model, inputs, return_outputs=False):
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        logits = outputs.logits

        loss = self.loss_fct(logits, labels.float())
        return (loss, outputs) if return_outputs else loss

def main():
    tokenizer = DistilBertTokenizerFast.from_pretrained(MODEL)
    model = DistilBertForSequenceClassification.from_pretrained(
        MODEL,
        num_labels=NUM_LABELS,
        problem_type="multi_label_classification"
    )

    pos_weight = torch.tensor(
        [8.4, 46.8, 21.0, 8.0, 65.9, 2.8],  # stress, anxiety, sadness, anger, fear, neutral
        device="cuda"
            )

    model.loss_fct = BCEWithLogitsLoss(pos_weight=pos_weight)



    X_train, X_val, y_train, y_val = load_data("data/emotion_train.csv")

    train_ds = TextDataset(X_train, y_train, tokenizer)
    val_ds = TextDataset(X_val, y_val, tokenizer)

    args = TrainingArguments(
        output_dir="models/emotion",
        evaluation_strategy="epoch",
        save_strategy="epoch",
        learning_rate=1e-5,
        per_device_train_batch_size=32,
        per_device_eval_batch_size=32,
        num_train_epochs=5,
        weight_decay=0.01,
        load_best_model_at_end=True,
        save_total_limit=2
    )

    trainer = WeightedTrainer(
    pos_weight=pos_weight,
    model=model,
    args=args,
    train_dataset=train_ds,
    eval_dataset=val_ds
    )

    trainer.train()
    trainer.save_model("models/emotion")
    tokenizer.save_pretrained("models/emotion")

if __name__ == "__main__":
    main()