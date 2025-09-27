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
        self.title("LSB Steganography Tool - Enhanced GUI with Audio & Text Support")
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
        self.audio_stego_path = tk.StringVar()      # NEW: last-created stego WAV (encode tab)
        self.audio_decode_stego_path = tk.StringVar()  # NEW: stego path chosen in decode tab
        self.audio_secret_key = tk.StringVar()
        self.audio_num_lsbs = tk.IntVar(value=1)
        self.audio_payload_type = tk.StringVar(value="file")
        self.audio_payload_text = tk.StringVar()
        self.show_key = tk.BooleanVar(value=False)
        self.show_audio_key = tk.BooleanVar(value=False)

        # playback state
        self._audio_proc = None  # for macOS/Linux subprocess player
        self._ab_state = "cover"  # toggle state

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

        analysis_frame = ttk.Frame(notebook)
        notebook.add(analysis_frame, text="Image Analysis")

        audio_analysis_frame = ttk.Frame(notebook)
        notebook.add(audio_analysis_frame, text="Audio Analysis")
        
        self.setup_audio_analysis_tab(audio_analysis_frame)
        self.setup_analysis_tab(analysis_frame)
        self.setup_encode_tab(encode_frame)
        self.setup_decode_tab(decode_frame)
        self.setup_audio_encode_tab(audio_encode_frame)
        self.setup_audio_decode_tab(audio_decode_frame)

    # -------------------- IMAGE ENCODE TAB --------------------
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

    # -------------------- AUDIO ENCODE TAB --------------------
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
        self.audio_cover_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

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
        self.audio_payload_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        tk.Button(self.audio_payload_file_frame, text="Browse", command=self.browse_audio_payload,
                  bg='#2196F3', fg='white', font=('Helvetica', 9, 'bold')).pack(side=tk.RIGHT)

        self.audio_payload_drop_zone = DropZone(payload_section,
                                                "Drag & Drop Payload File Here\n(Any file type)",
                                                callback=self.set_audio_payload)
        self.audio_payload_drop_zone.pack(fill=tk.X, pady=5)

        self.audio_payload_text_frame = tk.Frame(payload_section, bg='#f5f5f5')
        self.audio_payload_text_area = tk.Text(self.audio_payload_text_frame, height=4, font=('Helvetica', 10))
        self.audio_payload_text_area.pack(fill=tk.X, pady=5)
        self.audio_payload_text_area.bind('<<Modified>>', self.update_audio_payload_text)

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

        # FIX Bullet 2: extend to 8 LSBs
        audio_lsb_slider = Scale(lsb_frame, from_=1, to=8, orient=HORIZONTAL,
                                 variable=self.audio_num_lsbs,
                                 command=lambda _=None: (self.update_audio_capacity_display(), self.update_audio_visuals()),
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

        # NEW: Playback & Compare UI (Bullet 8)
        play_frame = tk.LabelFrame(parent, text="Playback & Compare",
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

        # NEW: Waveform + LSB visualisation (Bullet 9)
        vis_frame = tk.LabelFrame(parent, text="Audio Visualisation (LSB changes)",
                                  font=('Helvetica', 10, 'bold'), bg='#f5f5f5',
                                  padx=10, pady=10)
        vis_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=5)

        canv_height = 140
        self.audio_canvas_cover = tk.Canvas(vis_frame, width=540, height=canv_height, bg="#ffffff", bd=1, relief=tk.SUNKEN)
        self.audio_canvas_cover.pack(side=tk.LEFT, padx=5, pady=5)
        self.audio_canvas_stego = tk.Canvas(vis_frame, width=540, height=canv_height, bg="#ffffff", bd=1, relief=tk.SUNKEN)
        self.audio_canvas_stego.pack(side=tk.LEFT, padx=5, pady=5)

        self.audio_flip_label = tk.Label(parent, text="LSB flips: N/A", bg="#f5f5f5", font=("Helvetica", 10, "italic"))
        self.audio_flip_label.pack(anchor=tk.W, padx=20, pady=(0, 10))

        button_frame = tk.Frame(parent, bg='#f5f5f5')
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
        self.audio_stego_canvas_dec = tk.Canvas(decode_frame, width=1100, height=140, bg="#ffffff", bd=1, relief=tk.SUNKEN)
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
                                  command=self.run_decode, height=3, width=30)
        decode_button.pack(pady=20)

        self.decode_result = tk.Text(decode_frame, height=10, width=60,
                                     font=('Consolas', 10), bg='#f8f8f8',
                                     relief=tk.SUNKEN, bd=2)
        self.decode_result.pack(fill=tk.BOTH, expand=True, pady=10)

    # -------------------- COMMON (image region selection) --------------------
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

    # -------------------- AUDIO HELPERS: playback & visualisation --------------------
    def _play_wav_crossplatform(self, path):
        sys = platform.system()
        try:
            if sys == "Windows":
                import winsound
                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                self._audio_proc = None  # winsound handles it
            elif sys == "Darwin":
                # macOS: afplay
                self._audio_proc = subprocess.Popen(["afplay", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                # Linux: try aplay, fallback to paplay
                try:
                    self._audio_proc = subprocess.Popen(["aplay", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception:
                    self._audio_proc = subprocess.Popen(["paplay", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            messagebox.showerror("Playback error", f"Could not play audio:\n{e}")

    def stop_audio(self):
        sys = platform.system()
        try:
            if sys == "Windows":
                import winsound
                winsound.PlaySound(None, 0)  # stop async
            else:
                if self._audio_proc and self._audio_proc.poll() is None:
                    self._audio_proc.terminate()
                    self._audio_proc = None
        except Exception:
            pass

    def play_audio_cover(self):
        path = self.audio_cover_path.get()
        if not path or not os.path.exists(path):
            messagebox.showinfo("Info", "No cover audio loaded.")
            return
        self._ab_state = "cover"
        self._play_wav_crossplatform(path)

    def _get_any_stego_path(self):
        # Prefer stego created in encode tab; fallback to one chosen in decode tab
        p1 = self.audio_stego_path.get()
        p2 = self.audio_decode_stego_path.get()
        if p1 and os.path.exists(p1):
            return p1
        if p2 and os.path.exists(p2):
            return p2
        return None

    def play_audio_stego(self):
        # If no stego path yet on encode tab, allow choosing one (useful in decode tab too)
        path = self._get_any_stego_path()
        if not path:
            # let user choose in case of decode tab or external stego
            path = filedialog.askopenfilename(title="Select Stego Audio (WAV)", filetypes=[("WAV files", "*.wav")])
            if not path:
                return
            self.audio_decode_stego_path.set(path)
            # draw decode tab waveform
            self._draw_waveform(self.audio_stego_canvas_dec, path, title="Stego (Decode)")

        self._ab_state = "stego"
        self._play_wav_crossplatform(path)

    def ab_toggle(self):
        # Quickly toggle between cover and stego
        stego = self._get_any_stego_path()
        cover = self.audio_cover_path.get()
        if not cover or not os.path.exists(cover):
            messagebox.showinfo("Info", "No cover audio loaded to A/B against.")
            return
        if not stego:
            messagebox.showinfo("Info", "No stego audio available to A/B against.")
            return

        # toggle
        self.stop_audio()
        if self._ab_state == "cover":
            self._ab_state = "stego"
            self._play_wav_crossplatform(stego)
        else:
            self._ab_state = "cover"
            self._play_wav_crossplatform(cover)

    def _load_wav_samples(self, path):
        with wave.open(path, 'rb') as wav_file:
            params = wav_file.getparams()
            frames = wav_file.readframes(params.nframes)
        if params.sampwidth == 1:
            data = np.frombuffer(frames, dtype=np.uint8).astype(np.int16) - 128  # center to 0
        elif params.sampwidth == 2:
            data = np.frombuffer(frames, dtype=np.int16)
        elif params.sampwidth == 3:
            raw = np.frombuffer(frames, dtype=np.uint8).reshape(-1, 3)
            data = (raw[:, 0].astype(np.int32) |
                    (raw[:, 1].astype(np.int32) << 8) |
                    (raw[:, 2].astype(np.int32) << 16))
            data = np.where(data >= (1 << 23), data - (1 << 24), data).astype(np.int32)
        else:
            raise ValueError("Unsupported sample width. Only 8/16/24-bit.")
        # If stereo or more, convert to mono for drawing
        with wave.open(path, 'rb') as wav_file:
            channels = wav_file.getnchannels()
        if channels > 1:
            data = data.reshape(-1, channels).mean(axis=1)
        return data

    def _draw_waveform(self, canvas, wav_path, title=""):
        if not os.path.exists(wav_path):
            canvas.delete("all")
            return
        try:
            samples = self._load_wav_samples(wav_path)
        except Exception:
            canvas.delete("all")
            return

        canvas.delete("all")
        w = canvas.winfo_width() or 540
        h = canvas.winfo_height() or 140
        # draw title
        if title:
            canvas.create_text(5, 8, text=title, anchor="w", font=("Helvetica", 9, "bold"))

        if len(samples) < 2:
            return
        # downsample for speed
        step = max(1, len(samples) // (w-10))
        seg = samples[::step]
        if len(seg) < 2:
            return
        # normalize to canvas height
        maxv = float(np.max(np.abs(seg))) or 1.0
        scale_y = (h - 20) / (2 * maxv)
        points = []
        for i, v in enumerate(seg[:w-10]):
            x = 5 + i
            y = h/2 - (v * scale_y)
            points.append((x, y))

        # draw midline
        canvas.create_line(5, h/2, w-5, h/2, fill="#cccccc")
        # draw waveform
        for i in range(1, len(points)):
            x1, y1 = points[i-1]
            x2, y2 = points[i]
            canvas.create_line(x1, y1, x2, y2)

    def _lsb_flip_count(self, cover_path, stego_path, num_lsbs):
        if not (cover_path and stego_path and os.path.exists(cover_path) and os.path.exists(stego_path)):
            return None
        try:
            with wave.open(cover_path, 'rb') as w1, wave.open(stego_path, 'rb') as w2:
                if (w1.getsampwidth(), w1.getnchannels(), w1.getframerate()) != \
                   (w2.getsampwidth(), w2.getnchannels(), w2.getframerate()):
                    # Still try with min len & channel-agnostic mono compare
                    pass

            a = self._load_wav_samples(cover_path)
            b = self._load_wav_samples(stego_path)
            n = min(len(a), len(b))
            if n == 0:
                return 0
            a = a[:n]
            b = b[:n]
            mask = (1 << num_lsbs) - 1
            flips = np.count_nonzero(((a ^ b) & mask) != 0)
            return int(flips)
        except Exception:
            return None

    def update_audio_visuals(self):
        # Draw cover waveform
        cpath = self.audio_cover_path.get()
        if cpath and os.path.exists(cpath):
            self._draw_waveform(self.audio_canvas_cover, cpath, title="Cover")
        else:
            self.audio_canvas_cover.delete("all")

        # Draw stego waveform (encode tab), if we have one
        spath = self.audio_stego_path.get()
        if spath and os.path.exists(spath):
            self._draw_waveform(self.audio_canvas_stego, spath, title="Stego")
            # compute LSB flips
            flips = self._lsb_flip_count(cpath, spath, self.audio_num_lsbs.get())
            if flips is None:
                self.audio_flip_label.config(text="LSB flips: N/A")
            else:
                self.audio_flip_label.config(text=f"LSB flips (within {self.audio_num_lsbs.get()} LSBs): {flips:,}")
        else:
            self.audio_canvas_stego.delete("all")
            self.audio_flip_label.config(text="LSB flips: N/A")

    # -------------------- AUDIO tab set/browse --------------------
    def set_audio_cover(self, file_path):
        self.audio_cover_path.set(file_path)
        self.audio_cover_drop_zone.update_text(f"✓ {os.path.basename(file_path)}")
        self.display_audio_info(file_path)
        self.update_audio_capacity_display()
        self.update_audio_visuals()

    def set_audio_payload(self, file_path):
        self.audio_payload_path.set(file_path)
        self.audio_payload_drop_zone.update_text(f"✓ {os.path.basename(file_path)}")
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

    # -------------------- TEXT/FILE toggles --------------------
    def toggle_key_visibility(self):
        self.key_entry.config(show="" if self.show_key.get() else "*")

    def toggle_audio_key_visibility(self):
        self.audio_key_entry.config(show="" if self.show_audio_key.get() else "*")

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
        self.payload_text.set(self.payload_text_area.get("1.0", tk.END).strip())
        self.payload_text_area.edit_modified(False)
        self.update_capacity_display()

    def update_audio_payload_text(self, event=None):
        self.audio_payload_text.set(self.audio_payload_text_area.get("1.0", tk.END).strip())
        self.audio_payload_text_area.edit_modified(False)
        self.update_audio_capacity_display()

    # -------------------- IMAGE DECODE/ENCODE --------------------
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

    def set_cover_image(self, file_path):
        self.cover_path.set(file_path)
        self.cover_drop_zone.update_text(f"✓ {os.path.basename(file_path)}")
        self.display_image(file_path)
        self.update_capacity_display()

    def set_payload_file(self, file_path):
        self.payload_path.set(file_path)
        self.payload_drop_zone.update_text(f"✓ {os.path.basename(file_path)}")
        self.update_capacity_display()

    def display_image(self, path):
        try:
            img = Image.open(path)
            canvas_width = self.cover_canvas.winfo_width()
            canvas_height = self.cover_canvas.winfo_height()
            if canvas_width < 10:
                canvas_width = 450
                canvas_height = 450

            img_width, img_height = img.size
            aspect_ratio = min(canvas_width / img_width, canvas_height / img_height)
            new_width = int(img_width * aspect_ratio)
            new_height = int(img_height * aspect_ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            self.tk_img = ImageTk.PhotoImage(img)
            self.cover_canvas.delete("all")
            self.cover_image_on_canvas = self.cover_canvas.create_image(0, 0, anchor="nw", image=self.tk_img)
            self.cover_canvas.config(scrollregion=(0, 0, new_width, new_height))
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
        self.cover_canvas.coords(self.selection_rect, self.start_x, self.start_y, event.x, event.y)

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
        return (int(x1 * scale_x), int(y1 * scale_y), int(x2 * scale_x), int(y2 * scale_y))

    # -------------------- HASH / KEY --------------------
    def hash_key(self, key):
        """Generate SHA-256 hash of the key and return first 4 bytes and integer seed."""
        key_bytes = key.encode('utf-8')
        key_hash = hashlib.sha256(key_bytes).digest()
        hash_prefix = key_hash[:4]  # First 4 bytes for metadata
        seed = int.from_bytes(key_hash, 'big') % (2**32)  # Convert to integer for random.seed
        return hash_prefix, seed

    # -------------------- IMAGE ENCODE/DECODE --------------------
    def run_encode(self):
        cover = self.cover_path.get()
        key = self.secret_key.get()

        if not cover or not key:
            messagebox.showerror("Error", "Please provide Cover Image and a Secret Key.")
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
                messagebox.showerror("Error", f"Failed to read payload file: {e}")
                return
        else:
            payload_text = self.payload_text.get()
            if not payload_text:
                messagebox.showerror("Error", "Please enter text to encode.")
                return
            payload_data = payload_text.encode('utf-8')
            filename = "text_payload.txt"

        try:
            stego_path = self._encode_image(cover, payload_data, filename, key, self.num_lsbs.get())
            messagebox.showinfo("Success", f"✅ Payload embedded successfully!\n📁 Stego-image saved as:\n{stego_path}")

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
            aspect_ratio = min(canvas_width / img_width, canvas_height / img_height)
            new_width = int(img_width * aspect_ratio)
            new_height = int(img_height * aspect_ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            self.stego_img = ImageTk.PhotoImage(img)
            self.stego_canvas.delete("all")
            self.stego_canvas.create_image(0, 0, anchor="nw", image=self.stego_img)
            self.stego_canvas.config(scrollregion=(0, 0, new_width, new_height))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to display stego image: {e}")

    def run_decode(self):
        stego_path = filedialog.askopenfilename(
            title="Select Stego-Image",
            filetypes=[("Image files", "*.png *.bmp *.jpg *.jpeg *.gif")]
        )
        if not stego_path:
            return

        key = simpledialog.askstring("Input", "Enter the Secret Key:", show="*")
        if not key:
            messagebox.showerror("Error", "A valid key is required for decoding.")
            return

        try:
            extracted_path, is_text = self._decode_image(stego_path, key, self.num_lsbs.get())

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

            if messagebox.askyesno("Success",
                                   f"✅ Payload extracted!\n📁 Saved as: {os.path.basename(extracted_path)}\n\n🔍 Open now?"):
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

    # -------------------- AUDIO ENCODE/DECODE --------------------
    def run_audio_encode(self):
        cover = self.audio_cover_path.get()
        key = self.audio_secret_key.get()

        if not cover or not key:
            messagebox.showerror("Error", "Please provide Cover Audio File and a Secret Key.")
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
                messagebox.showerror("Error", f"Failed to read payload file: {e}")
                return
        else:
            payload_text = self.audio_payload_text.get()
            if not payload_text:
                messagebox.showerror("Error", "Please enter text to encode.")
                return
            payload_data = payload_text.encode('utf-8')
            filename = "text_payload.txt"

        try:
            stego_path = self._encode_audio(cover, payload_data, filename, key, self.audio_num_lsbs.get())
            messagebox.showinfo("Success", f"✅ Payload embedded successfully!\n🎵 Stego-audio saved as:\n{stego_path}")

            # NEW: keep path for playback/visuals; enable buttons
            self.audio_stego_path.set(stego_path)
            try:
                self.btn_play_stego_enc.config(state=tk.NORMAL)
            except Exception:
                pass
            try:
                self.btn_play_stego_dec.config(state=tk.NORMAL)
            except Exception:
                pass

            # Update visuals (waveforms + flip count)
            self.update_audio_visuals()

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

        # draw in decode tab for quick preview
        self.audio_decode_stego_path.set(stego_path)
        self._draw_waveform(self.audio_stego_canvas_dec, stego_path, title="Stego (Decode)")

        key = simpledialog.askstring("Input", "Enter the Secret Key:", show="*")
        if not key:
            messagebox.showerror("Error", "A valid key is required for decoding.")
            return

        try:
            extracted_path, is_text = self._decode_audio(stego_path, key, self.audio_num_lsbs.get())

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

            if messagebox.askyesno("Success",
                                   f"✅ Payload extracted!\n📁 Saved as: {os.path.basename(extracted_path)}\n\n🔍 Open now?"):
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
        self.audio_info_label.config(text="Select an audio file to view information")
        self.show_audio_key.set(False)
        try:
            self.audio_key_entry.config(show="*")
        except Exception:
            pass

        self.audio_cover_drop_zone.update_text("Drag & Drop Cover Audio File Here\n(WAV format)")
        self.audio_payload_drop_zone.update_text("Drag & Drop Payload File Here\n(Any file type)")
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

        self.cover_drop_zone.update_text("Drag & Drop Cover Image Here\n(PNG, BMP, JPG)")
        self.payload_drop_zone.update_text("Drag & Drop Payload File Here\n(Any file type)")
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

            # Fixed header (22 bytes)
            header = (
                MAGIC +
                key_hash[:4] +
                bytes([num_lsbs & 0xFF]) +
                len(payload_data).to_bytes(4, "big") +
                bytes([fn_len]) +
                int(x1).to_bytes(2, "big") + int(y1).to_bytes(2, "big") +
                int(x2).to_bytes(2, "big") + int(y2).to_bytes(2, "big")
            )

            body = fn_bytes + payload_data

            hdr_bits = bitarray(); hdr_bits.frombytes(header)
            body_bits = bitarray(); body_bits.frombytes(body)

            pixels = image.load()
            all_pos = [(x, y) for y in range(height) for x in range(width)]

            def embed_bits(positions, bits, per_pixel_lsbs):
                idx = 0
                mask_keep = (255 << per_pixel_lsbs) & 255
                for (x, y) in positions:
                    if idx >= len(bits): break
                    r, g, b = pixels[x, y]
                    rgb = [r, g, b]
                    for i in range(3):
                        if idx >= len(bits): break
                        chunk = bits[idx:idx + per_pixel_lsbs]
                        val = int(chunk.to01(), 2) if chunk else 0
                        rgb[i] = (rgb[i] & mask_keep) | val
                        idx += per_pixel_lsbs
                    pixels[x, y] = tuple(rgb)
                return idx

            # 1) Write header with 1 LSB in raster order
            header_bits_needed = len(header) * 8
            hdr_px_needed = (header_bits_needed + (HEADER_LSBS * 3) - 1) // (HEADER_LSBS * 3)
            header_pos = all_pos[:hdr_px_needed]
            if embed_bits(header_pos, hdr_bits, HEADER_LSBS) < len(hdr_bits):
                raise ValueError("Not enough space for header.")

            # 2) Prepare body positions (region, minus header pixels)
            if x1 == y1 == x2 == y2 == 0:
                region_pos = all_pos
            else:
                region_pos = [(x, y) for y in range(y1, y2) for x in range(x1, x2)]
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

            stego_path = os.path.join(os.path.dirname(cover_path), "stego_" + os.path.basename(cover_path))
            image.save(stego_path, "PNG")
            return stego_path

    def _decode_image(self, stego_path, key, _ignored_num_lsbs):
        MAGIC = b"STG2"
        FIXED_HDR_LEN = 22
        HEADER_LSBS = 1

        image = Image.open(stego_path).convert("RGB")
        width, height = image.size
        pixels = image.load()

        all_pos = [(x, y) for y in range(height) for x in range(width)]
        header_bits_needed = FIXED_HDR_LEN * 8
        hdr_px_needed = (header_bits_needed + (HEADER_LSBS * 3) - 1) // (HEADER_LSBS * 3)
        header_pos = all_pos[:hdr_px_needed]

        def extract_bits(positions, nbits, per_pixel_lsbs):
            out = bitarray()
            mask = (1 << per_pixel_lsbs) - 1
            for (x, y) in positions:
                if len(out) >= nbits: break
                r, g, b = pixels[x, y]
                for val in (r, g, b):
                    if len(out) >= nbits: break
                    out.extend(bin(val & mask)[2:].zfill(per_pixel_lsbs))
            return out

        # 1) Read header
        hdr_bits = extract_bits(header_pos, header_bits_needed, HEADER_LSBS)
        hdr = hdr_bits.tobytes()[:FIXED_HDR_LEN]
        if hdr[:4] != MAGIC:
            raise ValueError("Unsupported/old stego format or corrupted header.")

        stored_key_prefix = hdr[4:8]
        body_num_lsbs = hdr[8]
        payload_size = int.from_bytes(hdr[9:13], "big")
        filename_len = hdr[13]
        x1 = int.from_bytes(hdr[14:16], "big")
        y1 = int.from_bytes(hdr[16:18], "big")
        x2 = int.from_bytes(hdr[18:20], "big")
        y2 = int.from_bytes(hdr[20:22], "big")

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

        # 3) Extract body with stored LSBs
        body_bits = extract_bits(region_pos, total_body_bits, body_num_lsbs)
        if len(body_bits) < total_body_bits:
            raise ValueError("Incomplete embedded data (region/LSB mismatch).")

        body = body_bits.tobytes()
        filename = body[:filename_len].decode("utf-8", errors="replace")
        payload = body[filename_len:filename_len + payload_size]

        extracted_path = os.path.join(os.path.dirname(stego_path), f"extracted_{filename}")
        with open(extracted_path, "wb") as f:
            f.write(payload)
        is_text = filename.endswith(".txt")
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
            raise ValueError("Unsupported sample width. Only 8, 16, and 24-bit audio supported.")

        max_bits = len(audio_data) * num_lsbs
        if len(bit_stream) > max_bits:
            raise ValueError(f"Payload too large: {len(bit_stream)} bits > {max_bits} bits available")

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

        stego_path = os.path.join(os.path.dirname(cover_path), "stego_" + os.path.basename(cover_path))

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
            raise ValueError("Unsupported sample width. Only 8, 16, and 24-bit audio supported.")

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

        payload_bits = extracted_bits[offset + filename_len * 8:offset + filename_len * 8 + payload_size * 8]
        if len(payload_bits) != payload_size * 8:
            raise ValueError("Incomplete payload data")

        payload_data = payload_bits.tobytes()
        extracted_path = os.path.join(os.path.dirname(stego_path), f"extracted_{filename}")
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
            filename = "text_payload.txt" if self.payload_type.get() == "text" else os.path.basename(self.payload_path.get())
            metadata_size = 9 + len(filename)  # bytes
            total_bits_needed = (payload_size + metadata_size) * 8
            if bits_available_per_pixel == 0:
                return None
            required_lsbs = math.ceil(total_bits_needed / bits_available_per_pixel)
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
            filename = "text_payload.txt" if self.audio_payload_type.get() == "text" else os.path.basename(self.audio_payload_path.get())
            metadata_size = 9 + len(filename)  # bytes
            total_bits_needed = (payload_size + metadata_size) * 8
            if total_samples == 0:
                return None
            required_lsbs = math.ceil(total_bits_needed / total_samples)
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
            capacity_bytes = self._calculate_capacity(cover_path, self.num_lsbs.get(), region)
            capacity_kb = capacity_bytes / 1024

            payload_size = 0
            if self.payload_type.get() == "file" and self.payload_path.get():
                try:
                    payload_size = os.path.getsize(self.payload_path.get())
                except:
                    payload_size = 0
            elif self.payload_type.get() == "text" and self.payload_text.get():
                payload_size = len(self.payload_text.get().encode('utf-8'))

            recommended_lsbs = self.calculate_required_lsbs_image(cover_path, payload_size, region)
            if recommended_lsbs is not None:
                self.capacity_label.config(text=f"Capacity: {capacity_kb:.2f} KB\nRecommended LSBs: {recommended_lsbs}")
            else:
                self.capacity_label.config(text=f"Capacity: {capacity_kb:.2f} KB\nRecommended LSBs: N/A (Select payload)")
        except Exception:
            self.capacity_label.config(text="Capacity: Error")

    def update_audio_capacity_display(self, *args):
        audio_path = self.audio_cover_path.get()
        if not audio_path or not os.path.exists(audio_path):
            self.audio_capacity_label.config(text="Capacity: Select an audio file")
            return
        try:
            capacity_bytes = self._calculate_audio_capacity(audio_path, self.audio_num_lsbs.get())
            capacity_kb = capacity_bytes / 1024

            payload_size = 0
            if self.audio_payload_type.get() == "file" and self.audio_payload_path.get():
                try:
                    payload_size = os.path.getsize(self.audio_payload_path.get())
                except:
                    payload_size = 0
            elif self.audio_payload_type.get() == "text" and self.audio_payload_text.get():
                payload_size = len(self.audio_payload_text.get().encode('utf-8'))

            recommended_lsbs = self.calculate_required_lsbs_audio(audio_path, payload_size)

            if recommended_lsbs is not None:
                self.audio_capacity_label.config(text=f"Capacity: {capacity_kb:.2f} KB\nRecommended LSBs: {recommended_lsbs}")
            else:
                self.audio_capacity_label.config(text=f"Capacity: {capacity_kb:.2f} KB\nRecommended LSBs: N/A (Select payload)")
        except Exception:
            self.audio_capacity_label.config(text="Capacity: Error")

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
        
    def setup_analysis_tab(self, parent):
        container = tk.Frame(parent, bg='#f5f5f5')
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ---- File pickers ----
        pickers = tk.LabelFrame(container, text="Select Image(s) to Analyze", bg='#f5f5f5', padx=10, pady=10)
        pickers.pack(fill=tk.X)

        self.analysis_image_path = tk.StringVar()
        self.analysis_cover_hint_path = tk.StringVar()

        row1 = tk.Frame(pickers, bg='#f5f5f5'); row1.pack(fill=tk.X, pady=3)
        tk.Label(row1, text="Suspected Stego Image:", bg='#f5f5f5').pack(side=tk.LEFT)
        tk.Entry(row1, textvariable=self.analysis_image_path, state='readonly').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        tk.Button(row1, text="Browse", command=self.browse_analysis_image, bg='#2196F3', fg='white').pack(side=tk.LEFT)

        row2 = tk.Frame(pickers, bg='#f5f5f5'); row2.pack(fill=tk.X, pady=3)
        tk.Label(row2, text="(Optional) Original Cover for Diff:", bg='#f5f5f5').pack(side=tk.LEFT)
        tk.Entry(row2, textvariable=self.analysis_cover_hint_path, state='readonly').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        tk.Button(row2, text="Browse", command=self.browse_analysis_cover_hint, bg='#607D8B', fg='white').pack(side=tk.LEFT)

        # ---- Run / Info ----
        actions = tk.Frame(container, bg='#f5f5f5'); actions.pack(fill=tk.X, pady=8)
        tk.Button(actions, text="🔍 Run Stego Analysis", command=self.run_image_analysis, bg='#4CAF50', fg='white', font=('Helvetica', 11, 'bold')).pack(side=tk.LEFT, padx=4)
        tk.Button(actions, text="🗑️ Clear", command=self.clear_analysis_ui, bg='#FF9800', fg='white').pack(side=tk.LEFT, padx=4)

        # ---- Results (text) ----
        self.analysis_text = tk.Text(container, height=10, bg='#f8f8f8', relief=tk.SUNKEN, bd=2, font=('Consolas', 10))
        self.analysis_text.pack(fill=tk.X, pady=6)

        # ---- Visuals ----
        viz = tk.LabelFrame(container, text="Visual Diagnostics", bg='#f5f5f5', padx=10, pady=10)
        viz.pack(fill=tk.BOTH, expand=True)

        # Four image slots: LSB plane, Heatmap, Hist, DiffAmp
        grid = tk.Frame(viz, bg='#f5f5f5'); grid.pack(fill=tk.BOTH, expand=True)

        self.viz_lsb_label = tk.Label(grid, bg='lightgrey', relief=tk.SUNKEN, bd=2, width=50, height=18)
        self.viz_heat_label = tk.Label(grid, bg='lightgrey', relief=tk.SUNKEN, bd=2, width=50, height=18)
        self.viz_hist_label = tk.Label(grid, bg='lightgrey', relief=tk.SUNKEN, bd=2, width=50, height=18)
        self.viz_diff_label = tk.Label(grid, bg='lightgrey', relief=tk.SUNKEN, bd=2, width=50, height=18)

        self.viz_lsb_label.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')
        self.viz_heat_label.grid(row=0, column=1, padx=5, pady=5, sticky='nsew')
        self.viz_hist_label.grid(row=1, column=0, padx=5, pady=5, sticky='nsew')
        self.viz_diff_label.grid(row=1, column=1, padx=5, pady=5, sticky='nsew')

        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)
        grid.grid_rowconfigure(0, weight=1)
        grid.grid_rowconfigure(1, weight=1)

    def browse_analysis_image(self):
        path = filedialog.askopenfilename(title="Select Image", filetypes=[("Image files", "*.png *.bmp *.jpg *.jpeg *.gif")])
        if path:
            self.analysis_image_path.set(path)

    def browse_analysis_cover_hint(self):
        path = filedialog.askopenfilename(title="Select Original Cover (optional)", filetypes=[("Image files", "*.png *.bmp *.jpg *.jpeg *.gif")])
        if path:
            self.analysis_cover_hint_path.set(path)

    def clear_analysis_ui(self):
        self.analysis_image_path.set("")
        self.analysis_cover_hint_path.set("")
        self.analysis_text.delete(1.0, tk.END)
        for lbl in (self.viz_lsb_label, self.viz_heat_label, self.viz_hist_label, self.viz_diff_label):
            lbl.configure(image='', text="")
            lbl.image = None

    def run_image_analysis(self):
        path = self.analysis_image_path.get().strip()
        if not path:
            messagebox.showerror("Error", "Select a suspected stego image first.")
            return

        try:
            img = Image.open(path).convert('RGB')
            arr = np.array(img, dtype=np.uint8)

            # Metrics
            chi_p = self._chi_square_lsb_pvalue(arr)
            corr = self._neighbor_correlation(arr)
            lsb_ratio = self._lsb_one_ratio(arr)
            heat = self._lsb_variance_heatmap(arr, block=8)  # 8x8 blocks

            # Visuals
            lsb_img = self._render_lsb_plane(arr)                   # grayscale LSB map
            hist_img = self._render_histograms(arr)                 # simple RGB hist
            heat_img = self._render_heatmap_image(heat, img.size)   # upscaled for display

            # Diff amplification (needs optional original)
            diff_img = None
            cover_hint = self.analysis_cover_hint_path.get().strip()
            if cover_hint and os.path.exists(cover_hint):
                diff_img = self._render_diff_amplified(Image.open(cover_hint).convert('RGB'), img, factor=16)

            # Put text report
            report = []
            report.append("Steganalysis Report\n-------------------")
            report.append(f"Image: {os.path.basename(path)}  |  {img.size[0]}×{img.size[1]}  |  RGB")
            report.append(f"Chi-square LSB p-value (higher ~ more random LSBs): {chi_p:.4f}")
            report.append(f"Neighbor correlation (0..1). Natural images ~0.90–0.99: {corr:.4f}")
            report.append(f"LSB(1-bit) ones ratio (should be near 0.5): {lsb_ratio:.4f}")
            report.append("Heatmap: bright regions = higher LSB variability (possible embedding zones)\n")
            self.analysis_text.delete(1.0, tk.END)
            self.analysis_text.insert(1.0, "\n".join(report))

            # Display images
            def _to_tk(im, max_wh=(450, 450)):
                imc = im.copy()
                imc.thumbnail(max_wh)
                tkimg = ImageTk.PhotoImage(imc)
                return tkimg

            lsb_tk = _to_tk(lsb_img); self.viz_lsb_label.configure(image=lsb_tk); self.viz_lsb_label.image = lsb_tk
            heat_tk = _to_tk(heat_img); self.viz_heat_label.configure(image=heat_tk); self.viz_heat_label.image = heat_tk
            hist_tk = _to_tk(hist_img); self.viz_hist_label.configure(image=hist_tk); self.viz_hist_label.image = hist_tk

            if diff_img is not None:
                diff_tk = _to_tk(diff_img)
                self.viz_diff_label.configure(image=diff_tk); self.viz_diff_label.image = diff_tk
            else:
                self.viz_diff_label.configure(image='', text="(Optional) Provide cover to see amplified difference")

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
        R, G, B = arr[:,:,0].astype(np.float32), arr[:,:,1].astype(np.float32), arr[:,:,2].astype(np.float32)
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
            return np.zeros((1,1), dtype=np.float32)
        heat = np.zeros((h_blocks, w_blocks), dtype=np.float32)
        for by in range(h_blocks):
            for bx in range(w_blocks):
                tile = lsb[by*block:(by+1)*block, bx*block:(bx+1)*block].ravel()
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
        img = Image.fromarray(lsb_sum.astype(np.uint8), mode='L').convert('RGB')
        return img

    def _render_heatmap_image(self, heat, size):
        """
        Upscale small heat array to image size with a simple grayscale colormap.
        """
        h_norm = (heat*255.0).clip(0,255).astype(np.uint8)
        hm = Image.fromarray(h_norm, mode='L').resize(size, Image.NEAREST).convert('RGB')
        return hm

    def _render_histograms(self, arr):
        """
        Quick RGB histogram render (256x100 per channel stacked).
        """
        H, W = 100, 256
        canvas = Image.new('RGB', (W, H*3), (240,240,240))
        for i, ch in enumerate([0,1,2]):
            hist = np.bincount(arr[:,:,ch].ravel(), minlength=256).astype(np.float32)
            if hist.max() > 0: hist /= hist.max()
            hist_h = (hist * (H-1)).astype(np.int32)
            layer = Image.new('RGB', (W, H), (255,255,255))
            px = layer.load()
            for x in range(256):
                h = hist_h[x]
                for y in range(H-1, H-1-h, -1):
                    # draw a vertical bar
                    px[x, y] = (50,50,50)
            canvas.paste(layer, (0, i*H))
        return canvas

    def _render_diff_amplified(self, cover_img, stego_img, factor=16):
        """
        |stego - cover| * factor, clipped, to reveal subtle embedding patterns.
        """
        if cover_img.size != stego_img.size:
            # fallback: resize cover to stego just for visualization
            cover_img = cover_img.resize(stego_img.size, Image.BILINEAR)
        c = np.array(cover_img, dtype=np.int16)
        s = np.array(stego_img, dtype=np.int16)
        d = np.clip(np.abs(s - c) * factor, 0, 255).astype(np.uint8)
        return Image.fromarray(d, mode='RGB')

    def setup_audio_analysis_tab(self, parent):
        container = tk.Frame(parent, bg='#f5f5f5')
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        picks = tk.LabelFrame(container, text="Select WAV(s) to Analyze", bg='#f5f5f5', padx=10, pady=10)
        picks.pack(fill=tk.X)

        self.an_audio_path = tk.StringVar()
        self.an_audio_cover_hint = tk.StringVar()
        self.an_audio_lsbs = tk.IntVar(value=1)  # assumed LSBs for analysis view (1–4 is common)

        r1 = tk.Frame(picks, bg='#f5f5f5'); r1.pack(fill=tk.X, pady=3)
        tk.Label(r1, text="Suspected Stego WAV:", bg='#f5f5f5').pack(side=tk.LEFT)
        tk.Entry(r1, textvariable=self.an_audio_path, state='readonly').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        tk.Button(r1, text="Browse", command=self._an_browse_audio, bg='#2196F3', fg='white').pack(side=tk.LEFT)

        r2 = tk.Frame(picks, bg='#f5f5f5'); r2.pack(fill=tk.X, pady=3)
        tk.Label(r2, text="(Optional) Original Cover WAV:", bg='#f5f5f5').pack(side=tk.LEFT)
        tk.Entry(r2, textvariable=self.an_audio_cover_hint, state='readonly').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        tk.Button(r2, text="Browse", command=self._an_browse_audio_cover, bg='#607D8B', fg='white').pack(side=tk.LEFT)

        r3 = tk.Frame(picks, bg='#f5f5f5'); r3.pack(fill=tk.X, pady=6)
        tk.Label(r3, text="Assumed LSBs for Analysis:", bg='#f5f5f5').pack(side=tk.LEFT)
        tk.Scale(r3, from_=1, to=8, orient=HORIZONTAL, variable=self.an_audio_lsbs, bg='#f5f5f5', length=200).pack(side=tk.LEFT, padx=10)

        actions = tk.Frame(container, bg='#f5f5f5'); actions.pack(fill=tk.X, pady=8)
        tk.Button(actions, text="🔎 Run Audio Analysis", command=self.run_audio_stego_analysis,
                bg='#4CAF50', fg='white', font=('Helvetica', 11, 'bold')).pack(side=tk.LEFT, padx=4)
        tk.Button(actions, text="💾 Save Report", command=self._an_save_report,
                bg='#3F51B5', fg='white').pack(side=tk.LEFT, padx=4)
        tk.Button(actions, text="📂 Load Report", command=self._an_load_report,
                bg='#009688', fg='white').pack(side=tk.LEFT, padx=4)
        tk.Button(actions, text="🗑️ Clear", command=self._an_clear_ui, bg='#FF9800', fg='white').pack(side=tk.LEFT, padx=4)

        self.an_audio_text = tk.Text(container, height=10, bg='#f8f8f8', relief=tk.SUNKEN, bd=2, font=('Consolas', 10))
        self.an_audio_text.pack(fill=tk.X, pady=6)

        viz = tk.LabelFrame(container, text="Visual Diagnostics", bg='#f5f5f5', padx=10, pady=10)
        viz.pack(fill=tk.BOTH, expand=True)
        grid = tk.Frame(viz, bg='#f5f5f5'); grid.pack(fill=tk.BOTH, expand=True)

        self.viz_wave = tk.Label(grid, bg='lightgrey', relief=tk.SUNKEN, bd=2, width=50, height=18)
        self.viz_spec = tk.Label(grid, bg='lightgrey', relief=tk.SUNKEN, bd=2, width=50, height=18)
        self.viz_lsbvar = tk.Label(grid, bg='lightgrey', relief=tk.SUNKEN, bd=2, width=50, height=18)
        self.viz_diffaudio = tk.Label(grid, bg='lightgrey', relief=tk.SUNKEN, bd=2, width=50, height=18)

        self.viz_wave.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')
        self.viz_spec.grid(row=0, column=1, padx=5, pady=5, sticky='nsew')
        self.viz_lsbvar.grid(row=1, column=0, padx=5, pady=5, sticky='nsew')
        self.viz_diffaudio.grid(row=1, column=1, padx=5, pady=5, sticky='nsew')

        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)
        grid.grid_rowconfigure(0, weight=1)
        grid.grid_rowconfigure(1, weight=1)

    def _an_browse_audio(self):
        path = filedialog.askopenfilename(title="Select WAV", filetypes=[("WAV files", "*.wav")])
        if path: self.an_audio_path.set(path)

    def _an_browse_audio_cover(self):
        path = filedialog.askopenfilename(title="Select Original Cover WAV", filetypes=[("WAV files", "*.wav")])
        if path: self.an_audio_cover_hint.set(path)

    def _an_clear_ui(self):
        self.an_audio_path.set("")
        self.an_audio_cover_hint.set("")
        self.an_audio_lsbs.set(1)
        self.an_audio_text.delete(1.0, tk.END)
        for lbl in (self.viz_wave, self.viz_spec, self.viz_lsbvar, self.viz_diffaudio):
            lbl.configure(image='', text="")
            lbl.image = None

    def run_audio_stego_analysis(self):
        path = self.an_audio_path.get().strip()
        if not path:
            messagebox.showerror("Error", "Select a WAV file to analyze.")
            return

        try:
            # Load samples
            params, samples = self._wav_read_any(path)  # (N,C)
            N, C = samples.shape
            lsbs = max(1, min(int(self.an_audio_lsbs.get()), 8))

            # Main metrics for chosen LSBs
            chi_p_overall, chi_p_ch = self._chi_square_lsb_audio(samples, lsbs)
            corr_overall, corr_ch = self._neighbor_corr_audio(samples)
            lsb_ratio_overall, lsb_ratio_ch = self._lsb_ratio_audio(samples, lsbs)
            lsb_var_series = self._lsb_block_variance_1d(samples, lsbs, block=2048)
            lsb_var_mean = float(lsb_var_series.mean()) if lsb_var_series.size else 0.0

            # Optional difference image
            diff_img = None
            cover_path = self.an_audio_cover_hint.get().strip()
            if cover_path and os.path.exists(cover_path):
                _, cover_samples = self._wav_read_any(cover_path)
                diff_img = self._render_audio_diff(cover_samples, samples)

            # Visuals
            wave_img = self._render_waveform(samples)
            spec_img = self._render_spectrogram(samples[:,0])
            lsbvar_img = self._render_lsb_var_bar(lsb_var_series)

            # -------- Auto-detect 1..4 LSBs --------
            autodet = []
            for d in range(1, min(lsbs, 8) + 1):
                chi_p_o, _ = self._chi_square_lsb_audio(samples, d)
                _, corr_ch_tmp = self._neighbor_corr_audio(samples)
                corr_o = float(np.mean(corr_ch_tmp)) if corr_ch_tmp else 0.0
                lsb_ratio_o, _ = self._lsb_ratio_audio(samples, d)
                series = self._lsb_block_variance_1d(samples, d, block=2048)
                var_mean = float(series.mean()) if series.size else 0.0
                score = self._score_stegoish(chi_p_o, corr_o, lsb_ratio_o, var_mean)
                autodet.append({
                    "lsbs": d,
                    "chi_p": float(chi_p_o),
                    "corr": float(corr_o),
                    "lsb_ratio": float(lsb_ratio_o),
                    "lsb_var_mean": float(var_mean),
                    "score": float(score),
                })
            best = max(autodet, key=lambda z: z["score"]) if autodet else None

            # Report text
            sr = params.framerate
            dur = N / float(sr) if sr else 0.0
            rep = []
            rep.append("Audio Steganalysis Report")
            rep.append("--------------------------")
            rep.append(f"File: {os.path.basename(path)}  |  {sr} Hz, {params.nchannels} ch, {8*params.sampwidth}-bit, {dur:.2f}s")
            rep.append(f"Assumed analysis LSBs: {lsbs}")
            rep.append("")
            rep.append(f"Chi-square LSB p-value (overall): {chi_p_overall:.4f}")
            for c in range(C): rep.append(f"  - ch{c+1}: {chi_p_ch[c]:.4f}")
            rep.append(f"Neighbor correlation (overall): {corr_overall:.4f}")
            for c in range(C): rep.append(f"  - ch{c+1}: {corr_ch[c]:.4f}")
            rep.append(f"LSB ones-ratio (overall): {lsb_ratio_overall:.4f}")
            for c in range(C): rep.append(f"  - ch{c+1}: {lsb_ratio_ch[c]:{'.4f'}}")
            rep.append(f"Mean LSB variance (blocks): {lsb_var_mean:.4f}")
            rep.append("")
            rep.append("Auto-detect (scan LSB=1..4): higher score = more 'stego-ish'")
            for row in autodet:
                rep.append(f"  LSBs={row['lsbs']}: score={row['score']:.3f} | chi_p={row['chi_p']:.4f} corr={row['corr']:.4f} lsb_ratio={row['lsb_ratio']:.4f} var={row['lsb_var_mean']:.4f}")
            if best:
                rep.append(f"→ Likely LSB depth: {best['lsbs']} (score {best['score']:.3f})")
            rep.append("\nLSB variance over time blocks: brighter = more variability (possible embedding zones)")
            self.an_audio_text.delete(1.0, tk.END)
            self.an_audio_text.insert(1.0, "\n".join(rep))

            # Display images
            def _to_tk(im, max_wh=(450, 450)):
                imc = im.copy(); imc.thumbnail(max_wh)
                return ImageTk.PhotoImage(imc)

            wtk = _to_tk(wave_img); self.viz_wave.configure(image=wtk); self.viz_wave.image = wtk
            stk = _to_tk(spec_img); self.viz_spec.configure(image=stk); self.viz_spec.image = stk
            vtk = _to_tk(lsbvar_img); self.viz_lsbvar.configure(image=vtk); self.viz_lsbvar.image = vtk

            if diff_img is not None:
                dtk = _to_tk(diff_img); self.viz_diffaudio.configure(image=dtk); self.viz_diffaudio.image = dtk
            else:
                self.viz_diffaudio.configure(image='', text="(Optional) Provide cover WAV to see difference spikes")

            # -------- persist a JSON-ready report for Save --------
            self._last_audio_report = {
                "file": path,
                "cover_hint": cover_path if cover_path else None,
                "samplerate": int(sr),
                "channels": int(params.nchannels),
                "bitdepth": int(8*params.sampwidth),
                "duration_sec": float(dur),
                "assumed_lsbs": int(lsbs),
                "metrics": {
                    "chi_p_overall": float(chi_p_overall),
                    "chi_p_per_channel": [float(v) for v in chi_p_ch],
                    "corr_overall": float(corr_overall),
                    "corr_per_channel": [float(v) for v in corr_ch],
                    "lsb_ratio_overall": float(lsb_ratio_overall),
                    "lsb_ratio_per_channel": [float(v) for v in lsb_ratio_ch],
                    "lsb_var_mean": float(lsb_var_mean),
                },
                "autodetect_scan_1to4": autodet,
                "autodetect_best": best,
            }

        except Exception as e:
            messagebox.showerror("Analysis Error", str(e))


    def _wav_read_any(self, path):
        with wave.open(path, 'rb') as w:
            params = w.getparams()
            frames = w.readframes(params.nframes)

        # dtype by sampwidth
        sw = params.sampwidth
        if sw == 1:
            arr = np.frombuffer(frames, dtype=np.uint8).astype(np.uint16)  # 0..255
        elif sw == 2:
            arr = np.frombuffer(frames, dtype=np.int16).astype(np.int32)
        elif sw == 3:
            raw = np.frombuffer(frames, dtype=np.uint8).reshape(-1, 3)
            vals = (raw[:,0].astype(np.uint32) |
                    (raw[:,1].astype(np.uint32) << 8) |
                    (raw[:,2].astype(np.uint32) << 16))
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

    def _chi_square_lsb_audio(self, samples, num_lsbs):
        """
        Chi-square across all channels for the chosen LSB depth.
        Returns (overall_p_value, [per_channel_p_values]).
        """
        import math
        mask = (1 << num_lsbs) - 1

        # Overall test using only the least-significant bit
        lsb = ((samples & mask) & 1).ravel()
        n = lsb.size
        ones = int(np.count_nonzero(lsb))
        zeros = n - ones
        expected = n / 2.0
        chi = ((zeros - expected) ** 2) / expected + ((ones - expected) ** 2) / expected
        p_overall = 1.0 if chi <= 1e-12 else math.exp(-chi / 2.0)  # approx tail for df=1

        # Per-channel
        p_ch = []
        C = samples.shape[1]
        for c in range(C):
            ch = ((samples[:, c] & mask) & 1)
            n_c = ch.size
            ones_c = int(np.count_nonzero(ch))
            zeros_c = n_c - ones_c
            expected_c = n_c / 2.0
            chi_c = ((zeros_c - expected_c) ** 2) / expected_c + ((ones_c - expected_c) ** 2) / expected_c
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
                corr_ch.append(0.0); continue
            xm, ym = x.mean(), y.mean()
            num = np.sum((x-xm)*(y-ym))
            den = np.sqrt(np.sum((x-xm)**2) * np.sum((y-ym)**2))
            corr_ch.append(float(num/den) if den != 0 else 0.0)
        # overall = mean of channels
        overall = float(np.mean(corr_ch)) if corr_ch else 0.0
        return overall, corr_ch

    def _lsb_ratio_audio(self, samples, num_lsbs):
        mask = (1 << num_lsbs) - 1
        lsb = (samples & mask) & 1
        overall = float(np.count_nonzero(lsb)) / max(lsb.size, 1)
        ch = []
        for c in range(samples.shape[1]):
            arr = lsb[:,c]
            ch.append(float(np.count_nonzero(arr)) / max(arr.size, 1))
        return overall, ch

    def _lsb_block_variance_1d(self, samples, num_lsbs, block=2048):
        """
        Compute variance of LSB (1-bit of assumed num_lsbs) per time block (across channels).
        Returns a 1D array of length ~N/block, normalized 0..1.
        """
        mask = (1 << num_lsbs) - 1
        lsb = ((samples & mask) & 1).astype(np.float32)
        # average across channels to 1D
        if lsb.ndim == 2 and lsb.shape[1] > 1:
            lsb = lsb.mean(axis=1)
        N = lsb.shape[0]
        if N < block:
            v = np.array([lsb.var()], dtype=np.float32)
        else:
            nblk = N // block
            v = np.zeros(nblk, dtype=np.float32)
            for i in range(nblk):
                seg = lsb[i*block:(i+1)*block]
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
        ch = samples[:,0].astype(np.float32)
        if ch.size > w:
            # downsample by picking evenly spaced points
            idx = np.linspace(0, ch.size-1, w).astype(int)
            ch = ch[idx]
        else:
            # pad to width
            pad = w - ch.size
            if pad > 0: ch = np.pad(ch, (0,pad), mode='edge')

        # normalize to -1..1
        m = max(np.max(np.abs(ch)), 1e-9)
        y = (ch / m) * 0.9  # leave margin
        img = Image.new('RGB', (w, h), (240,240,240))
        px = img.load()
        mid = h//2
        # draw axis
        for x in range(w):
            px[x, mid] = (180,180,180)
        # draw waveform
        for x in range(w):
            ypix = int(mid - y[x]* (h//2 - 5))
            # vertical line from mid to ypix
            y0, y1 = sorted((mid, ypix))
            for yy in range(y0, y1+1):
                px[x, yy] = (30,30,30)
        return img

    def _render_spectrogram(self, mono, win=1024, hop=512):
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
            return Image.new('RGB', (4,4), (240,240,240))
        S = np.stack(frames, axis=1)  # (freq_bins, time)
        S = S + 1e-8
        S = 20.0 * np.log10(S)  # dB
        # normalize to 0..255
        S = (S - S.min()) / max(S.max()-S.min(), 1e-6)
        S = (S*255.0).astype(np.uint8)
        # flip freq so low at bottom
        S = np.flipud(S)
        return Image.fromarray(S, mode='L').convert('RGB')

    def _render_lsb_var_bar(self, var_series, height=120):
        """
        Render 1D variance series as a bar image (grayscale): bright = high variance.
        """
        if var_series.size == 0:
            return Image.new('RGB', (4, height), (240,240,240))
        w = int(max(64, var_series.size))
        # stretch to width
        xs = np.linspace(0, var_series.size-1, w).astype(int)
        v = var_series[xs]
        vimg = (v*255.0).clip(0,255).astype(np.uint8)
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
        c0 = cover[:,0].astype(np.int64)
        s0 = stego[:,0].astype(np.int64)
        m = min(c0.size, s0.size)
        if m == 0:
            return Image.new('RGB', (4,4), (240,240,240))
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
            if pad > 0: d = np.pad(d, (0,pad), mode='edge')
        img = Image.new('RGB', (w, h), (240,240,240))
        px = img.load()
        for x in range(w):
            bh = int(d[x] * (h-10))
            for y in range(h-1, h-1-bh, -1):
                px[x, y] = (30,30,30)
        return img
    def _score_stegoish(self, chi_p, corr, lsb_ratio, lsb_var_mean):
        """
        Lower chi_p (more random LSBs), lower corr (more noise),
        lsb_ratio close to 0.5, higher LSB variance => more 'stego-ish'.
        Returns a higher-better score in ~[0..1].
        """
        # map each metric to 0..1 (higher worse/nastier)
        s_chi  = 1.0 - float(chi_p)              # 0 (clean) .. 1 (very random)
        s_corr = float(max(0.0, min(1.0, 1.0 - corr)))  # lower corr -> higher score
        s_lsb  = 1.0 - min(1.0, abs(lsb_ratio - 0.5) * 4.0)  # peak at 0.5
        s_var  = float(max(0.0, min(1.0, lsb_var_mean)))     # already 0..1

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
            messagebox.showerror("Save Error", f"Failed to save text report:\n{e}")
            return

        # Save JSON (if we have it)
        try:
            import json, os
            data = getattr(self, "_last_audio_report", None)
            if data is not None:
                json_path = os.path.splitext(base)[0] + ".json"
                with open(json_path, "w", encoding="utf-8") as jf:
                    json.dump(data, jf, indent=2)
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save JSON report:\n{e}")
            return

        messagebox.showinfo("Saved", "Report saved (text and JSON, if available).")

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
                lines.append(f"File: {os.path.basename(data.get('file',''))}")
                lines.append(f"Samplerate: {data.get('samplerate','?')} Hz  |  Channels: {data.get('channels','?')}  |  Bitdepth: {data.get('bitdepth','?')}")
                lines.append(f"Duration: {data.get('duration_sec',0):.2f}s")
                lines.append(f"Assumed analysis LSBs: {data.get('assumed_lsbs','?')}")
                lines.append("")
                m = data.get("metrics", {})
                lines.append(f"Chi-square LSB p-value (overall): {m.get('chi_p_overall','?')}")
                co = m.get("corr_overall","?")
                lines.append(f"Neighbor correlation (overall): {co}")
                lines.append(f"LSB ones-ratio (overall): {m.get('lsb_ratio_overall','?')}")
                lines.append(f"Mean LSB variance (blocks): {m.get('lsb_var_mean','?')}")
                lines.append("")
                lines.append("Auto-detect (scan LSB=1..4):")
                for r in data.get("autodetect_scan_1to4", []):
                    lines.append(f"  LSBs={r['lsbs']}: score={r['score']:.3f} | chi_p={r['chi_p']:.4f} corr={r['corr']:.4f} lsb_ratio={r['lsb_ratio']:.4f} var={r['lsb_var_mean']:.4f}")
                best = data.get("autodetect_best")
                if best:
                    lines.append(f"→ Likely LSB depth: {best['lsbs']} (score {best['score']:.3f})")

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
        diff_path = os.path.join(os.path.dirname(cover_path), "difference_map.png")
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
