"""Campaign Forge — Windows desktop campaign-writing prototype.

Run with: python app.py
No AI account or internet connection is needed for the writing and PDF features.
"""
from __future__ import annotations

import copy
import math
import threading
import tkinter as tk
import webbrowser
import os
import sys
from pathlib import Path
from tkinter import ttk, filedialog, messagebox, simpledialog

from campaign_data import CATEGORIES, SYSTEMS, new_campaign, new_entry, new_map, sample_campaign, save_campaign, load_campaign
from reference_import import import_reference
from map_tools import PALETTE, TILE_NAMES, PROP_NAMES, render_map, export_map
from pdf_book import export_book
from ai_assistant import consult_ai
from oracle_providers import (LOCAL_MODELS, RECOMMENDED_LOCAL_MODEL, model_display_label, model_id_from_label,
    OLLA_DOWNLOAD, OPENAI_KEYS, OPENAI_BILLING,
    ollama_executable, ollama_models, has_model, consult_local, organize_local,
    install_ollama_windows, start_local_service, download_model)
from campaign_import import (extract_document, build_local_proposal, apply_proposal,
                             organize_with_ai, split_manuscript_for_ai, LABELS)
from PIL import Image, ImageTk
from download_metrics import PullSpeedMeter, format_transfer_speed
from oracle_session import clean_markdown, apply_suggestion, transcript_text, load_preferences, save_preferences
from oracle_render import render_message
from project_files import suggest_save_name, last_project_directory, remember_project_directory
from oracle_field import DEFAULT_FIELD_REQUEST, clean_field_revision, InvalidFieldRevision
from forge_ui_mixins import ForgeEnhancements
from forge_library import Archive
from forge_book import suggest_outline
from oracle_grounding import gather_sources, is_attribution_question
from image_setup import open_image_setup
from comfy_studio import open_comfy_studio
from project_actions import project_outline_context, action_instructions, normalize_plan, apply_actions, summarize_actions
from archive_vision import describe_image, match_requested_image

APP_VERSION = "1.1.0-beta.1"

# Studio Dark: contemporary writing tools, with subtle dungeon/brass accents.
BG = '#121B25'
PANEL = '#1B2A35'
FIELD = '#283A45'
FG = '#EAF0F0'
SOFT = '#ACBEC6'
ACCENT = '#CBA16A'
FOREST = '#276D74'
FOREST_HOVER = '#348B91'
BORDER = '#39505E'
ENTRY_BG = '#243440'


