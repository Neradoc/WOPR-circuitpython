Animation that mimics movie password cracking: each character shows quickly changing scrambled letters scrolling from the right, until one by one each letter of the passord settles.

Install word directories

- Create a `dicts` folder on the board.
- Run the `make_dicts.sh` script in the repository.
- Copy at least one of the word files generated onto the dicts folder of the board.

You can use your own list of words, where dict-n.txt containes n-letter words. Up to 12.
The `make_dicts.sh` script reads a local `dict-all.txt` file and splits it into files by word length.
Words with less than 12 characters get numbers and dashes added when displayed.
