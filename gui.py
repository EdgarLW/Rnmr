import tkinter.ttk
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from main import parse_fasta
from main import special_chars
from main import validate_seq
from main import parse_single_fasta
from main import group_similar_strings
from difflib import SequenceMatcher
from regex_gp import *
import re

# Set the minimum size for the window
WINDOW_HEIGHT = 500
WINDOW_WIDTH = 900

# ----- GLOBAL VARIABLES -----
# Base
file = ''
config_file = './config.txt'
cfg = {}


class FastaFile:
    # A Fasta class is a dictionary containing headers as keys and lists as values
    # These lists present 5 entries:
    # 0: Index - The index of the entry as an integer
    # 1: Seq - The sequence of the fasta
    # 2: special_chars of the Header - Runs special_chars on the header and returns a list of strings or None
    # 3: validate_seq of Seq - Runs validate_seq on Seq and returns a list of strings or None
    # 4: IsDup - A bool indicating if the sequence is a duplicate of another
    def __init__(self, content):
        self.content = content
        self.headers = self.content.keys()
        self.values = self.content.values()
        self.items = self.content.items()

    def update_trees(self):

        # Delete the content inside the trees before updating each
        t_overview.delete(*t_overview.get_children())
        t_dup.delete(*t_dup.get_children())
        t_sc_header.delete(*t_sc_header.get_children())
        t_sc_seq.delete(*t_sc_seq.get_children())
        t_sim.delete(*t_sim.get_children())

        # Delete the widgets in Special Characters before updating them
        # Headers Notebook
        for widget in n_headers.winfo_children():
            if isinstance(widget, (ttk.Combobox, ttk.Entry, ttk.Checkbutton)):
                widget.destroy()
        # Sequences Notebook
        for widget in n_seqs.winfo_children():
            if isinstance(widget, (ttk.Combobox, ttk.Entry, ttk.Checkbutton)):
                widget.destroy()

        # Add the content inside the trees
        for header, values in self.items:
            # OVERVIEW
            # Index  Header  Length  |  Sequence
            t_overview.insert('', 'end', text=values[0], values=[header, len(values[1]), values[1]])
            # If there are any SCs in Header:
            # HEADER SCs
            # Index  Header SCs
            if values[2]:
                t_sc_header.insert('', 'end', text=values[0], values=[header, values[2]])
            # If there are any SCs in Sequence:
            # SEQUENCE SCs
            # Index  Header  SCs
            if values[3]:
                t_sc_seq.insert('', 'end', text=values[0], values=[header, values[3]])
            # If the sequence is a duplicate:
            # DUPLICATES
            # Index  Header  |  Sequence
            if values[4]:
                t_dup.insert('', 'end', text=values[0], values=[header, values[1]])

        # Time to add the Widgets to SCs:
        params = [[t_sc_header, go_buttonH, n_headers],
                  [t_sc_seq, go_buttonS, n_seqs]]
        # Run the loop twice, once for n_headers and the second for n_seqs
        for i in range(2):
            # Get the params
            tree, button, master = params[i]
            # The content
            children = tree.get_children('')
            # Return if nothing in it
            if not children:
                continue
            # Set state to not disabled
            button.state(['!disabled'])

            # Create a set to use as a map to add widgets later
            set_children = set()
            for child in children:
                sc = tree.item(child)['values'][1].split(' ')
                for s in sc:
                    set_children.add(s)

            # Add the widgets for every entry in the set at row j + 2
            for j in range(len(set_children)):
                ttk.Checkbutton(master, text=list(set_children)[j], width=6)\
                                .grid(column=0, row=j + 2, padx=5, sticky='W')
                ttk.Combobox(master, values=('replace for', 'copy to file', 'move to file'), state='readonly',
                             width=12) \
                   .grid(column=1, row=j + 2, sticky='w')
                ttk.Entry(master).grid(column=2, row=j + 2, sticky='we')

        fasta.headers = fasta.content.keys()
        fasta.values = fasta.content.values()

    def save(self, _as=False):

        if not _as:
            global file
        else:
            file = filedialog.asksaveasfile()

        out = ''
        for k, v in self.items:
            v = v[1]  # Get only the sequence
            out += f'>{k}\n{v}\n'

        file.write(out[:-1])


# Initiate GLOBAL fasta
fasta = FastaFile({})
# GLOBAL sorting variables
tree_sort_column = None
tree_sort_reverse = False
# Similarity Tool
sim_lst = []
# Renaming Tool
renames = []

# File Comparison Tool


