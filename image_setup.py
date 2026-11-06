"""Optional, transparent image-model installer for Windows ComfyUI users.

Only downloads the selected, official SDXL model to a user-picked directory.
Does not install system software or silently execute downloaded programs.
"""
from __future__ import annotations
import hashlib
import os
from pathlib import Path
import urllib.request, urllib.error, webbrowser, threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

COMFY_DOWNLOAD = 'https://www.comfy.org/download'
MODEL_PAGE = 'https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0'
MODEL_URL = MODEL_PAGE + '/resolve/main/sd_xl_base_1.0.safetensors'
MODEL_FILE = 'sd_xl_base_1.0.safetensors'
MODEL_SHA256 = '31e35c80fc4829d14f90153f4c74cd59c90b779f6afe05a74cd6120b893f7e5b'
MODEL_SIZE_GB = 6.94


def candidate_checkpoint_dirs(home=None, localappdata=None, appdata=None):
    """Find existing common ComfyUI folders without scanning entire drives."""
    home = Path(home) if home is not None else Path.home()
    local = Path(localappdata) if localappdata is not None else Path(os.environ.get('LOCALAPPDATA') or home / 'AppData' / 'Local')
    roaming = Path(appdata) if appdata is not None else Path(os.environ.get('APPDATA') or home / 'AppData' / 'Roaming')
    roots = [local/'Comfy-Desktop'/'ComfyUI-Shared'/'models',
             home/'ComfyUI-Shared'/'models',
             home/'Documents'/'ComfyUI'/'models',
             roaming/'ComfyUI'/'models']
    found = []
    seen = set()
    for root in roots:
        checkpoint = root/'checkpoints'
        try:
            if not checkpoint.is_dir():
                continue
            resolved = checkpoint.resolve()
        except OSError:
            continue
        key = str(resolved).casefold()
        if key not in seen:
            seen.add(key)
            found.append(resolved)
    return found


def checkpoints_help_text():
    return (
        'Comfy Desktop: open Settings > Storage > Shared Models, then click the folder icon '
        'beside the PRIMARY models directory. Open its checkpoints subfolder and choose it here.\n\n'
        'Possible Windows default:\n'
        '%LOCALAPPDATA%\\Comfy-Desktop\\ComfyUI-Shared\\models\\checkpoints\n\n'
        'Older installs may use %USERPROFILE%\\ComfyUI-Shared\\models\\checkpoints. '
        'For portable ComfyUI use ComfyUI\\models\\checkpoints. '
        'For a custom installation, choose your existing checkpoints folder manually.\n\n'
        'Select the FOLDER, not an individual model file. '
        'The new Generate Image button in Cartography connects to the running ComfyUI server. '
        'This setup screen only downloads optional SDXL Base weights; it does not start jobs.'
    )


def inspect_model_status(checkpoint_names, checkpoint_dirs):
    """Find an existing SDXL installation without downloading or changing files.

    Active ComfyUI's model index is the authoritative readiness signal; local
    filenames are only hints and are not treated as integrity verification.
    Returns (state, message, detected_directory).
    """
    if any(isinstance(name, str) and Path(name.replace('\\', '/')).name.casefold() == MODEL_FILE.casefold()
           for name in (checkpoint_names or [])):
        return ('ready', 'SDXL Base is already available in the running ComfyUI instance. No download is needed.', None)
    seen = set()
    for folder in checkpoint_dirs:
        if not folder:
            continue
        directory = Path(folder)
        key = str(directory).casefold()
        if key in seen:
            continue
        seen.add(key)
        if (directory / MODEL_FILE).is_file():
            return ('found', 'SDXL Base file found on disk. It has not been re-verified here; check that your running ComfyUI instance lists this checkpoint.', directory)
        if (directory / (MODEL_FILE + '.part')).is_file():
            return ('partial', 'An unfinished SDXL download was found. Select this folder if you want to resume; do not start a second download elsewhere.', directory)
    return ('unknown', 'No SDXL checkpoint was detected in the running instance or checked folders. This does NOT prove it is absent elsewhere; select your ComfyUI checkpoints folder to check.', None)


