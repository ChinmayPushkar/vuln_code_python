"""Module for building new datasets or reading it from files. Upper layer of data (sequence) management."""
# pylint: disable=too-many-arguments, too-many-locals
import gzip
import math
import os
import pickle
import random
import sys
from collections import defaultdict
import numpy as np

from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from sklearn import cross_validation
from VirClass.VirClass.load_ncbi import load_seqs_from_ncbi

MEDIA_DIR = "media/"

def one_hot(x, n):
    assert np.max(x) < n, "Cannot create numpy array; number of classes must be bigger than max number of list."
    if isinstance(x, list):
        x = np.array(x)
    x = x.flatten()
    o_h = np.zeros((len(x), n))
    o_h[np.arange(len(x)), x] = 1
    return o_h

def seq_to_bits(vec, unique_nucleotides=None, trans_dict=None):
    if trans_dict is None:
        assert unique_nucleotides is not None, "Number of unique nucleotides and transmission dictionary not present."
        trans_dict = {}
        for el in unique_nucleotides:
            trans_dict[el] = [1 if x == el else 0 for x in unique_nucleotides]
    else:
        if len(list(trans_dict.keys())) != len(next(iter(trans_dict.values()))):
            print("WARNING: number of keys in transmission dictionary and length of either value aren't same!")
    
    bits_vector = []
    for c in vec:
        if c in list(trans_dict.keys()):
            bits_vector += trans_dict[c]
        else:
            bits_vector += [1 for _ in list(trans_dict.keys())]
    return bits_vector

def load_from_file_fasta(filename, depth=4, taxonomy_el_count=-1):
    temp_data = defaultdict(list)
    temp_tax = {}

    try:
        assert os.path.isfile(filename)
        with gzip.open(filename, "rt") as file:
            for seq_record in SeqIO.parse(file, "fasta"):
                oid = seq_record.id
                classification = seq_record.description.split(oid)[1].strip()
                seq = str(seq_record.seq)
                temp_data[oid] = seq
                temp_tax[oid] = classification
    except AssertionError:
        temp_data, temp_tax = load_seqs_from_ncbi(seq_len=-1, skip_read=0, overlap=0, taxonomy_el_count=taxonomy_el_count)
        with gzip.open(filename, "wt") as file:
            for oid, seq in temp_data.items():
                temp_tax[oid] = ';'.join(temp_tax[oid].split(";")[:depth])
                row = SeqRecord(Seq(seq), id=str(oid), description=temp_tax[oid])
                SeqIO.write(row, file, "fasta")

    return temp_data, temp_tax

def dataset_from_id(temp_data, temp_tax, ids, read_size, sample, trans_dict, unique_nuc=None):
    assert 0.0 < sample <= 1.0, "Sampling size is in wrong range - it must be between 0.0 and 1.0."
    assert trans_dict is not None or unique_nuc is not None, "Both transmission dictionary and unique nucleotides cannot be empty."
    tempX = []
    tempY = []
    for te_id in ids:
        seq = temp_data[te_id]
        while seq:
            if len(seq) < read_size:
                break
            tempX.append(seq_to_bits(seq[:read_size], trans_dict=trans_dict, unique_nucleotides=unique_nuc))
            tempY.append(temp_tax[te_id])
            seq = seq[int(math.ceil(read_size / sample)):]
    return tempX, tempY

def load_dataset(filename):
    with gzip.open(filename, "rt") as f:
        return pickle.load(f)

def save_dataset(filename, obj):
    with gzip.open(filename, "wt") as f:
        pickle.dump(obj, f)
    print("Successfully saved as: " + filename)

def build_dataset_ids(oids, test, seed):
    datasets_ids = {"tr_ids": [], "te_ids": [], "trtr_ids": [], "trte_ids": []}
    ss = cross_validation.LabelShuffleSplit(oids, n_iter=1, test_size=test, random_state=seed)
    for train_index, test_index in ss:
        datasets_ids["tr_ids"] = list(oids[i] for i in train_index)
        datasets_ids["te_ids"] = list(oids[i] for i in test_index)
        assert set(datasets_ids["tr_ids"]).intersection(set(datasets_ids["te_ids"])) == set()
        tr_ids = datasets_ids["tr_ids"]
        ss_tr = cross_validation.LabelShuffleSplit(tr_ids, n_iter=1, test_size=0.2, random_state=seed)
        for train_train_index, train_test_index in ss_tr:
            datasets_ids["trtr_ids"] = list(tr_ids[i] for i in train_train_index)
            datasets_ids["trte_ids"] = list(tr_ids[i] for i in test_test_index)
    return datasets_ids

