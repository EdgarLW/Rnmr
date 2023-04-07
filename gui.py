from tkinter import *
from tkinter import ttk
from tkinter import filedialog


def donothing():
    print('Nothing')


def open_file():
    global file_path
    file_path.set(filedialog.askopenfilename())


root = Tk()
root.title("Rnmr")

mainframe = ttk.Frame(root, padding="3 3 12 12")
mainframe.grid(column=0, row=0, sticky='NWES')
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
root.option_add('**tearOff', FALSE)

menubar = Menu(root)
root['menu'] = menubar

menu_file = Menu(menubar, tearoff=0)
menubar.add_cascade(menu=menu_file, label='File')
menu_file.add_command(label='New', command=donothing)
menu_file.add_command(label='Open...', command=open_file)
menu_file.add_command(label='Save', command=donothing)
menu_file.add_command(label='Save as...', command=donothing)
menu_file.add_separator()
menu_file.add_command(label='Close', command=root.quit)

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


file_path = StringVar()
file_path.set(f'No file selected')
label = ttk.Label(mainframe, textvariable=file_path)
label.grid()

root.mainloop()
