from datasets import load_dataset
import os

# Load the dataset (lhoestq version)
dataset = load_dataset("lhoestq/conll2003") 

# Manually define the official CoNLL-2003 labels
label_list = [
    "O",       # 0
    "B-PER",   # 1
    "I-PER",   # 2
    "B-ORG",   # 3
    "I-ORG",   # 4
    "B-LOC",   # 5
    "I-LOC",   # 6
    "B-MISC",  # 7
    "I-MISC"   # 8
]

def save_as_conll(split_name, data):
    output_file = f"{split_name}.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        for entry in data:
            tokens = entry['tokens']
            tag_ids = entry['ner_tags'] 
            
            for token, tid in zip(tokens, tag_ids):
                # Map the ID to the string label using the manual list
                label = label_list[tid]
                # Write in CoNLL format: Token _ _ Label
                f.write(f"{token} _ _ {label}\n")
            f.write("\n")
    print(f"Created: {output_file}")

# Process and save the splits
save_as_conll("train", dataset["train"])
save_as_conll("valid", dataset["validation"])
save_as_conll("test", dataset["test"])