class CompLst:
    # A CompLst is simply a list of three dictionaries: dictionary A through C.
    # Dictionary A has the elements exclusive to A file, B to B file, and C to both files.
    def __init__(self, lst):
        self.lst = lst
        self.lst_a = self.lst[0]
        self.lst_b = self.lst[1]
        self.lst_c = self.lst[2]

    # run method for filling a CompLst
    def run(self, bfile):
        # Reference GLOBAL fasta to act as file number 1
        global fasta
        # ----- ERROR CHECKS -----
        # If there is no main file loaded raise error
        if not fasta:
            raise_error('Please load a main file')
            return self
        # If there is no second file loaded raise error
        if not bfile:
            raise_error('Please load a second file')
            return self
        # ------------------------
        # Initiate 3 empty dictionaries
        a_lst = {}
        b_lst = {}
        c_lst = {}
        # the parsed a and b files
        af = fasta.content
        bf = parse_fasta(bfile)
        # For every element in A, check for their presence in B
        # If they exist, add to C, else A
        for ak, ai in af.items():
            try:
                # [[idxA, idxB], sequence, special_chars(header), validate_seq(sequence), Repeated(bool)]

                # This confusion is to prevent an expansion of the first element of the list
                # (the indexes for A and B files)
                c_lst[ak] = [af[ak][0], list(bf.keys()).index(ak) + 1],\
                            af[ak][1], af[ak][2], af[ak][3], af[ak][4]
            except ValueError:
                a_lst[ak] = ai
        # For every element in B, check for their presence in A
        for bk, bi in bf.items():
            try:
                list(af.keys()).index(bk)
            except ValueError:
                b_lst[bk] = bi

        # Must update EVERY parameter of self
        self.lst = [a_lst, b_lst, c_lst]
        self.lst_a = a_lst
        self.lst_b = b_lst
        self.lst_c = c_lst
        return self

    # remove method to remove a given header from the CompLst class, from every dictionary
    def remove(self, header):
        try:
            self.lst_a.pop(header)
        except KeyError:
            pass
        try:
            self.lst_b.pop(header)
        except KeyError:
            pass
        try:
            self.lst_c.pop(header)
        except KeyError:
            pass

        return self

    # action method to write to file or update a TreeView, in this case the t_comp TreeView, given the CompLst
    def action(self):
        # comp_file_select:
        # A (Current File)          0
        # B (Other File)            1
        # C (Both Files)            2
        # A + B (Not in Both Files) 3
        option = comp_file_select.current()

        # comp_file_action:
        # Move      0
        # Copy      1
        # Treeview  2
        action = comp_file_action.current()

        # comp_file_entry:
        # ttk.Entry (text)
        to_file = comp_file_entry.get()

        # ----- ERROR CHECKS -----
        if option not in (0, 1, 2, 3):
            raise_error('Please select a valid comparison option')
            return
        if action not in (0, 1, 2):
            raise_error('Please select a valid comparison action')
            return
        if action != 2 and not to_file:
            raise_error('Please input a destiny file name')
            return
        if option == 0 and not self.lst_a:
            raise_error('There are no sequences unique to the current file')
            return
        if option == 1 and not self.lst_b:
            raise_error('There are no sequences unique to the second file')
            return
        if option == 2 and not self.lst_c:
            raise_error('The files do not present redundancies')
            return
        if option == 3 and not self.lst_a and not self.lst_b:
            raise_error('The files are identical')
            return
        # ------------------------

        # Move or Copy
        if action in (0, 1):

            out = ''

            # A + B
            if option == 3:
                dictionaries = (self.lst_a, self.lst_b)
            # Others
            else:
                dictionaries = self.lst[option]

            # Write FASTA
            for dic in dictionaries:
                for k, v in dic.items():
                    out += f'>{k}\n{v[1]}\n'

            # Append to file
            with open(to_file, 'w') as file_out:
                file_out.write(out)

            # Move
            if action == 0:
                for dic in dictionaries:
                    for k in dic.keys():
                        self.remove(k)

            # return to prevent from running the code below
            return

        # Treeview

        # Remove everything in the tree before adding stuff
        t_comp.delete(*t_comp.get_children())

        if option == 0:
            for ak, ai in self.lst_a.items():
                t_comp.insert('', 'end', text=ai[0], values=('', ak, ai[1]))
        elif option == 1:
            for bk, bi in self.lst_b.items():
                t_comp.insert('', 'end', text='', values=(bi[0], bk, bi[1]))
        elif option == 2:
            for ck, ci in self.lst_c.items():
                # remember that the very first item has two values for those in C: idxA and idxB
                t_comp.insert('', 'end', text=ci[0][0], values=(ci[0][1], ck, ci[1]))
        elif option == 3:
            for ak, ai in self.lst_a.items():
                t_comp.insert('', 'end', text=ai[0], values=('', ak, ai[1]))
            for bk, bi in self.lst_b.items():
                t_comp.insert('', 'end', text='', values=(bi[0], bk, bi[1]))


# Initiate GLOBAL comp_lst
comp_lst = CompLst([{}, {}, {}])

# ----------------------------


# ----- BASIC FUNCTIONS -----

def donothing():
    print('Nothing')


def open_file():
    global file
    file = filedialog.askopenfilename()
    if file:
        global fasta
        fasta = FastaFile(parse_fasta(file))
        global file_label
        file_label.set('Current file: ' + file)
        update_labels()
        fasta.update_trees()


def update_labels():
    sc_h_count, sc_s_count, dup_count = 0, 0, 0
    for entry in fasta.values:
        i, seq, sc_h, sc_s, dup = entry
        if sc_h:
            sc_h_count += 1
        if sc_s:
            sc_s_count += 1
        if dup:
            dup_count += 1
    global head_label
    head_label.set(f'A total of {sc_h_count} headers were detected with special characters!')
    global seq_label
    seq_label.set(f'A total of {sc_s_count} sequences were detected with special characters!')
    global dup_label
    dup_label.set(f'A total of {dup_count} sequences were detected as duplicates!')


def navigate(idxs):
    for idx in idxs:
        # Overview
        if int(idx) == 0:
            overview_frame.grid()
            dup_frame.grid_remove()
            sc_frame.grid_remove()
            sim_frame.grid_remove()
            o2h_frame.grid_remove()
            rnmr_frame.grid_remove()
            comp_frame.grid_remove()
        # Check for Duplicates
        elif int(idx) == 2:
            overview_frame.grid_remove()
            dup_frame.grid()
            sc_frame.grid_remove()
            sim_frame.grid_remove()
            o2h_frame.grid_remove()
            rnmr_frame.grid_remove()
            comp_frame.grid_remove()
        # Special Characters
        elif int(idx) == 3:
            overview_frame.grid_remove()
            dup_frame.grid_remove()
            sc_frame.grid()
            sim_frame.grid_remove()
            o2h_frame.grid_remove()
            rnmr_frame.grid_remove()
            comp_frame.grid_remove()
        # Group similar headers
        elif int(idx) == 4:
            overview_frame.grid_remove()
            dup_frame.grid_remove()
            sc_frame.grid_remove()
            sim_frame.grid()
            o2h_frame.grid_remove()
            rnmr_frame.grid_remove()
            comp_frame.grid_remove()
        # ORF to HMMER
        elif int(idx) == 5:
            overview_frame.grid_remove()
            dup_frame.grid_remove()
            sc_frame.grid_remove()
            sim_frame.grid_remove()
            o2h_frame.grid()
            rnmr_frame.grid_remove()
            comp_frame.grid_remove()
        elif int(idx) == 6:
            overview_frame.grid_remove()
            dup_frame.grid_remove()
            sc_frame.grid_remove()
            sim_frame.grid_remove()
            o2h_frame.grid_remove()
            rnmr_frame.grid()
            comp_frame.grid_remove()
        elif int(idx) == 7:
            overview_frame.grid_remove()
            dup_frame.grid_remove()
            sc_frame.grid_remove()
            sim_frame.grid_remove()
            o2h_frame.grid_remove()
            rnmr_frame.grid_remove()
            comp_frame.grid()


