from tkinter import *
from tkinter import messagebox

from connection_mgmt import Connection
from protocols import Protocol


PAD_X = 5
PAD_Y = 5
BACKGROUND_COLOR = "gray12"
FEATURE_BACKGROUND_COLOR = "gray25"
FONT = ("Helvetica", 12)
FONT_COLOR = "gray99"
HIGHLIGHT_COLOR = "gray"
HIGHLIGHT_THICKNESS = 2

root = Tk()
root.title("Remote Connection Manager")

main_frame = Frame(bg=BACKGROUND_COLOR, highlightbackground=HIGHLIGHT_COLOR, relief=RAISED)

title = Label(main_frame, text="Connections", bg=BACKGROUND_COLOR, fg=FONT_COLOR, font='Helvetica 12 bold')

connection_list = Listbox(main_frame, bg=FEATURE_BACKGROUND_COLOR, fg=FONT_COLOR, selectmode=SINGLE)

connect_button = Button(main_frame, text="Connect", activebackground=HIGHLIGHT_COLOR, bg=BACKGROUND_COLOR, fg=FONT_COLOR, font=FONT, 
                        highlightbackground=BACKGROUND_COLOR, highlightthickness=HIGHLIGHT_THICKNESS, overrelief="raised")

add_button = Button(main_frame, text="Add", activebackground=HIGHLIGHT_COLOR, bg=BACKGROUND_COLOR, fg=FONT_COLOR, font=FONT, 
                        highlightbackground=BACKGROUND_COLOR, highlightthickness=HIGHLIGHT_THICKNESS, overrelief="raised")

edit_button = Button(main_frame, text="Edit", activebackground=HIGHLIGHT_COLOR, bg=BACKGROUND_COLOR, fg=FONT_COLOR, font=FONT, 
                        highlightbackground=BACKGROUND_COLOR, highlightthickness=HIGHLIGHT_THICKNESS, overrelief="raised")

remove_button = Button(main_frame, text="Remove", activebackground=HIGHLIGHT_COLOR, bg=BACKGROUND_COLOR, fg=FONT_COLOR, font=FONT, 
                        highlightbackground=BACKGROUND_COLOR, highlightthickness=HIGHLIGHT_THICKNESS, overrelief="raised")

main_frame.grid(row=0, column=0, padx=PAD_X, pady=PAD_Y, ipadx=PAD_X, ipady=PAD_Y, sticky="nswe")

title.grid(column=0, row=0, padx=PAD_X, pady=PAD_Y, columnspan=4)

connection_list.grid(column=0, row=1, columnspan=4, padx=PAD_X, pady=PAD_Y, sticky='nswe')

connect_button.grid(column=0, row=2, padx=PAD_X, pady=PAD_Y, sticky='sw')
add_button.grid(column=1, row=2, padx=PAD_X, pady=PAD_Y, sticky='s')
edit_button.grid(column=2, row=2, padx=PAD_X, pady=PAD_Y, sticky='s')
remove_button.grid(column=3, row=2, padx=PAD_X, pady=PAD_Y, sticky='se')

root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

main_frame.columnconfigure((0,1,2,3), weight=1)
main_frame.rowconfigure(1, weight=1)

title.columnconfigure(0, weight=1)
title.rowconfigure(0, weight=1)

connection_list.columnconfigure(0, weight=1)
connection_list.rowconfigure(0, weight=1)


def connect_connection(arg):
    selection = connection_list.curselection()
    if not selection:
        return
    
    selection = selection[0]
    selection = connection_list.get(selection)
    selections = Connection.load_connections()
    if not selections:
        return
    selections = [x for x in selections if x.name == selection]
    if len(selections) > 1:
        raise RuntimeError(f"Multiple connections found for {selection}")
    selections[0].connect()


