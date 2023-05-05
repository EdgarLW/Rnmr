import tkinter.ttk
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from main import parse_fasta
from main import special_chars
from main import validate_seq
from main import parse_single_fasta
from main import group_similar_strings

# Set the minimum size for the window
WINDOW_HEIGHT = 500
WINDOW_WIDTH = 900

# ----- GLOBAL VARIABLES -----
# Base
file = ''
fasta = {}
# Similarity Tool
sim_lst = []

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
        af = fasta
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
                    out += f'{k}\n{v[1]}\n'

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


def donothing():
    print('Nothing')


def open_file():
    global file
    file = filedialog.askopenfilename()
    if file:
        global fasta
        fasta = parse_fasta(file)
        global file_label
        file_label.set('Current file: ' + file)
        update_labels()
        update_trees(fasta)


def update_labels():
    sc_h_count, sc_s_count, dup_count = 0, 0, 0
    for entry in fasta.values():
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


def update_trees(fasta):
    t_overview.delete(*t_overview.get_children())
    t_dup.delete(*t_dup.get_children())
    t_sc_header.delete(*t_sc_header.get_children())
    t_sc_seq.delete(*t_sc_seq.get_children())
    t_sim.delete(*t_sim.get_children())
    for widget in n_headers.winfo_children():
        if isinstance(widget, (ttk.Combobox, ttk.Entry, ttk.Checkbutton)):
            widget.destroy()
    for widget in n_seqs.winfo_children():
        if isinstance(widget, (ttk.Combobox, ttk.Entry, ttk.Checkbutton)):
            widget.destroy()
    fasta = fasta.items()
    for header, values in fasta:
        t_overview.insert('', 'end', text=values[0], values=[header, len(values[1]), values[1]])
        if values[2]:
            t_sc_header.insert('', 'end', text=values[0], values=[header, values[2]])
        if values[3]:
            t_sc_seq.insert('', 'end', text=values[0], values=[header, values[3]])
        if values[4]:
            t_dup.insert('', 'end', text=values[0], values=[header, values[1]])
    t_sc_header_children = t_sc_header.get_children()
    if t_sc_header_children:
        go_buttonH.state(['!disabled'])
        header_children = set()
        for child in t_sc_header_children:
            sc = t_sc_header.item(child)['values'][1]
            sc = set(sc.split(' '))
            for s in sc:
                header_children.add(s)
        for i in range(len(header_children)):
            ttk.Checkbutton(n_headers, text=list(header_children)[i], width=6).grid(column=0, row=i + 2, padx=5, sticky='W')
            ttk.Combobox(n_headers, values=('replace for', 'copy to file', 'move to file'), state='readonly', width=12)\
                .grid(column=1, row=i + 2, sticky='w')
            ttk.Entry(n_headers).grid(column=2, row=i + 2, sticky='we')
    t_sc_seq_children = t_sc_seq.get_children()
    if t_sc_seq_children:
        go_buttonS.state(['!disabled'])
        seq_children = set()
        for child in t_sc_seq_children:
            sc = t_sc_seq.item(child)['values'][1]
            sc = set(sc.split(' '))
            for s in sc:
                seq_children.add(s)
        for i in range(len(seq_children)):
            ttk.Checkbutton(n_seqs, text=list(seq_children)[i]).grid(column=0, row=i + 2)
            ttk.Combobox(n_seqs, values=('replace for', 'copy to file', 'move to file'), state='readonly')\
                .grid(column=1, row=i + 2)
            ttk.Entry(n_seqs).grid(column=2, row=i + 2, sticky='we')


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


def open_fasta(event):
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
    newframe = ttk.Frame(new_window, padding="3 3 7 0")
    newframe.grid(column=0, row=0, sticky='NSEW')
    new_window.option_add('**tearOff', FALSE)

    # Add the content inside the new window
    # Entry (text)
    entry = Text(newframe)
    entry.configure()
    entry.insert('1.0', f'>{values[0]}\n{fasta[values[0]][1]}')
    entry.grid(column=0, row=0, sticky='NSEW')

    # Button for Saving
    save_button = Button(newframe, text='Save', width=10,
                         command=lambda: save_fasta(parse_single_fasta(entry.get('1.0', 'end')),
                                                    window=new_window, save=True))
    save_button.grid(column=0, row=1, pady=7, sticky='NES')

    # Set minimum size
    new_window.update_idletasks()
    new_window.minsize(new_window.winfo_width(), new_window.winfo_height())


def save_fasta(text, window=None, type=None, replace=None, save=False):
    new_header, seq = text
    if window is None:
        if type == 'H':
            old_header = new_header
            new_header = new_header.replace(replace[0], replace[1])
        elif type == 'S':
            old_header = new_header
            seq = seq.replace(replace[0], replace[1])
        else:
            return 'type variable required'
    else:
        old_header = window.title()
    global fasta
    if old_header != new_header:
        new_fasta = {}
        for key, value in fasta.items():
            if value[0] == fasta[old_header][0]:
                new_fasta[new_header] = [value[0],
                                         seq,
                                         special_chars(new_header),
                                         validate_seq(seq, type='protein')]
            else:
                new_fasta[key] = value
        fasta = new_fasta
        if window:
            window.title(f"{new_header}")
    else:
        fasta[old_header][1] = seq
        fasta[old_header][2] = special_chars(new_header)
        fasta[old_header][3] = validate_seq(seq, type='protein')
    if save:
        update_trees(fasta)
        update_labels()


