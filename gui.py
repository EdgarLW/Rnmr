from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from main import parse_fasta
from main import special_chars
from main import validate_seq


def donothing():
    print('Nothing')


def open_file():
    global file_label
    file = filedialog.askopenfilename()
    file_label.set('Current file: ' + file)
    update_overview(file)
    global head_label
    head_label.set(f'A total of {len(special_chars(file))} headers were detected with special characters!')
    global seq_label
    seq_label.set(f'A total of {len(validate_seq(file, type="protein"))} sequences were detected with special characters!')


def update_overview(file):
    it = parse_fasta(file).items()
    for (header, seq), i in zip(it, range(len(it))):
        t_overview.insert('', 'end', text=i + 1, values=(header, seq))


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

    # Get the item that was clicked
    item_id = event.widget.focus()

    # Get the values of the item
    item = event.widget.item(item_id)
    values = item['values']

    # Create and display the new window
    new_window = Toplevel(root)
    new_window.title(f"{values[0]}")
    newframe = ttk.Frame(new_window, padding="3 3 12 12")
    newframe.grid(column=0, row=0, sticky='NWES')
    new_window.columnconfigure(0, weight=1)
    new_window.rowconfigure(0, weight=1)
    new_window.option_add('**tearOff', FALSE)

    # Add the content inside the new window
    entry = Text(newframe)
    entry.configure()
    entry.insert('1.0', f'>{values[0]}\n{values[1]}')
    entry.grid(column=0, row=0, sticky='NWES')

    # Set minimum size
    new_window.update_idletasks()
    new_window.minsize(new_window.winfo_width(), new_window.winfo_height())



# Initiate
root = Tk()
root.title("Rnmr")

# Set root and mainframe
mainframe = ttk.Frame(root, padding="3 3 12 12")
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
file_button.grid(column=2, ipadx=6, row=0, sticky='NW')

# Listbox for actions
options = ['Overview', 'Tools', '    Special Characters']
optionsvar = StringVar(value=options)
listbox = Listbox(mainframe, listvariable=optionsvar, selectmode='browse')
listbox.grid(column=0, row=0, rowspan=2, sticky='NSW')
# Add select to change the current options
listbox.bind('<<ListboxSelect>>', lambda e: navigate(listbox.curselection()))

# Overview Frame
overview_frame = Frame(mainframe, height=200, borderwidth=2, relief='groove', width=475)
overview_frame.grid(column=1, columnspan=2, row=1, sticky='NSEW', padx=7)
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
sc_frame = Frame(mainframe, height=200, borderwidth=2, relief='groove', width=475)
sc_frame.grid(column=1, columnspan=2, row=1, sticky='NSEW', padx=7)
# Notebook with Headers and Sequences tabs
sc_notebook = ttk.Notebook(sc_frame)
n_headers = ttk.Frame(sc_notebook)
n_seqs = ttk.Frame(sc_notebook)
# Headers tab
sc_notebook.add(n_headers, text='Headers')
head_label = StringVar(value='Please select a file')
sc_head_label = ttk.Label(n_headers, textvariable=head_label, width=89)
sc_head_label.grid(column=0, row=0, sticky='NW')
# Sequences tab
sc_notebook.add(n_seqs, text='Sequences')
seq_label = StringVar(value='Please select a file')
seq_head_label = ttk.Label(n_seqs, textvariable=seq_label, width=89)
seq_head_label.grid(column=0, row=0, sticky='NW')

sc_notebook.grid(column=0, row=0, columnspan=2)


sc_frame.grid_remove()

root.update_idletasks()
root.minsize(root.winfo_width(), root.winfo_height())

root.mainloop()
