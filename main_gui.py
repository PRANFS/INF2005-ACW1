import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from tkinter import Scale, HORIZONTAL
import tkinterdnd2 as TkinterDnD
from PIL import Image, ImageTk
import os
import random
import platform
import subprocess
import wave
import numpy as np
from bitarray import bitarray
import wave, numpy as np, os, random


class DropZone(tk.Frame):
    def __init__(self, parent, text, callback, file_types=None):
        super().__init__(parent, bg='#e8f4fd', relief=tk.RAISED, bd=2, height=80)
        self.callback = callback
        self.file_types = file_types or []
        self.default_text = text
        self.default_bg = '#e8f4fd'
        self.hover_bg = '#d0e7f7'
        self.drop_bg = '#b8ddf0'
        
        self.label = tk.Label(self, text=text, bg=self.default_bg, 
                             font=('Helvetica', 10), wraplength=300)
        self.label.pack(expand=True, fill=tk.BOTH)
        
        self.drop_target_register(TkinterDnD.DND_FILES)
        self.dnd_bind('<<DropEnter>>', self.on_drop_enter)
        self.dnd_bind('<<DropLeave>>', self.on_drop_leave)
        self.dnd_bind('<<Drop>>', self.on_drop)
    
    def on_drop_enter(self, event):
        self.configure(bg=self.hover_bg)
        self.label.configure(bg=self.hover_bg)
    
    def on_drop_leave(self, event):
        self.configure(bg=self.default_bg)
        self.label.configure(bg=self.default_bg)
    
    def on_drop(self, event):
        file_path = event.data.strip('{}')
        if self.file_types:
            if not any(file_path.lower().endswith(ft) for ft in self.file_types):
                messagebox.showerror("Error", f"Invalid file type. Expected: {', '.join(self.file_types)}")
                return
        self.callback(file_path)
        self.configure(bg=self.drop_bg)
        self.label.configure(bg=self.drop_bg)
    
    def update_text(self, text):
        self.label.configure(text=text)
    
    def reset_colors(self):
        self.configure(bg=self.default_bg)
        self.label.configure(bg=self.default_bg)


class StegApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("LSB Steganography Tool - Enhanced GUI with Audio Support")
        self.geometry("1200x900")
        self.configure(bg='#f5f5f5')

        # --- Variables ---
        self.cover_path = tk.StringVar()
        self.payload_path = tk.StringVar()
        self.stego_path = tk.StringVar()
        self.secret_key = tk.StringVar()
        self.num_lsbs = tk.IntVar(value=1)
        
        # Audio-specific variables
        self.audio_cover_path = tk.StringVar()
        self.audio_payload_path = tk.StringVar()
        self.audio_secret_key = tk.StringVar()
        self.audio_num_lsbs = tk.IntVar(value=1)

        self.setup_ui()

    def setup_ui(self):
        # --- Main Notebook for Tabs ---
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Image Encoding Tab
        encode_frame = ttk.Frame(notebook)
        notebook.add(encode_frame, text="Image Encode")
        
        # Image Decoding Tab
        decode_frame = ttk.Frame(notebook)
        notebook.add(decode_frame, text="Image Decode")
        
        # Audio Encoding Tab
        audio_encode_frame = ttk.Frame(notebook)
        notebook.add(audio_encode_frame, text="Audio Encode")
        
        # Audio Decoding Tab
        audio_decode_frame = ttk.Frame(notebook)
        notebook.add(audio_decode_frame, text="Audio Decode")
        
        self.setup_encode_tab(encode_frame)
        self.setup_decode_tab(decode_frame)
        self.setup_audio_encode_tab(audio_encode_frame)
        self.setup_audio_decode_tab(audio_decode_frame)

    def setup_encode_tab(self, parent):
        # --- File Selection Section ---
        file_frame = tk.LabelFrame(parent, text="File Selection", font=('Helvetica', 10, 'bold'), 
                                  bg='#f5f5f5', padx=10, pady=10)
        file_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Cover Image Section
        cover_section = tk.Frame(file_frame, bg='#f5f5f5')
        cover_section.pack(fill=tk.X, pady=5)
        
        tk.Label(cover_section, text="Cover Image:", font=('Helvetica', 10, 'bold'), 
                bg='#f5f5f5').pack(anchor=tk.W)
        
        cover_input_frame = tk.Frame(cover_section, bg='#f5f5f5')
        cover_input_frame.pack(fill=tk.X, pady=2)
        
        self.cover_entry = tk.Entry(cover_input_frame, textvariable=self.cover_path, 
                                   font=('Helvetica', 10), state='readonly')
        self.cover_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        tk.Button(cover_input_frame, text="Browse", command=self.browse_cover,
                 bg='#4CAF50', fg='white', font=('Helvetica', 9, 'bold')).pack(side=tk.RIGHT)
        
        # Cover Image Drop Zone
        self.cover_drop_zone = DropZone(cover_section, 
                                       "Drag & Drop Cover Image Here\n(PNG, BMP, JPG)",
                                       callback=self.set_cover_image,
                                       file_types=['.png', '.bmp', '.jpg', '.jpeg'])
        self.cover_drop_zone.pack(fill=tk.X, pady=5)
        
        # Payload Section
        payload_section = tk.Frame(file_frame, bg='#f5f5f5')
        payload_section.pack(fill=tk.X, pady=10)
        
        tk.Label(payload_section, text="Payload File:", font=('Helvetica', 10, 'bold'), 
                bg='#f5f5f5').pack(anchor=tk.W)
        
        payload_input_frame = tk.Frame(payload_section, bg='#f5f5f5')
        payload_input_frame.pack(fill=tk.X, pady=2)
        
        self.payload_entry = tk.Entry(payload_input_frame, textvariable=self.payload_path, 
                                     font=('Helvetica', 10), state='readonly')
        self.payload_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        tk.Button(payload_input_frame, text="Browse", command=self.browse_payload,
                 bg='#2196F3', fg='white', font=('Helvetica', 9, 'bold')).pack(side=tk.RIGHT)
        
        # Payload Drop Zone
        self.payload_drop_zone = DropZone(payload_section,
                                         "Drag & Drop Payload File Here\n(Any file type)",
                                         callback=self.set_payload_file)
        self.payload_drop_zone.pack(fill=tk.X, pady=5)
        
        # --- Configuration Section ---
        config_frame = tk.LabelFrame(parent, text="Configuration", 
                                    font=('Helvetica', 10, 'bold'), bg='#f5f5f5', 
                                    padx=10, pady=10)
        config_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Secret Key
        key_frame = tk.Frame(config_frame, bg='#f5f5f5')
        key_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(key_frame, text="Secret Key (Numeric):", 
                font=('Helvetica', 10, 'bold'), bg='#f5f5f5').pack(side=tk.LEFT)
        tk.Entry(key_frame, textvariable=self.secret_key, width=20, show="*",
                font=('Helvetica', 10)).pack(side=tk.LEFT, padx=10)
        
        # LSB Configuration
        lsb_frame = tk.Frame(config_frame, bg='#f5f5f5')
        lsb_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(lsb_frame, text="Number of LSBs:", 
                font=('Helvetica', 10, 'bold'), bg='#f5f5f5').pack(side=tk.LEFT)
        
        lsb_slider = Scale(lsb_frame, from_=1, to=8, orient=HORIZONTAL, 
                          variable=self.num_lsbs, command=self.update_capacity_display,
                          bg='#f5f5f5', font=('Helvetica', 9))
        lsb_slider.pack(side=tk.LEFT, padx=10)
        
        self.capacity_label = tk.Label(lsb_frame, text="Capacity: N/A", 
                                      font=('Helvetica', 10, 'italic'), bg='#f5f5f5')
        self.capacity_label.pack(side=tk.LEFT, padx=20)
        
        # --- Action Buttons ---
        button_frame = tk.Frame(parent, bg='#f5f5f5')
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(button_frame, text="🔒 Encode Payload", bg="#4CAF50", fg="white", 
                 font=("Helvetica", 12, "bold"), command=self.run_encode,
                 height=2, width=20).pack(side=tk.LEFT, padx=10)
        
        tk.Button(button_frame, text="🗑️ Clear All", bg="#FF9800", fg="white", 
                 font=("Helvetica", 12, "bold"), command=self.clear_all,
                 height=2, width=15).pack(side=tk.LEFT, padx=10)
        
        # --- Image Display Area ---
        display_frame = tk.LabelFrame(parent, text="Image Display", 
                                     font=('Helvetica', 10, 'bold'), bg='#f5f5f5')
        display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Cover image canvas
        canvas_frame = tk.Frame(display_frame, bg='#f5f5f5')
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        tk.Label(canvas_frame, text="Cover Image", font=('Helvetica', 10, 'bold'), 
                bg='#f5f5f5').pack()
        
        self.cover_canvas = tk.Canvas(canvas_frame, bg="lightgrey", relief=tk.SUNKEN, bd=2)
        self.cover_canvas.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Stego image display
        stego_frame = tk.Frame(display_frame, bg='#f5f5f5')
        stego_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        tk.Label(stego_frame, text="Stego Object / Difference Map", 
                font=('Helvetica', 10, 'bold'), bg='#f5f5f5').pack()
        
        self.stego_display = tk.Label(stego_frame, bg="lightgrey", relief=tk.SUNKEN, bd=2)
        self.stego_display.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.setup_canvas_bindings()

    def setup_decode_tab(self, parent):
        # Decode interface
        decode_frame = tk.LabelFrame(parent, text="Decode Steganographic Image", 
                                    font=('Helvetica', 12, 'bold'), bg='#f5f5f5', 
                                    padx=20, pady=20)
        decode_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Instructions
        instructions = tk.Label(decode_frame, 
                               text="Select a steganographic image to extract the hidden payload.\n" +
                                    "You'll need the same secret key and LSB settings used during encoding.",
                               font=('Helvetica', 10), bg='#f5f5f5', wraplength=500, justify=tk.CENTER)
        instructions.pack(pady=20)
        
        # Decode button
        decode_button = tk.Button(decode_frame, text="🔓 Select Stego Image & Decode", 
                                 bg="#2196F3", fg="white", font=("Helvetica", 14, "bold"), 
                                 command=self.run_decode, height=3, width=30)
        decode_button.pack(pady=20)
        
        # Result display
        self.decode_result = tk.Text(decode_frame, height=10, width=60, 
                                    font=('Consolas', 10), bg='#f8f8f8', 
                                    relief=tk.SUNKEN, bd=2)
        self.decode_result.pack(fill=tk.BOTH, expand=True, pady=10)

    def setup_audio_encode_tab(self, parent):
        # --- File Selection Section ---
        file_frame = tk.LabelFrame(parent, text="Audio File Selection", font=('Helvetica', 10, 'bold'), 
                                  bg='#f5f5f5', padx=10, pady=10)
        file_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Cover Audio Section
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
        
        # Audio Cover Drop Zone
        self.audio_cover_drop_zone = DropZone(cover_section, 
                                             "Drag & Drop Cover Audio File Here\n(WAV format)",
                                             callback=self.set_audio_cover,
                                             file_types=['.wav'])
        self.audio_cover_drop_zone.pack(fill=tk.X, pady=5)
        
        # Payload Section
        payload_section = tk.Frame(file_frame, bg='#f5f5f5')
        payload_section.pack(fill=tk.X, pady=10)
        
        tk.Label(payload_section, text="Payload File:", font=('Helvetica', 10, 'bold'), 
                bg='#f5f5f5').pack(anchor=tk.W)
        
        payload_input_frame = tk.Frame(payload_section, bg='#f5f5f5')
        payload_input_frame.pack(fill=tk.X, pady=2)
        
        self.audio_payload_entry = tk.Entry(payload_input_frame, textvariable=self.audio_payload_path, 
                                           font=('Helvetica', 10), state='readonly')
        self.audio_payload_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        tk.Button(payload_input_frame, text="Browse", command=self.browse_audio_payload,
                 bg='#2196F3', fg='white', font=('Helvetica', 9, 'bold')).pack(side=tk.RIGHT)
        
        # Payload Drop Zone
        self.audio_payload_drop_zone = DropZone(payload_section,
                                               "Drag & Drop Payload File Here\n(Any file type)",
                                               callback=self.set_audio_payload)
        self.audio_payload_drop_zone.pack(fill=tk.X, pady=5)
        
        # --- Configuration Section ---
        config_frame = tk.LabelFrame(parent, text="Audio Configuration", 
                                    font=('Helvetica', 10, 'bold'), bg='#f5f5f5', 
                                    padx=10, pady=10)
        config_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Secret Key
        key_frame = tk.Frame(config_frame, bg='#f5f5f5')
        key_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(key_frame, text="Secret Key (Numeric):", 
                font=('Helvetica', 10, 'bold'), bg='#f5f5f5').pack(side=tk.LEFT)
        tk.Entry(key_frame, textvariable=self.audio_secret_key, width=20, show="*",
                font=('Helvetica', 10)).pack(side=tk.LEFT, padx=10)
        
        # LSB Configuration
        lsb_frame = tk.Frame(config_frame, bg='#f5f5f5')
        lsb_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(lsb_frame, text="Number of LSBs:", 
                font=('Helvetica', 10, 'bold'), bg='#f5f5f5').pack(side=tk.LEFT)
        
        audio_lsb_slider = Scale(lsb_frame, from_=1, to=8, orient=HORIZONTAL, 
                                variable=self.audio_num_lsbs, command=self.update_audio_capacity_display,
                                bg='#f5f5f5', font=('Helvetica', 9))
        audio_lsb_slider.pack(side=tk.LEFT, padx=10)
        
        self.audio_capacity_label = tk.Label(lsb_frame, text="Capacity: N/A", 
                                           font=('Helvetica', 10, 'italic'), bg='#f5f5f5')
        self.audio_capacity_label.pack(side=tk.LEFT, padx=20)
        
        # --- Audio Info Display ---
        info_frame = tk.LabelFrame(parent, text="Audio Information", 
                                  font=('Helvetica', 10, 'bold'), bg='#f5f5f5', 
                                  padx=10, pady=10)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.audio_info_label = tk.Label(info_frame, text="Select an audio file to view information", 
                                        font=('Helvetica', 10), bg='#f5f5f5')
        self.audio_info_label.pack(pady=5)
        
        # --- Action Buttons ---
        button_frame = tk.Frame(parent, bg='#f5f5f5')
        button_frame.pack(fill=tk.X, padx=10, pady=20)
        
        tk.Button(button_frame, text="🎵 Encode Audio Payload", bg="#4CAF50", fg="white", 
                 font=("Helvetica", 12, "bold"), command=self.run_audio_encode,
                 height=2, width=25).pack(side=tk.LEFT, padx=10)
        
        tk.Button(button_frame, text="🗑️ Clear All", bg="#FF9800", fg="white", 
                 font=("Helvetica", 12, "bold"), command=self.clear_audio_all,
                 height=2, width=15).pack(side=tk.LEFT, padx=10)

    def setup_audio_decode_tab(self, parent):
        # Decode interface
        decode_frame = tk.LabelFrame(parent, text="Decode Steganographic Audio", 
                                    font=('Helvetica', 12, 'bold'), bg='#f5f5f5', 
                                    padx=20, pady=20)
        decode_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Instructions
        instructions = tk.Label(decode_frame, 
                               text="Select a steganographic WAV file to extract the hidden payload.\n" +
                                    "You'll need the same secret key and LSB settings used during encoding.",
                               font=('Helvetica', 10), bg='#f5f5f5', wraplength=500, justify=tk.CENTER)
        instructions.pack(pady=20)
        
        # Decode button
        decode_button = tk.Button(decode_frame, text="🎵 Select Stego Audio & Decode", 
                                 bg="#2196F3", fg="white", font=("Helvetica", 14, "bold"), 
                                 command=self.run_audio_decode, height=3, width=30)
        decode_button.pack(pady=20)
        
        # Result display
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

    # --- Audio Callback Methods ---
    def set_audio_cover(self, file_path):
        self.audio_cover_path.set(file_path)
        self.audio_cover_drop_zone.update_text(f"✓ {os.path.basename(file_path)}")
        self.display_audio_info(file_path)
        self.update_audio_capacity_display()

    def set_audio_payload(self, file_path):
        self.audio_payload_path.set(file_path)
        self.audio_payload_drop_zone.update_text(f"✓ {os.path.basename(file_path)}")

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

    def update_audio_capacity_display(self, *args):
        audio_path = self.audio_cover_path.get()
        if not audio_path or not os.path.exists(audio_path):
            self.audio_capacity_label.config(text="Capacity: Select an audio file")
            return
        try:
            capacity_bytes = self._calculate_audio_capacity(audio_path, self.audio_num_lsbs.get())
            capacity_kb = capacity_bytes / 1024
            self.audio_capacity_label.config(text=f"Capacity: {capacity_kb:.2f} KB")
        except Exception:
            self.audio_capacity_label.config(text="Capacity: Error")

    # --- Audio Action Methods ---
    def run_audio_encode(self):
        cover = self.audio_cover_path.get()
        payload = self.audio_payload_path.get()
        key = self.audio_secret_key.get()
        
        if not all([cover, payload, key]):
            messagebox.showerror("Error", "Please provide Cover Audio File, Payload File, and a Secret Key.")
            return
        
        if not key.isdigit():
            messagebox.showerror("Error", "The secret key must be numeric.")
            return
        
        try:
            stego_path = self._encode_audio(cover, payload, int(key), self.audio_num_lsbs.get())
            messagebox.showinfo("Success", f"✅ Payload embedded successfully!\n🎵 Stego-audio saved as:\n{stego_path}")
                
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
            
        key = simpledialog.askstring("Input", "Enter the Secret Key:", show='*')
        if not key or not key.isdigit():
            messagebox.showerror("Error", "A valid numeric key is required for decoding.")
            return
            
        try:
            extracted_path = self._decode_audio(stego_path, int(key), self.audio_num_lsbs.get())
            
            # Update decode result display
            result_text = f"✅ Payload extracted successfully!\n\n"
            result_text += f"📁 Extracted file: {extracted_path}\n"
            result_text += f"📊 File size: {os.path.getsize(extracted_path)} bytes\n"
            result_text += f"🔑 Key used: {key}\n"
            result_text += f"⚙️ LSBs used: {self.audio_num_lsbs.get()}\n"
            
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
        self.audio_capacity_label.config(text="Capacity: N/A")
        self.audio_info_label.config(text="Select an audio file to view information")
        
        # Reset drop zones
        self.audio_cover_drop_zone.update_text("Drag & Drop Cover Audio File Here\n(WAV format)")
        self.audio_payload_drop_zone.update_text("Drag & Drop Payload File Here\n(Any file type)")
        self.audio_cover_drop_zone.reset_colors()
        self.audio_payload_drop_zone.reset_colors()

    # --- Original Image Methods (unchanged) ---
    def set_cover_image(self, file_path):
        self.cover_path.set(file_path)
        self.cover_drop_zone.update_text(f"✓ {os.path.basename(file_path)}")
        self.display_image(file_path)
        self.update_capacity_display()

    def set_payload_file(self, file_path):
        self.payload_path.set(file_path)
        self.payload_drop_zone.update_text(f"✓ {os.path.basename(file_path)}")

    def explorer_file_selected(self, file_path):
        # Determine if it's an image or other file
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            self.set_cover_image(file_path)
        else:
            self.set_payload_file(file_path)

    # --- Original Methods (Updated) ---
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
            img.thumbnail((450, 450))
            self.tk_img = ImageTk.PhotoImage(img)
            self.cover_canvas.delete("all")
            self.cover_image_on_canvas = self.cover_canvas.create_image(
                0, 0, anchor="nw", image=self.tk_img)
            self.original_display_size = img.size
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

    def update_capacity_display(self, *args):
        cover_path = self.cover_path.get()
        if not cover_path or not os.path.exists(cover_path):
            self.capacity_label.config(text="Capacity: Select a cover image")
            return
        try:
            region = self.get_embed_region_in_original()
            capacity_bytes = self._calculate_capacity(cover_path, self.num_lsbs.get(), region)
            capacity_kb = capacity_bytes / 1024
            self.capacity_label.config(text=f"Capacity: {capacity_kb:.2f} KB")
        except Exception:
            self.capacity_label.config(text="Capacity: Error")

    def run_encode(self):
        cover = self.cover_path.get()
        payload = self.payload_path.get()
        key = self.secret_key.get()
        
        if not all([cover, payload, key]):
            messagebox.showerror("Error", "Please provide Cover Image, Payload File, and a Secret Key.")
            return
        
        if not key.isdigit():
            messagebox.showerror("Error", "The secret key must be numeric.")
            return
        
        try:
            stego_path = self._encode_image(cover, payload, int(key), self.num_lsbs.get())
            messagebox.showinfo("Success", f"✅ Payload embedded successfully!\n📁 Stego-image saved as:\n{stego_path}")
            
            # Display the stego image
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
            img.thumbnail((450, 450))
            stego_img = ImageTk.PhotoImage(img)
            self.stego_display.configure(image=stego_img, text="")
            self.stego_display.image = stego_img  # Keep a reference
        except Exception as e:
            messagebox.showerror("Error", f"Failed to display stego image: {e}")

    def run_decode(self):
        stego_path = filedialog.askopenfilename(
            title="Select Stego-Image", 
            filetypes=[("Image files", "*.png *.bmp *.jpg *.jpeg *.gif")]
        )
        if not stego_path:
            return
            
        key = simpledialog.askstring("Input", "Enter the Secret Key:", show='*')
        if not key or not key.isdigit():
            messagebox.showerror("Error", "A valid numeric key is required for decoding.")
            return
            
        try:
            extracted_path = self._decode_image(stego_path, int(key), self.num_lsbs.get())
            
            # Update decode result display
            result_text = f"✅ Payload extracted successfully!\n\n"
            result_text += f"📁 Extracted file: {extracted_path}\n"
            result_text += f"📊 File size: {os.path.getsize(extracted_path)} bytes\n"
            result_text += f"🔑 Key used: {key}\n"
            result_text += f"⚙️ LSBs used: {self.num_lsbs.get()}\n"
            
            self.decode_result.delete(1.0, tk.END)
            self.decode_result.insert(1.0, result_text)
            
            if messagebox.askyesno("Success", f"✅ Payload extracted!\n📁 Saved as: {os.path.basename(extracted_path)}\n\n🔍 Open now?"):
                self.open_file(extracted_path)
                
        except Exception as e:
            error_text = f"❌ Failed to decode: {e}\n\n"
            error_text += "Please check:\n"
            error_text += "• Correct secret key\n"
            error_text += "• Same LSB settings as encoding\n"
            error_text += "• Valid stego image\n"
            
            self.decode_result.delete(1.0, tk.END)
            self.decode_result.insert(1.0, error_text)
            messagebox.showerror("Decoding Error", f"Failed to decode: {e}")

    def clear_all(self):
        self.cover_path.set("")
        self.payload_path.set("")
        self.secret_key.set("")
        self.num_lsbs.set(1)
        self.cover_canvas.delete("all")
        self.stego_display.config(image='', text="Stego-Object / Difference Map")
        self.capacity_label.config(text="Capacity: N/A")
        self.embed_region = None
        
        # Reset drop zones
        self.cover_drop_zone.update_text("Drag & Drop Cover Image Here\n(PNG, BMP, JPG)")
        self.payload_drop_zone.update_text("Drag & Drop Payload File Here\n(Any file type)")
        self.cover_drop_zone.reset_colors()
        self.payload_drop_zone.reset_colors()

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

    # --- Audio Steganography Backend Methods ---
    def _encode_audio(self, cover_path, payload_path, stego_key, num_lsbs):
        # --- Read payload file ---
        with open(payload_path, 'rb') as f:
            payload_bytes = f.read()

        # Prepare metadata (payload size + filename length + filename)
        filename = os.path.basename(payload_path)
        metadata = (
            len(payload_bytes).to_bytes(4, 'big')
            + len(filename).to_bytes(1, 'big')
            + filename.encode()
        )
        data_to_embed = metadata + payload_bytes

        # Convert to bitarray (fast + memory-efficient)
        bit_stream = bitarray(endian="big")
        bit_stream.frombytes(data_to_embed)

        # --- Read audio file ---
        with wave.open(cover_path, 'rb') as wav_file:
            params = wav_file.getparams()
            frames = wav_file.readframes(params.nframes)

        # Convert to numpy array (mutable copy)
        if params.sampwidth == 1:
            audio_data = np.frombuffer(frames, dtype=np.uint8).copy()
            max_val, min_val = 255, 0
        elif params.sampwidth == 2:
            audio_data = np.frombuffer(frames, dtype=np.uint16).copy()
            max_val, min_val = 65535, 0
        elif params.sampwidth == 3:
            # 24-bit PCM → unpack into int32
            raw = np.frombuffer(frames, dtype=np.uint8).reshape(-1, 3)
            audio_data = (
                raw[:, 0].astype(np.uint32)
                | (raw[:, 1].astype(np.uint32) << 8)
                | (raw[:, 2].astype(np.uint32) << 16)
            )
            # Adjust for unsigned 24-bit
            audio_data = audio_data & 0xFFFFFF
            max_val, min_val = 16777215, 0
        else:
            raise ValueError("Unsupported sample width. Only 8, 16, and 24-bit audio supported.")

        # --- Capacity check ---
        max_bits = len(audio_data) * num_lsbs
        if len(bit_stream) > max_bits:
            raise ValueError(
                f"Payload too large: {len(bit_stream)} bits > {max_bits} bits available"
            )

        # --- Generate pseudorandom embedding positions ---
        random.seed(stego_key)
        sample_indices = list(range(len(audio_data)))
        random.shuffle(sample_indices)

        # --- Embed data ---
        mask = ~((1 << num_lsbs) - 1)  # clear num_lsbs
        bit_index = 0
        total_bits = len(bit_stream)

        for sample_idx in sample_indices:
            if bit_index >= total_bits:
                break

            # Take next chunk of bits
            chunk = bit_stream[bit_index : bit_index + num_lsbs]
            bits_to_embed = int(chunk.to01().ljust(num_lsbs, '0'), 2)

            # Modify sample
            original_sample = int(audio_data[sample_idx])
            modified_sample = (original_sample & mask) | bits_to_embed

            # Clip to valid range
            modified_sample = np.clip(modified_sample, min_val, max_val)
            audio_data[sample_idx] = modified_sample
            bit_index += num_lsbs

        # --- Save stego audio ---
        stego_path = os.path.join(
            os.path.dirname(cover_path), "stego_" + os.path.basename(cover_path)
        )

        with wave.open(stego_path, "wb") as stego_file:
            stego_file.setparams(params)

            if params.sampwidth == 3:
                # Pack back into 24-bit little-endian
                packed = np.zeros((len(audio_data), 3), dtype=np.uint8)
                vals = audio_data.astype(np.uint32) & 0xFFFFFF
                packed[:, 0] = vals & 0xFF
                packed[:, 1] = (vals >> 8) & 0xFF
                packed[:, 2] = (vals >> 16) & 0xFF
                stego_file.writeframes(packed.tobytes())
            else:
                stego_file.writeframes(audio_data.tobytes())

        return stego_path

    def _decode_audio(self, stego_path, stego_key, num_lsbs):
        # Read stego audio file
        with wave.open(stego_path, 'rb') as wav_file:
            params = wav_file.getparams()
            frames = wav_file.readframes(params.nframes)

        # Convert to numpy array depending on sample width
        if params.sampwidth == 1:
            audio_data = np.frombuffer(frames, dtype=np.uint8)
            max_val = 0xFF
        elif params.sampwidth == 2:
            audio_data = np.frombuffer(frames, dtype=np.uint16)
            max_val = 0xFFFF
        elif params.sampwidth == 3:
            # 24-bit PCM → convert to int32
            raw = np.frombuffer(frames, dtype=np.uint8).reshape(-1, 3)
            # Little-endian assembly
            audio_data = (raw[:, 0].astype(np.uint32) |
                        (raw[:, 1].astype(np.uint32) << 8) |
                        (raw[:, 2].astype(np.uint32) << 16))
            # Adjust for unsigned values
            audio_data = audio_data & 0xFFFFFF
            max_val = 0xFFFFFF
        else:
            raise ValueError("Unsupported sample width. Only 8, 16, and 24-bit audio supported.")

        # Create same pseudorandom sequence used during embedding
        random.seed(stego_key)
        sample_indices = list(range(len(audio_data)))
        random.shuffle(sample_indices)

        # Prepare bit storage
        extracted_bits = bitarray(endian='big')
        mask = (1 << num_lsbs) - 1

        # --- Extract enough bits for metadata ---
        for i in range(40 // num_lsbs + 10):  # small overhead
            sample_idx = sample_indices[i]
            sample_value = int(audio_data[sample_idx]) & max_val
            extracted_bits.extend(bin(sample_value & mask)[2:].zfill(num_lsbs))

        if len(extracted_bits) < 40:
            raise ValueError("Insufficient data for metadata")

        # Parse metadata
        payload_size = int(extracted_bits[:32].to01(), 2)
        filename_len = int(extracted_bits[32:40].to01(), 2)

        if filename_len <= 0 or filename_len > 255:
            raise ValueError(f"Invalid filename length: {filename_len}")
        if payload_size <= 0 or payload_size > 50 * 1024 * 1024:  # 50MB safety limit
            raise ValueError(f"Invalid payload size: {payload_size}")

        total_bits_needed = 40 + filename_len * 8 + payload_size * 8
        max_capacity = len(audio_data) * num_lsbs
        if total_bits_needed > max_capacity:
            raise ValueError("Declared payload exceeds available audio capacity")

        # --- Extract all necessary bits ---
        needed_samples = (total_bits_needed + num_lsbs - 1) // num_lsbs
        for i in range(len(extracted_bits) // num_lsbs, needed_samples):
            sample_idx = sample_indices[i]
            sample_value = int(audio_data[sample_idx]) & max_val
            extracted_bits.extend(bin(sample_value & mask)[2:].zfill(num_lsbs))

        # --- Extract filename ---
        filename_bits = extracted_bits[40:40 + filename_len * 8]
        filename = filename_bits.tobytes().decode("utf-8", errors="replace")

        # --- Extract payload ---
        payload_bits = extracted_bits[40 + filename_len * 8:40 + filename_len * 8 + payload_size * 8]
        if len(payload_bits) != payload_size * 8:
            raise ValueError("Incomplete payload data")

        payload_data = payload_bits.tobytes()

        # Save extracted file
        extracted_path = os.path.join(os.path.dirname(stego_path), f"extracted_{filename}")
        try:
            with open(extracted_path, "wb") as f:
                f.write(payload_data)
        except Exception as e:
            raise ValueError(f"Failed to save extracted file: {str(e)}")

        return extracted_path


    def _calculate_audio_capacity(self, audio_path, num_lsbs):
        try:
            with wave.open(audio_path, 'rb') as wav_file:
                frames = wav_file.getnframes()
                channels = wav_file.getnchannels()
                sampwidth = wav_file.getsampwidth()

            # Each frame = (channels × sampwidth) bytes
            # Each sample contributes `num_lsbs` bits of capacity
            total_samples = frames * channels
            max_bits = total_samples * num_lsbs

            return max_bits // 8  # return capacity in bytes

        except Exception:
            return 0


    # --- Backend Image Steganography Methods (unchanged) ---
    def _encode_image(self, cover_path, payload_path, stego_key, num_lsbs):
        with open(payload_path, 'rb') as f:
            payload_bytes = f.read()
        filename = os.path.basename(payload_path)
        metadata = len(payload_bytes).to_bytes(4, 'big') + len(filename).to_bytes(1, 'big') + filename.encode()
        data_to_embed = metadata + payload_bytes
        bit_stream = ''.join(f'{b:08b}' for b in data_to_embed)

        image = Image.open(cover_path).convert('RGB')
        width, height = image.size
        region = self.get_embed_region_in_original()
        if region:
            x1, y1, x2, y2 = region
            pixel_indices = [(x, y) for y in range(y1, y2) for x in range(x1, x2)]
        else:
            pixel_indices = [(x, y) for y in range(height) for x in range(width)]

        max_bits = len(pixel_indices) * 3 * num_lsbs
        if len(bit_stream) > max_bits:
            raise ValueError(f"Payload too large: {len(bit_stream)} bits > {max_bits} bits available")

        random.seed(stego_key)
        random.shuffle(pixel_indices)
        data_index = 0
        pixels = image.load()
        mask = (255 << num_lsbs) & 255
        for x, y in pixel_indices:
            if data_index >= len(bit_stream): break
            r, g, b = pixels[x, y]
            rgb = [r, g, b]
            for i in range(3):
                if data_index < len(bit_stream):
                    chunk = bit_stream[data_index:data_index+num_lsbs].ljust(num_lsbs, '0')
                    bits = int(chunk, 2)
                    rgb[i] = (rgb[i] & mask) | bits
                    data_index += num_lsbs
            pixels[x, y] = tuple(rgb)
        stego_path = os.path.join(os.path.dirname(cover_path), "stego_" + os.path.basename(cover_path))
        image.save(stego_path, "PNG")
        return stego_path

    def _decode_image(self, stego_path, stego_key, num_lsbs):
        image = Image.open(stego_path).convert('RGB')
        width, height = image.size
        region = self.get_embed_region_in_original()
        if region:
            x1, y1, x2, y2 = region
            pixel_indices = [(x, y) for y in range(y1, y2) for x in range(x1, x2)]
        else:
            pixel_indices = [(x, y) for y in range(height) for x in range(width)]
        random.seed(stego_key)
        random.shuffle(pixel_indices)

        extracted_bits = ""
        mask = (1 << num_lsbs) - 1
        pixels = image.load()
        for x, y in pixel_indices:
            r, g, b = pixels[x, y]
            extracted_bits += f'{(r & mask):0{num_lsbs}b}'
            extracted_bits += f'{(g & mask):0{num_lsbs}b}'
            extracted_bits += f'{(b & mask):0{num_lsbs}b}'

        payload_size = int(extracted_bits[:32], 2)
        filename_len = int(extracted_bits[32:40], 2)
        filename_bits = extracted_bits[40:40+filename_len*8]
        filename = int(filename_bits, 2).to_bytes(filename_len, 'big').decode(errors='ignore')
        start = 40 + filename_len*8
        payload_bits = extracted_bits[start:start+payload_size*8]
        payload_bytes = int(payload_bits, 2).to_bytes(payload_size, 'big')

        extracted_path = os.path.join(os.path.dirname(stego_path), f"extracted_{filename}")
        with open(extracted_path, 'wb') as f:
            f.write(payload_bytes)
        return extracted_path

    def _calculate_capacity(self, image_path, num_lsbs, region=None):
        image = Image.open(image_path)
        width, height = image.size
        if region:
            x1, y1, x2, y2 = region
            num_pixels = (x2-x1) * (y2-y1)
        else:
            num_pixels = width * height
        return (num_pixels * 3 * num_lsbs) // 8

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