def go_button(type):
    check_list = []
    combo_list = []
    entry_list = []
    if type == 'H':
        notebook = n_headers
    else:
        notebook = n_seqs
    for widget in notebook.winfo_children():
        if isinstance(widget, tkinter.ttk.Checkbutton):
            check_list.append(widget)
        elif isinstance(widget, tkinter.ttk.Combobox):
            combo_list.append(widget)
        elif isinstance(widget, tkinter.ttk.Entry):
            entry_list.append(widget)
    children = []
    for check, choice, text in zip(check_list, combo_list, entry_list):
        if check.state() == ('selected',):
            if type == 'H':
                t = t_sc_header
                t_children = t_sc_header.get_children()
            else:
                t = t_sc_seq
                t_children = t_sc_seq.get_children()
            for child in t_children:
                children.append(t.item(child)['values'][0])
            if choice.current() == 0:
                for child in children:
                    seq = fasta[child][1]
                    rep = str(check.cget('text'))
                    if rep == 'Space':
                        rep = ' '
                    save_fasta((child, seq), type=type, replace=(rep, text.get()))
            elif choice.current() == 1:
                out = ''
                for child in children:
                    out += f'>{child}\n{fasta[child][1]}\n'
                with open(text.get(), 'a') as file:
                    file.write(out)
            elif choice.current() == 2:
                out = ''
                for child in children:
                    out += f'>{child}\n{fasta[child][1]}\n'
                    fasta.pop(child)
                with open(text.get(), 'a') as file:
                    file.write(out)
    update_trees(fasta)
    update_labels()


def delete_seq(tree, event):
    # Check for content inside Treeview before opening new window
    if not event.widget.selection():
        return

    global fasta
    global sim_lst

    # Get a list of the widgets children and then the index number of the selected item
    tree_children = tree.get_children()
    item_idx = tree_children.index(event.widget.focus())

    # Get the item that was clicked
    item_id = event.widget.focus()

    # Get the values of the item
    item = event.widget.item(item_id)
    header = item['values'][0]
    fasta.pop(header)
    for lst in sim_lst:
        try:
            lst.remove(header)
        except KeyError:
            pass

    # Update the trees and labels
    update_labels()
    update_trees(fasta)
    fill_similarity_tree(0.5)

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


def update_sim_message(event):
    if not event:
        return
    col_width = sim_frame.grid_bbox(0, 0)[2]
    sim_message.config(wraplength=col_width)


def fill_similarity_tree(threshold):
    global fasta
    global sim_lst
    if not sim_lst:
        sim_lst = group_similar_strings(fasta.keys(), threshold)
    if sim_lst:
        t_sim.state(['!disabled'])
        for i in range(len(sim_lst)):
            if i != 0:
                t_sim.insert('', 'end', text='---')
            group = sim_lst[i]
            for header in group:
                t_sim.insert('', 'end', text=fasta[header][0], values=(header, fasta[header][1]))
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
menu_file.add_command(label='New', command=donothing)
menu_file.add_command(label='Open...', command=open_file)
menu_file.add_command(label='Save', command=donothing)
menu_file.add_command(label='Save as...', command=donothing)
menu_file.add_separator()
menu_file.add_command(label='Close', command=root.quit)
# Edit (Menu)
menu_edit = Menu(menubar, tearoff=0)
menubar.add_cascade(menu=menu_edit, label='Edit')
menu_edit.add_command(label='Select', command=donothing)
menu_edit.add_command(label='Select all', command=donothing)
menu_edit.add_separator()
menu_edit.add_command(label='Copy', command=donothing)
menu_edit.add_command(label='Cut', command=donothing)
menu_edit.add_command(label='Paste', command=donothing)
menu_edit.add_command(label='Delete', command=donothing)
menu_edit.add_separator()
menu_edit.add_command(label='Undo', command=donothing)
menu_edit.add_command(label='Redo', command=donothing)

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
t_overview.heading('#0', text='#')
t_overview.column('#0', width=50, anchor='w', stretch=False)
t_overview.heading('header', text='Header')
t_overview.column('header', anchor='w')
t_overview.heading('length', text='Length')
t_overview.column('length', anchor='w')
t_overview.grid(column=0, row=0, sticky='NSEW', pady=1)
# Add a slider to the right
t_slider = ttk.Scrollbar(overview_frame, orient=VERTICAL, command=t_overview.yview)
t_overview.configure(yscrollcommand=t_slider.set)
t_slider.grid(column=1, row=0, sticky='NSE')
# Add double click option on entry to open new window with FASTA
t_overview.bind('<Double-1>', open_fasta)
# Add a Delete event for removal of sequences
t_overview.bind('<Delete>', lambda e: delete_seq(t_overview, e))