class CampaignForge(ForgeEnhancements, tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry("1390x890")
        self.minsize(1110, 740)
        self.title(f"Campaign Forge v{APP_VERSION} — The Archivist's Studio")
        self.configure(bg=BG)
        try:
            if sys.platform == 'win32':
                self.iconbitmap(str(self.asset_path('CampaignForge.ico')))
        except (OSError, tk.TclError):
            pass  # Keep the main editor usable even if an icon cannot be loaded.
        self.data = new_campaign()
        self.archive = Archive()
        self.current_character_id = None
        self.current_encounter_id = None
        self.project_path = None
        self.last_project_dir = last_project_directory()
        self.current_entry_id = None
        self.current_map_id = None
        self.current_ref_id = None
        self.dirty = False
        self.loading = False
        self.tool = 'wall'
        self.map_mode = 'paint'
        self.map_prop_kind = tk.StringVar(value='Crate')
        self.map_drag_index = None
        self.map_selected_prop_index = None
        self.ai_busy = False
        self.ai_has_response = False
        self.import_busy = False
        self.import_cancel = threading.Event()
        self.cloud_key = ""  # current process only, never saved to a campaign file
        self.local_actions_busy = False
        self.model_pull_progress = tk.DoubleVar(value=0)
        self.model_pull_note = tk.StringVar(value="No download in progress.")
        self.model_pull_speed_note = tk.StringVar(value="— MB/s    ·    — Mbps")
        self.model_pull_activity_note = tk.StringVar(value="Download a model to see its transfer speed.")
        self.pull_meter = None
        self.import_doc = None
        self.import_proposal = None
        self.import_choices = set()
        self.pre_import_snapshot = None
        self.map_size = 25
        self.import_report = []
        self.project_epoch = 0
        self.preferences = load_preferences()  # never stored in campaign files
        self.oracle_turns = []  # current process only; never written to campaign JSON
        self.selected_oracle_turn = None
        self.last_transcript_export = 0
        self.oracle_target = None
        self.ai_request_target = None
        self.last_ai_request = None
        self.field_undo = []
        self.project_action_undo = None
        self.setup_styles()
        self.build_interface()
        self.load_into_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_exit)
        self.bind_all("<Control-s>", lambda e: self.save())
        self.bind_all("<Control-Shift-S>", lambda e: self.save_as())
        self.bind_all("<Control-o>", lambda e: self.open_file())
        self.bind_all("<Control-n>", lambda e: self.new_file())
        self.bind_all("<F1>", lambda e: self.open_help())

    def setup_styles(self):
        s=ttk.Style(self);s.theme_use('clam')
        s.configure('TFrame',background=BG)
        s.configure('Panel.TFrame',background=PANEL,relief='flat')
        s.configure('TLabel',background=BG,foreground=FG,font=('Segoe UI',10))
        s.configure('Panel.TLabel',background=PANEL,foreground=FG,font=('Segoe UI',10))
        s.configure('Muted.TLabel',background=BG,foreground=SOFT,font=('Segoe UI',9))
        s.configure('Title.TLabel',background=BG,foreground=FG,font=('Segoe UI',23,'bold'))
        s.configure('Section.TLabel',background=BG,foreground=FG,font=('Segoe UI',17,'bold'))
        s.configure('PanelSection.TLabel',background=PANEL,foreground=ACCENT,font=('Segoe UI',11,'bold'))
        s.configure('TButton',font=('Segoe UI',9,'bold'),padding=(12,9),background=FOREST,
                    foreground='#F9FCFD',bordercolor=FOREST,relief='flat',borderwidth=0)
        s.map('TButton',background=[('active',FOREST_HOVER),('disabled','#344852')],
              foreground=[('disabled','#9EAEB5')])
        s.configure('Accent.TButton',background=ACCENT,foreground='#101820',font=('Segoe UI',9,'bold'))
        s.map('Accent.TButton',background=[('active','#E2B57C')],foreground=[('active','#101820')])
        s.configure('TEntry',fieldbackground=ENTRY_BG,foreground=FG,insertcolor=FG,
                    bordercolor=BORDER,lightcolor=BORDER,darkcolor=BORDER,padding=8)
        s.map('TEntry',foreground=[('disabled',SOFT)],fieldbackground=[('disabled',FIELD)])
        s.configure('TCombobox',fieldbackground=ENTRY_BG,foreground=FG,background=FIELD,
                    arrowcolor=ACCENT,selectbackground=ENTRY_BG,selectforeground=FG,padding=7)
        s.map('TCombobox',fieldbackground=[('readonly',ENTRY_BG)],selectbackground=[('readonly',ENTRY_BG)],
              foreground=[('readonly',FG)])
        s.configure('TNotebook',background=BG,borderwidth=0,tabmargins=(0,5,0,0))
        s.configure('TNotebook.Tab',background='#202F3B',foreground=SOFT,
                    font=('Segoe UI',9,'bold'),padding=(11,11),borderwidth=0)
        s.map('TNotebook.Tab',background=[('selected',PANEL),('active',FIELD)],
              foreground=[('selected',ACCENT)])
        s.configure('TCheckbutton',background=BG,foreground=FG,font=('Segoe UI',10))
        s.map('TCheckbutton',background=[('active',BG)],foreground=[('active',FG)])
        s.configure('Vertical.TScrollbar',background=FIELD,arrowcolor=ACCENT,troughcolor=BG)
        s.configure('Treeview',background=ENTRY_BG,fieldbackground=ENTRY_BG,foreground=FG,
                    rowheight=30,font=('Segoe UI',10),bordercolor=BORDER)
        s.configure('Treeview.Heading',background=FIELD,foreground=FG,font=('Segoe UI',10,'bold'))
        s.map('Treeview',background=[('selected',FOREST)],foreground=[('selected','#FFFFFF')])

    def asset_path(self, name):
        base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
        return base / "assets" / name

    def text_box(self, parent, height=8, **kwargs):
        t = tk.Text(parent, height=height, wrap="word", bg=ENTRY_BG, fg=FG,
                    insertbackground=FG, selectbackground=FOREST, relief="flat",
                    padx=12, pady=10, undo=True, font=("Segoe UI", 11), highlightthickness=1, highlightbackground=BORDER, **kwargs)
        return t

    def list_box(self, parent, **kwargs):
        return tk.Listbox(parent, bg=ENTRY_BG, fg=FG, selectbackground=FOREST,
                          selectforeground="#FFFFFF", relief="flat", highlightthickness=0,
                          activestyle="none", exportselection=False, font=("Segoe UI", 10), **kwargs)

    def _banner_background(self,canvas_width):
        """Original vector-style dark banner. No licensed image assets needed."""
        from PIL import ImageDraw
        w=max(1100,canvas_width);h=86
        picture=Image.new('RGB',(w,h),(21,37,46));d=ImageDraw.Draw(picture)
        for y in range(h):
            factor=y/max(1,h-1)
            d.line((0,y,w,y),fill=(int(19+8*factor),int(35+11*factor),int(45+11*factor)))
        # A few faint contour/dungeon corridors provide atmosphere without distraction.
        import math
        for lane in range(7):
            pts=[(x, int(22+lane*11+5*math.sin(x/105.0+lane*.71))) for x in range(0,w,8)]
            d.line(pts,fill=(37,65,71),width=1)
        d.line((0,h-2,w,h-2),fill=(104,114,107),width=1)
        self.banner_photo=ImageTk.PhotoImage(picture,master=self)
        self.banner.delete('banner_bg')
        self.banner.create_image(0,0,image=self.banner_photo,anchor='nw',tags='banner_bg')
        self.banner.tag_lower('banner_bg')

    def _draw_banner_button(self,x,y,text,command,icon,highlight=False,width=111):
        tag='toolbar_'+text.lower().replace(' ','_')
        fill='#CBA16A' if highlight else '#254854'
        ink='#17212A' if highlight else '#EAF0F0'
        h=36;r=8
        self.banner.create_rectangle(x+r,y,x+width-r,y+h,fill=fill,outline=fill,tags=(tag,'toolbar'))
        self.banner.create_rectangle(x,y+r,x+width,y+h-r,fill=fill,outline=fill,tags=(tag,'toolbar'))
        for cx,cy in ((x+r,y+r),(x+width-r,y+r),(x+r,y+h-r),(x+width-r,y+h-r)):
            self.banner.create_oval(cx-r,cy-r,cx+r,cy+r,fill=fill,outline=fill,tags=(tag,'toolbar'))
        self.banner.create_text(x+width/2,y+h/2,text=f'{icon}  {text}',fill=ink,
                                font=('Segoe UI',9,'bold'),tags=(tag,'toolbar'))
        self.banner.tag_bind(tag,'<Button-1>',lambda e:command())
        self.banner.tag_bind(tag,'<Enter>',lambda e:self.banner.configure(cursor='hand2'))
        self.banner.tag_bind(tag,'<Leave>',lambda e:self.banner.configure(cursor=''))

    def _render_banner(self,width):
        self.banner.delete('all');self._banner_background(width)
        self.banner.create_oval(19,15,76,72,fill='#16313A',outline='#CBA16A',width=2)
        self.banner.create_text(47,43,text='✦',fill='#D8B078',font=('Segoe UI',28,'bold'))
        self.banner.create_text(93,31,text='CAMPAIGN FORGE',anchor='w',fill=FG,
                                font=('Segoe UI',22,'bold'))
        self.banner.create_text(94,58,text='CREATOR STUDIO    /    WRITE  ·  BUILD  ·  PUBLISH',
                                anchor='w',fill='#A7BBC1',font=('Segoe UI',9,'bold'))
        right=max(width,1100)-18
        buttons=[('New','+',self.new_file,False,80),('Open','▤',self.open_file,False,90),
                 ('Save','✓',self.save,True,82),('Save As','▣',self.save_as,False,103),
                 ('Help','?',self.open_help,False,78)]
        total=sum(b[-1] for b in buttons)+(len(buttons)-1)*8
        x=right-total
        for text,icon,fn,prominent,bw in buttons:
            self._draw_banner_button(x,25,text,fn,icon,prominent,bw)
            x+=bw+8

    def _resize_scroll_shell(self, event):
        if not hasattr(self, "shell_window"):
            return
        self.shell_canvas.itemconfigure(self.shell_window, width=event.width)
        # Extra canvas space is available for the editor; below that, the
        # outside scrollbar permits access to the whole page.
        if hasattr(self, "tabs"):
            self.tabs.configure(height=max(730,event.height-110))

    def _scroll_main(self, event):
        # Preserve independent wheel scrolling for content boxes and lists.
        if isinstance(event.widget, (tk.Text, tk.Listbox, ttk.Treeview, ttk.Combobox)):
            return
        if getattr(event, "num", None) in (4, 5):
            steps = -3 if event.num == 4 else 3
        else:
            units = event.delta / 120
            steps = -(int(units) if units else (1 if event.delta > 0 else -1)) * 3
        self.shell_canvas.yview_scroll(steps, "units")

    def build_interface(self):
        # There are two distinct scroll layers: the full workspace scrolls,
        # while documents, trees and story editors keep their own scrollbars.
        self.shell_canvas = tk.Canvas(self, bg=BG, highlightthickness=0, bd=0)
        outer_scroll = ttk.Scrollbar(self, orient="vertical", command=self.shell_canvas.yview)
        outer_scroll.pack(side="right", fill="y")
        self.shell_canvas.pack(side="left", fill="both", expand=True)
        self.shell_canvas.configure(yscrollcommand=outer_scroll.set)
        shell = ttk.Frame(self.shell_canvas)
        self.shell_window = self.shell_canvas.create_window((0,0), window=shell, anchor="nw")
        shell.bind("<Configure>", lambda e: self.shell_canvas.configure(scrollregion=self.shell_canvas.bbox("all")))
        self.shell_canvas.bind("<Configure>", self._resize_scroll_shell)
        self.bind_all("<MouseWheel>", self._scroll_main, add="+")
        self.bind_all("<Button-4>", self._scroll_main, add="+")
        self.bind_all("<Button-5>", self._scroll_main, add="+")

        self.banner = tk.Canvas(shell, height=86, bg=BG, highlightthickness=0, bd=0)
        self.banner.pack(fill="x", padx=11, pady=(8, 2))
        self.banner.bind("<Configure>", lambda e: self._render_banner(e.width))

        self.tabs = ttk.Notebook(shell)
        self.tabs.bind("<<NotebookTabChanged>>", lambda e: self.shell_canvas.yview_moveto(0))
        self.tabs.pack(fill="both", expand=True, padx=12, pady=(2, 5))
        self.overview_tab = ttk.Frame(self.tabs)
        self.library_tab = ttk.Frame(self.tabs)
        self.archives_tab = ttk.Frame(self.tabs)
        self.roster_tab = ttk.Frame(self.tabs)
        self.maps_tab = ttk.Frame(self.tabs)
        self.ai_tab = ttk.Frame(self.tabs)
        self.publish_tab = ttk.Frame(self.tabs)
        # Light-weight navigation glyphs keep the style, with more useful area
        # than the older oversized title and traditional boxed tab strip.
        self.nav_images = []
        for name, tab, png in [("THE ATLAS", self.overview_tab, "nav_atlas.png"),
                               ("CHRONICLES", self.library_tab, "nav_chronicles.png"),
                               ("THE ARCHIVES", self.archives_tab, "nav_chronicles.png"),
                               ("ROSTER", self.roster_tab, "nav_atlas.png"),
                               ("CARTOGRAPHY", self.maps_tab, "nav_cartography.png"),
                               ("THE ORACLE", self.ai_tab, "nav_oracle.png"),
                               ("BIND THE TOME", self.publish_tab, "nav_book.png")]:
            photo = ImageTk.PhotoImage(Image.open(self.asset_path(png)))
            self.nav_images.append(photo)
            self.tabs.add(tab, text="  " + name + "  ", image=photo, compound="left")
        self.build_overview()
        self.build_library()
        self.build_archives()
        self.build_roster()
        self.build_maps()
        self.build_ai()
        self.build_publish()
        self.status = tk.StringVar(value="New manuscript — start writing or import an existing campaign under The Oracle.")
        ttk.Label(shell, textvariable=self.status, style="Muted.TLabel").pack(
            fill="x", padx=19, pady=(0, 8))

    def open_help(self):
        """F1/Help: plain-language directions for each workspace, not roleplay."""
        contents = [
            ("Getting started", "Start a new campaign by entering details in The Atlas, or choose The Oracle > Import an Existing Campaign to load a Word or PDF file.\n\nUse New to start from scratch. Open loads a previously saved .campaign.json project. The first Save (Ctrl+S) asks you to choose a filename based on your campaign title. After that, Save updates that same file. Use Save As (Ctrl+Shift+S) to create a separate version. The app remembers the last folder used, but never automatically overwrites a similar-named project. Exporting a PDF does not save your editable project.\n\nUse the scrollbar on the far right to scroll the whole workspace. Text boxes and lists also have their own scrolling."),
            ("The Atlas", "Enter your campaign title, system, levels, setting, premise and main story arc. You can leave unfinished fields empty. Importing a manuscript will fill empty fields without replacing existing writing.\n\nUse Improve with Oracle next to Premise, Setting or Main Story Arc. It opens Creative Consultation with that exact field's text in the prompt. Review and send the question, then choose Apply selected to field to compare before editing."),
            ("Chronicles", "Create and edit chapters, NPCs, locations, quests, encounters and other story entries. Select an entry on the left, edit its content on the right, and choose Save entry changes. Mark DM-only material to exclude it from a player-facing PDF."),
            ("The Archives", "Add documents to your computer-based library. You can store documents for the current campaign or share them across campaigns. Supported files include PDFs, Word files, text, images, and JSON. The library is not uploaded to a server. Scanned PDFs and pictures are stored but do not become searchable text.\n\nTo let The Oracle consult documents, enable the Archives source checkbox in Creative Consultation. Cloud requests require separate approval for reference excerpts. Export library backup makes a ZIP of all locally archived files."),
            ("Roster & Bestiary", "Create NPCs, creatures and encounters. Check Combat character to enable structured statistic fields; leave unknown figures blank. Noncombat characters print biography information only. Use Read PDF / image character sheet to extract labeled fields from selectable-text PDFs. For scans and photos, the app can ask a locally installed vision-capable Ollama model, then show a review dialog before saving. JSON import and Chronicle NPC copying remain available. Encounter Builder links existing characters without duplicating their records. All AI-derived combat statistics require verification."),
            ("Cartography", "Create a grid map, import a background image, and paint terrain on top. Imported images are copied into The Archives. Choose a prop such as a crate, barrel, tree or marker; click Place / drag props, then click or drag on the map. Right-click a prop to remove it. Export a high-resolution PNG; D&D Beyond uploads remain manual. Generate Image (ComfyUI) opens a local Art Studio with positive/negative prompts, model choice, preview and opt-in Archives import. ComfyUI and an SDXL model must be installed separately. This does not call a cloud API. Images from The Archives need to travel with an Archives backup when moving to another computer."),
            ("The Oracle — Import", "Open The Oracle, then Import an Existing Campaign. Choose a text-based PDF or DOCX. You will first see offline suggestions. Select entries to include, review their source text, and choose Add selected to campaign. You must confirm before any content changes.\n\nIf you enable Local Oracle, Organize with selected Oracle analyzes your manuscript in passages. The app retries malformed AI responses. Unreadable passages are kept in Needs Review, not lost. Always verify AI suggestions against your manuscript. The imported project is not saved until you choose Save."),
            ("The Oracle — Creative Consultation", "The Scribe works offline without AI. To connect AI on your PC, open The Oracle > Creative Consultation > The Local Oracle, install Ollama, download a model, then use Check status. Local requests use your PC and may take several minutes.\n\nFor cloud AI, select The Greater Oracle and follow the API-key setup. API usage may incur charges and sends approved material to OpenAI. Campaign Forge does not use your ChatGPT password.\n\nUse Hide setup choices to give the conversation more room, or Show setup choices to change Oracle modes. Clear destination makes new questions general rather than linked to a field.\n\nEvery question and response appears in a scrollable transcript. Click a response heading to select that reply. Use Copy selected reply for clean text, Export transcript (.txt) to save it, or Apply selected to field to compare and append or replace a field. Merge & refine asks the Oracle for a combined draft; it never changes the field automatically. Undo field change restores previous text.\n\nOracle conversations live only in the running application. When closing, choose to export a text file or discard the session. You can disable repeated request notices with Don't show this notice again."),
            ("Bind the Tome", "Use The Book Architect to select a D&D, Pathfinder, world guide or custom outline. Rearrange sections and entries before publishing. Click Preview book to inspect the final PDF pages inside the application without creating a permanent downloaded file; select a section and choose Preview selected section / entry for a shorter proof. Suggest original manuscript order uses matching headings from an Archives document and asks before changing the order. Review every proposed scene order manually. Save the editable project separately from the final PDF."),
            ("Troubleshooting", "If a model appears stuck, open The Oracle > Creative Consultation > Local Oracle setup to check the installed model and download progress.\n\nIf AI organization reports issues, open View analysis report on the import screen. Failed passages remain as unselected Needs Review entries. The app writes limited local diagnostics for malformed replies; those files may contain excerpts of your campaign, so treat them as private.\n\nFor help, press F1 from anywhere in Campaign Forge."),
        ]
        dialog = tk.Toplevel(self)
        dialog.title("Campaign Forge — Help")
        dialog.geometry("850x585")
        dialog.minsize(640, 430)
        dialog.configure(bg=BG)
        dialog.transient(self)
        panel = ttk.Frame(dialog, padding=14)
        panel.pack(fill="both", expand=True)
        ttk.Label(panel, text="Campaign Forge Help", style="Title.TLabel").pack(anchor="w", pady=(0, 8))
        ttk.Label(panel, text="Choose a topic. Instructions are written for the desktop application.",
                  style="Muted.TLabel").pack(anchor="w", pady=(0, 9))
        body = ttk.Frame(panel)
        body.pack(fill="both", expand=True)
        side = ttk.Frame(body, style="Panel.TFrame", padding=8)
        side.pack(side="left", fill="y", padx=(0, 12))
        topics = self.list_box(side, width=28, height=18)
        topics.pack(fill="both", expand=True)
        content = ttk.Frame(body)
        content.pack(side="left", fill="both", expand=True)
        txt = self.text_box(content, height=15)
        bar = ttk.Scrollbar(content, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=bar.set)
        bar.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True)
        def choose_topic(event=None):
            choice = topics.curselection()
            if not choice:
                return
            txt.configure(state="normal")
            txt.delete("1.0", "end")
            txt.insert("1.0", contents[choice[0]][1])
            txt.configure(state="disabled")
            txt.yview_moveto(0)
        for name, _ in contents:
            topics.insert("end", name)
        topics.bind("<<ListboxSelect>>", choose_topic)
        idx = self.tabs.index(self.tabs.select()) if hasattr(self, "tabs") else 0
        topics.selection_set({0:1, 1:2, 2:3, 3:4, 4:5, 5:6, 6:8}.get(idx, 0))
        choose_topic()
        ttk.Button(panel, text="Close", command=dialog.destroy).pack(anchor="e", pady=(9, 0))
        dialog.focus_set()

    def _update_window_title(self):
        filename = Path(self.project_path).name if self.project_path else "Unsaved campaign"
        suffix = " *" if self.dirty else ""
        self.title(f"Campaign Forge v{APP_VERSION} — {filename}{suffix}")

    def mark_dirty(self, event=None):
        if not self.loading:
            self.dirty = True
            self._update_window_title()

    def row_label(self, parent, text, row, col=0):
        ttk.Label(parent, text=text).grid(row=row, column=col, sticky="w", pady=(5, 3))

    def build_overview(self):
        tab = self.overview_tab
        tab.columnconfigure(0, weight=1)
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(5, weight=1)
        ttk.Label(tab, text="Here begins the chronicle of your world.",
                  style="Section.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(9, 15))
        basics = ttk.Frame(tab)
        basics.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        for i in range(3):
            basics.columnconfigure(i, weight=1)
        self.meta = {}
        fields = [("title", "Campaign title", 0, 0), ("author", "Author / DM", 0, 1),
                  ("levels", "Character levels", 0, 2), ("system", "Game system", 2, 0),
                  ("tone", "Tone / genre", 2, 1)]
        for key, label, r, c in fields:
            self.row_label(basics, label, r, c)
            if key == "system":
                w = ttk.Combobox(basics, state="readonly", values=SYSTEMS)
                w.bind("<<ComboboxSelected>>", self.mark_dirty)
            else:
                w = ttk.Entry(basics)
                w.bind("<KeyRelease>", self.mark_dirty)
            w.grid(row=r+1, column=c, sticky="ew", padx=(0, 15), pady=(0, 7))
            self.meta[key] = w

        self.overview_text = {}
        for col, key, label, height in [(0, "pitch", "Premise / elevator pitch", 6),
                                         (1, "setting", "World and setting", 6),
                                         (0, "story_arc", "Main story arc", 13)]:
            r = 3 if key != "story_arc" else 5
            head = ttk.Frame(tab)
            head.grid(row=4 if key == "story_arc" else 2, column=col, sticky="ew", padx=(0, 18))
            ttk.Label(head, text=label).pack(side="left", pady=(5, 3))
            ttk.Button(head, text="✦ Improve with Oracle",
                       command=lambda k=key, l=label: self.send_field_to_oracle("overview", k, l)).pack(side="right", pady=(2, 2))
            box = self.text_box(tab, height=height)
            box.grid(row=r, column=col, sticky="nsew", padx=(0, 18), pady=(2, 12))
            box.bind("<KeyRelease>", self.mark_dirty)
            self.overview_text[key] = box
        guidance = ttk.Frame(tab, style="Panel.TFrame", padding=17)
        guidance.grid(row=5, column=1, sticky="nsew", padx=(0, 8), pady=(2, 12))
        ttk.Label(guidance, text="THE KEEPER OF THE LORE", style="PanelSection.TLabel").pack(anchor="w")
        tk.Label(guidance, text="Your story remains your own. The Oracle can help without rewriting canon.\n\nAlready have a manuscript? Recover your PDF or Word campaign under The Oracle.\n\nSave as a portable .campaign.json file.",
                 bg=PANEL, fg=SOFT, wraplength=455, justify="left", font=("Georgia", 10)).pack(anchor="w", pady=14)

    def build_library(self):
        tab = self.library_tab
        tab.columnconfigure(0, weight=1)
        tab.columnconfigure(1, weight=3)
        tab.rowconfigure(0, weight=1)
        left = ttk.Frame(tab, style="Panel.TFrame", padding=12)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 14), pady=8)
        right = ttk.Frame(tab)
        right.grid(row=0, column=1, sticky="nsew", pady=8)
        ttk.Label(left, text="CAMPAIGN CONTENT", style="PanelSection.TLabel").pack(anchor="w", pady=(2, 10))
        self.entry_filter = ttk.Combobox(left, state="readonly", values=["All content"] + CATEGORIES)
        self.entry_filter.set("All content")
        self.entry_filter.pack(fill="x", pady=(0, 10))
        self.entry_filter.bind("<<ComboboxSelected>>", lambda e: self.refresh_entry_list())
        self.entry_list = self.list_box(left)
        self.entry_list.pack(fill="both", expand=True)
        self.entry_list.bind("<<ListboxSelect>>", self.on_entry_selected)
        actions = ttk.Frame(left, style="Panel.TFrame")
        actions.pack(fill="x", pady=10)
        ttk.Button(actions, text="+ New", command=self.add_entry).pack(side="left", padx=(0, 5))
        ttk.Button(actions, text="Duplicate", command=self.duplicate_entry).pack(side="left", padx=(0, 5))
        ttk.Button(actions, text="Delete", command=self.delete_entry).pack(side="left")

        ttk.Label(right, text="Story entry", style="Section.TLabel").pack(anchor="w", pady=(5, 14))
        form = ttk.Frame(right)
        form.pack(fill="x")
        form.columnconfigure(0, weight=3)
        form.columnconfigure(1, weight=1)
        self.row_label(form, "Name", 0, 0)
        self.row_label(form, "Type", 0, 1)
        self.entry_name = ttk.Entry(form)
        self.entry_name.grid(row=1, column=0, sticky="ew", padx=(0, 12))
        self.entry_kind = ttk.Combobox(form, values=CATEGORIES, state="readonly")
        self.entry_kind.grid(row=1, column=1, sticky="ew")
        self.entry_name.bind("<KeyRelease>", self.mark_dirty)
        self.entry_kind.bind("<<ComboboxSelected>>", self.mark_dirty)
        self.gm_only_var = tk.BooleanVar()
        ttk.Checkbutton(right, text="DM-only material (exclude from player book)",
                        variable=self.gm_only_var, command=self.mark_dirty).pack(anchor="w", pady=13)
        ttk.Label(right, text="Notes, description, roleplay prompts, mechanics, dialogue, clues …").pack(anchor="w", pady=(0, 7))
        self.entry_body = self.text_box(right, height=17)
        self.entry_body.pack(fill="both", expand=True)
        self.entry_body.bind("<KeyRelease>", self.mark_dirty)
        entry_actions = ttk.Frame(right)
        entry_actions.pack(fill="x", pady=12)
        ttk.Button(entry_actions, text="✦ Improve with Oracle",
                   command=lambda: self.send_field_to_oracle("entry", self.current_entry_id,
                                  f"{self.entry_kind.get()} — {self.entry_name.get()}")).pack(side="left")
        ttk.Button(entry_actions, text="Save entry changes", command=self.save_entry_changes,
                   style="Accent.TButton").pack(side="right")

    def build_maps(self):
        tab = self.maps_tab
        ttk.Label(tab, text="Map Workshop", style="Section.TLabel").pack(anchor="w", pady=(8, 3))
        ttk.Label(tab, text="Import an existing map, paint terrain, and arrange moveable props. Export as a clean high-resolution PNG.",
                  style="Muted.TLabel").pack(anchor="w", pady=(0, 13))
        area = ttk.Frame(tab)
        area.pack(fill="both", expand=True)
        left = ttk.Frame(area, style="Panel.TFrame", padding=12)
        left.pack(side="left", fill="y", padx=(0, 15))
        ttk.Label(left, text="MAPS", style="PanelSection.TLabel").pack(anchor="w", pady=(0, 9))
        self.map_list = self.list_box(left, width=24, height=13)
        self.map_list.pack(fill="y", expand=False)
        self.map_list.bind("<<ListboxSelect>>", self.on_map_selected)
        ttk.Button(left, text="+ New map", command=self.add_map).pack(fill="x", pady=(12, 5))
        ttk.Button(left, text="Delete map", command=self.delete_map).pack(fill="x", pady=5)
        ttk.Button(left,text='Import map background',command=self.import_map_background).pack(fill='x',pady=(11,4))
        ttk.Button(left,text='Remove background',command=self.remove_map_background).pack(fill='x',pady=4)
        ttk.Button(left,text='AI image model setup',command=lambda:open_image_setup(self)).pack(fill='x',pady=4)
        ttk.Button(left, text='Generate Image (ComfyUI)', command=lambda:open_comfy_studio(self),
                   style='Accent.TButton').pack(fill='x', pady=(5, 7))
        ttk.Button(left, text="Export PNG", command=self.export_map_png,
                   style="Accent.TButton").pack(fill="x", pady=(13, 6))

        right = ttk.Frame(area)
        right.pack(side="left", fill="both", expand=True)
        tools = ttk.Frame(right)
        tools.pack(fill="x", pady=(0, 9))
        ttk.Label(tools, text="Paint:").pack(side="left", padx=(0, 9))
        self.paint_tools = {}
        for name in TILE_NAMES:
            label = name.title()
            btn = ttk.Button(tools, text=label, command=lambda n=name: self.select_tool(n))
            btn.pack(side="left", padx=2)
            self.paint_tools[name] = btn
        props=ttk.Frame(right);props.pack(fill='x',pady=(0,9))
        ttk.Label(props,text='Props:').pack(side='left',padx=(0,8))
        ttk.Combobox(props,state='readonly',textvariable=self.map_prop_kind,values=PROP_NAMES,width=14).pack(side='left')
        ttk.Button(props,text='Place / drag props',command=self.map_enable_props).pack(side='left',padx=6)
        ttk.Button(props,text='Paint terrain',command=lambda:self.select_tool('wall')).pack(side='left',padx=5)
        ttk.Label(props,text='Right-click a prop to remove it',style='Muted.TLabel').pack(side='left',padx=8)
        custom=ttk.Frame(right);custom.pack(fill='x',pady=(0,7))
        ttk.Label(custom,text='Prop size:').pack(side='left')
        self.map_prop_width=tk.IntVar(value=1);self.map_prop_height=tk.IntVar(value=1)
        ttk.Spinbox(custom,from_=1,to=12,width=3,textvariable=self.map_prop_width).pack(side='left',padx=4)
        ttk.Label(custom,text='x').pack(side='left')
        ttk.Spinbox(custom,from_=1,to=12,width=3,textvariable=self.map_prop_height).pack(side='left',padx=4)
        ttk.Button(custom,text='Resize selected',command=self.map_resize_prop).pack(side='left',padx=4)
        ttk.Button(custom,text='Rotate 90°',command=self.map_rotate_prop).pack(side='left',padx=4)
        ttk.Button(custom,text='Import PNG prop…',command=self.map_import_prop).pack(side='left',padx=4)
        ttk.Label(custom,text='Click or drag a prop to select it',style='Muted.TLabel').pack(side='left',padx=6)
        self.map_tool_label = ttk.Label(right, text="Selected: Wall", style="Muted.TLabel")
        self.map_tool_label.pack(anchor="w", pady=(0, 5))
        self.map_canvas = tk.Canvas(right, bg=ENTRY_BG, highlightthickness=0, height=430, width=660)
        self.map_canvas.pack(anchor="nw", fill="both", expand=True)
        self.map_canvas.bind("<Button-1>", self.paint_at)
        self.map_canvas.bind("<B1-Motion>", self.paint_at)
        self.map_canvas.bind("<ButtonRelease-1>",lambda ev:setattr(self,'map_drag_index',None))
        self.map_canvas.bind("<Button-3>", self.map_remove_prop)
        ttk.Label(right, text="Imported images are stored in The Archives. Use paint for terrain and prop mode for moveable objects. VTT grid scaling depends on your tabletop.",
                  style="Muted.TLabel").pack(anchor="w", pady=8)

    def build_ai(self):
        host = self.ai_tab
        ttk.Label(host, text="The Oracle & Manuscript Scriptorium", style="Section.TLabel").pack(
            anchor="w", pady=(9, 3))
        ttk.Label(host, text="Recover stories already written, then seek inspiration where the path grows unclear.",
                  style="Muted.TLabel").pack(anchor="w", pady=(0, 8))
        panels = ttk.Notebook(host)
        panels.pack(fill="both", expand=True)
        recover = ttk.Frame(panels)
        consult = ttk.Frame(panels)
        panels.add(recover, text="  IMPORT AN EXISTING CAMPAIGN  ")
        panels.add(consult, text="  CREATIVE CONSULTATION  ")
        self.oracle_panels = panels
        self.build_recovery(recover)

        self.oracle_mode = tk.StringVar(value="scribe")
        self.local_model = tk.StringVar(value=RECOMMENDED_LOCAL_MODEL)
        self.local_model_display = tk.StringVar(value=model_display_label(RECOMMENDED_LOCAL_MODEL))
        self._auto_select_installed_model = True
        self.local_status = tk.StringVar(value="Not checked. Install Ollama, then download a model.")
        self.cloud_status = tk.StringVar(value="Not connected · API key required")
        self.cloud_model = tk.StringVar(value="gpt-4.1-mini")
        self.include_refs = tk.BooleanVar(value=True)
        self.include_archive = tk.BooleanVar(value=True)
        self.oracle_source_policy = tk.StringVar(value="Use uploaded lore (recommended)")
        self.oracle_reply_kind = tk.StringVar(value="Ask / explain (no edits)")
        consult.columnconfigure(0, weight=1)
        consult.rowconfigure(6, weight=0)
        ttk.Label(consult, text="Choose your Oracle", style="Section.TLabel").grid(
            row=0, column=0, sticky="w", pady=(8, 2))
        ttk.Label(consult, text="Three ways to work. The Scribe is always free and offline; AI is optional.",
                  style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=(0, 7))
        cards = ttk.Frame(consult)
        cards.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        for column in range(3):
            cards.columnconfigure(column, weight=1, uniform="oracle")
        mode_data = [
            ("scribe", "I. THE SCRIBE", "No AI · offline · no account",
             "Write, format and import existing PDFs or Word documents. No information is sent anywhere."),
            ("local", "II. THE LOCAL ORACLE", "Local AI · no per-request fees",
             "Install Ollama and a model on your PC. Creative consultations stay on your computer."),
            ("cloud", "III. THE GREATER ORACLE", "OpenAI API · usage charges",
             "Use a cloud model for more complex writing. Requires an API key and sends approved context online."),
        ]
        for col, (key, title, subtitle, detail) in enumerate(mode_data):
            card = tk.Frame(cards, bg=PANEL, highlightbackground=BORDER, highlightthickness=1, padx=12, pady=9)
            card.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 5, 5 if col < 2 else 0))
            radio = tk.Radiobutton(card, text=title, variable=self.oracle_mode, value=key,
                command=self.oracle_mode_changed, bg=PANEL, fg=FOREST, selectcolor=ENTRY_BG,
                activebackground=PANEL, activeforeground=ACCENT, font=("Georgia", 11, "bold"), anchor="w")
            radio.pack(anchor="w", fill="x")
            tk.Label(card, text=subtitle, bg=PANEL, fg=ACCENT, font=("Georgia", 9, "bold"), anchor="w").pack(anchor="w", pady=(2, 3))
            tk.Label(card, text=detail, bg=PANEL, fg=SOFT, font=("Segoe UI", 9), justify="left",
                     wraplength=310, anchor="nw", height=3).pack(anchor="w", fill="x")
            if key == "scribe":
                ttk.Button(card, text="Explore campaign importer", command=lambda: panels.select(recover)).pack(anchor="w", pady=(8, 0))
            elif key == "local":
                ttk.Button(card, text="Install / set up local AI", command=self.open_local_setup).pack(anchor="w", pady=(8, 0))
                ttk.Button(card, text="Set up image generator", command=lambda:open_image_setup(self)).pack(anchor="w", pady=(4, 0))
            else:
                ttk.Button(card, text="Connect OpenAI API", command=self.open_cloud_setup).pack(anchor="w", pady=(8, 0))
        self.oracle_cards = cards
        self.oracle_setup_visible = True
        self.oracle_explainer = tk.StringVar()
        mode_strip = ttk.Frame(consult)
        mode_strip.grid(row=3, column=0, sticky="ew", pady=(0, 6))
        ttk.Label(mode_strip, textvariable=self.oracle_explainer, style="Muted.TLabel").pack(side="left", fill="x", expand=True)
        self.mode_toggle = ttk.Button(mode_strip, text="Hide setup choices", command=self.toggle_oracle_setup)
        self.mode_toggle.pack(side="right")
        source_bar = ttk.Frame(consult)
        source_bar.grid(row=4, column=0, sticky="ew", pady=(0, 4))
        ttk.Label(source_bar,text="Source priority:").pack(side="left")
        ttk.Combobox(source_bar,textvariable=self.oracle_source_policy, state="readonly", width=31,
            values=("Use uploaded lore (recommended)", "Brainstorm new ideas")).pack(side="left", padx=(5,14))
        ttk.Label(source_bar,text="Reply type:").pack(side="left")
        ttk.Combobox(source_bar,textvariable=self.oracle_reply_kind,state="readonly",width=25,
            values=("Revise selected field", "Ask / explain (no edits)")).pack(side="left",padx=5)
        prompt_head = ttk.Frame(consult)
        prompt_head.grid(row=5, column=0, sticky="ew", pady=(0, 3))
        ttk.Label(prompt_head, text="Ask about plot holes, lore, encounters, or dialogue.").pack(side="left")
        ttk.Checkbutton(prompt_head, text="Project reference excerpts", variable=self.include_refs).pack(side="right")
        ttk.Checkbutton(prompt_head, text="Search The Archives", variable=self.include_archive).pack(side="right", padx=(0, 12))
        self.ai_question = self.text_box(consult, height=2)
        self.ai_question.grid(row=6, column=0, sticky="ew", pady=(0, 7))
        actions = ttk.Frame(consult)
        actions.grid(row=7, column=0, sticky="ew", pady=(0, 7))
        self.ai_consult_button = ttk.Button(actions, text="Consult the Oracle", command=self.request_ai, style="Accent.TButton")
        self.ai_consult_button.pack(side="left")
        ttk.Button(actions, text="Save suggestion as entry", command=self.ai_to_entry).pack(side="left", padx=9)
        ttk.Button(actions, text="Plan project edits…", command=self.plan_project_edits).pack(side="left", padx=4)
        ttk.Button(actions, text="Undo project edits", command=self.undo_project_edits).pack(side="left", padx=4)
        ttk.Button(actions, text="Apply selected to field…", command=self.preview_oracle_application).pack(side="left", padx=4)
        ttk.Button(actions, text="Undo field change", command=self.undo_field_change).pack(side="left", padx=4)
        self.oracle_target_label = tk.StringVar(value="Target: none — use ✦ Improve with Oracle beside a field")
        target_bar = ttk.Frame(consult)
        target_bar.grid(row=8, column=0, sticky="ew", pady=(0, 4))
        ttk.Label(target_bar, textvariable=self.oracle_target_label, style="Muted.TLabel").pack(side="left", fill="x", expand=True)
        ttk.Button(target_bar, text="Clear destination", command=self.clear_oracle_destination).pack(side="right")
        history_bar = ttk.Frame(consult)
        history_bar.grid(row=9, column=0, sticky="ew", pady=(0, 3))
        ttk.Label(history_bar, text="Consultation history · select an Oracle reply to apply or copy").pack(side="left")
        ttk.Button(history_bar, text="Export transcript (.txt)", command=self.save_oracle_transcript).pack(side="right", padx=4)
        ttk.Button(history_bar, text="Copy selected reply", command=self.copy_oracle_reply).pack(side="right")
        transcript_frame = ttk.Frame(consult)
        consult.rowconfigure(10, weight=1)
        transcript_frame.grid(row=10, column=0, sticky="nsew", pady=(0, 4))
        transcript_frame.columnconfigure(0, weight=1)
        transcript_frame.rowconfigure(0, weight=1)
        self.ai_output = self.text_box(transcript_frame, height=12)
        self.ai_output.configure(state="disabled", cursor="arrow")
        self.ai_output.grid(row=0, column=0, sticky="nsew")
        transcript_scroll = ttk.Scrollbar(transcript_frame, orient="vertical", command=self.ai_output.yview)
        transcript_scroll.grid(row=0, column=1, sticky="ns")
        self.ai_output.configure(yscrollcommand=transcript_scroll.set)
        self.ai_output.tag_configure("oracle_heading", foreground=FOREST, font=("Georgia", 13, "bold"), spacing1=7)
        self.ai_output.tag_configure("oracle_body", foreground=FG, font=("Segoe UI", 11), spacing2=3)
        self.ai_output.tag_configure("oracle_list", foreground=FG, lmargin1=20, lmargin2=20, font=("Segoe UI", 11))
        self.ai_output.tag_configure("oracle_quote", foreground=SOFT, lmargin1=20, font=("Segoe UI", 10, "italic"))
        self.ai_output.tag_configure("oracle_user", foreground=FOREST, font=("Segoe UI", 11, "bold"), spacing1=9)
        self.ai_output.tag_configure("oracle_reply_label", foreground=ACCENT, font=("Segoe UI", 10, "bold"), spacing1=9)
        self.ai_output.tag_configure("oracle_selected", background=FOREST)
        self.refresh_oracle_transcript()
        self.oracle_mode_changed()

    def toggle_oracle_setup(self):
        self.oracle_setup_visible = not self.oracle_setup_visible
        if self.oracle_setup_visible:
            self.oracle_cards.grid()
        else:
            self.oracle_cards.grid_remove()
        self.mode_toggle.configure(text="Hide setup choices" if self.oracle_setup_visible else "Show setup choices")

    def clear_oracle_destination(self):
        self.oracle_target = None
        self.oracle_target_label.set("Target: none — use ✦ Improve with Oracle beside a field")
        self.oracle_reply_kind.set("Ask / explain (no edits)")
        self.status.set("Oracle destination cleared. New consultations will be general questions.")

    def oracle_mode_changed(self):
        mode = self.oracle_mode.get()
        if mode == "scribe":
            text = "SCRIBE SELECTED · Offline manuscript import, writing, maps and publishing remain available. AI is off."
        elif mode == "local":
            text = "LOCAL SELECTED · " + self.local_status.get()
        else:
            text = "GREATER ORACLE SELECTED · " + self.cloud_status.get() + ". Online API use may incur charges."
        self.oracle_explainer.set(text)
        if hasattr(self, "ai_consult_button"):
            self.ai_consult_button.configure(state="disabled" if mode == "scribe" else "normal")
        if hasattr(self, "ai_organize_button") and not self.import_busy:
            self.ai_organize_button.configure(state="disabled" if mode == "scribe" else "normal")

    def open_local_setup(self):
        self.oracle_mode.set("local")
        self.oracle_mode_changed()
        win = tk.Toplevel(self)
        win.title("Local Oracle · Ollama setup")
        win.geometry(f"690x820+{self.winfo_rootx() + 260}+{self.winfo_rooty() + 115}")
        win.minsize(630, 760)
        win.configure(bg=BG)
        win.transient(self)
        self.local_setup_window = win
        area = ttk.Frame(win, padding=21)
        area.pack(fill="both", expand=True)
        ttk.Label(area, text="Set up your Local Oracle", style="Section.TLabel").pack(anchor="w", pady=(0, 9))
        tk.Label(area, text="Your computer does the writing. Ollama is a separate, free local-AI runtime. "
                 "Installing it and downloading a model require internet access and disk space. "
                 "After setup, consultations can work without internet.",
                 wraplength=625, justify="left", bg=BG, fg=SOFT, font=("Georgia", 10)).pack(anchor="w", pady=(0, 12))
        step1 = ttk.Frame(area, style="Panel.TFrame", padding=12)
        step1.pack(fill="x", pady=(0, 11))
        ttk.Label(step1, text="1 · Install Ollama", style="PanelSection.TLabel").pack(anchor="w")
        bar1 = ttk.Frame(step1, style="Panel.TFrame")
        bar1.pack(anchor="w", pady=(7, 0))
        ttk.Button(bar1, text="Install Ollama with Windows", command=self.install_local_runtime).pack(side="left", padx=(0, 7))
        ttk.Button(bar1, text="Official download page", command=lambda: webbrowser.open(OLLA_DOWNLOAD)).pack(side="left")
        step2 = ttk.Frame(area, style="Panel.TFrame", padding=12)
        step2.pack(fill="x", pady=(0, 11))
        ttk.Label(step2, text="2 · Choose and download a language model", style="PanelSection.TLabel").pack(anchor="w", pady=(0, 6))
        selector = ttk.Combobox(step2,
                                values=[model_display_label(mid) for mid in LOCAL_MODELS],
                                textvariable=self.local_model_display,
                                state="readonly", width=34)
        selector.pack(side="left", padx=(0, 9))
        selector.bind("<<ComboboxSelected>>", self.select_local_model)
        ttk.Button(step2, text="Download selected model", command=self.install_local_model).pack(side="left")
        self.local_model_note = tk.StringVar()
        ttk.Label(area, textvariable=self.local_model_note, style="Muted.TLabel").pack(anchor="w", pady=(0, 7))
        self.local_model.trace_add("write", lambda *args: self.local_model_note.set(LOCAL_MODELS.get(self.local_model.get(), "")))
        self.local_model_note.set(LOCAL_MODELS.get(self.local_model.get(), ""))
        ttk.Label(area, text="Recommended for campaign writing on a GPU with ~16 GB VRAM. "
                  "Already downloaded a smaller model? Select it instead; no need to re-download.",
                  style="Muted.TLabel", wraplength=620).pack(anchor="w", pady=(0, 6))
        ttk.Label(area, text="Live download progress (current model layer)", style="PanelSection.TLabel").pack(anchor="w", pady=(3, 3))
        self.model_pull_bar = ttk.Progressbar(area, orient="horizontal", mode="indeterminate",
                                               variable=self.model_pull_progress, maximum=100)
        self.model_pull_bar.pack(fill="x", pady=(0, 4))
        ttk.Label(area, textvariable=self.model_pull_note, style="Muted.TLabel", wraplength=625).pack(
            anchor="w", pady=(0, 5))
        # Real per-layer Ollama byte deltas: not a whole-PC network meter.
        monitor = ttk.Frame(area, style="Panel.TFrame", padding=(12, 9))
        monitor.pack(fill="x", pady=(0, 10))
        ttk.Label(monitor, text="LIVE MODEL TRANSFER SPEED", style="PanelSection.TLabel").pack(anchor="w")
        tk.Label(monitor, textvariable=self.model_pull_speed_note, bg=PANEL, fg=FOREST,
                 font=("Segoe UI", 17, "bold"), anchor="w").pack(fill="x", pady=(2, 2))
        ttk.Label(monitor, textvariable=self.model_pull_activity_note, style="Panel.TLabel",
                  wraplength=580).pack(anchor="w")
        self.after(1000, lambda w=win: self._refresh_transfer_meter(w))
        step3 = ttk.Frame(area, style="Panel.TFrame", padding=12)
        step3.pack(fill="x", pady=(0, 9))
        ttk.Label(step3, text="3 · Check that the model is ready", style="PanelSection.TLabel").pack(anchor="w", pady=(0, 5))
        buttons = ttk.Frame(step3, style="Panel.TFrame")
        buttons.pack(anchor="w")
        ttk.Button(buttons, text="Check status", command=self.check_local_status).pack(side="left", padx=(0, 7))
        ttk.Button(buttons, text="Start Ollama", command=self.start_local_runtime).pack(side="left")
        ttk.Label(area, textvariable=self.local_status, style="Muted.TLabel", wraplength=620).pack(anchor="w", pady=(6, 10))
        ttk.Label(area, text="Privacy: Campaign content goes only to Ollama at 127.0.0.1. Ollama itself is separately installed software; review its settings before use.",
                  style="Muted.TLabel", wraplength=625).pack(anchor="w")
        self.check_local_status()

    def select_local_model(self, event=None):
        """The friendly label must never reach an Ollama API call."""
        model = model_id_from_label(self.local_model_display.get())
        self._auto_select_installed_model = False
        self.local_model.set(model)
        self.check_local_status()

    def check_local_status(self):
        executable = ollama_executable()
        try:
            models = ollama_models()
            # On an upgrade, preserve the user's previously downloaded model
            # instead of accidentally suggesting they install the new default.
            if self._auto_select_installed_model:
                self._auto_select_installed_model = False
                for existing in (RECOMMENDED_LOCAL_MODEL, "gemma3:4b", "llama3.2:3b"):
                    if has_model(models, existing):
                        self.local_model.set(existing)
                        self.local_model_display.set(model_display_label(existing))
                        break
            if has_model(models, self.local_model.get()):
                note = f"Ready · {self.local_model.get()} is installed and Ollama is running."
            else:
                note = f"Ollama is running. Selected model {self.local_model.get()} is not installed yet." + (
                    " Installed: " + ", ".join(models[:4]) if models else "")
        except ConnectionError:
            note = "Ollama is installed but not running. Click Start Ollama." if executable else (
                "Ollama is not detected. Install it from the official source above, then check status.")
        self.local_status.set(note)
        self.oracle_mode_changed()

    def run_local_setup_task(self, operation, worker):
        if self.local_actions_busy:
            messagebox.showinfo("Already working", "An installation or model download is already in progress.")
            return
        self.local_actions_busy = True
        self.local_status.set(operation + " … This may take several minutes; the window remains responsive.")
        self.oracle_mode_changed()
        def background():
            try:
                note = worker()
                self.after(0, lambda: self.complete_local_task(note, None))
            except Exception as exc:
                msg = str(exc)
                self.after(0, lambda: self.complete_local_task(None, msg))
        threading.Thread(target=background, daemon=True).start()

    def _refresh_transfer_meter(self, window):
        # Refresh while no Ollama updates arrive: otherwise the last observed
        # speed would misleadingly stay visible even after a stalled download.
        if not window.winfo_exists() or window is not getattr(self, "local_setup_window", None):
            return
        if self.local_actions_busy and self.pull_meter is not None:
            self._render_transfer_meter(self.pull_meter.snapshot())
        self.after(1000, lambda w=window: self._refresh_transfer_meter(w))

    def _render_transfer_meter(self, reading):
        phase = reading["phase"]
        speed = reading["speed_bps"]
        self.model_pull_speed_note.set(format_transfer_speed(speed))
        if phase == "downloading":
            idle = reading["idle_seconds"]
            if idle is not None and idle >= 15:
                self.model_pull_activity_note.set(
                    f"No new download data for {int(idle)} seconds. Ollama may be waiting or stalled; check the connection if this continues.")
            elif idle is not None and idle >= 3:
                self.model_pull_activity_note.set(
                    f"No new data for {int(idle)} seconds · current transfer speed 0 MB/s.")
            elif speed is None:
                self.model_pull_activity_note.set("Measuring current model layer · waiting for another progress update …")
            else:
                self.model_pull_activity_note.set("Transferring model data · speed averaged over recent Ollama updates.")
        elif phase == "verifying":
            self.model_pull_activity_note.set("Verifying / finalizing the model · no download speed applies.")
        elif phase == "ready":
            self.model_pull_activity_note.set("Ready · download and verification completed.")
        elif phase == "preparing":
            self.model_pull_activity_note.set("Contacting Ollama / preparing model layers …")
        else:
            self.model_pull_activity_note.set("Download a model to see its transfer speed.")

    def update_model_pull_progress(self, event):
        if not getattr(self, "local_actions_busy", False):
            return
        if not hasattr(self, "model_pull_bar") or not self.model_pull_bar.winfo_exists():
            return  # setup window may have been closed during a background pull
        if self.pull_meter is None:
            self.pull_meter = PullSpeedMeter()
        self._render_transfer_meter(self.pull_meter.observe(event))
        status = event.get("status", "Downloading")
        pct = event.get("percent")
        total = event.get("total")
        completed = event.get("completed")
        if pct is None:
            self.model_pull_bar.configure(mode="indeterminate")
            self.model_pull_bar.start(12)
            self.model_pull_note.set(status + " …")
        else:
            self.model_pull_bar.stop()
            self.model_pull_bar.configure(mode="determinate")
            self.model_pull_progress.set(pct)
            if isinstance(total, (int, float)) and isinstance(completed, (int, float)):
                done_gb, total_gb = completed / 1e9, total / 1e9
                self.model_pull_note.set(f"{status} · {pct:.1f}% · {done_gb:.2f} / {total_gb:.2f} GB")
            else:
                self.model_pull_note.set(f"{status} · {pct:.1f}%")

    def complete_local_task(self, note, error):
        self.local_actions_busy = False
        if hasattr(self, "model_pull_bar") and self.model_pull_bar.winfo_exists():
            self.model_pull_bar.stop()
            self.model_pull_bar.configure(mode="determinate")
        if error:
            self.model_pull_note.set("Download or setup stopped. See status below; you can retry without starting from scratch.")
            self.model_pull_speed_note.set("— MB/s    ·    — Mbps")
            self.model_pull_activity_note.set("Stopped · choose Download selected model to resume if needed.")
        elif note and note.startswith("Ready ·"):
            self.model_pull_progress.set(100)
            self.model_pull_note.set("100% · Download finished and model verified.")
            self.model_pull_speed_note.set("— MB/s    ·    — Mbps")
            self.model_pull_activity_note.set("Ready · download and verification completed.")
        if error:
            self.local_status.set("Setup problem: " + error)
            self.oracle_mode_changed()
            messagebox.showwarning("Local Oracle setup", error)
        else:
            self.local_status.set(note)
            self.oracle_mode_changed()

    def install_local_runtime(self):
        if sys.platform != "win32":
            messagebox.showinfo("Windows setup", "Automatic installation is available on Windows. On this system, use the official download link.")
            return
        if not messagebox.askyesno("Install Ollama?", "Campaign Forge will run Windows Package Manager (winget) to install Ollama.Ollama from its public package registry.\n\nThis downloads third-party software and may display an OS permission prompt. Continue?"):
            return
        self.run_local_setup_task("Installing Ollama", install_ollama_windows)

    def start_local_runtime(self):
        if not messagebox.askyesno("Start local service?", "Start the locally installed Ollama service? It runs separately from Campaign Forge on your computer."):
            return
        try:
            self.local_status.set(start_local_service())
            self.oracle_mode_changed()
        except Exception as exc:
            messagebox.showerror("Could not start Ollama", str(exc))

    def install_local_model(self):
        if self.local_actions_busy:
            messagebox.showinfo("Already working", "An installation or model download is already in progress.")
            return
        model = self.local_model.get()
        if not ollama_executable():
            messagebox.showwarning("Install Ollama first", "Ollama is not installed yet. Complete Step 1 first.")
            return
        if not messagebox.askyesno("Download local model?", f"Download {model} ({LOCAL_MODELS.get(model)}) using Ollama?\n\nThis uses the internet and disk space. The download happens only if you approve."):
            return
        self.pull_meter = PullSpeedMeter()
        self.model_pull_speed_note.set("— MB/s    ·    — Mbps")
        self.model_pull_activity_note.set("Connecting to Ollama and requesting model layers …")
        self.model_pull_progress.set(0)
        self.model_pull_note.set(f"Requesting {model} from Ollama …")
        self.model_pull_bar.configure(mode="indeterminate")
        self.model_pull_bar.start(12)

        def on_progress(event):
            # Main UI updates must run on Tk's event thread.
            self.after(0, lambda e=event: self.update_model_pull_progress(e))

        self.run_local_setup_task("Downloading " + model,
                                  lambda: download_model(model, progress_callback=on_progress))

    def open_cloud_setup(self):
        self.oracle_mode.set("cloud")
        self.oracle_mode_changed()
        win = tk.Toplevel(self)
        win.title("Greater Oracle · OpenAI API connection")
        win.geometry(f"670x455+{self.winfo_rootx() + 260}+{self.winfo_rooty() + 115}")
        win.resizable(False, False)
        win.configure(bg=BG)
        win.transient(self)
        area = ttk.Frame(win, padding=23)
        area.pack(fill="both", expand=True)
        ttk.Label(area, text="Connect to OpenAI's API", style="Section.TLabel").pack(anchor="w", pady=(0, 8))
        tk.Label(area, text="OpenAI's API is billed separately from ChatGPT subscriptions. Use your own API project and secret key. "
                 "Do not enter a ChatGPT password. Your key stays only in this app session and is never saved into the campaign.",
                 bg=BG, fg=SOFT, wraplength=612, justify="left", font=("Georgia", 10)).pack(anchor="w", pady=(0, 12))
        links = ttk.Frame(area)
        links.pack(fill="x", pady=(0, 13))
        ttk.Button(links, text="1 · Create / view API keys", command=lambda: webbrowser.open(OPENAI_KEYS)).pack(side="left", padx=(0, 7))
        ttk.Button(links, text="2 · Review API billing & limits", command=lambda: webbrowser.open(OPENAI_BILLING)).pack(side="left")
        ttk.Label(area, text="3 · Paste a project API key (hidden on screen)").pack(anchor="w", pady=(0, 4))
        key_entry = ttk.Entry(area, show="•", width=75)
        key_entry.pack(fill="x", pady=(0, 10))
        if self.cloud_key:
            key_entry.insert(0, self.cloud_key)
        row = ttk.Frame(area)
        row.pack(anchor="w", fill="x", pady=(0, 15))
        ttk.Label(row, text="Model:").pack(side="left", padx=(0, 9))
        ttk.Entry(row, textvariable=self.cloud_model, width=25).pack(side="left")
        tk.Label(area, text="A key entered here enables API requests, but is not a paid-plan login or proof of billing. The first actual consultation may incur costs. We request confirmation before each transfer.",
                 bg=BG, fg=SOFT, font=("Segoe UI", 9), wraplength=610, justify="left").pack(anchor="w", pady=(0, 12))
        actions = ttk.Frame(area)
        actions.pack(fill="x")
        def connect():
            value = key_entry.get().strip()
            if not value:
                messagebox.showwarning("API key missing", "Paste an API key from the OpenAI API platform, or choose Disconnect.", parent=win)
                return
            self.cloud_key = value
            self.cloud_status.set("API key entered for this session (not yet verified)")
            self.oracle_mode_changed()
            win.destroy()
        def disconnect():
            self.cloud_key = ""
            self.cloud_status.set("Not connected · API key required")
            self.oracle_mode_changed()
            win.destroy()
        ttk.Button(actions, text="Use key for this session", command=connect, style="Accent.TButton").pack(side="left")
        ttk.Button(actions, text="Disconnect / clear key", command=disconnect).pack(side="left", padx=9)
        ttk.Button(actions, text="Cancel", command=win.destroy).pack(side="right")

    def build_recovery(self, tab):
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(4, weight=1)
        ttk.Label(tab, text="Restore the story, not rewrite it.", style="Section.TLabel").grid(
            row=0, column=0, sticky="w", pady=(10, 4))
        ttk.Label(tab, text="Choose a PDF or Word manuscript. Review each suggested field and chapter before adding it to your project.",
                  style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=(0, 9))
        tools = ttk.Frame(tab)
        tools.grid(row=2, column=0, sticky="ew", pady=(0, 7))
        self.open_manuscript_button = ttk.Button(tools, text="+ Open manuscript  (PDF / DOCX)",
                   command=self.recover_document, style="Accent.TButton")
        self.open_manuscript_button.pack(side="left", padx=(0, 9))
        self.ai_organize_button = ttk.Button(tools, text="Organize with selected Oracle  ✦", command=self.recover_with_ai)
        self.ai_organize_button.pack(side="left", padx=(0, 7))
        self.ai_cancel_button = ttk.Button(tools, text="Cancel analysis", command=self.cancel_recovery,
                                            state="disabled")
        self.ai_cancel_button.pack(side="left", padx=(0, 9))
        ttk.Label(tools, text="Offline analysis first · AI is opt-in", style="Muted.TLabel").pack(side="left")
        self.import_status = tk.StringVar(value="No manuscript loaded. Select a file to see a reviewable import plan.")
        ttk.Label(tab, textvariable=self.import_status, style="Muted.TLabel", wraplength=1050).grid(
            row=3, column=0, sticky="ew", pady=(0, 8))
        area = ttk.Frame(tab)
        area.grid(row=4, column=0, sticky="nsew")
        area.columnconfigure(0, weight=3)
        area.columnconfigure(1, weight=2)
        area.rowconfigure(1, weight=1)
        ttk.Label(area, text="SUGGESTED DESTINATIONS  ·  DOUBLE-CLICK TO INCLUDE / EXCLUDE",
                  style="PanelSection.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 5))
        ttk.Label(area, text="SOURCE EXCERPT / IMPORT PREVIEW", style="PanelSection.TLabel").grid(
            row=0, column=1, sticky="w", padx=(12, 0), pady=(0, 5))
        left = ttk.Frame(area)
        left.grid(row=1, column=0, sticky="nsew")
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)
        self.import_tree = ttk.Treeview(left, columns=("kind", "origin"), show="tree headings", selectmode="browse")
        self.import_tree.heading("#0", text="Include  ·  Proposed title or field")
        self.import_tree.heading("kind", text="Destination")
        self.import_tree.heading("origin", text="Source")
        self.import_tree.column("#0", width=365, minwidth=150, stretch=True)
        self.import_tree.column("kind", width=104, minwidth=72, stretch=False)
        self.import_tree.column("origin", width=85, minwidth=60, stretch=False)
        self.import_tree.grid(row=0, column=0, sticky="nsew")
        tscroll = ttk.Scrollbar(left, orient="vertical", command=self.import_tree.yview)
        tscroll.grid(row=0, column=1, sticky="ns")
        self.import_tree.configure(yscrollcommand=tscroll.set)
        self.import_tree.bind("<<TreeviewSelect>>", self.preview_candidate)
        self.import_tree.bind("<Double-Button-1>", self.toggle_candidate)
        self.import_tree.bind("<space>", self.toggle_candidate)
        self.import_preview = self.text_box(area, height=13, width=36)
        self.import_preview.grid(row=1, column=1, sticky="nsew", padx=(12, 0))
        self.import_preview.configure(state="disabled")
        actions = ttk.Frame(tab)
        actions.grid(row=5, column=0, sticky="ew", pady=(8, 10))
        ttk.Button(actions, text="Select all", command=lambda: self.select_candidates(True)).pack(side="left", padx=(0, 4))
        ttk.Button(actions, text="Select none", command=lambda: self.select_candidates(False)).pack(side="left", padx=4)
        self.import_keep_reference = tk.BooleanVar(value=True)
        ttk.Checkbutton(actions, text="Keep source text as reference", variable=self.import_keep_reference).pack(side="left", padx=12)
        ttk.Button(actions, text="Undo last import", command=self.undo_import).pack(side="right", padx=(5, 0))
        ttk.Button(actions, text="View analysis report", command=self.view_import_report).pack(side="right", padx=(5, 7))
        self.commit_import_button = ttk.Button(actions, text="Add selected to campaign", style="Accent.TButton", command=self.commit_import)
        self.commit_import_button.pack(side="right")

    def recover_document(self):
        path = filedialog.askopenfilename(title="Recover an existing campaign manuscript",
                                          filetypes=[("Campaign manuscripts", "*.pdf *.docx *.txt *.md")])
        if not path:
            return
        try:
            doc = extract_document(path)
            proposal = build_local_proposal(doc)
        except Exception as exc:
            messagebox.showerror("Manuscript could not be read", str(exc))
            return
        self.import_doc = doc
        self.show_proposal(proposal)
        if doc["chars"] > 30000:
            passes = len(split_manuscript_for_ai(doc["text"]))
            self.import_status.set(self.import_status.get() +
                                   f" · Local AI can analyze this in {passes} passages automatically")

    def show_proposal(self, proposal):
        self.import_proposal = proposal
        self.import_choices = set()
        self.import_tree.delete(*self.import_tree.get_children())
        for key, candidate in proposal["values"].items():
            uid = "field:" + key
            self.import_choices.add(uid)
            self.import_tree.insert("", "end", iid=uid, text="☑  " + LABELS[key],
                                    values=("Overview", candidate.get("source", "")))
        for index, candidate in enumerate(proposal["entries"]):
            uid = "entry:" + str(index)
            default_include = candidate.get("confidence") not in ("archive", "needs-review")
            if default_include:
                self.import_choices.add(uid)
            self.import_tree.insert("", "end", iid=uid,
                                    text=("☑  " if default_include else "☐  ") + candidate["title"][:95],
                                    values=(candidate["category"], candidate.get("location", "") or "Document"))
        self.import_report = list(proposal.get("warnings", []))
        warnings = "  |  ".join(proposal.get("warnings", []))
        self.import_status.set(f"{proposal['source']} · {proposal['method']} · "
            f"{len(proposal['values'])} overview suggestions · {len(proposal['entries'])} story sections"
            + ("    ⚠ " + warnings[:250] + ("…" if len(warnings)>250 else "") if warnings else ""))
        items = self.import_tree.get_children()
        if items:
            self.import_tree.selection_set(items[0])
            self.preview_candidate()

    def view_import_report(self):
        if not self.import_proposal:
            messagebox.showinfo("No import report", "Load a manuscript first.")
            return
        lines = self.import_report or ["No warnings from the latest analysis."]
        win = tk.Toplevel(self)
        win.title("Campaign Forge — Import analysis report")
        win.geometry("780x475")
        win.configure(bg=BG)
        ttk.Label(win, text="Import analysis report", style="Section.TLabel").pack(anchor="w", padx=15, pady=12)
        detail = self.text_box(win, height=15)
        detail.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        detail.insert("1.0", "\n\n".join(f"{i}. {line}" for i, line in enumerate(lines, 1)))
        detail.configure(state="disabled")
        ttk.Button(win, text="Close", command=win.destroy).pack(anchor="e", padx=15, pady=(0, 13))

    def preview_candidate(self, event=None):
        selection = self.import_tree.selection()
        if not selection or not self.import_proposal:
            return
        key = selection[0]
        if key.startswith("field:"):
            name = key.split(":", 1)[1]
            candidate = self.import_proposal["values"][name]
            text = f"DESTINATION: {LABELS[name]}\nCONFIDENCE: {candidate.get('confidence', 'review')}\nSOURCE: {candidate.get('source', '')}\n\n" + candidate["value"]
        else:
            index = int(key.split(":", 1)[1])
            candidate = self.import_proposal["entries"][index]
            text = (f"{candidate['category'].upper()}  /  {candidate['title']}\n"
                    f"SOURCE: {candidate.get('source','')}  {candidate.get('location','')}\n"
                    f"DM ONLY: {'Yes' if candidate.get('gm_only') else 'No'}\n\n" + candidate["content"])
        self.import_preview.configure(state="normal")
        self.import_preview.delete("1.0", "end")
        self.import_preview.insert("1.0", text)
        self.import_preview.configure(state="disabled")

    def toggle_candidate(self, event=None):
        if event is not None and hasattr(event, "y"):
            item = self.import_tree.identify_row(event.y)
        else:
            item = (self.import_tree.selection() or [None])[0]
        if not item:
            return
        if item in self.import_choices:
            self.import_choices.remove(item)
            symbol = "☐"
        else:
            self.import_choices.add(item)
            symbol = "☑"
        orig = self.import_tree.item(item, "text")
        self.import_tree.item(item, text=symbol + orig[1:])

    def select_candidates(self, include):
        for item in self.import_tree.get_children():
            label = self.import_tree.item(item, "text")
            self.import_tree.item(item, text=("☑" if include else "☐") + label[1:])
        self.import_choices = set(self.import_tree.get_children()) if include else set()

    def commit_import(self):
        if self.import_proposal is None:
            messagebox.showinfo("Choose a manuscript", "Open a PDF or DOCX first.")
            return
        if not self.import_choices:
            messagebox.showinfo("No sections selected", "Select at least one section to import.")
            return
        self.gather_all()
        previous = copy.deepcopy(self.data)
        imported, stats = apply_proposal(self.data, self.import_proposal, self.import_choices,
                                          keep_reference=self.import_keep_reference.get())
        message = f"Fill empty overview fields: {stats['fields']}\nAdd story entries: {stats['entries']}"
        if stats["skipped_existing_fields"]:
            message += "\n\nUnchanged existing fields: " + ", ".join(stats["skipped_existing_fields"])
        if stats["skipped_duplicate_entries"]:
            message += "\n\nDuplicate titles skipped: " + ", ".join(stats["skipped_duplicate_entries"][:12])
        if not messagebox.askyesno("Review import changes", message + "\n\nApply these changes? Nothing will be overwritten."):
            return
        self.pre_import_snapshot = previous
        self.data = imported
        self.load_into_ui()
        self.mark_dirty()
        self.status.set("Manuscript imported; review your Atlas & Chronicles, then Ctrl+S to save. Undo Last Import is available.")
        messagebox.showinfo("Manuscript recovered", message + "\n\nReview the new entries before publishing.")

    def undo_import(self):
        if self.pre_import_snapshot is None:
            messagebox.showinfo("Nothing to undo", "There is no previous import in this session.")
            return
        if not messagebox.askyesno("Undo last import", "Restore your campaign as it was immediately before the last import? Later unsaved changes will be lost."):
            return
        self.data = self.pre_import_snapshot
        self.pre_import_snapshot = None
        self.load_into_ui()
        self.mark_dirty()
        self.status.set("Last import undone. Save your campaign if you wish to keep this version.")

    def recover_with_ai(self):
        if self.import_busy:
            return
        if not self.import_doc:
            messagebox.showinfo("Open a manuscript", "Start by opening a PDF or DOCX manuscript.")
            return
        mode = self.oracle_mode.get()
        if mode == "scribe":
            messagebox.showinfo("The Scribe", "The offline manuscript organizer is already available. Choose a Local or Greater Oracle for optional AI analysis.")
            return
        if mode == "cloud" and not self.cloud_key:
            messagebox.showinfo("API setup needed", "Connect an OpenAI API key under Creative Consultation first.")
            return
        source = self.import_doc
        if mode == "cloud":
            notice = f"Send the FULL extracted manuscript ({source['chars']:,} characters) to OpenAI for optional organization?\n\nAPI charges may apply."
        else:
            passes = len(split_manuscript_for_ai(source["text"]))
            notice = (f"Analyze {source['chars']:,} characters in {passes} local passage{'s' if passes != 1 else ''}?\n\n"
                      "Each passage is processed on your computer, one at a time. A large campaign may take many minutes. "
                      "Progress appears below; cancellation takes effect after the current passage. "
                      "Nothing is sent to OpenAI by Campaign Forge.")
        if not self.confirm_oracle_notice("Review AI manuscript organization", notice +
                                         "\n\nResults are only PREVIEW suggestions. You must approve each import.",
                                         "hide_import_notice"):
            return
        self.import_busy = True
        self.import_cancel.clear()
        self.ai_organize_button.configure(state="disabled")
        self.open_manuscript_button.configure(state="disabled")
        self.commit_import_button.configure(state="disabled")
        self.ai_cancel_button.configure(state="normal" if mode == "local" else "disabled")
        self.import_status.set("Starting " + ("Local" if mode == "local" else "Greater") + " Oracle analysis … original preview preserved.")
        doc = copy.deepcopy(source)
        selected_model = self.local_model.get() if mode == "local" else self.cloud_model.get()
        selected_key = self.cloud_key
        def background():
            try:
                if mode == "local":
                    def progress(i, total, stage):
                        note = (f"Local Oracle · passage {i} of {total} · "
                                + {"processing":"analyzing…", "retrying":"retrying unexpected response…",
                                   "needs-review":"needs review", "completed":"completed"}.get(stage, stage)
                                + " · existing preview and campaign unchanged")
                        self.after(0, lambda note=note: self.import_status.set(note))
                    result = organize_local(doc, model=selected_model, progress_callback=progress,
                                            cancel_event=self.import_cancel)
                else:
                    result = organize_with_ai(doc, selected_key, selected_model)
                self.after(0, lambda: self.finish_recovery(result, None))
            except InterruptedError as exc:
                self.after(0, lambda msg=str(exc): self.finish_recovery(None, msg, cancelled=True))
            except Exception as exc:
                message = str(exc)
                self.after(0, lambda: self.finish_recovery(None, message))
        threading.Thread(target=background, daemon=True).start()

    def cancel_recovery(self):
        if self.import_busy:
            self.import_cancel.set()
            self.ai_cancel_button.configure(state="disabled")
            self.import_status.set("Cancellation requested · finishing the current passage. Existing preview remains available.")

    def finish_recovery(self, result, error, cancelled=False):
        self.import_busy = False
        self.ai_organize_button.configure(state="normal" if self.oracle_mode.get() != "scribe" else "disabled")
        self.open_manuscript_button.configure(state="normal")
        self.commit_import_button.configure(state="normal")
        self.ai_cancel_button.configure(state="disabled")
        if error:
            if not cancelled:
                messagebox.showerror("AI organizing failed", error)
            self.import_status.set(("Analysis cancelled" if cancelled else "AI analysis unsuccessful") +
                                   " · the existing offline import preview is still available; no changes applied.")
            return
        self.show_proposal(result)
        review_count = sum(e.get("confidence") == "needs-review" for e in result.get("entries", []))
        if review_count:
            messagebox.showwarning("Review needed", f"The AI could not interpret {review_count} passage(s) reliably. "
                "Those passages were preserved in the import preview under 'Needs review' and are not selected by default. "
                "You can review them, include them manually, or use the offline suggestions. "
                "Choose View analysis report for more detail.")

    def build_publish(self):
        tab = self.publish_tab
        self.export_dm_only = tk.BooleanVar(value=True)
        self.build_architect(tab)
        options=ttk.Frame(tab)
        options.pack(fill="x",pady=(12,5))
        ttk.Checkbutton(options,text="DM edition: include DM-only information, encounters and combat blocks",
                        variable=self.export_dm_only).pack(side="left")
        ttk.Button(options,text="Manage documents in The Archives",
                   command=lambda:self.tabs.select(self.archives_tab)).pack(side="right")
        ttk.Label(tab,text="For a player-safe PDF, uncheck DM edition. Publication uses the approved outline. Save your editable project separately.",
                  style="Muted.TLabel").pack(anchor="w",pady=7)
        ttk.Separator(tab).pack(fill="x",pady=9)
        ttk.Label(tab,text="Legacy project reference excerpts",style="PanelSection.TLabel").pack(anchor="w",pady=(0,5))
        refs=ttk.Frame(tab); refs.pack(fill="both",expand=True)
        self.ref_list=self.list_box(refs,height=3,width=34);self.ref_list.pack(side="left",fill="y",padx=(0,10))
        self.ref_list.bind("<<ListboxSelect>>",self.on_ref_selected)
        ctr=ttk.Frame(refs);ctr.pack(side="left",fill="y")
        ttk.Button(ctr,text="+ Add references",command=self.add_references).pack(fill="x",pady=3)
        ttk.Button(ctr,text="Remove",command=self.remove_reference).pack(fill="x",pady=3)
        self.ref_detail=self.text_box(refs,height=3,width=50,state="disabled");self.ref_detail.pack(side="left",fill="both",expand=True,padx=12)

    # ---- campaign project management ----
    def gather_all(self):
        self.capture_overview()
        self.capture_entry()
        self._capture_character()
        self._capture_encounter()
        return self.data

    def capture_overview(self):
        for key, widget in self.meta.items():
            self.data[key] = widget.get().strip()
        for key, widget in self.overview_text.items():
            self.data[key] = widget.get("1.0", "end-1c")

    def load_into_ui(self):
        self.project_epoch += 1
        self.loading = True
        for key, widget in self.meta.items():
            if isinstance(widget, ttk.Combobox):
                widget.set(self.data.get(key, "System-neutral"))
            else:
                widget.delete(0, "end")
                widget.insert(0, self.data.get(key, ""))
        for key, widget in self.overview_text.items():
            widget.delete("1.0", "end")
            widget.insert("1.0", self.data.get(key, ""))
        self.current_entry_id = None
        self.current_map_id = None
        self.current_ref_id = None
        self.entry_filter.set("All content")
        self.refresh_entry_list()
        self.refresh_map_list()
        self.refresh_ref_list()
        self.refresh_new_workspaces()
        self.dirty = False
        self.loading = False
        self.oracle_target = None
        self.oracle_target_label.set("Target: none — use ✦ Improve with Oracle beside a field")
        self.ai_has_response = bool(self.oracle_turns)
        self.field_undo.clear()  # undo stacks never cross different loaded projects
        self.refresh_oracle_transcript()
        self._update_window_title()

    def ask_to_discard(self):
        if not self.dirty:
            return True
        answer = messagebox.askyesnocancel("Unsaved changes", "Save your campaign changes first?")
        if answer is None:
            return False
        if answer and not self.save():
            return False
        return True

    def new_file(self):
        if not self.ask_to_discard():
            return
        self.data = new_campaign()
        self.project_action_undo = None
        self.project_path = None
        self.load_into_ui()
        self.status.set("New campaign — enter your premise and save the project.")

    def _remember_project_folder(self, path):
        self.last_project_dir = Path(path).resolve().parent
        try:
            remember_project_directory(path)
        except OSError:
            pass  # Failure to remember a folder never prevents saving projects.

    def open_file(self):
        if not self.ask_to_discard():
            return
        kwargs = {'title': 'Open Campaign Forge project',
                  'filetypes': [('Campaign Forge Project', '*.campaign.json'), ('JSON', '*.json')]}
        if self.last_project_dir and self.last_project_dir.is_dir():
            kwargs['initialdir'] = str(self.last_project_dir)
        path = filedialog.askopenfilename(**kwargs)
        if not path:
            return
        try:
            new_data = load_campaign(path)
        except Exception as exc:
            messagebox.showerror("Could not open project", str(exc))
            return
        self.data = new_data
        self.project_action_undo = None
        self.project_path = path
        self._remember_project_folder(path)
        self.load_into_ui()
        self.status.set(f"Opened: {Path(path).name}")

    def _project_saved(self, path):
        self.dirty = False
        self._remember_project_folder(path)
        self._update_window_title()
        self.status.set(f"Saved: {Path(path).name}  —  {Path(path).parent}")

    def save(self):
        self.gather_all()
        if not self.project_path:
            return self.save_as()
        try:
            save_campaign(self.data, self.project_path)
        except Exception as exc:
            messagebox.showerror("Save error", str(exc))
            return False
        self._project_saved(self.project_path)
        return True

    def save_as(self):
        self.gather_all()
        folder = (Path(self.project_path).parent if self.project_path
                  else self.last_project_dir or (Path.home() / 'Documents'))
        if not folder.is_dir():
            folder = Path.home()
        suggested = suggest_save_name(self.data.get('title', ''), folder, self.project_path)
        path = filedialog.asksaveasfilename(
            title='Save campaign project as', defaultextension='.campaign.json',
            filetypes=[('Campaign Forge Project', '*.campaign.json')],
            initialdir=str(folder), initialfile=suggested)
        if not path:
            return False
        # Write before switching the active project. A failed Save As leaves the
        # original Save destination intact.
        try:
            save_campaign(self.data, path)
        except Exception as exc:
            messagebox.showerror('Save error', str(exc))
            return False
        self.project_path = path
        self._project_saved(path)
        return True

    def on_exit(self):
        if not self.ask_to_discard():
            return
        if self.oracle_turns and self.last_transcript_export < len(self.oracle_turns):
            answer = messagebox.askyesnocancel(
                "Oracle conversation",
                "Save this Oracle conversation as a .txt file before closing?\n\n"
                "Yes: choose where to save it.\nNo: discard this session permanently.\nCancel: return to Campaign Forge.")
            if answer is None:
                return
            if answer and not self.save_oracle_transcript():
                return
        self.destroy()

    # ---- story library ----
    def visible_entries(self):
        f = self.entry_filter.get()
        return [e for e in self.data["entries"] if f == "All content" or e["category"] == f]

    def refresh_entry_list(self, selected=None):
        self.capture_entry()
        self.loading = True
        self.entry_list.delete(0, "end")
        entries = self.visible_entries()
        for e in entries:
            prefix = "[DM] " if e.get("gm_only") else ""
            self.entry_list.insert("end", f"{prefix}{e['title']}")
        target = selected or self.current_entry_id
        ix = next((i for i, e in enumerate(entries) if e["id"] == target), -1)
        self.entry_list.selection_clear(0, "end")
        self.current_entry_id = None
        if ix >= 0:
            self.entry_list.selection_set(ix)
            self.current_entry_id = entries[ix]["id"]
            self.show_entry(entries[ix])
        else:
            self.show_entry(None)
        self.loading = False

    def capture_entry(self):
        if self.current_entry_id is None or self.loading:
            return
        e = next((x for x in self.data["entries"] if x["id"] == self.current_entry_id), None)
        if not e:
            return
        e["title"] = self.entry_name.get().strip() or "Untitled"
        e["category"] = self.entry_kind.get() or "Chapter"
        e["content"] = self.entry_body.get("1.0", "end-1c")
        e["gm_only"] = self.gm_only_var.get()

    def show_entry(self, e):
        self.entry_name.delete(0, "end")
        self.entry_kind.set("")
        self.entry_body.delete("1.0", "end")
        self.gm_only_var.set(False)
        if e:
            self.entry_name.insert(0, e.get("title", ""))
            self.entry_kind.set(e.get("category", "Chapter"))
            self.entry_body.insert("1.0", e.get("content", ""))
            self.gm_only_var.set(e.get("gm_only", False))

    def on_entry_selected(self, event=None):
        if self.loading:
            return
        sel = self.entry_list.curselection()
        if not sel:
            return
        entries = self.visible_entries()
        if sel[0] >= len(entries):
            return
        new_id = entries[sel[0]]["id"]
        if new_id == self.current_entry_id:
            return
        self.capture_entry()
        self.loading = True
        self.current_entry_id = new_id
        self.show_entry(entries[sel[0]])
        self.loading = False

    def add_entry(self):
        self.capture_entry()
        kind = self.entry_filter.get() if self.entry_filter.get() in CATEGORIES else "Chapter"
        title = simpledialog.askstring("New story entry", "Title:", initialvalue="New " + kind, parent=self)
        if title is None:
            return
        e = new_entry(kind, title.strip() or "Untitled")
        self.data["entries"].append(e)
        self.mark_dirty()
        self.refresh_entry_list(e["id"])

    def duplicate_entry(self):
        self.capture_entry()
        e = next((e for e in self.data["entries"] if e["id"] == self.current_entry_id), None)
        if e is None:
            return
        copied = new_entry(e["category"], e["title"] + " (copy)", e["content"], e["gm_only"])
        self.data["entries"].append(copied)
        self.mark_dirty()
        self.refresh_entry_list(copied["id"])

    def delete_entry(self):
        if self.current_entry_id is None:
            return
        if not messagebox.askyesno("Delete entry", "Delete this story entry permanently?"):
            return
        self.data["entries"] = [e for e in self.data["entries"] if e["id"] != self.current_entry_id]
        self.current_entry_id = None
        self.refresh_entry_list()
        self.mark_dirty()

    def save_entry_changes(self):
        self.capture_entry()
        self.mark_dirty()
        self.refresh_entry_list(self.current_entry_id)
        self.status.set("Entry updated in project. Save the campaign file with Ctrl+S.")

    # ---- maps ----
    def refresh_map_list(self, selected=None):
        self.loading = True
        self.map_list.delete(0, "end")
        for m in self.data["maps"]:
            self.map_list.insert("end", m["title"])
        self.current_map_id = None
        maps = self.data["maps"]
        target = selected or (maps[0]["id"] if maps else None)
        ix = next((i for i, m in enumerate(maps) if m["id"] == target), -1)
        if ix >= 0:
            self.map_list.selection_set(ix)
            self.current_map_id = maps[ix]["id"]
        self.loading = False
        self.draw_map()

    def selected_map(self):
        return next((m for m in self.data["maps"] if m["id"] == self.current_map_id), None)

    def on_map_selected(self, event=None):
        if self.loading:
            return
        sel = self.map_list.curselection()
        if sel and sel[0] < len(self.data["maps"]):
            self.current_map_id = self.data["maps"][sel[0]]["id"]
            self.draw_map()

    def select_tool(self, name):
        self.tool = name
        self.map_mode = 'paint'
        self.map_tool_label.config(text='Paint terrain: '+name.title())

    def map_enable_props(self):
        self.map_mode='props'
        self.map_tool_label.configure(text='Arrange props: '+self.map_prop_kind.get()+' — click to place, drag to move')

    def _map_prop_asset(self, ident):
        return self.archive.source_path(ident,self.data.get('project_id'))

    def map_resize_prop(self):
        m=self.selected_map();idx=self.map_selected_prop_index
        if not m or idx is None or idx>=len(m.get('objects',[])):
            messagebox.showinfo('Select a prop','Click a placed prop on the map first.');return
        obj=m['objects'][idx]
        obj['w']=max(1,min(12,int(self.map_prop_width.get())))
        obj['h']=max(1,min(12,int(self.map_prop_height.get())))
        self.draw_map();self.mark_dirty()

    def map_rotate_prop(self):
        m=self.selected_map();idx=self.map_selected_prop_index
        if not m or idx is None or idx>=len(m.get('objects',[])):
            messagebox.showinfo('Select a prop','Click a placed prop on the map first.');return
        obj=m['objects'][idx];obj['rotation']=(int(obj.get('rotation',0))+90)%360
        self.draw_map();self.mark_dirty()
        self.status.set(f'Prop rotated to {obj["rotation"]} degrees.')

    def map_import_prop(self):
        m=self.selected_map()
        if not m:messagebox.showinfo('No map','Create or select a map first.');return
        path=filedialog.askopenfilename(title='Import a custom map prop',filetypes=[('PNG with transparency','*.png'),('Image prop','*.jpg *.jpeg *.webp')])
        if not path:return
        try:
            with Image.open(path) as src:width,height=src.size
            if width<32 or height<32:raise ValueError('Images must be at least 32 by 32 pixels.')
            if width>8192 or height>8192:raise ValueError('Image exceeds the 8192px safe limit.')
            tiles_x=max(1,min(12,int(self.map_prop_width.get())))
            tiles_y=max(1,min(12,int(self.map_prop_height.get())))
            if not messagebox.askyesno('Import custom prop?',
                f'{Path(path).name}\nImage resolution: {width} × {height} px\nPlacement size: {tiles_x} × {tiles_y} grid squares\n\n'
                'The image will be copied into The Archives and placed as an editable prop. Continue?'):
                return
            ident=self.archive.add(path,'campaign',self.data['project_id'],category='Map prop')
            m.setdefault('objects',[]).append({'kind':Path(path).stem,'x':0,'y':0,'w':tiles_x,'h':tiles_y,'rotation':0,'asset_archive_id':ident})
            self.map_selected_prop_index=len(m['objects'])-1
            self.map_enable_props();self.draw_map();self.mark_dirty();self.archive_refresh()
            self.status.set('Image prop imported. Drag it to the intended position; use Resize selected to change its footprint.')
        except Exception as exc:messagebox.showerror('Prop import failed',str(exc))

    def _map_background(self,map_data):
        ident=map_data.get('background_archive_id')
        if not ident:return None
        try:return self.archive.source_path(ident,self.data.get('project_id'))
        except (KeyError,PermissionError,OSError):return None

    def import_map_background(self):
        m=self.selected_map()
        if m is None:
            messagebox.showinfo('No map','Create or select a map first.');return
        path=filedialog.askopenfilename(title='Import map background',filetypes=[('Image backgrounds','*.png *.jpg *.jpeg *.webp')])
        if not path:return
        try:
            ident=self.archive.add(path,'campaign',self.data['project_id'],category='Map background')
            m['background_archive_id']=ident
        except Exception as exc:messagebox.showerror('Map import failed',str(exc));return
        self.draw_map();self.mark_dirty();self.archive_refresh()
        self.status.set('Imported map image into Archives. Editable props and terrain sit above it.')

    def remove_map_background(self):
        m=self.selected_map()
        if not m:return
        m.pop('background_archive_id',None);self.draw_map();self.mark_dirty()
        # The original image remains available in The Archives; this only unlinks it.

    def map_remove_prop(self,event):
        m=self.selected_map()
        if not m:return
        x,y=event.x//self.map_size,event.y//self.map_size
        objects=m.get('objects',[])
        match=next((i for i,o in reversed(list(enumerate(objects))) if o.get('x',0)<=x<o.get('x',0)+max(1,int(o.get('w',1))) and o.get('y',0)<=y<o.get('y',0)+max(1,int(o.get('h',1)))),None)
        if match is not None:
            objects.pop(match);self.map_selected_prop_index=None;self.draw_map();self.mark_dirty()

    def draw_map(self):
        self.map_canvas.delete('all')
        m=self.selected_map()
        if not m:
            self.map_canvas.create_text(50,55,text='Create a map to begin.',anchor='nw',fill=FG)
            return
        scale=max(8,min(27,int(650/m['cols']),int(420/m['rows'])))
        self.map_size=scale
        try:
            im=render_map(m,size=scale,background=self._map_background(m),asset_resolver=self._map_prop_asset)
            self.map_preview_image=ImageTk.PhotoImage(im,master=self)
            self.map_canvas.create_image(0,0,image=self.map_preview_image,anchor='nw')
        except Exception as exc:
            self.map_canvas.create_text(25,25,text='Map preview unavailable: '+str(exc)[:130],anchor='nw',fill=FG)

    def paint_at(self,event):
        m=self.selected_map()
        if m is None:return
        x,y=event.x//self.map_size,event.y//self.map_size
        if not (0<=x<m['cols'] and 0<=y<m['rows']):return
        if self.map_mode=='props':
            objects=m.setdefault('objects',[])
            if self.map_drag_index is None:
                match=next((i for i,o in reversed(list(enumerate(objects))) if o.get('x',0)<=x<o.get('x',0)+int(o.get('w',1)) and o.get('y',0)<=y<o.get('y',0)+int(o.get('h',1))),None)
                if match is None:
                    objects.append({'kind':self.map_prop_kind.get(),'x':x,'y':y,'w':max(1,int(self.map_prop_width.get())),'h':max(1,int(self.map_prop_height.get())),'rotation':0})
                    match=len(objects)-1
                self.map_drag_index=match
                self.map_selected_prop_index=match
                self.map_prop_width.set(int(objects[match].get('w',1)))
                self.map_prop_height.set(int(objects[match].get('h',1)))
            objects[self.map_drag_index]['x']=x;objects[self.map_drag_index]['y']=y
        else:
            if m['tiles'][y][x]==self.tool:return
            m['tiles'][y][x]=self.tool
        self.mark_dirty();self.draw_map()

    def add_map(self):
        title = simpledialog.askstring("New map", "Map name:", initialvalue="Unexplored Ruins", parent=self)
        if title is None:
            return
        cols = simpledialog.askinteger("Map width", "Grid columns (4–40):", initialvalue=24, minvalue=4, maxvalue=40, parent=self)
        if cols is None:
            return
        rows = simpledialog.askinteger("Map height", "Grid rows (4–25):", initialvalue=16, minvalue=4, maxvalue=25, parent=self)
        if rows is None:
            return
        m = new_map(title.strip() or "Untitled Map", cols, rows)
        self.data["maps"].append(m)
        self.refresh_map_list(m["id"])
        self.mark_dirty()

    def delete_map(self):
        if not self.current_map_id:
            return
        if not messagebox.askyesno("Delete map", "Delete selected map?"):
            return
        self.data["maps"] = [m for m in self.data["maps"] if m["id"] != self.current_map_id]
        self.refresh_map_list()
        self.mark_dirty()

    def export_map_png(self):
        m = self.selected_map()
        if not m:
            messagebox.showinfo("No map", "Create or select a map first.")
            return
        safe = "".join(c if c.isalnum() or c in " _-" else "_" for c in m["title"])
        path = filedialog.asksaveasfilename(defaultextension=".png", initialfile=safe + ".png",
                                            filetypes=[("PNG image", "*.png")])
        if not path:
            return
        try:
            export_map(m,path,background=self._map_background(m),asset_resolver=self._map_prop_asset)
            messagebox.showinfo("Map exported", f"Saved PNG:\n{path}\n\nUpload it manually using D&D Beyond Maps' Upload Map feature.")
        except Exception as exc:
            messagebox.showerror("Map export error", str(exc))

    # ---- references ----
    def refresh_ref_list(self):
        self.ref_list.delete(0, "end")
        for r in self.data["references"]:
            self.ref_list.insert("end", r["name"] + (" (excerpt)" if r.get("truncated") else ""))
        self.show_ref_text("")

    def show_ref_text(self, text):
        self.ref_detail.configure(state="normal")
        self.ref_detail.delete("1.0", "end")
        self.ref_detail.insert("1.0", text)
        self.ref_detail.configure(state="disabled")

    def on_ref_selected(self, event=None):
        sel = self.ref_list.curselection()
        if sel and sel[0] < len(self.data["references"]):
            r = self.data["references"][sel[0]]
            self.current_ref_id = r["id"]
            self.show_ref_text(r["text"][:4000] or "No text was found.")

    def add_references(self):
        paths = filedialog.askopenfilenames(title="Import reference materials",
            filetypes=[("Reference documents", "*.txt *.md *.docx *.pdf")])
        failures = []
        for path in paths:
            try:
                self.data["references"].append(import_reference(path))
                self.mark_dirty()
            except Exception as exc:
                failures.append(f"{Path(path).name}: {exc}")
        self.refresh_ref_list()
        if failures:
            messagebox.showwarning("Some references could not be imported", "\n".join(failures))
        elif paths:
            self.status.set(f"Imported {len(paths)} reference(s). Save your project to store the extracted text.")

    def remove_reference(self):
        sel = self.ref_list.curselection()
        if not sel:
            return
        self.data["references"].pop(sel[0])
        self.current_ref_id = None
        self.refresh_ref_list()
        self.mark_dirty()

    # ---- Oracle conversation and user-approved field editing ----
    def confirm_oracle_notice(self, title, message, preference_key):
        if self.preferences.get(preference_key, False):
            return True
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.geometry("610x355")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.configure(bg=BG)
        value = {"approved": False}
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=title, style="Section.TLabel").pack(anchor="w", pady=(0, 10))
        tk.Label(frame, text=message, justify="left", wraplength=490, bg=BG, fg=FG,
                 font=("Segoe UI", 10)).pack(fill="x", anchor="w")
        skip = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="Don't show this notice again", variable=skip).pack(anchor="w", pady=(14, 8))
        actions = ttk.Frame(frame)
        actions.pack(side="bottom", fill="x")
        def finish(approved):
            value["approved"] = approved
            if approved and skip.get():
                self.preferences[preference_key] = True
                try:
                    save_preferences(self.preferences)
                except OSError:
                    pass  # preferences never prevent a consultation
            dialog.destroy()
        ttk.Button(actions, text="Cancel", command=lambda: finish(False)).pack(side="right", padx=4)
        ttk.Button(actions, text="Continue", style="Accent.TButton",
                   command=lambda: finish(True)).pack(side="right")
        dialog.protocol("WM_DELETE_WINDOW", lambda: finish(False))
        dialog.grab_set()
        self.wait_window(dialog)
        return value["approved"]

    def target_value(self, target):
        if target.get("project_epoch") != self.project_epoch:
            return None  # past-session suggestions must not edit another campaign
        if target["kind"] == "overview":
            widget = self.overview_text.get(target["key"])
            if widget is None:
                return None
            return widget.get("1.0", "end-1c")
        entry = next((e for e in self.data["entries"] if e["id"] == target["key"]), None)
        if entry is None:
            return None
        if target["key"] == self.current_entry_id:
            return self.entry_body.get("1.0", "end-1c")
        return entry.get("content", "")

    def send_field_to_oracle(self, kind, key, label):
        if kind == "entry" and key is None:
            messagebox.showinfo("Select an entry", "Choose a story entry first.")
            return
        target = {"kind": kind, "key": key, "label": label, "project_epoch": self.project_epoch}
        current = self.target_value(target)
        if current is None:
            messagebox.showwarning("Field unavailable", "The selected field no longer exists.")
            return
        target["baseline"] = current
        self.oracle_target = target
        self.oracle_reply_kind.set("Revise selected field")
        self.oracle_target_label.set("Destination: " + label + " · suggestions require approval")
        self.tabs.select(self.ai_tab)
        self.oracle_panels.select(1)
        if self.oracle_mode.get() != "scribe" and self.oracle_setup_visible:
            self.toggle_oracle_setup()  # more room for the active transcript
        self.ai_question.delete("1.0", "end")
        if not current.strip():
            self.ai_question.insert("1.0", "Draft only this field from my uploaded manuscript. Do not invent new characters, conflicts, or events. If the source lacks enough detail, tell me instead.")
        else:
            self.ai_question.insert("1.0", DEFAULT_FIELD_REQUEST)
        self.ai_question.focus_set()
        self.status.set("Editing ONLY " + label + ". Background lore is read-only. Review your instructions and Consult.")

    def selected_oracle_response(self):
        if self.selected_oracle_turn is None or not (0 <= self.selected_oracle_turn < len(self.oracle_turns)):
            return None
        return self.oracle_turns[self.selected_oracle_turn]

    def choose_oracle_turn(self, idx):
        self.selected_oracle_turn = idx
        self.refresh_oracle_transcript(scroll_to_end=False)
        turn = self.selected_oracle_response()
        if turn and turn.get("target"):
            self.oracle_target = copy.deepcopy(turn["target"])
            self.oracle_target_label.set("Destination: " + self.oracle_target["label"] + " · preview before applying")

    def refresh_oracle_transcript(self, scroll_to_end=True):
        if not hasattr(self, "ai_output"):
            return
        t = self.ai_output
        t.configure(state="normal")
        t.delete("1.0", "end")
        if not self.oracle_turns:
            t.insert("end", "Consultations will appear here as a scrollable conversation.\n"
                            "Your transcript stays in memory until you export it or close Campaign Forge.\n", "oracle_body")
        for idx, turn in enumerate(self.oracle_turns):
            start = t.index("end-1c")
            t.insert("end", f"YOU  ·  Inquiry {idx + 1}\n", "oracle_user")
            t.insert("end", turn["question"] + "\n\n", "oracle_body")
            label = f"ORACLE  ·  Response {idx + 1}   [select this response to apply or copy]\n"
            if turn.get("sources"):
                label += "Source excerpts: " + ", ".join(turn["sources"]) + " (verify claims)\n"
            elif turn.get("grounded"):
                label += "Source-grounded mode · no uploaded source excerpts were available\n"
            tag = f"oracle_turn_{idx}"
            t.insert("end", label, ("oracle_reply_label", tag))
            t.tag_bind(tag, "<Button-1>", lambda event, i=idx: self.choose_oracle_turn(i))
            t.tag_bind(tag, "<Enter>", lambda event: t.configure(cursor="hand2"))
            t.tag_bind(tag, "<Leave>", lambda event: t.configure(cursor="arrow"))
            render_message(t, turn["answer"])
            end = t.index("end-1c")
            if idx == self.selected_oracle_turn:
                t.tag_add("oracle_selected", start, end)
        t.configure(state="disabled")
        if scroll_to_end:
            t.see("end")

    def copy_oracle_reply(self):
        turn = self.selected_oracle_response()
        if not turn:
            messagebox.showinfo("Select a reply", "Consult the Oracle, then select a reply in the transcript.")
            return
        self.clipboard_clear()
        self.clipboard_append(clean_markdown(turn["answer"]))
        self.status.set("Clean Oracle text copied without Markdown markers.")

    def save_oracle_transcript(self):
        if not self.oracle_turns:
            messagebox.showinfo("No conversation", "There is no Oracle conversation to export.")
            return False
        path = filedialog.asksaveasfilename(parent=self, title="Export Oracle conversation",
                defaultextension=".txt", initialfile="Campaign Forge - Oracle transcript.txt",
                filetypes=[("Plain text", "*.txt")])
        if not path:
            return False
        try:
            Path(path).write_text(transcript_text(self.oracle_turns), encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("Export failed", str(exc))
            return False
        self.last_transcript_export = len(self.oracle_turns)
        self.status.set("Oracle transcript exported. It is separate from your campaign file.")
        return True

    def write_target(self, target, new_value):
        if target["kind"] == "overview":
            widget = self.overview_text.get(target["key"])
            if widget is None:
                return False
            widget.delete("1.0", "end")
            widget.insert("1.0", new_value)
            self.data[target["key"]] = new_value
        else:
            entry = next((e for e in self.data["entries"] if e["id"] == target["key"]), None)
            if entry is None:
                return False
            entry["content"] = new_value
            if target["key"] == self.current_entry_id:
                self.entry_body.delete("1.0", "end")
                self.entry_body.insert("1.0", new_value)
        self.mark_dirty()
        return True

    def preview_oracle_application(self):
        turn = self.selected_oracle_response()
        if not turn:
            messagebox.showinfo("No suggestion", "Choose an Oracle response from the conversation first.")
            return
        target = turn.get("target")
        if not target:
            messagebox.showinfo("Choose a field", "Use Improve with Oracle beside a field before applying a suggestion.")
            return
        original = self.target_value(target)
        if original is None:
            messagebox.showwarning("Field unavailable", "This destination no longer exists in the open campaign.")
            return
        try:
            revision = clean_field_revision(turn["answer"])
        except InvalidFieldRevision as exc:
            messagebox.showwarning("Revision needs review", str(exc))
            return
        dialog = tk.Toplevel(self)
        dialog.title("Review Oracle suggestion — " + target["label"])
        dialog.geometry("1050x650")
        dialog.minsize(750, 480)
        dialog.configure(bg=BG)
        dialog.transient(self)
        frame = ttk.Frame(dialog, padding=16)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Review before changing your campaign", style="Section.TLabel").pack(anchor="w")
        if original != target.get("baseline"):
            ttk.Label(frame, text="The original field has changed since this request. This preview uses the CURRENT text.",
                      style="Muted.TLabel").pack(anchor="w", pady=6)
        grid = ttk.Frame(frame)
        grid.pack(fill="both", expand=True, pady=9)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        grid.rowconfigure(1, weight=1)
        ttk.Label(grid, text="CURRENT WRITING").grid(row=0, column=0, sticky="w")
        ttk.Label(grid, text="ORACLE SUGGESTION").grid(row=0, column=1, sticky="w")
        for col, data in [(0, original), (1, revision)]:
            txt = self.text_box(grid, height=16)
            txt.grid(row=1, column=col, sticky="nsew", padx=(0, 9) if col == 0 else (9, 0), pady=5)
            txt.insert("1.0", data)
            txt.configure(state="disabled")
        ttk.Label(frame, text="Append keeps your writing. Replace removes the current field text, but Undo can restore it.",
                  style="Muted.TLabel").pack(anchor="w", pady=(0, 8))
        controls = ttk.Frame(frame)
        controls.pack(fill="x")
        def accept(action):
            latest = self.target_value(target)
            if latest is None:
                messagebox.showwarning("Unavailable", "This destination no longer exists.", parent=dialog)
                return
            if latest != original:
                messagebox.showwarning("Field changed", "Your field changed while this preview was open. Open the comparison again before applying.", parent=dialog)
                return
            if action == "replace" and latest and not messagebox.askyesno("Replace field text?",
                    "Replace the current text in " + target["label"] + "? You can undo this change.", parent=dialog):
                return
            result = apply_suggestion(latest, revision, action)
            if self.write_target(target, result):
                self.field_undo.append((copy.deepcopy(target), latest, result))
                self.status.set("Oracle suggestion applied to " + target["label"] + ". Undo is available until you change projects.")
                dialog.destroy()
        def ask_merge():
            dialog.destroy()
            self.oracle_target = copy.deepcopy(target)
            self.ai_question.delete("1.0", "end")
            self.ai_question.insert("1.0", "Blend the current selected field with this alternative draft. "
                 "Preserve established facts, the DM's voice and the field's original scope. "
                 "Return only one ready-to-use version of THIS field, not the whole campaign.\n\n"
                 "Alternative wording to consider:\n" + revision)
            self.request_ai()  # produces another reviewable response; never edits a field directly
        ttk.Button(controls, text="Cancel", command=dialog.destroy).pack(side="right")
        ttk.Button(controls, text="Merge & refine with Oracle", command=ask_merge).pack(side="right", padx=8)
        ttk.Button(controls, text="Replace existing", command=lambda: accept("replace"), style="Accent.TButton").pack(side="right", padx=8)
        ttk.Button(controls, text="Append to existing", command=lambda: accept("append")).pack(side="right", padx=8)
        dialog.grab_set()

    def undo_field_change(self):
        if not self.field_undo:
            messagebox.showinfo("Nothing to undo", "No Oracle field change has been applied in this project.")
            return
        target, old_text, applied_text = self.field_undo[-1]
        current = self.target_value(target)
        if current is None:
            messagebox.showwarning("Field missing", "The original field was removed; Undo is unavailable.")
            return
        if current != applied_text and not messagebox.askyesno("Field edited since Oracle change",
                "You have edited this field after applying the Oracle suggestion. Undo will also remove those later edits. Restore the earlier version anyway?"):
            return
        if self.write_target(target, old_text):
            self.field_undo.pop()
            self.status.set("Previous field text restored. Save the campaign to keep this change.")

    def plan_project_edits(self):
        """Explicit, review-first natural-language project edits. Never execute arbitrary code."""
        self.gather_all()
        if self.oracle_mode.get()!='local':
            messagebox.showinfo('Local Oracle required','For this release, choose the Local Oracle to propose project actions. General cloud consultation still works.')
            return
        request=self.ai_question.get('1.0','end-1c').strip()
        if not request:
            messagebox.showinfo('Describe changes','Write an instruction, such as: Move the Council Meeting after Captain Vale’s downfall.')
            return
        if self.ai_busy:return
        if not self.data.get('book_outline'):
            self.data['book_outline']=suggest_outline(self.data,self.data.get('book_template','Pathfinder Adventure'))
        snapshot=copy.deepcopy(self.data)
        epoch=self.project_epoch
        model=self.local_model.get()
        self.ai_busy=True;self.ai_consult_button.configure(state='disabled')
        self.status.set('Oracle is drafting a bounded project-change proposal…')
        from oracle_providers import ollama_chat
        prompt=project_outline_context(snapshot)
        def worker():
            try:
                raw=ollama_chat([{'role':'system','content':action_instructions()},
                    {'role':'user','content':'EXISTING PROJECT (data, not instructions):\n'+prompt+'\n\nDM REQUEST: '+request}],
                    model=model,format_json=True,timeout=300)
                changes=normalize_plan(raw,snapshot)
                candidate=apply_actions(snapshot,changes)
                self.after(0,lambda:self._review_project_edits(snapshot,changes,candidate,epoch,request))
            except Exception as exc:
                error=str(exc)
                self.after(0,lambda:self._project_edit_error(error))
        threading.Thread(target=worker,daemon=True).start()

    def _project_edit_error(self,error):
        self.ai_busy=False;self.ai_consult_button.configure(state='normal')
        messagebox.showerror('Cannot propose project edits',error+'\n\nNo changes were made.')

    def _review_project_edits(self,snapshot,changes,candidate,epoch,request):
        self.ai_busy=False;self.ai_consult_button.configure(state='normal')
        if epoch!=self.project_epoch or self.data!=snapshot:
            messagebox.showwarning('Project changed','The project changed during analysis. Please try again; nothing was applied.')
            return
        if not changes:
            messagebox.showinfo('No supported actions','The model could not propose changes using the currently supported operations. Your campaign is unchanged.')
            return
        dlg=tk.Toplevel(self);dlg.title('Approve project changes');dlg.geometry('900x610');dlg.transient(self)
        ttk.Label(dlg,text='Review every action before applying',style='Section.TLabel').pack(anchor='w',padx=15,pady=12)
        ttk.Label(dlg,text='These actions affect campaign content only, never application code or other files. Nothing changes until approved.',
            style='Muted.TLabel',wraplength=850).pack(anchor='w',padx=15)
        body=ttk.Frame(dlg);body.pack(fill='both',expand=True,padx=15,pady=10)
        txt=self.text_box(body,height=20);txt.pack(side='left',fill='both',expand=True)
        scroll=ttk.Scrollbar(body,orient='vertical',command=txt.yview);scroll.pack(side='right',fill='y');txt.configure(yscrollcommand=scroll.set)
        txt.insert('1.0',summarize_actions(snapshot,changes));txt.configure(state='disabled')
        footer=ttk.Frame(dlg);footer.pack(fill='x',padx=15,pady=13)
        def confirm():
            if self.data!=snapshot or epoch!=self.project_epoch:
                messagebox.showerror('Project changed','Project changed during review. The plan was not applied.',parent=dlg);return
            self.project_action_undo=copy.deepcopy(self.data)
            self.data=candidate
            self.load_into_ui();self.mark_dirty();dlg.destroy()
            self.status.set(f'{len(changes)} approved project edits applied. Save the project, or use Undo project edits.')
        ttk.Button(footer,text='Cancel — no changes',command=dlg.destroy).pack(side='right',padx=6)
        ttk.Button(footer,text=f'Approve {len(changes)} edit(s)',style='Accent.TButton',command=confirm).pack(side='right')
        dlg.grab_set()

    def undo_project_edits(self):
        if self.project_action_undo is None:
            messagebox.showinfo('Nothing to undo','No approved project-wide edits are waiting to be undone.');return
        if self.project_action_undo.get('project_id') != self.data.get('project_id'):
            self.project_action_undo=None
            messagebox.showwarning('Project changed','The old undo snapshot belongs to a different project.')
            return
        self.data,self.project_action_undo=self.project_action_undo,None
        self.load_into_ui();self.mark_dirty()
        self.status.set('Approved project edits undone. Save to preserve the restored project.')

    # ---- AI and book export ----
    def request_ai(self):
        if self.ai_busy:
            return
        self.gather_all()
        mode=self.oracle_mode.get()
        question=self.ai_question.get("1.0", "end-1c").strip()
        if mode == "scribe":
            messagebox.showinfo("The Scribe", "Select the Local or Greater Oracle for AI assistance.")
            return
        if not question:
            messagebox.showinfo("Question needed", "Write a request or question first.")
            return
        if mode == "cloud" and not self.cloud_key:
            messagebox.showinfo("Connect first", "Connect your OpenAI API key first.")
            return
        # Follow-up questions take precedence over the earlier field-edit mode.
        discussion=(self.oracle_reply_kind.get() == "Ask / explain (no edits)"
                    or is_attribution_question(question))
        if discussion:
            self.oracle_reply_kind.set("Ask / explain (no edits)")
        requested_target=copy.deepcopy(self.oracle_target) if not discussion else None
        # Images in The Archives require a vision-capable local model; text excerpts alone cannot describe them.
        if discussion and self.include_archive.get():
            archive_image=match_requested_image(self.archive,self.data.get('project_id',''),question)
            if archive_image:
                if mode!='local':
                    messagebox.showinfo('Local vision required','Choose Local Oracle to describe an archived map. Cloud image sharing is not implemented in this release.')
                    return
                path=self.archive.source_path(archive_image['id'],self.data.get('project_id',''))
                self.ai_busy=True;self.ai_consult_button.configure(state='disabled')
                self.last_ai_request={'mode':mode,'question':question,'target':None,
                    'sources':[archive_image['name']],'grounded':True,'project_epoch':self.project_epoch}
                model=self.local_model.get()
                self.status.set('Local Oracle is inspecting archived image '+archive_image['name']+'…')
                def background_image():
                    try:
                        answer=describe_image(path,question,model)
                        self.after(0,lambda:self.finish_ai(answer,None))
                    except Exception as exc:
                        error=str(exc)
                        self.after(0,lambda:self.finish_ai(None,error))
                threading.Thread(target=background_image,daemon=True).start()
                return
        requested_target=copy.deepcopy(self.oracle_target) if not discussion else None
        if requested_target is not None:
            current=self.target_value(requested_target)
            if current is None:
                messagebox.showwarning("Field unavailable", "The selected field no longer exists.")
                return
            requested_target['baseline']=current
        grounded=self.oracle_source_policy.get().startswith("Use uploaded")
        # Always retrieve the original manuscript FIRST if opted in; derived story
        # entries and past AI responses are never considered original sources.
        sources=gather_sources(self.data,self.archive,self.data.get('project_id',''),
            question+' '+(self.oracle_target or {}).get('label','')+' '+self.data.get('title',''),
            requested_target or self.oracle_target,
            use_project_refs=self.include_refs.get(),use_archive=self.include_archive.get()) if grounded else None
        if (grounded and requested_target and not requested_target['baseline'].strip()
                and (sources is None or not sources.text)):
            messagebox.showwarning('No source text available',
                'This field is blank and Campaign Forge found no readable excerpts from your uploaded documents. '
                'Add a PDF or DOCX to The Archives or enable Project reference excerpts. '
                'For an invented alternative, explicitly switch to Brainstorm new ideas.')
            return
        if mode=='cloud':
            # Never let a previously saved 'Don't show again' choice silently
            # authorize transmitting newly uploaded personal source documents.
            shared_names=(sources.names if sources else
                          [str(r.get('name','Reference')) for r in self.data.get('references',[])]
                          if self.include_refs.get() else [])
            if shared_names and not messagebox.askyesno('Send source material to OpenAI?',
                    'Selected text excerpts from these documents may be sent to OpenAI for this request:\n\n'
                    + '\n'.join(shared_names[:8])+'\n\nContinue?'):
                return
            details=("Selected field and source excerpts" if requested_target else "Question, relevant campaign details and source excerpts")
            if grounded and sources and sources.names:
                details+=' from '+', '.join(sources.names)
            note=(details+' will be sent to the OpenAI API for this request.\n\n'
                  'Your API use may incur charges. Do not continue if these sources must remain local.')
        else:
            note=('This consultation will run through local Ollama. '
                  'Original manuscript excerpts take priority in Source-grounded mode. '
                  'No text is sent to OpenAI.')
        if not self.confirm_oracle_notice('Consult '+('Local' if mode=='local' else 'Greater')+' Oracle?',note,
                                          'hide_local_notice' if mode=='local' else 'hide_cloud_notice'):
            return
        previous=[copy.deepcopy(t) for t in self.oracle_turns if t.get('project_epoch')==self.project_epoch][-3:]
        self.last_ai_request={'mode':mode,'question':question,'target':requested_target,
            'sources':(sources.names if sources else []),'grounded':grounded,
            'project_epoch':self.project_epoch}
        self.ai_busy=True
        self.ai_consult_button.configure(state='disabled')
        self.status.set('Consulting the '+('Local' if mode=='local' else 'Greater')+' Oracle…')
        data=copy.deepcopy(self.data)
        # Do not append large original manuscripts twice under the provider's
        # generic campaign context; instead send ranked excerpts once.
        data['references']=[] if grounded else (data.get('references',[]) if self.include_refs.get() else [])
        kwargs=dict(include_refs=not grounded and self.include_refs.get(),
            field_target=copy.deepcopy(requested_target),
            source_context=sources.text if sources else '',
            source_text=sources.source_text if sources else '',
            source_grounded=grounded,discussion=discussion,history=previous)
        model=self.local_model.get() if mode=='local' else self.cloud_model.get()
        key=self.cloud_key
        def background():
            try:
                if mode=='local':
                    result=consult_local(data,question,model=model,**kwargs)
                else:
                    result=consult_ai(data,question,key,model=model,**kwargs)
                self.after(0,lambda:self.finish_ai(result,None))
            except Exception as exc:
                detail=str(exc)
                self.after(0,lambda:self.finish_ai(None,detail))
        threading.Thread(target=background,daemon=True).start()

    def finish_ai(self, result, error):
        self.ai_busy = False
        self.ai_consult_button.configure(state="normal" if self.oracle_mode.get() != "scribe" else "disabled")
        if error:
            messagebox.showerror("AI request failed", error)
            self.status.set("AI request failed; campaign project is unchanged.")
            return
        request = self.last_ai_request or {"question": "", "mode": self.oracle_mode.get(), "target": None}
        target = request.get("target")
        if target:
            try:
                result = clean_field_revision(result)
            except InvalidFieldRevision as exc:
                messagebox.showwarning("Oracle returned an unusable field revision", str(exc))
                self.status.set("The Oracle response could not be safely applied. Your campaign was not changed.")
                return
        self.oracle_turns.append({"question": request["question"], "answer": result,
                                  "mode": request["mode"], "target": target,
                                  "target_label": target["label"] if target else None,
                                  "grounded": request.get("grounded", False),
                                  "sources": request.get("sources", []),
                                  "project_epoch": request.get("project_epoch", self.project_epoch)})
        self.selected_oracle_turn = len(self.oracle_turns) - 1
        self.ai_has_response = True
        self.refresh_oracle_transcript()
        self.status.set("Oracle reply added to this session. Choose Apply selected to field to review it; nothing was changed.")

    def ai_to_entry(self):
        turn = self.selected_oracle_response()
        content = clean_markdown(turn["answer"]) if turn else ""
        if not content or not self.ai_has_response:
            messagebox.showinfo("No suggestion yet", "Consult the Local or Greater Oracle first, then save a suggestion as an entry.")
            return
        title = simpledialog.askstring("Keep suggestion", "Entry title:",
                                        initialvalue="AI Workshop Notes", parent=self)
        if title is None:
            return
        e = new_entry("Session Notes", title.strip() or "AI Workshop Notes", content, True)
        self.data["entries"].append(e)
        self.entry_filter.set("All content")
        self.refresh_entry_list(e["id"])
        self.mark_dirty()
        self.tabs.select(self.library_tab)
        self.status.set("Suggestion copied to an editable DM-only entry. Save project to keep it.")

    def export_pdf(self):
        self.gather_all()
        outline=self.data.get('book_outline')
        if outline:
            from forge_book import suggest_outline, outline_node_ids, node_title
            expected=suggest_outline(self.data,self.data.get('book_template','Pathfinder Adventure'))
            placed=outline_node_ids(outline)
            missing=[node_title(self.data,n) for s in expected['sections'] for n in s['nodes']
                     if (n['type'],n['id']) not in placed]
            if missing and not messagebox.askyesno('Unplaced book contents',
                f'{len(missing)} campaign entry/entries are not in the book outline.\n\n'
                'Choose No to go to Bind the Tome and select Restore missing project entries, '
                'or Yes to export only the currently placed content.\n\n'
                + '\n'.join(missing[:7])):
                self.tabs.select(self.publish_tab)
                return
        title = self.data.get("title") or "Campaign"
        safe = "".join(c if c.isalnum() or c in " _-" else "_" for c in title).strip() or "Campaign"
        path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                            initialfile=safe + " - Campaign Book.pdf",
                                            filetypes=[("PDF document", "*.pdf")])
        if not path:
            return
        try:
            export_book(self.data, path, include_gm=self.export_dm_only.get(), archive=self.archive)
            messagebox.showinfo("Book exported", "Your campaign book is ready:\n" + path)
            self.status.set("PDF exported: " + Path(path).name)
        except Exception as exc:
            messagebox.showerror("PDF export error", str(exc))


if __name__ == "__main__":
    app = CampaignForge()
    app.mainloop()