def delete_seq(event):
    if t_overview.winfo_ismapped():
        tree = t_overview
    elif t_dup.winfo_ismapped():
        tree = t_dup
    elif t_dup_seq.winfo_ismapped():
        tree = t_dup_seq
    elif t_sc_header.winfo_ismapped():
        tree = t_sc_header
    elif t_sc_seq.winfo_ismapped():
        tree = t_sc_seq
    elif t_sim.winfo_ismapped():
        tree = t_sim
    elif t_comp.winfo_ismapped():
        tree = t_comp
    else:
        return

    # Check for content inside Treeview before opening new window
    if not event.widget.selection():
        return

    global fasta
    global sim_lst

    # Get a list of the widgets children and then the index number of the selected item
    tree_children = tree.get_children('')

    for child in tree.selection():

        item_idx = tree_children.index(child)

        # Get the values of the item
        item = event.widget.item(child)
        header = item['values'][0]
        fasta.content.pop(header)
        for lst in sim_lst:
            try:
                lst.remove(header)
            except KeyError:
                pass

    # Update the trees and labels
    update_labels()
    fasta.update_trees()

    # Set the focus to be the same idx number
    tree_children = tree.get_children()
    # If we have not deleted the very last element present
    if tree_children:
        try:
            tree.focus(tree_children[item_idx])
            tree.selection_set(tree_children[item_idx])
        # if we delete the last element we need to go back
        except IndexError:
            tree.focus(tree_children[item_idx - 1])
            tree.selection_set(tree_children[item_idx - 1])


def select_all():
    if t_overview.winfo_ismapped():
        for child in t_overview.get_children():
            t_overview.selection_add(child)
    elif t_dup.winfo_ismapped():
        for child in t_dup.get_children():
            t_dup.selection_add(child)
    elif t_dup_seq.winfo_ismapped():
        for child in t_dup_seq.get_children():
            t_dup_seq.selection_add(child)
    elif t_sc_header.winfo_ismapped():
        for child in t_sc_header.get_children():
            t_sc_header.selection_add(child)
    elif t_sc_seq.winfo_ismapped():
        for child in t_sc_seq.get_children():
            t_sc_seq.selection_add(child)
    elif t_sim.winfo_ismapped():
        for child in t_sim.get_children():
            t_sim.selection_add(child)
    elif t_comp.winfo_ismapped():
        for child in t_comp.get_children():
            t_comp.selection_add(child)


def update_sim_message(event):
    if not event:
        return
    col_width = sim_frame.grid_bbox(0, 0)[2]
    sim_message.config(wraplength=col_width)


def fill_similarity_tree(threshold):
    global fasta
    global sim_lst
    if not sim_lst:
        sim_lst = group_similar_strings(fasta.headers, threshold)
    if sim_lst:
        t_sim.state(['!disabled'])
        for i in range(len(sim_lst)):
            if i != 0:
                t_sim.insert('', 'end', text='---')
            group = sim_lst[i]
            for header in group:
                t_sim.insert('', 'end', text=fasta.content[header][0], values=(header, fasta.content[header][1]))
    else:
        t_sim.state(['disabled'])


def load_b_file():
    global b_file
    b_file.set(filedialog.askopenfilename())
    if not b_file:
        return


def raise_error(text):
    # Create an Error window
    error_window = Toplevel(root, pady=20)
    error_window.title('Error')
    error_window.option_add('**tearOff', FALSE)
    error_window.minsize(300, 180)
    error_window.maxsize(300, 180)
    error_window.columnconfigure(0, minsize=100)
    error_window.columnconfigure(1, weight=1)
    error_window.rowconfigure(0, weight=1)

    # Add the content inside the new window
    error_img = PhotoImage(file='Assets/error.png')
    error = Label(error_window, image=error_img)
    error.image = error_img  # A must so the python garbage collector doesn't delete the image
    error.grid(column=0, row=0, sticky='nsew')
    error_text = Label(error_window, text=text, justify='center', wraplength=200)
    error_text.grid(column=1, row=0, sticky='nsw')
    error_ok = Button(error_window, text='OK', command=error_window.destroy, anchor='center', width=8)
    error_ok.grid(column=0, columnspan=2, row=1)


def open_window(event):
    # Check for content inside Treeview before opening new window
    if not event.widget.selection():
        return

    global fasta

    # Get the item that was clicked
    item_id = event.widget.focus()

    # Get the values of the item
    item = event.widget.item(item_id)
    values = item['values']

    # Create and display the new window
    new_window = Toplevel(root)
    new_window.title(f"{values[0]}")
    new_window.columnconfigure(0, weight=1)
    new_window.rowconfigure(0, weight=1)
    new_frame = ttk.Frame(new_window, padding="3 3 7 0")
    new_frame.grid(column=0, row=0, sticky='NSEW')
    new_window.option_add('**tearOff', FALSE)

    # Add the content inside the new window
    # Entry (text)
    entry = Text(new_frame)
    entry.configure()
    entry.insert('1.0', f'>{values[0]}\n{fasta.content[values[0]][1]}')
    entry.grid(column=0, row=0, sticky='NSEW')

    # Button for Saving
    save_button = Button(new_frame, text='Save', width=10,
                         command=lambda: func_save_button(entry, inWindow=new_window, save=True))
    save_button.grid(column=0, row=1, pady=7, sticky='NES')

    # Set minimum size
    new_window.update_idletasks()
    new_window.minsize(new_window.winfo_width(), new_window.winfo_height())


