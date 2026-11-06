"""In-app paged PDF proof. Temporary previews never fill the user's Downloads folder."""
from __future__ import annotations
import copy, tempfile
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from pdf_book import export_book


def preview_campaign(parent, campaign, archive=None, section_id=None, node_index=None):
    import pypdfium2 as pdfium
    data=copy.deepcopy(campaign)
    outline=data.get('book_outline') or {}
    if section_id:
        sections=[s for s in outline.get('sections',[]) if s.get('id')==section_id]
        if not sections:raise ValueError('The selected section no longer exists.')
        if node_index is not None:
            nodes=sections[0]['nodes']
            if node_index<0 or node_index>=len(nodes):raise ValueError('Selected entry has moved.')
            sections[0]['nodes']=[nodes[node_index]]
        outline['sections']=sections
        data['book_outline']=outline
    directory=tempfile.TemporaryDirectory(prefix='campaign-forge-proof-')
    path=Path(directory.name)/'book-proof.pdf'
    try:
        export_book(data,str(path),archive=archive)
        doc=pdfium.PdfDocument(str(path))
    except Exception:
        directory.cleanup();raise
    window=tk.Toplevel(parent);window.title('Campaign Forge — Book Preview');window.geometry('880x850');window.minsize(520,470)
    window.transient(parent)
    bar=ttk.Frame(window,padding=10);bar.pack(fill='x')
    page=tk.IntVar(value=0);zoom=tk.DoubleVar(value=0.95)
    label=ttk.Label(bar,text='');label.pack(side='left',padx=(4,14))
    ttk.Label(bar,text='Zoom').pack(side='left');ttk.Combobox(bar,state='readonly',textvariable=zoom,
                 values=[0.6,0.75,0.95,1.15,1.4],width=6).pack(side='left',padx=8)
    stage=ttk.Frame(window);stage.pack(fill='both',expand=True)
    canvas=tk.Canvas(stage,bg='#151b22',highlightthickness=0);canvas.pack(side='left',fill='both',expand=True)
    vs=ttk.Scrollbar(stage,orient='vertical',command=canvas.yview);vs.pack(side='right',fill='y');canvas.configure(yscrollcommand=vs.set)
    canvas.bind('<MouseWheel>',lambda ev:canvas.yview_scroll(-int(ev.delta/120),'units'))
    state={'image':None}
    def redraw(*_):
        if not window.winfo_exists():return
        n=page.get();scale=zoom.get()
        if n<0 or n>=len(doc):return
        pdf_page=doc[n]
        try:
            bitmap=pdf_page.render(scale=scale*1.45)
            try: img=bitmap.to_pil().convert('RGB')
            finally: bitmap.close()
        finally: pdf_page.close()
        state['image']=ImageTk.PhotoImage(img,master=window)
        canvas.delete('all');canvas.create_image(18,18,image=state['image'],anchor='nw')
        canvas.configure(scrollregion=(0,0,img.width+36,img.height+36));canvas.yview_moveto(0)
        label.configure(text=f'Page {n+1} of {len(doc)}')
    def go(offset):page.set(min(max(0,page.get()+offset),len(doc)-1));redraw()
    ttk.Button(bar,text='◀ Previous',command=lambda:go(-1)).pack(side='left')
    ttk.Button(bar,text='Next ▶',command=lambda:go(1)).pack(side='left',padx=5)
    def changed(*_):redraw()
    zoom.trace_add('write',changed)
    def on_close():
        doc.close();directory.cleanup();window.destroy()
    window.protocol('WM_DELETE_WINDOW',on_close)
    redraw()
    return window
