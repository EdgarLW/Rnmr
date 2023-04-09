from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from main import parse_fasta
from main import special_chars
from main import validate_seq


def donothing():
    print('Nothing')


def open_file():
    global file
    file = filedialog.askopenfilename()
    global fasta
    fasta = parse_fasta(file)
    global file_label
    file_label.set('Current file: ' + file)
    sc_h_count, sc_s_count = 0, 0
    for entry in fasta.values():
        i, seq, sc_h, sc_s = entry
        if sc_h:
            sc_h_count += 1
        if sc_s:
            sc_s_count += 1
    global head_label
    head_label.set(f'A total of {sc_h_count} headers were detected with special characters!')
    global seq_label
    seq_label.set(f'A total of {sc_s_count} sequences were detected with special characters!')
    update_trees(fasta)


def update_trees(fasta):
    t_overview.delete(*t_overview.get_children())
    t_sc_header.delete(*t_sc_header.get_children())
    t_sc_seq.delete(*t_sc_seq.get_children())
    fasta = fasta.items()
    for header, values in fasta:
        t_overview.insert('', 'end', text=values[0], values=(header, values[1]))
        if values[2]:
            t_sc_header.insert('', 'end', text=values[0], values=(header, values[2]))
        if values[3]:
            t_sc_seq.insert('', 'end', text=values[0], values=(header, values[3]))


def navigate(idxs):
    for idx in idxs:
        if int(idx) == 0:
            overview_frame.grid()
            sc_frame.grid_remove()
        elif int(idx) == 2:
            overview_frame.grid_remove()
            sc_frame.grid()


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
                         command=lambda: save_fasta(values[0], entry.get('1.1', '1.end'), entry.get('2.0', '2.end')))
    save_button.grid(column=0, row=1, pady=7, sticky='NES')

    # Set minimum size
    new_window.update_idletasks()
    new_window.minsize(new_window.winfo_width(), new_window.winfo_height())


def save_fasta(old_header, new_header, seq):
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
    else:
        fasta[header][1] = seq
        fasta[header][2] = special_chars(new_header)
        fasta[header][3] = validate_seq(seq, type='protein')
    update_trees(fasta)


# Initiate
root = Tk()
root.title("Rnmr")

file = ''
fasta = {}

# Set root and mainframe
mainframe = ttk.Frame(root, padding="3 3 12 12")
mainframe.columnconfigure(6, weight=1)
mainframe.rowconfigure(6, weight=1)
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
file_button.grid(column=2, ipadx=6, row=0, sticky='W')

# Listbox for actions
options = ['Overview', 'Tools', '    Special Characters']
optionsvar = StringVar(value=options)
listbox = Listbox(mainframe, listvariable=optionsvar, selectmode='browse')
listbox.grid(column=0, row=0, rowspan=2, sticky='NSW')
# Add select to change the current options
listbox.bind('<<ListboxSelect>>', lambda e: navigate(listbox.curselection()))

# Overview Frame
overview_frame = Frame(mainframe, borderwidth=2, relief='groove', width=475)
overview_frame.grid(column=1, columnspan=2, row=1, sticky='NW', padx=7)
overview_frame.grid_rowconfigure(0, weight=1)
overview_frame.grid_columnconfigure(0, weight=1)
# Overview action
t_overview = ttk.Treeview(overview_frame, columns='header')
t_overview.heading('#0', text='#')
t_overview.column('#0', width=50, anchor='w')
t_overview.heading('header', text='Header')
t_overview.column('header', width=overview_frame['width'])
t_overview.grid(column=0, row=0, sticky='NSE', pady=1)
# Add a slider to the right
t_slider = ttk.Scrollbar(overview_frame, orient=VERTICAL, command=t_overview.yview)
t_overview.configure(yscrollcommand=t_slider.set)
t_slider.grid(column=1, row=0, sticky='NSE')
# Add double click option on entry to open new window with FASTA
t_overview.bind('<Double-1>', open_fasta)

# Special Chars Frame
sc_frame = Frame(mainframe, borderwidth=2, relief='groove', width=600)
sc_frame.grid(column=1, columnspan=2, row=1, sticky='NSEW', padx=7)
sc_frame.grid_rowconfigure(0, weight=1)
sc_frame.grid_columnconfigure(0, weight=1)
# Notebook with Headers and Sequences tabs
sc_notebook = ttk.Notebook(sc_frame)
n_headers = ttk.Frame(sc_notebook)
n_seqs = ttk.Frame(sc_notebook)
sc_notebook.grid(column=0, row=0, columnspan=2, sticky='NEW')
n_headers.grid_rowconfigure(0, weight=1)
n_headers.grid_columnconfigure(0, weight=1)
n_seqs.grid_rowconfigure(0, weight=1)
n_seqs.grid_columnconfigure(0, weight=1)


# Headers tab
sc_notebook.add(n_headers, text='Headers')
head_label = StringVar(value='Please select a file')
sc_head_label = ttk.Label(n_headers, textvariable=head_label)
sc_head_label.grid(column=0, row=0, sticky='NW', ipadx=5)
t_sc_header = ttk.Treeview(n_headers, columns=('h', 'sc'))
t_sc_header.heading('#0', text='#')
t_sc_header.column('#0', width=50, anchor='w')
t_sc_header.heading('h', text='Header')
t_sc_header.column('h', width=322)
t_sc_header.heading('sc', text='Special Characters')
t_sc_header.column('sc', width=150)
t_sc_header.grid(column=0, row=1, sticky='NSEW')
# Add a slider to the right
t_sc_header_slider = ttk.Scrollbar(n_headers, orient=VERTICAL, command=t_sc_header.yview)
t_sc_header.configure(yscrollcommand=t_sc_header_slider.set)
t_sc_header_slider.grid(column=1, row=1, sticky='NSE')
# Add double click option on entry to open new window with FASTA
t_sc_header.bind('<Double-1>', open_fasta)

# Sequences tab
sc_notebook.add(n_seqs, text='Sequences')
seq_label = StringVar(value='Please select a file')
seq_head_label = ttk.Label(n_seqs, textvariable=seq_label)
seq_head_label.grid(column=0, row=0, sticky='NW', ipadx=5)
t_sc_seq = ttk.Treeview(n_seqs, columns=('h', 'sc'))
t_sc_seq.heading('#0', text='#')
t_sc_seq.column('#0', width=50, anchor='w')
t_sc_seq.heading('h', text='Header')
t_sc_seq.column('h', width=322)
t_sc_seq.heading('sc', text='Special Characters')
t_sc_seq.column('sc', width=150)
t_sc_seq.grid(column=0, row=1, sticky='NSEW')
# Add a slider to the right
t_sc_seq_slider = ttk.Scrollbar(n_seqs, orient=VERTICAL, command=t_sc_seq.yview)
t_sc_seq.configure(yscrollcommand=t_sc_seq_slider.set)
t_sc_seq_slider.grid(column=1, row=1, sticky='NSE')
# Add double click option on entry to open new window with FASTA
t_sc_seq.bind('<Double-1>', open_fasta)

sc_frame.grid_remove()

root.update_idletasks()
root.minsize(root.winfo_width(), root.winfo_height())

root.mainloop()
