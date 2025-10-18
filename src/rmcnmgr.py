import hashlib
import time

from threading import Thread

from tkinter import *
from tkinter import messagebox

from connection_mgmt import Connection, CONNECTION_FILE
from gui_settings import *
from password_manager import PasswordManager
from protocols import Protocol


root = Tk()
root.title("Remote Connection Manager")


class Gui(Frame):

    prompted_values = ['name', 'address', 'username']

    def __init__(self, parent, password_manager):
        super().__init__(bg=BACKGROUND_COLOR, highlightbackground=HIGHLIGHT_COLOR, relief=RAISED)

        self.password_manager = password_manager

        self.title = Label(self, text="Connections", bg=BACKGROUND_COLOR, fg=FONT_COLOR, font='Helvetica 12 bold')

        self.connection_list = Listbox(self, bg=FEATURE_BACKGROUND_COLOR, fg=FONT_COLOR, selectmode=SINGLE)

        self.pw_button = Button(self, text="Enter Password", activebackground=HIGHLIGHT_COLOR, bg=FEATURE_BACKGROUND_COLOR,
                                     fg=FONT_COLOR, font=FONT, width=BUTTON_WIDTH,
                                     highlightbackground=BACKGROUND_COLOR, highlightthickness=HIGHLIGHT_THICKNESS,
                                     overrelief="raised")

        self.connect_button = Button(self, text="Connect", activebackground=HIGHLIGHT_COLOR, bg=FEATURE_BACKGROUND_COLOR,
                                fg=FONT_COLOR, font=FONT, width=BUTTON_WIDTH,
                                highlightbackground=BACKGROUND_COLOR, highlightthickness=HIGHLIGHT_THICKNESS,
                                overrelief="raised")

        self.add_button = Button(self, text="Add Connection", activebackground=HIGHLIGHT_COLOR, bg=FEATURE_BACKGROUND_COLOR,
                            fg=FONT_COLOR, font=FONT, width=BUTTON_WIDTH,
                            highlightbackground=BACKGROUND_COLOR, highlightthickness=HIGHLIGHT_THICKNESS,
                            overrelief="raised")

        self.edit_button = Button(self, text="Edit Connection", activebackground=HIGHLIGHT_COLOR, bg=FEATURE_BACKGROUND_COLOR,
                             fg=FONT_COLOR, font=FONT, width=BUTTON_WIDTH,
                             highlightbackground=BACKGROUND_COLOR, highlightthickness=HIGHLIGHT_THICKNESS,
                             overrelief="raised")

        self.remove_button = Button(self, text="Remove Connection", activebackground=HIGHLIGHT_COLOR, bg=FEATURE_BACKGROUND_COLOR,
                               fg=FONT_COLOR, font=FONT, width=BUTTON_WIDTH,
                               highlightbackground=BACKGROUND_COLOR, highlightthickness=HIGHLIGHT_THICKNESS,
                               overrelief="raised")

        self.grid(row=0, column=0, padx=PAD_X, pady=PAD_Y, ipadx=PAD_X, ipady=PAD_Y, sticky="nswe")

        self.title.grid(column=0, row=0, padx=PAD_X, pady=PAD_Y, columnspan=4)

        self.connection_list.grid(column=0, row=1, columnspan=4, padx=PAD_X, pady=PAD_Y, sticky='nswe')

        self.connect_button.grid(column=0, row=2, padx=PAD_X, pady=PAD_Y, sticky='sw')
        self.pw_button.grid(column=3, row=2, columnspan=4, padx=PAD_X, pady=PAD_Y, sticky='se')
        self.add_button.grid(column=0, row=3, padx=PAD_X, pady=PAD_Y, sticky='sw')
        self.edit_button.grid(column=3, row=3, padx=PAD_X, pady=PAD_Y, sticky='se')
        self.remove_button.grid(column=0, row=4, columnspan=4, padx=PAD_X, pady=PAD_Y, sticky='sw')

        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        self.columnconfigure((0, 1, 2, 3), weight=1)
        self.rowconfigure(1, weight=1)

        self.title.columnconfigure(0, weight=1)
        self.title.rowconfigure(0, weight=1)

        self.connection_list.columnconfigure(0, weight=1)
        self.connection_list.rowconfigure(0, weight=1)

        self.pw_button.bind("<Button-1>", self.password_manager.get_password)
        self.connect_button.bind("<Button-1>", self.connect_connection)
        self.add_button.bind("<Button-1>", self.create_new_connection)
        self.edit_button.bind("<Button-1>", self.edit_connection)
        self.remove_button.bind("<Button-1>", self.remove_connection)

        self.file_hash = self.retrieve_file_hash()

    def connect_connection(self, arg):
        if not self.password_manager.password:
            messagebox.showerror("Error", "You must enter a password first!")
            return

        selection = self.connection_list.curselection()
        if not selection:
            return

        selection = selection[0]
        selection = self.connection_list.get(selection)
        selections = Connection.load_connections(self.password_manager)
        if not selections:
            return
        selections = [x for x in selections if x.name == selection]
        if len(selections) > 1:
            raise RuntimeError(f"Multiple connections found for {selection}")
        selections[0].connect()

    def create_new_connection(self, arg, connection: Connection = None):
        if not self.password_manager.password:
            messagebox.showerror("Error", "You must enter a password first!")
            return

        self.added_gui = Toplevel(root)
        self.added_gui.title("Add Connection")
        self.added_gui.geometry("250x250")

        new_frame = Frame(self.added_gui, bg=BACKGROUND_COLOR)
        new_frame.grid(row=0, column=0, sticky="nswe")

        self.entries = {'protocol': StringVar(value=""), 'salt': None}
        self.previous_connection = connection
        if self.previous_connection:
            self.entries['salt'] = self.previous_connection.salt
        else:
            self.entries['salt'] = PasswordManager.generate_salt()

        for prop_index, prop in enumerate(Gui.prompted_values):

            label = Label(new_frame, bg=BACKGROUND_COLOR, fg=FONT_COLOR, text=f'{prop.title()}:', padx=PAD_X, pady=PAD_Y)
            label.grid(column=0, row=prop_index*2, columnspan=2, padx=PAD_X, pady=PAD_Y, sticky='w')

            entry = Entry(new_frame, bg=FEATURE_BACKGROUND_COLOR, fg=FONT_COLOR)
            if connection:
                entry.insert(0, connection.__getattribute__(prop))
            self.entries[prop] = entry

            entry.grid(column=2, row=prop_index*2, columnspan=3, padx=PAD_X, pady=PAD_Y)

        label = Label(new_frame, bg=BACKGROUND_COLOR, fg=FONT_COLOR, text=f'Protocol:', padx=PAD_X, pady=PAD_Y)
        label.grid(column=0, row=9, columnspan=2, padx=PAD_X, pady=PAD_Y, sticky='w')

        for protocol_index, protocol in enumerate([*Protocol]):
            opt = Radiobutton(new_frame, text=protocol.name, variable=self.entries['protocol'], value=protocol.name, bg=FEATURE_BACKGROUND_COLOR, fg=BACKGROUND_COLOR)
            opt.grid(column=protocol_index+1, row=10, padx=PAD_X)

            if connection:
                if connection.protocol == protocol:
                    opt.select()
                    opt.state = "active"
            else:
                opt.select()

        submit = Button(new_frame, text='Submit', command=self.confirm_add_connection, activebackground=HIGHLIGHT_COLOR, bg=BACKGROUND_COLOR, fg=FONT_COLOR, font=FONT,
            highlightbackground=BACKGROUND_COLOR, highlightthickness=2, overrelief="raised")
        submit.grid(column=1, row=11, columnspan=3, padx=PAD_X, pady=PAD_Y)

        self.added_gui.rowconfigure(0, weight=1)
        self.added_gui.columnconfigure(0, weight=1)
        new_frame.columnconfigure((2,3), weight=1)

    def confirm_add_connection(self):
        connection_settings = {}
        for prop in Gui.prompted_values:
            entry = self.entries[prop]
            value = entry.get()
            if len(value) < 1 or not self.entries['protocol'].get() or not self.entries['salt']:
                messagebox.showerror("Error", "Necessary configuration option missing")
                return
            connection_settings[prop] = value
        connection_settings["protocol"] = [p for p in Protocol if p.name == self.entries['protocol'].get()][0]
        connection_settings["salt"] = self.entries['salt']
        self.added_gui.destroy()

        new_connection = Connection(**connection_settings)
        Connection.add_connection(self.password_manager, new_connection)
        if self.previous_connection and self.previous_connection.name != new_connection.name:
            Connection.remove_connection(self.password_manager, self.previous_connection.name)
            self.previous_connection = None

    def edit_connection(self, arg):
        if not self.password_manager.password:
            messagebox.showerror("Error", "You must enter a password first!")
            return

        if not self.connection_list.curselection():
            return

        selection = self.connection_list.get(self.connection_list.curselection()[0])
        if selection == "No connections added":
            return
        connection = [x for x in Connection.load_connections(self.password_manager) if x.name == selection][0]
        if not connection:
            raise RuntimeError(f"Bad list option: {self.connection_list.curselection()} {selection}")
        self.create_new_connection(None, connection)

    def remove_connection(self, arg):
        if not self.password_manager.password:
            messagebox.showerror("Error", "You must enter a password first!")
            return

        if not self.connection_list.curselection():
            return

        selection = self.connection_list.get(self.connection_list.curselection()[0])
        confirmation = messagebox.askyesno("Question", f"Are you sure you want to delete {selection}?")
        if confirmation:
            Connection.remove_connection(self.password_manager, selection)

    def build_connection_list(self):
        connections = Connection.load_connections(self.password_manager)
        if not connections:
            return
        while self.connection_list.get(0):
            self.connection_list.delete(0)
        for connection_index, connection in enumerate(connections):
            self.connection_list.insert(connection_index, connection.name)
        if not connections:
            self.connection_list.insert(1, "No connections added")

    def retrieve_file_hash(self):
        with open(CONNECTION_FILE, 'rb') as f:
            return hashlib.file_digest(f, "sha256").hexdigest()


def file_hash_updater(gui):
    password_updated = False
    while True:
        if not gui.password_manager.password:
            continue

        if not password_updated:
            gui.build_connection_list()
            password_updated = True
            continue

        current_hash = gui.retrieve_file_hash()

        if current_hash == gui.file_hash:
            continue
        gui.file_hash = current_hash

        gui.build_connection_list()

        time.sleep(1)


def main():
    password_manager = PasswordManager(root)
    gui = Gui(root, password_manager)
    password_manager.get_password()

    update_list_thread = Thread(target=file_hash_updater, args=(gui,), daemon=True)
    update_list_thread.start()

    root.focus()
    root.mainloop()

    gui.password_manager.reset = True


if __name__ == "__main__":
    main()