added_connection_settings = {}
added_gui = None
selected_protocol = StringVar(value="")
def add_connection(arg, connection: Connection = None):
    global added_gui, selected_protocol
    if connection:
        added_connection_settings['old_connection'] = connection.name
    else:
        added_connection_settings['old_connection'] = None

    added_gui = Toplevel(root)    
    added_gui.title("Add Connection")
    added_gui.geometry("250x250")
    
    new_frame = Frame(added_gui, bg=BACKGROUND_COLOR)
    new_frame.grid(row=0, column=0, sticky="nswe")
    for prop_index, prop in enumerate(["name", "address", "username"]):
        
        label = Label(new_frame, bg=BACKGROUND_COLOR, fg=FONT_COLOR, text=f'{prop.title()}:', padx=PAD_X, pady=PAD_Y)
        label.grid(column=0, row=prop_index*2, columnspan=2, padx=PAD_X, pady=PAD_Y, sticky='w')
        
        entry = Entry(new_frame, bg=FEATURE_BACKGROUND_COLOR, fg=FONT_COLOR)
        if connection:
            entry.insert(0, connection.to_json()[prop])
            
        entry.grid(column=2, row=prop_index*2, columnspan=3, padx=PAD_X, pady=PAD_Y)
        added_connection_settings[prop] = entry

    label = Label(new_frame, bg=BACKGROUND_COLOR, fg=FONT_COLOR, text=f'Protocol:', padx=PAD_X, pady=PAD_Y)
    label.grid(column=0, row=9, columnspan=2, padx=PAD_X, pady=PAD_Y, sticky='w')

    for protocol_index, protocol in enumerate([x for x in Protocol]):
        opt = Radiobutton(new_frame, text=protocol.name, variable=selected_protocol, value=protocol.name, bg=FEATURE_BACKGROUND_COLOR, fg=BACKGROUND_COLOR)  
        opt.grid(column=protocol_index+1, row=10, padx=PAD_X)
        opt.select()
        
        if connection:
            if connection.protocol == protocol:
                opt.select()
                opt.state = "active"        

    submit = Button(new_frame, text='Submit', command=confirm_add_connection, activebackground=HIGHLIGHT_COLOR, bg=BACKGROUND_COLOR, fg=FONT_COLOR, font=FONT, 
        highlightbackground=BACKGROUND_COLOR, highlightthickness=2, overrelief="raised")
    submit.grid(column=1, row=11, columnspan=3, padx=PAD_X, pady=PAD_Y)

    added_gui.rowconfigure(0, weight=1)
    added_gui.columnconfigure(0, weight=1)
    new_frame.columnconfigure((2,3), weight=1)

    

def confirm_add_connection():
    connection_settings = {}
    for prop, entry in added_connection_settings.items():
        if prop == 'old_connection':
            continue
        value = entry.get()
        if len(value) < 1 or not selected_protocol.get():
            messagebox.showerror("Error", "Necessary configuration option missing")
            return
        connection_settings[prop] = value
    connection_settings["protocol"] = [x for x in Protocol if x.name == selected_protocol.get()][0]
    added_gui.destroy()

    Connection.add_connection(Connection(**connection_settings))
    if(connection_settings['name'] != added_connection_settings['old_connection']):
        Connection.remove_connection(added_connection_settings['old_connection'])
    build_connect_list()


def edit_connection(arg):
    if not connection_list.curselection():
        return
    selection = connection_list.get(connection_list.curselection()[0])
    connection = [x for x in Connection.load_connections() if x.name == selection][0]
    if not connection:
        raise RuntimeError(f"Bad list option: {connection_list.curselection()} {selection}")
    add_connection(None, connection)


def remove_connection(arg):
    if not connection_list.curselection():
        return
    selection = connection_list.get(connection_list.curselection()[0])
    confirmation = messagebox.askyesno("Question", f"Are you sure you want to delete {selection}?")
    if confirmation:
        Connection.remove_connection(selection)
        build_connect_list()
    remove_button.overrelief = "raised"


def build_connect_list():
    connections = Connection.load_connections()
    while connection_list.get(0):
        connection_list.delete(0)
    for connection_index, connection in enumerate(connections):
        connection_list.insert(connection_index, connection.name)
    if not connections:
        connection_list.insert(1, "No connections added")


def main():
    build_connect_list()    

    connect_button.bind("<Button-1>", connect_connection)
    add_button.bind("<Button-1>", add_connection)
    edit_button.bind("<Button-1>", edit_connection)
    remove_button.bind("<Button-1>", remove_connection)

    root.focus()
    root.mainloop()


if __name__ == "__main__":
    main()

