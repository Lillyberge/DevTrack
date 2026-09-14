import customtkinter as ctk
import json
import time
import shutil
from datetime import datetime
from pathlib import Path
from tkinter import messagebox

from skills import SKILL_TEMPLATES

from styles import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT,
    APP_BG,
    SIDEBAR_BG,
    CARD_BG,
    CARD_LIGHT,
    ACCENT,
    ACCENT_HOVER,
    TEXT_COLOR,
    MUTED_TEXT,
    BORDER_COLOR,
    SIDEBAR_WIDTH,
    PAGE_PADDING,
    CARD_CORNER_RADIUS,
)


# -------------------------
# APP-INNSTILLINGER
# -------------------------

ctk.set_appearance_mode("light")

APP_SUPPORT_DIR = (
    Path.home()
    / "Library"
    / "Application Support"
    / "DevTrack"
)

DATA_FILE = (
    APP_SUPPORT_DIR
    / "data.json"
)

OLD_DATA_FILE = (
    Path(__file__).parent
    / "data.json"
)


class DevTrackApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("DevTrack")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")

        self.minsize(
            MIN_WINDOW_WIDTH,
            MIN_WINDOW_HEIGHT
        )

        self.configure(
            fg_color=APP_BG
        )

        # Hent lagrede data
        self.data = self.load_data()

        # Timer-status
        self.timer_running = False
        self.timer_started_at = None
        self.timer_elapsed_seconds = 0

        # Vinduet deles i:
        # kolonne 0 = meny
        # kolonne 1 = innhold
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_sidebar()
        self.create_pages()

        self.show_page("home")
        
        self.protocol(
            "WM_DELETE_WINDOW",
            self.on_close
        )

    # -------------------------
    # DATA
    # -------------------------

    def load_data(self):
        """Leser data fra data.json."""

        # Sørg for at DevTrack-mappen finnes.
        APP_SUPPORT_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        # Hvis vi fortsatt har den gamle data.json
        # i prosjektmappen, kopierer vi den til
        # den nye permanente plasseringen.
        #
        # Den gamle filen slettes IKKE.
        if (
            not DATA_FILE.exists()
            and OLD_DATA_FILE.exists()
        ):
            shutil.copy2(
                OLD_DATA_FILE,
                DATA_FILE
            )

        if DATA_FILE.exists():
            with open(
                DATA_FILE,
                "r",
                encoding="utf-8"
            ) as file:
                data = json.load(file)

            # Legg til nye felt dersom data.json
            # ble laget før disse funksjonene eksisterte.

            if "sessions" not in data:
                data["sessions"] = []

            if "total_seconds" not in data:
                old_minutes = data.get(
                    "total_minutes",
                    0
                )

                data["total_seconds"] = (
                    old_minutes * 60
                )

            if "skills" not in data:
                data["skills"] = {}

            if "notes" not in data:
                data["notes"] = []

            for technology in data["technologies"]:

                if technology not in data["skills"]:
                    data["skills"][technology] = {}

                template = SKILL_TEMPLATES.get(
                    technology,
                    []
                )

                for skill in template:
                    if (
                        skill
                        not in data["skills"][technology]
                    ):
                        data["skills"][technology][
                            skill
                        ] = "Ikke startet"

            self.save_data(data)

            return data

        # Dette brukes første gang appen åpnes
        data = {
            "technologies": [
                "Python",
                "SQL",
                "JavaScript"
            ],
            "projects": [],
            "sessions": [],
            "total_seconds": 0,
            "skills": {},
            "notes": []
        }

        for technology in data["technologies"]:

            data["skills"][technology] = {}

            for skill in SKILL_TEMPLATES.get(
                technology,
                []
            ):
                data["skills"][technology][
                    skill
                ] = "Ikke startet"

        self.save_data(data)

        return data

    def save_data(self, data=None):
        """Lagrer data i data.json."""

        if data is None:
            data = self.data

        with open(
            DATA_FILE,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False
            )

    # -------------------------
    # SIDEMENY
    # -------------------------

    def create_sidebar(self):

        self.sidebar = ctk.CTkFrame(
            self,
            width=SIDEBAR_WIDTH,
            corner_radius=0,
            fg_color=SIDEBAR_BG
        )

        self.sidebar.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        self.sidebar.grid_propagate(False)

        title = ctk.CTkLabel(
            self.sidebar,
            text="DevTrack",
            font=ctk.CTkFont(
                size=22,
                weight="bold"
            )
        )

        title.pack(
            padx=20,
            pady=(30, 25)
        )

        self.create_nav_button(
            "Hjem",
            "home"
        )

        self.create_nav_button(
            "Teknologier",
            "technologies"
        )

        self.create_nav_button(
            "Prosjekter",
            "projects"
        )

        self.create_nav_button(
            "Timer",
            "timer"
        )

        self.create_nav_button(
            "Notater",
            "notes"
        )

    def create_nav_button(
        self,
        text,
        page
    ):

        button = ctk.CTkButton(
            self.sidebar,
            text=text,
            anchor="w",
            height=40,
            corner_radius=8,
            fg_color="transparent",
            hover_color=CARD_BG,
            text_color=TEXT_COLOR,
            command=lambda: self.show_page(
                page
            )
        )

        button.pack(
            padx=12,
            pady=5,
            fill="x"
        )

    # -------------------------
    # SIDER
    # -------------------------

    def create_pages(self):

        self.pages = {}

        page_names = [
            "home",
            "technologies",
            "projects",
            "timer",
            "notes"
        ]

        for name in page_names:

            frame = ctk.CTkFrame(
                self,
                corner_radius=0,
                fg_color="transparent"
            )

            frame.grid(
                row=0,
                column=1,
                sticky="nsew"
            )

            self.pages[name] = frame

        self.create_home_page()
        self.create_technologies_page()
        self.create_projects_page()
        self.create_timer_page()
        self.create_notes_page()

    # -------------------------
    # HJEM
    # -------------------------

    def create_home_page(self):

        page = self.pages["home"]

        title = ctk.CTkLabel(
            page,
            text="Din utvikling",
            font=ctk.CTkFont(
                size=26,
                weight="bold"
            ),
            text_color=TEXT_COLOR
        )

        title.pack(
            anchor="w",
            padx=PAGE_PADDING,
            pady=(30, 3)
        )

        subtitle = ctk.CTkLabel(
            page,
            text="Oversikt over programmeringen din.",
            text_color=MUTED_TEXT
        )

        subtitle.pack(
            anchor="w",
            padx=PAGE_PADDING
        )

        # Statistikk
        stats_frame = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )

        stats_frame.pack(
            fill="x",
            padx=PAGE_PADDING,
            pady=(22, 18)
        )

        self.total_time_label = self.create_stat_card(
            stats_frame,
            "Total tid",
            "0 min"
        )

        self.project_count_label = self.create_stat_card(
            stats_frame,
            "Prosjekter",
            "0"
        )

        self.technology_count_label = self.create_stat_card(
            stats_frame,
            "Teknologier",
            "0"
        )

        # Teknologier
        technologies_title = ctk.CTkLabel(
            page,
            text="Mine teknologier",
            font=ctk.CTkFont(
                size=18,
                weight="bold"
            ),
            text_color=TEXT_COLOR
        )

        technologies_title.pack(
            anchor="w",
            padx=PAGE_PADDING,
            pady=(5, 10)
        )

        self.home_technologies_frame = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )

        self.home_technologies_frame.pack(
            fill="both",
            expand=True,
            padx=PAGE_PADDING,
            pady=(0, 20)
        )

        self.refresh_home_page()

    def create_stat_card(
        self,
        parent,
        title,
        value
    ):

        card = ctk.CTkFrame(
            parent,
            height=90,
            corner_radius=CARD_CORNER_RADIUS,
            fg_color=CARD_BG,
            border_width=1,
            border_color=BORDER_COLOR
        )

        card.pack(
            side="left",
            expand=True,
            fill="both",
            padx=5
        )

        title_label = ctk.CTkLabel(
            card,
            text=title,
            text_color=MUTED_TEXT
        )

        title_label.pack(
            pady=(14, 2)
        )

        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            ),
            text_color=TEXT_COLOR
        )

        value_label.pack(
            pady=(0, 12)
        )

        return value_label

    def refresh_home_page(self):

        total_seconds = self.data[
            "total_seconds"
        ]

        self.total_time_label.configure(
            text=self.format_time(
                total_seconds
            )
        )

        self.project_count_label.configure(
            text=str(
                len(
                    self.data["projects"]
                )
            )
        )

        self.technology_count_label.configure(
            text=str(
                len(
                    self.data["technologies"]
                )
            )
        )

        for widget in (
            self.home_technologies_frame
            .winfo_children()
        ):
            widget.destroy()

        for technology in self.data[
            "technologies"
        ]:

            technology_seconds = (
                self.get_technology_time(
                    technology
                )
            )

            technology_time = self.format_time(
                technology_seconds
            )

            skill_counts = self.get_skill_counts(
                technology
            )

            total_skills = sum(
                skill_counts.values()
            )

            completed_points = (
                skill_counts["Under læring"]
                + skill_counts["Kan bruke"] * 2
                + skill_counts["Trygg"] * 3
            )

            max_points = total_skills * 3

            if max_points > 0:
                progress = (
                    completed_points
                    / max_points
                )
            else:
                progress = 0

            card = ctk.CTkFrame(
                self.home_technologies_frame,
                corner_radius=CARD_CORNER_RADIUS,
                fg_color=CARD_LIGHT,
                border_width=1,
                border_color=BORDER_COLOR
            )

            card.pack(
                fill="x",
                pady=5
            )

            top_row = ctk.CTkFrame(
                card,
                fg_color="transparent"
            )

            top_row.pack(
                fill="x",
                padx=15,
                pady=(12, 5)
            )

            name_label = ctk.CTkLabel(
                top_row,
                text=technology,
                font=ctk.CTkFont(
                    size=15,
                    weight="bold"
                ),
                text_color=TEXT_COLOR
            )

            name_label.pack(
                side="left"
            )

            time_label = ctk.CTkLabel(
                top_row,
                text=technology_time,
                text_color=MUTED_TEXT
            )

            time_label.pack(
                side="right"
            )

            progress_bar = ctk.CTkProgressBar(
                card,
                height=8,
                progress_color=ACCENT,
                fg_color=CARD_BG
            )

            progress_bar.pack(
                fill="x",
                padx=15,
                pady=(3, 5)
            )

            progress_bar.set(
                progress
            )

            progress_text = ctk.CTkLabel(
                card,
                text=(
                    f"{skill_counts['Trygg']} trygg  •  "
                    f"{skill_counts['Kan bruke']} kan bruke  •  "
                    f"{skill_counts['Under læring']} lærer"
                ),
                font=ctk.CTkFont(
                    size=11
                ),
                text_color=MUTED_TEXT
            )

            progress_text.pack(
                anchor="w",
                padx=15,
                pady=(0, 10)
            )

    # -------------------------
    # TEKNOLOGIER
    # -------------------------

    def create_technologies_page(self):

        page = self.pages[
            "technologies"
        ]

        self.create_page_title(
            page,
            "Teknologier",
            "Språk og verktøy du lærer."
        )

        add_button = ctk.CTkButton(
            page,
            text="+ Legg til teknologi",
            command=self.add_technology,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER
        )

        add_button.pack(
            anchor="w",
            padx=30,
            pady=20
        )

        self.technology_list_frame = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )

        self.technology_list_frame.pack(
            fill="both",
            expand=True,
            padx=30
        )

        self.refresh_technology_list()

    def refresh_technology_list(self):
        # Fjern gammel liste
        for widget in self.technology_list_frame.winfo_children():
            widget.destroy()

        if not self.data["technologies"]:
            empty_label = ctk.CTkLabel(
                self.technology_list_frame,
                text="Ingen teknologier lagt til ennå."
            )

            empty_label.pack(
                anchor="w",
                pady=10
            )

            return

        for technology in self.data["technologies"]:

            total_seconds = self.get_technology_time(
                technology
            )

            time_text = self.format_time(
                total_seconds
            )

            row = ctk.CTkFrame(
                self.technology_list_frame,
                fg_color="transparent"
            )

            row.pack(
                fill="x",
                pady=5
            )

            # Åpne teknologi
            technology_button = ctk.CTkButton(
                row,
                text=f"{technology}    •    {time_text}",
                anchor="w",
                height=55,
                font=ctk.CTkFont(
                    size=16,
                    weight="bold"
                ),
                fg_color=ACCENT,
                hover_color=ACCENT_HOVER,
                command=lambda tech=technology:
                    self.open_technology_window(tech)
            )

            technology_button.pack(
                side="left",
                fill="x",
                expand=True
            )

            # Slett teknologi
            delete_button = ctk.CTkButton(
                row,
                text="Slett",
                width=60,
                height=55,
                fg_color="transparent",
                hover_color=CARD_BG,
                text_color=TEXT_COLOR,
                command=lambda tech=technology:
                    self.delete_technology(tech)
            )

            delete_button.pack(
                side="right",
                padx=(8, 0)
            )
            
    
    def delete_technology(self, technology):
        message = (
            f"Er du sikker på at du vil fjerne '{technology}'?\n\n"
            "Ferdighetsnivåene for teknologien blir slettet.\n\n"
            "Gamle timer, prosjekter og notater beholdes."
        )

        confirmed = messagebox.askyesno(
            "Fjern teknologi",
            message
        )

        if not confirmed:
            return

        # Fjern fra listen over aktive teknologier
        if technology in self.data["technologies"]:
            self.data["technologies"].remove(
                technology
            )

        # Fjern ferdighetsoversikten
        if technology in self.data["skills"]:
            del self.data["skills"][technology]

        # Vi endrer IKKE sessions, projects eller notes.
        # De fungerer som historikk og beholder teknologinavnet.

        self.save_data()

        self.refresh_technology_list()
        self.refresh_home_page()
        self.refresh_timer_options()
        
        

    def open_technology_window(
        self,
        technology
    ):

        window = ctk.CTkToplevel(
            self
        )

        window.title(
            technology
        )

        window.geometry(
            "520x650"
        )

        window.minsize(
            480,
            550
        )

        window.transient(
            self
        )

        title = ctk.CTkLabel(
            window,
            text=technology,
            font=ctk.CTkFont(
                size=24,
                weight="bold"
            )
        )

        title.pack(
            anchor="w",
            padx=25,
            pady=(25, 5)
        )

        total_seconds = (
            self.get_technology_time(
                technology
            )
        )

        time_label = ctk.CTkLabel(
            window,
            text=(
                "Total tid: "
                f"{self.format_time(total_seconds)}"
            )
        )

        time_label.pack(
            anchor="w",
            padx=25,
            pady=(0, 20)
        )

        # Kompetanse
        skill_counts = self.get_skill_counts(
            technology
        )

        competence_frame = ctk.CTkFrame(
            window
        )

        competence_frame.pack(
            fill="x",
            padx=25,
            pady=(0, 15)
        )

        competence_title = ctk.CTkLabel(
            competence_frame,
            text="Kompetanse",
            font=ctk.CTkFont(
                size=17,
                weight="bold"
            )
        )

        competence_title.pack(
            anchor="w",
            padx=15,
            pady=(12, 8)
        )

        competence_text = (
            f"Trygg: {skill_counts['Trygg']}    "
            f"Kan bruke: {skill_counts['Kan bruke']}\n"
            f"Under læring: {skill_counts['Under læring']}    "
            f"Ikke startet: {skill_counts['Ikke startet']}"
        )

        competence_label = ctk.CTkLabel(
            competence_frame,
            text=competence_text,
            justify="left"
        )

        competence_label.pack(
            anchor="w",
            padx=15,
            pady=(0, 12)
        )

        # Prosjekter
        projects = self.get_projects_for_technology(
            technology
        )

        projects_frame = ctk.CTkFrame(
            window
        )

        projects_frame.pack(
            fill="x",
            padx=25,
            pady=(0, 15)
        )

        projects_title = ctk.CTkLabel(
            projects_frame,
            text="Prosjekter",
            font=ctk.CTkFont(
                size=17,
                weight="bold"
            )
        )

        projects_title.pack(
            anchor="w",
            padx=15,
            pady=(12, 6)
        )

        if projects:

            for project in projects:

                project_seconds = (
                    self.get_project_time(
                        project["name"]
                    )
                )

                project_text = (
                    f"• {project['name']} "
                    f"— "
                    f"{self.format_time(project_seconds)}"
                )

                project_label = ctk.CTkLabel(
                    projects_frame,
                    text=project_text
                )

                project_label.pack(
                    anchor="w",
                    padx=15,
                    pady=2
                )

        else:

            no_projects_label = ctk.CTkLabel(
                projects_frame,
                text=(
                    "Ingen prosjekter med "
                    "denne teknologien."
                )
            )

            no_projects_label.pack(
                anchor="w",
                padx=15,
                pady=2
            )

        spacer = ctk.CTkLabel(
            projects_frame,
            text=""
        )

        spacer.pack(
            pady=2
        )

        # Ferdigheter
        heading = ctk.CTkLabel(
            window,
            text="Ferdigheter",
            font=ctk.CTkFont(
                size=17,
                weight="bold"
            )
        )

        heading.pack(
            anchor="w",
            padx=25,
            pady=(0, 8)
        )

        skill_frame = ctk.CTkScrollableFrame(
            window
        )

        skill_frame.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=(0, 25)
        )

        skills = self.data[
            "skills"
        ].get(
            technology,
            {}
        )

        if not skills:

            empty_label = ctk.CTkLabel(
                skill_frame,
                text=(
                    "Ingen ferdigheter "
                    "lagt til ennå."
                )
            )

            empty_label.pack(
                anchor="w",
                pady=10
            )

            return

        levels = [
            "Ikke startet",
            "Under læring",
            "Kan bruke",
            "Trygg"
        ]

        for (
            skill,
            current_level
        ) in skills.items():

            row = ctk.CTkFrame(
                skill_frame
            )

            row.pack(
                fill="x",
                pady=5
            )

            skill_label = ctk.CTkLabel(
                row,
                text=skill,
                anchor="w"
            )

            skill_label.pack(
                side="left",
                padx=12,
                pady=10,
                expand=True,
                fill="x"
            )

            level_menu = ctk.CTkOptionMenu(
                row,
                values=levels,
                width=130,
                fg_color=ACCENT,
                button_color=ACCENT,
                button_hover_color=(
                    ACCENT_HOVER
                ),
                command=lambda value,
                tech=technology,
                skill_name=skill:
                    self.update_skill_level(
                        tech,
                        skill_name,
                        value
                    )
            )

            level_menu.set(
                current_level
            )

            level_menu.pack(
                side="right",
                padx=10,
                pady=8
            )

    def update_skill_level(
        self,
        technology,
        skill,
        level
    ):

        self.data[
            "skills"
        ][technology][skill] = level

        self.save_data()

        self.refresh_home_page()

    def add_technology(self):

        dialog = ctk.CTkInputDialog(
            text="Hva heter teknologien?",
            title="Legg til teknologi"
        )

        technology = dialog.get_input()

        if technology is None:
            return

        technology = technology.strip()

        if technology == "":
            return

        if technology in self.data[
            "technologies"
        ]:
            return

        self.data[
            "technologies"
        ].append(
            technology
        )

        self.data[
            "skills"
        ][technology] = {}

        for skill in SKILL_TEMPLATES.get(
            technology,
            []
        ):

            self.data[
                "skills"
            ][technology][
                skill
            ] = "Ikke startet"

        self.save_data()

        self.refresh_technology_list()
        self.refresh_home_page()



    # -------------------------
    # PROSJEKTER
    # -------------------------

    def create_projects_page(self):
        page = self.pages["projects"]

        self.create_page_title(
            page,
            "Prosjekter",
            "Hold oversikt over det du bygger."
        )

        button = ctk.CTkButton(
            page,
            text="+ Nytt prosjekt",
            command=lambda: self.open_project_window(),
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER
        )

        button.pack(
            anchor="w",
            padx=30,
            pady=20
        )

        self.project_list_frame = ctk.CTkScrollableFrame(
            page,
            fg_color="transparent"
        )

        self.project_list_frame.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=(0, 20)
        )

        self.refresh_project_list()


    def refresh_project_list(self):
        # Fjern den gamle listen
        for widget in self.project_list_frame.winfo_children():
            widget.destroy()

        if not self.data["projects"]:
            empty_label = ctk.CTkLabel(
                self.project_list_frame,
                text="Ingen prosjekter ennå."
            )

            empty_label.pack(
                anchor="w",
                pady=10
            )

            return

        # Vis alle prosjektene
        for index, project in enumerate(self.data["projects"]):
            card = ctk.CTkFrame(
                self.project_list_frame,
                fg_color=CARD_LIGHT,
                corner_radius=CARD_CORNER_RADIUS,
                border_width=1,
                border_color=BORDER_COLOR
            )

            card.pack(
                fill="x",
                pady=6
            )

            # Øverste rad:
            # prosjektnavn + rediger/slett
            top_row = ctk.CTkFrame(
                card,
                fg_color="transparent"
            )

            top_row.pack(
                fill="x",
                padx=15,
                pady=(12, 3)
            )

            name_label = ctk.CTkLabel(
                top_row,
                text=project["name"],
                font=ctk.CTkFont(
                    size=17,
                    weight="bold"
                ),
                text_color=TEXT_COLOR
            )

            name_label.pack(
                side="left"
            )

            delete_button = ctk.CTkButton(
                top_row,
                text="Slett",
                width=55,
                height=28,
                fg_color="transparent",
                hover_color=CARD_BG,
                text_color=TEXT_COLOR,
                command=lambda i=index:
                    self.delete_project(i)
            )

            delete_button.pack(
                side="right",
                padx=(5, 0)
            )

            edit_button = ctk.CTkButton(
                top_row,
                text="Rediger",
                width=70,
                height=28,
                fg_color=ACCENT,
                hover_color=ACCENT_HOVER,
                command=lambda i=index:
                    self.open_project_window(i)
            )

            edit_button.pack(
                side="right"
            )

            # Teknologi, status og tid
            technologies = ", ".join(
                project.get(
                    "technologies",
                    []
                )
            )

            if technologies == "":
                technologies = "Ingen teknologi"

            project_seconds = self.get_project_time(
                project["name"]
            )

            project_time = self.format_time(
                project_seconds
            )

            info_text = (
                f"{technologies}  •  "
                f"{project.get('status', 'Aktivt')}  •  "
                f"{project_time}"
            )

            info_label = ctk.CTkLabel(
                card,
                text=info_text,
                text_color=MUTED_TEXT
            )

            info_label.pack(
                anchor="w",
                padx=15
            )

            notes = project.get(
                "notes",
                ""
            )

            if notes:
                notes_label = ctk.CTkLabel(
                    card,
                    text=notes,
                    justify="left",
                    anchor="w",
                    wraplength=450,
                    text_color=TEXT_COLOR
                )

                notes_label.pack(
                    anchor="w",
                    padx=15,
                    pady=(7, 12)
                )

            else:
                info_label.pack_configure(
                    pady=(0, 12)
                )


    def open_project_window(self, project_index=None):
        """
        Åpner vinduet for nytt prosjekt eller redigering.

        project_index = None:
            nytt prosjekt

        project_index = et tall:
            rediger eksisterende prosjekt
        """

        self.editing_project_index = project_index

        editing = project_index is not None

        if editing:
            project = self.data["projects"][project_index]
            window_title = "Rediger prosjekt"
        else:
            project = None
            window_title = "Nytt prosjekt"

        self.project_window = ctk.CTkToplevel(
            self
        )

        self.project_window.title(
            window_title
        )

        self.project_window.geometry(
            "420x580"
        )

        self.project_window.resizable(
            False,
            False
        )

        self.project_window.transient(
            self
        )

        self.project_window.grab_set()

        title = ctk.CTkLabel(
            self.project_window,
            text=window_title,
            font=ctk.CTkFont(
                size=22,
                weight="bold"
            )
        )

        title.pack(
            anchor="w",
            padx=25,
            pady=(25, 15)
        )

        # -------------------------
        # PROSJEKTNAVN
        # -------------------------

        name_label = ctk.CTkLabel(
            self.project_window,
            text="Prosjektnavn"
        )

        name_label.pack(
            anchor="w",
            padx=25
        )

        self.project_name_entry = ctk.CTkEntry(
            self.project_window,
            placeholder_text="For eksempel StudyTimer"
        )

        self.project_name_entry.pack(
            fill="x",
            padx=25,
            pady=(5, 15)
        )

        if editing:
            self.project_name_entry.insert(
                0,
                project["name"]
            )

        # -------------------------
        # TEKNOLOGI
        # -------------------------

        technology_label = ctk.CTkLabel(
            self.project_window,
            text="Teknologi"
        )

        technology_label.pack(
            anchor="w",
            padx=25
        )

        technology_values = [
            "Ingen"
        ] + self.data["technologies"]

        self.project_technology_menu = ctk.CTkOptionMenu(
            self.project_window,
            values=technology_values,
            fg_color=ACCENT,
            button_color=ACCENT,
            button_hover_color=ACCENT_HOVER
        )

        self.project_technology_menu.pack(
            fill="x",
            padx=25,
            pady=(5, 15)
        )

        if editing:
            project_technologies = project.get(
                "technologies",
                []
            )

            if project_technologies:
                self.project_technology_menu.set(
                    project_technologies[0]
                )
            else:
                self.project_technology_menu.set(
                    "Ingen"
                )
        else:
            if self.data["technologies"]:
                self.project_technology_menu.set(
                    self.data["technologies"][0]
                )
            else:
                self.project_technology_menu.set(
                    "Ingen"
                )

        # -------------------------
        # STATUS
        # -------------------------

        status_label = ctk.CTkLabel(
            self.project_window,
            text="Status"
        )

        status_label.pack(
            anchor="w",
            padx=25
        )

        self.project_status_menu = ctk.CTkOptionMenu(
            self.project_window,
            values=[
                "Planlagt",
                "Aktivt",
                "På pause",
                "Ferdig"
            ],
            fg_color=ACCENT,
            button_color=ACCENT,
            button_hover_color=ACCENT_HOVER
        )

        self.project_status_menu.pack(
            fill="x",
            padx=25,
            pady=(5, 15)
        )

        if editing:
            self.project_status_menu.set(
                project.get(
                    "status",
                    "Aktivt"
                )
            )
        else:
            self.project_status_menu.set(
                "Aktivt"
            )

        # -------------------------
        # NOTATER
        # -------------------------

        notes_label = ctk.CTkLabel(
            self.project_window,
            text="Notater"
        )

        notes_label.pack(
            anchor="w",
            padx=25
        )

        self.project_notes_text = ctk.CTkTextbox(
            self.project_window,
            height=100
        )

        self.project_notes_text.pack(
            fill="x",
            padx=25,
            pady=(5, 15)
        )

        if editing:
            self.project_notes_text.insert(
                "1.0",
                project.get(
                    "notes",
                    ""
                )
            )

        # -------------------------
        # FEILMELDING
        # -------------------------

        self.project_error_label = ctk.CTkLabel(
            self.project_window,
            text=""
        )

        self.project_error_label.pack()

        # -------------------------
        # LAGRE
        # -------------------------

        if editing:
            button_text = "Lagre endringer"
        else:
            button_text = "Lagre prosjekt"

        save_button = ctk.CTkButton(
            self.project_window,
            text=button_text,
            command=self.save_project,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER
        )

        save_button.pack(
            pady=10
        )


    def save_project(self):
        name = (
            self.project_name_entry
            .get()
            .strip()
        )

        if name == "":
            self.project_error_label.configure(
                text="Skriv inn et prosjektnavn."
            )
            return

        # Ikke tillat to prosjekter med samme navn.
        for index, project in enumerate(
            self.data["projects"]
        ):
            if (
                project["name"].lower()
                == name.lower()
                and index
                != self.editing_project_index
            ):
                self.project_error_label.configure(
                    text=(
                        "Det finnes allerede et "
                        "prosjekt med dette navnet."
                    )
                )
                return

        technology = (
            self.project_technology_menu
            .get()
        )

        status = (
            self.project_status_menu
            .get()
        )

        notes = (
            self.project_notes_text
            .get(
                "1.0",
                "end"
            )
            .strip()
        )

        if technology == "Ingen":
            technologies = []
        else:
            technologies = [
                technology
            ]

        new_project = {
            "name": name,
            "status": status,
            "technologies": technologies,
            "notes": notes
        }

        # -------------------------
        # REDIGERING
        # -------------------------

        if self.editing_project_index is not None:

            old_project = self.data[
                "projects"
            ][self.editing_project_index]

            old_name = old_project[
                "name"
            ]

            self.data[
                "projects"
            ][self.editing_project_index] = (
                new_project
            )

            # Hvis prosjektnavnet endres,
            # må gamle timer fortsatt høre
            # til det samme prosjektet.
            if old_name != name:

                for session in self.data[
                    "sessions"
                ]:

                    if (
                        session.get("project")
                        == old_name
                    ):
                        session["project"] = name

        # -------------------------
        # NYTT PROSJEKT
        # -------------------------

        else:
            self.data[
                "projects"
            ].append(
                new_project
            )

        self.save_data()

        self.refresh_project_list()
        self.refresh_home_page()
        self.refresh_timer_options()

        self.project_window.destroy()


    def delete_project(self, project_index):
        project = self.data[
            "projects"
        ][project_index]

        project_name = project[
            "name"
        ]

        confirmed = messagebox.askyesno(
            "Slett prosjekt",
            (
                f"Er du sikker på at du vil "
                f"slette '{project_name}'?"
            )
        )

        if not confirmed:
            return

        # Fjern prosjektet
        self.data[
            "projects"
        ].pop(
            project_index
        )

        # Vi sletter IKKE arbeidstimene.
        # De historiske øktene beholdes,
        # men koblingen til prosjektet fjernes.
        for session in self.data[
            "sessions"
        ]:

            if (
                session.get("project")
                == project_name
            ):
                session["project"] = None

        self.save_data()

        self.refresh_project_list()
        self.refresh_home_page()
        self.refresh_timer_options()


    # -------------------------
    # TIMER
    # -------------------------

    def create_timer_page(self):

        page = self.pages[
            "timer"
        ]

        self.create_page_title(
            page,
            "Timer",
            "Logg tiden du bruker på programmering."
        )

        # Teknologi
        technology_label = ctk.CTkLabel(
            page,
            text="Teknologi"
        )

        technology_label.pack(
            anchor="w",
            padx=30,
            pady=(25, 5)
        )

        self.timer_technology_menu = ctk.CTkOptionMenu(
            page,
            values=self.data[
                "technologies"
            ],
            fg_color=ACCENT,
            button_color=ACCENT,
            button_hover_color=ACCENT_HOVER
        )

        self.timer_technology_menu.pack(
            fill="x",
            padx=30
        )

        # Prosjekt
        project_label = ctk.CTkLabel(
            page,
            text="Prosjekt"
        )

        project_label.pack(
            anchor="w",
            padx=30,
            pady=(15, 5)
        )

        project_names = [
            project["name"]
            for project
            in self.data["projects"]
        ]

        if not project_names:
            project_names = [
                "Ingen prosjekt"
            ]

        self.timer_project_menu = ctk.CTkOptionMenu(
            page,
            values=project_names,
            fg_color=ACCENT,
            button_color=ACCENT,
            button_hover_color=ACCENT_HOVER
        )

        self.timer_project_menu.pack(
            fill="x",
            padx=30
        )

        # Timer
        self.timer_label = ctk.CTkLabel(
            page,
            text="00:00:00",
            font=ctk.CTkFont(
                size=42,
                weight="bold"
            )
        )

        self.timer_label.pack(
            pady=(35, 20)
        )

        button_frame = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )

        button_frame.pack()

        # Første rad: Start og Pause
        top_button_row = ctk.CTkFrame(
            button_frame,
            fg_color="transparent"
        )

        top_button_row.pack(
            pady=(0, 8)
        )

        self.start_timer_button = ctk.CTkButton(
            top_button_row,
            text="Start",
            width=110,
            command=self.start_timer,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER
        )

        self.start_timer_button.pack(
            side="left",
            padx=5
        )

        self.pause_timer_button = ctk.CTkButton(
            top_button_row,
            text="Pause",
            width=110,
            command=self.pause_timer,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER
        )

        self.pause_timer_button.pack(
            side="left",
            padx=5
        )

        # Andre rad: Lagre og Kast
        bottom_button_row = ctk.CTkFrame(
            button_frame,
            fg_color="transparent"
        )

        bottom_button_row.pack()

        self.save_timer_button = ctk.CTkButton(
            bottom_button_row,
            text="Lagre",
            width=110,
            command=self.save_timer,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER
        )

        self.save_timer_button.pack(
            side="left",
            padx=5
        )

        self.discard_timer_button = ctk.CTkButton(
            bottom_button_row,
            text="Kast",
            width=110,
            command=self.discard_timer,
            fg_color="transparent",
            hover_color=CARD_BG,
            text_color=TEXT_COLOR,
            border_width=1,
            border_color=BORDER_COLOR
        )

        self.discard_timer_button.pack(
            side="left",
            padx=5
        )

        # Historikk
        history_title = ctk.CTkLabel(
            page,
            text="Siste økter",
            font=ctk.CTkFont(
                size=17,
                weight="bold"
            )
        )

        history_title.pack(
            anchor="w",
            padx=30,
            pady=(35, 10)
        )

        self.session_history_frame = ctk.CTkScrollableFrame(
            page,
            fg_color="transparent",
            height=180
        )

        self.session_history_frame.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=(0, 20)
        )

        self.refresh_session_history()

        self.update_timer_display()

    def start_timer(self):

        if self.timer_running:
            return

        self.timer_started_at = time.monotonic()
        self.timer_running = True

        self.start_timer_button.configure(
            text="Fortsett"
        )



    def pause_timer(self):

        if not self.timer_running:
            return

        elapsed = (
            time.monotonic()
            - self.timer_started_at
        )

        self.timer_elapsed_seconds += elapsed

        self.timer_running = False
        self.timer_started_at = None

    def get_timer_seconds(self):

        total = self.timer_elapsed_seconds

        if self.timer_running:

            total += (
                time.monotonic()
                - self.timer_started_at
            )

        return int(total)

    def update_timer_display(self):

        total_seconds = (
            self.get_timer_seconds()
        )

        hours = (
            total_seconds // 3600
        )

        minutes = (
            total_seconds % 3600
        ) // 60

        seconds = (
            total_seconds % 60
        )

        self.timer_label.configure(
            text=(
                f"{hours:02}:"
                f"{minutes:02}:"
                f"{seconds:02}"
            )
        )

        self.after(
            200,
            self.update_timer_display
        )


    def save_timer(self):

        # Hvis timeren fortsatt går,
        # ta med tiden helt frem til Lagre ble trykket.
        if self.timer_running:

            elapsed = (
                time.monotonic()
                - self.timer_started_at
            )

            self.timer_elapsed_seconds += elapsed

            self.timer_running = False
            self.timer_started_at = None

        total_seconds = int(
            self.timer_elapsed_seconds
        )

        # Ikke lagre tomme økter
        if total_seconds <= 0:
            return

        technology = (
            self.timer_technology_menu
            .get()
        )

        project = (
            self.timer_project_menu
            .get()
        )

        if technology == "Ingen teknologi":
            messagebox.showinfo(
                "Ingen teknologi",
                "Velg eller legg til en teknologi før du lagrer."
            )
            return

        if project == "Ingen prosjekt":
            project = None

        session = {
            "date": (
                datetime.now()
                .isoformat(
                    timespec="seconds"
                )
            ),
            "technology": technology,
            "project": project,
            "seconds": total_seconds
        }

        self.data[
            "sessions"
        ].append(
            session
        )

        self.data[
            "total_seconds"
        ] += total_seconds

        self.save_data()

        self.reset_timer()

        self.refresh_home_page()
        self.refresh_session_history()
        
        
    def discard_timer(self):

        total_seconds = (
            self.get_timer_seconds()
        )

        # Hvis timeren allerede er tom,
        # er det ingenting å kaste.
        if total_seconds <= 0:
            return

        confirmed = messagebox.askyesno(
            "Kast økt",
            "Er du sikker på at du vil kaste denne økten?"
        )

        if not confirmed:
            return

        self.reset_timer()
    
    
    def reset_timer(self):

        self.timer_running = False
        self.timer_started_at = None
        self.timer_elapsed_seconds = 0

        self.timer_label.configure(
            text="00:00:00"
        )

        self.start_timer_button.configure(
            text="Start"
        )  
    

    def refresh_session_history(self):

        # Fjern gammel historikk fra skjermen
        for widget in (
            self.session_history_frame
            .winfo_children()
        ):
            widget.destroy()

        sessions = self.data["sessions"]

        if not sessions:

            label = ctk.CTkLabel(
                self.session_history_frame,
                text="Ingen registrerte økter ennå."
            )

            label.pack(
                anchor="w"
            )

            return

        # Vis alle øktene, nyeste først
        for index in range(
            len(sessions) - 1,
            -1,
            -1
        ):

            session = sessions[index]

            total_seconds = session.get(
                "seconds",
                0
            )

            # -------------------------
            # VARIGHET
            # -------------------------

            hours = (
                total_seconds // 3600
            )

            minutes = (
                total_seconds % 3600
            ) // 60

            seconds = (
                total_seconds % 60
            )

            if hours > 0:

                duration = (
                    f"{hours} t "
                    f"{minutes} min"
                )

            elif minutes > 0:

                duration = (
                    f"{minutes} min "
                    f"{seconds} sek"
                )

            else:

                duration = (
                    f"{seconds} sek"
                )

            # -------------------------
            # DATO
            # -------------------------

            saved_date = session.get(
                "date"
            )

            if saved_date:

                try:

                    session_date = (
                        datetime.fromisoformat(
                            saved_date
                        )
                    )

                    date_text = (
                        session_date.strftime(
                            "%d.%m.%Y kl. %H:%M"
                        )
                    )

                except ValueError:

                    date_text = (
                        saved_date
                    )

            else:

                date_text = ""

            # -------------------------
            # TEKNOLOGI / PROSJEKT
            # -------------------------

            technology = session.get(
                "technology",
                "Ukjent teknologi"
            )

            project = session.get(
                "project"
            )

            if project:

                session_text = (
                    f"{technology} "
                    f"• {project} "
                    f"• {duration}"
                )

            else:

                session_text = (
                    f"{technology} "
                    f"• {duration}"
                )

            # -------------------------
            # KORT FOR ØKT
            # -------------------------

            session_frame = ctk.CTkFrame(
                self.session_history_frame,
                fg_color=CARD_LIGHT,
                corner_radius=8,
                border_width=1,
                border_color=BORDER_COLOR
            )

            session_frame.pack(
                fill="x",
                pady=4
            )

            top_row = ctk.CTkFrame(
                session_frame,
                fg_color="transparent"
            )

            top_row.pack(
                fill="x",
                padx=12,
                pady=(8, 0)
            )

            date_label = ctk.CTkLabel(
                top_row,
                text=date_text,
                font=ctk.CTkFont(
                    size=11
                ),
                text_color=MUTED_TEXT
            )

            date_label.pack(
                side="left"
            )

            delete_button = ctk.CTkButton(
                top_row,
                text="Slett",
                width=50,
                height=25,
                fg_color="transparent",
                hover_color=CARD_BG,
                text_color=TEXT_COLOR,
                command=lambda i=index:
                    self.delete_session(i)
            )

            delete_button.pack(
                side="right"
            )

            session_label = ctk.CTkLabel(
                session_frame,
                text=session_text,
                text_color=TEXT_COLOR
            )

            session_label.pack(
                anchor="w",
                padx=12,
                pady=(2, 8)
            )
    
    def delete_session(self, session_index):

        session = self.data[
            "sessions"
        ][session_index]

        technology = session.get(
            "technology",
            "Ukjent teknologi"
        )

        total_seconds = session.get(
            "seconds",
            0
        )

        confirmed = messagebox.askyesno(
            "Slett økt",
            (
                f"Er du sikker på at du vil "
                f"slette denne økten?\n\n"
                f"{technology} • "
                f"{self.format_time(total_seconds)}"
            )
        )

        if not confirmed:
            return

        # Fjern økten
        self.data[
            "sessions"
        ].pop(
            session_index
        )

        # Trekk tiden fra total tid
        self.data[
            "total_seconds"
        ] = max(
            0,
            self.data[
                "total_seconds"
            ] - total_seconds
        )

        self.save_data()

        # Oppdater visningen
        self.refresh_session_history()
        self.refresh_home_page()
        self.refresh_project_list()
        self.refresh_technology_list()
    

    # -------------------------
    # NOTATER
    # -------------------------

    def create_notes_page(self):
        page = self.pages["notes"]

        self.create_page_title(
            page,
            "Notater",
            "Skriv ned ting du lærer underveis."
        )

        button = ctk.CTkButton(
            page,
            text="+ Nytt notat",
            command=lambda: self.open_note_window(),
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER
        )

        button.pack(
            anchor="w",
            padx=30,
            pady=20
        )

        self.notes_list_frame = ctk.CTkScrollableFrame(
            page,
            fg_color="transparent"
        )

        self.notes_list_frame.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=(0, 20)
        )

        self.refresh_notes_list()


    def refresh_notes_list(self):
        # Fjern gamle notater fra skjermen
        for widget in self.notes_list_frame.winfo_children():
            widget.destroy()

        notes = self.data["notes"]

        if not notes:
            label = ctk.CTkLabel(
                self.notes_list_frame,
                text="Ingen notater ennå."
            )

            label.pack(
                anchor="w",
                pady=10
            )

            return

        # Nyeste notat øverst
        for index in range(
            len(notes) - 1,
            -1,
            -1
        ):
            note = notes[index]

            card = ctk.CTkFrame(
                self.notes_list_frame,
                fg_color=CARD_LIGHT,
                corner_radius=CARD_CORNER_RADIUS,
                border_width=1,
                border_color=BORDER_COLOR
            )

            card.pack(
                fill="x",
                pady=6
            )

            # Øverste rad
            top_row = ctk.CTkFrame(
                card,
                fg_color="transparent"
            )

            top_row.pack(
                fill="x",
                padx=15,
                pady=(12, 3)
            )

            title_label = ctk.CTkLabel(
                top_row,
                text=note["title"],
                font=ctk.CTkFont(
                    size=16,
                    weight="bold"
                ),
                text_color=TEXT_COLOR
            )

            title_label.pack(
                side="left"
            )

            delete_button = ctk.CTkButton(
                top_row,
                text="Slett",
                width=55,
                height=28,
                fg_color="transparent",
                hover_color=CARD_BG,
                text_color=TEXT_COLOR,
                command=lambda i=index:
                    self.delete_note(i)
            )

            delete_button.pack(
                side="right",
                padx=(5, 0)
            )

            edit_button = ctk.CTkButton(
                top_row,
                text="Rediger",
                width=70,
                height=28,
                fg_color=ACCENT,
                hover_color=ACCENT_HOVER,
                command=lambda i=index:
                    self.open_note_window(i)
            )

            edit_button.pack(
                side="right"
            )

            # Teknologi og dato
            info_label = ctk.CTkLabel(
                card,
                text=(
                    f"{note.get('technology', 'Generelt')} "
                    f"• {note.get('date', '')}"
                ),
                font=ctk.CTkFont(
                    size=11
                ),
                text_color=MUTED_TEXT
            )

            info_label.pack(
                anchor="w",
                padx=15
            )

            # Notattekst
            text_label = ctk.CTkLabel(
                card,
                text=note["text"],
                justify="left",
                anchor="w",
                wraplength=450,
                text_color=TEXT_COLOR
            )

            text_label.pack(
                anchor="w",
                padx=15,
                pady=(8, 12)
            )


    def open_note_window(self, note_index=None):
        self.editing_note_index = note_index

        editing = note_index is not None

        if editing:
            note = self.data["notes"][note_index]
            window_title = "Rediger notat"
        else:
            note = None
            window_title = "Nytt notat"

        self.note_window = ctk.CTkToplevel(
            self
        )

        self.note_window.title(
            window_title
        )

        self.note_window.geometry(
            "430x540"
        )

        self.note_window.resizable(
            False,
            False
        )

        self.note_window.transient(
            self
        )

        self.note_window.grab_set()

        title = ctk.CTkLabel(
            self.note_window,
            text=window_title,
            font=ctk.CTkFont(
                size=22,
                weight="bold"
            )
        )

        title.pack(
            anchor="w",
            padx=25,
            pady=(25, 15)
        )

        # -------------------------
        # TITTEL
        # -------------------------

        title_label = ctk.CTkLabel(
            self.note_window,
            text="Tittel"
        )

        title_label.pack(
            anchor="w",
            padx=25
        )

        self.note_title_entry = ctk.CTkEntry(
            self.note_window,
            placeholder_text="Hva lærte du?"
        )

        self.note_title_entry.pack(
            fill="x",
            padx=25,
            pady=(5, 15)
        )

        if editing:
            self.note_title_entry.insert(
                0,
                note["title"]
            )

        # -------------------------
        # TEKNOLOGI
        # -------------------------

        technology_label = ctk.CTkLabel(
            self.note_window,
            text="Teknologi"
        )

        technology_label.pack(
            anchor="w",
            padx=25
        )

        technology_values = (
            ["Generelt"]
            + self.data["technologies"]
        )

        self.note_technology_menu = ctk.CTkOptionMenu(
            self.note_window,
            values=technology_values,
            fg_color=ACCENT,
            button_color=ACCENT,
            button_hover_color=ACCENT_HOVER
        )

        self.note_technology_menu.pack(
            fill="x",
            padx=25,
            pady=(5, 15)
        )

        if editing:
            saved_technology = note.get(
                "technology",
                "Generelt"
            )

            if saved_technology in technology_values:
                self.note_technology_menu.set(
                    saved_technology
                )
            else:
                self.note_technology_menu.set(
                    "Generelt"
                )

        else:
            self.note_technology_menu.set(
                "Generelt"
            )

        # -------------------------
        # NOTATTEKST
        # -------------------------

        note_label = ctk.CTkLabel(
            self.note_window,
            text="Notat"
        )

        note_label.pack(
            anchor="w",
            padx=25
        )

        self.note_textbox = ctk.CTkTextbox(
            self.note_window,
            height=180
        )

        self.note_textbox.pack(
            fill="x",
            padx=25,
            pady=(5, 15)
        )

        if editing:
            self.note_textbox.insert(
                "1.0",
                note["text"]
            )

        # -------------------------
        # FEILMELDING
        # -------------------------

        self.note_error_label = ctk.CTkLabel(
            self.note_window,
            text=""
        )

        self.note_error_label.pack()

        # -------------------------
        # LAGRE
        # -------------------------

        if editing:
            button_text = "Lagre endringer"
        else:
            button_text = "Lagre notat"

        save_button = ctk.CTkButton(
            self.note_window,
            text=button_text,
            command=self.save_note,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER
        )

        save_button.pack(
            pady=8
        )


    def save_note(self):
        title = (
            self.note_title_entry
            .get()
            .strip()
        )

        text = (
            self.note_textbox
            .get(
                "1.0",
                "end"
            )
            .strip()
        )

        technology = (
            self.note_technology_menu
            .get()
        )

        if title == "":
            self.note_error_label.configure(
                text="Skriv inn en tittel."
            )
            return

        if text == "":
            self.note_error_label.configure(
                text="Skriv inn et notat."
            )
            return

        # Hvis vi redigerer et eksisterende notat,
        # beholder vi den opprinnelige datoen.
        if self.editing_note_index is not None:
            old_note = self.data[
                "notes"
            ][self.editing_note_index]

            note_date = old_note.get(
                "date",
                datetime.now().isoformat(
                    timespec="minutes"
                )
            )

        else:
            note_date = (
                datetime.now()
                .isoformat(
                    timespec="minutes"
                )
            )

        new_note = {
            "title": title,
            "text": text,
            "technology": technology,
            "date": note_date
        }

        if self.editing_note_index is not None:
            self.data[
                "notes"
            ][self.editing_note_index] = new_note

        else:
            self.data[
                "notes"
            ].append(
                new_note
            )

        self.save_data()
        self.refresh_notes_list()

        self.note_window.destroy()


    def delete_note(self, note_index):
        note = self.data[
            "notes"
        ][note_index]

        confirmed = messagebox.askyesno(
            "Slett notat",
            (
                f"Er du sikker på at du vil "
                f"slette '{note['title']}'?"
            )
        )

        if not confirmed:
            return

        self.data[
            "notes"
        ].pop(
            note_index
        )

        self.save_data()
        self.refresh_notes_list()

    # -------------------------
    # FELLES
    # -------------------------

    def on_close(self):

        unsaved_seconds = (
            self.get_timer_seconds()
        )

        if unsaved_seconds > 0:

            confirmed = messagebox.askyesno(
                "Ulagret økt",
                (
                    "Du har en ulagret timerøkt.\n\n"
                    "Hvis du lukker DevTrack nå, "
                    "blir denne økten kastet.\n\n"
                    "Vil du lukke likevel?"
                )
            )

            if not confirmed:
                return

        self.destroy()
    
    
    def format_time(
        self,
        total_seconds
    ):
        """Gjør sekunder om til en pen tekst."""

        hours = (
            total_seconds // 3600
        )

        minutes = (
            total_seconds % 3600
        ) // 60

        if hours > 0:
            return (
                f"{hours} t "
                f"{minutes} min"
            )

        return (
            f"{minutes} min"
        )

    def get_technology_time(
        self,
        technology
    ):
        """Regner ut total tid brukt på én teknologi."""

        total_seconds = 0

        for session in self.data[
            "sessions"
        ]:

            if (
                session.get(
                    "technology"
                )
                == technology
            ):

                total_seconds += (
                    session.get(
                        "seconds",
                        0
                    )
                )

        return total_seconds

    def get_project_time(
        self,
        project_name
    ):
        """Regner ut total tid brukt på ett prosjekt."""

        total_seconds = 0

        for session in self.data[
            "sessions"
        ]:

            if (
                session.get(
                    "project"
                )
                == project_name
            ):

                total_seconds += (
                    session.get(
                        "seconds",
                        0
                    )
                )

        return total_seconds

    def get_skill_counts(
        self,
        technology
    ):
        """Teller hvor mange ferdigheter som er på hvert nivå."""

        counts = {
            "Ikke startet": 0,
            "Under læring": 0,
            "Kan bruke": 0,
            "Trygg": 0
        }

        skills = self.data[
            "skills"
        ].get(
            technology,
            {}
        )

        for level in skills.values():

            if level in counts:
                counts[level] += 1

        return counts

    def get_projects_for_technology(
        self,
        technology
    ):
        """Finner alle prosjekter som bruker en bestemt teknologi."""

        matching_projects = []

        for project in self.data[
            "projects"
        ]:

            technologies = project.get(
                "technologies",
                []
            )

            if technology in technologies:

                matching_projects.append(
                    project
                )

        return matching_projects

    def create_page_title(
        self,
        page,
        title,
        subtitle
    ):

        title_label = ctk.CTkLabel(
            page,
            text=title,
            font=ctk.CTkFont(
                size=26,
                weight="bold"
            )
        )

        title_label.pack(
            anchor="w",
            padx=30,
            pady=(35, 5)
        )

        subtitle_label = ctk.CTkLabel(
            page,
            text=subtitle
        )

        subtitle_label.pack(
            anchor="w",
            padx=30
        )

    def refresh_timer_options(self):
        # -------------------------
        # TEKNOLOGIER
        # -------------------------

        technologies = self.data["technologies"]

        if technologies:
            technology_values = technologies
        else:
            technology_values = ["Ingen teknologi"]

        self.timer_technology_menu.configure(
            values=technology_values
        )

        current_technology = (
            self.timer_technology_menu.get()
        )

        if current_technology not in technology_values:
            self.timer_technology_menu.set(
                technology_values[0]
            )

        # -------------------------
        # PROSJEKTER
        # -------------------------

        project_names = [
            project["name"]
            for project in self.data["projects"]
        ]

        if not project_names:
            project_names = [
                "Ingen prosjekt"
            ]

        self.timer_project_menu.configure(
            values=project_names
        )

        current_project = (
            self.timer_project_menu.get()
        )

        if current_project not in project_names:
            self.timer_project_menu.set(
                project_names[0]
            )

    def show_page(
        self,
        page_name
    ):

        if page_name == "timer":
            self.refresh_timer_options()

        self.pages[
            page_name
        ].tkraise()