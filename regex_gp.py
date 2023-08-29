import re


def brute_conserved_motif(seqs):
    seq0 = seqs[0]
    for i in range(len(seq0)):
        window = len(seq0) - i
        for ii in range(len(seq0) - window + 1):
            motif = seq0[ii:ii + window]
            for seq in seqs:
                if motif not in seq:
                    break
            else:
                return motif


def create_regex(subjects):
    seed = brute_conserved_motif(subjects)

    rows = len(subjects)
    matrix = [[]] * rows
    for i in range(rows):
        seq = subjects[i]
        prior, post = seq.split(seed, 1)
        matrix[i] = [prior, post]

    out = ''
    for c in seed:
        if not re.match('[A-z|\d]', c):
            out += f'\{c}'
        else:
            out += c
    seed = out
    del out

    regex = ''
    for p in range(2):
        if p:
            regex += seed
        run = True
        out = ''
        while run:
            cond = False
            lst = []
            for i in range(rows):
                seq = matrix[i][p]
                try:
                    lst += seq[0]
                except IndexError:
                    lst += ' '
            typ = None
            if any(map(lambda x: x == ' ', lst)):
                cond = True
                lst = list(filter(' '.__ne__, lst))
            if len(lst) == 0:
                run = False
                break
            elif len(set(lst)) == 1:
                cond = 'GIGA FALSE'
                if re.match('[A-z|\d]', lst[0]):
                    typ = lst[0]
                else:
                    typ = f'\{lst[0]}'
            elif all(map(lambda x: re.match('\d', x), lst)):
                    typ = '\d'
            elif all(map(lambda x: re.match('[A-z]', x), lst)):
                    typ = '[A-z]'
            else:
                typ = '.+'
                cond = 'GIGA FALSE'

            if cond == 'GIGA FALSE':
                pass
            elif cond:
                typ = f'{typ}*'
            else:
                typ = f'{typ}+'

            for i in range(rows):
                try:
                    matrix[i][p] = matrix[i][p].replace(re.match(typ, matrix[i][p])[0], '', 1)
                except TypeError:
                    pass

            out += typ
        regex += out
    return regex.replace('_', '[_.]').replace('\.', '[_.]')