def func_save_button(entry, inWindow=None, save=False):

    global fasta
    if inWindow:
        # Saves the alterations made
        new_header, seq = parse_single_fasta(entry.get('1.0', 'end'))
        # Gets the old header
        old_header = str(inWindow.title())
        #
        type = True

    # If not inWindow that means it was called from GO Button
    else:
        type, f1, f2 = entry
        if type:
            old_header = f1
            new_header = f2
            seq = fasta.content[f1][1]
        else:
            old_header = new_header = f1
            seq = f2

    # If there were no alterations made, return
    if old_header == new_header and fasta.content[old_header][1] == seq:
        return

    for value in fasta.values:
        # When the match is found
        if value[0] == fasta.content[old_header][0]:
            # Create a new entry
            fasta.content[new_header] = [value[0],
                                         seq,
                                         special_chars(new_header),
                                         validate_seq(seq, type='protein'),
                                         value[4]]
            # And remove the old one if in header mode
            if type:
                fasta.content.pop(old_header)
            break

    # Set the updated title
    if inWindow:
        inWindow.title(f"{new_header}")

    # Order the dictionary
    fasta.content = {k: v for k, v in sorted(fasta.content.items(), key=lambda x: x[1][0])}
    fasta.header = fasta.content.keys()
    fasta.values = fasta.content.values()
    fasta.items = fasta.content.items()

    # Updates
    if save:
        fasta.update_trees()
        update_labels()


def go_button(type):

    # type (bool)
    # True --> Header
    # False --> Sequence

    # Make 3 empty lists for the widgets in SC
    check_list = []
    combo_list = []
    entry_list = []

    # Check for what notebook we are in
    if type:
        notebook = n_headers
        t = t_sc_header
        t_children = [t.item(x)['values'][0] for x in t.get_children()]
    else:
        notebook = n_seqs
        t = t_sc_seq
        t_children = [t.item(x)['values'][0] for x in t.get_children()]

    # For every widget in the frame, check for their types to add to the lists
    for widget in notebook.winfo_children():
        if isinstance(widget, tkinter.ttk.Checkbutton):
            check_list.append(widget)
        elif isinstance(widget, tkinter.ttk.Combobox):
            combo_list.append(widget)
        elif isinstance(widget, tkinter.ttk.Entry):
            entry_list.append(widget)

    # For every widget line
    for check, choice, text in zip(check_list, combo_list, entry_list):
        # If not selected, return
        if check.state() != ('selected',):
            continue

        # choice
        # replace       0
        # copy to file  1
        # move to file  2

        # replace
        if choice.current() == 0:
            # Get the text to replace
            rep = check.cget('text')
            # For every header
            for child in t_children:
                # If the text is Space get the real deal
                if rep == 'Space':
                    rep = ' '
                if type:
                    func_save_button((type, child, child.replace(rep, text.get())), save=False)
                else:
                    func_save_button((type, child, fasta.content[child][1].replace(rep, text.get())), save=False)

        # copy to file / move to file
        elif choice.current() in (1, 2):
            out = ''
            for child in t_children:
                out += f'>{child}\n{fasta.content[child][1]}\n'
                # if move to file
                if choice.current() == 2:
                    fasta.content.pop(child)
            with open(text.get(), 'a') as file:
                file.write(out)

    # Update
    fasta.update_trees()
    update_labels()


def dup_seq_go(threshold):

    # Delete the content inside the trees before updating each
    t_dup_seq.delete(*t_dup_seq.get_children())

    global fasta

    list1 = list(fasta.headers)
    list2 = list1.copy()
    x = 1

    for i in range(len(list1)):
        for j in range(i + 1, len(list2)):
            ratio = SequenceMatcher(None, fasta.content[list1[i]][1], fasta.content[list2[j]][1]).quick_ratio()
            if ratio >= threshold/100:
                t_dup_seq.insert('', 'end', text=str(x), values=[f'{list1[i]} is {round(ratio*100, 1)}% identical to {list2[j]}'])
                x += 1

    fasta.update_trees()
    update_labels()


def sort_tree(tree, col, data_type):

    global tree_sort_column, tree_sort_reverse

    if col == tree_sort_column:
        tree_sort_reverse = not tree_sort_reverse
    else:
        tree_sort_reverse = False

    tree_sort_column = col

    try:
        column_index = tree['columns'].index(col)
        if data_type == 'int':
            data = [(int(tree.item(child)['values'][column_index]), child) for child in tree.get_children('')]
        else:
            data = [(tree.item(child)['values'][column_index], child) for child in tree.get_children('')]
        data.sort(reverse=tree_sort_reverse)
    except ValueError:
        data = [(int(tree.item(child)['text']), child) for child in tree.get_children('')]  # Display column #0 cannot be set
        data.sort(reverse=tree_sort_reverse)

    for index, (value, child) in enumerate(data):
        tree.move(child, '', index)


