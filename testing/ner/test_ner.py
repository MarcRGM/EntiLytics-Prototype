from pathlib import Path
from flair.data import Corpus
from flair.datasets import ColumnCorpus
from flair.models import SequenceTagger
import sys

sys.dont_write_bytecode = True

# Get the directory where the script is located
# Prevent the AssertionError by providing a concrete path
base_path = Path(__file__).parent

# Define the columns: 0 is Token, 3 is the NER label
columns = {0: 'text', 3: 'ner'}

try:
    # Load the corpus using the absolute path
    corpus: Corpus = ColumnCorpus(
        base_path, 
        columns,
        train_file='train.txt',
        test_file='test.txt',
        dev_file='valid.txt'
    )

    # Load BiLSTM-Softmax model
    print("Loading model and evaluating...")
    tagger = SequenceTagger.load('ner-fast')

    # Run evaluation
    result = tagger.evaluate(corpus.test, gold_label_type='ner')

    print("\n" + "="*45)
    print(f"CONLL-2003 BASELINE RESULTS")
    print("="*45)
    print(f"Overall F1-Score: {result.main_score:.4f}")
    print("-" * 45)
    print(result.detailed_results)
    print("="*45)

except AssertionError:
    print("Error: Could not find .txt files. Ensure they are in the same folder as this script.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")