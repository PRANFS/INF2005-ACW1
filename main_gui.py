import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from tkinter import Scale, HORIZONTAL, Checkbutton
import tkinterdnd2 as TkinterDnD
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os
import random
import platform
import subprocess
import wave
import numpy as np
from bitarray import bitarray
import math
import matplotlib.cm as cm
import hashlib
import json
import tempfile
import shutil


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


class KeyLsbDialog(tk.Toplevel):
    def __init__(self, parent, title="Enter Credentials"):
        super().__init__(parent)
        self.title(title)
        self.geometry("300x200")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.focus_set()

        # Variables
        self.key_var = tk.StringVar()
        self.lsb_var = tk.StringVar()

        # Key field
        tk.Label(self, text="Secret Key:").pack(pady=5)
        self.key_entry = tk.Entry(self, textvariable=self.key_var, show="*")
        self.key_entry.pack(pady=5)
        self.key_entry.focus()

        # LSB field
        tk.Label(self, text="LSB Value (1-8):").pack(pady=5)
        self.lsb_entry = tk.Entry(self, textvariable=self.lsb_var)
        self.lsb_entry.pack(pady=5)

        # Buttons
        button_frame = tk.Frame(self)
        button_frame.pack(pady=20)
        tk.Button(button_frame, text="OK", command=self.on_ok,
                  width=10, padx=20, pady=10).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Cancel", command=self.on_cancel,
                  width=10, padx=20, pady=10).pack(side=tk.LEFT, padx=10)

        self.result = None
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        self.wait_window(self)

    def on_ok(self):
        key = self.key_var.get().strip()
        lsb_str = self.lsb_var.get().strip()

        if not key:
            messagebox.showerror("Error", "Secret key cannot be empty.")
            return

        try:
            lsb = int(lsb_str)
            if not (1 <= lsb <= 8):
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Error", "LSB value must be an integer between 1 and 8.")
            return

        self.result = (key, lsb)
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()


class StegApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title(
            "LSB Steganography Tool - Enhanced GUI with Audio & Text Support")
        self.geometry("1250x980")
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
        # NEW: last-created stego WAV (encode tab)
        self.audio_stego_path = tk.StringVar()
        # NEW: stego path chosen in decode tab
        self.audio_decode_stego_path = tk.StringVar()
        self.audio_secret_key = tk.StringVar()
        self.audio_num_lsbs = tk.IntVar(value=1)
        self.audio_payload_type = tk.StringVar(value="file")
        self.audio_payload_text = tk.StringVar()
        self.show_key = tk.BooleanVar(value=False)
        self.show_audio_key = tk.BooleanVar(value=False)

        # playback state
        self._audio_proc = None  # for macOS/Linux subprocess player
        self._ab_state = "cover"  # toggle state

        # Video variables
        self.video_cover_path = tk.StringVar()
        self.video_payload_path = tk.StringVar()
        self.video_stego_path = tk.StringVar()
        self.video_decode_stego_path = tk.StringVar()
        self.video_secret_key = tk.StringVar()
        self.video_num_lsbs = tk.IntVar(value=1)
        self.video_payload_type = tk.StringVar(value="file")
        self.video_payload_text = tk.StringVar()
        self.show_video_key = tk.BooleanVar(value=False)

        # Image encode specific: scaling and region
        self.cover_orig_path = None
        self.orig_size = None
        self.scale = 1.0
        self.scaled_size = (0, 0)
        self.embed_region_orig = None
        self.rect = None
        self.start_canvas_x = None
        self.start_canvas_y = None

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

        video_encode_frame = ttk.Frame(notebook)
        notebook.add(video_encode_frame, text="Video Encode")

        video_decode_frame = ttk.Frame(notebook)
        notebook.add(video_decode_frame, text="Video Decode")

        analysis_frame = ttk.Frame(notebook)
        notebook.add(analysis_frame, text="Image Analysis")

        audio_analysis_frame = ttk.Frame(notebook)
        notebook.add(audio_analysis_frame, text="Audio Analysis")

        video_analysis_frame = ttk.Frame(notebook)
        notebook.add(video_analysis_frame, text="Video Analysis")

        self.setup_audio_analysis_tab(audio_analysis_frame)
        self.setup_analysis_tab(analysis_frame)
        self.setup_video_analysis_tab(video_analysis_frame)
        self.setup_encode_tab(encode_frame)
        self.setup_decode_tab(decode_frame)
        self.setup_audio_encode_tab(audio_encode_frame)
        self.setup_audio_decode_tab(audio_decode_frame)
        self.setup_video_encode_tab(video_encode_frame)
        self.setup_video_decode_tab(video_decode_frame)

    def create_scrolled_frame(self, parent):
        canvas = tk.Canvas(parent, bg='#f5f5f5')
        scrollbar = ttk.Scrollbar(
            parent, orient="vertical", command=canvas.yview)
        inner_frame = ttk.Frame(canvas)
        inner_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        window_id = canvas.create_window(
            (0, 0), window=inner_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(
            window_id, width=e.width))
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return inner_frame

    # -------------------- IMAGE ENCODE TAB --------------------
    def setup_encode_tab(self, parent):
        inner_frame = self.create_scrolled_frame(parent)

        file_frame = tk.LabelFrame(inner_frame, text="File Selection", font=('Helvetica', 10, 'bold'),
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

        config_frame = tk.LabelFrame(inner_frame, text="Configuration",
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

        lsb_slider = tk.Scale(lsb_frame, from_=1, to=8, orient=HORIZONTAL,
                              variable=self.num_lsbs, command=self.update_capacity_display,
                              bg='#f5f5f5', font=('Helvetica', 9))
        lsb_slider.pack(side=tk.LEFT, padx=10)

        self.capacity_label = tk.Label(lsb_frame, text="Capacity: N/A",
                                       font=('Helvetica', 10, 'italic'), bg='#f5f5f5')
        self.capacity_label.pack(side=tk.LEFT, padx=20)

        button_frame = tk.Frame(inner_frame, bg='#f5f5f5')
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(button_frame, text="🔒 Encode Payload", bg="#4CAF50", fg="white",
                  font=("Helvetica", 12, "bold"), command=self.run_encode,
                  height=2, width=20).pack(side=tk.LEFT, padx=10)

        tk.Button(button_frame, text="🗑️ Clear All", bg="#FF9800", fg="white",
                  font=("Helvetica", 12, "bold"), command=self.clear_all,
                  height=2, width=15).pack(side=tk.LEFT, padx=10)

        display_frame = tk.LabelFrame(inner_frame, text="Image Display",
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

        self.cover_canvas = tk.Canvas(
            cover_canvas_frame, bg="lightgrey", relief=tk.SUNKEN, bd=2
        )

        vscroll_cover = ttk.Scrollbar(
            cover_canvas_frame, orient='vertical', command=self.cover_canvas.yview)
        hscroll_cover = ttk.Scrollbar(
            cover_canvas_frame, orient='horizontal', command=self.cover_canvas.xview)
        self.cover_canvas.configure(
            yscrollcommand=vscroll_cover.set, xscrollcommand=hscroll_cover.set)

        self.cover_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vscroll_cover.pack(side=tk.RIGHT, fill=tk.Y)
        hscroll_cover.pack(side=tk.BOTTOM, fill=tk.X)

        # Bind configure for scaling
        self.cover_canvas.bind("<Configure>", self.on_cover_canvas_configure)

        stego_frame = tk.Frame(display_frame, bg='#f5f5f5')
        stego_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)

        tk.Label(stego_frame, text="Stego Object / Difference Map",
                 font=('Helvetica', 10, 'bold'), bg='#f5f5f5').pack()

        stego_canvas_frame = tk.Frame(stego_frame, bg='#f5f5f5')
        stego_canvas_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.stego_canvas = tk.Canvas(
            stego_canvas_frame, bg="lightgrey", relief=tk.SUNKEN, bd=2
        )

        vscroll_stego = ttk.Scrollbar(
            stego_canvas_frame, orient='vertical', command=self.stego_canvas.yview)
        hscroll_stego = ttk.Scrollbar(
            stego_canvas_frame, orient='horizontal', command=self.stego_canvas.xview)
        self.stego_canvas.configure(
            yscrollcommand=vscroll_stego.set, xscrollcommand=hscroll_stego.set)

        self.stego_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vscroll_stego.pack(side=tk.RIGHT, fill=tk.Y)
        hscroll_stego.pack(side=tk.BOTTOM, fill=tk.X)

        self.setup_canvas_bindings()
        self.toggle_payload_input()

    def on_cover_canvas_configure(self, event):
        if hasattr(self, 'cover_orig_path') and self.cover_orig_path:
            self.redisplay_cover()

    def redisplay_cover(self):
        if not self.cover_orig_path or not os.path.exists(self.cover_orig_path):
            return
        try:
            orig_img = Image.open(self.cover_orig_path)
            orig_w, orig_h = self.orig_size or orig_img.size
            self.orig_size = (orig_w, orig_h)

            self.cover_canvas.update_idletasks()
            c_w = self.cover_canvas.winfo_width()
            c_h = self.cover_canvas.winfo_height()
            if c_w <= 1 or c_h <= 1:
                return

            scale_w = c_w / orig_w
            scale_h = c_h / orig_h
            self.scale = min(scale_w, scale_h, 1.0)
            scaled_w = int(orig_w * self.scale)
            scaled_h = int(orig_h * self.scale)
            self.scaled_size = (scaled_w, scaled_h)

            scaled_img = orig_img.resize(
                (scaled_w, scaled_h), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(scaled_img)

            self.cover_canvas.delete("all")
            self.cover_canvas.create_image(0, 0, anchor=tk.NW, image=photo)
            self.cover_canvas.image = photo
            self.cover_canvas.config(scrollregion=(0, 0, scaled_w, scaled_h))

            # Redraw selection rect if exists
            if self.embed_region_orig:
                x1, y1, x2, y2 = self.embed_region_orig
                cx1 = x1 * self.scale
                cy1 = y1 * self.scale
                cx2 = x2 * self.scale
                cy2 = y2 * self.scale
                self.rect = self.cover_canvas.create_rectangle(
                    cx1, cy1, cx2, cy2, outline='red', width=2)

            self.update_capacity_display()
        except Exception:
            pass

    def display_image_on_canvas(self, path, canvas, label=None, overlay=False):
        if not overlay:
            canvas.delete("all")
        try:
            img = Image.open(path)
            photo = ImageTk.PhotoImage(img)
            canvas.create_image(0, 0, anchor=tk.NW, image=photo)
            canvas.image = photo
            canvas.config(scrollregion=(0, 0, img.width, img.height))
            if label:
                canvas.create_text(
                    10, 10, anchor=tk.NW, text=label, fill="white", font=('Helvetica', 10, 'bold'))
        except Exception:
            pass

    # -------------------- AUDIO ENCODE TAB --------------------
    def setup_audio_encode_tab(self, parent):
        inner_frame = self.create_scrolled_frame(parent)

        file_frame = tk.LabelFrame(inner_frame, text="Audio File Selection", font=('Helvetica', 10, 'bold'),
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

        config_frame = tk.LabelFrame(inner_frame, text="Audio Configuration",
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

        audio_lsb_slider = Scale(lsb_frame, from_=1, to=8, orient=HORIZONTAL,
                                 variable=self.audio_num_lsbs,
                                 command=lambda _=None: (
                                     self.update_audio_capacity_display(), self.update_audio_visuals()),
                                 bg='#f5f5f5', font=('Helvetica', 9))
        audio_lsb_slider.pack(side=tk.LEFT, padx=10)

        self.audio_capacity_label = tk.Label(lsb_frame, text="Capacity: N/A",
                                             font=('Helvetica', 10, 'italic'), bg='#f5f5f5')
        self.audio_capacity_label.pack(side=tk.LEFT, padx=20)

        info_frame = tk.LabelFrame(inner_frame, text="Audio Information",
                                   font=('Helvetica', 10, 'bold'), bg='#f5f5f5',
                                   padx=10, pady=10)
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        self.audio_info_label = tk.Label(info_frame, text="Select an audio file to view information",
                                         font=('Helvetica', 10), bg='#f5f5f5')
        self.audio_info_label.pack(pady=5)

        play_frame = tk.LabelFrame(inner_frame, text="Playback & Compare",
                                   font=('Helvetica', 10, 'bold'), bg='#f5f5f5', padx=10, pady=10)
        play_frame.pack(fill=tk.X, padx=10, pady=5)

        self.btn_play_cover_enc = tk.Button(
            play_frame, text="▶ Play Cover", bg="#4CAF50", fg="white",
            font=("Helvetica", 10, "bold"), command=self.play_audio_cover)
        self.btn_play_cover_enc.pack(side=tk.LEFT, padx=5, pady=2)

        self.btn_play_stego_enc = tk.Button(
            play_frame, text="▶ Play Stego", bg="#9C27B0", fg="white",
            font=("Helvetica", 10, "bold"), command=self.play_audio_stego, state=tk.DISABLED)
        self.btn_play_stego_enc.pack(side=tk.LEFT, padx=5, pady=2)

        self.btn_ab_toggle_enc = tk.Button(
            play_frame, text="A/B Toggle", bg="#03A9F4", fg="white",
            font=("Helvetica", 10, "bold"), command=self.ab_toggle)
        self.btn_ab_toggle_enc.pack(side=tk.LEFT, padx=5, pady=2)

        self.btn_stop_audio_enc = tk.Button(
            play_frame, text="⏹ Stop", bg="#F44336", fg="white",
            font=("Helvetica", 10, "bold"), command=self.stop_audio)
        self.btn_stop_audio_enc.pack(side=tk.LEFT, padx=5, pady=2)

        vis_frame = tk.LabelFrame(inner_frame, text="Audio Visualisation (LSB changes)",
                                  font=('Helvetica', 10, 'bold'), bg='#f5f5f5',
                                  padx=10, pady=10)
        vis_frame.pack(fill=tk.X, padx=10, pady=5)

        canv_height = 140
        self.audio_canvas_cover = tk.Canvas(
            vis_frame, width=540, height=canv_height, bg="#ffffff", bd=1, relief=tk.SUNKEN)
        self.audio_canvas_cover.pack(side=tk.LEFT, padx=5, pady=5)
        self.audio_canvas_stego = tk.Canvas(
            vis_frame, width=540, height=canv_height, bg="#ffffff", bd=1, relief=tk.SUNKEN)
        self.audio_canvas_stego.pack(side=tk.LEFT, padx=5, pady=5)

        self.audio_flip_label = tk.Label(
            inner_frame, text="LSB flips: N/A", bg="#f5f5f5", font=("Helvetica", 10, "italic"))
        self.audio_flip_label.pack(anchor=tk.W, padx=20, pady=(0, 10))

        button_frame = tk.Frame(inner_frame, bg='#f5f5f5')
        button_frame.pack(fill=tk.X, padx=10, pady=(10, 20))

        tk.Button(button_frame, text="🎵 Encode Audio Payload", bg="#4CAF50", fg="white",
                  font=("Helvetica", 12, "bold"), command=self.run_audio_encode,
                  height=2, width=25).pack(side=tk.LEFT, padx=10)

        tk.Button(button_frame, text="🗑️ Clear All", bg="#FF9800", fg="white",
                  font=("Helvetica", 12, "bold"), command=self.clear_audio_all,
                  height=2, width=15).pack(side=tk.LEFT, padx=10)

        self.toggle_audio_payload_input()

    # -------------------- AUDIO DECODE TAB --------------------
    def setup_audio_decode_tab(self, parent):
        decode_frame = tk.LabelFrame(parent, text="Decode Steganographic Audio",
                                     font=('Helvetica', 12, 'bold'), bg='#f5f5f5',
                                     padx=20, pady=20)
        decode_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        instructions = tk.Label(decode_frame,
                                text="Select a steganographic WAV file to extract the hidden payload.\n"
                                     "Use the same secret key and LSB settings as during encoding.",
                                font=('Helvetica', 10), bg='#f5f5f5', wraplength=700, justify=tk.CENTER)
        instructions.pack(pady=10)

        # Playback in Decode tab (Bullet 8)
        play_frame = tk.LabelFrame(decode_frame, text="Playback (Decode Tab)",
                                   font=('Helvetica', 10, 'bold'), bg='#f5f5f5', padx=10, pady=10)
        play_frame.pack(fill=tk.X, padx=10, pady=5)

        self.btn_play_stego_dec = tk.Button(
            play_frame, text="▶ Play Stego (choose file)", bg="#9C27B0", fg="white",
            font=("Helvetica", 10, "bold"), command=self.play_audio_stego)
        self.btn_play_stego_dec.pack(side=tk.LEFT, padx=5, pady=2)

        self.btn_play_cover_dec = tk.Button(
            play_frame, text="▶ Play Cover (if loaded)", bg="#4CAF50", fg="white",
            font=("Helvetica", 10, "bold"), command=self.play_audio_cover)
        self.btn_play_cover_dec.pack(side=tk.LEFT, padx=5, pady=2)

        self.btn_stop_audio_dec = tk.Button(
            play_frame, text="⏹ Stop", bg="#F44336", fg="white",
            font=("Helvetica", 10, "bold"), command=self.stop_audio)
        self.btn_stop_audio_dec.pack(side=tk.LEFT, padx=5, pady=2)

        # Simple visualisation of stego waveform in decode tab
        self.audio_stego_canvas_dec = tk.Canvas(
            decode_frame, width=1100, height=140, bg="#ffffff", bd=1, relief=tk.SUNKEN)
        self.audio_stego_canvas_dec.pack(fill=tk.X, padx=10, pady=10)

        decode_button = tk.Button(decode_frame, text="🎵 Select Stego Audio & Decode",
                                  bg="#2196F3", fg="white", font=("Helvetica", 14, "bold"),
                                  command=self.run_audio_decode, height=2, width=30)
        decode_button.pack(pady=10)

        self.audio_decode_result = tk.Text(decode_frame, height=10, width=90,
                                           font=('Consolas', 10), bg='#f8f8f8',
                                           relief=tk.SUNKEN, bd=2)
        self.audio_decode_result.pack(fill=tk.BOTH, expand=True, pady=10)

    # -------------------- IMAGE DECODE TAB --------------------
    def setup_decode_tab(self, parent):
        decode_frame = tk.LabelFrame(parent, text="Decode Steganographic Image",
                                     font=('Helvetica', 12, 'bold'), bg='#f5f5f5',
                                     padx=20, pady=20)
        decode_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        instructions = tk.Label(decode_frame,
                                text="Select a steganographic image to extract the hidden payload.\n"
                                     "You'll need the same secret key and LSB settings used during encoding.",
                                font=('Helvetica', 10), bg='#f5f5f5', wraplength=500, justify=tk.CENTER)
        instructions.pack(pady=20)

        decode_button = tk.Button(decode_frame, text="🔓 Select Stego Image & Decode",
                                  bg="#2196F3", fg="white", font=("Helvetica", 14, "bold"),
                                  command=self.run_decode, height=2, width=30)
        decode_button.pack(pady=10)

        self.decode_result = tk.Text(decode_frame, height=10, width=90,
                                     font=('Consolas', 10), bg='#f8f8f8',
                                     relief=tk.SUNKEN, bd=2)
        self.decode_result.pack(fill=tk.BOTH, expand=True, pady=10)

    # -------------------- VIDEO ENCODE TAB --------------------
    def setup_video_encode_tab(self, parent):
        inner_frame = self.create_scrolled_frame(parent)

        file_frame = tk.LabelFrame(inner_frame, text="Video File Selection", font=('Helvetica', 10, 'bold'),
                                   bg='#f5f5f5', padx=10, pady=10)
        file_frame.pack(fill=tk.X, padx=10, pady=5)

        cover_section = tk.Frame(file_frame, bg='#f5f5f5')
        cover_section.pack(fill=tk.X, pady=5)

        tk.Label(cover_section, text="Cover Video File (MP4 or MKV):", font=('Helvetica', 10, 'bold'),
                 bg='#f5f5f5').pack(anchor=tk.W)

        cover_input_frame = tk.Frame(cover_section, bg='#f5f5f5')
        cover_input_frame.pack(fill=tk.X, pady=2)

        self.video_cover_entry = tk.Entry(cover_input_frame, textvariable=self.video_cover_path,
                                          font=('Helvetica', 10), state='readonly')
        self.video_cover_entry.pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        tk.Button(cover_input_frame, text="Browse", command=self.browse_video_cover,
                  bg='#4CAF50', fg='white', font=('Helvetica', 9, 'bold')).pack(side=tk.RIGHT)

        self.video_cover_drop_zone = DropZone(cover_section,
                                              "Drag & Drop Cover Video File Here\n(MP4 or MKV format)",
                                              callback=self.set_video_cover,
                                              file_types=['.mp4', '.mkv'])
        self.video_cover_drop_zone.pack(fill=tk.X, pady=5)

        payload_section = tk.Frame(file_frame, bg='#f5f5f5')
        payload_section.pack(fill=tk.X, pady=10)

        tk.Label(payload_section, text="Payload:", font=('Helvetica', 10, 'bold'),
                 bg='#f5f5f5').pack(anchor=tk.W)

        payload_type_frame = tk.Frame(payload_section, bg='#f5f5f5')
        payload_type_frame.pack(fill=tk.X, pady=2)

        tk.Radiobutton(payload_type_frame, text="File", variable=self.video_payload_type,
                       value="file", command=self.toggle_video_payload_input,
                       bg='#f5f5f5', font=('Helvetica', 10)).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(payload_type_frame, text="Text", variable=self.video_payload_type,
                       value="text", command=self.toggle_video_payload_input,
                       bg='#f5f5f5', font=('Helvetica', 10)).pack(side=tk.LEFT, padx=10)

        self.video_payload_file_frame = tk.Frame(payload_section, bg='#f5f5f5')
        self.video_payload_file_frame.pack(fill=tk.X, pady=2)

        self.video_payload_entry = tk.Entry(self.video_payload_file_frame, textvariable=self.video_payload_path,
                                            font=('Helvetica', 10), state='readonly')
        self.video_payload_entry.pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        tk.Button(self.video_payload_file_frame, text="Browse", command=self.browse_video_payload,
                  bg='#2196F3', fg='white', font=('Helvetica', 9, 'bold')).pack(side=tk.RIGHT)

        self.video_payload_drop_zone = DropZone(payload_section,
                                                "Drag & Drop Payload File Here\n(Any file type)",
                                                callback=self.set_video_payload)
        self.video_payload_drop_zone.pack(fill=tk.X, pady=5)

        self.video_payload_text_frame = tk.Frame(payload_section, bg='#f5f5f5')
        self.video_payload_text_area = tk.Text(
            self.video_payload_text_frame, height=4, font=('Helvetica', 10))
        self.video_payload_text_area.pack(fill=tk.X, pady=5)
        self.video_payload_text_area.bind(
            '<<Modified>>', self.update_video_payload_text)

        config_frame = tk.LabelFrame(inner_frame, text="Video Configuration",
                                     font=('Helvetica', 10, 'bold'), bg='#f5f5f5',
                                     padx=10, pady=10)
        config_frame.pack(fill=tk.X, padx=10, pady=5)

        key_frame = tk.Frame(config_frame, bg='#f5f5f5')
        key_frame.pack(fill=tk.X, pady=2)

        tk.Label(key_frame, text="Secret Key:", font=('Helvetica', 10, 'bold'),
                 bg='#f5f5f5').pack(side=tk.LEFT)
        self.video_key_entry = tk.Entry(key_frame, textvariable=self.video_secret_key, width=20,
                                        font=('Helvetica', 10), show="*")
        self.video_key_entry.pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(key_frame, text="Show Key", variable=self.show_video_key,
                       command=self.toggle_video_key_visibility, bg='#f5f5f5',
                       font=('Helvetica', 9)).pack(side=tk.LEFT, padx=5)

        lsb_frame = tk.Frame(config_frame, bg='#f5f5f5')
        lsb_frame.pack(fill=tk.X, pady=5)

        tk.Label(lsb_frame, text="Number of LSBs:", font=('Helvetica', 10, 'bold'),
                 bg='#f5f5f5').pack(side=tk.LEFT)

        video_lsb_slider = Scale(lsb_frame, from_=1, to=8, orient=HORIZONTAL,
                                 variable=self.video_num_lsbs,
                                 command=lambda _=None: (
                                     self.update_video_capacity_display(), self.update_video_visuals()),
                                 bg='#f5f5f5', font=('Helvetica', 9))
        video_lsb_slider.pack(side=tk.LEFT, padx=10)

        self.video_capacity_label = tk.Label(lsb_frame, text="Capacity: N/A",
                                             font=('Helvetica', 10, 'italic'), bg='#f5f5f5')
        self.video_capacity_label.pack(side=tk.LEFT, padx=20)

        info_frame = tk.LabelFrame(inner_frame, text="Video Information",
                                   font=('Helvetica', 10, 'bold'), bg='#f5f5f5',
                                   padx=10, pady=10)
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        self.video_info_label = tk.Label(info_frame, text="Select a video file to view information",
                                         font=('Helvetica', 10), bg='#f5f5f5')
        self.video_info_label.pack(pady=5)

        play_frame = tk.LabelFrame(inner_frame, text="Playback & Compare",
                                   font=('Helvetica', 10, 'bold'), bg='#f5f5f5', padx=10, pady=10)
        play_frame.pack(fill=tk.X, padx=10, pady=5)

        self.btn_play_video_cover_enc = tk.Button(
            play_frame, text="▶ Play Cover Video", bg="#4CAF50", fg="white",
            font=("Helvetica", 10, "bold"), command=self.play_video_cover)
        self.btn_play_video_cover_enc.pack(side=tk.LEFT, padx=5, pady=2)

        self.btn_play_video_stego_enc = tk.Button(
            play_frame, text="▶ Play Stego Video", bg="#9C27B0", fg="white",
            font=("Helvetica", 10, "bold"), command=self.play_video_stego, state=tk.DISABLED)
        self.btn_play_video_stego_enc.pack(side=tk.LEFT, padx=5, pady=2)

        vis_frame = tk.LabelFrame(inner_frame, text="I-Frame Visualisation (LSB changes)",
                                  font=('Helvetica', 10, 'bold'), bg='#f5f5f5',
                                  padx=10, pady=10)
        vis_frame.pack(fill=tk.X, padx=10, pady=5)

        canv_height = 140
        self.video_canvas_cover = tk.Canvas(
            vis_frame, width=540, height=canv_height, bg="#ffffff", bd=1, relief=tk.SUNKEN)
        self.video_canvas_cover.pack(side=tk.LEFT, padx=5, pady=5)
        self.video_canvas_stego = tk.Canvas(
            vis_frame, width=540, height=canv_height, bg="#ffffff", bd=1, relief=tk.SUNKEN)
        self.video_canvas_stego.pack(side=tk.LEFT, padx=5, pady=5)

        self.video_flip_label = tk.Label(
            inner_frame, text="LSB flips: N/A", bg="#f5f5f5", font=("Helvetica", 10, "italic"))
        self.video_flip_label.pack(anchor=tk.W, padx=20, pady=(0, 10))

        button_frame = tk.Frame(inner_frame, bg='#f5f5f5')
        button_frame.pack(fill=tk.X, padx=10, pady=(10, 20))

        tk.Button(button_frame, text="📹 Encode Video Payload", bg="#4CAF50", fg="white",
                  font=("Helvetica", 12, "bold"), command=self.run_video_encode,
                  height=2, width=25).pack(side=tk.LEFT, padx=10)

        tk.Button(button_frame, text="🗑️ Clear All", bg="#FF9800", fg="white",
                  font=("Helvetica", 12, "bold"), command=self.clear_video_all,
                  height=2, width=15).pack(side=tk.LEFT, padx=10)

        self.toggle_video_payload_input()

    # -------------------- VIDEO DECODE TAB --------------------
    def setup_video_decode_tab(self, parent):
        decode_frame = tk.LabelFrame(parent, text="Decode Steganographic Video",
                                     font=('Helvetica', 12, 'bold'), bg='#f5f5f5',
                                     padx=20, pady=20)
        decode_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        instructions = tk.Label(decode_frame,
                                text="Select a steganographic MP4 or MKV file to extract the hidden payload from its I-frames.\n"
                                     "Use the same secret key and LSB settings as during encoding.",
                                font=('Helvetica', 10), bg='#f5f5f5', wraplength=700, justify=tk.CENTER)
        instructions.pack(pady=10)

        play_frame = tk.LabelFrame(decode_frame, text="Playback (Decode Tab)",
                                   font=('Helvetica', 10, 'bold'), bg='#f5f5f5', padx=10, pady=10)
        play_frame.pack(fill=tk.X, padx=10, pady=5)

        self.btn_play_video_stego_dec = tk.Button(
            play_frame, text="▶ Play Stego Video (choose file)", bg="#9C27B0", fg="white",
            font=("Helvetica", 10, "bold"), command=self.play_video_stego)
        self.btn_play_video_stego_dec.pack(side=tk.LEFT, padx=5, pady=2)

        self.video_stego_canvas_dec = tk.Canvas(
            decode_frame, width=1100, height=140, bg="#ffffff", bd=1, relief=tk.SUNKEN)
        self.video_stego_canvas_dec.pack(fill=tk.X, padx=10, pady=10)

        decode_button = tk.Button(decode_frame, text="📹 Select Stego Video & Decode",
                                  bg="#2196F3", fg="white", font=("Helvetica", 14, "bold"),
                                  command=self.run_video_decode, height=2, width=30)
        decode_button.pack(pady=10)

        self.video_decode_result = tk.Text(decode_frame, height=10, width=90,
                                           font=('Consolas', 10), bg='#f8f8f8',
                                           relief=tk.SUNKEN, bd=2)
        self.video_decode_result.pack(fill=tk.BOTH, expand=True, pady=10)

    # -------------------- BROWSE / SET FUNCTIONS --------------------
    def browse_cover(self):
        path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.bmp *.jpg *.jpeg")])
        if path:
            self.set_cover_image(path)

    def set_cover_image(self, path):
        self.cover_path.set(path)
        self.cover_drop_zone.update_text(os.path.basename(path))
        self.cover_orig_path = path
        self.display_cover_on_canvas(self.cover_canvas)
        self.update_capacity_display()

    def display_cover_on_canvas(self, canvas):
        self.redisplay_cover()

    def browse_payload(self):
        path = filedialog.askopenfilename()
        if path:
            self.set_payload_file(path)

    def set_payload_file(self, path):
        self.payload_path.set(path)
        self.payload_drop_zone.update_text(os.path.basename(path))
        self.update_capacity_display()

    def browse_audio_cover(self):
        path = filedialog.askopenfilename(filetypes=[("WAV files", "*.wav")])
        if path:
            self.set_audio_cover(path)

    def set_audio_cover(self, path):
        self.audio_cover_path.set(path)
        self.audio_cover_drop_zone.update_text(os.path.basename(path))
        self.update_audio_info()
        self.update_audio_capacity_display()
        self.update_audio_visuals()

    def browse_audio_payload(self):
        path = filedialog.askopenfilename()
        if path:
            self.set_audio_payload(path)

    def set_audio_payload(self, path):
        self.audio_payload_path.set(path)
        self.audio_payload_drop_zone.update_text(os.path.basename(path))
        self.update_audio_capacity_display()

    def browse_video_cover(self):
        path = filedialog.askopenfilename(
            filetypes=[("Video files", "*.mp4 *.mkv")])
        if path:
            self.set_video_cover(path)

    def set_video_cover(self, path):
        self.video_cover_path.set(path)
        self.video_cover_drop_zone.update_text(os.path.basename(path))
        self.update_video_info()
        self.update_video_capacity_display()
        self.update_video_visuals()

    def browse_video_payload(self):
        path = filedialog.askopenfilename()
        if path:
            self.set_video_payload(path)

    def set_video_payload(self, path):
        self.video_payload_path.set(path)
        self.video_payload_drop_zone.update_text(os.path.basename(path))
        self.update_video_capacity_display()

    # -------------------- TOGGLE INPUTS --------------------
    def toggle_payload_input(self):
        if self.payload_type.get() == "file":
            self.payload_text_frame.pack_forget()
            self.payload_file_frame.pack(fill=tk.X, pady=2)
            self.payload_drop_zone.pack(fill=tk.X, pady=5)
            self.payload_text.set("")
        else:
            self.payload_file_frame.pack_forget()
            self.payload_drop_zone.pack_forget()
            self.payload_text_frame.pack(fill=tk.X, pady=5)
            self.payload_path.set("")

        self.update_capacity_display()

    def toggle_audio_payload_input(self):
        if self.audio_payload_type.get() == "file":
            self.audio_payload_text_frame.pack_forget()
            self.audio_payload_file_frame.pack(fill=tk.X, pady=2)
            self.audio_payload_drop_zone.pack(fill=tk.X, pady=5)
            self.audio_payload_text.set("")
        else:
            self.audio_payload_file_frame.pack_forget()
            self.audio_payload_drop_zone.pack_forget()
            self.audio_payload_text_frame.pack(fill=tk.X, pady=5)
            self.audio_payload_path.set("")

        self.update_audio_capacity_display()

    def toggle_video_payload_input(self):
        if self.video_payload_type.get() == "file":
            self.video_payload_text_frame.pack_forget()
            self.video_payload_file_frame.pack(fill=tk.X, pady=2)
            self.video_payload_drop_zone.pack(fill=tk.X, pady=5)
            self.video_payload_text.set("")
        else:
            self.video_payload_file_frame.pack_forget()
            self.video_payload_drop_zone.pack_forget()
            self.video_payload_text_frame.pack(fill=tk.X, pady=5)
            self.video_payload_path.set("")

        self.update_video_capacity_display()

    def update_payload_text(self, event=None):
        self.payload_text.set(
            self.payload_text_area.get("1.0", tk.END).strip())
        self.update_capacity_display()

    def update_audio_payload_text(self, event=None):
        self.audio_payload_text.set(
            self.audio_payload_text_area.get("1.0", tk.END).strip())
        self.update_audio_capacity_display()

    def update_video_payload_text(self, event=None):
        self.video_payload_text.set(
            self.video_payload_text_area.get("1.0", tk.END).strip())
        self.update_video_capacity_display()

    # -------------------- KEY VISIBILITY --------------------
    def toggle_key_visibility(self):
        show = "" if self.show_key.get() else "*"
        self.key_entry.config(show=show)

    def toggle_audio_key_visibility(self):
        show = "" if self.show_audio_key.get() else "*"
        self.audio_key_entry.config(show=show)

    def toggle_video_key_visibility(self):
        show = "" if self.show_video_key.get() else "*"
        self.video_key_entry.config(show=show)

    # -------------------- AUDIO INFO UPDATE --------------------
    def update_audio_info(self):
        path = self.audio_cover_path.get()
        if not path:
            self.audio_info_label.config(
                text="Select an audio file to view information")
            return
        try:
            with wave.open(path, 'rb') as wav:
                params = wav.getparams()
                duration = params.nframes / params.framerate
                info = f"Duration: {duration:.2f} s | Sample Rate: {params.framerate} Hz | "
                info += f"Channels: {params.nchannels} | Bit Depth: {params.sampwidth * 8} bits"
            self.audio_info_label.config(text=info)
        except Exception as e:
            self.audio_info_label.config(text=f"Error reading audio info: {e}")

    # -------------------- VIDEO INFO UPDATE --------------------
    def update_video_info(self):
        path = self.video_cover_path.get()
        if not path:
            self.video_info_label.config(
                text="Select a video file to view information")
            return
        try:
            params = self.get_video_params(path)
            duration = params['duration']
            resolution = f"{params['width']}x{params['height']}"
            fps = params['fps']
            i_frame_count = params['i_frame_count']
            info = f"Duration: {duration:.2f} s | Resolution: {resolution} | FPS: {fps:.2f} | I-frames: {i_frame_count} (Capacity based on first I-frame only)"
            self.video_info_label.config(text=info)
        except Exception as e:
            self.video_info_label.config(text=f"Error reading video info: {e}")

    def get_video_params(self, video_path):
        if shutil.which("ffprobe") is None:
            raise ValueError("FFprobe not found. Please install FFmpeg.")

        # Get stream info (width, height, fps)
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height,r_frame_rate",
             "-of", "json", video_path],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            raise ValueError("Failed to get video stream info.")
            raise ValueError("Failed to get video stream info.")
        data = json.loads(result.stdout)
        if not data.get("streams"):
            raise ValueError("No video stream found.")
        stream = data["streams"][0]
        width = int(stream.get("width", 0))
        height = int(stream.get("height", 0))
        fps_frac = stream.get("r_frame_rate", "0/1")
        fps = eval(fps_frac) if '/' in fps_frac else float(fps_frac)

        # Get overall duration from format level (more reliable for MKV/MP4)
        result_format = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "json", video_path],
            capture_output=True, text=True
        )
        if result_format.returncode != 0:
            raise ValueError("Failed to get video duration.")
        format_data = json.loads(result_format.stdout)
        duration = float(format_data.get("format", {}).get("duration", 0))

        # Count I-frames (unchanged)
        result_frames = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "frame=pict_type", "-of", "json", video_path],
            capture_output=True, text=True
        )
        frames_data = json.loads(result_frames.stdout)
        i_frame_count = sum(1 for f in frames_data.get(
            "frames", []) if f.get("pict_type") == "I")

        return {
            'width': width,
            'height': height,
            'fps': fps,
            'duration': duration,
            'i_frame_count': i_frame_count
        }

    # -------------------- PLAY FUNCTIONS --------------------
    def play_audio_cover(self):
        self.play_audio(self.audio_cover_path.get())

    def play_audio_stego(self):
        path = self.audio_stego_path.get() or self.audio_decode_stego_path.get()
        self.play_audio(path)

    def play_audio(self, path):
        if not path:
            return
        self.stop_audio()
        if platform.system() == 'Windows':
            os.startfile(path)
        else:
            self._audio_proc = subprocess.Popen(
                ["afplay" if platform.system() == 'Darwin' else "aplay", path])

    def ab_toggle(self):
        if self._ab_state == "cover":
            self.play_audio_stego()
            self._ab_state = "stego"
        else:
            self.play_audio_cover()
            self._ab_state = "cover"

    def stop_audio(self):
        if self._audio_proc:
            self._audio_proc.terminate()
            self._audio_proc = None

    def play_video_cover(self):
        self.open_file(self.video_cover_path.get())

    def play_video_stego(self):
        path = self.video_stego_path.get() or self.video_decode_stego_path.get()
        self.open_file(path)

    # -------------------- VISUALS --------------------
    def update_audio_visuals(self):
        cover_path = self.audio_cover_path.get()
        stego_path = self.audio_stego_path.get()
        if cover_path:
            self._draw_waveform(self.audio_canvas_cover, cover_path, "Cover")
        if stego_path:
            self._draw_waveform(self.audio_canvas_stego, stego_path, "Stego")
            flips = self._calculate_lsb_flips(
                cover_path, stego_path, self.audio_num_lsbs.get())
            self.audio_flip_label.config(text=f"LSB flips: {flips}")
        else:
            self.audio_canvas_stego.delete("all")
            self.audio_flip_label.config(text="LSB flips: N/A")

    def update_video_visuals(self):
        cover_path = self.video_cover_path.get()
        stego_path = self.video_stego_path.get()
        if not cover_path:
            return
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                cover_iframe = self._extract_first_iframe(
                    cover_path, tmpdir, "cover_iframe.png")
                self.display_image_on_canvas(
                    cover_iframe, self.video_canvas_cover)
                if stego_path:
                    stego_iframe = self._extract_first_iframe(
                        stego_path, tmpdir, "stego_iframe.png")
                    self.display_image_on_canvas(
                        stego_iframe, self.video_canvas_stego)
                    diff_path = self._create_difference_map(
                        cover_iframe, stego_iframe)
                    self.display_image_on_canvas(
                        diff_path, self.video_canvas_stego, overlay=True)
                    flips = self._calculate_lsb_flips_image(
                        cover_iframe, stego_iframe, self.video_num_lsbs.get())
                    self.video_flip_label.config(
                        text=f"LSB flips (first I-frame): {flips}")
                else:
                    self.video_canvas_stego.delete("all")
                    self.video_flip_label.config(text="LSB flips: N/A")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update visuals: {e}")

    def _extract_first_iframe(self, video_path, tmpdir, output_name):
        output_path = os.path.join(tmpdir, output_name)
        subprocess.check_call(
            ["ffmpeg", "-i", video_path, "-vf",
                "select='eq(pict_type\\,I)'", "-vsync", "vfr", "-frames:v", "1", output_path],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        return output_path

    def _draw_waveform(self, canvas, audio_path, title):
        canvas.delete("all")
        try:
            with wave.open(audio_path, 'rb') as wav:
                params = wav.getparams()
                frames = wav.readframes(params.nframes)
                data = np.frombuffer(
                    frames, dtype=np.int16 if params.sampwidth == 2 else np.int8)
            width, height = canvas.winfo_width(), canvas.winfo_height()
            canvas.create_text(width/2, 10, text=title)
            if len(data) == 0:
                return
            step = max(1, len(data) // width)
            max_amp = 2 ** (params.sampwidth * 8 - 1)
            scale = (height - 20) / 2 / max_amp
            mid = height / 2
            for x in range(width):
                chunk = data[x*step:(x+1)*step]
                if len(chunk) > 0:
                    amp = abs(chunk).max()
                    y = amp * scale
                    canvas.create_line(x, mid - y, x, mid + y)
        except Exception:
            pass

    def _calculate_lsb_flips(self, cover_path, stego_path, num_lsbs):
        try:
            with wave.open(cover_path, 'rb') as c_wav, wave.open(stego_path, 'rb') as s_wav:
                c_params = c_wav.getparams()
                s_params = s_wav.getparams()
                if c_params != s_params:
                    return "N/A (mismatch)"
                c_data = np.frombuffer(c_wav.readframes(
                    c_params.nframes), dtype=np.int16 if c_params.sampwidth == 2 else np.int8)
                s_data = np.frombuffer(s_wav.readframes(
                    s_params.nframes), dtype=np.int16 if s_params.sampwidth == 2 else np.int8)
            mask = (1 << num_lsbs) - 1
            flips = np.sum((c_data & mask) != (s_data & mask))
            return flips
        except Exception:
            return "N/A"

    def _calculate_lsb_flips_image(self, cover_path, stego_path, num_lsbs):
        try:
            cover_img = Image.open(cover_path).convert('RGB')
            stego_img = Image.open(stego_path).convert('RGB')
            if cover_img.size != stego_img.size:
                return "N/A (mismatch)"
            width, height = cover_img.size
            cp, sp = cover_img.load(), stego_img.load()
            flips = 0
            mask = (1 << num_lsbs) - 1
            for y in range(height):
                for x in range(width):
                    for ch in range(3):
                        if (cp[x, y][ch] & mask) != (sp[x, y][ch] & mask):
                            flips += 1
            return flips
        except Exception:
            return "N/A"

    # -------------------- RUN ENCODE/DECODE --------------------
    def run_encode(self):
        cover_path = self.cover_path.get()
        key = self.secret_key.get()
        num_lsbs = self.num_lsbs.get()

        if not cover_path:
            messagebox.showerror("Error", "Please select a cover image.")
            return
        if not key:
            messagebox.showerror("Error", "Please enter a secret key.")
            return

        if self.payload_type.get() == "file":
            payload_path = self.payload_path.get()
            if not payload_path:
                messagebox.showerror("Error", "Please select a payload file.")
                return
            with open(payload_path, 'rb') as f:
                payload_data = f.read()
            filename = os.path.basename(payload_path)
        else:
            self.update_payload_text()  # Ensure text is updated
            text = self.payload_text.get()
            if not text:
                messagebox.showerror("Error", "Please enter payload text.")
                return
            payload_data = text.encode('utf-8')
            filename = "text_payload.txt"

        try:
            stego_path = self._encode_image(
                cover_path, payload_data, filename, key, num_lsbs)
            self.stego_path.set(stego_path)
            diff_path = self._create_difference_map(cover_path, stego_path)
            self.display_image_on_canvas(
                stego_path, self.stego_canvas, label="Stego")
            self.display_image_on_canvas(
                diff_path, self.stego_canvas, label="Difference Map", overlay=False)
            messagebox.showinfo(
                "Success", f"Stego image saved as: {stego_path}")
        except ValueError as e:
            messagebox.showerror("Encoding Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {e}")

    def run_decode(self):
        stego_path = filedialog.askopenfilename(title="Select Stego Image", filetypes=[
                                                ("Image files", "*.png *.bmp *.jpg *.jpeg")])
        if not stego_path:
            return

        # New: Single dialog for key and LSB
        dialog = KeyLsbDialog(self, title="Enter Decoding Credentials")
        if dialog.result is None:
            return  # User canceled

        key, user_lsbs = dialog.result

        try:
            extracted_path, is_text = self._decode_image(
                stego_path, key, user_lsbs)

            result_text = f"✅ Payload extracted successfully!\n\n"
            result_text += f"📁 Extracted file: {extracted_path}\n"
            result_text += f"📊 File size: {os.path.getsize(extracted_path)} bytes\n"
            result_text += f"🔑 Key used: [Hidden]\n"
            result_text += f"⚙️ LSBs used: {user_lsbs}\n"
            if is_text:
                with open(extracted_path, 'r', encoding='utf-8') as f:
                    content = f.read()[:1000]
                result_text += f"\n📝 Extracted text:\n{content}"

            self.decode_result.delete(1.0, tk.END)
            self.decode_result.insert(1.0, result_text)

            if messagebox.askyesno("Success", f"✅ Payload extracted!\n📁 Saved as: {os.path.basename(extracted_path)}\n\n🔍 Open now?"):
                self.open_file(extracted_path)

        except Exception as e:
            error_text = f"❌ Failed to decode: {e}\n\n"
            error_text += "Please check:\n"
            error_text += "• Correct secret key\n"
            error_text += "• Correct LSB value (must match encoding)\n"
            error_text += "• Valid stego image file\n"

            self.decode_result.delete(1.0, tk.END)
            self.decode_result.insert(1.0, error_text)
            messagebox.showerror("Decoding Error", f"Failed to decode: {e}")

    def run_audio_encode(self):
        cover_path = self.audio_cover_path.get()
        key = self.audio_secret_key.get()
        num_lsbs = self.audio_num_lsbs.get()

        if not cover_path:
            messagebox.showerror("Error", "Please select a cover audio file.")
            return
        if not key:
            messagebox.showerror("Error", "Please enter a secret key.")
            return

        if self.audio_payload_type.get() == "file":
            payload_path = self.audio_payload_path.get()
            if not payload_path:
                messagebox.showerror("Error", "Please select a payload file.")
                return
            with open(payload_path, 'rb') as f:
                payload_data = f.read()
            filename = os.path.basename(payload_path)
        else:
            self.update_audio_payload_text()  # Ensure text is updated
            text = self.audio_payload_text.get()
            if not text:
                messagebox.showerror("Error", "Please enter payload text.")
                return
            payload_data = text.encode('utf-8')
            filename = "text_payload.txt"

        try:
            stego_path = self._encode_audio(
                cover_path, payload_data, filename, key, num_lsbs)
            self.audio_stego_path.set(stego_path)
            self.btn_play_stego_enc.config(state=tk.NORMAL)
            try:
                self.btn_play_stego_dec.config(state=tk.NORMAL)
            except Exception:
                pass

            # Update visuals (waveforms + flip count)
            self.update_audio_visuals()

            messagebox.showinfo(
                "Success", f"Stego audio saved as: {stego_path}")
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

        self.audio_decode_stego_path.set(stego_path)
        self._draw_waveform(self.audio_stego_canvas_dec,
                            stego_path, title="Stego (Decode)")

        # New: Single dialog for key and LSB
        dialog = KeyLsbDialog(self, title="Enter Decoding Credentials")
        if dialog.result is None:
            return  # User canceled

        key, user_lsbs = dialog.result

        try:
            extracted_path, is_text = self._decode_audio(
                stego_path, key, user_lsbs)

            result_text = f"✅ Payload extracted successfully!\n\n"
            result_text += f"📁 Extracted file: {extracted_path}\n"
            result_text += f"📊 File size: {os.path.getsize(extracted_path)} bytes\n"
            result_text += f"🔑 Key used: [Hidden]\n"
            result_text += f"⚙️ LSBs used: {user_lsbs}\n"
            if is_text:
                with open(extracted_path, 'r', encoding='utf-8') as f:
                    result_text += f"\n📝 Extracted text:\n{f.read()[:1000]}"

            self.audio_decode_result.delete(1.0, tk.END)
            self.audio_decode_result.insert(1.0, result_text)

            if messagebox.askyesno("Success",
                                   f"✅ Payload extracted!\n📁 Saved as: {os.path.basename(extracted_path)}\n\n🔍 Open now?"):
                self.open_file(extracted_path)

        except Exception as e:
            error_text = f"❌ Failed to decode: {e}\n\n"
            error_text += "Please check:\n"
            error_text += "• Correct secret key\n"
            error_text += "• Correct LSB value (must match encoding)\n"
            error_text += "• Valid stego audio file\n"

            self.audio_decode_result.delete(1.0, tk.END)
            self.audio_decode_result.insert(1.0, error_text)
            messagebox.showerror("Decoding Error", f"Failed to decode: {e}")

    def run_video_encode(self):
        if shutil.which("ffmpeg") is None:
            messagebox.showerror(
                "Error", "FFmpeg not found. Please install FFmpeg to use video steganography.")
            return

        cover_path = self.video_cover_path.get()
        key = self.video_secret_key.get()
        num_lsbs = self.video_num_lsbs.get()

        if not cover_path:
            messagebox.showerror("Error", "Please select a cover video file.")
            return
        if not key:
            messagebox.showerror("Error", "Please enter a secret key.")
            return

        if self.video_payload_type.get() == "file":
            payload_path = self.video_payload_path.get()
            if not payload_path:
                messagebox.showerror("Error", "Please select a payload file.")
                return
            with open(payload_path, 'rb') as f:
                payload_data = f.read()
            filename = os.path.basename(payload_path)
        else:
            self.update_video_payload_text()  # Ensure text is updated
            text = self.video_payload_text.get()
            if not text:
                messagebox.showerror("Error", "Please enter payload text.")
                return
            payload_data = text.encode('utf-8')
            filename = "text_payload.txt"

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                # Extract first I-frame as PNG
                iframe_path = os.path.join(tmpdir, "iframe.png")
                result = subprocess.run(
                    ["ffmpeg", "-i", cover_path, "-vf",
                        "select='eq(pict_type\\,I)'", "-vsync", "vfr", "-frames:v", "1", iframe_path],
                    capture_output=True, text=True
                )
                if result.returncode != 0:
                    print(f"I-frame extraction failed:")
                    print(f"stdout: {result.stdout}")
                    print(f"stderr: {result.stderr}")
                    raise subprocess.CalledProcessError(
                        result.returncode, result.args)

                if not os.path.exists(iframe_path):
                    raise ValueError("No I-frame found in video.")

                print("I-frame extraction successful")

                # Embed payload into the I-frame using image method (full region)
                stego_iframe = self._encode_image(
                    iframe_path, payload_data, filename, key, num_lsbs)
                print(f"Stego I-frame created: {stego_iframe}")

                # Get video params and frame duration
                params = self.get_video_params(cover_path)
                frame_duration = 1 / params['fps']
                timestamp = self._get_first_iframe_timestamp(cover_path)
                print(
                    f"Video params: FPS={params['fps']}, frame_duration={frame_duration}, timestamp={timestamp}")

                # Build filter_complex to replace the I-frame
                if timestamp == 0:
                    # First I-frame at start: concat stego frame + rest of video
                    filter_complex = f"[1:v]setpts=PTS[v2]; [0:v]trim={frame_duration}:,setpts=PTS-STARTPTS[v3]; [v2][v3]concat=n=2:v=1:a=0[v]"
                else:
                    # First I-frame not at start: concat before + stego frame + after
                    filter_complex = f"[0:v]trim=0:{timestamp},setpts=PTS-STARTPTS[v1]; [1:v]setpts=PTS+{timestamp}[v2]; [0:v]trim={timestamp + frame_duration}:,setpts=PTS-STARTPTS[v3]; [v1][v2][v3]concat=n=3:v=1:a=0[v]"

                print(f"Filter complex: {filter_complex}")

                # Re-encode video with stego I-frame inserted, using FFV1 (lossless) in MKV
                base_name = os.path.splitext(os.path.basename(cover_path))[0]
                stego_path = os.path.join(os.path.dirname(
                    cover_path), f"stego_{base_name}.mkv")
                print(f"Final encoding to: {stego_path}")

                result = subprocess.run(
                    ["ffmpeg", "-y", "-i", cover_path, "-i", stego_iframe, "-filter_complex", filter_complex,
                     "-map", "[v]", "-map", "0:a?", "-c:v", "ffv1", "-c:a", "copy", stego_path],
                    capture_output=True, text=True
                )
                if result.returncode != 0:
                    print(f"Final encoding failed:")
                    print(f"stdout: {result.stdout}")
                    print(f"stderr: {result.stderr}")
                    raise subprocess.CalledProcessError(
                        result.returncode, result.args)

                print("Final encoding successful")

            self.video_stego_path.set(stego_path)
            self.btn_play_video_stego_enc.config(state=tk.NORMAL)

            self.update_video_visuals()

            messagebox.showinfo(
                "Success", f"Stego video saved as: {stego_path}")

        except subprocess.CalledProcessError as e:
            messagebox.showerror(
                "Error", f"FFmpeg failed during processing. Check console for details.")
        except ValueError as e:
            messagebox.showerror("Encoding Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {e}")

    def _get_first_iframe_timestamp(self, video_path):
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "frame=pts_time,pict_type", "-of", "json", video_path],
            capture_output=True, text=True
        )
        frames = json.loads(result.stdout).get("frames", [])
        for f in frames:
            if f.get("pict_type") == "I":
                return float(f.get("pts_time", 0))
        return 0.0

    def run_video_decode(self):
        if shutil.which("ffmpeg") is None:
            messagebox.showerror(
                "Error", "FFmpeg not found. Please install FFmpeg to use video steganography.")
            return

        stego_path = filedialog.askopenfilename(
            title="Select Stego-Video File",
            filetypes=[("Video files", "*.mp4 *.mkv")]
        )
        if not stego_path:
            return

        self.video_decode_stego_path.set(stego_path)

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                iframe_path = os.path.join(tmpdir, "stego_iframe.png")
                subprocess.check_call(
                    ["ffmpeg", "-i", stego_path, "-vf",
                        "select='eq(pict_type\\,I)'", "-vsync", "vfr", "-frames:v", "1", iframe_path],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                if not os.path.exists(iframe_path):
                    raise ValueError("No I-frame found in video.")
                self.display_image_on_canvas(
                    iframe_path, self.video_stego_canvas_dec)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to draw I-frame: {e}")

        # New: Single dialog for key and LSB
        dialog = KeyLsbDialog(self, title="Enter Decoding Credentials")
        if dialog.result is None:
            return  # User canceled

        key, user_lsbs = dialog.result

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                iframe_path = os.path.join(tmpdir, "stego_iframe.png")
                subprocess.check_call(
                    ["ffmpeg", "-i", stego_path, "-vf",
                        "select='eq(pict_type\\,I)'", "-vsync", "vfr", "-frames:v", "1", iframe_path],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                extracted_path, is_text = self._decode_image(
                    iframe_path, key, user_lsbs)  # Pass user_lsbs

                # Move extracted file to permanent location before temp dir deletion
                permanent_dir = os.path.dirname(stego_path)
                permanent_path = os.path.join(
                    permanent_dir, os.path.basename(extracted_path))
                shutil.move(extracted_path, permanent_path)
                extracted_path = permanent_path

            result_text = f"✅ Payload extracted successfully!\n\n"
            result_text += f"📁 Extracted file: {extracted_path}\n"
            result_text += f"📊 File size: {os.path.getsize(extracted_path)} bytes\n"
            result_text += f"🔑 Key used: [Hidden]\n"
            result_text += f"⚙️ LSBs used: {user_lsbs}\n"
            if is_text:
                with open(extracted_path, 'r', encoding='utf-8') as f:
                    result_text += f"\n📝 Extracted text:\n{f.read()[:1000]}"

            self.video_decode_result.delete(1.0, tk.END)
            self.video_decode_result.insert(1.0, result_text)

            if messagebox.askyesno("Success",
                                   f"✅ Payload extracted!\n📁 Saved as: {os.path.basename(extracted_path)}\n\n🔍 Open now?"):
                self.open_file(extracted_path)

        except Exception as e:
            error_text = f"❌ Failed to decode: {e}\n\n"
            error_text += "Please check:\n"
            error_text += "• Correct secret key\n"
            error_text += "• Correct LSB value (must match encoding)\n"
            error_text += "• Valid stego video file with I-frames\n"

            self.video_decode_result.delete(1.0, tk.END)
            self.video_decode_result.insert(1.0, error_text)
            messagebox.showerror("Decoding Error", f"Failed to decode: {e}")

    # -------------------- CLEAR / CAPACITY / OPEN --------------------
    def clear_audio_all(self):
        self.stop_audio()
        self.audio_cover_path.set("")
        self.audio_payload_path.set("")
        self.audio_stego_path.set("")     # NEW: reset stego path
        self.audio_decode_stego_path.set("")
        self.audio_secret_key.set("")
        self.audio_num_lsbs.set(1)
        self.audio_payload_type.set("file")
        self.audio_payload_text.set("")
        self.audio_capacity_label.config(text="Capacity: N/A")
        self.audio_info_label.config(
            text="Select an audio file to view information")
        self.show_audio_key.set(False)
        try:
            self.audio_key_entry.config(show="*")
        except Exception:
            pass

        self.audio_cover_drop_zone.update_text(
            "Drag & Drop Cover Audio File Here\n(WAV format)")
        self.audio_payload_drop_zone.update_text(
            "Drag & Drop Payload File Here\n(Any file type)")
        self.audio_cover_drop_zone.reset_colors()
        self.audio_payload_drop_zone.reset_colors()
        self.audio_payload_text_area.delete("1.0", tk.END)
        self.toggle_audio_payload_input()

        # clear visuals
        if hasattr(self, 'audio_canvas_cover'):
            self.audio_canvas_cover.delete("all")
        if hasattr(self, 'audio_canvas_stego'):
            self.audio_canvas_stego.delete("all")
        if hasattr(self, 'audio_stego_canvas_dec'):
            self.audio_stego_canvas_dec.delete("all")
        self.audio_flip_label.config(text="LSB flips: N/A")

        # disable stego button on encode tab
        try:
            self.btn_play_stego_enc.config(state=tk.DISABLED)
        except Exception:
            pass

    def clear_video_all(self):
        self.video_cover_path.set("")
        self.video_payload_path.set("")
        self.video_stego_path.set("")
        self.video_decode_stego_path.set("")
        self.video_secret_key.set("")
        self.video_num_lsbs.set(1)
        self.video_payload_type.set("file")
        self.video_payload_text.set("")
        self.video_capacity_label.config(text="Capacity: N/A")
        self.video_info_label.config(
            text="Select a video file to view information")
        self.show_video_key.set(False)
        try:
            self.video_key_entry.config(show="*")
        except Exception:
            pass

        self.video_cover_drop_zone.update_text(
            "Drag & Drop Cover Video File Here\n(MP4 or MKV format)")
        self.video_payload_drop_zone.update_text(
            "Drag & Drop Payload File Here\n(Any file type)")
        self.video_cover_drop_zone.reset_colors()
        self.video_payload_drop_zone.reset_colors()
        self.video_payload_text_area.delete("1.0", tk.END)
        self.toggle_video_payload_input()

        # clear visuals
        if hasattr(self, 'video_canvas_cover'):
            self.video_canvas_cover.delete("all")
        if hasattr(self, 'video_canvas_stego'):
            self.video_canvas_stego.delete("all")
        if hasattr(self, 'video_stego_canvas_dec'):
            self.video_stego_canvas_dec.delete("all")
        self.video_flip_label.config(text="LSB flips: N/A")

        # disable stego button
        try:
            self.btn_play_video_stego_enc.config(state=tk.DISABLED)
        except Exception:
            pass

    def clear_all(self):
        self.cover_path.set("")
        self.payload_path.set("")
        self.secret_key.set("")
        self.num_lsbs.set(1)
        self.payload_type.set("file")
        self.payload_text.set("")
        self.cover_orig_path = None
        self.orig_size = None
        self.scale = 1.0
        self.scaled_size = (0, 0)
        self.embed_region_orig = None
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

    # -------------------- CORE ENCODERS/DECODERS --------------------
    def _encode_image(self, cover_path, payload_data, filename, key, num_lsbs):
        MAGIC = b"STG2"
        HEADER_LSBS = 1  # fixed so decode can always read

        key_hash, seed = self.hash_key(key)
        fn_bytes = filename.encode("utf-8")[:255]
        fn_len = len(fn_bytes)

        with Image.open(cover_path).convert("RGB") as image:
            width, height = image.size
            if width > 65535 or height > 65535:
                raise ValueError("Image too large (dims must fit in uint16).")

            reg = self.get_embed_region_in_original()
            if reg:
                x1, y1, x2, y2 = reg
            else:
                x1 = y1 = x2 = y2 = 0  # sentinel for "full image"

            # Fixed header (21 bytes)
            header = (
                MAGIC +
                key_hash[:4] +
                len(payload_data).to_bytes(4, "big") +
                bytes([fn_len]) +
                int(x1).to_bytes(2, "big") + int(y1).to_bytes(2, "big") +
                int(x2).to_bytes(2, "big") + int(y2).to_bytes(2, "big")
            )

            body = fn_bytes + payload_data

            hdr_bits = bitarray()
            hdr_bits.frombytes(header)
            body_bits = bitarray()
            body_bits.frombytes(body)

            pixels = image.load()
            all_pos = [(x, y) for y in range(height) for x in range(width)]

            def embed_bits(positions, bits, per_pixel_lsbs):
                idx = 0
                mask_keep = (255 << per_pixel_lsbs) & 255
                for (x, y) in positions:
                    if idx >= len(bits):
                        break
                    r, g, b = pixels[x, y]
                    rgb = [r, g, b]
                    for i in range(3):
                        if idx >= len(bits):
                            break
                        chunk = bits[idx:idx + per_pixel_lsbs]
                        val = int(chunk.to01().ljust(per_pixel_lsbs, '0'), 2)
                        rgb[i] = (rgb[i] & mask_keep) | val
                        idx += per_pixel_lsbs
                    pixels[x, y] = tuple(rgb)
                return idx

            # 1) Write header with 1 LSB in raster order
            header_bits_needed = len(header) * 8
            hdr_px_needed = (header_bits_needed +
                             (HEADER_LSBS * 3) - 1) // (HEADER_LSBS * 3)
            header_pos = all_pos[:hdr_px_needed]
            if embed_bits(header_pos, hdr_bits, HEADER_LSBS) < len(hdr_bits):
                raise ValueError("Not enough space for header.")

            # 2) Prepare body positions (region, minus header pixels)
            if x1 == y1 == x2 == y2 == 0:
                region_pos = all_pos
            else:
                region_pos = [(x, y) for y in range(y1, y2)
                              for x in range(x1, x2)]
            header_set = set(header_pos)
            region_pos = [p for p in region_pos if p not in header_set]

            max_body_bits = len(region_pos) * 3 * num_lsbs
            if len(body_bits) > max_body_bits:
                raise ValueError(
                    f"Payload too large for selected region/LSBs: "
                    f"{len(body_bits)} bits > {max_body_bits} bits available"
                )

            # Key-driven permutation
            random.seed(seed)
            random.shuffle(region_pos)
            embed_bits(region_pos, body_bits, num_lsbs)

            stego_path = os.path.join(os.path.dirname(
                cover_path), "stego_" + os.path.basename(cover_path))
            image.save(stego_path, "PNG")
            return stego_path

    def _decode_image(self, stego_path, key, num_lsbs):
        MAGIC = b"STG2"
        FIXED_HDR_LEN = 21  # Updated: removed 1 byte for body_num_lsbs
        HEADER_LSBS = 1

        image = Image.open(stego_path).convert("RGB")
        width, height = image.size
        pixels = image.load()

        all_pos = [(x, y) for y in range(height) for x in range(width)]
        header_bits_needed = FIXED_HDR_LEN * 8
        hdr_px_needed = (header_bits_needed +
                         (HEADER_LSBS * 3) - 1) // (HEADER_LSBS * 3)
        header_pos = all_pos[:hdr_px_needed]

        def extract_bits(positions, nbits, per_pixel_lsbs):
            out = bitarray()
            mask = (1 << per_pixel_lsbs) - 1
            for (x, y) in positions:
                if len(out) >= nbits:
                    break
                r, g, b = pixels[x, y]
                for val in (r, g, b):
                    if len(out) >= nbits:
                        break
                    out.extend(bin(val & mask)[2:].zfill(per_pixel_lsbs))
            return out

        # 1) Read header
        hdr_bits = extract_bits(header_pos, header_bits_needed, HEADER_LSBS)
        hdr = hdr_bits.tobytes()[:FIXED_HDR_LEN]
        if hdr[:4] != MAGIC:
            raise ValueError(
                "Unsupported/old stego format or corrupted header.")

        stored_key_prefix = hdr[4:8]
        # Removed: body_num_lsbs = hdr[8]  # No longer stored
        payload_size = int.from_bytes(hdr[8:12], "big")  # Shifted: was 9:13
        filename_len = hdr[12]  # Shifted: was 13
        x1 = int.from_bytes(hdr[13:15], "big")  # Shifted: was 14:16
        y1 = int.from_bytes(hdr[15:17], "big")  # Shifted: was 16:18
        x2 = int.from_bytes(hdr[17:19], "big")  # Shifted: was 18:20
        y2 = int.from_bytes(hdr[19:21], "big")  # Shifted: was 20:22

        key_hash, seed = self.hash_key(key)
        if stored_key_prefix != key_hash[:4]:
            raise ValueError("Wrong secret key.")

        # 2) Region & positions (minus header)
        if x1 == y1 == x2 == y2 == 0:
            region_pos = all_pos
        else:
            region_pos = [(x, y) for y in range(y1, y2) for x in range(x1, x2)]
        header_set = set(header_pos)
        region_pos = [p for p in region_pos if p not in header_set]

        total_body_bits = (filename_len + payload_size) * 8
        random.seed(seed)
        random.shuffle(region_pos)

        # 3) Extract body with user-provided LSBs
        body_bits = extract_bits(region_pos, total_body_bits, num_lsbs)
        if len(body_bits) < total_body_bits:
            raise ValueError("Incomplete embedded data (region/LSB mismatch).")

        body = body_bits.tobytes()
        filename = body[:filename_len].decode("utf-8", errors="replace")
        payload = body[filename_len:filename_len + payload_size]

        extracted_path = os.path.join(os.path.dirname(
            stego_path), f"extracted_{filename}")
        with open(extracted_path, "wb") as f:
            f.write(payload)
        is_text = filename.endswith(".txt")
        return extracted_path, is_text

    def _encode_audio(self, cover_path, payload_data, filename, key, num_lsbs):
        key_hash, seed = self.hash_key(key)
        key_hash = key_hash[:4]  # Use only first 4 bytes for embedding
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
            audio_data = np.frombuffer(frames, dtype=np.uint16).copy()
            max_val, min_val = 65535, 0
        elif params.sampwidth == 3:
            raw = np.frombuffer(frames, dtype=np.uint8).reshape(-1, 3)
            audio_data = (
                raw[:, 0].astype(np.uint32)
                | (raw[:, 1].astype(np.uint32) << 8)
                | (raw[:, 2].astype(np.uint32) << 16)
            )
            audio_data = audio_data & 0xFFFFFF
            max_val, min_val = 16777215, 0
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
            bits_to_embed = int(chunk.to01().ljust(num_lsbs, '0'), 2)

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
            audio_data = (raw[:, 0].astype(np.uint32) |
                          (raw[:, 1].astype(np.uint32) << 8) |
                          (raw[:, 2].astype(np.uint32) << 16))
            audio_data = audio_data & 0xFFFFFF
            max_val = 0xFFFFFF
        else:
            raise ValueError(
                "Unsupported sample width. Only 8, 16, and 24-bit audio supported.")

        key_hash, seed = self.hash_key(key)
        key_hash = key_hash[:4]  # Use only first 4 bytes for comparison
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
        # Updated to show 4-byte hash
        print(f"Debug: computed key_hash: {key_hash.hex()}")
        print(f"Debug: extracted stored_key_hash: {stored_key_hash.hex()}")
        # Now comparable
        print(
            f"Debug: stored_key_hash matches key_hash: {stored_key_hash == key_hash}")
        if len(stored_key_hash) == 4 and stored_key_hash == key_hash:
            # New format with key hash
            payload_size = int(extracted_bits[offset:offset+32].to01(), 2)
            offset += 32
            filename_len = int(extracted_bits[offset:offset+8].to01(), 2)
            offset += 8
        else:
            # Old format (no key hash) - fallback for compatibility
            offset = 0
            payload_size = int(extracted_bits[offset:offset+32].to01(), 2)
            offset += 32
            filename_len = int(extracted_bits[offset:offset+8].to01(), 2)
            offset += 8

        print(f"Debug: extracted payload_size: {payload_size}")
        print(f"Debug: extracted filename_len: {filename_len}")

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

    # -------------------- CAPACITY / RECOMMENDED LSBs --------------------
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
            filename = "text_payload.txt" if self.payload_type.get(
            ) == "text" else os.path.basename(self.payload_path.get())
            metadata_size = 9 + len(filename)  # bytes
            total_bits_needed = (payload_size + metadata_size) * 8
            if bits_available_per_pixel == 0:
                return None
            required_lsbs = math.ceil(
                total_bits_needed / bits_available_per_pixel)
            return min(max(1, required_lsbs), 8)
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
            filename = "text_payload.txt" if self.audio_payload_type.get(
            ) == "text" else os.path.basename(self.audio_payload_path.get())
            metadata_size = 9 + len(filename)  # bytes
            total_bits_needed = (payload_size + metadata_size) * 8
            if total_samples == 0:
                return None
            required_lsbs = math.ceil(total_bits_needed / total_samples)
            return min(max(1, required_lsbs), 8)
        except Exception:
            return None

    def calculate_required_lsbs_video(self, video_path, payload_size):
        if not video_path or not os.path.exists(video_path):
            return None
        try:
            params = self.get_video_params(video_path)
            width, height = params['width'], params['height']
            total_pixels = 1 * width * height * 3  # First I-frame only
            filename = "text_payload.txt" if self.video_payload_type.get(
            ) == "text" else os.path.basename(self.video_payload_path.get())
            metadata_size = 9 + len(filename)  # bytes
            total_bits_needed = (payload_size + metadata_size) * 8
            if total_pixels == 0:
                return None
            required_lsbs = math.ceil(total_bits_needed / total_pixels)
            return min(max(1, required_lsbs), 8)
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

            payload_size = 0
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
                    text=f"Capacity: {capacity_kb:.2f} KB\nRecommended LSBs: {recommended_lsbs}")
            else:
                self.capacity_label.config(
                    text=f"Capacity: {capacity_kb:.2f} KB\nRecommended LSBs: N/A (Select payload)")
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

            payload_size = 0
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
                    text=f"Capacity: {capacity_kb:.2f} KB\nRecommended LSBs: {recommended_lsbs}")
            else:
                self.audio_capacity_label.config(
                    text=f"Capacity: {capacity_kb:.2f} KB\nRecommended LSBs: N/A (Select payload)")
        except Exception:
            self.audio_capacity_label.config(text="Capacity: Error")

    def update_video_capacity_display(self, *args):
        video_path = self.video_cover_path.get()
        if not video_path or not os.path.exists(video_path):
            self.video_capacity_label.config(
                text="Capacity: Select a video file")
            return
        try:
            capacity_bytes = self._calculate_video_capacity(
                video_path, self.video_num_lsbs.get())
            capacity_kb = capacity_bytes / 1024

            payload_size = 0
            if self.video_payload_type.get() == "file" and self.video_payload_path.get():
                try:
                    payload_size = os.path.getsize(
                        self.video_payload_path.get())
                except:
                    payload_size = 0
            elif self.video_payload_type.get() == "text" and self.video_payload_text.get():
                payload_size = len(
                    self.video_payload_text.get().encode('utf-8'))

            recommended_lsbs = self.calculate_required_lsbs_video(
                video_path, payload_size)

            if recommended_lsbs is not None:
                self.video_capacity_label.config(
                    text=f"Capacity: {capacity_kb:.2f} KB\nRecommended LSBs: {recommended_lsbs}")
            else:
                self.video_capacity_label.config(
                    text=f"Capacity: {capacity_kb:.2f} KB\nRecommended LSBs: N/A (Select payload)")
        except Exception:
            self.video_capacity_label.config(text="Capacity: Error")

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

    def _calculate_video_capacity(self, video_path, num_lsbs):
        try:
            params = self.get_video_params(video_path)
            width, height = params['width'], params['height']
            total_pixels = 1 * width * height * 3  # First I-frame only
            max_bits = total_pixels * num_lsbs
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

    # -------------------- IMAGE DISPLAY / SELECTION --------------------
    def setup_canvas_bindings(self):
        self.cover_canvas.bind("<ButtonPress-1>", self.on_press)
        self.cover_canvas.bind("<B1-Motion>", self.on_drag)
        self.cover_canvas.bind("<ButtonRelease-1>", self.on_release)

    def on_press(self, event):
        scaled_w, scaled_h = self.scaled_size
        if (event.x < 0 or event.y < 0 or
                event.x > scaled_w or event.y > scaled_h):
            return "break"  # Ignore drags outside image

        self.start_canvas_x = event.x
        self.start_canvas_y = event.y
        if hasattr(self, 'rect'):
            self.cover_canvas.delete(self.rect)
        self.rect = self.cover_canvas.create_rectangle(
            self.start_canvas_x, self.start_canvas_y, self.start_canvas_x, self.start_canvas_y, outline='red', width=2)
        return None

    def on_drag(self, event):
        if not hasattr(self, 'start_canvas_x'):
            return
        scaled_w, scaled_h = self.scaled_size
        cur_x = max(0, min(scaled_w, event.x))
        cur_y = max(0, min(scaled_h, event.y))
        self.cover_canvas.coords(
            self.rect, self.start_canvas_x, self.start_canvas_y, cur_x, cur_y)

    def on_release(self, event):
        if not hasattr(self, 'start_canvas_x'):
            return
        scaled_w, scaled_h = self.scaled_size
        orig_w, orig_h = self.orig_size
        cur_x = max(0, min(scaled_w, event.x))
        cur_y = max(0, min(scaled_h, event.y))

        # convert canvas (possibly scaled) coords back to original image coords
        ox1 = self.start_canvas_x / self.scale
        oy1 = self.start_canvas_y / self.scale
        ox2 = cur_x / self.scale
        oy2 = cur_y / self.scale

        # use rounding and cast to int to avoid floats being used in ranges or image indexing
        x1 = int(round(max(0, min(orig_w, min(ox1, ox2)))))
        y1 = int(round(max(0, min(orig_h, min(oy1, oy2)))))
        x2 = int(round(max(0, min(orig_w, max(ox1, ox2)))))
        y2 = int(round(max(0, min(orig_h, max(oy1, oy2)))))

        if x1 >= x2 or y1 >= y2:
            self.embed_region_orig = None
            if hasattr(self, 'rect'):
                self.cover_canvas.delete(self.rect)
                del self.rect
        else:
            self.embed_region_orig = (x1, y1, x2, y2)

        self.update_capacity_display()

    def get_embed_region_in_original(self):
        return self.embed_region_orig

    def clear_selection(self):
        if hasattr(self, 'rect'):
            self.cover_canvas.delete(self.rect)
            self.rect = None
        self.embed_region_orig = None
        self.update_capacity_display()

     # -------------------- ANALYSIS TAB --------------------

    def setup_analysis_tab(self, parent):
        container = self.create_scrolled_frame(parent)

        # ---- File pickers ----
        pickers = tk.LabelFrame(
            container, text="Select Image(s) to Analyze", bg='#f5f5f5', padx=10, pady=10)
        pickers.pack(fill=tk.X)

        self.analysis_image_path = tk.StringVar()
        self.analysis_cover_hint_path = tk.StringVar()

        row1 = tk.Frame(pickers, bg='#f5f5f5')
        row1.pack(fill=tk.X, pady=3)
        tk.Label(row1, text="Suspected Stego Image:",
                 bg='#f5f5f5').pack(side=tk.LEFT)
        tk.Entry(row1, textvariable=self.analysis_image_path, state='readonly').pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        tk.Button(row1, text="Browse", command=self.browse_analysis_image,
                  bg='#2196F3', fg='white').pack(side=tk.LEFT)

        row2 = tk.Frame(pickers, bg='#f5f5f5')
        row2.pack(fill=tk.X, pady=3)
        tk.Label(row2, text="(Optional) Original Cover for Diff:",
                 bg='#f5f5f5').pack(side=tk.LEFT)
        tk.Entry(row2, textvariable=self.analysis_cover_hint_path, state='readonly').pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        tk.Button(row2, text="Browse", command=self.browse_analysis_cover_hint,
                  bg='#607D8B', fg='white').pack(side=tk.LEFT)

        # ---- Run / Info ----
        actions = tk.Frame(container, bg='#f5f5f5')
        actions.pack(fill=tk.X, pady=8)
        tk.Button(actions, text="🔍 Run Stego Analysis", command=self.run_image_analysis,
                  bg='#4CAF50', fg='white', font=('Helvetica', 11, 'bold')).pack(side=tk.LEFT, padx=4)
        tk.Button(actions, text="🗑️ Clear", command=self.clear_analysis_ui,
                  bg='#FF9800', fg='white').pack(side=tk.LEFT, padx=4)

        # ---- Results (text) ----
        self.analysis_text = tk.Text(
            container, height=10, bg='#f8f8f8', relief=tk.SUNKEN, bd=2, font=('Consolas', 10))
        self.analysis_text.pack(fill=tk.X, pady=6)

        # ---- Visuals ----
        viz = tk.LabelFrame(container, text="Visual Diagnostics",
                            bg='#f5f5f5', padx=10, pady=10)
        viz.pack(fill=tk.BOTH, expand=True)

        # Four image slots: LSB plane, Heatmap, Hist, DiffAmp
        grid = tk.Frame(viz, bg='#f5f5f5')
        grid.pack(fill=tk.BOTH, expand=True)

        cap_font = ('Helvetica', 10, 'bold')
        self.viz_lsb_label = tk.Label(grid, bg='lightgrey', relief=tk.SUNKEN, bd=2,
                                      compound='top', font=cap_font,
                                      text="Cover Histogram (optional)")
        self.viz_heat_label = tk.Label(grid, bg='lightgrey', relief=tk.SUNKEN, bd=2,
                                       compound='top', font=cap_font,
                                       text="Stego Histogram")
        self.viz_hist_label = tk.Label(grid, bg='lightgrey', relief=tk.SUNKEN, bd=2,
                                       compound='top', font=cap_font,
                                       text="LSB Plane (combined RGB)")
        self.viz_diff_label = tk.Label(grid, bg='lightgrey', relief=tk.SUNKEN, bd=2,
                                       compound='top', font=cap_font,
                                       text="LSB-Variance Heatmap")

        self.viz_lsb_label.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')
        self.viz_heat_label.grid(
            row=0, column=1, padx=5, pady=5, sticky='nsew')
        self.viz_hist_label.grid(
            row=1, column=0, padx=5, pady=5, sticky='nsew')
        self.viz_diff_label.grid(
            row=1, column=1, padx=5, pady=5, sticky='nsew')

        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)
        grid.grid_rowconfigure(0, weight=1)
        grid.grid_rowconfigure(1, weight=1)

    def _ia_set_row_heights(self, grid, top_left_tk, top_right_tk, bottom_left_tk, bottom_right_tk, pad=10):
        def h(im):
            return im.height() if im is not None else 0
        r0 = max(h(top_left_tk), h(top_right_tk)) + pad
        r1 = max(h(bottom_left_tk), h(bottom_right_tk)) + pad
        grid.grid_rowconfigure(0, minsize=r0)
        grid.grid_rowconfigure(1, minsize=r1)

    def _render_histograms_gui_style(self, arr, *, w=620, h=420, bins=256):
        """
        GUI-style histograms (R, G, B) stacked vertically:
        - Black filled histogram with thin white vertical stems
        - Colored baseline per channel (red/green/blue)
        - Metadata text: Index (mode bin), Pixels (count & %), Total pixels
        - ~20% headroom on Y scale so it doesn't touch top
        """
        # layout
        rows = 3
        pad_outer = 14
        vgap = 14
        panel_h = (h - pad_outer*2 - vgap*(rows-1)) // rows
        panel_w = w - pad_outer*2

        # inside a panel
        pad_l, pad_r, pad_t, pad_b = 14, 14, 28, 42   # room for title & foot
        axis_col = (105, 105, 105)
        grid_col = (228, 228, 228)
        fill_col = (0, 0, 0)
        stems_col = (255, 255, 255)

        ch_colors = {
            'R': (205, 40, 40),
            'G': (40, 165, 60),
            'B': (80, 70, 205),
        }

        img = Image.new("RGB", (w, h), (238, 238, 238))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None

        chans = [('R', arr[:, :, 0].ravel()),
                 ('G', arr[:, :, 1].ravel()),
                 ('B', arr[:, :, 2].ravel())]

        for i, (label, ch) in enumerate(chans):
            # histogram
            hist, edges = np.histogram(ch, bins=bins, range=(0, 256))
            total_px = int(hist.sum())
            peak_bin = int(np.argmax(hist))
            peak_ct = int(hist[peak_bin])
            peak_pct = (100.0 * peak_ct / total_px) if total_px else 0.0

            # headroom
            ymax = hist.max() if hist.max() > 0 else 1
            ylimit = int(np.ceil(ymax * 1.2))  # 20% headroom

            # panel rect
            top = pad_outer + i * (panel_h + vgap)
            left = pad_outer
            p_x0 = left
            p_y0 = top
            p_x1 = left + panel_w
            p_y1 = top + panel_h

            # background (fake dialog panel)
            draw.rectangle([p_x0, p_y0, p_x1, p_y1], fill=(
                245, 245, 245), outline=(180, 180, 180))

            # title bar text
            draw.text((p_x0 + 8, p_y0 + 6), "Image Histogram",
                      fill=(25, 25, 25), font=font)

            # channel selector text (lightweight illusion)
            draw.text((p_x0 + 8, p_y0 + 20), "Channel:",
                      fill=(25, 25, 25), font=font)
            # mark the active channel
            opts = ['Red', 'Green', 'Blue']
            for j, opt in enumerate(opts):
                yopt = p_y0 + 38 + j*13
                bullet = "◉ " if (opt[0] == label or (label == 'R' and opt == 'Red') or
                                  (label == 'G' and opt == 'Green') or (label == 'B' and opt == 'Blue')) else "○ "
                draw.text((p_x0 + 16, yopt), bullet + opt,
                          fill=(40, 40, 40), font=font)

            # plotting box (axes)
            x0 = p_x0 + pad_l + 130   # leave room for "Channel" stub at left
            y0 = p_y0 + pad_t + 6
            x1 = p_x1 - pad_r - 6
            y1 = p_y1 - pad_b

            # axes + grid
            draw.rectangle([x0, y0, x1, y1], outline=axis_col, width=1)
            for frac in (0.25, 0.5, 0.75):
                gy = int(y1 - frac * (y1 - y0))
                draw.line([(x0, gy), (x1, gy)], fill=grid_col, width=1)

            # draw black filled histogram under curve
            nb = len(hist)
            span = x1 - x0
            if nb <= 1:
                nb = 1
            step = span / nb

            # polygon points (under curve)
            poly = [(x0, y1)]
            for b in range(nb):
                x = x0 + b * step
                val = hist[b]
                y = y1 - (val / ylimit) * (y1 - y0)
                poly.append((x, y))
            poly.append((x1, y1))
            draw.polygon(poly, fill=fill_col)

            # thin white stems to mimic the example (sparse for readability)
            stride = max(2, bins // 128)   # fewer when many bins
            for b in range(0, nb, stride):
                x = x0 + b * step
                val = hist[b]
                y = y1 - (val / ylimit) * (y1 - y0)
                draw.line([(x, y1), (x, y)], fill=stems_col, width=1)

            # colored baseline strip
            base_col = ch_colors[label]
            draw.rectangle([x0, y1 + 10, x1, y1 + 14], fill=base_col)

            # x ticks (0..255 ends + mids)
            for xt in [0, 50, 100, 150, 200, 255]:
                xp = x0 + (xt / 255.0) * (x1 - x0)
                draw.line([(xp, y1), (xp, y1 + 4)], fill=axis_col)
                draw.text((xp - 6, y1 + 16), str(xt),
                          fill=(60, 60, 60), font=font)

            # footer metadata (index / pixels / total)
            meta_y = y1 + 26
            draw.text((x0, meta_y), f"Index: {peak_bin:>3}", fill=(
                35, 35, 35), font=font)
            meta_x2 = x0 + 140
            draw.text((meta_x2, meta_y), f"Pixels: {peak_ct:,} ({peak_pct:.1f}%)", fill=(
                35, 35, 35), font=font)
            meta_x3 = x0 + 340
            draw.text((meta_x3, meta_y), f"Total pixels: {total_px:,}", fill=(
                35, 35, 35), font=font)

        return img

    def browse_analysis_image(self):
        path = filedialog.askopenfilename(title="Select Image", filetypes=[
                                          ("Image files", "*.png *.bmp *.jpg *.jpeg *.gif")])
        if path:
            self.analysis_image_path.set(path)

    def browse_analysis_cover_hint(self):
        path = filedialog.askopenfilename(title="Select Original Cover (optional)", filetypes=[
                                          ("Image files", "*.png *.bmp *.jpg *.jpeg *.gif")])
        if path:
            self.analysis_cover_hint_path.set(path)

    def clear_analysis_ui(self):
        self.analysis_image_path.set("")
        self.analysis_cover_hint_path.set("")
        self.analysis_text.delete(1.0, tk.END)

        # restore titles, clear images
        self.viz_lsb_label.configure(
            image="", text="Cover Histogram (optional)")
        self.viz_lsb_label.image = None
        self.viz_heat_label.configure(image="", text="Stego Histogram")
        self.viz_heat_label.image = None
        self.viz_hist_label.configure(
            image="", text="LSB Plane (combined RGB)")
        self.viz_hist_label.image = None
        self.viz_diff_label.configure(image="", text="LSB-Variance Heatmap")
        self.viz_diff_label.image = None

    def run_image_analysis(self):
        path = self.analysis_image_path.get().strip()
        if not path:
            messagebox.showerror(
                "Error", "Select a suspected stego image first.")
            return

        try:
            img = Image.open(path).convert('RGB')
            arr = np.array(img, dtype=np.uint8)

            # ---- Metrics (unchanged) ----
            chi_p = self._chi_square_lsb_pvalue(arr)
            corr = self._neighbor_correlation(arr)
            lsb_ratio = self._lsb_one_ratio(arr)
            heat = self._lsb_variance_heatmap(arr, block=8)

            # ---- Visuals (TOP ROW unchanged) ----
            lsb_img = self._render_lsb_plane(arr)                  # top-left
            heat_img = self._render_heatmap_image(heat, img.size)   # top-right

            # ---- NEW: top row = histograms ----
            # top-right: suspected stego histogram
            hist_stego_img = self._render_histograms_gui_style(arr)

            hist_cover_img = None
            cover_hint = self.analysis_cover_hint_path.get().strip()
            if cover_hint and os.path.exists(cover_hint):
                cover_img = Image.open(cover_hint).convert('RGB')
                cover_arr = np.array(cover_img, dtype=np.uint8)
                hist_cover_img = self._render_histograms_gui_style(cover_arr)

            # ---- Report text (matches new layout) ----
            has_cover = bool(self.analysis_cover_hint_path.get().strip(
            ) and os.path.exists(self.analysis_cover_hint_path.get().strip()))

            report = []
            report.append("Steganalysis Report\n-------------------")
            report.append(
                f"Image: {os.path.basename(path)}  |  {img.size[0]}×{img.size[1]}  |  RGB")
            report.append(
                f"Chi-square LSB p-value (higher ~ more random LSBs): {chi_p:.4f}")
            report.append(
                f"Neighbor correlation (0–1). Natural images ~0.90–0.99: {corr:.4f}")
            report.append(
                f"LSB(1-bit) ones ratio (should be near 0.5): {lsb_ratio:.4f}")
            if has_cover:
                report.append(
                    "Top row: Cover histogram (left) vs Stego histogram (right).")
            else:
                report.append(
                    "Top row: Stego histogram (right). (Provide a cover to compare on the left.)")
            report.append(
                "Bottom row: LSB plane (left) and LSB-variance heatmap (right).")
            report.append("")  # blank line

            self.analysis_text.delete(1.0, tk.END)
            self.analysis_text.insert(1.0, "\n".join(report))

            # ---- Display images ----

            def _to_tk(im, max_wh=(450, 450)):
                imc = im.copy()
                imc.thumbnail(max_wh)
                return ImageTk.PhotoImage(imc)

            # top row (histograms)
            if hist_cover_img is not None:
                cov_tk = _to_tk(hist_cover_img)
                self.viz_lsb_label.configure(image=cov_tk)  # <-- no text=""
                self.viz_lsb_label.image = cov_tk
            else:
                cov_tk = None
                self.viz_lsb_label.configure(
                    image="", text="Cover Histogram (optional)")
                self.viz_lsb_label.image = None

            stego_tk = _to_tk(hist_stego_img)
            self.viz_heat_label.configure(image=stego_tk)   # <-- no text=""
            self.viz_heat_label.image = stego_tk

            # bottom row (LSB + heatmap)
            lsb_tk = _to_tk(lsb_img)
            heat_tk = _to_tk(heat_img)
            self.viz_hist_label.configure(image=lsb_tk)     # <-- no text=""
            self.viz_hist_label.image = lsb_tk
            self.viz_diff_label.configure(image=heat_tk)    # <-- no text=""
            self.viz_diff_label.image = heat_tk

            # ensure row heights fit what we just displayed
            self._ia_set_row_heights(
                grid=self.viz_lsb_label.master,
                top_left_tk=cov_tk,
                top_right_tk=stego_tk,
                bottom_left_tk=lsb_tk,
                bottom_right_tk=heat_tk
            )

        except Exception as e:
            messagebox.showerror("Analysis Error", str(e))

    def _lsb_one_ratio(self, arr):
        # Combine all channels; ratio of LSB=1
        lsb = arr & 1
        ones = np.count_nonzero(lsb)
        total = lsb.size
        return ones / max(total, 1)

    def _chi_square_lsb_pvalue(self, arr):
        """
        Chi-square test on LSBs across all channels.
        H0: LSBs are fair (0/1 equally likely).
        Returns an approximate p-value without scipy.
        """
        lsb = (arr & 1).ravel()
        n = lsb.size
        c1 = np.count_nonzero(lsb)           # observed ones
        c0 = n - c1                          # observed zeros
        expected = n / 2.0
        # Chi-square with 1 df
        chi = ((c0 - expected)**2 / expected) + ((c1 - expected)**2 / expected)
        # Approx p from survival function of chi2 with df=1: p ≈ exp(-chi/2) * sqrt(2/ (pi*chi)) for chi>0
        # Use a robust fallback for very small chi
        if chi <= 1e-12:
            return 1.0
        # Wilson-Hilferty approx or a simple tail approx:
        # We'll use a tight approximation: p ≈ erfc( sqrt(chi/2) ) but we don't have erfc -> use exp bound
        # A simple monotonic surrogate:
        from math import exp
        # Lower bound-ish (conservative): p_lower ≈ exp(-chi/2)
        p = exp(-chi / 2.0)
        return min(max(p, 0.0), 1.0)

    def _neighbor_correlation(self, arr):
        """
        Pearson correlation between neighboring horizontal pixels over all channels.
        """
        # Convert to luminance to be channel-agnostic
        R, G, B = arr[:, :, 0].astype(np.float32), arr[:, :, 1].astype(
            np.float32), arr[:, :, 2].astype(np.float32)
        Y = 0.299*R + 0.587*G + 0.114*B
        # pairs (x, x+1)
        X = Y[:, :-1].ravel()
        Ynext = Y[:, 1:].ravel()
        if X.size < 2:
            return 0.0
        Xm, Ym = X.mean(), Ynext.mean()
        num = np.sum((X - Xm)*(Ynext - Ym))
        den = np.sqrt(np.sum((X - Xm)**2) * np.sum((Ynext - Ym)**2))
        if den == 0:
            return 0.0
        return float(num/den)

    def _lsb_variance_heatmap(self, arr, block=8):
        """
        Compute per-block variance of LSBs (across channels) -> high = suspicious.
        Returns a (H/block, W/block) float array normalized to 0..1.
        """
        H, W, _ = arr.shape
        lsb = (arr & 1).sum(axis=2)  # 0..3 per pixel
        h_blocks, w_blocks = H // block, W // block
        if h_blocks == 0 or w_blocks == 0:
            return np.zeros((1, 1), dtype=np.float32)
        heat = np.zeros((h_blocks, w_blocks), dtype=np.float32)
        for by in range(h_blocks):
            for bx in range(w_blocks):
                tile = lsb[by*block:(by+1)*block, bx *
                           block:(bx+1)*block].ravel()
                # normalize to 0..1 by dividing by 3
                tile01 = tile / 3.0
                v = float(tile01.var())
                heat[by, bx] = v
        # normalize heat 0..1
        if heat.max() > 0:
            heat = heat / heat.max()
        return heat

    def _render_lsb_plane(self, arr):
        """
        Show LSB plane (combined RGB). Brighter = LSB=1 more frequently across channels.
        """
        lsb_sum = (arr & 1).sum(axis=2) * 85  # 0..3 -> 0..255
        img = Image.fromarray(lsb_sum.astype(np.uint8),
                              mode='L').convert('RGB')
        return img

    def _render_heatmap_image(self, heat, size):
        """
        Upscale small heat array to image size with a simple grayscale colormap.
        """
        h_norm = (heat*255.0).clip(0, 255).astype(np.uint8)
        hm = Image.fromarray(h_norm, mode='L').resize(
            size, Image.NEAREST).convert('RGB')
        return hm

    def _render_histograms_styled(self, arr, *, w=560, h=360, bins=32,
                                  bar_color=(160, 70, 255),  # purple-ish
                                  title=None):
        """
        Paper-style histograms for R, G, B channels (stacked vertically).
        - coarse 'bins' for chunky bars (example-like look)
        - axes + light grid + labels
        - returns one RGB image containing three small plots (R,G,B)
        """
        # ---- layout ----
        rows = 3
        pad_outer = 16
        vgap = 16                      # gap between subplots
        plot_h = (h - pad_outer*2 - vgap*(rows-1)) // rows
        plot_w = w - pad_outer*2
        pad_l, pad_r, pad_t, pad_b = 40, 12, 24, 28   # in-axes padding

        # canvas
        img = Image.new("RGB", (w, h), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None

        # optional title at the very top
        if title:
            draw.text((pad_outer, 6), title, fill=(30, 30, 30), font=font)

        # channels (R, G, B) — same order as your current function
        chans = [arr[:, :, 0].ravel(), arr[:, :, 1].ravel(),
                 arr[:, :, 2].ravel()]
        labels = ["R", "G", "B"]

        # ticks for x axis
        xticks = [0, 50, 100, 150, 200, 255]

        for i, ch in enumerate(chans):
            # histogram with coarse bins (0..256)
            hist, edges = np.histogram(ch, bins=bins, range=(0, 256))
            hist = hist.astype(np.float64)
            ymax = hist.max() if hist.max() > 0 else 1.0

            # subplot top-left corner
            top = pad_outer + i * (plot_h + vgap)
            left = pad_outer

            # axes rect (data area)
            x0 = left + pad_l
            y0 = top + pad_t
            x1 = left + plot_w - pad_r
            y1 = top + plot_h - pad_b
            draw.rectangle([x0, y0, x1, y1], outline=(80, 80, 80), width=1)

            # grid lines (horizontal)
            for frac in (0.25, 0.5, 0.75):
                gy = int(y1 - frac * (y1 - y0))
                draw.line([(x0, gy), (x1, gy)], fill=(220, 220, 220), width=1)

            # x-axis ticks & labels
            for xt in xticks:
                # map intensity (0..255) to x-pixel
                xpix = x0 + int((xt / 255.0) * (x1 - x0))
                draw.line([(xpix, y1), (xpix, y1 + 4)],
                          fill=(80, 80, 80), width=1)
                draw.text((xpix - 6, y1 + 6), str(xt),
                          fill=(60, 60, 60), font=font)

            # y-axis tick labels (0, mid, max)
            for frac, lab in [(0.0, "0"), (0.5, f"{int(ymax*0.5)}"), (1.0, f"{int(ymax)}")]:
                yp = int(y1 - frac * (y1 - y0))
                draw.text((x0 - 32, yp - 6), lab, fill=(60, 60, 60), font=font)

            # bars
            nb = len(hist)
            bar_w = max(1, (x1 - x0) // nb)
            for b in range(nb):
                v = hist[b]
                if v <= 0:
                    continue
                xA = x0 + b * bar_w
                xB = xA + bar_w - 1
                yB = y1
                yA = int(y1 - (v / ymax) * (y1 - y0))
                draw.rectangle([xA, yA, xB, yB],
                               fill=bar_color, outline=bar_color)

            # subplot label (R/G/B)
            draw.text((x0 - 28, y0 - 16),
                      labels[i], fill=(50, 50, 50), font=font)

            # axis labels (y for each subplot, x only for bottom subplot)
            draw.text((left, y0 - 16), "No of pixels",
                      fill=(50, 50, 50), font=font)
            if i == rows - 1:
                draw.text((x0 + (x1 - x0)//2 - 40, y1 + 20),
                          "Pixel intensity", fill=(50, 50, 50), font=font)

        return img

    def _render_histograms(self, arr):
        """
        Quick RGB histogram histogram render (256x120 per channel stacked).
        """
        H, W = 120, 256
        canvas = Image.new('RGB', (W, H*3), (240, 240, 240))
        for i, ch in enumerate([0, 1, 2]):
            hist = np.bincount(arr[:, :, ch].ravel(),
                               minlength=256).astype(np.float32)
            if hist.max() > 0:
                hist /= hist.max()
            hist_h = (hist * (H-1)).astype(np.int32)
            layer = Image.new('RGB', (W, H), (255, 255, 255))
            px = layer.load()
            for x in range(256):
                h = hist_h[x]
                for y in range(H-1, H-1-h, -1):
                    # draw a vertical bar
                    px[x, y] = (50, 50, 50)
            canvas.paste(layer, (0, i*H))
        return canvas

    def _render_diff_amplified(self, cover_img, stego_img, factor=16):
        """
        |stego - cover| * factor, clipped, to reveal subtle subtle embedding patterns.
        """
        if cover_img.size != stego_img.size:
            # fallback: resize cover to stego just for visualization
            cover_img = cover_img.resize(stego_img.size, Image.BILINEAR)
        c = np.array(cover_img, dtype=np.int16)
        s = np.array(stego_img, dtype=np.int16)
        d = np.clip(np.abs(s - c) * factor, 0, 255).astype(np.uint8)
        return Image.fromarray(d, mode='RGB')

    def setup_audio_analysis_tab(self, parent):
        inner_frame = self.create_scrolled_frame(parent)
        pad = tk.Frame(inner_frame, bg='#f5f5f5')
        pad.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        picks = tk.LabelFrame(
            pad, text="Select WAV(s) to Analyze", bg='#f5f5f5', padx=10, pady=10)
        picks.pack(fill=tk.X)

        self.an_audio_path = tk.StringVar()
        self.an_audio_cover_hint = tk.StringVar()
        # assumed LSBs for analysis view (1–4 is common)
        self.an_audio_lsbs = tk.IntVar(value=1)

        r1 = tk.Frame(picks, bg='#f5f5f5')
        r1.pack(fill=tk.X, pady=3)
        tk.Label(r1, text="Suspected Stego WAV:",
                 bg='#f5f5f5').pack(side=tk.LEFT)
        tk.Entry(r1, textvariable=self.an_audio_path, state='readonly').pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        tk.Button(r1, text="Browse", command=self._an_browse_audio,
                  bg='#2196F3', fg='white').pack(side=tk.LEFT)

        r2 = tk.Frame(picks, bg='#f5f5f5')
        r2.pack(fill=tk.X, pady=3)
        tk.Label(r2, text="(Optional) Original Cover WAV:",
                 bg='#f5f5f5').pack(side=tk.LEFT)
        tk.Entry(r2, textvariable=self.an_audio_cover_hint, state='readonly').pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        tk.Button(r2, text="Browse", command=self._an_browse_audio_cover,
                  bg='#607D8B', fg='white').pack(side=tk.LEFT)

        r3 = tk.Frame(picks, bg='#f5f5f5')
        r3.pack(fill=tk.X, pady=6)
        tk.Label(r3, text="Assumed LSBs for Analysis:",
                 bg='#f5f5f5').pack(side=tk.LEFT)
        tk.Scale(r3, from_=1, to=8, orient=HORIZONTAL, variable=self.an_audio_lsbs,
                 bg='#f5f5f5', length=200).pack(side=tk.LEFT, padx=10)

        actions = tk.Frame(pad, bg='#f5f5f5')
        actions.pack(fill=tk.X, pady=8)
        tk.Button(actions, text="🔎 Run Audio Analysis", command=self.run_audio_stego_analysis,
                  bg='#4CAF50', fg='white', font=('Helvetica', 11, 'bold')).pack(side=tk.LEFT, padx=4)
        tk.Button(actions, text="💾 Save Report", command=self._an_save_report,
                  bg='#3F51B5', fg='white').pack(side=tk.LEFT, padx=4)
        tk.Button(actions, text="📂 Load Report", command=self._an_load_report,
                  bg='#009688', fg='white').pack(side=tk.LEFT, padx=4)
        tk.Button(actions, text="🗑️ Clear", command=self._an_clear_ui,
                  bg='#FF9800', fg='white').pack(side=tk.LEFT, padx=4)

        self.an_audio_text = tk.Text(
            pad, height=10, bg='#f8f8f8', relief=tk.SUNKEN, bd=2, font=('Consolas', 10))
        self.an_audio_text.pack(fill=tk.X, pady=6)

        viz = tk.LabelFrame(pad, text="Visual Diagnostics",
                            bg='#f5f5f5', padx=10, pady=10)
        viz.pack(fill=tk.BOTH, expand=True)
        grid = tk.Frame(viz, bg='#f5f5f5')
        grid.pack(fill=tk.BOTH, expand=True)

        cap_font = ('Helvetica', 10, 'bold')
        self.viz_wave = tk.Label(grid, bg='lightgrey', relief=tk.SUNKEN, bd=2,
                                 compound='top', font=cap_font,
                                 text="Before Steganography (Cover Waveform)")
        self.viz_spec = tk.Label(grid, bg='lightgrey', relief=tk.SUNKEN, bd=2,
                                 compound='top', font=cap_font,
                                 text="After Steganography (Stego Waveform)")
        self.viz_lsbvar = tk.Label(grid, bg='lightgrey', relief=tk.SUNKEN, bd=2,
                                   compound='top', font=cap_font,
                                   text="Spectrogram (ch 1)")
        self.viz_diffaudio = tk.Label(grid, bg='lightgrey', relief=tk.SUNKEN, bd=2,
                                      compound='top', font=cap_font,
                                      text="Diff vs Cover (or LSB Variance)")

        self.viz_wave.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')
        self.viz_spec.grid(row=0, column=1, padx=5, pady=5, sticky='nsew')
        self.viz_lsbvar.grid(row=1, column=0, padx=5, pady=5, sticky='nsew')
        self.viz_diffaudio.grid(row=1, column=1, padx=5, pady=5, sticky='nsew')

        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)
        grid.grid_rowconfigure(0, weight=1)
        grid.grid_rowconfigure(1, weight=1)

    def _render_waveform_chart(self, samples, title=None, w=1024, h=220):
        """
        Waveform with midline and optional title text (first channel).
        """
        ch = samples[:, 0].astype(np.float32)
        # fit/trim to width
        if ch.size > w:
            idx = np.linspace(0, ch.size - 1, w).astype(int)
            ch = ch[idx]
        else:
            pad = w - ch.size
            if pad > 0:
                ch = np.pad(ch, (0, pad), mode='edge')

        # normalize to -1..1
        m = max(np.max(np.abs(ch)), 1e-9)
        y = (ch / m) * 0.9

        img = Image.new('RGB', (w, h), (245, 245, 245))
        px = img.load()
        mid = h // 2

        # midline
        for x in range(w):
            px[x, mid] = (190, 190, 190)

        # waveform (vertical sticks)
        for x in range(w):
            ypix = int(mid - y[x] * (h // 2 - 10))
            y0, y1 = sorted((mid, ypix))
            for yy in range(y0, y1 + 1):
                px[x, yy] = (30, 60, 140)

        # title
        if title:
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.load_default()
            except Exception:
                font = None
            draw.text((8, 6), title, fill=(20, 20, 20), font=font)

        return img

    def _an_browse_audio(self):
        path = filedialog.askopenfilename(
            title="Select WAV", filetypes=[("WAV files", "*.wav")])
        if path:
            self.an_audio_path.set(path)

    def _an_browse_audio_cover(self):
        path = filedialog.askopenfilename(
            title="Select Original Cover WAV", filetypes=[("WAV files", "*.wav")])
        if path:
            self.an_audio_cover_hint.set(path)

    def _an_clear_ui(self):
        self.an_audio_path.set("")
        self.an_audio_cover_hint.set("")
        self.an_audio_lsbs.set(1)
        self.an_audio_text.delete(1.0, tk.END)

        self.viz_wave.configure(
            image='', text="Before Steganography (Cover Waveform)")
        self.viz_wave.image = None
        self.viz_spec.configure(
            image='', text="After Steganography (Stego Waveform)")
        self.viz_spec.image = None
        self.viz_lsbvar.configure(image='', text="Spectrogram (ch 1)")
        self.viz_lsbvar.image = None
        self.viz_diffaudio.configure(
            image='', text="Diff vs Cover (or LSB Variance)")
        self.viz_diffaudio.image = None

    def _render_lsb_var_plot(self, var_series, w=1024, h=220, title=None):
        """
        Render block variance series as a simple line plot:
        x = block index, y = normalized variance (0..1).
        """
        if var_series.size == 0:
            return Image.new('RGB', (w, h), (245, 245, 245))

        # resample series to width w
        xs = np.linspace(0, var_series.size - 1, w).astype(int)
        v = var_series[xs].astype(np.float32)
        v = np.clip(v, 0.0, 1.0)

        pad_top, pad_bot, pad_lr = 24, 20, 40
        plot_w = w - 2*pad_lr
        plot_h = h - (pad_top + pad_bot)

        img = Image.new('RGB', (w, h), (245, 245, 245))
        draw = ImageDraw.Draw(img)

        # axes rectangle
        x0, y0 = pad_lr, pad_top
        x1, y1 = x0 + plot_w, y0 + plot_h
        draw.rectangle([x0, y0, x1, y1], outline=(180, 180, 180), width=1)

        # horizontal gridlines at 0, .25, .5, .75, 1.0
        for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
            yy = int(y1 - frac * plot_h)
            draw.line([(x0, yy), (x1, yy)], fill=(220, 220, 220), width=1)

        # polyline for v
        last = None
        for i in range(plot_w):
            # map i->x pixel, v[i]->y pixel
            vi = v[int(i * (len(v) - 1) / max(plot_w - 1, 1))]
            px = x0 + i
            py = int(y1 - vi * plot_h)
            if last is not None:
                draw.line([last, (px, py)], fill=(30, 30, 30), width=2)
            last = (px, py)

        # title and tiny ticks
        if title:
            try:
                font = ImageFont.load_default()
            except Exception:
                font = None
            draw.text((8, 6), title, fill=(20, 20, 20), font=font)
            # y-axis ticks labels
            for frac, lab in [(1.0, "1.0"), (0.5, "0.5"), (0.0, "0.0")]:
                yy = int(y1 - frac * plot_h)
                draw.text((6, yy - 6), lab, fill=(100, 100, 100), font=font)

        return img

    def run_audio_stego_analysis(self):
        path = self.an_audio_path.get().strip()
        if not path:
            messagebox.showerror("Error", "Select a WAV file to analyze.")
            return

        try:
            # ---- load suspected stego ----
            # (N, C) int array (8/16/24-bit handled)
            params, samples = self._wav_read_any(path)
            N, C = samples.shape

            # ---- choose bit-plane from slider (1..8 on UI ⇒ 0..7 bit index) ----
            k = max(0, min(int(self.an_audio_lsbs.get()) - 1, 7))

            # ---- headline metrics on selected bit-plane k ----
            chi_p_overall, chi_p_ch = self._chi_square_lsb_audio(samples, k)
            corr_overall, corr_ch = self._neighbor_corr_audio(
                samples)  # plane-independent
            lsb_ratio_overall, lsb_ratio_ch = self._lsb_ratio_audio(samples, k)
            lsb_var_series = self._lsb_block_variance_1d(
                samples, k, block=2048)
            lsb_var_mean = float(lsb_var_series.mean()
                                 ) if lsb_var_series.size else 0.0

            # ---- auto-detect most likely bit depth (scan 1..8 → bit_index 0..7) ----
            autodet_rows = []
            best = None
            for d in range(1, 9):
                kk = d - 1
                chi_p_o, _ = self._chi_square_lsb_audio(samples, kk)
                _, corr_ch_tmp = self._neighbor_corr_audio(samples)
                corr_o = float(np.mean(corr_ch_tmp)) if corr_ch_tmp else 0.0
                lsb_ratio_o, _ = self._lsb_ratio_audio(samples, kk)
                series = self._lsb_block_variance_1d(samples, kk, block=2048)
                var_mean = float(series.mean()) if series.size else 0.0
                score = float(self._score_stegoish(
                    chi_p_o, corr_o, lsb_ratio_o, var_mean))
                row = {
                    "lsbs": d, "score": score,
                    "chi_p": float(chi_p_o),
                    "corr": float(corr_o),
                    "lsb_ratio": float(lsb_ratio_o),
                    "var": float(var_mean),
                }
                autodet_rows.append(row)
                if (best is None) or (row["score"] > best["score"]):
                    best = row

            # ---- optional difference view with original cover ----
            diff_img = None
            cover_path = self.an_audio_cover_hint.get().strip()
            if cover_path and os.path.exists(cover_path):
                _, cover_samples = self._wav_read_any(cover_path)
                diff_img = self._render_audio_diff(cover_samples, samples)

            # ---- visuals ----
            # BEFORE (cover) waveform for top-left
            cover_path = self.an_audio_cover_hint.get().strip()
            cover_samples = None
            if cover_path and os.path.exists(cover_path):
                _, cover_samples = self._wav_read_any(cover_path)
                wave_before_img = self._render_waveform_chart(
                    cover_samples, title="Before Steganography")
            else:
                # fallback note if no cover provided
                wave_before_img = Image.new(
                    'RGB', (1024, 220), (245, 245, 245))
                d = ImageDraw.Draw(wave_before_img)
                d.text((10, 10), "Provide cover WAV to view 'Before Steganography' waveform", fill=(
                    50, 50, 50))

            # AFTER (stego) waveform for bottom-left
            wave_after_img = self._render_waveform_chart(
                samples, title="After Steganography")

            # Keep spectrogram at top-right (first channel quick look)
            spec_img = self._render_spectrogram(samples[:, 0])

            # Keep LSB variance bars at bottom-right
            # already computed earlier; keep line if you use later too
            lsb_var_series = self._lsb_block_variance_1d(
                samples, k, block=2048)
            lsbvar_img = self._render_lsb_var_plot(
                lsb_var_series,
                title=f"Block Variance (bit-plane {k})"
            )

            # ---- show images ----
            def _to_tk(im, max_wh=(450, 450)):
                imc = im.copy()
                imc.thumbnail(max_wh)
                return ImageTk.PhotoImage(imc)

            before_tk = _to_tk(wave_before_img)
            self.viz_wave.configure(image=before_tk)
            self.viz_wave.image = before_tk

            after_tk = _to_tk(wave_after_img)
            self.viz_spec.configure(image=after_tk)
            self.viz_spec.image = after_tk

            spec_tk = _to_tk(spec_img)
            self.viz_lsbvar.configure(image=spec_tk)
            self.viz_lsbvar.image = spec_tk

            if diff_img is not None:
                diff_tk = _to_tk(diff_img)
                self.viz_diffaudio.configure(image=diff_tk)
                self.viz_diffaudio.image = diff_tk
            else:
                var_tk = _to_tk(lsbvar_img)
                self.viz_diffaudio.configure(image=var_tk)
                self.viz_diffaudio.image = var_tk

            # ---- report text ----
            sr = params.framerate
            dur = N / float(sr) if sr else 0.0
            lines = []
            lines.append(
                "Auto-detect (scan LSB=1..8): higher score = more likely to be stego")
            for r in autodet_rows:
                lines.append(
                    f"LSBs={r['lsbs']}: score={r['score']:.3f} | "
                    f"chi_p={r['chi_p']:.4f} corr={r['corr']:.4f} "
                    f"lsb_ratio={r['lsb_ratio']:.4f} var={r['var']:.4f}"
                )
            if best:
                lines.append(
                    f"\nLikely LSB depth: {best['lsbs']} (score {best['score']:.3f})\n")

            lines.append("Summary on selected plane")
            lines.append("------------------------")
            lines.append(
                f"File: {os.path.basename(path)}  |  {sr} Hz, {params.nchannels} ch, {8*params.sampwidth}-bit, {dur:.2f}s")
            lines.append(
                f"Chi-square LSB p-value (overall): {chi_p_overall:.4f}")
            for c in range(C):
                lines.append(f"  - ch{c+1}: {chi_p_ch[c]:.4f}")
            lines.append(f"Neighbor correlation (overall): {corr_overall:.4f}")
            for c in range(C):
                lines.append(f"  - ch{c+1}: {corr_ch[c]:.4f}")
            lines.append(f"LSB ones-ratio (overall): {lsb_ratio_overall:.4f}")
            for c in range(C):
                lines.append(f"  - ch{c+1}: {lsb_ratio_ch[c]:.4f}")
            lines.append(
                f"Mean block variance on plane {k}: {lsb_var_mean:.4f}")

            # ---- show text ----
            self.an_audio_text.delete(1.0, tk.END)
            self.an_audio_text.insert(1.0, "\n".join(lines))

        except Exception as e:
            messagebox.showerror("Analysis Error", str(e))

    def _score_stegoish(self, chi_p, corr, lsb_ratio, var_mean):
        """
        Heuristic: higher = more 'stego-ish'.
        - want chi_p small (LSB distribution deviates from 50/50) -> use (1 - chi_p)
        - want corr small (more noise)          -> use (1 - corr)
        - want ones-ratio near 0.5 -> use bell around 0.5
        - want variance across blocks high                      -> use var_mean
        Weights are gentle; tweak if you like.
        """
        near_half = 1.0 - min(1.0, abs(lsb_ratio - 0.5)
                              * 4.0)  # 1.0 at 0.5, ~0 by 0.25/0.75
        return 0.35 * (1.0 - chi_p) + 0.35 * (1.0 - corr) + 0.15 * near_half + 0.15 * var_mean

    def _wav_read_any(self, path):
        with wave.open(path, 'rb') as w:
            params = w.getparams()
            frames = w.readframes(params.nframes)

        # dtype by sampwidth
        sw = params.sampwidth
        if sw == 1:
            arr = np.frombuffer(frames, dtype=np.uint8).astype(
                np.uint16)  # 0..255
        elif sw == 2:
            arr = np.frombuffer(frames, dtype=np.int16).astype(np.int32)
        elif sw == 3:
            raw = np.frombuffer(frames, dtype=np.uint8).reshape(-1, 3)
            vals = (raw[:, 0].astype(np.uint32) |
                    (raw[:, 1].astype(np.uint32) << 8) |
                    (raw[:, 2].astype(np.uint32) << 16))
            # interpret as signed 24-bit
            sign = (vals & 0x800000) != 0
            vals = vals - (sign.astype(np.uint32) << 24)
            arr = vals.astype(np.int32)
        else:
            raise ValueError("Unsupported sample width (8/16/24-bit only).")

        # channels
        C = params.nchannels
        if C == 1:
            samples = arr.reshape(-1, 1)
        else:
            samples = arr.reshape(-1, C)
        return params, samples

    def _chi_square_lsb_audio(self, samples, bit_index=0):
        """Chi-square on the selected bit-plane (0 = LSB)."""
        import math
        bp = ((samples >> bit_index) & 1).ravel()
        n = bp.size
        ones = int(np.count_nonzero(bp))
        zeros = n - ones
        expected = n / 2.0
        chi = ((zeros - expected) ** 2) / expected + \
            ((ones - expected) ** 2) / expected
        p_overall = 1.0 if chi <= 1e-12 else math.exp(-chi / 2.0)

        p_ch = []
        C = samples.shape[1]
        for c in range(C):
            ch = ((samples[:, c] >> bit_index) & 1)
            n_c = ch.size
            ones_c = int(np.count_nonzero(ch))
            zeros_c = n_c - ones_c
            expected_c = n_c / 2.0
            chi_c = ((zeros_c - expected_c) ** 2) / expected_c + \
                ((ones_c - expected_c) ** 2) / expected_c
            p_c = 1.0 if chi_c <= 1e-12 else math.exp(-chi_c / 2.0)
            p_ch.append(float(p_c))
        return float(p_overall), p_ch

    def _neighbor_corr_audio(self, samples):
        """
        Pearson correlation between adjacent samples per channel.
        Natural audio usually has strong correlation; LSB embedding adds noise.
        """
        C = samples.shape[1]
        corr_ch = []
        for c in range(C):
            x = samples[:-1, c].astype(np.float32)
            y = samples[1:, c].astype(np.float32)
            if x.size < 2:
                corr_ch.append(0.0)
                continue
            xm, ym = x.mean(), y.mean()
            num = np.sum((x-xm)*(y-ym))
            den = np.sqrt(np.sum((x-xm)**2) * np.sum((y-ym)**2))
            corr_ch.append(float(num/den) if den != 0 else 0.0)
        # overall = mean of channels
        overall = float(np.mean(corr_ch)) if corr_ch else 0.0
        return overall, corr_ch

    def _lsb_ratio_audio(self, samples, bit_index=0):
        """Ones-ratio for the selected bit-plane (0 = LSB)."""
        bp = ((samples >> bit_index) & 1)
        overall = float(np.count_nonzero(bp)) / max(bp.size, 1)
        ch = [float(np.count_nonzero(bp[:, c])) / max(bp[:, c].size, 1)
              for c in range(bp.shape[1])]
        return overall, ch

    def _lsb_block_variance_1d(self, samples, bit_index=0, block=2048):
        """Variance over time for the selected bit-plane; normalized 0..1 series."""
        bp = ((samples >> bit_index) & 1).astype(np.float32)
        if bp.ndim == 2 and bp.shape[1] > 1:
            bp = bp.mean(axis=1)
        N = bp.shape[0]
        if N < block:
            v = np.array([bp.var()], dtype=np.float32)
        else:
            nblk = N // block
            v = np.zeros(nblk, dtype=np.float32)
            for i in range(nblk):
                seg = bp[i*block:(i+1)*block]
                v[i] = float(seg.var())
        if v.max() > 0:
            v = v / v.max()
        return v

    # ---------- Visuals ----------
    def _render_waveform(self, samples):
        """
        Simple normalized waveform of first channel; 1024 wide, 200 high.
        """
        h, w = 200, 1024
        ch = samples[:, 0].astype(np.float32)
        if ch.size > w:
            # downsample by picking evenly spaced points
            idx = np.linspace(0, ch.size-1, w).astype(int)
            ch = ch[idx]
        else:
            # pad to width
            pad = w - ch.size
            if pad > 0:
                ch = np.pad(ch, (0, pad), mode='edge')

        # normalize to -1..1
        m = max(np.max(np.abs(ch)), 1e-9)
        y = (ch / m) * 0.9  # leave margin
        img = Image.new('RGB', (w, h), (240, 240, 240))
        px = img.load()
        mid = h//2
        # draw axis
        for x in range(w):
            px[x, mid] = (180, 180, 180)
        # draw waveform
        for x in range(w):
            ypix = int(mid - y[x] * (h//2 - 5))
            # vertical line from mid to ypix
            y0, y1 = sorted((mid, ypix))
            for yy in range(y0, y1+1):
                px[x, yy] = (30, 30, 30)
        return img

    def _render_spectrogram(self, mono, win=512, hop=256):
        """
        Very lightweight STFT log-magnitude spectrogram (grayscale).
        """
        x = mono.astype(np.float32)
        N = x.size
        if N < win:
            x = np.pad(x, (0, win-N), mode='constant')
            N = x.size
        # frames
        frames = []
        for start in range(0, N-win+1, hop):
            seg = x[start:start+win]
            # Hann
            n = np.arange(win, dtype=np.float32)
            seg = seg * (0.5 - 0.5*np.cos(2*np.pi*n/(win-1)))
            # FFT mag
            spec = np.abs(np.fft.rfft(seg))
            frames.append(spec)
        if not frames:
            return Image.new('RGB', (4, 4), (240, 240, 240))
        S = np.stack(frames, axis=1)  # (freq_bins, time)
        S = S + 1e-8
        S = 20.0 * np.log10(S)  # dB
        # normalize to 0..255
        S = (S - S.min()) / max(S.max()-S.min(), 1e-6)
        S = (S*255.0).astype(np.uint8)
        # flip freq so low at bottom
        S = np.flipud(S)
        cmap = cm.get_cmap('magma')
        rgba = cmap(S / 255.0, bytes=True)   # map grayscale to RGBA
        return Image.fromarray(rgba[:, :, :3], mode='RGB')

    def _render_lsb_var_bar(self, var_series, height=120):
        """
        Render 1D variance series as a bar image (grayscale): bright = high variance.
        """
        if var_series.size == 0:
            return Image.new('RGB', (4, height), (240, 240, 240))
        w = int(max(64, var_series.size))
        # stretch to width
        xs = np.linspace(0, var_series.size-1, w).astype(int)
        vimg = (var_series[xs]*255.0).clip(0, 255).astype(np.uint8)
        img = Image.new('L', (w, height), 255)
        px = img.load()
        for x in range(w):
            h = int(vimg[x] * (height/255.0))
            for y in range(height-1, height-1-h, -1):
                px[x, y] = 0  # draw black bar up from bottom
        return img.convert('RGB')

    def _render_audio_diff(self, cover, stego, amplify=8):
        """
        Render absolute sample differences (first channel) as spikes after amplification.
        """
        c0 = cover[:, 0].astype(np.int64)
        s0 = stego[:, 0].astype(np.int64)
        m = min(c0.size, s0.size)
        if m == 0:
            return Image.new('RGB', (4, 4), (240, 240, 240))
        d = np.abs(s0[:m] - c0[:m])
        d = np.clip(d * amplify, 0, np.iinfo(np.int32).max)
        # normalize
        if d.max() == 0:
            d = d.astype(np.float32)
        else:
            d = d.astype(np.float32) / d.max()
        # draw like waveform (bars)
        h, w = 200, 1024
        if d.size > w:
            idx = np.linspace(0, d.size-1, w).astype(int)
            d = d[idx]
        else:
            pad = w - d.size
            if pad > 0:
                d = np.pad(d, (0, pad), mode='edge')
        img = Image.new('RGB', (w, h), (240, 240, 240))
        px = img.load()
        for x in range(w):
            bh = int(d[x] * (h-10))
            for y in range(h-1, h-1-bh, -1):
                px[x, y] = (30, 30, 30)
        return img

    def _score_stegoish(self, chi_p, corr, lsb_ratio, lsb_var_mean):
        """
        Lower chi_p (more random LSBs), lower corr (more noise),
        lsb_ratio close to 0.5, higher LSB variance => more 'stego-ish'.
        Returns a higher-better score in ~[0..1].
        """
        # map each metric to 0..1 (higher worse/nastier)
        s_chi = 1.0 - float(chi_p)              # 0 (clean) .. 1 (very random)
        # lower corr -> higher score
        s_corr = float(max(0.0, min(1.0, 1.0 - corr)))
        s_lsb = 1.0 - min(1.0, abs(lsb_ratio - 0.5) * 4.0)  # peak at 0.5
        s_var = float(max(0.0, min(1.0, lsb_var_mean)))     # already 0..1

        # weighted average (tweakable)
        return 0.35*s_chi + 0.25*s_corr + 0.25*s_lsb + 0.15*s_var

    def _an_save_report(self):
        text = self.an_audio_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showinfo("Info", "No analysis text to save yet.")
            return
        # Ask a base filename; we will create .txt and .json
        base = filedialog.asksaveasfilename(
            title="Save analysis report",
            defaultextension=".txt",
            filetypes=[("Text report", "*.txt")]
        )
        if not base:
            return
        # Save text
        try:
            with open(base, "w", encoding="utf-8") as f:
                f.write(text + "\n")
        except Exception as e:
            messagebox.showerror(
                "Save Error", f"Failed to save text report:\n{e}")
            return

        # Save JSON (if we have it)
        try:
            import json
            import os
            data = getattr(self, "_last_audio_report", None)
            if data is not None:
                json_path = os.path.splitext(base)[0] + ".json"
                with open(json_path, "w", encoding="utf-8") as jf:
                    json.dump(data, jf, indent=2)
        except Exception as e:
            messagebox.showerror(
                "Save Error", f"Failed to save JSON report:\n{e}")
            return

        messagebox.showinfo(
            "Saved", "Report saved (text and JSON, if available).")

    def _an_load_report(self):
        import json
        path = filedialog.askopenfilename(
            title="Load analysis report (.json or .txt)",
            filetypes=[("JSON or Text", "*.json *.txt")]
        )
        if not path:
            return
        try:
            if path.lower().endswith(".json"):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Rebuild a readable text from JSON
                lines = []
                lines.append("Audio Steganalysis Report (loaded)")
                lines.append("-------------------------------")
                lines.append(f"File: {os.path.basename(data.get('file', ''))}")
                lines.append(
                    f"Samplerate: {data.get('samplerate', '?')} Hz  |  Channels: {data.get('channels', '?')}  |  Bitdepth: {data.get('bitdepth', '?')}")
                lines.append(f"Duration: {data.get('duration_sec', 0):.2f}s")
                lines.append(
                    f"Assumed analysis LSBs: {data.get('assumed_lsbs', '?')}")
                lines.append("")
                m = data.get("metrics", {})
                lines.append(
                    f"Chi-square LSB p-value (overall): {m.get('chi_p_overall', '?')}")
                co = m.get("corr_overall", "?")
                lines.append(f"Neighbor correlation (overall): {co}")
                lines.append(
                    f"LSB ones-ratio (overall): {m.get('lsb_ratio_overall', '?')}")
                lines.append(
                    f"Mean LSB variance (blocks): {m.get('lsb_var_mean', '?')}")
                lines.append("")
                lines.append("Auto-detect (scan LSB=1..8):")
                for r in data.get("autodetect_scan_1to8", []):
                    lines.append(
                        f"  LSBs={r['lsbs']}: score={r['score']:.3f} | chi_p={r['chi_p']:.4f} corr={r['corr']:.4f} lsb_ratio={r['lsb_ratio']:.4f} var={r['lsb_var_mean']:.4f}")
                best = data.get("autodetect_best")
                if best:
                    lines.append(
                        f"→ Likely LSB depth: {best['lsbs']} (score {best['score']:.3f})")

                self.an_audio_text.delete(1.0, tk.END)
                self.an_audio_text.insert(1.0, "\n".join(lines))
                # We don't reconstruct images on load (that would require caching them); text+metrics is usually enough.
            else:
                # Plain text report
                with open(path, "r", encoding="utf-8") as f:
                    txt = f.read()
                self.an_audio_text.delete(1.0, tk.END)
                self.an_audio_text.insert(1.0, txt)
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load report:\n{e}")

    # -------------------- HASH KEY --------------------
    def hash_key(self, key):
        h = hashlib.sha256(key.encode()).digest()
        seed = int.from_bytes(h[:8], 'big')
        return h, seed

    # -------------------- VIDEO ANALYSIS TAB --------------------
    def setup_video_analysis_tab(self, parent):
        # same helper used by image analysis
        container = self.create_scrolled_frame(parent)
        # add padding wrapper (optional, keeps the same margins you had)
        pad = tk.Frame(container, bg='#f5f5f5')
        pad.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        picks = tk.LabelFrame(
            container, text="Select Video(s) to Analyze", bg='#f5f5f5', padx=10, pady=10)
        picks.pack(fill=tk.X)

        self.an_video_path = tk.StringVar()
        self.an_video_cover_hint = tk.StringVar()
        self.an_video_lsbs = tk.IntVar(value=1)

        r1 = tk.Frame(picks, bg='#f5f5f5')
        r1.pack(fill=tk.X, pady=3)
        tk.Label(r1, text="Suspected Stego Video:",
                 bg='#f5f5f5').pack(side=tk.LEFT)
        tk.Entry(r1, textvariable=self.an_video_path, state='readonly').pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        tk.Button(r1, text="Browse", command=self._an_browse_video,
                  bg='#2196F3', fg='white').pack(side=tk.LEFT)

        r2 = tk.Frame(picks, bg='#f5f5f5')
        r2.pack(fill=tk.X, pady=3)
        tk.Label(r2, text="(Optional) Original Cover Video:",
                 bg='#f5f5f5').pack(side=tk.LEFT)
        tk.Entry(r2, textvariable=self.an_video_cover_hint, state='readonly').pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        tk.Button(r2, text="Browse", command=self._an_browse_video_cover,
                  bg='#607D8B', fg='white').pack(side=tk.LEFT)

        r3 = tk.Frame(picks, bg='#f5f5f5')
        r3.pack(fill=tk.X, pady=6)
        tk.Label(r3, text="Assumed LSBs for Analysis:",
                 bg='#f5f5f5').pack(side=tk.LEFT)
        tk.Scale(r3, from_=1, to=8, orient=HORIZONTAL, variable=self.an_video_lsbs,
                 bg='#f5f5f5', length=200).pack(side=tk.LEFT, padx=10)

        actions = tk.Frame(container, bg='#f5f5f5')
        actions.pack(fill=tk.X, pady=8)
        tk.Button(actions, text="🔎 Run Video Analysis", command=self.run_video_stego_analysis,
                  bg='#4CAF50', fg='white', font=('Helvetica', 11, 'bold')).pack(side=tk.LEFT, padx=4)
        tk.Button(actions, text="💾 Save Report", command=self._an_video_save_report,
                  bg='#3F51B5', fg='white').pack(side=tk.LEFT, padx=4)
        tk.Button(actions, text="📂 Load Report", command=self._an_video_load_report,
                  bg='#009688', fg='white').pack(side=tk.LEFT, padx=4)
        tk.Button(actions, text="🗑️ Clear", command=self._an_video_clear_ui,
                  bg='#FF9800', fg='white').pack(side=tk.LEFT, padx=4)

        self.an_video_text = tk.Text(
            container, height=10, bg='#f8f8f8', relief=tk.SUNKEN, bd=2, font=('Consolas', 10))
        self.an_video_text.pack(fill=tk.X, pady=6)

        viz = tk.LabelFrame(
            container, text="Visual Diagnostics (First I-Frame)", bg='#f5f5f5', padx=10, pady=10)
        viz.pack(fill=tk.BOTH, expand=True)
        grid = tk.Frame(viz, bg='#f5f5f5')
        grid.pack(fill=tk.BOTH, expand=True)

        cap_font = ('Helvetica', 10, 'bold')
        self.viz_video_lsb_label = tk.Label(grid, bg='lightgrey', relief=tk.SUNKEN, bd=2,
                                            compound='top', font=cap_font,
                                            text="Cover Histogram (optional)")
        self.viz_video_heat_label = tk.Label(grid, bg='lightgrey', relief=tk.SUNKEN, bd=2,
                                             compound='top', font=cap_font,
                                             text="Stego Histogram")
        self.viz_video_hist_label = tk.Label(grid, bg='lightgrey', relief=tk.SUNKEN, bd=2,
                                             compound='top', font=cap_font,
                                             text="LSB Plane (combined RGB)")
        self.viz_video_diff_label = tk.Label(grid, bg='lightgrey', relief=tk.SUNKEN, bd=2,
                                             compound='top', font=cap_font,
                                             text="LSB-Variance Heatmap")

        self.viz_video_lsb_label.grid(
            row=0, column=0, padx=5, pady=5, sticky='nsew')
        self.viz_video_heat_label.grid(
            row=0, column=1, padx=5, pady=5, sticky='nsew')
        self.viz_video_hist_label.grid(
            row=1, column=0, padx=5, pady=5, sticky='nsew')
        self.viz_video_diff_label.grid(
            row=1, column=1, padx=5, pady=5, sticky='nsew')

        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)
        grid.grid_rowconfigure(0, weight=1)
        grid.grid_rowconfigure(1, weight=1)

    def _an_browse_video(self):
        path = filedialog.askopenfilename(title="Select Video", filetypes=[
                                          ("Video files", "*.mp4 *.mkv")])
        if path:
            self.an_video_path.set(path)

    def _an_browse_video_cover(self):
        path = filedialog.askopenfilename(title="Select Original Cover Video", filetypes=[
                                          ("Video files", "*.mp4 *.mkv")])
        if path:
            self.an_video_cover_hint.set(path)

    def _an_video_clear_ui(self):
        self.an_video_path.set("")
        self.an_video_cover_hint.set("")
        self.an_video_lsbs.set(1)
        self.an_video_text.delete(1.0, tk.END)
        # Restore default text for each label (matching setup_video_analysis_tab)
        self.viz_video_lsb_label.configure(
            image='', text="Cover Histogram (optional)")
        self.viz_video_lsb_label.image = None
        self.viz_video_heat_label.configure(image='', text="Stego Histogram")
        self.viz_video_heat_label.image = None
        self.viz_video_hist_label.configure(
            image='', text="LSB Plane (combined RGB)")
        self.viz_video_hist_label.image = None
        self.viz_video_diff_label.configure(
            image='', text="LSB-Variance Heatmap")
        self.viz_video_diff_label.image = None

    def run_video_stego_analysis(self):
        if shutil.which("ffmpeg") is None:
            messagebox.showerror(
                "Error", "FFmpeg not found. Please install FFmpeg to use video analysis.")
            return

        path = self.an_video_path.get().strip()
        if not path:
            messagebox.showerror("Error", "Select a video file to analyze.")
            return

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                # Extract first I-frame from stego video
                stego_iframe_path = self._extract_first_iframe(
                    path, tmpdir, "stego_iframe.png")
                if not os.path.exists(stego_iframe_path):
                    raise ValueError("No I-frame found in stego video.")

                # Load I-frame as array
                img = Image.open(stego_iframe_path).convert('RGB')
                arr = np.array(img, dtype=np.uint8)

                # ---- choose bit-plane from slider (1..8 on UI ⇒ 0..7 bit index) ----
                k = max(0, min(int(self.an_video_lsbs.get()) - 1, 7))

                # ---- headline metrics on selected bit-plane k ----
                chi_p = self._chi_square_lsb_pvalue(arr)
                corr = self._neighbor_correlation(arr)
                lsb_ratio = self._lsb_one_ratio(arr)
                heat = self._lsb_variance_heatmap(arr, block=8)  # 8x8 blocks

                # ---- auto-detect most likely bit depth (scan 1..8 → bit_index 0..7) ----
                autodet_rows = []
                best = None
                for d in range(1, 9):
                    kk = d - 1
                    chi_p_o = self._chi_square_lsb_pvalue(arr)
                    corr_o = self._neighbor_correlation(arr)
                    lsb_ratio_o = self._lsb_one_ratio(arr)
                    series = self._lsb_variance_heatmap(arr, block=8)
                    var_mean = float(series.mean()) if series.size else 0.0
                    score = float(self._score_stegoish(
                        chi_p_o, corr_o, lsb_ratio_o, var_mean))
                    row = {
                        "lsbs": d, "score": score,
                        "chi_p": float(chi_p_o),
                        "corr": float(corr_o),
                        "lsb_ratio": float(lsb_ratio_o),
                        "var": float(var_mean),
                    }
                    autodet_rows.append(row)
                    if (best is None) or (row["score"] > best["score"]):
                        best = row

                # ---- optional difference view with original cover ----
                diff_img = None
                hist_cover_img = None
                cover_path = self.an_video_cover_hint.get().strip()
                if cover_path and os.path.exists(cover_path):
                    cover_iframe_path = self._extract_first_iframe(
                        cover_path, tmpdir, "cover_iframe.png")
                    if os.path.exists(cover_iframe_path):
                        cover_img = Image.open(
                            cover_iframe_path).convert('RGB')
                        cover_arr = np.array(cover_img, dtype=np.uint8)
                        diff_img = self._render_diff_amplified(
                            cover_img, img, factor=16)
                        hist_cover_img = self._render_histograms_gui_style(
                            cover_arr)  # Changed to match Image Analysis style

                # ---- visuals ----
                lsb_img = self._render_lsb_plane(arr)
                hist_img = self._render_histograms_gui_style(
                    arr)     # Changed to match Image Analysis style
                heat_img = self._render_heatmap_image(heat, img.size)

                # ---- video params ----
                params = self.get_video_params(path)
                duration = params['duration']
                resolution = f"{params['width']}x{params['height']}"
                fps = params['fps']
                i_frame_count = params['i_frame_count']

                # ---- report text ----
                lines = []
                lines.append(
                    "Auto-detect (scan LSB=1..8 on first I-frame): higher score = more 'stego-ish'")
                for r in autodet_rows:
                    lines.append(
                        f"LSBs={r['lsbs']}: score={r['score']:.3f} | "
                        f"chi_p={r['chi_p']:.4f} corr={r['corr']:.4f} "
                        f"lsb_ratio={r['lsb_ratio']:.4f} var={r['var']:.4f}"
                    )
                if best:
                    lines.append(
                        f"\nLikely LSB depth: {best['lsbs']} (score {best['score']:.3f})\n")

                lines.append("Summary on first I-frame (bit-plane 0)")
                lines.append("------------------------")
                lines.append(
                    f"Video: {os.path.basename(path)}  |  Duration: {duration:.2f}s | Resolution: {resolution} | FPS: {fps:.2f} | I-frames: {i_frame_count}")
                lines.append(f"Analyzed bit-plane: {k}  (UI value {k+1})")
                lines.append(f"Chi-square LSB p-value: {chi_p:.4f}")
                lines.append(
                    f"Neighbor correlation (0..1). Natural images ~0.90–0.99: {corr:.4f}")
                lines.append(
                    f"LSB ones-ratio (should be near 0.5): {lsb_ratio:.4f}")
                lines.append(
                    "Heatmap: bright regions = higher LSB variability (possible embedding zones)\n")

                # ---- show text ----
                self.an_video_text.delete(1.0, tk.END)
                self.an_video_text.insert(1.0, "\n".join(lines))

                # ---- show images ----
                def _to_tk(im, max_wh=(450, 450)):
                    imc = im.copy()
                    imc.thumbnail(max_wh)
                    return ImageTk.PhotoImage(imc)

                # Assign to match labels: Cover Hist (if available), Stego Hist, LSB Plane, Heatmap/Diff
                if hist_cover_img is not None:
                    cov_tk = _to_tk(hist_cover_img)
                    self.viz_video_lsb_label.configure(image=cov_tk)
                    self.viz_video_lsb_label.image = cov_tk
                else:
                    self.viz_video_lsb_label.configure(
                        image='', text="Cover Histogram (optional)")
                    self.viz_video_lsb_label.image = None

                stego_tk = _to_tk(hist_img)
                self.viz_video_heat_label.configure(image=stego_tk)
                self.viz_video_heat_label.image = stego_tk

                lsb_tk = _to_tk(lsb_img)
                self.viz_video_hist_label.configure(image=lsb_tk)
                self.viz_video_hist_label.image = lsb_tk

                if diff_img is not None:
                    diff_tk = _to_tk(diff_img)
                    self.viz_video_diff_label.configure(image=diff_tk)
                    self.viz_video_diff_label.image = diff_tk
                else:
                    heat_tk = _to_tk(heat_img)
                    self.viz_video_diff_label.configure(image=heat_tk)
                    self.viz_video_diff_label.image = heat_tk

        except Exception as e:
            messagebox.showerror("Analysis Error", str(e))

    def _an_video_save_report(self):
        text = self.an_video_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showinfo("Info", "No analysis text to save yet.")
            return
        base = filedialog.asksaveasfilename(
            title="Save analysis report",
            defaultextension=".txt",
            filetypes=[("Text report", "*.txt")]
        )
        if not base:
            return
        try:
            with open(base, "w", encoding="utf-8") as f:
                f.write(text + "\n")
        except Exception as e:
            messagebox.showerror(
                "Save Error", f"Failed to save text report:\n{e}")
            return

        messagebox.showinfo("Saved", "Report saved.")

    def _an_video_load_report(self):
        path = filedialog.askopenfilename(
            title="Load analysis report (.txt)",
            filetypes=[("Text report", "*.txt")]
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                txt = f.read()
            self.an_video_text.delete(1.0, tk.END)
            self.an_video_text.insert(1.0, txt)
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load report:\n{e}")


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
