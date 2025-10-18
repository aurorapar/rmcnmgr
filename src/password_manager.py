import os
import time

from threading import Thread

from tkinter import Toplevel, Label, Entry, Frame, Button, messagebox, END

from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from gui_settings import *


class PasswordManager:

    key_size_bits = 256
    block_size_bits = 128
    encoding = 'UTF-8'

    def __init__(self, parent):
        self.parent = parent
        self.password = None
        self.reset = False
        self.timer_amount = 300
        self.entry = None
        self.password_prompt = None
        self.timer_last_check = time.time()
        self.thread = Thread(target=self.password_clearer, daemon=True)
        self.thread.start()

    def password_clearer(self):

        while True:
            time.sleep(1)
            if self.reset:
                break
            if time.time() - self.timer_last_check >= self.timer_amount:
                self.password = None
                self.entry = None
                self.confirm_entry = None
                self.timer_last_check = time.time()
                if self.password_prompt:
                    self.password_prompt.destroy()
                if self.entry:
                    self.entry.destroy()
                    self.confirm_entry = None

    def get_password(self, arg=None):
        if self.password:
            return self.password

        if self.password_prompt:
            return

        self.password_prompt = Toplevel(self.parent)
        self.password_prompt.title("Enter Password")
        self.password_prompt.geometry("300x150")
        self.password_prompt.bind("<Destroy>", self.reset_password_prompt)

        new_frame = Frame(self.password_prompt, bg=BACKGROUND_COLOR)
        new_frame.grid(row=0, column=0, sticky="nswe")

        label = Label(new_frame, bg=BACKGROUND_COLOR, fg=FONT_COLOR, text=f'Enter Password:', padx=PAD_X, pady=PAD_Y)
        label.grid(column=0, row=0, padx=PAD_X, pady=PAD_Y, sticky='w')

        self.entry = Entry(new_frame, bg=FEATURE_BACKGROUND_COLOR, fg=FONT_COLOR, show="*")
        self.entry.grid(column=1, row=0, padx=PAD_X, pady=PAD_Y)

        confirm_label = Label(new_frame, bg=BACKGROUND_COLOR, fg=FONT_COLOR, text=f'Confirm Password:', padx=PAD_X, pady=PAD_Y)
        confirm_label.grid(column=0, row=1, padx=PAD_X, pady=PAD_Y, sticky='w')

        self.confirm_entry = Entry(new_frame, bg=FEATURE_BACKGROUND_COLOR, fg=FONT_COLOR, show="*")
        self.confirm_entry.grid(column=1, row=1, padx=PAD_X, pady=PAD_Y)

        submit = Button(new_frame, text='Submit', command=self.retrieve_password, activebackground=HIGHLIGHT_COLOR,
                        bg=BACKGROUND_COLOR, fg=FONT_COLOR, font=FONT,
                        highlightbackground=BACKGROUND_COLOR, highlightthickness=2, overrelief="raised")
        submit.grid(column=1, row=3, padx=PAD_X, pady=PAD_Y)

        label2 = Label(new_frame, bg=BACKGROUND_COLOR, fg=FONT_COLOR)
        label2.grid(column=3, row=4, sticky='e')

        self.password_prompt.columnconfigure(0, weight=1)
        self.password_prompt.rowconfigure(0, weight=1)
        new_frame.columnconfigure(3, weight=1)
        new_frame.rowconfigure(4, weight=1)

        self.password_prompt.focus()

    def reset_password_prompt(self, arg):
        self.password_prompt = None
        self.password = None

    def retrieve_password(self):
        if self.entry:
            password = self.entry.get()
            if 15 > len(password) or 64 < len(password):
                messagebox.showerror("Error", "A sane password is between 15 and 64 characters")
            elif password != self.confirm_entry.get():
                messagebox.showerror("Error", "Passwords do not match")
            else:
                self.password = password
                self.timer_last_check = time.time()
                self.password_prompt.destroy()
                self.password_prompt = None
                return
        else:
            messagebox.showerror("Error", "You didn't enter your password!")

    @staticmethod
    def encrypt_data(password, salt, data):
        key = PasswordManager.generate_aes_key(password, salt)
        cipher = Cipher(algorithms.AES(key), modes.CBC(salt))
        encryptor = cipher.encryptor()
        padded_data = PasswordManager.pad_data(data)
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        return encrypted_data

    @staticmethod
    def decrypt_data(password, salt, encrypted_data):
        try:
            key = PasswordManager.generate_aes_key(password, salt)
            cipher = Cipher(algorithms.AES(key), modes.CBC(salt))
            decryptor = cipher.decryptor()
            decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()
            decrypted_data = PasswordManager.unpad_data(decrypted_data)
            return decrypted_data.decode(PasswordManager.encoding)
        except ValueError:
            messagebox.showerror("Error", "Your password was incorrect")
            return None

    @staticmethod
    def generate_aes_key(password, salt):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=int(PasswordManager.key_size_bits / 8),
            salt=salt,
            iterations=1_200_000,
        )

        return kdf.derive(password.encode(PasswordManager.encoding))

    @staticmethod
    def generate_salt():
        return os.urandom(int(PasswordManager.block_size_bits/8))

    @staticmethod
    def pad_data(data):
        padder = padding.PKCS7(PasswordManager.block_size_bits).padder()
        padded_data = padder.update(data.encode(PasswordManager.encoding))
        return padded_data + padder.finalize()

    @staticmethod
    def unpad_data(data):
        unpadder = padding.PKCS7(PasswordManager.block_size_bits).unpadder()
        unpadded_data = unpadder.update(data)
        return unpadded_data + unpadder.finalize()
