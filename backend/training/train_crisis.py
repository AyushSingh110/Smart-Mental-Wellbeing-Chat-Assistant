import pandas as pd
import numpy as np
import torch
from sklearn.model_selection import train_test_split
from sklearn.metrics import recall_score
from transformers import (
    DistilBertTokenizerFast,
    DistilBertForSequenceClassification,
    Trainer,
    TrainingArguments
)
from dataset_utils import TextDataset
MODEL = "distilbert-base-uncased"
NUM_LABELS = 2  # BINARY CLASSIFICATION

def load_data(path):
    df = pd.read_csv(path)
    df = df.dropna(subset=["label"])
    df["text"] = df["text"].astype(str)
    df["label"] = df["label"].astype(int)

    return train_test_split(
        df["text"].tolist(),
        df["label"].tolist(),
        test_size=0.1,
        random_state=42,
        stratify=df["label"]  # IMPORTANT for crisis data
    )

def compute_metrics(eval_pred):
    logits, labels = eval_pred

    preds = np.argmax(logits, axis=1)
    recall = recall_score(labels, preds, zero_division=0)

    return {"recall": recall}

def main():
    tokenizer = DistilBertTokenizerFast.from_pretrained(MODEL)

    model = DistilBertForSequenceClassification.from_pretrained(
        MODEL,
        num_labels=NUM_LABELS
    )
    
    X_train, X_val, y_train, y_val = load_data("data/crisis_train.csv")

    train_ds = TextDataset(X_train, y_train, tokenizer)
    val_ds = TextDataset(X_val, y_val, tokenizer)

    args = TrainingArguments(
        output_dir="models/crisis",
        evaluation_strategy="epoch",
        save_strategy="epoch",

        learning_rate=2e-5,
        num_train_epochs=4,

        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,

        fp16=True,
        weight_decay=0.01,

        load_best_model_at_end=True,
        metric_for_best_model="recall",
        greater_is_better=True,

        save_total_limit=2,
        logging_steps=50
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        compute_metrics=compute_metrics
    )

    trainer.train()

    trainer.save_model("models/crisis")
    tokenizer.save_pretrained("models/crisis")

if __name__ == "__main__":
    main()