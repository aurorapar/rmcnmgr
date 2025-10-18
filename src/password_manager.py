import os
import time

from threading import Thread

from tkinter import Toplevel, Label, Entry, Frame, Button, messagebox, END

from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from gui_settings import *


class PasswordManager:

    key_size = 256
    block_size = 16
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
                self.timer_last_check = time.time()
                if self.password_prompt:
                    self.password_prompt.destroy()
                if self.entry:
                    self.entry.destroy()

    def get_password(self):
        if self.password:
            return self.password

        if self.password_prompt:
            return

        self.password_prompt = Toplevel(self.parent)
        self.password_prompt.title("Enter Password")
        self.password_prompt.geometry("250x100")

        new_frame = Frame(self.password_prompt, bg=BACKGROUND_COLOR)
        new_frame.grid(row=0, column=0, sticky="nswe")

        label = Label(new_frame, bg=BACKGROUND_COLOR, fg=FONT_COLOR, text=f'Enter Password:', padx=PAD_X, pady=PAD_Y)
        label.grid(column=0, row=0, padx=PAD_X, pady=PAD_Y, sticky='w')

        self.entry = Entry(new_frame, bg=FEATURE_BACKGROUND_COLOR, fg=FONT_COLOR, show="*")
        self.entry.grid(column=1, row=0, padx=PAD_X, pady=PAD_Y)

        submit = Button(new_frame, text='Submit', command=self.retrieve_password, activebackground=HIGHLIGHT_COLOR,
                        bg=BACKGROUND_COLOR, fg=FONT_COLOR, font=FONT,
                        highlightbackground=BACKGROUND_COLOR, highlightthickness=2, overrelief="raised")
        submit.grid(column=1, row=2, padx=PAD_X, pady=PAD_Y)

        label2 = Label(new_frame, bg=BACKGROUND_COLOR, fg=FONT_COLOR)
        label2.grid(column=3, row=3, sticky='e')

        self.password_prompt.columnconfigure(0, weight=1)
        self.password_prompt.rowconfigure(0, weight=1)
        new_frame.columnconfigure(3, weight=1)
        new_frame.rowconfigure(3, weight=1)

        self.password_prompt.focus()

    def retrieve_password(self):
        if self.entry:
            password = self.entry.get()
            if 15 > len(password) or 64 < len(password):
                messagebox.showerror("Error", "A sane password is between 15 and 64 characters")
            else:
                self.password = password
                self.timer_last_check = time.time()
                self.password_prompt.destroy()
                self.password_prompt = None
                return
        else:
            messagebox.showerror("Error", "You didn't enter your password!")

        self.password_prompt.destroy()
        self.password_prompt = None
        self.get_password()

    @staticmethod
    def encrypt_data(password, salt, data):
        key = PasswordManager.generate_aes_key(password, salt)
        cipher = Cipher(algorithms.AES(key), modes.CBC(salt))
        encryptor = cipher.encryptor()
        padded_data = PasswordManager.pad_data(data)
        encrypted_data = encryptor.update(PasswordManager.pad_data(data)) + encryptor.finalize()
        return encrypted_data

    @staticmethod
    def decrypt_data(password, salt, encrypted_data):
        key = PasswordManager.generate_aes_key(password, salt)
        cipher = Cipher(algorithms.AES(key), modes.CBC(salt))
        decryptor = cipher.decryptor()
        unpadded_data = PasswordManager.unpad_data(encrypted_data)
        decrypted_data = decryptor.update(unpadded_data) + decryptor.finalize()
        return decrypted_data.decode(PasswordManager.encoding)

    @staticmethod
    def generate_aes_key(password, salt):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=int(PasswordManager.key_size/8),
            salt=salt,
            iterations=1_200_000,
        )

        return kdf.derive(password.encode(PasswordManager.encoding))

    @staticmethod
    def generate_salt():
        return os.urandom(PasswordManager.block_size)

    @staticmethod
    def pad_data(data):
        padder = padding.PKCS7(PasswordManager.block_size).padder()
        padded_data = padder.update(data.encode(PasswordManager.encoding))
        return padded_data + padder.finalize()

    @staticmethod
    def unpad_data(data):
        unpadder = padding.PKCS7(PasswordManager.block_size).unpadder()
        unpadded_data = unpadder.update(data)
        return unpadded_data + unpadder.finalize()
