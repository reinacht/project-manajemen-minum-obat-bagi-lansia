import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import datetime
import os
import threading
import time
import winsound
import sys
import io
import math
from pathlib import Path
from collections import defaultdict

# Warna elegant theme (soft professional palette)
COLORS = {
    'bg': '#f8f9fa',
    'card_bg': '#ffffff',
    'primary': '#4361ee',
    'primary_light': '#e6f0ff',
    'secondary': '#7209b7',
    'accent': '#06d6a0',
    'danger': '#ef476f',
    'warning': '#ffd166',
    'success': '#06d6a0',
    'text': '#2d3748',
    'text_light': '#718096',
    'border': '#e2e8f0'
}

# Suppress pygame welcome message
class SuppressPygameOutput:
    def __enter__(self):
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr

with SuppressPygameOutput():
    try:
        import pygame
        PYGAME_AVAILABLE = True
    except ImportError:
        PYGAME_AVAILABLE = False
        print("Pygame tidak tersedia, menggunakan fallback sound")

class SoundManager:
    def __init__(self):
        self.sound_enabled = True
        self.pygame_available = PYGAME_AVAILABLE
        self.custom_sounds = {}
        self.sound_files_path = "sound_files"
        self.initialize_sound_system()
    
    def initialize_sound_system(self):
        if self.pygame_available:
            try:
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
                self.create_default_sounds()
                self.load_custom_sounds()
            except:
                self.pygame_available = False
    
    def create_default_sounds(self):
        if not self.pygame_available:
            return
            
        try:
            self.create_beep_sound(800, 1000, "reminder")
            self.create_beep_sound(1200, 500, "success")
        except:
            pass
    
    def create_beep_sound(self, frequency, duration, sound_name):
        if not self.pygame_available:
            return
            
        try:
            sample_rate = 22050
            n_samples = int(sample_rate * duration / 1000.0)
            buf = []
            max_sample = 2**(16 - 1) - 1
            for i in range(n_samples):
                t = float(i) / sample_rate
                sample = int(max_sample * math.sin(2 * math.pi * frequency * t))
                buf.append([sample, sample])
            
            try:
                import numpy as np
                wave_array = np.array(buf, dtype=np.int16)
                self.custom_sounds[sound_name] = pygame.sndarray.make_sound(wave_array)
            except ImportError:
                sound_buffer = pygame.sndarray.array(buf)
                self.custom_sounds[sound_name] = pygame.sndarray.make_sound(sound_buffer)
        except:
            pass
    
    def load_custom_sounds(self):
        if not self.pygame_available:
            return
            
        os.makedirs(self.sound_files_path, exist_ok=True)
        supported_formats = ['.wav', '.mp3', '.ogg']
        
        for file_format in supported_formats:
            for sound_file in Path(self.sound_files_path).glob(f"*{file_format}"):
                try:
                    sound_name = sound_file.stem
                    sound = pygame.mixer.Sound(str(sound_file))
                    self.custom_sounds[sound_name] = sound
                except:
                    pass
    
    def add_custom_sound(self, file_path, sound_name):
        if not self.pygame_available:
            return False
            
        try:
            sound = pygame.mixer.Sound(file_path)
            self.custom_sounds[sound_name] = sound
            
            sound_files_path = Path(self.sound_files_path)
            sound_files_path.mkdir(exist_ok=True)
            
            import shutil
            dest_path = sound_files_path / f"{sound_name}{Path(file_path).suffix}"
            shutil.copy2(file_path, dest_path)
            return True
        except:
            return False
    
    def get_available_sounds(self):
        sounds = list(self.custom_sounds.keys())
        if not sounds:
            sounds = ["reminder", "success"]
        return sounds
    
    def play_sound(self, sound_name="reminder"):
        if not self.sound_enabled:
            return False
            
        try:
            if self.pygame_available and sound_name in self.custom_sounds:
                self.custom_sounds[sound_name].play()
                return True
            else:
                return self.play_system_sound(sound_name)
        except:
            return self.play_system_sound(sound_name)
    
    def play_system_sound(self, sound_type="reminder"):
        try:
            if sound_type == "success":
                winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
            else:
                winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
            return True
        except:
            print("\a")
            return True
    
    def toggle_sound(self, enabled):
        self.sound_enabled = enabled

class Medicine:
    def __init__(self, name, dosage, schedule, description="", with_food=False, 
                 sound_enabled=True, custom_sound="reminder"):
        self.name = name
        self.dosage = dosage
        self.schedule = schedule
        self.description = description
        self.with_food = with_food
        self.sound_enabled = sound_enabled
        self.custom_sound = custom_sound
        self.history = []
    
    def to_dict(self):
        return {
            'name': self.name,
            'dosage': self.dosage,
            'schedule': self.schedule,
            'description': self.description,
            'with_food': self.with_food,
            'sound_enabled': self.sound_enabled,
            'custom_sound': self.custom_sound,
            'history': self.history
        }
    
    @classmethod
    def from_dict(cls, data):
        medicine = cls(
            data['name'],
            data['dosage'],
            data['schedule'],
            data.get('description', ''),
            data.get('with_food', False),
            data.get('sound_enabled', True),
            data.get('custom_sound', 'reminder')
        )
        medicine.history = data.get('history', [])
        return medicine