def extract_ids():

    global fasta

    if not fasta.content:
        raise_error('Please open a file first')

    id_regex = re.compile('ID=[a-zA-Z0-9_.]*')
    locus_regex = re.compile('locus=[a-zA-Z0-9_.]*')
    # t_regex = re.compile('transcript:[a-zA-Z0-9_.]*')

    for header in list(fasta.headers):
        if re.search(id_regex, header):
            match = re.search(id_regex, header)
            func_save_button((True, header, match.group(0)[3:]))
        elif re.search(locus_regex, header):
            match = re.search(locus_regex, header)
            func_save_button((True, header, match.group(0)[6:]))
        # elif re.search(t_regex, header):
        #     match = re.search(t_regex, header)
        #     func_save_button((True, header, match.group(0)[11:]))
        else:
            func_save_button((True, header, header.split(' ')[0]))

    fasta.update_trees()
    update_labels()


# translate_entry( str ->  )
def translate_entry(config):

    if config:
        with open(config) as file:
            lines = file.readlines()
    else:
        global config_file
        with open(config_file) as file:
            lines = file.readlines()

    global renames

    renames = []

    for line in lines:
        line = line.split(',')
        renames.append(line)

    global fasta

    for item in renames:
        genus, species = item[0].split(' ')
        re_gex = item[1].strip()
        pattern = re.compile(re_gex)

        for header in list(fasta.headers):
            # When a match is found
            if re.match(pattern, header) and header[:6] != f'{genus[:2]}{species[:3]}_':
                func_save_button((True, header, f'{genus[:2]}{species[:3]}_{header}'))

    fasta.update_trees()
    update_labels()


def load_configure():
    global config_file
    config_file = filedialog.askopenfilename()
    rnmr_label.set('Configuration file: ' + config_file)
    if not rnmr_label:
        return


def open_cfg_window():

    if not t_overview.selection():
        return

    # Load config_file
    global config_file
    global cfg
    with open(config_file) as config:
        config = config.read()

    dict_ = {}
    entries = config.split('\n')
    for entry in entries:
        if not entry:
            break
        spec, rgx = entry.split(',')[0], entry.split(',')[1:]
        dict_[spec] = [r.strip() for r in rgx]
    cfg = dict_
    del dict_, config

    # Create and display the new window
    cfg_window = Toplevel(root)
    cfg_window.title('Add to Config')
    cfg_window.columnconfigure(0, weight=1)
    cfg_window.rowconfigure(3, weight=1)
    cfg_frame = ttk.Frame(cfg_window, padding="3 3 3 3")
    cfg_frame.grid(column=0, row=0, sticky='NSEW')
    cfg_window.option_add('**tearOff', FALSE)
    cfg_window.minsize(500, 180)
    cfg_window.maxsize(500, 180)

    # Add the content inside the new window
    # Label (Species)
    cfg_species = Label(cfg_frame, text='Species:')
    cfg_species.grid(column=0, row=0, sticky='nsew')

    # Entry (Species)
    entry_species = Text(cfg_frame, height=1, width=52)
    entry_species.grid(column=1, row=0, sticky='NEW')

    # Label (Regex)
    cfg_regex = Label(cfg_frame, text='Regex:')
    cfg_regex.grid(column=0, row=1, sticky='nsew')

    # Entry (Regex)
    entry_regex = Text(cfg_frame, height=1, width=52)
    entry_regex.configure()
    entry_regex.insert('1.0', create_regex(list(t_overview.item(child)['values'][0] for child in t_overview.selection())))
    entry_regex.grid(column=1, row=1, sticky='new')

    # Note frame
    cfg_note_frame = ttk.Frame(cfg_frame, borderwidth=2, relief='groove', padding="3 3 3 3")
    cfg_note_frame.grid(column=0, columnspan=2, row=3, sticky='nsew')
    cfg_note = Label(cfg_note_frame, text='Please provide a species name!\ne.g. Arabidopsis thaliana', justify='left')
    cfg_note.grid(column=0, row=0, sticky='nsew')

    # Button for Saving
    add_button = Button(cfg_frame, text='Add', width=10, command=lambda: add2cfg(entry_species.get('1.0', 'end'),
                                                                                 entry_regex.get('1.0', 'end'),
                                                                                 cfg_window))
    add_button.grid(column=1, row=2, pady=7, sticky='NES')


def add2cfg(species, regex, window):

    species, regex = species.replace('\n', ''), regex.replace('\n', '')

    if not species:
        raise_error('Please provide a species name')
        return
    elif not regex:
        raise_error('Please provide a sequence regex')
        return

    global cfg
    try:
        if regex not in cfg[species]:
            cfg[species] += [regex]
    except KeyError:
        cfg[species] = [regex]

    out = ''
    for s, r in cfg.items():
        out += f'{s}, '
        for r_item in r:
            out += f'{r_item}, '
        out = f'{out[:-2]}\n'
    with open(config_file, 'w') as file:
        file.write(out)

    window.destroy()


# ----- CONSTANT -------------------------------------------------------------------------------------------------------
# Initiate
root = Tk()
root.title("Rnmr")

# Set root and mainframe
mainframe = ttk.Frame(root, padding="3 3 12 12")
mainframe.columnconfigure(1, weight=1)
mainframe.rowconfigure(1, weight=1)
mainframe.grid(column=0, row=0, sticky='NWES')
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
root.option_add('**tearOff', FALSE)

# Menubar
menubar = Menu(root)
root['menu'] = menubar
# File (Menu)
menu_file = Menu(menubar, tearoff=0)
menubar.add_cascade(menu=menu_file, label='File')
menu_file.add_command(label='Open...', command=open_file)
menu_file.add_command(label='Save', command=fasta.save)
menu_file.add_command(label='Save as...', command=lambda: fasta.save(_as=True))
menu_file.add_separator()
menu_file.add_command(label='Close', command=root.quit)
# Edit (Menu)
menu_edit = Menu(menubar, tearoff=0)
menubar.add_cascade(menu=menu_edit, label='Edit')
menu_edit.add_command(label='Select all', command=select_all)
menu_edit.add_separator()
menu_edit.add_command(label='Undo', command=donothing)
menu_edit.add_command(label='Redo', command=donothing)
# Actions (Menu)
menu_actions = Menu(menubar, tearoff=0)
menubar.add_cascade(menu=menu_actions, label='Actions')
menu_actions.add_command(label='Extract IDs', command=extract_ids)
menu_actions.add_command(label='Rename', command=lambda: translate_entry('./config.txt'))

