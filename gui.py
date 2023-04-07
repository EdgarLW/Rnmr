from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from main import parse_fasta


def donothing():
    print('Nothing')


def open_file():
    global file_path
    filename = filedialog.askopenfilename()
    file_path.set(filename)
    update_tree(filename)


def update_tree(file):
    for header, seq in parse_fasta(file).items():
        t_special_chars.insert('', 'end', text=header, values=seq)


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
top_label = ttk.Label(mainframe, text='Current file:')
top_label.grid(column=0, padx=2, row=0)

# Filename loaded
file_frame = ttk.Frame(mainframe)
file_frame.grid(column=1, ipadx=80, row=0, sticky='W')
file_path = StringVar()
filename = ttk.Label(file_frame, textvariable=file_path)
filename.grid(sticky='W')

# Button to load file
file_button = Button(mainframe, text='Load', command=open_file)
file_button.grid(column=2, ipadx=6, row=0)

# Notebook for actions
notebook = ttk.Notebook(mainframe)
p_special_chars = ttk.Frame(notebook)
notebook.add(p_special_chars, text='Special Characters')
p_dup_seqs = ttk.Frame(notebook)
notebook.add(p_dup_seqs, text='Duplicates')
notebook.grid(column=1, row=1)

# Tree inside p_special_chars
t_special_chars = ttk.Treeview(p_special_chars, columns=('Sequence', 'Special Characters'), )
t_special_chars.heading('#0', text='Header')
t_special_chars.heading('Sequence', text='Sequence')
t_special_chars.heading('Special Characters', text='Special Characters')
t_special_chars.grid(ipadx=80)


root.mainloop()