def download_checkpoint(destination, notify, stopped, opener=None):
    """Resume if supported; hash-check before publishing the model to ComfyUI."""
    destination=Path(destination)
    if destination.name!=MODEL_FILE:raise ValueError('Unexpected checkpoint filename.')
    if not destination.parent.is_dir():raise ValueError('Choose an existing ComfyUI checkpoints directory.')
    temporary=destination.with_name(destination.name+'.part')
    if destination.exists():
        if sha256_file(destination,stopped)==MODEL_SHA256:
            notify('The SDXL model is already installed and verified.',100);return destination
        raise ValueError('An existing model file failed verification. Move or rename it before downloading.')
    existing=temporary.stat().st_size if temporary.exists() else 0
    request=urllib.request.Request(MODEL_URL,headers={
        'User-Agent':'CampaignForge/1.1.0-beta.3 (optional-model-download)',
        **({'Range':f'bytes={existing}-'} if existing else {})})
    opener=opener or urllib.request.build_opener()
    with opener.open(request,timeout=60) as response:
        status=getattr(response,'status',200)
        if existing and status!=206:
            existing=0  # server did not accept resume
        header=response.headers.get('Content-Length')
        total=existing+int(header) if header and header.isdigit() else 0
        mode='ab' if existing else 'wb'
        progress=existing
        notify('Downloading SDXL Base (6.94 GB). You may cancel and resume later.',100*progress/total if total else None)
        with temporary.open(mode) as output:
            while True:
                if stopped.is_set():raise InterruptedError('Download paused. Partial file kept for resuming.')
                block=response.read(1024*1024)
                if not block:break
                output.write(block);progress+=len(block)
                notify(f'Downloaded {progress/1e9:.2f} GB'+(f' of {total/1e9:.2f} GB' if total else ''),100*progress/total if total else None)
    notify('Verifying the complete download (this may take a few minutes)…',None)
    if sha256_file(temporary,stopped)!=MODEL_SHA256:
        raise ValueError('Downloaded checkpoint failed SHA256 verification. The .part file was retained for inspection; do not use it.')
    temporary.rename(destination)
    notify('Model verified and ready for ComfyUI.',100)
    return destination


def sha256_file(path,stopped):
    sha=hashlib.sha256()
    with Path(path).open('rb') as file:
        while chunk:=file.read(4*1024*1024):
            if stopped.is_set():raise InterruptedError('Operation cancelled.')
            sha.update(chunk)
    return sha.hexdigest()


