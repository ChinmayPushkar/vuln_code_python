#! /usr/bin/python
# -*- coding: utf8 -*-
import tensorflow as tf
import os
from sys import platform as _platform
import collections
import random
import numpy as np
import warnings
from six.moves import xrange
from tensorflow.python.platform import gfile
import re

## Iteration functions
def generate_skip_gram_batch(data, batch_size, num_skips, skip_window, data_index=0):
    """Generate a training batch for the Skip-Gram model."""
    assert batch_size % num_skips == 0
    assert num_skips <= 2 * skip_window
    batch = np.ndarray(shape=(batch_size), dtype=np.int32)
    labels = np.ndarray(shape=(batch_size, 1), dtype=np.int32)
    span = 2 * skip_window + 1
    buffer = collections.deque(maxlen=span)
    for _ in range(span):
        buffer.append(data[data_index])
        data_index = (data_index + 1) % len(data)
    for i in range(batch_size // num_skips):
        target = skip_window
        targets_to_avoid = [ skip_window ]
        for j in range(num_skips):
            while target in targets_to_avoid:
                target = random.randint(0, span - 1)
            targets_to_avoid.append(target)
            batch[i * num_skips + j] = buffer[skip_window]
            labels[i * num_skips + j, 0] = buffer[target]
        buffer.append(data[data_index])
        data_index = (data_index + 1) % len(data)
    return batch, labels, data_index

## Sampling functions
def sample(a=[], temperature=1.0):
    """Sample an index from a probability array."""
    b = np.copy(a)
    try:
        if temperature == 1:
            return np.argmax(np.random.multinomial(1, a, 1))
        if temperature is None:
            return np.argmax(a)
        else:
            a = np.log(a) / temperature
            a = np.exp(a) / np.sum(np.exp(a))
            return np.argmax(np.random.multinomial(1, a, 1))
    except:
        message = "For large vocabulary_size, choice a higher temperature to avoid log error. Hint : use ``sample_top``."
        warnings.warn(message, Warning)
        return np.argmax(np.random.multinomial(1, b, 1))

def sample_top(a=[], top_k=10):
    """Sample from ``top_k`` probabilities."""
    idx = np.argpartition(a, -top_k)[-top_k:]
    probs = a[idx]
    probs = probs / np.sum(probs)
    choice = np.random.choice(idx, p=probs)
    return choice

## Vector representations of words (Advanced)  UNDOCUMENT
class SimpleVocabulary(object):
    """Simple vocabulary wrapper."""
    def __init__(self, vocab, unk_id):
        self._vocab = vocab
        self._unk_id = unk_id

    def word_to_id(self, word):
        """Returns the integer id of a word string."""
        return self._vocab.get(word, self._unk_id)

class Vocabulary(object):
    """Create Vocabulary class."""
    def __init__(self, vocab_file, start_word="<S>", end_word="</S>", unk_word="<UNK>", pad_word="<PAD>"):
        if not tf.gfile.Exists(vocab_file):
            tf.logging.fatal("Vocab file %s not found.", vocab_file)
        with tf.gfile.GFile(vocab_file, mode="r") as f:
            reverse_vocab = list(f.readlines())
        reverse_vocab = [line.split()[0] for line in reverse_vocab]
        assert start_word in reverse_vocab
        assert end_word in reverse_vocab
        if unk_word not in reverse_vocab:
            reverse_vocab.append(unk_word)
        vocab = dict([(x, y) for (y, x) in enumerate(reverse_vocab)])
        self.vocab = vocab
        self.reverse_vocab = reverse_vocab
        self.start_id = vocab[start_word]
        self.end_id = vocab[end_word]
        self.unk_id = vocab[unk_word]
        self.pad_id = vocab[pad_word]

    def word_to_id(self, word):
        """Returns the integer word id of a word string."""
        return self.vocab.get(word, self.unk_id)

    def id_to_word(self, word_id):
        """Returns the word string of an integer word id."""
        if word_id >= len(self.reverse_vocab):
            return self.reverse_vocab[self.unk_id]
        else:
            return self.reverse_vocab[word_id]

def process_sentence(sentence, start_word="<S>", end_word="</S>"):
    """Converts a sentence string into a list of string words."""
    try:
        import nltk
    except:
        raise Exception("Hint : NLTK is required.")
    if start_word is not None:
        process_sentence = [start_word]
    else:
        process_sentence = []
    process_sentence.extend(nltk.tokenize.word_tokenize(sentence.lower()))
    if end_word is not None:
        process_sentence.append(end_word)
    return process_sentence

def create_vocab(sentences, word_counts_output_file, min_word_count=1):
    """Creates the vocabulary of word to word_id."""
    from collections import Counter
    counter = Counter()
    for c in sentences:
        counter.update(c)
    word_counts = [x for x in counter.items() if x[1] >= min_word_count]
    word_counts.sort(key=lambda x: x[1], reverse=True)
    word_counts = [("<PAD>", 0)] + word_counts
    with tf.gfile.FastGFile(word_counts_output_file, "w") as f:
        f.write("\n".join(["%s %d" % (w, c) for w, c in word_counts]))
    reverse_vocab = [x[0] for x in word_counts]
    unk_id = len(reverse_vocab)
    vocab_dict = dict([(x, y) for (y, x) in enumerate(reverse_vocab)])
    vocab = SimpleVocabulary(vocab_dict, unk_id)
    return vocab

## Vector representations of words
def simple_read_words(filename="nietzsche.txt"):
    """Read context from file without any preprocessing."""
    with open(filename, "r") as f:
        words = f.read()
        return words

def read_words(filename="nietzsche.txt", replace=['\n', '<eos>']):
    """File to list format context."""
    with tf.gfile.GFile(filename, "r") as f:
        try:
            context_list = f.read().replace(*replace).split()
        except:
            f.seek(0)
            replace = [x.encode('utf-8') for x in replace]
            context_list = f.read().replace(*replace).split()
        return context_list

def read_analogies_file(eval_file='questions-words.txt', word2id={}):
    """Reads through an analogy question file, return its id format."""
    questions = []
    questions_skipped = 0
    with open(eval_file, "rb") as analogy_f:
        for line in analogy_f:
            if line.startswith(b":"):
                continue
            words = line.strip().lower().split(b" ")
            ids = [word2id.get(w.strip()) for w in words]
            if None in ids or len(ids) != 4:
                questions_skipped += 1
            else:
                questions.append(np.array(ids))
    print("Eval analogy file: ", eval_file)
    print("Questions: ", len(questions))
    print("Skipped: ", questions_skipped)
    analogy_questions = np.array(questions, dtype=np.int32)
    return analogy_questions

def build_vocab(data):
    """Build vocabulary."""
    counter = collections.Counter(data)
    count_pairs = sorted(counter.items(), key=lambda x: (-x[1], x[0]))
    words, _ = list(zip(*count_pairs))
    word_to_id = dict(zip(words, range(len(words))))
    return word_to_id

def build_reverse_dictionary(word_to_id):
    """Given a dictionary for converting word to integer id."""
    reverse_dictionary = dict(zip(word_to_id.values(), word_to_id.keys()))
    return reverse_dictionary

def build_words_dataset(words=[], vocabulary_size=50000, printable=True, unk_key='UNK'):
    """Build the words dictionary and replace rare words with 'UNK' token."""
    count = [[unk_key, -1]]
    count.extend(collections.Counter(words).most_common(vocabulary_size - 1))
    dictionary = dict()
    for word, _ in count:
        dictionary[word] = len(dictionary)
    data = list()
    unk_count = 0
    for word in words:
        if word in dictionary:
            index = dictionary[word]
        else:
            index = 0
            unk_count += 1
        data.append(index)
    count[0][1] = unk_count
    reverse_dictionary = dict(zip(dictionary.values(), dictionary.keys()))
    if printable:
        print('Real vocabulary size    %d' % len(collections.Counter(words).keys()))
        print('Limited vocabulary size {}'.format(vocabulary_size))
    return data, count, dictionary, reverse_dictionary

def words_to_word_ids(data=[], word_to_id={}, unk_key='UNK'):
    """Given a context (words) in list format and the vocabulary."""
    word_ids = []
    for word in data:
        if word_to_id.get(word) is not None:
            word_ids.append(word_to_id[word])
        else:
            word_ids.append(word_to_id[unk_key])
    return word_ids

def word_ids_to_words(data, id_to_word):
    """Given a context (ids) in list format and the vocabulary."""
    return [id_to_word[i] for i in data]

def save_vocab(count=[], name='vocab.txt'):
    """Save the vocabulary to a file so the model can be reloaded."""
    pwd = os.getcwd()
    vocabulary_size = len(count)
    with open(os.path.join(pwd, name), "w") as f:
        for i in range(vocabulary_size):
            f.write("%s %d\n" % (tf.compat.as_text(count[i][0]), count[i][1]))
    print("%d vocab saved to %s in %s" % (vocabulary_size, name, pwd))

## Functions for translation
def basic_tokenizer(sentence, _WORD_SPLIT=re.compile(b"([.,!?\"':;)(])")):
    """Very basic tokenizer: split the sentence into a list of tokens."""
    words = []
    sentence = tf.compat.as_bytes(sentence)
    for space_separated_fragment in sentence.strip().split():
        words.extend(re.split(_WORD_SPLIT, space_separated_fragment))
    return [w for w in words if w]

def create_vocabulary(vocabulary_path, data_path, max_vocabulary_size, tokenizer=None, normalize_digits=True, _DIGIT_RE=re.compile(br"\d"), _START_VOCAB=[b"_PAD", b"_GO", b"_EOS", b"_UNK"]):
    """Create vocabulary file (if it does not exist yet) from data file."""
    if not gfile.Exists(vocabulary_path):
        print("Creating vocabulary %s from data %s" % (vocabulary_path, data_path))
        vocab = {}
        with gfile.GFile(data_path, mode="rb") as f:
            counter = 0
            for line in f:
                counter += 1
                if counter % 100000 == 0:
                    print("  processing line %d" % counter)
                tokens = tokenizer(line) if tokenizer else basic_tokenizer(line)
                for w in tokens:
                    word = re.sub(_DIGIT_RE, b"0", w) if normalize_digits else w
                    if word in vocab:
                        vocab[word] += 1
                    else:
                        vocab[word] = 1
            vocab_list = _START_VOCAB + sorted(vocab, key=vocab.get, reverse=True)
            if len(vocab_list) > max_vocabulary_size:
                vocab_list = vocab_list[:max_vocabulary_size]
            with gfile.GFile(vocabulary_path, mode="wb") as vocab_file:
                for w in vocab_list:
                    vocab_file.write(w + b"\n")
    else:
        print("Vocabulary %s from data %s exists" % (vocabulary_path, data_path))

def initialize_vocabulary(vocabulary_path):
    """Initialize vocabulary from file, return the word_to_id (dictionary) and id_to_word (list)."""
    if gfile.Exists(vocabulary_path):
        rev_vocab = []
        with gfile.GFile(vocabulary_path, mode="rb") as f:
            rev_vocab.extend(f.readlines())
        rev_vocab = [tf.compat.as_bytes(line.strip()) for line in rev_vocab]
        vocab = dict([(x, y) for (y, x) in enumerate(rev_vocab)])
        return vocab, rev_vocab
    else:
        raise ValueError("Vocabulary file %s not found.", vocabulary_path)

def sentence_to_token_ids(sentence, vocabulary, tokenizer=None, normalize_digits=True, UNK_ID=3, _DIGIT_RE=re.compile(br"\d")):
    """Convert a string to list of integers representing token-ids."""
    if tokenizer:
        words = tokenizer(sentence)
    else:
        words = basic_tokenizer(sentence)
    if not normalize_digits:
        return [vocabulary.get(w, UNK_ID) for w in words]
    return [vocabulary.get(re.sub(_DIGIT_RE, b"0", w), UNK_ID) for w in words]

def data_to_token_ids(data_path, target_path, vocabulary_path, tokenizer=None, normalize_digits=True, UNK_ID=3, _DIGIT_RE=re.compile(br"\d")):
    """Tokenize data file and turn into token-ids using given vocabulary file."""
    if not gfile.Exists(target_path):
        print("Tokenizing data in %s" % data_path)
        vocab, _ = initialize_vocabulary(vocabulary_path)
        with gfile.GFile(data_path, mode="rb") as data_file:
            with gfile.GFile(target_path, mode="w") as tokens_file:
                counter = 0
                for line in data_file:
                    counter += 1
                    if counter % 100000 == 0:
                        print("  tokenizing line %d" % counter)
                    token_ids = sentence_to_token_ids(line, vocab, tokenizer, normalize_digits, UNK_ID=UNK_ID, _DIGIT_RE=_DIGIT_RE)
                    tokens_file.write(" ".join([str(tok) for tok in token_ids]) + "\n")
    else:
        print("Target path %s exists" % target_path)