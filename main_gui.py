import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from tkinter import Scale, HORIZONTAL, Checkbutton
import tkinterdnd2 as TkinterDnD
from PIL import Image, ImageTk
import os
import random
import platform
import subprocess
import wave
import numpy as np
from bitarray import bitarray
import math
import hashlib


class DropZone(tk.Frame):
    def __init__(self, parent, text, callback, file_types=None):
        super().__init__(parent, bg='#e8f4fd', relief=tk.RAISED, bd=2, height=80)
        self.callback = callback
        self.file_types = file_types or []
        self.default_text = text
        self.default_bg = '#e8f4fd'
        self.hover_bg = '#d0e7f7'
        self.drop_bg = '#b8ddf0'
        self.disabled_bg = '#d3d3d3'
        self.is_enabled = True

        self.label = tk.Label(self, text=text, bg=self.default_bg,
                              font=('Helvetica', 10), wraplength=300)
        self.label.pack(expand=True, fill=tk.BOTH)

        self.drop_target_register(TkinterDnD.DND_FILES)
        self.dnd_bind('<<DropEnter>>', self.on_drop_enter)
        self.dnd_bind('<<DropLeave>>', self.on_drop_leave)
        self.dnd_bind('<<Drop>>', self.on_drop)

    def on_drop_enter(self, event):
        if self.is_enabled:
            self.configure(bg=self.hover_bg)
            self.label.configure(bg=self.hover_bg)

    def on_drop_leave(self, event):
        if self.is_enabled:
            self.configure(bg=self.default_bg)
            self.label.configure(bg=self.default_bg)

    def on_drop(self, event):
        if not self.is_enabled:
            return
        file_path = event.data.strip('{}')
        if self.file_types:
            if not any(file_path.lower().endswith(ft) for ft in self.file_types):
                messagebox.showerror(
                    "Error", f"Invalid file type. Expected: {', '.join(self.file_types)}")
                return
        self.callback(file_path)
        self.configure(bg=self.drop_bg)
        self.label.configure(bg=self.drop_bg)

    def update_text(self, text):
        self.label.configure(text=text)

    def reset_colors(self):
        self.configure(bg=self.default_bg)
        self.label.configure(bg=self.default_bg)

    def disable(self):
        self.is_enabled = False
        self.configure(bg=self.disabled_bg)
        self.label.configure(bg=self.disabled_bg,
                             text=f"{self.default_text}\n(Disabled)")

    def enable(self):
        self.is_enabled = True
        self.configure(bg=self.default_bg)
        self.label.configure(bg=self.default_bg, text=self.default_text)


class StegApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title(
            "LSB Steganography Tool - Enhanced GUI with Audio & Text Support")
        self.geometry("1200x900")
        self.configure(bg='#f5f5f5')

        # Variables
        self.cover_path = tk.StringVar()
        self.payload_path = tk.StringVar()
        self.stego_path = tk.StringVar()
        self.secret_key = tk.StringVar()
        self.num_lsbs = tk.IntVar(value=1)
        self.payload_type = tk.StringVar(value="file")
        self.payload_text = tk.StringVar()

        self.audio_cover_path = tk.StringVar()
        self.audio_payload_path = tk.StringVar()
        self.audio_secret_key = tk.StringVar()
        self.audio_num_lsbs = tk.IntVar(value=1)
        self.audio_payload_type = tk.StringVar(value="file")
        self.audio_payload_text = tk.StringVar()
        self.show_key = tk.BooleanVar(value=False)
        self.show_audio_key = tk.BooleanVar(value=False)

        self.setup_ui()

    def setup_ui(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        encode_frame = ttk.Frame(notebook)
        notebook.add(encode_frame, text="Image Encode")

        decode_frame = ttk.Frame(notebook)
        notebook.add(decode_frame, text="Image Decode")

        audio_encode_frame = ttk.Frame(notebook)
        notebook.add(audio_encode_frame, text="Audio Encode")

        audio_decode_frame = ttk.Frame(notebook)
        notebook.add(audio_decode_frame, text="Audio Decode")

        self.setup_encode_tab(encode_frame)
        self.setup_decode_tab(decode_frame)
        self.setup_audio_encode_tab(audio_encode_frame)
        self.setup_audio_decode_tab(audio_decode_frame)

    def setup_encode_tab(self, parent):
        file_frame = tk.LabelFrame(parent, text="File Selection", font=('Helvetica', 10, 'bold'),
                                   bg='#f5f5f5', padx=10, pady=10)
        file_frame.pack(fill=tk.X, padx=10, pady=5)

        cover_section = tk.Frame(file_frame, bg='#f5f5f5')
        cover_section.pack(fill=tk.X, pady=5)

        tk.Label(cover_section, text="Cover Image:", font=('Helvetica', 10, 'bold'),
                 bg='#f5f5f5').pack(anchor=tk.W)

        cover_input_frame = tk.Frame(cover_section, bg='#f5f5f5')
        cover_input_frame.pack(fill=tk.X, pady=2)

        self.cover_entry = tk.Entry(cover_input_frame, textvariable=self.cover_path,
                                    font=('Helvetica', 10), state='readonly')
        self.cover_entry.pack(side=tk.LEFT, fill=tk.X,
                              expand=True, padx=(0, 5))

        tk.Button(cover_input_frame, text="Browse", command=self.browse_cover,
                  bg='#4CAF50', fg='white', font=('Helvetica', 9, 'bold')).pack(side=tk.RIGHT)

        self.cover_drop_zone = DropZone(cover_section,
                                        "Drag & Drop Cover Image Here\n(PNG, BMP, JPG)",
                                        callback=self.set_cover_image,
                                        file_types=['.png', '.bmp', '.jpg', '.jpeg'])
        self.cover_drop_zone.pack(fill=tk.X, pady=5)

        payload_section = tk.Frame(file_frame, bg='#f5f5f5')
        payload_section.pack(fill=tk.X, pady=10)

        tk.Label(payload_section, text="Payload:", font=('Helvetica', 10, 'bold'),
                 bg='#f5f5f5').pack(anchor=tk.W)

        payload_type_frame = tk.Frame(payload_section, bg='#f5f5f5')
        payload_type_frame.pack(fill=tk.X, pady=2)

        tk.Radiobutton(payload_type_frame, text="File", variable=self.payload_type,
                       value="file", command=self.toggle_payload_input,
                       bg='#f5f5f5', font=('Helvetica', 10)).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(payload_type_frame, text="Text", variable=self.payload_type,
                       value="text", command=self.toggle_payload_input,
                       bg='#f5f5f5', font=('Helvetica', 10)).pack(side=tk.LEFT, padx=10)

        self.payload_file_frame = tk.Frame(payload_section, bg='#f5f5f5')
        self.payload_file_frame.pack(fill=tk.X, pady=2)

        self.payload_entry = tk.Entry(self.payload_file_frame, textvariable=self.payload_path,
                                      font=('Helvetica', 10), state='readonly')
        self.payload_entry.pack(side=tk.LEFT, fill=tk.X,
                                expand=True, padx=(0, 5))

        tk.Button(self.payload_file_frame, text="Browse", command=self.browse_payload,
                  bg='#2196F3', fg='white', font=('Helvetica', 9, 'bold')).pack(side=tk.RIGHT)

        self.payload_drop_zone = DropZone(payload_section,
                                          "Drag & Drop Payload File Here\n(Any file type)",
                                          callback=self.set_payload_file)
        self.payload_drop_zone.pack(fill=tk.X, pady=5)

        self.payload_text_frame = tk.Frame(payload_section, bg='#f5f5f5')
        self.payload_text_area = tk.Text(
            self.payload_text_frame, height=4, font=('Helvetica', 10))
        self.payload_text_area.pack(fill=tk.X, pady=5)
        self.payload_text_area.bind('<<Modified>>', self.update_payload_text)

        config_frame = tk.LabelFrame(parent, text="Configuration",
                                     font=('Helvetica', 10, 'bold'), bg='#f5f5f5',
                                     padx=10, pady=10)
        config_frame.pack(fill=tk.X, padx=10, pady=5)

        key_frame = tk.Frame(config_frame, bg='#f5f5f5')
        key_frame.pack(fill=tk.X, pady=2)

        tk.Label(key_frame, text="Secret Key:", font=('Helvetica', 10, 'bold'),
                 bg='#f5f5f5').pack(side=tk.LEFT)
        self.key_entry = tk.Entry(key_frame, textvariable=self.secret_key, width=20,
                                  font=('Helvetica', 10), show="*")
        self.key_entry.pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(key_frame, text="Show Key", variable=self.show_key,
                       command=self.toggle_key_visibility, bg='#f5f5f5',
                       font=('Helvetica', 9)).pack(side=tk.LEFT, padx=5)

        lsb_frame = tk.Frame(config_frame, bg='#f5f5f5')
        lsb_frame.pack(fill=tk.X, pady=5)

        tk.Label(lsb_frame, text="Number of LSBs:", font=('Helvetica', 10, 'bold'),
                 bg='#f5f5f5').pack(side=tk.LEFT)

        lsb_slider = Scale(lsb_frame, from_=1, to=8, orient=HORIZONTAL,
                           variable=self.num_lsbs, command=self.update_capacity_display,
                           bg='#f5f5f5', font=('Helvetica', 9))
        lsb_slider.pack(side=tk.LEFT, padx=10)

        self.capacity_label = tk.Label(lsb_frame, text="Capacity: N/A",
                                       font=('Helvetica', 10, 'italic'), bg='#f5f5f5')
        self.capacity_label.pack(side=tk.LEFT, padx=20)

        button_frame = tk.Frame(parent, bg='#f5f5f5')
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(button_frame, text="🔒 Encode Payload", bg="#4CAF50", fg="white",
                  font=("Helvetica", 12, "bold"), command=self.run_encode,
                  height=2, width=20).pack(side=tk.LEFT, padx=10)

        tk.Button(button_frame, text="🗑️ Clear All", bg="#FF9800", fg="white",
                  font=("Helvetica", 12, "bold"), command=self.clear_all,
                  height=2, width=15).pack(side=tk.LEFT, padx=10)

        display_frame = tk.LabelFrame(parent, text="Image Display",
                                      font=('Helvetica', 10, 'bold'), bg='#f5f5f5')
        display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        cover_frame = tk.Frame(display_frame, bg='#f5f5f5')
        cover_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        tk.Label(cover_frame, text="Cover Image", font=('Helvetica', 10, 'bold'),
                 bg='#f5f5f5').pack()
        tk.Label(cover_frame, text="Click and drag to select embedding region",
                 font=('Helvetica', 9, 'italic'), bg='#f5f5f5').pack()

        cover_canvas_frame = tk.Frame(cover_frame, bg='#f5f5f5')
        cover_canvas_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        tk.Button(cover_canvas_frame, text="Clear Selection", command=self.clear_selection,
                  bg='#FF5722', fg='white', font=('Helvetica', 9, 'bold')).pack(anchor=tk.NE, padx=5)

        cover_v_scroll = tk.Scrollbar(cover_canvas_frame, orient=tk.VERTICAL)
        cover_v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        cover_h_scroll = tk.Scrollbar(cover_canvas_frame, orient=tk.HORIZONTAL)
        cover_h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        self.cover_canvas = tk.Canvas(
            cover_canvas_frame, bg="lightgrey", relief=tk.SUNKEN, bd=2,
            scrollregion=(0, 0, 450, 450), yscrollcommand=cover_v_scroll.set,
            xscrollcommand=cover_h_scroll.set
        )
        self.cover_canvas.pack(fill=tk.BOTH, expand=True)

        cover_v_scroll.config(command=self.cover_canvas.yview)
        cover_h_scroll.config(command=self.cover_canvas.xview)

        stego_frame = tk.Frame(display_frame, bg='#f5f5f5')
        stego_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)

        tk.Label(stego_frame, text="Stego Object / Difference Map",
                 font=('Helvetica', 10, 'bold'), bg='#f5f5f5').pack()

        stego_canvas_frame = tk.Frame(stego_frame, bg='#f5f5f5')
        stego_canvas_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        stego_v_scroll = tk.Scrollbar(stego_canvas_frame, orient=tk.VERTICAL)
        stego_v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        stego_h_scroll = tk.Scrollbar(stego_canvas_frame, orient=tk.HORIZONTAL)
        stego_h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        self.stego_canvas = tk.Canvas(
            stego_canvas_frame, bg="lightgrey", relief=tk.SUNKEN, bd=2,
            scrollregion=(0, 0, 450, 450), yscrollcommand=stego_v_scroll.set,
            xscrollcommand=stego_h_scroll.set
        )
        self.stego_canvas.pack(fill=tk.BOTH, expand=True)

        stego_v_scroll.config(command=self.stego_canvas.yview)
        stego_h_scroll.config(command=self.stego_canvas.xview)

        self.setup_canvas_bindings()
        self.toggle_payload_input()

    def setup_audio_encode_tab(self, parent):
        file_frame = tk.LabelFrame(parent, text="Audio File Selection", font=('Helvetica', 10, 'bold'),
                                   bg='#f5f5f5', padx=10, pady=10)
        file_frame.pack(fill=tk.X, padx=10, pady=5)

        cover_section = tk.Frame(file_frame, bg='#f5f5f5')
        cover_section.pack(fill=tk.X, pady=5)

        tk.Label(cover_section, text="Cover Audio File (WAV):", font=('Helvetica', 10, 'bold'),
                 bg='#f5f5f5').pack(anchor=tk.W)

        cover_input_frame = tk.Frame(cover_section, bg='#f5f5f5')
        cover_input_frame.pack(fill=tk.X, pady=2)

        self.audio_cover_entry = tk.Entry(cover_input_frame, textvariable=self.audio_cover_path,
                                          font=('Helvetica', 10), state='readonly')
        self.audio_cover_entry.pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        tk.Button(cover_input_frame, text="Browse", command=self.browse_audio_cover,
                  bg='#4CAF50', fg='white', font=('Helvetica', 9, 'bold')).pack(side=tk.RIGHT)

        self.audio_cover_drop_zone = DropZone(cover_section,
                                              "Drag & Drop Cover Audio File Here\n(WAV format)",
                                              callback=self.set_audio_cover,
                                              file_types=['.wav'])
        self.audio_cover_drop_zone.pack(fill=tk.X, pady=5)

        payload_section = tk.Frame(file_frame, bg='#f5f5f5')
        payload_section.pack(fill=tk.X, pady=10)

        tk.Label(payload_section, text="Payload:", font=('Helvetica', 10, 'bold'),
                 bg='#f5f5f5').pack(anchor=tk.W)

        payload_type_frame = tk.Frame(payload_section, bg='#f5f5f5')
        payload_type_frame.pack(fill=tk.X, pady=2)

        tk.Radiobutton(payload_type_frame, text="File", variable=self.audio_payload_type,
                       value="file", command=self.toggle_audio_payload_input,
                       bg='#f5f5f5', font=('Helvetica', 10)).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(payload_type_frame, text="Text", variable=self.audio_payload_type,
                       value="text", command=self.toggle_audio_payload_input,
                       bg='#f5f5f5', font=('Helvetica', 10)).pack(side=tk.LEFT, padx=10)

        self.audio_payload_file_frame = tk.Frame(payload_section, bg='#f5f5f5')
        self.audio_payload_file_frame.pack(fill=tk.X, pady=2)

        self.audio_payload_entry = tk.Entry(self.audio_payload_file_frame, textvariable=self.audio_payload_path,
                                            font=('Helvetica', 10), state='readonly')
        self.audio_payload_entry.pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        tk.Button(self.audio_payload_file_frame, text="Browse", command=self.browse_audio_payload,
                  bg='#2196F3', fg='white', font=('Helvetica', 9, 'bold')).pack(side=tk.RIGHT)

        self.audio_payload_drop_zone = DropZone(payload_section,
                                                "Drag & Drop Payload File Here\n(Any file type)",
                                                callback=self.set_audio_payload)
        self.audio_payload_drop_zone.pack(fill=tk.X, pady=5)

        self.audio_payload_text_frame = tk.Frame(payload_section, bg='#f5f5f5')
        self.audio_payload_text_area = tk.Text(
            self.audio_payload_text_frame, height=4, font=('Helvetica', 10))
        self.audio_payload_text_area.pack(fill=tk.X, pady=5)
        self.audio_payload_text_area.bind(
            '<<Modified>>', self.update_audio_payload_text)

        config_frame = tk.LabelFrame(parent, text="Audio Configuration",
                                     font=('Helvetica', 10, 'bold'), bg='#f5f5f5',
                                     padx=10, pady=10)
        config_frame.pack(fill=tk.X, padx=10, pady=5)

        key_frame = tk.Frame(config_frame, bg='#f5f5f5')
        key_frame.pack(fill=tk.X, pady=2)

        tk.Label(key_frame, text="Secret Key:", font=('Helvetica', 10, 'bold'),
                 bg='#f5f5f5').pack(side=tk.LEFT)
        self.audio_key_entry = tk.Entry(key_frame, textvariable=self.audio_secret_key, width=20,
                                        font=('Helvetica', 10), show="*")
        self.audio_key_entry.pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(key_frame, text="Show Key", variable=self.show_audio_key,
                       command=self.toggle_audio_key_visibility, bg='#f5f5f5',
                       font=('Helvetica', 9)).pack(side=tk.LEFT, padx=5)

        lsb_frame = tk.Frame(config_frame, bg='#f5f5f5')
        lsb_frame.pack(fill=tk.X, pady=5)

        tk.Label(lsb_frame, text="Number of LSBs:", font=('Helvetica', 10, 'bold'),
                 bg='#f5f5f5').pack(side=tk.LEFT)

        audio_lsb_slider = Scale(lsb_frame, from_=1, to=4, orient=HORIZONTAL,
                                 variable=self.audio_num_lsbs, command=self.update_audio_capacity_display,
                                 bg='#f5f5f5', font=('Helvetica', 9))
        audio_lsb_slider.pack(side=tk.LEFT, padx=10)

        self.audio_capacity_label = tk.Label(lsb_frame, text="Capacity: N/A",
                                             font=('Helvetica', 10, 'italic'), bg='#f5f5f5')
        self.audio_capacity_label.pack(side=tk.LEFT, padx=20)

        info_frame = tk.LabelFrame(parent, text="Audio Information",
                                   font=('Helvetica', 10, 'bold'), bg='#f5f5f5',
                                   padx=10, pady=10)
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        self.audio_info_label = tk.Label(info_frame, text="Select an audio file to view information",
                                         font=('Helvetica', 10), bg='#f5f5f5')
        self.audio_info_label.pack(pady=5)

        button_frame = tk.Frame(parent, bg='#f5f5f5')
        button_frame.pack(fill=tk.X, padx=10, pady=20)

        tk.Button(button_frame, text="🎵 Encode Audio Payload", bg="#4CAF50", fg="white",
                  font=("Helvetica", 12, "bold"), command=self.run_audio_encode,
                  height=2, width=25).pack(side=tk.LEFT, padx=10)

        tk.Button(button_frame, text="🗑️ Clear All", bg="#FF9800", fg="white",
                  font=("Helvetica", 12, "bold"), command=self.clear_audio_all,
                  height=2, width=15).pack(side=tk.LEFT, padx=10)

        self.toggle_audio_payload_input()

    def toggle_key_visibility(self):
        self.key_entry.config(show="" if self.show_key.get() else "*")

    def toggle_audio_key_visibility(self):
        self.audio_key_entry.config(
            show="" if self.show_audio_key.get() else "*")

    def toggle_payload_input(self):
        if self.payload_type.get() == "file":
            self.payload_file_frame.pack(fill=tk.X, pady=2)
            self.payload_drop_zone.pack(fill=tk.X, pady=5)
            self.payload_drop_zone.enable()
            self.payload_text_frame.pack_forget()
        else:
            self.payload_file_frame.pack_forget()
            self.payload_drop_zone.pack_forget()
            self.payload_text_frame.pack(fill=tk.X, pady=5)
        self.update_capacity_display()

    def toggle_audio_payload_input(self):
        if self.audio_payload_type.get() == "file":
            self.audio_payload_file_frame.pack(fill=tk.X, pady=2)
            self.audio_payload_drop_zone.pack(fill=tk.X, pady=5)
            self.audio_payload_drop_zone.enable()
            self.audio_payload_text_frame.pack_forget()
        else:
            self.audio_payload_file_frame.pack_forget()
            self.audio_payload_drop_zone.pack_forget()
            self.audio_payload_text_frame.pack(fill=tk.X, pady=5)
        self.update_audio_capacity_display()

    def update_payload_text(self, event=None):
        self.payload_text.set(
            self.payload_text_area.get("1.0", tk.END).strip())
        self.payload_text_area.edit_modified(False)
        self.update_capacity_display()

    def update_audio_payload_text(self, event=None):
        self.audio_payload_text.set(
            self.audio_payload_text_area.get("1.0", tk.END).strip())
        self.audio_payload_text_area.edit_modified(False)
        self.update_audio_capacity_display()

    def setup_decode_tab(self, parent):
        decode_frame = tk.LabelFrame(parent, text="Decode Steganographic Image",
                                     font=('Helvetica', 12, 'bold'), bg='#f5f5f5',
                                     padx=20, pady=20)
        decode_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        instructions = tk.Label(decode_frame,
                                text="Select a steganographic image to extract the hidden payload.\n" +
                                "You'll need the same secret key and LSB settings used during encoding.",
                                font=('Helvetica', 10), bg='#f5f5f5', wraplength=500, justify=tk.CENTER)
        instructions.pack(pady=20)

        decode_button = tk.Button(decode_frame, text="🔓 Select Stego Image & Decode",
                                  bg="#2196F3", fg="white", font=("Helvetica", 14, "bold"),
                                  command=self.run_decode, height=3, width=30)
        decode_button.pack(pady=20)

        self.decode_result = tk.Text(decode_frame, height=10, width=60,
                                     font=('Consolas', 10), bg='#f8f8f8',
                                     relief=tk.SUNKEN, bd=2)
        self.decode_result.pack(fill=tk.BOTH, expand=True, pady=10)

    def setup_audio_decode_tab(self, parent):
        decode_frame = tk.LabelFrame(parent, text="Decode Steganographic Audio",
                                     font=('Helvetica', 12, 'bold'), bg='#f5f5f5',
                                     padx=20, pady=20)
        decode_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        instructions = tk.Label(decode_frame,
                                text="Select a steganographic WAV file to extract the hidden payload.\n" +
                                "You'll need the same secret key and LSB settings used during encoding.",
                                font=('Helvetica', 10), bg='#f5f5f5', wraplength=500, justify=tk.CENTER)
        instructions.pack(pady=20)

        decode_button = tk.Button(decode_frame, text="🎵 Select Stego Audio & Decode",
                                  bg="#2196F3", fg="white", font=("Helvetica", 14, "bold"),
                                  command=self.run_audio_decode, height=3, width=30)
        decode_button.pack(pady=20)

        self.audio_decode_result = tk.Text(decode_frame, height=10, width=60,
                                           font=('Consolas', 10), bg='#f8f8f8',
                                           relief=tk.SUNKEN, bd=2)
        self.audio_decode_result.pack(fill=tk.BOTH, expand=True, pady=10)

    def setup_canvas_bindings(self):
        self.cover_image_on_canvas = None
        self.selection_rect = None
        self.embed_region = None
        self.original_display_size = None
        self.original_img_size = None

        self.cover_canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.cover_canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.cover_canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

    def clear_selection(self):
        self.embed_region = None
        if self.selection_rect:
            self.cover_canvas.delete(self.selection_rect)
            self.selection_rect = None
        self.update_capacity_display()

    def set_audio_cover(self, file_path):
        self.audio_cover_path.set(file_path)
        self.audio_cover_drop_zone.update_text(
            f"✓ {os.path.basename(file_path)}")
        self.display_audio_info(file_path)
        self.update_audio_capacity_display()

    def set_audio_payload(self, file_path):
        self.audio_payload_path.set(file_path)
        self.audio_payload_drop_zone.update_text(
            f"✓ {os.path.basename(file_path)}")
        self.update_audio_capacity_display()

    def browse_audio_cover(self):
        path = filedialog.askopenfilename(
            title="Select Cover Audio File",
            filetypes=[("WAV files", "*.wav")]
        )
        if path:
            self.set_audio_cover(path)

    def browse_audio_payload(self):
        path = filedialog.askopenfilename(title="Select Payload File")
        if path:
            self.set_audio_payload(path)

    def display_audio_info(self, path):
        try:
            with wave.open(path, 'rb') as wav_file:
                frames = wav_file.getnframes()
                sample_rate = wav_file.getframerate()
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                duration = frames / sample_rate

                info_text = f"📊 Audio Information:\n"
                info_text += f"Duration: {duration:.2f} seconds\n"
                info_text += f"Sample Rate: {sample_rate} Hz\n"
                info_text += f"Channels: {channels}\n"
                info_text += f"Sample Width: {sample_width} bytes\n"
                info_text += f"Total Samples: {frames}"

                self.audio_info_label.config(text=info_text)
        except Exception as e:
            self.audio_info_label.config(text=f"Error reading audio file: {e}")

    def calculate_required_lsbs_image(self, cover_path, payload_size, region=None):
        if not cover_path or not os.path.exists(cover_path):
            return None
        try:
            image = Image.open(cover_path)
            width, height = image.size
            if region:
                x1, y1, x2, y2 = region
                num_pixels = (x2 - x1) * (y2 - y1)
            else:
                num_pixels = width * height
            bits_available_per_pixel = num_pixels * 3  # 3 channels (RGB)
            # Metadata: 4 bytes key hash + 4 bytes payload size + 1 byte filename length + filename
            filename = "text_payload.txt" if self.payload_type.get(
            ) == "text" else os.path.basename(self.payload_path.get())
            metadata_size = 9 + len(filename)  # in bytes
            total_bits_needed = (payload_size + metadata_size) * 8
            if bits_available_per_pixel == 0:
                return None
            required_lsbs = math.ceil(
                total_bits_needed / bits_available_per_pixel)
            return min(max(1, required_lsbs), 8)  # Constrain to 1–8 LSBs
        except Exception:
            return None

    def calculate_required_lsbs_audio(self, audio_path, payload_size):
        if not audio_path or not os.path.exists(audio_path):
            return None
        try:
            with wave.open(audio_path, 'rb') as wav_file:
                frames = wav_file.getnframes()
                channels = wav_file.getnchannels()
                total_samples = frames * channels
            # Metadata: 4 bytes key hash + 4 bytes payload size + 1 byte filename length + filename
            filename = "text_payload.txt" if self.audio_payload_type.get(
            ) == "text" else os.path.basename(self.audio_payload_path.get())
            metadata_size = 9 + len(filename)  # in bytes
            total_bits_needed = (payload_size + metadata_size) * 8
            if total_samples == 0:
                return None
            required_lsbs = math.ceil(total_bits_needed / total_samples)
            return min(max(1, required_lsbs), 4)  # Constrain to 1–4 LSBs
        except Exception:
            return None

    def update_capacity_display(self, *args):
        cover_path = self.cover_path.get()
        if not cover_path or not os.path.exists(cover_path):
            self.capacity_label.config(text="Capacity: Select a cover image")
            return
        try:
            region = self.get_embed_region_in_original()
            capacity_bytes = self._calculate_capacity(
                cover_path, self.num_lsbs.get(), region)
            capacity_kb = capacity_bytes / 1024

            # Calculate payload size and recommended LSBs
            payload_size = 0
            recommended_lsbs = None
            if self.payload_type.get() == "file" and self.payload_path.get():
                try:
                    payload_size = os.path.getsize(self.payload_path.get())
                except:
                    payload_size = 0
            elif self.payload_type.get() == "text" and self.payload_text.get():
                payload_size = len(self.payload_text.get().encode('utf-8'))

            recommended_lsbs = self.calculate_required_lsbs_image(
                cover_path, payload_size, region)

            if recommended_lsbs is not None:
                self.capacity_label.config(
                    text=f"Capacity: {capacity_kb:.2f} KB\nRecommended LSBs: {recommended_lsbs}"
                )
            else:
                self.capacity_label.config(
                    text=f"Capacity: {capacity_kb:.2f} KB\nRecommended LSBs: N/A (Select payload)"
                )
        except Exception:
            self.capacity_label.config(text="Capacity: Error")

    def update_audio_capacity_display(self, *args):
        audio_path = self.audio_cover_path.get()
        if not audio_path or not os.path.exists(audio_path):
            self.audio_capacity_label.config(
                text="Capacity: Select an audio file")
            return
        try:
            capacity_bytes = self._calculate_audio_capacity(
                audio_path, self.audio_num_lsbs.get())
            capacity_kb = capacity_bytes / 1024

            # Calculate payload size and recommended LSBs
            payload_size = 0
            recommended_lsbs = None
            if self.audio_payload_type.get() == "file" and self.audio_payload_path.get():
                try:
                    payload_size = os.path.getsize(
                        self.audio_payload_path.get())
                except:
                    payload_size = 0
            elif self.audio_payload_type.get() == "text" and self.audio_payload_text.get():
                payload_size = len(
                    self.audio_payload_text.get().encode('utf-8'))

            recommended_lsbs = self.calculate_required_lsbs_audio(
                audio_path, payload_size)

            if recommended_lsbs is not None:
                self.audio_capacity_label.config(
                    text=f"Capacity: {capacity_kb:.2f} KB\nRecommended LSBs: {recommended_lsbs}"
                )
            else:
                self.audio_capacity_label.config(
                    text=f"Capacity: {capacity_kb:.2f} KB\nRecommended LSBs: N/A (Select payload)"
                )
        except Exception:
            self.audio_capacity_label.config(text="Capacity: Error")

    def set_cover_image(self, file_path):
        self.cover_path.set(file_path)
        self.cover_drop_zone.update_text(f"✓ {os.path.basename(file_path)}")
        self.display_image(file_path)
        self.update_capacity_display()

    def set_payload_file(self, file_path):
        self.payload_path.set(file_path)
        self.payload_drop_zone.update_text(f"✓ {os.path.basename(file_path)}")
        self.update_capacity_display()

    def browse_cover(self):
        path = filedialog.askopenfilename(
            title="Select Cover Image",
            filetypes=[("Image files", "*.png *.bmp *.jpg *.jpeg *.gif")]
        )
        if path:
            self.set_cover_image(path)

    def browse_payload(self):
        path = filedialog.askopenfilename(title="Select Payload File")
        if path:
            self.set_payload_file(path)

    def display_image(self, path):
        try:
            img = Image.open(path)
            canvas_width = self.cover_canvas.winfo_width()
            canvas_height = self.cover_canvas.winfo_height()
            if canvas_width < 10:
                canvas_width = 450
                canvas_height = 450

            img_width, img_height = img.size
            aspect_ratio = min(canvas_width / img_width,
                               canvas_height / img_height)
            new_width = int(img_width * aspect_ratio)
            new_height = int(img_height * aspect_ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            self.tk_img = ImageTk.PhotoImage(img)
            self.cover_canvas.delete("all")
            self.cover_image_on_canvas = self.cover_canvas.create_image(
                0, 0, anchor="nw", image=self.tk_img
            )
            self.cover_canvas.config(
                scrollregion=(0, 0, new_width, new_height))
            self.original_display_size = (new_width, new_height)
            self.original_img_size = Image.open(path).size
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")

    def on_mouse_down(self, event):
        self.start_x, self.start_y = event.x, event.y
        if self.selection_rect:
            self.cover_canvas.delete(self.selection_rect)
        self.selection_rect = self.cover_canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="red", width=2
        )

    def on_mouse_drag(self, event):
        self.cover_canvas.coords(self.selection_rect, self.start_x,
                                 self.start_y, event.x, event.y)

    def on_mouse_up(self, event):
        self.end_x, self.end_y = event.x, event.y
        self.embed_region = (
            min(self.start_x, self.end_x), min(self.start_y, self.end_y),
            max(self.start_x, self.end_x), max(self.start_y, self.end_y)
        )
        self.update_capacity_display()

    def get_embed_region_in_original(self):
        if not self.embed_region or not self.original_display_size:
            return None
        x1, y1, x2, y2 = self.embed_region
        disp_w, disp_h = self.original_display_size
        orig_w, orig_h = self.original_img_size
        scale_x = orig_w / disp_w
        scale_y = orig_h / disp_h
        return (int(x1 * scale_x), int(y1 * scale_y),
                int(x2 * scale_x), int(y2 * scale_y))

    def hash_key(self, key):
        """Generate SHA-256 hash of the key and return first 4 bytes and integer seed."""
        key_bytes = key.encode('utf-8')
        key_hash = hashlib.sha256(key_bytes).digest()
        hash_prefix = key_hash[:4]  # First 4 bytes for metadata
        seed = int.from_bytes(key_hash, 'big') % (
            2**32)  # Convert to integer for random.seed
        return hash_prefix, seed

    def run_encode(self):
        cover = self.cover_path.get()
        key = self.secret_key.get()

        if not cover or not key:
            messagebox.showerror(
                "Error", "Please provide Cover Image and a Secret Key.")
            return

        payload_type = self.payload_type.get()
        if payload_type == "file":
            payload = self.payload_path.get()
            if not payload:
                messagebox.showerror("Error", "Please select a Payload File.")
                return
            try:
                with open(payload, 'rb') as f:
                    payload_data = f.read()
                filename = os.path.basename(payload)
            except Exception as e:
                messagebox.showerror(
                    "Error", f"Failed to read payload file: {e}")
                return
        else:
            payload_text = self.payload_text.get()
            if not payload_text:
                messagebox.showerror("Error", "Please enter text to encode.")
                return
            payload_data = payload_text.encode('utf-8')
            filename = "text_payload.txt"

        try:
            stego_path = self._encode_image(
                cover, payload_data, filename, key, self.num_lsbs.get())
            messagebox.showinfo(
                "Success", f"✅ Payload embedded successfully!\n📁 Stego-image saved as:\n{stego_path}")

            self.display_stego_image(stego_path)

            if messagebox.askyesno("Visualization", "Show a difference map to visualize changes?"):
                diff_map_path = self._create_difference_map(cover, stego_path)
                self.display_stego_image(diff_map_path)

        except ValueError as e:
            messagebox.showerror("Encoding Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {e}")

    def display_stego_image(self, path):
        try:
            img = Image.open(path)
            canvas_width = self.stego_canvas.winfo_width()
            canvas_height = self.stego_canvas.winfo_height()
            if canvas_width < 10:
                canvas_width = 450
                canvas_height = 450

            img_width, img_height = img.size
            aspect_ratio = min(canvas_width / img_width,
                               canvas_height / img_height)
            new_width = int(img_width * aspect_ratio)
            new_height = int(img_height * aspect_ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            self.stego_img = ImageTk.PhotoImage(img)
            self.stego_canvas.delete("all")
            self.stego_canvas.create_image(
                0, 0, anchor="nw", image=self.stego_img)
            self.stego_canvas.config(
                scrollregion=(0, 0, new_width, new_height))
        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to display stego image: {e}")

    def run_decode(self):
        stego_path = filedialog.askopenfilename(
            title="Select Stego-Image",
            filetypes=[("Image files", "*.png *.bmp *.jpg *.jpeg *.gif")]
        )
        if not stego_path:
            return

        key = simpledialog.askstring(
            "Input", "Enter the Secret Key:", show="*")
        if not key:
            messagebox.showerror(
                "Error", "A valid key is required for decoding.")
            return

        try:
            extracted_path, is_text = self._decode_image(
                stego_path, key, self.num_lsbs.get())

            result_text = f"✅ Payload extracted successfully!\n\n"
            result_text += f"📁 Extracted file: {extracted_path}\n"
            result_text += f"📊 File size: {os.path.getsize(extracted_path)} bytes\n"
            result_text += f"🔑 Key used: [Hidden]\n"
            result_text += f"⚙️ LSBs used: {self.num_lsbs.get()}\n"
            if is_text:
                with open(extracted_path, 'r', encoding='utf-8') as f:
                    result_text += f"\n📝 Extracted text:\n{f.read()[:1000]}"

            self.decode_result.delete(1.0, tk.END)
            self.decode_result.insert(1.0, result_text)

            if messagebox.askyesno("Success", f"✅ Payload extracted!\n📁 Saved as: {os.path.basename(extracted_path)}\n\n🔍 Open now?"):
                self.open_file(extracted_path)

        except ValueError as e:
            error_text = f"❌ Failed to decode: {e}\n\n"
            error_text += "Please check:\n"
            error_text += "• Correct secret key\n"
            error_text += "• Same LSB settings as encoding\n"
            error_text += "• Valid stego image\n"

            self.decode_result.delete(1.0, tk.END)
            self.decode_result.insert(1.0, error_text)
            messagebox.showerror("Decoding Error", f"Failed to decode: {e}")

    def run_audio_encode(self):
        cover = self.audio_cover_path.get()
        key = self.audio_secret_key.get()

        if not cover or not key:
            messagebox.showerror(
                "Error", "Please provide Cover Audio File and a Secret Key.")
            return

        payload_type = self.audio_payload_type.get()
        if payload_type == "file":
            payload = self.audio_payload_path.get()
            if not payload:
                messagebox.showerror("Error", "Please select a Payload File.")
                return
            try:
                with open(payload, 'rb') as f:
                    payload_data = f.read()
                filename = os.path.basename(payload)
            except Exception as e:
                messagebox.showerror(
                    "Error", f"Failed to read payload file: {e}")
                return
        else:
            payload_text = self.audio_payload_text.get()
            if not payload_text:
                messagebox.showerror("Error", "Please enter text to encode.")
                return
            payload_data = payload_text.encode('utf-8')
            filename = "text_payload.txt"

        try:
            stego_path = self._encode_audio(
                cover, payload_data, filename, key, self.audio_num_lsbs.get())
            messagebox.showinfo(
                "Success", f"✅ Payload embedded successfully!\n🎵 Stego-audio saved as:\n{stego_path}")
        except ValueError as e:
            messagebox.showerror("Encoding Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {e}")

    def run_audio_decode(self):
        stego_path = filedialog.askopenfilename(
            title="Select Stego-Audio File",
            filetypes=[("WAV files", "*.wav")]
        )
        if not stego_path:
            return

        key = simpledialog.askstring(
            "Input", "Enter the Secret Key:", show="*")
        if not key:
            messagebox.showerror(
                "Error", "A valid key is required for decoding.")
            return

        try:
            extracted_path, is_text = self._decode_audio(
                stego_path, key, self.audio_num_lsbs.get())

            result_text = f"✅ Payload extracted successfully!\n\n"
            result_text += f"📁 Extracted file: {extracted_path}\n"
            result_text += f"📊 File size: {os.path.getsize(extracted_path)} bytes\n"
            result_text += f"🔑 Key used: [Hidden]\n"
            result_text += f"⚙️ LSBs used: {self.audio_num_lsbs.get()}\n"
            if is_text:
                with open(extracted_path, 'r', encoding='utf-8') as f:
                    result_text += f"\n📝 Extracted text:\n{f.read()[:1000]}"

            self.audio_decode_result.delete(1.0, tk.END)
            self.audio_decode_result.insert(1.0, result_text)

            if messagebox.askyesno("Success", f"✅ Payload extracted!\n📁 Saved as: {os.path.basename(extracted_path)}\n\n🔍 Open now?"):
                self.open_file(extracted_path)

        except Exception as e:
            error_text = f"❌ Failed to decode: {e}\n\n"
            error_text += "Please check:\n"
            error_text += "• Correct secret key\n"
            error_text += "• Same LSB settings as encoding\n"
            error_text += "• Valid stego audio file\n"

            self.audio_decode_result.delete(1.0, tk.END)
            self.audio_decode_result.insert(1.0, error_text)
            messagebox.showerror("Decoding Error", f"Failed to decode: {e}")

    def clear_audio_all(self):
        self.audio_cover_path.set("")
        self.audio_payload_path.set("")
        self.audio_secret_key.set("")
        self.audio_num_lsbs.set(1)
        self.audio_payload_type.set("file")
        self.audio_payload_text.set("")
        self.audio_capacity_label.config(text="Capacity: N/A")
        self.audio_info_label.config(
            text="Select an audio file to view information")
        self.show_audio_key.set(False)
        self.audio_key_entry.config(show="*")

        self.audio_cover_drop_zone.update_text(
            "Drag & Drop Cover Audio File Here\n(WAV format)")
        self.audio_payload_drop_zone.update_text(
            "Drag & Drop Payload File Here\n(Any file type)")
        self.audio_cover_drop_zone.reset_colors()
        self.audio_payload_drop_zone.reset_colors()
        self.audio_payload_text_area.delete("1.0", tk.END)
        self.toggle_audio_payload_input()

    def clear_all(self):
        self.cover_path.set("")
        self.payload_path.set("")
        self.secret_key.set("")
        self.num_lsbs.set(1)
        self.payload_type.set("file")
        self.payload_text.set("")
        self.cover_canvas.delete("all")
        self.stego_canvas.delete("all")
        self.capacity_label.config(text="Capacity: N/A")
        self.clear_selection()
        self.show_key.set(False)
        self.key_entry.config(show="*")

        self.cover_drop_zone.update_text(
            "Drag & Drop Cover Image Here\n(PNG, BMP, JPG)")
        self.payload_drop_zone.update_text(
            "Drag & Drop Payload File Here\n(Any file type)")
        self.cover_drop_zone.reset_colors()
        self.payload_drop_zone.reset_colors()
        self.payload_text_area.delete("1.0", tk.END)
        self.toggle_payload_input()

    def open_file(self, filepath):
        try:
            if platform.system() == 'Darwin':
                subprocess.call(('open', filepath))
            elif platform.system() == 'Windows':
                os.startfile(filepath)
            else:
                subprocess.call(('xdg-open', filepath))
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {e}")

    def _encode_image(self, cover_path, payload_data, filename, key, num_lsbs):
        key_hash, seed = self.hash_key(key)
        metadata = key_hash + len(payload_data).to_bytes(4, 'big') + \
            len(filename).to_bytes(1, 'big') + filename.encode()
        data_to_embed = metadata + payload_data
        bit_stream = bitarray()
        bit_stream.frombytes(data_to_embed)

        image = Image.open(cover_path).convert('RGB')
        width, height = image.size
        region = self.get_embed_region_in_original()
        if region:
            x1, y1, x2, y2 = region
            pixel_indices = [(x, y) for y in range(y1, y2)
                             for x in range(x1, x2)]
        else:
            pixel_indices = [(x, y) for y in range(height)
                             for x in range(width)]

        max_bits = len(pixel_indices) * 3 * num_lsbs
        if len(bit_stream) > max_bits:
            raise ValueError(
                f"Payload too large: {len(bit_stream)} bits > {max_bits} bits available")

        random.seed(seed)
        random.shuffle(pixel_indices)
        data_index = 0
        pixels = image.load()
        mask = (255 << num_lsbs) & 255
        for x, y in pixel_indices:
            if data_index >= len(bit_stream):
                break
            r, g, b = pixels[x, y]
            rgb = [r, g, b]
            for i in range(3):
                if data_index < len(bit_stream):
                    chunk = bit_stream[data_index:data_index + num_lsbs]
                    bits = int(chunk.to01(), 2) if chunk else 0
                    rgb[i] = (rgb[i] & mask) | bits
                    data_index += num_lsbs
            pixels[x, y] = tuple(rgb)
        stego_path = os.path.join(os.path.dirname(
            cover_path), "stego_" + os.path.basename(cover_path))
        image.save(stego_path, "PNG")
        return stego_path

    def _decode_image(self, stego_path, key, num_lsbs):
        image = Image.open(stego_path).convert('RGB')
        width, height = image.size
        region = self.get_embed_region_in_original()
        if region:
            x1, y1, x2, y2 = region
            pixel_indices = [(x, y) for y in range(y1, y2)
                             for x in range(x1, x2)]
        else:
            pixel_indices = [(x, y) for y in range(height)
                             for x in range(width)]

        key_hash, seed = self.hash_key(key)
        random.seed(seed)
        random.shuffle(pixel_indices)

        extracted_bits = bitarray()
        mask = (1 << num_lsbs) - 1
        pixels = image.load()

        # Extract enough bits for metadata (4 bytes key hash + 4 bytes payload size + 1 byte filename length)
        bits_needed = (4 + 4 + 1) * 8
        pixels_needed = (bits_needed + num_lsbs * 3 - 1) // (num_lsbs * 3)
        pixels_needed = min(pixels_needed, len(pixel_indices))

        for i in range(pixels_needed):
            x, y = pixel_indices[i]
            r, g, b = pixels[x, y]
            for val in (r, g, b):
                extracted_bits.extend(bin(val & mask)[2:].zfill(num_lsbs))

        if len(extracted_bits) < 72:  # 9 bytes * 8 bits
            raise ValueError("Insufficient data for metadata")

        # Check metadata format (new: includes key hash; old: no key hash)
        stored_key_hash = extracted_bits[:32].tobytes()
        offset = 32
        if len(stored_key_hash) == 4 and stored_key_hash == key_hash:
            # New format with key hash
            payload_size = int(extracted_bits[offset:offset+32].to01(), 2)
            offset += 32
            filename_len = int(extracted_bits[offset:offset+8].to01(), 2)
            offset += 8
        else:
            # Old format (numeric key, no key hash)
            offset = 0
            payload_size = int(extracted_bits[offset:offset+32].to01(), 2)
            offset += 32
            filename_len = int(extracted_bits[offset:offset+8].to01(), 2)
            offset += 8

        if filename_len <= 0 or filename_len > 255:
            raise ValueError(f"Invalid filename length: {filename_len}")
        if payload_size <= 0 or payload_size > 50 * 1024 * 1024:
            raise ValueError(f"Invalid payload size: {payload_size}")

        # Extract filename and payload
        total_bits_needed = offset + filename_len * 8 + payload_size * 8
        pixels_needed = (total_bits_needed + num_lsbs *
                         3 - 1) // (num_lsbs * 3)
        pixels_needed = min(pixels_needed, len(pixel_indices))

        for i in range(len(extracted_bits) // (num_lsbs * 3), pixels_needed):
            x, y = pixel_indices[i]
            r, g, b = pixels[x, y]
            for val in (r, g, b):
                extracted_bits.extend(bin(val & mask)[2:].zfill(num_lsbs))

        filename_bits = extracted_bits[offset:offset + filename_len * 8]
        filename = filename_bits.tobytes().decode("utf-8", errors="replace")
        payload_bits = extracted_bits[offset + filename_len *
                                      8:offset + filename_len * 8 + payload_size * 8]
        if len(payload_bits) != payload_size * 8:
            raise ValueError("Incomplete payload data")

        payload_data = payload_bits.tobytes()
        extracted_path = os.path.join(os.path.dirname(
            stego_path), f"extracted_{filename}")
        is_text = filename.endswith(".txt")

        try:
            with open(extracted_path, "wb") as f:
                f.write(payload_data)
        except Exception as e:
            raise ValueError(f"Failed to save extracted file: {str(e)}")

        return extracted_path, is_text

    def _encode_audio(self, cover_path, payload_data, filename, key, num_lsbs):
        key_hash, seed = self.hash_key(key)
        metadata = key_hash + len(payload_data).to_bytes(4, 'big') + \
            len(filename).to_bytes(1, 'big') + filename.encode()
        data_to_embed = metadata + payload_data
        bit_stream = bitarray()
        bit_stream.frombytes(data_to_embed)

        with wave.open(cover_path, 'rb') as wav_file:
            params = wav_file.getparams()
            frames = wav_file.readframes(params.nframes)

        if params.sampwidth == 1:
            audio_data = np.frombuffer(frames, dtype=np.uint8).copy()
            max_val, min_val = 255, 0
        elif params.sampwidth == 2:
            audio_data = np.frombuffer(frames, dtype=np.int16).copy()
            max_val, min_val = 32767, -32768
        elif params.sampwidth == 3:
            raw = np.frombuffer(frames, dtype=np.uint8).reshape(-1, 3)
            audio_data = (
                raw[:, 0].astype(np.int32)
                | (raw[:, 1].astype(np.int32) << 8)
                | (raw[:, 2].astype(np.int32) << 16)
            )
            audio_data = np.where(
                audio_data >= (1 << 23), audio_data - (1 << 24), audio_data
            ).astype(np.int32)
            max_val, min_val = (1 << 23) - 1, -(1 << 23)
        else:
            raise ValueError(
                "Unsupported sample width. Only 8, 16, and 24-bit audio supported.")

        max_bits = len(audio_data) * num_lsbs
        if len(bit_stream) > max_bits:
            raise ValueError(
                f"Payload too large: {len(bit_stream)} bits > {max_bits} bits available")

        random.seed(seed)
        sample_indices = list(range(len(audio_data)))
        random.shuffle(sample_indices)

        mask = ~((1 << num_lsbs) - 1)
        bit_index = 0
        total_bits = len(bit_stream)

        for sample_idx in sample_indices:
            if bit_index >= total_bits:
                break

            chunk = bit_stream[bit_index:bit_index + num_lsbs]
            bits_to_embed = int(chunk.to01(), 2) if chunk else 0

            original_sample = int(audio_data[sample_idx])
            modified_sample = (original_sample & mask) | bits_to_embed

            modified_sample = np.clip(modified_sample, min_val, max_val)
            audio_data[sample_idx] = modified_sample
            bit_index += num_lsbs

        stego_path = os.path.join(os.path.dirname(
            cover_path), "stego_" + os.path.basename(cover_path))

        with wave.open(stego_path, "wb") as stego_file:
            stego_file.setparams(params)

            if params.sampwidth == 3:
                packed = np.zeros((len(audio_data), 3), dtype=np.uint8)
                vals = audio_data.astype(np.uint32) & 0xFFFFFF
                packed[:, 0] = vals & 0xFF
                packed[:, 1] = (vals >> 8) & 0xFF
                packed[:, 2] = (vals >> 16) & 0xFF
                stego_file.writeframes(packed.tobytes())
            else:
                stego_file.writeframes(audio_data.tobytes())

        return stego_path

    def _decode_audio(self, stego_path, key, num_lsbs):
        with wave.open(stego_path, 'rb') as wav_file:
            params = wav_file.getparams()
            frames = wav_file.readframes(params.nframes)

        if params.sampwidth == 1:
            audio_data = np.frombuffer(frames, dtype=np.uint8)
            max_val = 0xFF
        elif params.sampwidth == 2:
            audio_data = np.frombuffer(frames, dtype=np.int16)
            max_val = 0xFFFF
        elif params.sampwidth == 3:
            raw = np.frombuffer(frames, dtype=np.uint8).reshape(-1, 3)
            audio_data = (raw[:, 0].astype(np.int32) |
                          (raw[:, 1].astype(np.int32) << 8) |
                          (raw[:, 2].astype(np.int32) << 16))
            audio_data = np.where(audio_data >= (1 << 23),
                                  audio_data - (1 << 24),
                                  audio_data)
            max_val = 0xFFFFFF
        else:
            raise ValueError(
                "Unsupported sample width. Only 8, 16, and 24-bit audio supported.")

        key_hash, seed = self.hash_key(key)
        random.seed(seed)
        sample_indices = list(range(len(audio_data)))
        random.shuffle(sample_indices)

        extracted_bits = bitarray(endian='big')
        mask = (1 << num_lsbs) - 1

        # Extract enough bits for metadata (4 bytes key hash + 4 bytes payload size + 1 byte filename length)
        bits_needed = (4 + 4 + 1) * 8
        samples_needed = (bits_needed + num_lsbs - 1) // num_lsbs
        samples_needed = min(samples_needed, len(audio_data))

        for i in range(samples_needed):
            sample_idx = sample_indices[i]
            sample_value = int(audio_data[sample_idx]) & max_val
            extracted_bits.extend(bin(sample_value & mask)[2:].zfill(num_lsbs))

        if len(extracted_bits) < 72:  # 9 bytes * 8 bits
            raise ValueError("Insufficient data for metadata")

        # Check metadata format
        stored_key_hash = extracted_bits[:32].tobytes()
        offset = 32
        if len(stored_key_hash) == 4 and stored_key_hash == key_hash:
            # New format with key hash
            payload_size = int(extracted_bits[offset:offset+32].to01(), 2)
            offset += 32
            filename_len = int(extracted_bits[offset:offset+8].to01(), 2)
            offset += 8
        else:
            # Old format (no key hash)
            offset = 0
            payload_size = int(extracted_bits[offset:offset+32].to01(), 2)
            offset += 32
            filename_len = int(extracted_bits[offset:offset+8].to01(), 2)
            offset += 8

        if filename_len <= 0 or filename_len > 255:
            raise ValueError(f"Invalid filename length: {filename_len}")
        if payload_size <= 0 or payload_size > 50 * 1024 * 1024:
            raise ValueError(f"Invalid payload size: {payload_size}")

        total_bits_needed = offset + filename_len * 8 + payload_size * 8
        samples_needed = (total_bits_needed + num_lsbs - 1) // num_lsbs
        samples_needed = min(samples_needed, len(audio_data))

        for i in range(len(extracted_bits) // num_lsbs, samples_needed):
            sample_idx = sample_indices[i]
            sample_value = int(audio_data[sample_idx]) & max_val
            extracted_bits.extend(bin(sample_value & mask)[2:].zfill(num_lsbs))

        filename_bits = extracted_bits[offset:offset + filename_len * 8]
        filename = filename_bits.tobytes().decode("utf-8", errors="replace")

        payload_bits = extracted_bits[offset + filename_len *
                                      8:offset + filename_len * 8 + payload_size * 8]
        if len(payload_bits) != payload_size * 8:
            raise ValueError("Incomplete payload data")

        payload_data = payload_bits.tobytes()
        extracted_path = os.path.join(os.path.dirname(
            stego_path), f"extracted_{filename}")
        is_text = filename.endswith(".txt")

        try:
            with open(extracted_path, "wb") as f:
                f.write(payload_data)
        except Exception as e:
            raise ValueError(f"Failed to save extracted file: {str(e)}")

        return extracted_path, is_text

    def _calculate_capacity(self, image_path, num_lsbs, region=None):
        image = Image.open(image_path)
        width, height = image.size
        if region:
            x1, y1, x2, y2 = region
            num_pixels = (x2 - x1) * (y2 - y1)
        else:
            num_pixels = width * height
        return (num_pixels * 3 * num_lsbs) // 8

    def _calculate_audio_capacity(self, audio_path, num_lsbs):
        try:
            with wave.open(audio_path, 'rb') as wav_file:
                frames = wav_file.getnframes()
                channels = wav_file.getnchannels()
                total_samples = frames * channels
            max_bits = total_samples * num_lsbs
            return max_bits // 8
        except Exception:
            return 0

    def _create_difference_map(self, cover_path, stego_path):
        cover_img = Image.open(cover_path).convert('RGB')
        stego_img = Image.open(stego_path).convert('RGB')
        if cover_img.size != stego_img.size:
            raise ValueError("Images must have the same dimensions")
        width, height = cover_img.size
        diff_img = Image.new('RGB', (width, height))
        cp, sp, dp = cover_img.load(), stego_img.load(), diff_img.load()
        for y in range(height):
            for x in range(width):
                dp[x, y] = (255, 0, 0) if cp[x, y] != sp[x, y] else (0, 0, 0)
        diff_path = os.path.join(os.path.dirname(
            cover_path), "difference_map.png")
        diff_img.save(diff_path)
        return diff_path


if __name__ == "__main__":
    try:
        app = StegApp()
        app.mainloop()
    except ImportError as e:
        print("Error: Missing required library.")
        print("Please install required packages:")
        print("pip install tkinterdnd2 pillow numpy")
        print("pip install bitarray")
        print(f"\nSpecific error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