def open_image_setup(parent):
    dlg=tk.Toplevel(parent);dlg.title('Optional local image model — SDXL + ComfyUI')
    dlg.geometry('780x490');dlg.minsize(690,450);dlg.transient(parent)
    content=ttk.Frame(dlg,padding=18);content.pack(fill='both',expand=True)
    ttk.Label(content,text='Set up local image generation',style='Section.TLabel').pack(anchor='w',pady=(0,6))
    text=('ComfyUI is a separate, free local image-generation application for Windows. '
          'Campaign Forge can download an official SDXL Base 1.0 checkpoint (~6.94 GB) '
          'into the ComfyUI checkpoints folder you choose. To generate an image in Campaign Forge, '
          'use Cartography > Generate Image with a RUNNING local ComfyUI instance. '
          'No download starts without your approval.')
    ttk.Label(content,text=text,style='Muted.TLabel',wraplength=690,justify='left').pack(anchor='w',pady=(0,12))
    links=ttk.Frame(content);links.pack(fill='x',pady=5)
    ttk.Button(links,text='1. Install ComfyUI (official website)',command=lambda:webbrowser.open(COMFY_DOWNLOAD)).pack(side='left')
    ttk.Button(links,text='Model card and license',command=lambda:webbrowser.open(MODEL_PAGE)).pack(side='left',padx=8)
    ttk.Label(content,text='License: CreativeML Open RAIL++-M. Review the model license before use.',style='Muted.TLabel').pack(anchor='w',pady=6)
    selection=ttk.Frame(content);selection.pack(fill='x',pady=8)
    ttk.Label(selection,text='2. ComfyUI models/checkpoints folder (not a model file):').pack(anchor='w',pady=(0,5))
    path=tk.StringVar(value='')
    ttk.Entry(selection,textvariable=path,state='readonly').pack(side='left',fill='x',expand=True)
    ttk.Button(selection,text='Choose folder…',command=lambda:path.set(filedialog.askdirectory(parent=dlg,title='Choose your ComfyUI models/checkpoints folder') or path.get())).pack(side='right',padx=6)
    finder=ttk.Frame(content);finder.pack(fill='x',pady=(0,4))
    def find_models():
        matches=candidate_checkpoint_dirs()
        if len(matches)==1:
            path.set(str(matches[0]))
            messagebox.showinfo('ComfyUI models folder',f'Found a folder:\n{matches[0]}\n\nVerify it is used by your active instance.',parent=dlg)
        elif len(matches)>1:
            messagebox.showinfo('Multiple folders found','ComfyUI checkpoint directories:\n\n'+ '\n'.join(map(str,matches)) + '\n\nChoose the active one using Choose folder…',parent=dlg)
        else:
            messagebox.showinfo('Models folder not detected',checkpoints_help_text(),parent=dlg)
    ttk.Button(finder,text='Find models folder',command=find_models).pack(side='left')
    ttk.Button(finder,text='Where is it in Comfy Desktop?',command=lambda:messagebox.showinfo('Locate checkpoints',checkpoints_help_text(),parent=dlg)).pack(side='left',padx=8)
    status_button=ttk.Button(finder,text='Check Model Status')
    status_button.pack(side='left',padx=8)
    progress=tk.DoubleVar(value=0)
    bar=ttk.Progressbar(content,variable=progress,maximum=100);bar.pack(fill='x',pady=(12,5))
    status=tk.StringVar(value='Model status not checked yet. Existing models are never removed by an update.')
    ttk.Label(content,textvariable=status,style='Muted.TLabel',wraplength=685).pack(anchor='w')
    buttons=ttk.Frame(content);buttons.pack(fill='x',side='bottom',pady=7)
    cancel_event=threading.Event();running={'value':False}
    checking={'value':False}
    model_ready={'value':False}

    def check_model_status():
        if checking['value'] or running['value']:
            return
        checking['value']=True
        status_button.configure(state='disabled')
        status.set('Checking the running ComfyUI instance and existing model folders…')
        folders=[path.get()] if path.get() else []
        folders.extend(candidate_checkpoint_dirs())
        def worker():
            names=[]
            try:
                from comfy_bridge import find_local_comfy
                names=find_local_comfy().checkpoints()
            except (OSError, ValueError, TimeoutError, ConnectionError):
                pass  # ComfyUI may be stopped or using another configured port.
            state, note, detected=inspect_model_status(names, folders)
            def update():
                checking['value']=False
                if not dlg.winfo_exists():
                    return
                model_ready['value']=(state=='ready')
                status.set(note)
                status_button.configure(state='normal')
                if state in ('ready', 'found'):
                    progress.set(100 if state=='ready' else 0)
                if detected and not path.get():
                    path.set(str(detected))
            try:
                dlg.after(0, update)
            except RuntimeError:
                pass
        threading.Thread(target=worker,daemon=True).start()
    status_button.configure(command=check_model_status)
    download_btn=ttk.Button(buttons,text='3. Download SDXL Base (~6.94 GB)')
    download_btn.pack(side='left')
    def stop():
        if running['value']:
            cancel_event.set();status.set('Pausing after the current transfer block…')
        else:dlg.destroy()
    ttk.Button(buttons,text='Pause / Close',command=stop).pack(side='right')
    def start():
        directory=Path(path.get()) if path.get() else None
        if not directory or directory.name.casefold()!='checkpoints' or directory.parent.name.casefold()!='models':
            messagebox.showwarning('Choose checkpoints folder','Select the ComfyUI checkpoints FOLDER, not an individual model file. Use Find models folder or Comfy Desktop > Settings > Storage > Shared Models.',parent=dlg);return
        if model_ready['value']:
            messagebox.showinfo('SDXL already installed','The running ComfyUI instance already lists SDXL Base 1.0. You do not need to download it again.',parent=dlg)
            return
        if (directory / MODEL_FILE).is_file():
            messagebox.showinfo('SDXL file already present','An SDXL checkpoint already exists in the selected folder. Use Check Model Status to confirm ComfyUI sees it; do not download another copy.',parent=dlg)
            return
        if not messagebox.askyesno('Download ~6.94 GB?',
            'You are choosing an optional third-party SDXL Base 1.0 model download.\n\nReview its model card and CreativeML Open RAIL++-M license; you are responsible for complying with that license. This download is NOT part of the Campaign Forge package. It may use ~6.94 GB of data and disk space.\n\nHave you reviewed the model terms and do you wish to download it?',parent=dlg):return
        running['value']=True;cancel_event.clear();download_btn.configure(state='disabled')
        def update(note,value):
            def ui():
                if not dlg.winfo_exists():return
                status.set(note)
                if value is not None:progress.set(min(100,max(0,value)))
            parent.after(0,ui)
        def task():
            try:download_checkpoint(directory/MODEL_FILE,update,cancel_event)
            except Exception as exc:
                error=str(exc)
                parent.after(0,lambda: status.set(error) if dlg.winfo_exists() else None)
            finally:
                def done():
                    running['value']=False
                    if dlg.winfo_exists():download_btn.configure(state='normal')
                parent.after(0,done)
        threading.Thread(target=task,daemon=True).start()
    download_btn.configure(command=start)
    dlg.after(350,check_model_status)
    dlg.protocol('WM_DELETE_WINDOW',stop)
    return dlg