def classes_to_numerical(temp_data, labels):
    temp_l = []
    label_num = -1
    temp_tax = {}
    class_size = defaultdict(int)
    for gid, l in labels.items():
        if l not in temp_l:
            temp_l.append(l)
            label_num += 1
        temp_tax[gid] = label_num
        class_size[label_num] += len(temp_data[gid])

    for _class, s in class_size.items():
        class_size[_class] = s / list(temp_tax.values()).count(_class)

    return temp_tax, class_size

def load_data(filename, test=0.2, trans_dict=None, depth=4, sample=0.2, read_size=100, onehot=True, seed=random.randint(0, sys.maxsize), taxonomy_el_count=-1, unique_nuc=None):
    assert 0.0 <= test < 1.0, "Test size is in wrong range - it must be between 0.0 and 1.0."
    assert 0.0 < sample <= 1.0, "Sampling size is in wrong range - it must be between 0.0 and 1.0."
    assert (".fasta.gz" in filename), "Currently supported suffixes is '.fasta.gz'."
    suffix = ".fasta.gz"
    assert trans_dict is not None or unique_nuc is not None, "Both transmission dictionary and unique nucleotides cannot be empty."

    temp_data, labels = load_from_file_fasta(os.path.join(MEDIA_DIR, filename), depth=depth, taxonomy_el_count=taxonomy_el_count)
    assert set(temp_data.keys()) == set(labels.keys()), "When loading from fasta keys in data dictionary and labels dictionary must be same."

    temp_tax, class_size = classes_to_numerical(temp_data, labels)
    number_of_classes = len(list(class_size.keys()))

    dataset = {"trX": [], "trY": [], "teX": [], "teY": [], "trteX": [], "trteY": []}

    try:
        dataset["trX"] = load_dataset(os.path.join(MEDIA_DIR, filename[:filename.index(suffix)] + "-trX" + suffix))
        dataset["trY"] = load_dataset(os.path.join(MEDIA_DIR, filename[:filename.index(suffix)] + "-trY" + suffix))
        dataset["teX"] = load_dataset(os.path.join(MEDIA_DIR, filename[:filename.index(suffix)] + "-teX" + suffix))
        dataset["teY"] = load_dataset(os.path.join(MEDIA_DIR, filename[:filename.index(suffix)] + "-teY" + suffix))
        dataset["trteX"] = load_dataset(os.path.join(MEDIA_DIR, filename[:filename.index(suffix)] + "-trteX" + suffix))
        dataset["trteY"] = load_dataset(os.path.join(MEDIA_DIR, filename[:filename.index(suffix)] + "-trteY" + suffix))
    except IOError:
        oids = [x for x in list(labels.keys())]
        datasets_ids = build_dataset_ids(oids=oids, test=test, seed=seed)
        dataset["teX"], dataset["teY"] = dataset_from_id(temp_data, temp_tax, datasets_ids["te_ids"], read_size, sample, trans_dict, unique_nuc)
        dataset["trX"], dataset["trY"] = dataset_from_id(temp_data, temp_tax, datasets_ids["trtr_ids"], read_size, sample, trans_dict, unique_nuc)
        dataset["trteX"], dataset["trteY"] = dataset_from_id(temp_data, temp_tax, datasets_ids["trte_ids"], read_size, sample, trans_dict, unique_nuc)
        save_dataset(os.path.join(MEDIA_DIR, filename[:filename.index(suffix)] + "-trX" + suffix), dataset["trX"])
        save_dataset(os.path.join(MEDIA_DIR, filename[:filename.index(suffix)] + "-teX" + suffix), dataset["teY"])
        save_dataset(os.path.join(MEDIA_DIR, filename[:filename.index(suffix)] + "-trY" + suffix), dataset["trY"])
        save_dataset(os.path.join(MEDIA_DIR, filename[:filename.index(suffix)] + "-teY" + suffix), dataset["teY"])
        save_dataset(os.path.join(MEDIA_DIR, filename[:filename.index(suffix)] + "-trteX" + suffix), dataset["trteX"])
        save_dataset(os.path.join(MEDIA_DIR, filename[:filename.index(suffix)] + "-trteY" + suffix), dataset["trteY"])

    if onehot:
        dataset["trY"] = one_hot(dataset["trY"], number_of_classes)
        dataset["teY"] = one_hot(dataset["teY"], number_of_classes)
        dataset["trteY"] = one_hot(dataset["trteY"], number_of_classes)

    return np.asarray(dataset["trX"]), np.asarray(dataset["teX"]), np.asarray(dataset["trY"]), np.asarray(dataset["teY"]), np.asarray(dataset["trteX"]), np.asarray(dataset["trteY"]), number_of_classes, class_size