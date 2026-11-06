"""Optional ComfyUI Art Studio: user-driven local SDXL generation in Campaign Forge.

No model weights, node plugins, API keys or remote calls are bundled. ComfyUI
must be running independently. The SDXL workflow is an approved local preset.
"""
from __future__ import annotations

import io
import os
import queue
import tempfile
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from PIL import Image, ImageTk

from comfy_bridge import ComfyLocalClient, find_local_comfy, make_sdxl_workflow

# Safe, tested-core-node presets, not a promise that AI will produce usable grids.
PRESETS = {
    'Map background': (
        'Detailed hand-painted fantasy tabletop world map on aged parchment. '
        'Mountains, forests, winding roads, rivers, villages, dramatic terrain, '
        'beautiful illustrated cartography, top-down overview, no words or labels.'
    ),
    'Landscape / location': (
        'Wide fantasy landscape painting, a misty ancient forest surrounding a '
        'stone castle by a river, cinematic atmospheric light, environmental '
        'concept art, rich details and depth.'
    ),
    'Character portrait': (
        'Fantasy character portrait, wandering adventurer wearing practical '
        'travel clothes and leather armor, expressive face, hand-painted '
        'tabletop roleplaying character illustration, detailed backdrop.'
    ),
    'Cartography prop': (
        'Single isolated medieval fantasy treasure chest, top-down tabletop '
        'game prop, centered on a simple neutral background, clean edges, '
        'detailed painted object, no text.'
    ),
}
DEFAULT_NEGATIVE = 'letters, words, labels, numbers, text, watermark, signature, blurry, low quality'
IMAGE_DIMENSIONS = ('1024 x 1024', '1024 x 768', '768 x 1024', '768 x 768', '512 x 512')
POLL_INTERVAL_S = 2.0
MAX_WAIT_S = 900.0
MAX_PIXELS = 20_000_000


def validate_generated_image(data: bytes) -> Image.Image:
    """Decode Comfy's result, with a size ceiling before any Archive write."""
    if not isinstance(data, bytes) or not data:
        raise ValueError('No image was returned by ComfyUI.')
    with Image.open(io.BytesIO(data)) as original:
        if original.format not in ('PNG', 'JPEG', 'WEBP'):
            raise ValueError('ComfyUI returned an unsupported image format.')
        w, h = original.size
        if w < 32 or h < 32 or w * h > MAX_PIXELS:
            raise ValueError('ComfyUI image size is outside the supported range.')
        original.load()
        return original.convert('RGB').copy()


def create_image_workflow(prompt, negative, checkpoint, dimensions, steps, cfg, seed=''):
    """Convert Art Studio fields to the validated, bundled SDXL API graph."""
    try:
        width, height = [int(part.strip()) for part in dimensions.lower().split('x')]
    except (ValueError, AttributeError) as exc:
        raise ValueError('Select a valid image resolution.') from exc
    try:
        s = int(steps)
        c = float(cfg)
        rand_seed = int(seed) if str(seed).strip() else None
    except ValueError as exc:
        raise ValueError('Steps, CFG and optional seed must be numbers.') from exc
    return make_sdxl_workflow(prompt, negative=negative, checkpoint=checkpoint,
                              width=width, height=height, steps=s, cfg=c, seed=rand_seed)


