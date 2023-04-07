#!/bin/bash

import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument("dictionary", type=str, help="Dictionary file one word per line")
args = parser.parse_args()

dictionary = args.dictionary

MAX_LEN = 12
passwords = [set() for i in range(MAX_LEN + 1)]

with open(dictionary, "r") as input_file:
	for line in input_file:
		word = line.strip().lower()
		if len(word) <= MAX_LEN:
			passwords[len(word)].add(word)

os.makedirs("words")

for words in passwords:
	if len(words) == 0: continue
	words = sorted(words)
	wlen = len(words[0])

	with open(f"words/words-{wlen}.txt", "w") as fp:
		for word in words:
			fp.write(word+"\n")
