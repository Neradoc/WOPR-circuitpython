
for x in 1 2 3 4 5 6 7 8 9 10 11 12
do
	cat dict-all.txt | grep -E '^[a-z]{'$x'}$' > dicts/dict-${x}.txt
done