# "Current file:"
open_file_frame = ttk.Frame(mainframe, height=1)
open_file_frame.grid(column=1, row=0, sticky='NW', padx=7, pady=7)
file_label = StringVar(value='Current file:')
open_file_label = ttk.Label(open_file_frame, textvariable=file_label, width=80)
open_file_label.grid(column=1, row=0, sticky='W')
# Button to load file
file_button = Button(mainframe, text='Load', command=open_file)
file_button.grid(column=2, row=0, sticky='W')

# Listbox for actions
options = ['Overview', 'Tools', '    Duplicates', '    Special Characters', '    Similar', '    O2H', '    Renamer',
           '    Compare Files']
optionsvar = StringVar(value=options)
listbox = Listbox(mainframe, listvariable=optionsvar, selectmode='browse')
listbox.grid(column=0, row=0, rowspan=2, sticky='NSW')
# Add select to change the current options
listbox.bind('<<ListboxSelect>>', lambda e: navigate(listbox.curselection()))

# ----- Overview Frame -------------------------------------------------------------------------------------------------
overview_frame = Frame(mainframe, borderwidth=2, relief='groove')
overview_frame.grid(column=1, columnspan=2, row=1, sticky='NSEW', padx=7)
overview_frame.grid_rowconfigure(0, weight=1)
overview_frame.grid_columnconfigure(0, weight=1)
# Overview action
t_overview = ttk.Treeview(overview_frame, columns=('header', 'length'))
t_overview.heading('#0', text='#', command=lambda: sort_tree(t_overview, '#0', 'int'))
t_overview.column('#0', width=50, anchor='w', stretch=False)
t_overview.heading('header', text='Header', command=lambda: sort_tree(t_overview, 'header', 'str'))
t_overview.column('header', anchor='w')
t_overview.heading('length', text='Length', command=lambda: sort_tree(t_overview, 'length', 'int'))
t_overview.column('length', anchor='w')
t_overview.grid(column=0, row=0, sticky='NSEW', pady=1)
# Add a slider to the right
t_slider = ttk.Scrollbar(overview_frame, orient=VERTICAL, command=t_overview.yview)
t_overview.configure(yscrollcommand=t_slider.set)
t_slider.grid(column=1, row=0, sticky='NSE')
# Add double click option on entry to open new window with FASTA
t_overview.bind('<Double-1>', open_window)
# Add a Delete event for removal of sequences
t_overview.bind('<Delete>', lambda e: delete_seq(e))

context = Menu(root, tearoff=0)
context.add_command(label='Extract Regex', command=open_cfg_window)
# Add a Right click event to open-up the context menu
t_overview.bind('<Button-3>', lambda e: context.post(e.x_root, e.y_root))
# Add a Left click event to close the context menu
t_overview.bind('<Button-1>', lambda e: context.unpost())

# We start at the overview, so no need to grid_remove

# ----- Duplicates Frame -----------------------------------------------------------------------------------------------
dup_frame = Frame(mainframe, borderwidth=2, relief='groove')
dup_frame.grid(column=1, columnspan=2, row=1, sticky='nsew', padx=7)
dup_frame.grid_rowconfigure(1, weight=1)
dup_frame.grid_columnconfigure(0, weight=1)
dup_frame.grid_propagate(False)
#
dup_notebook = ttk.Notebook(dup_frame)
dup_notebook.grid(column=0, row=1, columnspan=2, sticky='NSEW')
#
dup_headers = ttk.Frame(dup_notebook)
dup_headers.grid_rowconfigure(1, weight=1)
dup_headers.grid_columnconfigure(0, weight=1)
dup_notebook.add(dup_headers, text='Headers')
#
dup_label = StringVar(value='Please select a file')
dup_dup_label = ttk.Label(dup_headers, textvariable=dup_label)
dup_dup_label.grid(column=0, columnspan=2, row=0, sticky='nw', ipadx=5)
#
t_dup = ttk.Treeview(dup_headers, columns='h')
t_dup.heading('#0', text='#', command=lambda: sort_tree(t_dup, '#0', 'int'))
t_dup.column('#0', width=50, stretch=False)
t_dup.heading('h', text='Header', command=lambda: sort_tree(t_dup, 'h', 'str'))
t_dup.grid(column=0, columnspan=4, row=1, sticky='nsew')
#
t_dup_slider_h = ttk.Scrollbar(dup_headers, orient=VERTICAL, command=t_dup.yview)
t_dup.configure(yscrollcommand=t_dup_slider_h.set)
t_dup_slider_h.grid(column=1, row=1, sticky='nse')
# Add double click option on entry to open new window with FASTA
t_dup.bind('<Double-1>', open_window)
# Add a Delete event for removal of sequences
t_dup.bind('<Delete>', lambda e: delete_seq(e))

