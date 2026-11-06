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
    """Existing ComfyUI checkpoint folders, not guessed model installations.

    Supports current Comfy Desktop shared storage, older Desktop installs,
    and the classic Documents/ComfyUI layout. Custom drives are supported by
    the manual picker; we deliberately do not crawl users' disks.
    """
    home = Path(home) if home is not None else Path.home()
    local = Path(localappdata) if localappdata is not None else Path(os.environ.get('LOCALAPPDATA') or home / 'AppData' / 'Local')
    roaming = Path(appdata) if appdata is not None else Path(os.environ.get('APPDATA') or home / 'AppData' / 'Roaming')
    model_roots = [
        local / 'Comfy-Desktop' / 'ComfyUI-Shared' / 'models',
        home / 'ComfyUI-Shared' / 'models',
        home / 'Documents' / 'ComfyUI' / 'models',
        roaming / 'ComfyUI' / 'models',
    ]
    results = []
    seen = set()
    for root in model_roots:
        checkpoint = root / 'checkpoints'
        try:
            if not checkpoint.is_dir():
                continue
            resolved = checkpoint.resolve()
        except OSError:
            continue
        key = str(resolved).casefold()
        if key not in seen:
            results.append(resolved)
            seen.add(key)
    return results


def checkpoints_help_text():
    return (
        'Comfy Desktop: open Settings > Storage > Shared Models, then click the folder icon '
        'beside the PRIMARY models directory. Open its checkpoints subfolder and choose it here.\n\n'
        'Windows default often used by newer Comfy Desktop:\n'
        '%LOCALAPPDATA%\\Comfy-Desktop\\ComfyUI-Shared\\models\\checkpoints\n\n'
        'Older installs may use %USERPROFILE%\\ComfyUI-Shared\\models\\checkpoints, '
        'and portable ComfyUI stores checkpoints inside its own ComfyUI\\models folder. '
        'If ComfyUI uses a custom drive/folder, choose it manually.\n\n'
        'Choose a FOLDER named checkpoints, not an individual .safetensors file. '
        'Only download SDXL if you want that additional model; if it is already installing, let it finish. '
        'Campaign Forge currently downloads models but does not send generation jobs to ComfyUI.'
    )


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
        'User-Agent':'CampaignForge/1.0.0 (optional-model-download)',
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
          'into the ComfyUI checkpoints folder you choose. Model generation currently runs in ComfyUI; '
          'direct in-app image generation is not part of this release. No download starts without your approval.')
    ttk.Label(content,text=text,style='Muted.TLabel',wraplength=690,justify='left').pack(anchor='w',pady=(0,12))
    links=ttk.Frame(content);links.pack(fill='x',pady=5)
    ttk.Button(links,text='1. Install ComfyUI (official website)',command=lambda:webbrowser.open(COMFY_DOWNLOAD)).pack(side='left')
    ttk.Button(links,text='Model card and license',command=lambda:webbrowser.open(MODEL_PAGE)).pack(side='left',padx=8)
    ttk.Label(content,text='License: CreativeML Open RAIL++-M. Review the model license before use.',style='Muted.TLabel').pack(anchor='w',pady=6)
    selection=ttk.Frame(content);selection.pack(fill='x',pady=8)
    ttk.Label(selection,text='2. ComfyUI models/checkpoints folder (folder, not a model file):').pack(anchor='w',pady=(0,5))
    path=tk.StringVar(value='')
    ttk.Entry(selection,textvariable=path,state='readonly').pack(side='left',fill='x',expand=True)
    ttk.Button(selection,text='Choose folder…',command=lambda:path.set(filedialog.askdirectory(parent=dlg,title='Choose your ComfyUI models/checkpoints folder') or path.get())).pack(side='right',padx=6)
    finder=ttk.Frame(content);finder.pack(fill='x',pady=(0,4))
    def find_models():
        matches=candidate_checkpoint_dirs()
        if len(matches)==1:
            path.set(str(matches[0]))
            messagebox.showinfo('ComfyUI models folder',f'Found a checkpoint folder:\n{matches[0]}\n\nConfirm this is the folder used by your active ComfyUI installation.',parent=dlg)
        elif len(matches)>1:
            # Never silently pick the wrong installation when more than one exists.
            messagebox.showinfo('Multiple folders found','Found these checkpoint directories:\n\n'+ '\n'.join(str(p) for p in matches) + '\n\nUse Choose folder… to select the one listed in Comfy Desktop > Settings > Storage.',parent=dlg)
        else:
            messagebox.showinfo('Models folder not detected',checkpoints_help_text(),parent=dlg)
    ttk.Button(finder,text='Find models folder',command=find_models).pack(side='left')
    ttk.Button(finder,text='Where is it in Comfy Desktop?',command=lambda:messagebox.showinfo('Locate checkpoints',checkpoints_help_text(),parent=dlg)).pack(side='left',padx=8)
    progress=tk.DoubleVar(value=0)
    bar=ttk.Progressbar(content,variable=progress,maximum=100);bar.pack(fill='x',pady=(12,5))
    status=tk.StringVar(value='Not downloaded. Install ComfyUI first and select its checkpoints folder.')
    ttk.Label(content,textvariable=status,style='Muted.TLabel',wraplength=685).pack(anchor='w')
    buttons=ttk.Frame(content);buttons.pack(fill='x',side='bottom',pady=7)
    cancel_event=threading.Event();running={'value':False}
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
    dlg.protocol('WM_DELETE_WINDOW',stop)
    return dlg
