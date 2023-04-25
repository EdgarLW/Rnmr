import re
from difflib import SequenceMatcher


# special_chars (str, str) --> bool
# Takes a string and a regex of accepted characters. Searches the given string for occurrences of non-accepted
# characters and returns False if there are any matches.
def special_chars(string, database='[^0-9A-z_]'):
    pattern = re.compile(database)
    match = re.findall(pattern, string)
    lst = []
    if match:
        for m in range(len(match)):
            if match[m] == ' ':
                match.pop(m)
                match.insert(m, 'Space')
        lst += match
    return lst


# validate_seq (str, str) --> bool
# Takes a sequence in str format and searches for non-canonical characters in its sequence. Accepts both DNA
# and PROTEIN sequences. Returns True for validated sequences and False otherwise.
def validate_seq(string, type):
    dic = {'DNA': 'ACTG',
           'PROTEIN': 'ACDEFGHIKLMNPQRSTVWY'}
    lst = []
    for c in range(len(string)):
        if string[c] not in dic[type.upper()]:
            lst += [string[c]]
    return lst


# parse_fasta (filename) --> dict
# Takes a filename in fasta format as str and returns a dictionary containing headers as keys and their sequences
# as values.
def parse_fasta(filename):
    with open(filename) as file:
        lines = file.readlines()
    count = 0
    fasta = {}
    for line in lines:
        line = line.replace('\n', '').strip()
        if line[0] == '>':
            header = line[1:]
            seq = ''
            count += 1
            if header not in fasta.keys():
                fasta[header] = [count, '', special_chars(header), '', False]
            else:
                fasta[header][4] = True
                i = 1
                while header in fasta.keys():
                    header = f'{line[1:]} ({i})'
                    i += 1
                fasta[header] = [count, '', special_chars(header), '', True]
        else:
            seq += line
            fasta[header][1] = seq
            fasta[header][3] = validate_seq(seq, type='protein')
    return fasta

def parse_single_fasta(string):
    string = string.split('>', 1)[-1]
    header, seq = string.split('\n', 1)
    header, seq = header.strip(), seq.strip().replace('\n', '')
    return header, seq


def group_similar_strings(dic, strings, similarity_threshold):
    groups = {}
    for s in strings:
        # Find similar strings using the SequenceMatcher
        for g in groups:
            ratio = SequenceMatcher(None, s, g).ratio()
            if ratio >= similarity_threshold:
                groups[g].add(s)
                break
        else:
            groups[s] = {s}

    aaa = set(tuple(map(str, l)) for l in groups.values())

    lst = []
    for g in aaa:
        g = set(g)
        if len(g) == 2:
            a, b = list(g)
            if a != b:
                lst += [g]
        elif len(g) > 2:
            lst += [g]

    # Create a dictionary using the frozensets as keys
    unique_dict = {}
    for g in lst:
        unique_dict[frozenset(g)] = g

    # Get the unique sets from the dictionary
    unique_lst = sorted(list(unique_dict.values()), key=lambda k: sorted(list(k)))
    for x in unique_lst:
        lst = []
        for s in x:
            if dic[s] not in lst:
                lst += [dic[s]]
        print(x, len(lst) == 1)


def seq_diff(afile, bfile):
    alst = {}
    blst = {}
    clst = {}
    af = parse_fasta(afile)
    bf = parse_fasta(bfile)
    for ha, sa in af.items():
        try:
            list(bf.keys()).index(ha)
            clst[ha] = sa
        except ValueError:
            alst[ha] = sa
    for hb, sb in bf.items():
        try:
            list(af.keys()).index(hb)
        except ValueError:
            blst[hb] = sb
    print(f"Number of sequences exclusive to {afile}: {len(alst)}")
    # print(f"Here they are: {alst}")
    print(f"Number of sequences exclusive to {bfile}: {len(blst)}")
    # print(f"Here they are: {blst}")
    print(f"Number of sequences present in both files: {len(clst)}")
    # print(f"Here they are: {clst}")