# SEQUENCES
dup_seqs = ttk.Frame(dup_notebook)
dup_seqs.grid_rowconfigure(2, weight=1)
dup_seqs.grid_columnconfigure(2, weight=1)
dup_notebook.add(dup_seqs, text='Sequences')
# Combobox for what comparison to make
dup_select = ttk.Combobox(dup_seqs, values=('U (Uniques)', 'D (Duplicates)', 'U + D'), state='readonly')
dup_select.grid(column=0, row=0, sticky='nsew')
# Combobox for what action to take for a given comparison
dup_action = ttk.Combobox(dup_seqs, values=('Move', 'Copy', 'Treeview'), state='readonly')
dup_action.grid(column=1, row=0, sticky='nsew')
# Entry field to a possible Move or Copy action
dup_entry = ttk.Entry(dup_seqs)
dup_entry.grid(column=2, row=0, sticky='nsew')
# The Go Button for running the above selected options
dup_go = ttk.Button(dup_seqs, text='Go', command=lambda: dup_seq_go(scale_var.get()))
dup_go.grid(column=3, row=0, sticky='nsew')
# A slider for adjusting the value of threshold
scale_var = IntVar()
dup_scale = tkinter.Scale(dup_seqs, orient=HORIZONTAL, from_=50.0, to=100.0, variable=scale_var)
dup_scale.grid(column=0, columnspan=4, row=1, sticky='we')
dup_scale.set(100)
# Treeview
t_dup_seq = ttk.Treeview(dup_seqs, columns='s')
t_dup_seq.heading('#0', text='#', command=lambda: sort_tree(t_dup_seq, '#0', 'int'))
t_dup_seq.column('#0', width=50, stretch=False)
t_dup_seq.heading('s', text='Sequences', command=lambda: sort_tree(t_dup_seq, 's', 'str'))
t_dup_seq.grid(column=0, columnspan=4, row=2, sticky='nsew')
# Add a slider to the right
t_dup_slider_s = ttk.Scrollbar(dup_seqs, orient=VERTICAL, command=t_dup_seq.yview)
t_dup_seq.configure(yscrollcommand=t_dup_slider_s.set)
t_dup_slider_s.grid(column=3, row=2, sticky='NSE')

dup_frame.grid_remove()

# ----- Special Chars Frame --------------------------------------------------------------------------------------------
sc_frame = Frame(mainframe, borderwidth=2, relief='groove')
sc_frame.grid(column=1, columnspan=2, row=1, sticky='NSEW', padx=7)
sc_frame.grid_rowconfigure(0, weight=1)
sc_frame.grid_columnconfigure(0, weight=1)
sc_frame.grid_propagate(False)
# Notebook with Headers and Sequences tabs
sc_notebook = ttk.Notebook(sc_frame)
n_headers = ttk.Frame(sc_notebook)
n_seqs = ttk.Frame(sc_notebook)
sc_notebook.grid(column=0, row=0, columnspan=2, sticky='NSEW')
n_headers.grid_rowconfigure(1, weight=1)
n_headers.grid_columnconfigure(2, weight=1)
n_seqs.grid_rowconfigure(1, weight=1)
n_seqs.grid_columnconfigure(2, weight=1)
# Headers tab
sc_notebook.add(n_headers, text='Headers')
head_label = StringVar(value='Please select a file')
sc_head_label = ttk.Label(n_headers, textvariable=head_label)
sc_head_label.grid(column=0, columnspan=4, row=0, sticky='NW', ipadx=5)
t_sc_header = ttk.Treeview(n_headers, columns=('h', 'sc'))
t_sc_header.heading('#0', text='#', command=lambda: sort_tree(t_sc_header, '#0', 'int'))
t_sc_header.column('#0', width=50, stretch=False)
t_sc_header.heading('h', text='Header', command=lambda: sort_tree(t_sc_header, 'h', 'str'))
t_sc_header.heading('sc', text='Special Characters')
t_sc_header.column('sc', width=0)
t_sc_header.grid(column=0, columnspan=4, row=1, sticky='NSEW')
# Add a slider to the right
t_sc_header_slider = ttk.Scrollbar(n_headers, orient=VERTICAL, command=t_sc_header.yview)
t_sc_header.configure(yscrollcommand=t_sc_header_slider.set)
t_sc_header_slider.grid(column=3, row=1, sticky='NSE')
# Add double click option on entry to open new window with FASTA
t_sc_header.bind('<Double-1>', open_window)
# Add a Delete event for removal of sequences
t_sc_header.bind('<Delete>', lambda e: delete_seq(e))

# Go Button
go_buttonH = ttk.Button(n_headers, text='Go', command=lambda: go_button(True))
go_buttonH.grid(column=3, row=2, rowspan=1000, sticky='NSE')
go_buttonH.state(['disabled'])

# Sequences tab
sc_notebook.add(n_seqs, text='Sequences')
seq_label = StringVar(value='Please select a file')
seq_head_label = ttk.Label(n_seqs, textvariable=seq_label)
seq_head_label.grid(column=0, columnspan=4, row=0, sticky='NW', ipadx=5)
t_sc_seq = ttk.Treeview(n_seqs, columns=('h', 'sc'))
t_sc_seq.heading('#0', text='#', command=lambda: sort_tree(t_sc_seq, '#0', 'int'))
t_sc_seq.column('#0', width=50, stretch=False)
t_sc_seq.heading('h', text='Header', command=lambda: sort_tree(t_sc_seq, 'h', 'str'))
t_sc_seq.heading('sc', text='Special Characters')
t_sc_seq.column('sc', width=0)
t_sc_seq.grid(column=0, columnspan=4, row=1, sticky='NSEW')
# Add a slider to the right
t_sc_seq_slider = ttk.Scrollbar(n_seqs, orient=VERTICAL, command=t_sc_seq.yview)
t_sc_seq.configure(yscrollcommand=t_sc_seq_slider.set)
t_sc_seq_slider.grid(column=3, row=1, sticky='NSE')
# Add double click option on entry to open new window with FASTA
t_sc_seq.bind('<Double-1>', open_window)
# Add a Delete event for removal of sequences
t_sc_seq.bind('<Delete>', lambda e: delete_seq(e))

# Go Button
go_buttonS = ttk.Button(n_seqs, text='Go', command=lambda: go_button(False))
go_buttonS.grid(column=3, row=2, rowspan=1000, sticky='NSE')
go_buttonS.state(['disabled'])

sc_frame.grid_remove()