class ComfyStudio(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_app = parent
        self.title('Campaign Forge | AI Art Studio (Local ComfyUI)')
        self.geometry('1000x700')
        self.minsize(820, 620)
        self.transient(parent)
        self.events = queue.Queue()
        self._closed = threading.Event()
        self._cancel_generation = threading.Event()
        self._job_number = 0
        self._busy = False
        self._connecting = False
        self.client = None
        self.selected_image = None
        self.preview_photo = None
        self._archive_id = None
        self._build()
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.after(100, self._drain_events)
        # Connection checks are local-only and lightweight. No generation is sent.
        self.after(300, self.connect)

    def _build(self):
        # The studio must remain usable on 1366x768 laptops and at high DPI.
        # A vertically scrollable frame keeps Generate/Save controls reachable.
        palette = ttk.Style(self)
        palette.configure('Studio.TLabelframe', background='#1B2A35', bordercolor='#39505E')
        palette.configure('Studio.TLabelframe.Label', background='#1B2A35', foreground='#EAF0F0')
        outer = ttk.Frame(self)
        outer.pack(fill='both', expand=True)
        canvas = tk.Canvas(outer, background='#121B25', highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)
        content = ttk.Frame(canvas, padding=16)
        content_id = canvas.create_window((0, 0), anchor='nw', window=content)
        content.bind('<Configure>', lambda event: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>', lambda event: canvas.itemconfigure(content_id, width=event.width))
        self.content_canvas = canvas
        ttk.Label(content, text='AI Art Studio — local SDXL', style='Section.TLabel').pack(anchor='w')
        ttk.Label(content, text='ComfyUI runs separately on this computer. Campaign Forge sends the built-in '
                  'SDXL workflow only when you click Generate. No cloud API or subscription is used.',
                  style='Muted.TLabel', wraplength=940).pack(anchor='w', pady=(4, 12))

        connection = ttk.LabelFrame(content, text='1. Connect to your running ComfyUI instance', padding=8, style='Studio.TLabelframe')
        connection.pack(fill='x', pady=(0, 10))
        bar = ttk.Frame(connection)
        bar.pack(fill='x')
        ttk.Label(bar, text='Server:').pack(side='left')
        self.address = tk.StringVar(value='Auto (ports 8188 or 8000)')
        ttk.Entry(bar, textvariable=self.address, width=38).pack(side='left', fill='x', expand=True, padx=8)
        self.connect_button = ttk.Button(bar, text='Find / Connect', command=self.connect)
        self.connect_button.pack(side='left')
        self.connection_note = tk.StringVar(value='Not connected yet. Open ComfyUI Desktop and start your instance.')
        ttk.Label(connection, textvariable=self.connection_note, style='Muted.TLabel', wraplength=950).pack(anchor='w', pady=(5, 0))

        columns = ttk.Frame(content)
        columns.pack(fill='both', expand=True)
        left = ttk.Frame(columns, padding=(0, 7, 12, 0))
        left.pack(side='left', fill='both', expand=True)
        right = ttk.Frame(columns)
        right.pack(side='right', fill='both', expand=True)

        ttk.Label(left, text='2. Describe your artwork', style='Section.TLabel').pack(anchor='w')
        row = ttk.Frame(left)
        row.pack(fill='x', pady=(5, 7))
        ttk.Label(row, text='Artwork type:').pack(side='left')
        self.preset = tk.StringVar(value='Map background')
        ttk.Combobox(row, textvariable=self.preset, values=tuple(PRESETS), state='readonly', width=25).pack(side='left', padx=8)
        ttk.Button(row, text='Use starter prompt', command=self.fill_preset).pack(side='right')

        ttk.Label(left, text='Positive prompt — what should appear:').pack(anchor='w')
        self.positive = tk.Text(left, height=6, wrap='word', undo=True, bg='#243440',
                                fg='#EAF0F0', insertbackground='#EAF0F0', selectbackground='#276D74')
        self.positive.pack(fill='both', expand=True, pady=(4, 10))
        self.positive.insert('1.0', PRESETS['Map background'])
        ttk.Label(left, text='Negative prompt — what should be avoided:').pack(anchor='w')
        self.negative = tk.Text(left, height=4, wrap='word', undo=True, bg='#243440',
                                fg='#EAF0F0', insertbackground='#EAF0F0', selectbackground='#276D74')
        self.negative.pack(fill='both', expand=True, pady=(4, 10))
        self.negative.insert('1.0', DEFAULT_NEGATIVE)

        settings = ttk.LabelFrame(left, text='3. Model and generation settings', padding=8, style='Studio.TLabelframe')
        settings.pack(fill='x', pady=(0, 9))
        ttk.Label(settings, text='Checkpoint (found in running ComfyUI):').grid(row=0, column=0, columnspan=4, sticky='w')
        self.checkpoint = tk.StringVar(value='')
        self.checkpoints = ttk.Combobox(settings, state='readonly', textvariable=self.checkpoint)
        self.checkpoints.grid(row=1, column=0, columnspan=4, sticky='ew', pady=(4, 7))
        ttk.Label(settings, text='Size:').grid(row=2, column=0, sticky='w')
        ttk.Label(settings, text='Steps:').grid(row=2, column=1, sticky='w')
        ttk.Label(settings, text='CFG:').grid(row=2, column=2, sticky='w')
        ttk.Label(settings, text='Seed (optional):').grid(row=2, column=3, sticky='w')
        self.dimensions = tk.StringVar(value='1024 x 1024')
        ttk.Combobox(settings, values=IMAGE_DIMENSIONS, textvariable=self.dimensions, state='readonly', width=12).grid(row=3, column=0, sticky='ew', padx=(0, 5))
        self.steps = tk.StringVar(value='25')
        ttk.Entry(settings, textvariable=self.steps, width=5).grid(row=3, column=1, sticky='ew', padx=(0, 5))
        self.cfg = tk.StringVar(value='7')
        ttk.Entry(settings, textvariable=self.cfg, width=5).grid(row=3, column=2, sticky='ew', padx=(0, 5))
        self.seed = tk.StringVar(value='')
        ttk.Entry(settings, textvariable=self.seed, width=16).grid(row=3, column=3, sticky='ew')
        settings.columnconfigure(0, weight=1)
        settings.columnconfigure(3, weight=1)
        ttk.Label(settings, text='Default settings match your successful SDXL test. Blank seed = random.',
                  style='Muted.TLabel', wraplength=395).grid(row=4, column=0, columnspan=4, sticky='w', pady=(7, 0))

        actions = ttk.Frame(left)
        actions.pack(fill='x')
        self.generate_button = ttk.Button(actions, text='Generate image', state='disabled', command=self.generate, style='Accent.TButton')
        self.generate_button.pack(side='left', fill='x', expand=True)
        self.stop_button = ttk.Button(actions, text='Stop waiting', state='disabled', command=self.stop_waiting)
        self.stop_button.pack(side='right', padx=(8, 0))
        self.busy_bar = ttk.Progressbar(left, mode='indeterminate')
        self.busy_bar.pack(fill='x', pady=(9, 4))
        self.status = tk.StringVar(value='Ready to connect. No images have been generated in Campaign Forge yet.')
        ttk.Label(left, textvariable=self.status, style='Muted.TLabel', wraplength=430).pack(anchor='w')

        ttk.Label(right, text='Generated image preview', style='Section.TLabel').pack(anchor='w')
        self.preview = ttk.Label(right, text='Your generated image appears here.', anchor='center', justify='center')
        self.preview.pack(fill='both', expand=True, pady=(7, 12))
        controls = ttk.Frame(right)
        controls.pack(fill='x', pady=(0, 4))
        self.save_button = ttk.Button(controls, text='Save PNG as…', state='disabled', command=self.save_png)
        self.save_button.pack(side='left', fill='x', expand=True, padx=(0, 4))
        self.archive_button = ttk.Button(controls, text='Add to The Archives', state='disabled', command=self.add_to_archives)
        self.archive_button.pack(side='left', fill='x', expand=True)
        ttk.Label(right, text='Generated images may contain visual errors or unwanted lettering. '
                  'Review them before inserting into a campaign. Stop waiting does not cancel a ComfyUI GPU job.',
                  style='Muted.TLabel', wraplength=470).pack(anchor='w', pady=(5, 0))

    def fill_preset(self):
        # Explicit button so selecting a category never destroys hand-written prompts.
        self.positive.delete('1.0', 'end')
        self.positive.insert('1.0', PRESETS.get(self.preset.get(), PRESETS['Map background']))

    def _run_worker(self, fn, *args):
        threading.Thread(target=fn, args=args, daemon=True).start()

    def connect(self):
        if self._busy or self._connecting:
            return
        self._connecting = True
        entry = self.address.get().strip()
        self.connection_note.set('Checking local ComfyUI service…')
        self.connect_button.configure(state='disabled')
        self.generate_button.configure(state='disabled')
        self._run_worker(self._connection_worker, entry)

    def _connection_worker(self, entry):
        try:
            if not entry or entry.lower().startswith('auto'):
                client = find_local_comfy()
            else:
                client = ComfyLocalClient(entry)
                client.system_stats()
            models = [name for name in client.checkpoints() if name.lower().endswith('.safetensors')]
            self.events.put(('connected', client, models))
        except Exception as exc:
            self.events.put(('connection_failed', str(exc)))

    def generate(self):
        if self.client is None or self._busy:
            return
        prompt = self.positive.get('1.0', 'end-1c').strip()
        negative = self.negative.get('1.0', 'end-1c').strip()
        try:
            graph = create_image_workflow(prompt, negative, self.checkpoint.get(),
                                          self.dimensions.get(), self.steps.get(), self.cfg.get(), self.seed.get())
        except (ValueError, TypeError) as exc:
            messagebox.showwarning('Check image settings', str(exc), parent=self)
            return
        if not messagebox.askyesno('Generate with local ComfyUI?',
                                   'Submit this image request to your running LOCAL ComfyUI instance?\n\n'
                                   'Your GPU will work until generation completes. No cloud API is called by Campaign Forge.',
                                   parent=self):
            return
        self._job_number += 1
        job = self._job_number
        self._cancel_generation = threading.Event()
        self._busy = True
        self.selected_image = None
        self._archive_id = None
        self.preview_photo = None
        self.preview.configure(image='', text='Generating locally…')
        self.generate_button.configure(state='disabled')
        self.save_button.configure(state='disabled')
        self.archive_button.configure(state='disabled')
        self.stop_button.configure(state='normal')
        self.busy_bar.start(12)
        self.status.set('Sending approved SDXL workflow to ComfyUI…')
        self._run_worker(self._generation_worker, job, self.client, graph, self._cancel_generation)

    def _generation_worker(self, job, client, graph, stopped):
        try:
            prompt_id = client.submit(graph)
            self.events.put(('job_started', job, prompt_id))
            deadline = time.monotonic() + MAX_WAIT_S
            while time.monotonic() < deadline and not stopped.is_set() and not self._closed.is_set():
                result = client.image_output(prompt_id)
                if result is not None:
                    image = validate_generated_image(client.download_image(result))
                    self.events.put(('finished', job, image))
                    return
                if stopped.wait(POLL_INTERVAL_S):
                    return
            if not stopped.is_set() and not self._closed.is_set():
                raise TimeoutError('ComfyUI has not returned an image after 15 minutes. Check its queue; the GPU job may still be running.')
        except Exception as exc:
            if not stopped.is_set():
                self.events.put(('generation_failed', job, str(exc)))

    def stop_waiting(self):
        if self._busy:
            self._cancel_generation.set()
            self._job_number += 1
            self._busy = False
            self.busy_bar.stop()
            self.stop_button.configure(state='disabled')
            self.generate_button.configure(state='normal' if self.client else 'disabled')
            self.status.set('Stopped waiting. An already queued ComfyUI job may continue on the GPU.')

    def _drain_events(self):
        if self._closed.is_set():
            return
        while True:
            try:
                msg = self.events.get_nowait()
            except queue.Empty:
                break
            kind = msg[0]
            if kind == 'connected':
                self._connecting = False
                self.client = msg[1]
                models = msg[2]
                self.address.set(self.client.base_url)
                self.checkpoints.configure(values=models)
                preferred = next((m for m in models if m.lower() == 'sd_xl_base_1.0.safetensors'), None)
                if preferred:
                    self.checkpoint.set(preferred)
                elif models:
                    self.checkpoint.set(models[0])
                else:
                    self.checkpoint.set('')
                self.connection_note.set(f'Connected locally: {self.client.base_url} — {len(models)} checkpoint(s) found.' +
                                         ('' if models else ' Install an SDXL checkpoint and restart the instance.'))
                self.generate_button.configure(state='normal' if models and not self._busy else 'disabled')
                self.connect_button.configure(state='normal')
            elif kind == 'connection_failed':
                self._connecting = False
                self.client = None
                self.checkpoints.configure(values=())
                self.checkpoint.set('')
                self.connect_button.configure(state='normal')
                self.connection_note.set('Connection failed: ' + msg[1] + '  Check that ComfyUI Desktop has a running instance.')
            elif kind == 'job_started' and msg[1] == self._job_number:
                self.status.set('Generation queued on ComfyUI. Waiting for the image (up to 15 minutes)…')
            elif kind == 'finished' and msg[1] == self._job_number:
                self._busy = False
                self.busy_bar.stop()
                self.stop_button.configure(state='disabled')
                self.generate_button.configure(state='normal')
                self.selected_image = msg[2]
                self._show_preview(self.selected_image)
                self.save_button.configure(state='normal')
                self.archive_button.configure(state='normal')
                self.status.set('Image generated. Preview it, save as PNG, or add to The Archives.')
            elif kind == 'generation_failed' and msg[1] == self._job_number:
                self._busy = False
                self.busy_bar.stop()
                self.stop_button.configure(state='disabled')
                self.generate_button.configure(state='normal')
                self.status.set('Image generation failed: ' + msg[2])
                messagebox.showerror('ComfyUI image generation', msg[2], parent=self)
        self.after(100, self._drain_events)

    def _show_preview(self, image):
        scaled = image.copy()
        scaled.thumbnail((460, 470), Image.Resampling.LANCZOS)
        self.preview_photo = ImageTk.PhotoImage(scaled)
        self.preview.configure(image=self.preview_photo, text='')

    def save_png(self):
        if self.selected_image is None:
            return
        destination = filedialog.asksaveasfilename(parent=self, title='Save generated image',
                  defaultextension='.png', initialfile='CampaignForge-Generated.png',
                  filetypes=[('PNG image', '*.png')])
        if not destination:
            return
        try:
            self.selected_image.save(destination, format='PNG')
            self.status.set('Saved generated image: ' + str(destination))
        except OSError as exc:
            messagebox.showerror('Save image failed', str(exc), parent=self)

    def add_to_archives(self):
        if self.selected_image is None:
            return
        app = self.parent_app
        if not messagebox.askyesno('Add to The Archives?',
            'Copy this generated image into the CURRENT CAMPAIGN Archives?\n\n'
            'This does not automatically overwrite or replace an existing map.', parent=self):
            return
        try:
            with tempfile.TemporaryDirectory(prefix='CampaignForge-Art-') as folder:
                basename = 'CampaignForge-' + self.preset.get().replace(' ', '-').replace('/', '-') + '.png'
                filepath = Path(folder) / basename
                self.selected_image.save(filepath, format='PNG')
                project_id = app.data.get('project_id', '')
                ident = app.archive.add(filepath, 'campaign', project_id,
                                        category='Generated ' + self.preset.get())
            self._archive_id = ident
            app.archive_refresh()
            self.archive_button.configure(state='disabled')
            self.status.set('Image copied into The Archives for this campaign.')
            if self.preset.get() == 'Map background':
                active_map = app.selected_map()
                if active_map is not None and messagebox.askyesno(
                    'Use as map background?',
                    'Apply this generated image to the currently selected map?\n'
                    'It will replace the map background link, but not delete the previous archived image.', parent=self):
                    active_map['background_archive_id'] = ident
                    app.draw_map()
                    app.mark_dirty()
                    self.status.set('Image archived and added as the map background. Save your campaign to retain the change.')
        except Exception as exc:
            messagebox.showerror('Add to Archives failed', str(exc), parent=self)

    def close(self):
        self._closed.set()
        self._cancel_generation.set()
        self.destroy()


def open_comfy_studio(parent):
    """Open a user-controlled, model-optional Art Studio window."""
    return ComfyStudio(parent)