# We start at the overview, so no need to grid_remove

# ----- Duplicates Frame -----------------------------------------------------------------------------------------------
dup_frame = Frame(mainframe, borderwidth=2, relief='groove')
dup_frame.grid(column=1, columnspan=2, row=1, sticky='nsew', padx=7)
dup_frame.grid_rowconfigure(1, weight=1)
dup_frame.grid_columnconfigure(0, weight=1)
dup_frame.grid_propagate(False)
#
dup_label = StringVar(value='Please select a file')
dup_dup_label = ttk.Label(dup_frame, textvariable=dup_label)
dup_dup_label.grid(column=0, columnspan=4, row=0, sticky='nw', ipadx=5)
#
t_dup = ttk.Treeview(dup_frame, columns='h')
t_dup.heading('#0', text='#')
t_dup.column('#0', width=50, stretch=False)
t_dup.heading('h', text='Header')
t_dup.grid(column=0, columnspan=4, row=1, sticky='nsew')
#
t_dup_slider = ttk.Scrollbar(dup_frame, orient=VERTICAL, command=t_dup.yview)
t_dup.configure(yscrollcommand=t_dup_slider.set)
t_dup_slider.grid(column=1, row=1, sticky='nse')
# Add double click option on entry to open new window with FASTA
t_dup.bind('<Double-1>', open_fasta)
# Add a Delete event for removal of sequences
t_dup.bind('<Delete>', lambda e: delete_seq(t_dup, e))

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
t_sc_header.heading('#0', text='#')
t_sc_header.column('#0', width=50, stretch=False)
t_sc_header.heading('h', text='Header')
t_sc_header.heading('sc', text='Special Characters')
t_sc_header.column('sc', width=0)
t_sc_header.grid(column=0, columnspan=4, row=1, sticky='NSEW')
# Add a slider to the right
t_sc_header_slider = ttk.Scrollbar(n_headers, orient=VERTICAL, command=t_sc_header.yview)
t_sc_header.configure(yscrollcommand=t_sc_header_slider.set)
t_sc_header_slider.grid(column=3, row=1, sticky='NSE')
# Add double click option on entry to open new window with FASTA
t_sc_header.bind('<Double-1>', open_fasta)

# Go Button
go_buttonH = ttk.Button(n_headers, text='Go', command=lambda: go_button('H'))
go_buttonH.grid(column=3, row=2, rowspan=1000, sticky='NSE')
go_buttonH.state(['disabled'])

# Sequences tab
sc_notebook.add(n_seqs, text='Sequences')
seq_label = StringVar(value='Please select a file')
seq_head_label = ttk.Label(n_seqs, textvariable=seq_label)
seq_head_label.grid(column=0, columnspan=4, row=0, sticky='NW', ipadx=5)
t_sc_seq = ttk.Treeview(n_seqs, columns=('h', 'sc'))
t_sc_seq.heading('#0', text='#')
t_sc_seq.column('#0', width=50, stretch=False)
t_sc_seq.heading('h', text='Header')
t_sc_seq.heading('sc', text='Special Characters')
t_sc_seq.column('sc', width=0)
t_sc_seq.grid(column=0, columnspan=4, row=1, sticky='NSEW')
# Add a slider to the right
t_sc_seq_slider = ttk.Scrollbar(n_seqs, orient=VERTICAL, command=t_sc_seq.yview)
t_sc_seq.configure(yscrollcommand=t_sc_seq_slider.set)
t_sc_seq_slider.grid(column=3, row=1, sticky='NSE')
# Add double click option on entry to open new window with FASTA
t_sc_seq.bind('<Double-1>', open_fasta)

# Go Button
go_buttonS = ttk.Button(n_seqs, text='Go', command=lambda: go_button('S'))
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
run_button = ttk.Button(sim_frame, text='Run', command=lambda: fill_similarity_tree(0.5))
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
t_sim.bind('<Double-1>', open_fasta)
# Add a Delete event for removal of sequences
t_sim.bind('<Delete>', lambda e: delete_seq(t_sim, e))

sim_frame.grid_remove()

# ----- ORF2HMMER Frame ------------------------------------------------------------------------------------------------
o2h_frame = Frame(mainframe, borderwidth=2, relief='groove')
o2h_frame.grid(column=1, columnspan=2, row=1, sticky='nsew', padx=7)

o2h_frame.grid_remove()

# ----- Renamer Frame --------------------------------------------------------------------------------------------------
rnmr_frame = Frame(mainframe, borderwidth=2, relief='groove')
rnmr_frame.grid(column=1, columnspan=2, row=1, sticky='nsew', padx=7)

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
t_comp.heading('#0', text='#A')
t_comp.column('#0', width=50, stretch=False)
t_comp.heading('#b', text='#B')
t_comp.column('#b', width=50, stretch=False)
t_comp.heading('h', text='Header')
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