# ----- Similarity Frame -----------------------------------------------------------------------------------------------
sim_frame = Frame(mainframe, borderwidth=2, relief='groove')
sim_frame.grid(column=1, columnspan=2, row=1, sticky='nsew', padx=7)
sim_frame.grid_rowconfigure(1, weight=1)
sim_frame.grid_columnconfigure(0, weight=1)
sim_frame.grid_propagate(False)
#
sim_message = ttk.Label(sim_frame,
                        text='Grouping very similar strings may take a while, so please press the Run'
                             ' button whenever you wish to run the analysis.')
sim_message.grid(column=0, row=0, sticky='nw')
sim_frame.bind('<Configure>', update_sim_message)
#
run_button = ttk.Button(sim_frame, text='Run', command=lambda: fill_similarity_tree(0.95))
run_button.grid(column=1, row=0, sticky='ns')
#
t_sim = ttk.Treeview(sim_frame, columns='h')
t_sim.heading('#0', text='#')
t_sim.column('#0', width=50, stretch=False)
t_sim.heading('h', text='Header')
# Add a slider to the right
t_sim_slider = ttk.Scrollbar(sim_frame, orient=VERTICAL, command=t_sim.yview)
t_sim.configure(yscrollcommand=t_sim_slider.set)
t_sim_slider.grid(column=1, row=1, sticky='NSE')

t_sim.state(['disabled'])
t_sim.grid(column=0, columnspan=2, row=1, sticky='nsew')

# Add double click option on entry to open new window with FASTA
t_sim.bind('<Double-1>', open_window)
# Add a Delete event for removal of sequences
t_sim.bind('<Delete>', lambda e: delete_seq(e))

sim_frame.grid_remove()

# ----- ORF2HMMER Frame ------------------------------------------------------------------------------------------------
o2h_frame = Frame(mainframe, borderwidth=2, relief='groove')
o2h_frame.grid(column=1, columnspan=2, row=1, sticky='nsew', padx=7)

o2h_frame.grid_remove()

# ----- Renamer Frame --------------------------------------------------------------------------------------------------
rnmr_frame = Frame(mainframe, borderwidth=2, relief='groove')
rnmr_frame.grid(column=1, columnspan=2, row=1, sticky='nsew', padx=7)
rnmr_frame.grid_rowconfigure(1, weight=1)
rnmr_frame.grid_columnconfigure(0, weight=1)
rnmr_frame.grid_propagate(False)
#
rnmr_label = StringVar(value='Configuration file:')
rnmr_message = ttk.Label(rnmr_frame, textvariable=rnmr_label, width=100)
rnmr_message.grid(column=0, row=0, sticky='nw')
rnmr_frame.bind('<Configure>', update_sim_message)
#
load_rnmr_button = ttk.Button(rnmr_frame, text='Load', command=load_configure)
load_rnmr_button.grid(column=2, row=0, sticky='nws')

rnmr_frame.grid_remove()

# ----- File Comparison Frame ------------------------------------------------------------------------------------------
comp_frame = Frame(mainframe, borderwidth=2, relief='groove')
comp_frame.grid(column=1, columnspan=2, row=1, sticky='nsew', padx=7)
comp_frame.grid_rowconfigure(3, weight=1)
comp_frame.grid_columnconfigure(2, weight=1)
comp_frame.grid_propagate(False)

# Very first message (reminder)
comp_message = ttk.Label(comp_frame, text='Select another file for comparison:')
comp_message.grid(column=0, row=0, sticky='nw')

# Shows current loaded b_file
b_file = StringVar(value='')
comp_file_message = ttk.Label(comp_frame, textvariable=b_file)
comp_file_message.grid(column=0, columnspan=4, row=1, sticky='nw')

# Button to update b_file
comp_load = ttk.Button(comp_frame, text='Load', command=load_b_file)
comp_load.grid(column=3, row=1, sticky='nse')

# Combobox for what comparison to make
comp_file_select = ttk.Combobox(comp_frame, values=('A (Only in Current File)', 'B (Only in Other File)',
                                                    'C (Present in Both)', 'A + B'), state='readonly')
comp_file_select.grid(column=0, row=2, sticky='nsew')
# Combobox for what action to take for a given comparison
comp_file_action = ttk.Combobox(comp_frame, values=('Move', 'Copy', 'Treeview'), state='readonly')
comp_file_action.grid(column=1, row=2, sticky='nsew')
# Entry field to a possible Move or Copy action
comp_file_entry = ttk.Entry(comp_frame)
comp_file_entry.grid(column=2, row=2, sticky='nsew')
# The Go Button for running the above selected options
comp_file_go = ttk.Button(comp_frame, text='Go', command=lambda: comp_lst.run(b_file.get()).action())
comp_file_go.grid(column=3, row=2, sticky='nsew')

# t_comp is a Treeview for looking at the comparison of files
#       Shown           |     Hidden
# #A    #B    Header    |    Sequence
t_comp = ttk.Treeview(comp_frame, columns=('#b', 'h'))
t_comp.heading('#0', text='#A', command=lambda: sort_tree(t_comp, '#0', 'int'))
t_comp.column('#0', width=50, stretch=False)
t_comp.heading('#b', text='#B', command=lambda: sort_tree(t_comp, '#b', 'int'))
t_comp.column('#b', width=50, stretch=False)
t_comp.heading('h', text='Header', command=lambda: sort_tree(t_comp, 'h', 'str'))
t_comp.grid(column=0, columnspan=4, row=3, sticky='nsew')

# Add the classic slider
t_comp_slider = ttk.Scrollbar(comp_frame, orient=VERTICAL, command=t_comp.yview)
t_comp.configure(yscrollcommand=t_comp_slider.set)
# One column in so it doesn't stick-out
t_comp_slider.grid(column=3, row=3, sticky='NSE')

comp_frame.grid_remove()
# ----------------------------------------------------------------------------------------------------------------------

root.update_idletasks()
root.minsize(WINDOW_WIDTH, WINDOW_HEIGHT)

root.mainloop()
