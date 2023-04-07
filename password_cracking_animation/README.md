Animation that mimics movie password cracking: each character shows quickly changing scrambled letters scrolling from the right, until one by one each letter of the passord settles.

First you need to create and install a words directory. It's a directory with one file pre word size, each file containing a list of words, each on a single line. The code takes one or more words and adds numbers and symbols to fill 12 characters.

If no file is present, a random assortment of charaters is used.

To create the example words directory from a list of words, run this in the repository. Or use the existing one.
```py
python make_dicts.py my-list-of-words.txt
```

- Then copy the words directory to the CIRCUITPY drive.
- And copy `password_search.py` to the board under the name `code.py`.
- Watch your high tech supercomputer crack passwords like a champ.
