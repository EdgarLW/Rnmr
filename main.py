import re


# parse_fasta (filename) --> dict
# Takes a filename in fasta format as str and returns a dictionary containing headers as keys and their sequences
# as values.
def parse_fasta(filename):
    with open(filename) as file:
        f = file.read()
        dic = {}
        entries = f.split('>')[1:]
        for entry in entries:
            header, seq = entry.split('\n')[:-1]
            dic[header] = seq
        return dic


# special_chars
def special_chars(string, database='[^0-9A-z_\-]'):
    pattern = re.compile(database)
    if re.search(pattern, string):
        return False


def validate_seq(string, type):
    dic = {'DNA': 'ACTG',
           'PROTEIN': 'ACDEFGHIKLMNPQRSTVWY'}
    for c in string:
        if c not in dic[type.upper()]:
            return False
    return True


dic = parse_fasta('../../Desktop/ALOGs_aa.fasta')
for h, s in dic.items():
    if special_chars(h):
        print(f"{h} presents special characters in header")
    if not validate_seq(s, 'protein'):
        print(f"{h} presents non-canonical protein residues")