class ElderlyPerson:
    def __init__(self, name, age, condition=""):
        self.name = name
        self.age = age
        self.condition = condition
        self.medicines = []
        self.medicine_suggestions = defaultdict(list)
    
    def add_medicine(self, medicine):
        self.medicines.append(medicine)
        if medicine.name not in self.medicine_suggestions:
            self.medicine_suggestions[medicine.name].append({
                'dosage': medicine.dosage,
                'description': medicine.description,
                'with_food': medicine.with_food,
                'count': 1
            })
        else:
            found = False
            for suggestion in self.medicine_suggestions[medicine.name]:
                if suggestion['dosage'] == medicine.dosage and suggestion['description'] == medicine.description:
                    suggestion['count'] += 1
                    found = True
                    break
            if not found:
                self.medicine_suggestions[medicine.name].append({
                    'dosage': medicine.dosage,
                    'description': medicine.description,
                    'with_food': medicine.with_food,
                    'count': 1
                })
    
    def remove_medicine(self, medicine_name):
        self.medicines = [med for med in self.medicines if med.name != medicine_name]
    
    def get_medicine_names(self):
        names = list(set(med.name for med in self.medicines))
        return sorted(names)
    
    def get_medicine_suggestions(self, medicine_name):
        return self.medicine_suggestions.get(medicine_name, [])
    
    def to_dict(self):
        return {
            'name': self.name,
            'age': self.age,
            'condition': self.condition,
            'medicines': [med.to_dict() for med in self.medicines],
            'medicine_suggestions': dict(self.medicine_suggestions)
        }
    
    @classmethod
    def from_dict(cls, data):
        person = cls(data['name'], data['age'], data.get('condition', ''))
        person.medicines = [Medicine.from_dict(med) for med in data.get('medicines', [])]
        person.medicine_suggestions = defaultdict(list, data.get('medicine_suggestions', {}))
        return person

class ElderlyManager:
    def __init__(self):
        self.data_file = "elderly_data.json"
        self.elderly_people = []  # Daftar semua lansia
        self.current_person = None  # Lansia yang sedang aktif
        self.elderly_suggestions = defaultdict(list)  # Saran untuk lansia
        self.sound_manager = SoundManager()
        self.load_data()
    
    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Load multiple elderly people
                    if isinstance(data, list):
                        self.elderly_people = [ElderlyPerson.from_dict(person_data) for person_data in data]
                        if self.elderly_people:
                            self.current_person = self.elderly_people[0]
                    else:
                        # Backward compatibility with old single-person format
                        person = ElderlyPerson.from_dict(data)
                        self.elderly_people = [person]
                        self.current_person = person
                    
                    # Load elderly suggestions
                    for person in self.elderly_people:
                        if person.name:
                            self.elderly_suggestions[person.name].append({
                                'age': person.age,
                                'condition': person.condition,
                                'count': 1
                            })
            except:
                self.elderly_people = [ElderlyPerson("", 0)]
                self.current_person = self.elderly_people[0]
        else:
            self.elderly_people = [ElderlyPerson("", 0)]
            self.current_person = self.elderly_people[0]
    
    def save_data(self):
        try:
            # Simpan semua data lansia
            data_to_save = [person.to_dict() for person in self.elderly_people]
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def get_elderly_names(self):
        """Mendapatkan semua nama lansia unik yang pernah dimasukkan"""
        names = list(set(person.name for person in self.elderly_people if person.name))
        return sorted(names)
    
    def get_elderly_suggestions(self, name):
        """Mendapatkan saran untuk lansia tertentu"""
        return self.elderly_suggestions.get(name, [])
    
    def set_current_person(self, name, age=None, condition=None):
        """Mengatur lansia yang sedang aktif"""
        # Cari apakah lansia sudah ada
        for person in self.elderly_people:
            if person.name == name:
                if age is not None:
                    person.age = age
                if condition is not None:
                    person.condition = condition
                self.current_person = person
                self.save_data()
                return person
        
        # Jika tidak ada, buat baru
        if age is None:
            age = 0
        if condition is None:
            condition = ""
        
        new_person = ElderlyPerson(name, age, condition)
        self.elderly_people.append(new_person)
        self.current_person = new_person
        
        # Tambahkan ke saran
        if name:
            self.elderly_suggestions[name].append({
                'age': age,
                'condition': condition,
                'count': 1
            })
        
        self.save_data()
        return new_person
    
    def get_person_info(self, name):
        """Mendapatkan informasi lansia berdasarkan nama"""
        for person in self.elderly_people:
            if person.name == name:
                return {
                    'name': person.name,
                    'age': person.age,
                    'condition': person.condition
                }
        return None
    
    def add_medicine(self, medicine):
        if self.current_person:
            self.current_person.add_medicine(medicine)
            self.save_data()
    
    def remove_medicine(self, medicine_name):
        if self.current_person:
            self.current_person.remove_medicine(medicine_name)
            self.save_data()
    
    def record_medicine_taken(self, medicine_name, time_taken):
        if self.current_person:
            for medicine in self.current_person.medicines:
                if medicine.name == medicine_name:
                    medicine.history.append({
                        'time': time_taken,
                        'timestamp': datetime.datetime.now().isoformat()
                    })
            self.sound_manager.play_sound("success")
            self.save_data()
    
    def add_custom_sound(self, file_path, sound_name):
        return self.sound_manager.add_custom_sound(file_path, sound_name)
    
    def get_available_sounds(self):
        return self.sound_manager.get_available_sounds()
    
    def get_medicine_names(self):
        if self.current_person:
            return self.current_person.get_medicine_names()
        return []
    
    def get_medicine_suggestions(self, medicine_name):
        if self.current_person:
            return self.current_person.get_medicine_suggestions(medicine_name)
        return []

class MedicineReminder:
    def __init__(self, medicine_manager, gui_callback):
        self.medicine_manager = medicine_manager
        self.gui_callback = gui_callback
        self.running = False
        self.reminder_thread = None
        self.pending_reminders = {}
    
    def start(self):
        self.running = True
        self.reminder_thread = threading.Thread(target=self._check_reminders)
        self.reminder_thread.daemon = True
        self.reminder_thread.start()
    
    def stop(self):
        self.running = False
    
    def _check_reminders(self):
        while self.running:
            try:
                now = datetime.datetime.now()
                current_time = now.strftime("%H:%M")
                current_date = now.strftime("%Y-%m-%d")
                
                if self.medicine_manager.current_person:
                    for medicine in self.medicine_manager.current_person.medicines:
                        if current_time in medicine.schedule:
                            reminder_key = f"{medicine.name}_{current_time}_{current_date}"
                            
                            taken_today = any(
                                record['time'] == current_time and 
                                record['timestamp'].startswith(current_date)
                                for record in medicine.history
                            )
                            
                            reminder_shown = reminder_key in self.pending_reminders
                            
                            if not taken_today and not reminder_shown:
                                if medicine.sound_enabled:
                                    self.medicine_manager.sound_manager.play_sound(medicine.custom_sound)
                                
                                self.pending_reminders[reminder_key] = now
                                self.gui_callback(medicine, current_time)
                
                one_day_ago = now - datetime.timedelta(days=1)
                self.pending_reminders = {
                    k: v for k, v in self.pending_reminders.items() 
                    if v > one_day_ago
                }
                
            except:
                pass
            
            time.sleep(30)

class MedicineGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("💊 Manajemen Obat Lansia (Yuda(164), Danies(195), Fakih(133))")
        self.root.geometry("1100x750")
        self.root.configure(bg=COLORS['bg'])
        
        self.manager = ElderlyManager()
        self.reminder = MedicineReminder(self.manager, self.show_reminder)
        
        self.setup_styles()
        self.create_gui()
        self.reminder.start()
        
        self.load_initial_data()
    
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('Custom.TFrame', background=COLORS['bg'])
        style.configure('Card.TFrame', background=COLORS['card_bg'])
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), background=COLORS['bg'], foreground=COLORS['primary'])
        style.configure('Subtitle.TLabel', font=('Arial', 11), background=COLORS['bg'], foreground=COLORS['text_light'])
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'), background=COLORS['card_bg'], foreground=COLORS['text'])
        
        # Button styles
        style.configure('Primary.TButton', font=('Arial', 10), background=COLORS['primary'], 
                       foreground='white', borderwidth=0, padding=6)
        style.map('Primary.TButton', 
                 background=[('active', COLORS['primary']), ('pressed', COLORS['primary'])])
        
        style.configure('Success.TButton', font=('Arial', 10), background=COLORS['success'], 
                       foreground='white', borderwidth=0, padding=6)
        
        style.configure('Danger.TButton', font=('Arial', 10), background=COLORS['danger'], 
                       foreground='white', borderwidth=0, padding=6)
        
        style.configure('Accent.TButton', font=('Arial', 10), background=COLORS['accent'], 
                       foreground='white', borderwidth=0, padding=6)
        
        # Entry and Combobox
        style.configure('Custom.TEntry', fieldbackground=COLORS['card_bg'])
        style.configure('Custom.TCombobox', fieldbackground=COLORS['card_bg'])
        
        # Treeview
        style.configure('Treeview', background=COLORS['card_bg'], fieldbackground=COLORS['card_bg'], 
                       foreground=COLORS['text'], rowheight=25)
        style.configure('Treeview.Heading', background=COLORS['primary_light'], foreground=COLORS['primary'], 
                       font=('Arial', 10, 'bold'))
        style.map('Treeview', background=[('selected', COLORS['primary_light'])])
    
    def create_gui(self):
        # Main container with padding
        main_container = ttk.Frame(self.root, padding="15", style='Custom.TFrame')
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=1)
        
        # Header Section
        header_frame = ttk.Frame(main_container, style='Custom.TFrame')
        header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W,tk.E), pady=(0, 15))
        
        # Container untuk semua elemen header
        header_container = ttk.Frame(header_frame, style='Custom.TFrame')
        header_container.pack(expand=True, fill='x')
        
        # Bagian kiri: judul dan kelompok
        left_header = ttk.Frame(header_container, style='Custom.TFrame')
        left_header.pack(side=tk.LEFT)
        
        # Judul utama
        ttk.Label(left_header, text="💊 Manajemen Obat Lansia", 
                 style='Title.TLabel').pack(side=tk.LEFT)
        
        # Label kelompok dengan warna berbeda
        group_label = tk.Label(left_header, 
                              text="            Program Kelompok 15",
                              font=('Arial', 16, 'bold'),
                              fg='#7209b7',  # Warna ungu
                              bg=COLORS['bg'])
        group_label.pack(side=tk.LEFT, padx=(15, 0))  # Spasi lebih besar agar ke tengah

        sound_frame = ttk.Frame(header_container, style='Custom.TFrame')
        sound_frame.pack(side=tk.RIGHT)
        
        self.sound_btn = ttk.Button(sound_frame, text="🔊 SUARA AKTIF", 
                                   command=self.toggle_sound, style='Primary.TButton')
        self.sound_btn.pack(side=tk.LEFT, padx=2)
        ttk.Button(sound_frame, text="Test Sound", 
                  command=self.test_sound, style='Accent.TButton').pack(side=tk.LEFT, padx=2)
        
        # Left Panel (Info & Add Medicine)
        left_panel = ttk.Frame(main_container, style='Custom.TFrame')
        left_panel.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Person Info Card
        info_card = ttk.Frame(left_panel, padding="15", style='Card.TFrame', relief='ridge', borderwidth=1)
        info_card.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        info_card.columnconfigure(1, weight=1)
        
        ttk.Label(info_card, text="👵 Informasi Lansia", style='Header.TLabel').grid(row=0, column=0, columnspan=4, pady=(0, 10))
        
        # Nama Lansia dengan Combobox
        ttk.Label(info_card, text="Nama:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.name_var = tk.StringVar()
        self.name_combo = ttk.Combobox(info_card, textvariable=self.name_var, 
                                      width=18, state="normal", style='Custom.TCombobox')
        self.name_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=3, padx=(5, 5))
        self.name_combo.bind('<<ComboboxSelected>>', self.on_person_name_selected)
        self.name_combo.bind('<KeyRelease>', self.on_person_name_changed)
        
        # Tombol untuk melihat daftar lansia
        self.view_persons_btn = ttk.Button(info_card, text="👥 Lihat Daftar", 
                                         command=self.show_person_list, style='Primary.TButton',
                                         width=10)
        self.view_persons_btn.grid(row=1, column=2, pady=3, padx=(5, 0))
        
        ttk.Label(info_card, text="Usia:").grid(row=1, column=3, sticky=tk.W, pady=3)
        self.age_entry = ttk.Entry(info_card, width=8, style='Custom.TEntry')
        self.age_entry.grid(row=1, column=4, sticky=tk.W, pady=3)
        
        ttk.Label(info_card, text="Kondisi:").grid(row=2, column=0, sticky=tk.W, pady=3)
        self.condition_var = tk.StringVar()
        self.condition_entry = ttk.Entry(info_card, textvariable=self.condition_var, 
                                       width=25, style='Custom.TEntry')
        self.condition_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=3, padx=(5, 10), columnspan=2)
        
        ttk.Button(info_card, text="Simpan Info", 
                  command=self.save_person_info, style='Primary.TButton').grid(row=2, column=4, pady=3)
        
        # Add Medicine Card
        medicine_card = ttk.Frame(left_panel, padding="15", style='Card.TFrame', relief='ridge', borderwidth=1)
        medicine_card.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        medicine_card.columnconfigure(1, weight=1)
        
        ttk.Label(medicine_card, text="➕ Tambah Obat Baru", style='Header.TLabel').grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Nama Obat dengan Combobox
        ttk.Label(medicine_card, text="Nama Obat:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.med_name_var = tk.StringVar()
        self.med_name_combo = ttk.Combobox(medicine_card, textvariable=self.med_name_var, 
                                          width=23, state="normal", style='Custom.TCombobox')
        self.med_name_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=3, padx=(5, 0))
        self.med_name_combo.bind('<<ComboboxSelected>>', self.on_medicine_name_selected)
        self.med_name_combo.bind('<KeyRelease>', self.on_medicine_name_changed)
        
        # Tombol untuk melihat daftar obat
        self.view_meds_btn = ttk.Button(medicine_card, text="📋 Lihat Daftar", 
                                       command=self.show_medicine_list, style='Primary.TButton',
                                       width=12)
        self.view_meds_btn.grid(row=1, column=2, pady=3, padx=(5, 0))
        
        fields = [
            ("Dosis:", "dosage_entry", 25),
            ("Jadwal (contoh: 08:00,12:00):", "schedule_entry", 25),
            ("Keterangan:", "desc_entry", 25),
        ]
        
        for i, (label, attr_name, width) in enumerate(fields, 2):
            ttk.Label(medicine_card, text=label).grid(row=i, column=0, sticky=tk.W, pady=3)
            entry = ttk.Entry(medicine_card, width=width, style='Custom.TEntry')
            entry.grid(row=i, column=1, sticky=(tk.W, tk.E), pady=3, padx=(5, 0), columnspan=2)
            setattr(self, attr_name, entry)
        
        # Sound selection
        ttk.Label(medicine_card, text="Suara Notifikasi:").grid(row=5, column=0, sticky=tk.W, pady=3)
        self.sound_combobox = ttk.Combobox(medicine_card, width=23, state="readonly", style='Custom.TCombobox')
        self.sound_combobox.grid(row=5, column=1, sticky=(tk.W, tk.E), pady=3, padx=(5, 0))
        
        self.with_food_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(medicine_card, text="Diminum setelah makan", 
                       variable=self.with_food_var).grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=3)
        
        self.sound_enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(medicine_card, text="Aktifkan notifikasi suara", 
                       variable=self.sound_enabled_var).grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=3)
        
        ttk.Button(medicine_card, text="Tambah Obat", 
                  command=self.add_medicine, style='Success.TButton').grid(row=8, column=0, columnspan=3, pady=10)
        
        # Sound Management Card
        sound_card = ttk.Frame(left_panel, padding="15", style='Card.TFrame', relief='ridge', borderwidth=1)
        sound_card.grid(row=2, column=0, sticky=(tk.W, tk.E))
        sound_card.columnconfigure(1, weight=1)
        
        ttk.Label(sound_card, text="🎵 Kelola Suara Kustom", style='Header.TLabel').grid(row=0, column=0, columnspan=4, pady=(0, 10))
        
        # Row 1: Nama suara
        ttk.Label(sound_card, text="Nama Suara:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.sound_name_entry = ttk.Entry(sound_card, width=20, style='Custom.TEntry')
        self.sound_name_entry.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(5, 5))
        self.sound_name_entry.insert(0, "nama_suara")
        
        # Row 2: Tombol pilih file dan tambah
        ttk.Button(sound_card, text="Pilih File Suara", 
                  command=self.browse_sound_file, style='Primary.TButton').grid(row=1, column=2, pady=5, padx=(5, 5))
        
        ttk.Button(sound_card, text="Tambah", 
                  command=self.add_custom_sound, style='Success.TButton').grid(row=1, column=3, pady=5)
        
        # Row 3: Label suara tersedia
        ttk.Label(sound_card, text="Suara Tersedia:").grid(row=2, column=0, sticky=tk.W, pady=(10, 5))
        
        # Row 4: Combobox suara tersedia dan tombol test
        self.sounds_combobox = ttk.Combobox(sound_card, width=20, state="readonly", style='Custom.TCombobox')
        self.sounds_combobox.grid(row=2, column=1, sticky=tk.W, pady=(10, 5), padx=(5, 5))
        
        ttk.Button(sound_card, text="Test Suara", 
                  command=self.test_selected_sound, style='Accent.TButton').grid(row=2, column=2, pady=(10, 5))
        
        # Row 5: Info format
        ttk.Label(sound_card, text="Format: WAV, MP3, OGG", 
                 font=('Arial', 8), foreground=COLORS['text_light']).grid(row=3, column=0, columnspan=4, sticky=tk.W, pady=(5, 0))
        
        # Right Panel (Medicines List & History)
        right_panel = ttk.Frame(main_container, style='Custom.TFrame')
        right_panel.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_panel.rowconfigure(1, weight=1)
        right_panel.columnconfigure(0, weight=1)
        
        # Current Person Display
        current_person_frame = ttk.Frame(right_panel, padding="10", style='Card.TFrame', relief='ridge', borderwidth=1)
        current_person_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.current_person_label = ttk.Label(current_person_frame, 
                                             text="👵 Lansia Aktif: Tidak ada",
                                             font=('Arial', 11, 'bold'),
                                             foreground=COLORS['primary'])
        self.current_person_label.pack()
        
        # Medicines List Card
        list_card = ttk.Frame(right_panel, padding="15", style='Card.TFrame', relief='ridge', borderwidth=1)
        list_card.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        list_card.rowconfigure(0, weight=1)
        list_card.columnconfigure(0, weight=1)
        
        ttk.Label(list_card, text="📋 Daftar Obat", style='Header.TLabel').grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        columns = ('Nama', 'Dosis', 'Jadwal', 'Suara', 'Status')
        self.medicines_tree = ttk.Treeview(list_card, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.medicines_tree.heading(col, text=col)
            self.medicines_tree.column(col, width=120 if col != 'Jadwal' else 150)
        
        self.medicines_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(list_card, orient=tk.VERTICAL, command=self.medicines_tree.yview)
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.medicines_tree.configure(yscrollcommand=scrollbar.set)
        
        btn_frame = ttk.Frame(list_card, style='Card.TFrame')
        btn_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(btn_frame, text="Hapus Obat", 
                  command=self.remove_medicine, style='Danger.TButton').pack(side=tk.LEFT, padx=2)
        
        ttk.Button(btn_frame, text="Tandai Diminum", 
                  command=self.mark_as_taken, style='Success.TButton').pack(side=tk.LEFT, padx=2)
        
        ttk.Button(btn_frame, text="Ubah Suara", 
                  command=self.change_medicine_sound, style='Primary.TButton').pack(side=tk.LEFT, padx=2)
        
        # History Card
        history_card = ttk.Frame(right_panel, padding="15", style='Card.TFrame', relief='ridge', borderwidth=1)
        history_card.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        history_card.rowconfigure(0, weight=1)
        history_card.columnconfigure(0, weight=1)
        
        ttk.Label(history_card, text="📊 Riwayat Minum", style='Header.TLabel').grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        columns = ('Waktu', 'Nama Obat', 'Dosis', 'Status')
        self.history_tree = ttk.Treeview(history_card, columns=columns, show='headings', height=6)
        
        column_widths = {'Waktu': 150, 'Nama Obat': 150, 'Dosis': 100, 'Status': 100}
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=column_widths.get(col, 100))
        
        self.history_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar2 = ttk.Scrollbar(history_card, orient=tk.VERTICAL, command=self.history_tree.yview)
        scrollbar2.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.history_tree.configure(yscrollcommand=scrollbar2.set)
        
        ttk.Button(history_card, text="Refresh Riwayat", 
                  command=self.refresh_history, style='Primary.TButton').grid(row=2, column=0, pady=(10, 0))
    
    def load_initial_data(self):
        self.refresh_elderly_names()
        self.refresh_medicine_names()
        self.refresh_sound_list()
        self.update_current_person_display()
        
        if self.manager.current_person:
            self.load_current_person_info()
            self.refresh_medicines_list()
            self.refresh_history()
    
    def load_current_person_info(self):
        """Memuat informasi lansia yang sedang aktif ke form"""
        if self.manager.current_person:
            person = self.manager.current_person
            self.name_var.set(person.name)
            self.age_entry.delete(0, tk.END)
            self.age_entry.insert(0, str(person.age) if person.age else "")
            self.condition_var.set(person.condition)
    
    def update_current_person_display(self):
        """Update label lansia aktif"""
        if self.manager.current_person and self.manager.current_person.name:
            person = self.manager.current_person
            self.current_person_label.config(
                text=f"👵 Lansia Aktif: {person.name} ({person.age} tahun)"
            )
        else:
            self.current_person_label.config(text="👵 Lansia Aktif: Tidak ada")
    
    def refresh_sound_list(self):
        sounds = self.manager.get_available_sounds()
        self.sounds_combobox['values'] = sounds
        self.sound_combobox['values'] = sounds
        
        if sounds:
            self.sounds_combobox.set(sounds[0])
            self.sound_combobox.set(sounds[0])
    
    def refresh_medicine_names(self):
        """Refresh daftar nama obat untuk combobox"""
        medicine_names = self.manager.get_medicine_names()
        self.med_name_combo['values'] = medicine_names
    
    def refresh_elderly_names(self):
        """Refresh daftar nama lansia untuk combobox"""
        elderly_names = self.manager.get_elderly_names()
        self.name_combo['values'] = elderly_names
    
    def on_person_name_selected(self, event):
        """Ketika nama lansia dipilih dari dropdown"""
        selected_name = self.name_var.get()
        if selected_name:
            # Dapatkan informasi lansia
            person_info = self.manager.get_person_info(selected_name)
            if person_info:
                # Set lansia aktif
                self.manager.set_current_person(
                    person_info['name'], 
                    person_info['age'], 
                    person_info['condition']
                )
                
                # Load informasi ke form
                self.load_current_person_info()
                self.update_current_person_display()
                self.refresh_medicines_list()
                self.refresh_history()
    
    def on_person_name_changed(self, event):
        """Ketika teks di combobox nama lansia berubah"""
        current_text = self.name_var.get()
        if current_text:
            # Filter suggestions based on input
            all_names = self.manager.get_elderly_names()
            filtered_names = [name for name in all_names if current_text.lower() in name.lower()]
            self.name_combo['values'] = filtered_names
    
    def show_person_list(self):
        """Menampilkan dialog dengan daftar semua lansia yang pernah dimasukkan"""
        elderly_names = self.manager.get_elderly_names()
        
        list_dialog = tk.Toplevel(self.root)
        list_dialog.title("👥 Daftar Lansia")
        list_dialog.geometry("400x350")
        list_dialog.configure(bg=COLORS['bg'])
        list_dialog.transient(self.root)
        
        ttk.Label(list_dialog, text="Pilih lansia dari daftar:", 
                 font=('Arial', 11, 'bold')).pack(pady=10)
        
        # Frame untuk listbox
        list_frame = ttk.Frame(list_dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Listbox
        person_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                   bg=COLORS['card_bg'], font=('Arial', 10))
        person_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=person_listbox.yview)
        
        # Isi listbox dengan informasi lengkap
        for name in elderly_names:
            person_info = self.manager.get_person_info(name)
            if person_info:
                display_text = f"{name} ({person_info['age']} tahun)"
                if person_info['condition']:
                    display_text += f" - {person_info['condition']}"
                person_listbox.insert(tk.END, display_text)
        
        def select_person():
            selection = person_listbox.curselection()
            if selection:
                selected_text = person_listbox.get(selection[0])
                # Ekstrak nama dari teks
                selected_name = selected_text.split(' (')[0]
                self.name_var.set(selected_name)
                self.on_person_name_selected(None)  # Trigger load info
                list_dialog.destroy()
        
        def delete_person():
            selection = person_listbox.curselection()
            if selection:
                selected_text = person_listbox.get(selection[0])
                selected_name = selected_text.split(' (')[0]
                
                if messagebox.askyesno("Konfirmasi", f"Hapus data {selected_name}?"):
                    # Hapus dari daftar
                    self.manager.elderly_people = [
                        p for p in self.manager.elderly_people 
                        if p.name != selected_name
                    ]
                    self.manager.save_data()
                    
                    # Refresh daftar
                    person_listbox.delete(selection[0])
                    self.refresh_elderly_names()
                    
                    messagebox.showinfo("Sukses", f"Data {selected_name} berhasil dihapus!")
        
        # Tombol pilih
        btn_frame = ttk.Frame(list_dialog)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Pilih Lansia", 
                  command=select_person, style='Primary.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Hapus Lansia", 
                  command=delete_person, style='Danger.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Tutup", 
                  command=list_dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def on_medicine_name_selected(self, event):
        """Ketika nama obat dipilih dari dropdown"""
        selected_name = self.med_name_var.get()
        if selected_name:
            # Dapatkan saran untuk obat ini
            suggestions = self.manager.get_medicine_suggestions(selected_name)
            if suggestions:
                # Urutkan berdasarkan frekuensi penggunaan (count)
                suggestions.sort(key=lambda x: x['count'], reverse=True)
                most_common = suggestions[0]
                
                # Isi otomatis field berdasarkan saran
                self.dosage_entry.delete(0, tk.END)
                self.dosage_entry.insert(0, most_common['dosage'])
                
                self.desc_entry.delete(0, tk.END)
                if most_common['description']:
                    self.desc_entry.insert(0, most_common['description'])
                
                self.with_food_var.set(most_common.get('with_food', True))
    
    def on_medicine_name_changed(self, event):
        """Ketika teks di combobox obat berubah"""
        current_text = self.med_name_var.get()
        if current_text:
            # Filter suggestions based on input
            all_names = self.manager.get_medicine_names()
            filtered_names = [name for name in all_names if current_text.lower() in name.lower()]
            self.med_name_combo['values'] = filtered_names
    
    def show_medicine_list(self):
        """Menampilkan dialog dengan daftar semua obat yang pernah dimasukkan"""
        medicine_names = self.manager.get_medicine_names()
        
        list_dialog = tk.Toplevel(self.root)
        list_dialog.title("📋 Daftar Obat Tersedia")
        list_dialog.geometry("350x300")
        list_dialog.configure(bg=COLORS['bg'])
        list_dialog.transient(self.root)
        
        ttk.Label(list_dialog, text="Pilih obat dari daftar:", 
                 font=('Arial', 11, 'bold')).pack(pady=10)
        
        # Frame untuk listbox
        list_frame = ttk.Frame(list_dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Listbox
        medicine_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                     bg=COLORS['card_bg'], font=('Arial', 10))
        medicine_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=medicine_listbox.yview)
        
        # Isi listbox
        for name in medicine_names:
            medicine_listbox.insert(tk.END, name)
        
        def select_medicine():
            selection = medicine_listbox.curselection()
            if selection:
                selected_name = medicine_listbox.get(selection[0])
                self.med_name_var.set(selected_name)
                self.on_medicine_name_selected(None)  # Trigger autofill
                list_dialog.destroy()
        
        # Tombol pilih
        btn_frame = ttk.Frame(list_dialog)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Pilih Obat", 
                  command=select_medicine, style='Primary.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Tutup", 
                  command=list_dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def browse_sound_file(self):
        file_types = [
            ("Audio files", "*.wav *.mp3 *.ogg"),
            ("All files", "*.*")
        ]
        
        file_path = filedialog.askopenfilename(
            title="Pilih File Suara",
            filetypes=file_types
        )
        
        if file_path:
            suggested_name = Path(file_path).stem
            self.sound_name_entry.delete(0, tk.END)
            self.sound_name_entry.insert(0, suggested_name)
            messagebox.showinfo("File Dipilih", f"File suara dipilih: {Path(file_path).name}")
    
    def add_custom_sound(self):
        sound_name = self.sound_name_entry.get().strip()
        if not sound_name:
            messagebox.showerror("Error", "Masukkan nama untuk suara!")
            return
        
        # Tanyakan file suara
        file_types = [
            ("Audio files", "*.wav *.mp3 *.ogg"),
            ("All files", "*.*")
        ]
        
        file_path = filedialog.askopenfilename(
            title="Pilih File Suara untuk " + sound_name,
            filetypes=file_types
        )
        
        if not file_path:
            return  # User membatalkan
        
        # Tambahkan suara
        success = self.manager.add_custom_sound(file_path, sound_name)
        if success:
            messagebox.showinfo("Sukses", f"Suara '{sound_name}' berhasil ditambahkan!")
            self.refresh_sound_list()
        else:
            messagebox.showerror("Error", "Gagal menambahkan suara. Pastikan format file didukung.")
    
    def test_selected_sound(self):
        sound_name = self.sounds_combobox.get()
        if sound_name:
            success = self.manager.sound_manager.play_sound(sound_name)
            if success:
                messagebox.showinfo("Test Suara", f"Memainkan suara: {sound_name}")
            else:
                messagebox.showerror("Error", f"Gagal memainkan suara: {sound_name}")
        else:
            messagebox.showwarning("Peringatan", "Pilih suara terlebih dahulu!")
    
    def test_sound(self):
        self.manager.sound_manager.play_sound("reminder")
        messagebox.showinfo("Test Suara", "Suara notifikasi di-test!")
    
    def toggle_sound(self):
        current_state = self.manager.sound_manager.sound_enabled
        new_state = not current_state
        
        self.manager.sound_manager.toggle_sound(new_state)
        
        if new_state:
            self.sound_btn.configure(text="🔊 SUARA AKTIF", style='Primary.TButton')
            messagebox.showinfo("Suara", "Notifikasi suara diaktifkan!")
        else:
            self.sound_btn.configure(text="🔇 SUARA NONAKTIF", style='Danger.TButton')
            messagebox.showinfo("Suara", "Notifikasi suara dinonaktifkan!")
    
    def change_medicine_sound(self):
        selection = self.medicines_tree.selection()
        if not selection:
            messagebox.showwarning("Peringatan", "Pilih obat terlebih dahulu!")
            return
        
        item = selection[0]
        medicine_name = self.medicines_tree.item(item)['values'][0]
        
        sound_dialog = tk.Toplevel(self.root)
        sound_dialog.title("Ubah Suara Notifikasi")
        sound_dialog.geometry("300x150")
        sound_dialog.configure(bg=COLORS['bg'])
        sound_dialog.transient(self.root)
        sound_dialog.grab_set()
        
        ttk.Label(sound_dialog, text=f"Pilih suara untuk {medicine_name}:").pack(pady=10)
        
        sound_var = tk.StringVar()
        sound_combo = ttk.Combobox(sound_dialog, textvariable=sound_var, state="readonly")
        sound_combo['values'] = self.manager.get_available_sounds()
        sound_combo.pack(pady=5)
        
        if sound_combo['values']:
            sound_combo.set(sound_combo['values'][0])
        
        def apply_sound():
            new_sound = sound_var.get()
            if new_sound:
                if self.manager.current_person:
                    for medicine in self.manager.current_person.medicines:
                        if medicine.name == medicine_name:
                            medicine.custom_sound = new_sound
                            self.manager.save_data()
                            self.refresh_medicines_list()
                            messagebox.showinfo("Sukses", f"Suara untuk {medicine_name} diubah menjadi: {new_sound}")
                            break
                sound_dialog.destroy()
        
        ttk.Button(sound_dialog, text="Terapkan", command=apply_sound, style='Primary.TButton').pack(pady=10)
    
    def save_person_info(self):
        try:
            name = self.name_var.get().strip()
            age_str = self.age_entry.get().strip()
            condition = self.condition_var.get().strip()
            
            if not name:
                messagebox.showerror("Error", "Nama lansia harus diisi!")
                return
            
            age = 0
            if age_str:
                try:
                    age = int(age_str)
                except ValueError:
                    messagebox.showerror("Error", "Usia harus berupa angka!")
                    return
            
            # Set atau update lansia
            self.manager.set_current_person(name, age, condition)
            
            self.update_current_person_display()
            messagebox.showinfo("Sukses", "Informasi lansia berhasil disimpan!")
            
            # Refresh daftar nama
            self.refresh_elderly_names()
            
        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan: {str(e)}")
    
    def add_medicine(self):
        # Periksa apakah ada lansia aktif
        if not self.manager.current_person or not self.manager.current_person.name:
            messagebox.showerror("Error", "Pilih atau buat lansia terlebih dahulu!")
            return
        
        name = self.med_name_var.get()
        dosage = self.dosage_entry.get()
        schedule_str = self.schedule_entry.get()
        description = self.desc_entry.get()
        with_food = self.with_food_var.get()
        sound_enabled = self.sound_enabled_var.get()
        custom_sound = self.sound_combobox.get()
        
        if not name or not dosage or not schedule_str:
            messagebox.showerror("Error", "Nama obat, dosis, dan jadwal harus diisi!")
            return
        
        try:
            schedule = [time.strip() for time in schedule_str.split(',')]
            for time_str in schedule:
                datetime.datetime.strptime(time_str, "%H:%M")
        except ValueError:
            messagebox.showerror("Error", "Format jadwal tidak valid! Gunakan format HH:MM")
            return
        
        medicine = Medicine(name, dosage, schedule, description, with_food, sound_enabled, custom_sound)
        self.manager.add_medicine(medicine)
        
        # Clear form kecuali nama obat
        self.dosage_entry.delete(0, tk.END)
        self.schedule_entry.delete(0, tk.END)
        self.desc_entry.delete(0, tk.END)
        
        # Refresh daftar nama obat
        self.refresh_medicine_names()
        self.refresh_medicines_list()
        messagebox.showinfo("Sukses", "Obat berhasil ditambahkan!")
    
    def remove_medicine(self):
        selection = self.medicines_tree.selection()
        if not selection:
            messagebox.showwarning("Peringatan", "Pilih obat yang akan dihapus!")
            return
        
        item = selection[0]
        medicine_name = self.medicines_tree.item(item)['values'][0]
        
        if messagebox.askyesno("Konfirmasi", f"Hapus {medicine_name}?"):
            self.manager.remove_medicine(medicine_name)
            self.refresh_medicines_list()
            self.refresh_medicine_names()
    
    def mark_as_taken(self):
        selection = self.medicines_tree.selection()
        if not selection:
            messagebox.showwarning("Peringatan", "Pilih obat yang sudah diminum!")
            return
        
        item = selection[0]
        medicine_name = self.medicines_tree.item(item)['values'][0]
        current_time = datetime.datetime.now().strftime("%H:%M")
        
        self.manager.record_medicine_taken(medicine_name, current_time)
        self.refresh_history()
        messagebox.showinfo("Sukses", f"{medicine_name} ditandai sudah diminum!")
    
    def refresh_medicines_list(self):
        for item in self.medicines_tree.get_children():
            self.medicines_tree.delete(item)
        
        if self.manager.current_person:
            for medicine in self.manager.current_person.medicines:
                schedule_str = ", ".join(medicine.schedule)
                sound_status = "🔊" if medicine.sound_enabled else "🔇"
                self.medicines_tree.insert('', tk.END, values=(
                    medicine.name,
                    medicine.dosage,
                    schedule_str,
                    medicine.custom_sound,
                    sound_status
                ))
    
    def refresh_history(self):
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        if self.manager.current_person:
            for medicine in self.manager.current_person.medicines:
                for record in medicine.history[-10:]:
                    timestamp = datetime.datetime.fromisoformat(record['timestamp'])
                    time_str = timestamp.strftime("%Y-%m-%d %H:%M")
                    self.history_tree.insert('', tk.END, values=(
                        time_str,
                        medicine.name,
                        medicine.dosage,
                        "✓ Sudah diminum"
                    ))
    
    def show_reminder(self, medicine, current_time):
        def create_reminder_window():
            reminder_win = tk.Toplevel(self.root)
            reminder_win.title("⏰ PENGINGAT OBAT! 🔊")
            reminder_win.geometry("400x250")
            reminder_win.configure(bg=COLORS['warning'])
            reminder_win.attributes('-topmost', True)
            
            reminder_win.transient(self.root)
            reminder_win.grab_set()
            
            # Tambahkan informasi lansia
            person_info = ""
            if self.manager.current_person:
                person_info = f"Untuk: {self.manager.current_person.name}"
            
            def play_repeating_sound():
                if hasattr(reminder_win, 'sound_active') and reminder_win.sound_active:
                    if medicine.sound_enabled and self.manager.sound_manager.sound_enabled:
                        self.manager.sound_manager.play_sound(medicine.custom_sound)
                    reminder_win.after(5000, play_repeating_sound)
            
            reminder_win.sound_active = True
            
            ttk.Label(reminder_win, text="⏰ WAKTU MINUM OBAT! 🔊", 
                     font=('Arial', 14, 'bold'), background=COLORS['warning']).pack(pady=5)
            
            if person_info:
                ttk.Label(reminder_win, text=person_info, 
                         font=('Arial', 11, 'italic'), background=COLORS['warning']).pack(pady=2)
            
            info_text = f"""
Nama Obat: {medicine.name}
Dosis: {medicine.dosage}
Waktu: {current_time}
{'✓ Diminum setelah makan' if medicine.with_food else ''}
            """
            
            ttk.Label(reminder_win, text=info_text, background=COLORS['warning'], 
                     font=('Arial', 11)).pack(pady=5)
            
            def mark_and_close():
                reminder_win.sound_active = False
                self.manager.record_medicine_taken(medicine.name, current_time)
                self.refresh_history()
                reminder_win.destroy()
            
            def snooze():
                reminder_win.sound_active = False
                reminder_win.destroy()
                self.root.after(300000, lambda: self.show_reminder(medicine, current_time))
            
            btn_frame = ttk.Frame(reminder_win)
            btn_frame.pack(pady=15)
            
            ttk.Button(btn_frame, text="✓ Sudah Diminum", 
                      command=mark_and_close, style='Success.TButton').pack(side=tk.LEFT, padx=5)
            
            ttk.Button(btn_frame, text="⏰ Tunda 5 menit", 
                      command=snooze, style='Primary.TButton').pack(side=tk.LEFT, padx=5)
            
            play_repeating_sound()
        
        self.root.after(0, create_reminder_window)

def main():
    root = tk.Tk()
    app = MedicineGUI(root)
    
    try:
        root.mainloop()
    finally:
        app.reminder.stop()

if __name__ == "__main__":
    main()