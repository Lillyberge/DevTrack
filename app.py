import customtkinter as ctk
import json
import time
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path
from tkinter import messagebox
import tkinter as tk
import sys
import os

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
    CODE_BG,
    CODE_TEXT,
)


# -------------------------
# APP-INNSTILLINGER
# -------------------------

ctk.set_appearance_mode("light")

# Norske navn, brukt når datoer skal vises.
# MONTHS[0] er januar, WEEKDAYS[0] er mandag.
MONTHS = [
    "januar", "februar", "mars", "april",
    "mai", "juni", "juli", "august",
    "september", "oktober", "november", "desember"
]

WEEKDAYS = [
    "mandag", "tirsdag", "onsdag", "torsdag",
    "fredag", "lørdag", "søndag"
]

# Nivåene en ferdighet kan ha, fra lavest til høyest.
# Knappene viser en kortere tekst for "Under læring".
SKILL_LEVELS = [
    "Ikke startet",
    "Under læring",
    "Kan bruke",
    "Trygg"
]

SKILL_BUTTON_LABELS = [
    "Ikke startet",
    "Lærer",
    "Kan bruke",
    "Trygg"
]

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

WINDOW_STATE_FILE = (
    APP_SUPPORT_DIR
    / "window_state.json"
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

        # Åpne vinduet på samme sted og med samme
        # størrelse som da DevTrack sist ble lukket.
        self.restore_window_geometry()

        # Timer-status
        self.timer_running = False
        self.timer_started_at = None
        self.timer_elapsed_seconds = 0

        # Holder styr på Canvas-scrollingen på hovedsidene.
        # Hovedsidene bruker samme type scrolling som
        # teknologi-vinduet.
        self.main_scroll_canvases = {}
        self.active_scroll_canvas = None

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

        # Fast scrolling for hovedvinduet.
        # Dette gjør scrollingen mer stabil når
        # DevTrack mister og får fokus igjen.
        self.bind(
            "<MouseWheel>",
            self.handle_main_scroll,
            add="+"
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
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as file:
                    data = json.load(file)

            except json.JSONDecodeError:
                backup_file = DATA_FILE.with_suffix(".bak")
                broken_file = DATA_FILE.with_suffix(".broken")

                messagebox.showwarning(
                    "Problem med data",
                    "data.json var ødelagt.\n\n"
                    "DevTrack henter dataene fra siste backup."
                )

                # Flytt den ødelagte filen til side,
                # så den ikke overskriver backupen.
                os.replace(DATA_FILE, broken_file)

                with open(backup_file, "r", encoding="utf-8") as file:
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
        """Lagrer data trygt i data.json."""

        if data is None:
            data = self.data

        temp_file = DATA_FILE.with_suffix(".tmp")
        backup_file = DATA_FILE.with_suffix(".bak")

        # 1. Skriv alt til en midlertidig fil først.
        #    Hvis noe går galt her, er data.json fortsatt urørt.
        with open(temp_file, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

        # 2. Ta vare på forrige versjon som backup.
        if DATA_FILE.exists():
            shutil.copy2(DATA_FILE, backup_file)

        # 3. Bytt ut den gamle filen med den nye i ett trekk.
        os.replace(temp_file, DATA_FILE)

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

        # Menyen skal alltid være like bred, selv om
        # det som ligger i den vil ha mer plass.
        self.sidebar.grid_propagate(False)
        self.sidebar.pack_propagate(False)

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

        # Her lagres menyknappene, med sidenavnet
        # som nøkkel, f.eks. "home" -> Hjem-knappen.
        self.nav_buttons = {}

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
            "Notater",
            "notes"
        )

        self.create_nav_button(
            "Statistikk",
            "stats"
        )

        self.create_sidebar_timer()

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

        # Husk knappen, så show_page kan markere
        # hvilken side vi står på.
        self.nav_buttons[page] = button

    # -------------------------
    # SIDER
    # -------------------------

    def create_pages(self):

        self.pages = {}

        page_names = [
            "home",
            "technologies",
            "projects",
            "notes",
            "stats",
            "technology"
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
        self.create_notes_page()
        self.create_stats_page()
        self.create_technology_detail_page()

    def create_main_scroll_area(
        self,
        page_name
    ):
        """Lager en helside-scroll med vanlig Tkinter Canvas."""

        page = self.pages[
            page_name
        ]

        scroll_container = ctk.CTkFrame(
            page,
            fg_color=APP_BG,
            corner_radius=0
        )

        scroll_container.pack(
            fill="both",
            expand=True
        )

        scroll_container.grid_rowconfigure(
            0,
            weight=1
        )

        scroll_container.grid_columnconfigure(
            0,
            weight=1
        )

        canvas = tk.Canvas(
            scroll_container,
            bg=APP_BG,
            highlightthickness=0,
            borderwidth=0,
            yscrollincrement=1
        )

        canvas.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        scrollbar = ctk.CTkScrollbar(
            scroll_container,
            orientation="vertical",
            command=canvas.yview,
            fg_color=APP_BG,
            button_color=BORDER_COLOR,
            button_hover_color=MUTED_TEXT
        )

        scrollbar.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        canvas.configure(
            yscrollcommand=scrollbar.set
        )

        content = ctk.CTkFrame(
            canvas,
            fg_color=APP_BG,
            corner_radius=0
        )

        content_window = canvas.create_window(
            (0, 0),
            window=content,
            anchor="nw"
        )

        def update_scroll_region(
            event=None
        ):
            canvas.configure(
                scrollregion=canvas.bbox(
                    "all"
                )
            )

        content.bind(
            "<Configure>",
            update_scroll_region
        )

        def resize_content(event):
            canvas.itemconfigure(
                content_window,
                width=event.width
            )

        canvas.bind(
            "<Configure>",
            resize_content
        )

        self.main_scroll_canvases[
            page_name
        ] = canvas

        update_scroll_region()

        return content


    # -------------------------
    # HJEM
    # -------------------------

    def create_home_page(self):

        page = self.create_main_scroll_area(
            "home"
        )

        # Hilsen og streak.
        # Teksten fylles inn i refresh_home_page.
        self.home_title_label = ctk.CTkLabel(
            page,
            text="",
            font=ctk.CTkFont(
                size=26,
                weight="bold"
            ),
            text_color=TEXT_COLOR
        )

        self.home_title_label.pack(
            anchor="w",
            padx=PAGE_PADDING,
            pady=(30, 3)
        )

        self.home_subtitle_label = ctk.CTkLabel(
            page,
            text="",
            text_color=MUTED_TEXT
        )

        self.home_subtitle_label.pack(
            anchor="w",
            padx=PAGE_PADDING
        )

        # Øverste rad: timer til venstre, uka til høyre.
        top_row = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )

        top_row.pack(
            fill="x",
            padx=PAGE_PADDING,
            pady=(20, 18)
        )

        # "uniform" gjør at de to kortene alltid
        # er like brede.
        top_row.grid_columnconfigure(
            (0, 1),
            weight=1,
            uniform="top"
        )

        self.create_home_today_card(top_row)
        self.create_home_week_card(top_row)

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

        # Kortene har 4 piksler luft rundt seg,
        # så vi trekker fra 4 her for at kantene
        # skal stå på linje med kortene over.
        self.home_technologies_frame.pack(
            fill="x",
            padx=PAGE_PADDING - 4,
            pady=(0, 20)
        )

        self.refresh_home_page()

    def create_home_card(
        self,
        parent,
        column
    ):
        """Lager et tomt kort i den øverste raden på Hjem."""

        card = ctk.CTkFrame(
            parent,
            corner_radius=CARD_CORNER_RADIUS,
            fg_color=CARD_LIGHT,
            border_width=1,
            border_color=BORDER_COLOR
        )

        card.grid(
            row=0,
            column=column,
            sticky="nsew",
            padx=(0, 6) if column == 0 else (6, 0)
        )

        return card

    def create_home_today_card(self, parent):
        """I dag-kortet: tid i dag og siste økt.
        Selve timeren ligger nederst i menyen."""

        card = self.create_home_card(parent, 0)

        title = ctk.CTkLabel(
            card,
            text="I dag",
            text_color=MUTED_TEXT
        )

        title.pack(
            anchor="w",
            padx=18,
            pady=(14, 0)
        )

        self.home_today_label = ctk.CTkLabel(
            card,
            text="0 min",
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(
                size=30,
                weight="bold"
            )
        )

        self.home_today_label.pack(
            anchor="w",
            padx=18
        )

        self.home_today_count_label = ctk.CTkLabel(
            card,
            text="",
            text_color=MUTED_TEXT
        )

        self.home_today_count_label.pack(
            anchor="w",
            padx=18
        )

        last_title = ctk.CTkLabel(
            card,
            text="Siste økt",
            text_color=MUTED_TEXT,
            font=ctk.CTkFont(
                size=11,
                weight="bold"
            )
        )

        last_title.pack(
            anchor="w",
            padx=18,
            pady=(10, 0)
        )

        self.home_last_session_label = ctk.CTkLabel(
            card,
            text="",
            text_color=TEXT_COLOR,
            anchor="w",
            justify="left",
            wraplength=220
        )

        self.home_last_session_label.pack(
            anchor="w",
            padx=18,
            pady=(0, 14)
        )

    def refresh_home_today_card(self, daily_seconds):

        today = date.today()

        self.home_today_label.configure(
            text=self.format_time(
                daily_seconds[today]
            )
        )

        today_count = 0

        for session in self.data["sessions"]:
            if self.get_session_day(session) == today:
                today_count += 1

        if today_count == 0:
            count_text = "Ingen økter ennå i dag"
        elif today_count == 1:
            count_text = "1 økt"
        else:
            count_text = f"{today_count} økter"

        self.home_today_count_label.configure(
            text=count_text
        )

        if not self.data["sessions"]:
            self.home_last_session_label.configure(
                text="Start timeren nede til venstre."
            )
            return

        # max med key= finner økten med senest dato
        last_session = max(
            self.data["sessions"],
            key=lambda session: session.get("date", "")
        )

        technology = last_session.get(
            "technology",
            "Ukjent teknologi"
        )

        project = last_session.get("project")

        text = technology

        if project:
            text += f" · {project}"

        text += (
            f", {self.format_duration(last_session.get('seconds', 0))}"
        )

        description = last_session.get("description")

        if description:
            # Korte ned lange beskrivelser
            if len(description) > 80:
                description = description[:80].rstrip() + "…"

            text += f"\n{description}"

        self.home_last_session_label.configure(
            text=text
        )

    def create_home_week_card(self, parent):
        """Uke-kortet: tid denne uka, søylediagram og streak."""

        card = self.create_home_card(parent, 1)

        header = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        header.pack(
            fill="x",
            padx=18,
            pady=(14, 6)
        )

        # Overskriften og tiden står under hverandre,
        # slik at de får plass også i et smalt vindu.

        week_title = ctk.CTkLabel(
            header,
            text="Siste 7 dager",
            text_color=MUTED_TEXT
        )

        week_title.pack(
            anchor="w"
        )

        self.home_week_total_label = ctk.CTkLabel(
            header,
            text="0 min",
            font=ctk.CTkFont(
                size=22,
                weight="bold"
            ),
            text_color=TEXT_COLOR
        )

        self.home_week_total_label.pack(
            anchor="w"
        )

        # Søylene tegnes i refresh_home_page,
        # fordi de må lages på nytt når tallene endres.
        self.home_week_chart = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        self.home_week_chart.pack(
            fill="x",
            padx=18
        )

        self.home_streak_label = ctk.CTkLabel(
            card,
            text="",
            text_color=ACCENT,
            font=ctk.CTkFont(
                weight="bold"
            )
        )

        self.home_streak_label.pack(
            anchor="w",
            padx=18,
            pady=(4, 12)
        )

    def refresh_home_page(self):

        # Sørg for at timerens teknologiliste er oppdatert,
        # siden timeren også kan startes herfra.
        # (Timer-siden finnes ikke ennå første gang
        # Hjem-siden tegnes, derfor hasattr.)
        if hasattr(self, "timer_technology_menu"):
            self.refresh_timer_options()

        # -------------------------
        # HILSEN OG STREAK
        # -------------------------

        hour = datetime.now().hour

        if hour < 10:
            greeting = "God morgen"
        elif hour < 18:
            greeting = "God dag"
        else:
            greeting = "God kveld"

        self.home_title_label.configure(
            text=greeting
        )

        streak = self.get_streak()

        total_time = self.format_time(
            self.data["total_seconds"]
        )

        if streak == 0:
            streak_text = "Start en økt for å begynne en ny streak."
        elif streak == 1:
            streak_text = "Du har kodet 1 dag på rad."
        else:
            streak_text = f"Du har kodet {streak} dager på rad."

        self.home_subtitle_label.configure(
            text=f"{streak_text}  ·  {total_time} totalt"
        )

        if streak > 0:
            self.home_streak_label.configure(
                text=f"{streak} {'dag' if streak == 1 else 'dager'} på rad"
            )
        else:
            self.home_streak_label.configure(
                text="Ingen streak ennå"
            )

        # -------------------------
        # SISTE 7 DAGER
        # -------------------------

        daily_seconds = self.get_daily_seconds(7)

        self.home_week_total_label.configure(
            text=self.format_time(
                sum(daily_seconds.values())
            )
        )

        self.draw_week_chart(daily_seconds)

        self.refresh_home_today_card(daily_seconds)

        # -------------------------
        # TEKNOLOGIER
        # -------------------------

        for widget in (
            self.home_technologies_frame
            .winfo_children()
        ):
            widget.destroy()

        # Tre kort per rad, like brede.
        columns = 3

        self.home_technologies_frame.grid_columnconfigure(
            tuple(range(columns)),
            weight=1,
            uniform="tech"
        )

        for index, technology in enumerate(
            self.data["technologies"]
        ):

            # Hvilken rad og kolonne kortet skal stå i.
            # // er heltallsdivisjon og % er resten:
            # kort nr. 4 (index 3) havner i rad 1, kolonne 0.
            row = index // columns
            column = index % columns

            self.create_home_technology_card(
                technology,
                row,
                column
            )

    def create_home_technology_card(
        self,
        technology,
        row,
        column
    ):
        """Et lite kort med navn, tid og fremgang."""

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

        card.grid(
            row=row,
            column=column,
            sticky="nsew",
            padx=4,
            pady=4
        )

        name_label = ctk.CTkLabel(
            card,
            text=technology,
            font=ctk.CTkFont(
                size=15,
                weight="bold"
            ),
            text_color=TEXT_COLOR
        )

        name_label.pack(
            anchor="w",
            padx=14,
            pady=(10, 0)
        )

        time_label = ctk.CTkLabel(
            card,
            text=self.format_time(
                self.get_technology_time(
                    technology
                )
            ),
            text_color=MUTED_TEXT
        )

        time_label.pack(
            anchor="w",
            padx=14
        )

        progress_bar = ctk.CTkProgressBar(
            card,
            height=8,
            progress_color=ACCENT,
            fg_color=CARD_BG
        )

        progress_bar.pack(
            fill="x",
            padx=14,
            pady=(4, 14)
        )

        progress_bar.set(
            progress
        )

        self.make_clickable(
            card,
            lambda: self.show_technology(technology)
        )

    def draw_week_chart(self, daily_seconds):
        """Tegner én søyle per dag. Den høyeste
        dagen får full høyde, de andre i forhold til den."""

        for widget in (
            self.home_week_chart
            .winfo_children()
        ):
            widget.destroy()

        max_bar_height = 70

        # Unngå å dele på 0 hvis det ikke er
        # logget noe tid denne uka.
        most_seconds = max(
            max(daily_seconds.values()),
            1
        )

        weekday_letters = [
            "M", "T", "O", "T", "F", "L", "S"
        ]

        today = date.today()

        for index, (day, seconds) in enumerate(
            daily_seconds.items()
        ):

            self.home_week_chart.grid_columnconfigure(
                index,
                weight=1,
                uniform="day"
            )

            # En fast høy "boks" som søylen står
            # i bunnen av, så alle søylene starter
            # på samme linje.
            bar_area = ctk.CTkFrame(
                self.home_week_chart,
                height=max_bar_height,
                fg_color="transparent"
            )

            bar_area.grid(
                row=0,
                column=index,
                sticky="ew",
                padx=2
            )

            bar_area.pack_propagate(False)

            if seconds > 0:
                bar_height = max(
                    6,
                    int(
                        seconds
                        / most_seconds
                        * max_bar_height
                    )
                )

                # I dag får den sterkeste fargen.
                if day == today:
                    bar_color = ACCENT
                else:
                    bar_color = ACCENT_HOVER

            else:
                bar_height = 4
                bar_color = BORDER_COLOR

            bar = ctk.CTkFrame(
                bar_area,
                height=bar_height,
                corner_radius=4,
                fg_color=bar_color
            )

            bar.pack(
                side="bottom",
                fill="x"
            )

            day_label = ctk.CTkLabel(
                self.home_week_chart,
                text=weekday_letters[day.weekday()],
                height=18,
                text_color=(
                    TEXT_COLOR
                    if day == today
                    else MUTED_TEXT
                ),
                font=ctk.CTkFont(
                    size=11,
                    weight=(
                        "bold"
                        if day == today
                        else "normal"
                    )
                )
            )

            day_label.grid(
                row=1,
                column=index
            )

    def get_session_day(self, session):
        """Finner datoen en økt ble lagret.
        Gir None hvis datoen mangler eller er ugyldig."""

        try:
            return datetime.fromisoformat(
                session["date"]
            ).date()

        except (KeyError, TypeError, ValueError):
            return None

    def get_daily_seconds(self, number_of_days):
        """Regner ut hvor mye tid som er logget
        hver dag de siste dagene, med i dag sist."""

        today = date.today()

        # Lag en tom oversikt først, så dager
        # uten økter også blir med (med 0 sekunder).
        daily_seconds = {}

        for days_ago in range(
            number_of_days - 1,
            -1,
            -1
        ):
            day = today - timedelta(days=days_ago)
            daily_seconds[day] = 0

        for session in self.data["sessions"]:

            day = self.get_session_day(session)

            if day in daily_seconds:
                daily_seconds[day] += session.get(
                    "seconds",
                    0
                )

        return daily_seconds

    def get_streak(self):
        """Teller hvor mange dager på rad du har kodet.

        Hvis du ikke har kodet i dag ennå,
        teller vi fra i går, så streaken ikke
        forsvinner før dagen er over."""

        coding_days = set()

        for session in self.data["sessions"]:

            day = self.get_session_day(session)

            if day is not None:
                coding_days.add(day)

        day = date.today()

        if day not in coding_days:
            day -= timedelta(days=1)

        streak = 0

        while day in coding_days:
            streak += 1
            day -= timedelta(days=1)

        return streak

    # -------------------------
    # TEKNOLOGIER
    # -------------------------

    def create_technologies_page(self):

        page = self.create_main_scroll_area(
            "technologies"
        )

        self.create_page_title(
            page,
            "Teknologier",
            "Språk og verktøy du lærer. Klikk på en for å se ferdighetene."
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
            padx=PAGE_PADDING,
            pady=20
        )

        self.technology_list_frame = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )

        # Kortene har 4 piksler luft rundt seg
        self.technology_list_frame.pack(
            fill="x",
            padx=PAGE_PADDING - 4,
            pady=(0, 20)
        )

        self.technology_list_frame.grid_columnconfigure(
            (0, 1),
            weight=1,
            uniform="technology"
        )

        self.refresh_technology_list()

    def refresh_technology_list(self):

        for widget in self.technology_list_frame.winfo_children():
            widget.destroy()

        if not self.data["technologies"]:
            empty_label = ctk.CTkLabel(
                self.technology_list_frame,
                text="Ingen teknologier lagt til ennå.",
                text_color=MUTED_TEXT
            )

            empty_label.grid(
                row=0,
                column=0,
                sticky="w",
                padx=4
            )

            return

        # To kort per rad
        for index, technology in enumerate(
            self.data["technologies"]
        ):
            self.create_technology_list_card(
                technology,
                row=index // 2,
                column=index % 2
            )

    def create_technology_list_card(
        self,
        technology,
        row,
        column
    ):
        """Et kort i teknologilisten. Hele kortet
        kan klikkes for å åpne teknologien."""

        skill_counts = self.get_skill_counts(technology)

        total_skills = sum(skill_counts.values())

        card = ctk.CTkFrame(
            self.technology_list_frame,
            corner_radius=CARD_CORNER_RADIUS,
            fg_color=CARD_LIGHT,
            border_width=1,
            border_color=BORDER_COLOR
        )

        card.grid(
            row=row,
            column=column,
            sticky="nsew",
            padx=4,
            pady=4
        )

        top_row = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        top_row.pack(
            fill="x",
            padx=16,
            pady=(12, 0)
        )

        name_label = ctk.CTkLabel(
            top_row,
            text=technology,
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(
                size=17,
                weight="bold"
            )
        )

        name_label.pack(
            side="left"
        )

        arrow_label = ctk.CTkLabel(
            top_row,
            text="›",
            text_color=MUTED_TEXT,
            font=ctk.CTkFont(size=20)
        )

        arrow_label.pack(
            side="right"
        )

        time_label = ctk.CTkLabel(
            card,
            text=self.format_time(
                self.get_technology_time(technology)
            ),
            text_color=MUTED_TEXT
        )

        time_label.pack(
            anchor="w",
            padx=16
        )

        progress_bar = ctk.CTkProgressBar(
            card,
            height=8,
            progress_color=ACCENT,
            fg_color=CARD_BG
        )

        progress_bar.pack(
            fill="x",
            padx=16,
            pady=(6, 4)
        )

        progress_bar.set(
            self.get_skill_progress(technology)
        )

        if total_skills > 0:
            skills_text = (
                f"{skill_counts['Trygg']} av {total_skills} "
                f"ferdigheter er trygge"
            )
        else:
            skills_text = "Ingen ferdigheter ennå"

        skills_label = ctk.CTkLabel(
            card,
            text=skills_text,
            text_color=MUTED_TEXT,
            font=ctk.CTkFont(size=12)
        )

        skills_label.pack(
            anchor="w",
            padx=16,
            pady=(0, 12)
        )

        self.make_clickable(
            card,
            lambda: self.show_technology(technology)
        )

    def make_clickable(self, widget, command):
        """Gjør et kort og alt inni det klikkbart.

        Funksjonen kaller seg selv for hvert barn
        (det kalles rekursjon), slik at et klikk
        på teksten inni kortet også virker."""

        widget.bind(
            "<Button-1>",
            lambda event: command(),
            add="+"
        )

        try:
            widget.configure(cursor="hand2")
        except (ValueError, tk.TclError):
            pass

        for child in widget.winfo_children():
            self.make_clickable(child, command)

    def get_skill_progress(self, technology):
        """Gir et tall mellom 0 og 1 for hvor langt
        du har kommet. Trygg teller 3 poeng,
        Kan bruke 2 og Under læring 1."""

        skill_counts = self.get_skill_counts(technology)

        total_skills = sum(skill_counts.values())

        if total_skills == 0:
            return 0

        points = (
            skill_counts["Under læring"]
            + skill_counts["Kan bruke"] * 2
            + skill_counts["Trygg"] * 3
        )

        return points / (total_skills * 3)

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

        self.show_page("technologies")

    # -------------------------
    # ÉN TEKNOLOGI
    # -------------------------

    def create_technology_detail_page(self):
        """Siden for én teknologi. Innholdet lages
        på nytt hver gang du åpner en teknologi."""

        self.technology_detail_frame = (
            self.create_main_scroll_area(
                "technology"
            )
        )

    def show_technology(self, technology):

        self.current_technology = technology

        frame = self.technology_detail_frame

        for widget in frame.winfo_children():
            widget.destroy()

        # -------------------------
        # TOPP
        # -------------------------

        back_button = ctk.CTkButton(
            frame,
            text="‹ Teknologier",
            width=10,
            height=26,
            fg_color="transparent",
            hover_color=CARD_BG,
            text_color=MUTED_TEXT,
            anchor="w",
            command=lambda: self.show_page("technologies")
        )

        back_button.pack(
            anchor="w",
            padx=PAGE_PADDING - 8,
            pady=(24, 0)
        )

        header = ctk.CTkFrame(
            frame,
            fg_color="transparent"
        )

        header.pack(
            fill="x",
            padx=PAGE_PADDING
        )

        title = ctk.CTkLabel(
            header,
            text=technology,
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(
                size=26,
                weight="bold"
            )
        )

        title.pack(
            side="left"
        )

        start_button = ctk.CTkButton(
            header,
            text="Start timer",
            width=110,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=lambda: self.start_timer_for(technology)
        )

        start_button.pack(
            side="right"
        )

        subtitle = ctk.CTkLabel(
            frame,
            text=self.get_technology_subtitle(technology),
            text_color=MUTED_TEXT
        )

        subtitle.pack(
            anchor="w",
            padx=PAGE_PADDING
        )

        # -------------------------
        # OPPSUMMERING
        # -------------------------

        summary_card = self.create_detail_card(frame)

        counts_row = ctk.CTkFrame(
            summary_card,
            fg_color="transparent"
        )

        counts_row.pack(
            fill="x",
            padx=16,
            pady=(12, 4)
        )

        counts_row.grid_columnconfigure(
            (0, 1, 2, 3),
            weight=1,
            uniform="count"
        )

        # Tallene oppdateres når du endrer et nivå,
        # så vi tar vare på dem i en ordbok.
        self.technology_count_labels = {}

        for column, level in enumerate(SKILL_LEVELS):

            level_label = ctk.CTkLabel(
                counts_row,
                text=level,
                text_color=MUTED_TEXT,
                font=ctk.CTkFont(size=12),
                height=16
            )

            level_label.grid(
                row=0,
                column=column,
                sticky="w"
            )

            count_label = ctk.CTkLabel(
                counts_row,
                text="0",
                text_color=TEXT_COLOR,
                font=ctk.CTkFont(
                    size=20,
                    weight="bold"
                )
            )

            count_label.grid(
                row=1,
                column=column,
                sticky="w"
            )

            self.technology_count_labels[level] = count_label

        self.technology_progress_bar = ctk.CTkProgressBar(
            summary_card,
            height=8,
            progress_color=ACCENT,
            fg_color=CARD_BG
        )

        self.technology_progress_bar.pack(
            fill="x",
            padx=16,
            pady=(4, 16)
        )

        # -------------------------
        # NESTE Å LÆRE
        # -------------------------

        next_card = ctk.CTkFrame(
            frame,
            corner_radius=CARD_CORNER_RADIUS,
            fg_color=CARD_BG
        )

        next_card.pack(
            fill="x",
            padx=PAGE_PADDING,
            pady=6
        )

        next_title = ctk.CTkLabel(
            next_card,
            text="Neste å lære",
            text_color=MUTED_TEXT,
            font=ctk.CTkFont(size=12)
        )

        next_title.pack(
            anchor="w",
            padx=16,
            pady=(10, 0)
        )

        self.next_skill_label = ctk.CTkLabel(
            next_card,
            text="",
            text_color=ACCENT,
            font=ctk.CTkFont(
                size=16,
                weight="bold"
            )
        )

        self.next_skill_label.pack(
            anchor="w",
            padx=16
        )

        self.next_skill_hint_label = ctk.CTkLabel(
            next_card,
            text="",
            text_color=TEXT_COLOR,
            justify="left",
            anchor="w"
        )

        self.next_skill_hint_label.pack(
            anchor="w",
            padx=16,
            pady=(0, 10)
        )

        # -------------------------
        # FERDIGHETER
        # -------------------------

        skills_card = self.create_detail_card(frame)

        skills_header = ctk.CTkFrame(
            skills_card,
            fg_color="transparent"
        )

        skills_header.pack(
            fill="x",
            padx=16,
            pady=(12, 4)
        )

        skills_title = ctk.CTkLabel(
            skills_header,
            text="Ferdigheter",
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(
                size=15,
                weight="bold"
            )
        )

        skills_title.pack(
            side="left"
        )

        add_skill_button = ctk.CTkButton(
            skills_header,
            text="+ Legg til",
            width=80,
            height=26,
            fg_color="transparent",
            hover_color=CARD_BG,
            text_color=ACCENT,
            command=lambda: self.add_skill(technology)
        )

        add_skill_button.pack(
            side="right"
        )

        skills = self.data["skills"].get(technology, {})

        if not skills:
            empty_label = ctk.CTkLabel(
                skills_card,
                text="Ingen ferdigheter ennå. Trykk «+ Legg til» for å lage din egen liste.",
                text_color=MUTED_TEXT
            )

            empty_label.pack(
                anchor="w",
                padx=16,
                pady=(0, 14)
            )

        for skill, level in skills.items():
            self.create_skill_row(
                skills_card,
                technology,
                skill,
                level
            )

        # Litt luft under siste ferdighet
        ctk.CTkFrame(
            skills_card,
            height=2,
            fg_color="transparent"
        ).pack(pady=(0, 10))

        # -------------------------
        # PROSJEKTER OG NOTATER
        # -------------------------

        bottom_row = ctk.CTkFrame(
            frame,
            fg_color="transparent"
        )

        bottom_row.pack(
            fill="x",
            padx=PAGE_PADDING,
            pady=6
        )

        bottom_row.grid_columnconfigure(
            (0, 1),
            weight=1,
            uniform="bottom"
        )

        self.create_technology_projects_card(
            bottom_row,
            technology
        )

        self.create_technology_notes_card(
            bottom_row,
            technology
        )

        delete_button = ctk.CTkButton(
            frame,
            text=f"Fjern {technology}",
            width=10,
            height=26,
            fg_color="transparent",
            hover_color=CARD_BG,
            text_color=MUTED_TEXT,
            font=ctk.CTkFont(size=12),
            command=lambda: self.delete_technology(technology)
        )

        delete_button.pack(
            anchor="w",
            padx=PAGE_PADDING - 8,
            pady=(10, 24)
        )

        self.refresh_technology_summary(technology)

        self.show_page("technology")

        # Start øverst på siden
        self.main_scroll_canvases["technology"].yview_moveto(0)

    def create_detail_card(self, parent):
        """Et hvitt kort med full bredde."""

        card = ctk.CTkFrame(
            parent,
            corner_radius=CARD_CORNER_RADIUS,
            fg_color=CARD_LIGHT,
            border_width=1,
            border_color=BORDER_COLOR
        )

        card.pack(
            fill="x",
            padx=PAGE_PADDING,
            pady=6
        )

        return card

    def create_skill_row(
        self,
        parent,
        technology,
        skill,
        level
    ):
        """Én ferdighet med fire nivåknapper."""

        row = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )

        row.pack(
            fill="x",
            padx=16,
            pady=3
        )

        skill_label = ctk.CTkLabel(
            row,
            text=skill,
            text_color=TEXT_COLOR,
            anchor="w"
        )

        skill_label.pack(
            side="left",
            fill="x",
            expand=True
        )

        # På skjermen står det "Lærer" for å spare plass,
        # men i data.json heter nivået "Under læring".
        level_buttons = ctk.CTkSegmentedButton(
            row,
            values=SKILL_BUTTON_LABELS,
            height=26,
            font=ctk.CTkFont(size=12),
            fg_color=CARD_BG,
            unselected_color=CARD_BG,
            unselected_hover_color=BORDER_COLOR,
            selected_color=ACCENT_HOVER,
            selected_hover_color=ACCENT_HOVER,
            text_color=TEXT_COLOR,
            command=lambda label: self.update_skill_level(
                technology,
                skill,
                SKILL_LEVELS[
                    SKILL_BUTTON_LABELS.index(label)
                ]
            )
        )

        level_buttons.set(
            SKILL_BUTTON_LABELS[
                SKILL_LEVELS.index(level)
            ]
        )

        level_buttons.pack(
            side="right"
        )

    def create_technology_projects_card(self, parent, technology):

        card = ctk.CTkFrame(
            parent,
            corner_radius=CARD_CORNER_RADIUS,
            fg_color=CARD_LIGHT,
            border_width=1,
            border_color=BORDER_COLOR
        )

        card.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 6)
        )

        title = ctk.CTkLabel(
            card,
            text="Prosjekter",
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(
                size=15,
                weight="bold"
            )
        )

        title.pack(
            anchor="w",
            padx=16,
            pady=(12, 4)
        )

        projects = self.get_projects_for_technology(technology)

        if not projects:
            empty_label = ctk.CTkLabel(
                card,
                text="Ingen prosjekter ennå.",
                text_color=MUTED_TEXT
            )

            empty_label.pack(
                anchor="w",
                padx=16,
                pady=(0, 12)
            )

            return

        for project in projects:

            row = ctk.CTkFrame(
                card,
                fg_color="transparent"
            )

            row.pack(
                fill="x",
                padx=16
            )

            name_label = ctk.CTkLabel(
                row,
                text=project["name"],
                text_color=TEXT_COLOR
            )

            name_label.pack(
                side="left"
            )

            time_label = ctk.CTkLabel(
                row,
                text=self.format_time(
                    self.get_project_time(project["name"])
                ),
                text_color=MUTED_TEXT
            )

            time_label.pack(
                side="right"
            )

        # Litt luft nederst i kortet
        ctk.CTkFrame(
            card,
            height=2,
            fg_color="transparent"
        ).pack(pady=(0, 8))

    def create_technology_notes_card(self, parent, technology):

        card = ctk.CTkFrame(
            parent,
            corner_radius=CARD_CORNER_RADIUS,
            fg_color=CARD_LIGHT,
            border_width=1,
            border_color=BORDER_COLOR
        )

        card.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(6, 0)
        )

        title = ctk.CTkLabel(
            card,
            text="Notater",
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(
                size=15,
                weight="bold"
            )
        )

        title.pack(
            anchor="w",
            padx=16,
            pady=(12, 4)
        )

        notes = []

        for note in self.data["notes"]:
            if note.get("technology") == technology:
                notes.append(note)

        if not notes:
            empty_label = ctk.CTkLabel(
                card,
                text="Ingen notater ennå.",
                text_color=MUTED_TEXT
            )

            empty_label.pack(
                anchor="w",
                padx=16,
                pady=(0, 12)
            )

            return

        # Nyeste først, maks fem
        notes.sort(
            key=lambda note: note.get("date", ""),
            reverse=True
        )

        for note in notes[:5]:

            row = ctk.CTkFrame(
                card,
                fg_color="transparent"
            )

            row.pack(
                fill="x",
                padx=16
            )

            title_label = ctk.CTkLabel(
                row,
                text=note.get("title", ""),
                text_color=TEXT_COLOR
            )

            title_label.pack(
                side="left"
            )

            date_label = ctk.CTkLabel(
                row,
                text=self.format_short_date(note.get("date")),
                text_color=MUTED_TEXT
            )

            date_label.pack(
                side="right"
            )

        # Litt luft nederst i kortet
        ctk.CTkFrame(
            card,
            height=2,
            fg_color="transparent"
        ).pack(pady=(0, 8))

    def get_technology_subtitle(self, technology):
        """F.eks. "4 t 5 min totalt · sist brukt i dag"."""

        text = (
            f"{self.format_time(self.get_technology_time(technology))}"
            f" totalt"
        )

        last_day = None

        for session in self.data["sessions"]:
            if session.get("technology") == technology:
                day = self.get_session_day(session)

                if day is not None and (
                    last_day is None or day > last_day
                ):
                    last_day = day

        if last_day is not None:
            text += (
                " · sist brukt "
                f"{self.format_day_heading(last_day).lower()}"
            )

        return text

    def refresh_technology_summary(self, technology):
        """Oppdaterer tallene og «Neste å lære»
        uten å lage hele siden på nytt."""

        skill_counts = self.get_skill_counts(technology)

        for level, label in self.technology_count_labels.items():
            label.configure(
                text=str(skill_counts[level])
            )

        self.technology_progress_bar.set(
            self.get_skill_progress(technology)
        )

        next_skill, level = self.get_next_skill(technology)

        if next_skill is None:
            self.next_skill_label.configure(
                text="Du er trygg på alt!"
            )
            hint = "Legg til flere ferdigheter når du er klar for mer."

        elif level == "Under læring":
            self.next_skill_label.configure(
                text=next_skill
            )
            hint = (
                "Du har startet på denne. Øv litt til, og sett den "
                "til «Kan bruke» når den sitter."
            )

        elif level == "Ikke startet":
            self.next_skill_label.configure(
                text=next_skill
            )
            hint = "Den neste på listen du ikke har startet på."

        else:
            self.next_skill_label.configure(
                text=next_skill
            )
            hint = "Du kan bruke den. Neste mål er «Trygg»."

        self.next_skill_hint_label.configure(
            text=hint
        )

    def get_next_skill(self, technology):
        """Finner hva du bør jobbe med nå:
        1. noe du holder på å lære,
        2. ellers noe du ikke har startet på,
        3. ellers noe du kan bruke, men ikke er trygg på.
        Gir (None, None) hvis alt er Trygg."""

        skills = self.data["skills"].get(technology, {})

        for wanted_level in (
            "Under læring",
            "Ikke startet",
            "Kan bruke"
        ):
            for skill, level in skills.items():
                if level == wanted_level:
                    return skill, level

        return None, None

    def start_timer_for(self, technology):
        """Velger teknologien i mini-timeren og starter den."""

        self.timer_technology_menu.set(technology)
        self.update_timer_project_options(technology)
        self.start_timer()

    def add_skill(self, technology):

        dialog = ctk.CTkInputDialog(
            text=f"Hvilken ferdighet vil du legge til i {technology}?",
            title="Ny ferdighet"
        )

        skill = dialog.get_input()

        if skill is None:
            return

        skill = skill.strip()

        if skill == "":
            return

        skills = self.data["skills"].setdefault(technology, {})

        if skill in skills:
            messagebox.showinfo(
                "Finnes allerede",
                f"«{skill}» finnes allerede i {technology}."
            )
            return

        skills[skill] = "Ikke startet"

        self.save_data()

        self.show_technology(technology)
        self.refresh_technology_list()
        self.refresh_home_page()

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

        self.refresh_technology_summary(technology)
        self.refresh_technology_list()
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

        page = self.create_main_scroll_area(
            "projects"
        )

        self.create_page_title(
            page,
            "Prosjekter",
            "Hold oversikt over det du bygger. Klikk på et prosjekt for å endre det."
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
            padx=PAGE_PADDING,
            pady=20
        )

        # Tavlen: tre kolonner ved siden av hverandre
        self.project_board_frame = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )

        self.project_board_frame.pack(
            fill="x",
            padx=PAGE_PADDING,
            pady=(0, 20)
        )

        self.project_board_frame.grid_columnconfigure(
            (0, 1, 2),
            weight=1,
            uniform="board"
        )

        self.refresh_project_list()

    def refresh_project_list(self):
        """Fordeler prosjektene i kolonner etter status."""

        for widget in self.project_board_frame.winfo_children():
            widget.destroy()

        # Hver kolonne har en overskrift og en liste
        # med statuser som hører hjemme i den.
        # "På pause" vises under Aktive, men nedtonet.
        columns = [
            ("Planlagt", ["Planlagt"]),
            ("Aktive", ["Aktivt", "På pause"]),
            ("Ferdig", ["Ferdig"])
        ]

        for column, (title, statuses) in enumerate(columns):

            # Finn prosjektene i denne kolonnen.
            # Vi tar med index, så vi vet hvilket
            # prosjekt som skal åpnes ved klikk.
            projects = []

            for index, project in enumerate(self.data["projects"]):
                if project.get("status", "Planlagt") in statuses:
                    projects.append((index, project))

            # Aktive prosjekter før de på pause
            projects.sort(
                key=lambda item: item[1].get("status") == "På pause"
            )

            self.create_project_column(
                column,
                title,
                projects
            )

    def create_project_column(self, column, title, projects):

        column_frame = ctk.CTkFrame(
            self.project_board_frame,
            corner_radius=CARD_CORNER_RADIUS,
            fg_color=CARD_BG
        )

        column_frame.grid(
            row=0,
            column=column,
            sticky="nsew",
            padx=(0 if column == 0 else 5, 0 if column == 2 else 5)
        )

        header = ctk.CTkFrame(
            column_frame,
            fg_color="transparent"
        )

        header.pack(
            fill="x",
            padx=12,
            pady=(10, 4)
        )

        title_label = ctk.CTkLabel(
            header,
            text=title,
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(
                size=14,
                weight="bold"
            )
        )

        title_label.pack(
            side="left"
        )

        count_label = ctk.CTkLabel(
            header,
            text=str(len(projects)),
            text_color=MUTED_TEXT
        )

        count_label.pack(
            side="right"
        )

        if not projects:
            empty_label = ctk.CTkLabel(
                column_frame,
                text="Ingen her ennå",
                text_color=MUTED_TEXT,
                font=ctk.CTkFont(size=12)
            )

            empty_label.pack(
                anchor="w",
                padx=12,
                pady=(0, 12)
            )

            return

        for index, project in projects:
            self.create_project_card(
                column_frame,
                index,
                project
            )

        # Luft under siste kort
        ctk.CTkFrame(
            column_frame,
            height=2,
            fg_color="transparent"
        ).pack(pady=(0, 6))

    def create_project_card(self, parent, index, project):
        """Ett prosjekt på tavlen. Klikk for å endre."""

        paused = project.get("status") == "På pause"

        card = ctk.CTkFrame(
            parent,
            corner_radius=10,
            fg_color=CARD_LIGHT,
            border_width=1,
            border_color=BORDER_COLOR
        )

        card.pack(
            fill="x",
            padx=8,
            pady=(0, 8)
        )

        name_label = ctk.CTkLabel(
            card,
            text=project["name"],
            text_color=MUTED_TEXT if paused else TEXT_COLOR,
            anchor="w",
            justify="left",
            wraplength=130,
            font=ctk.CTkFont(
                size=14,
                weight="bold"
            )
        )

        name_label.pack(
            anchor="w",
            padx=12,
            pady=(10, 0)
        )

        # Tekstene som skal brytes når kortet er smalt
        wrapping_labels = [name_label]

        if paused:
            paused_label = ctk.CTkLabel(
                card,
                text="På pause",
                text_color=MUTED_TEXT,
                height=16,
                font=ctk.CTkFont(
                    size=11,
                    weight="bold"
                )
            )

            paused_label.pack(
                anchor="w",
                padx=12
            )

        technologies = project.get("technologies", [])

        if technologies:
            technology_label = ctk.CTkLabel(
                card,
                text=" · ".join(technologies),
                text_color=ACCENT,
                anchor="w",
                justify="left",
                wraplength=130,
                font=ctk.CTkFont(
                    size=12,
                    weight="bold"
                )
            )

            technology_label.pack(
                anchor="w",
                padx=12
            )

            wrapping_labels.append(technology_label)

        # Når du sist jobbet med prosjektet, og hvor lenge
        meta_label = ctk.CTkLabel(
            card,
            text=(
                f"{self.get_project_last_worked(project['name'])}"
                f" · {self.format_time(self.get_project_time(project['name']))}"
            ),
            text_color=MUTED_TEXT,
            anchor="w",
            justify="left",
            wraplength=130,
            font=ctk.CTkFont(size=12)
        )

        meta_label.pack(
            anchor="w",
            padx=12,
            pady=(2, 10)
        )

        wrapping_labels.append(meta_label)

        # Når kortet endrer bredde (f.eks. når du gjør
        # vinduet smalere), bryter vi teksten på nytt
        # så den ikke blir kuttet.
        def update_wrapping(event):
            for label in wrapping_labels:
                label.configure(
                    wraplength=max(60, event.width - 30)
                )

        card.bind(
            "<Configure>",
            update_wrapping,
            add="+"
        )

        self.make_clickable(
            card,
            lambda: self.open_project_window(index)
        )

    def get_project_last_worked(self, project_name):
        """F.eks. "Sist: i dag" eller "Ikke startet"."""

        last_day = None

        for session in self.data["sessions"]:
            if session.get("project") == project_name:
                day = self.get_session_day(session)

                if day is not None and (
                    last_day is None or day > last_day
                ):
                    last_day = day

        if last_day is None:
            return "Ikke startet"

        days_ago = (date.today() - last_day).days

        if days_ago == 0:
            return "Sist: i dag"

        if days_ago == 1:
            return "Sist: i går"

        if days_ago < 14:
            return f"Sist: {days_ago} dager siden"

        if days_ago < 60:
            return f"Sist: {days_ago // 7} uker siden"

        return f"Sist: {self.format_short_date(last_day.isoformat())}"

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
            "420x620"
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

        # Slett-knappen ligger her, inne i prosjektet,
        # i stedet for på hvert kort på tavlen.
        if editing:
            delete_button = ctk.CTkButton(
                self.project_window,
                text="Slett prosjekt",
                width=10,
                height=24,
                fg_color="transparent",
                hover_color=CARD_BG,
                text_color=MUTED_TEXT,
                font=ctk.CTkFont(size=12),
                command=lambda: self.delete_project_from_window(
                    project_index
                )
            )

            delete_button.pack()


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

                for note in self.data["notes"]:
                    if note.get("project") == old_name:
                        note["project"] = name

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


    def delete_project_from_window(self, project_index):
        """Lukker prosjektvinduet og sletter prosjektet."""

        self.project_window.destroy()
        self.delete_project(project_index)

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

        for note in self.data["notes"]:
            if note.get("project") == project_name:
                note["project"] = None

        self.save_data()

        self.refresh_project_list()
        self.refresh_home_page()
        self.refresh_timer_options()


    # -------------------------
    # TIMER (nederst i menyen)
    # -------------------------

    def create_sidebar_timer(self):
        """Mini-timeren nederst i menyen.
        Den er synlig uansett hvilken side du står på."""

        card = ctk.CTkFrame(
            self.sidebar,
            corner_radius=CARD_CORNER_RADIUS,
            fg_color=CARD_LIGHT,
            border_width=1,
            border_color=BORDER_COLOR
        )

        # side="bottom" legger kortet nederst i menyen
        card.pack(
            side="bottom",
            fill="x",
            padx=12,
            pady=12
        )

        # Viser "Timer", "● Pågår" eller "Pause"
        self.timer_status_label = ctk.CTkLabel(
            card,
            text="Timer",
            height=18,
            text_color=MUTED_TEXT,
            font=ctk.CTkFont(
                size=12,
                weight="bold"
            )
        )

        self.timer_status_label.pack(
            anchor="w",
            padx=12,
            pady=(10, 0)
        )

        self.timer_label = ctk.CTkLabel(
            card,
            text="00:00:00",
            height=30,
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(
                size=24,
                weight="bold"
            )
        )

        self.timer_label.pack(
            anchor="w",
            padx=12
        )

        # De to menyene skal se like ut, så vi
        # samler innstillingene i én ordbok og
        # gir den til begge med **.
        menu_style = {
            "height": 26,
            "font": ctk.CTkFont(size=12),
            "dropdown_font": ctk.CTkFont(size=12),
            "fg_color": CARD_BG,
            "button_color": CARD_BG,
            "button_hover_color": BORDER_COLOR,
            "text_color": TEXT_COLOR,
            "dynamic_resizing": False,
            "width": 120
        }

        self.timer_technology_menu = ctk.CTkOptionMenu(
            card,
            values=(
                self.data["technologies"]
                or ["Ingen teknologi"]
            ),
            command=self.update_timer_project_options,
            **menu_style
        )

        self.timer_technology_menu.pack(
            fill="x",
            padx=12,
            pady=(6, 4)
        )

        self.timer_project_menu = ctk.CTkOptionMenu(
            card,
            values=["Ingen prosjekt"],
            **menu_style
        )

        self.timer_project_menu.pack(
            fill="x",
            padx=12
        )

        self.update_timer_project_options(
            self.timer_technology_menu.get()
        )

        button_row = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        button_row.pack(
            fill="x",
            padx=12,
            pady=(8, 0)
        )

        button_row.grid_columnconfigure(
            (0, 1),
            weight=1,
            uniform="timer"
        )

        # Én knapp som bytter mellom
        # Start, Pause og Fortsett.
        self.start_timer_button = ctk.CTkButton(
            button_row,
            text="Start",
            width=60,
            height=28,
            command=self.toggle_timer,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER
        )

        self.start_timer_button.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 3)
        )

        self.save_timer_button = ctk.CTkButton(
            button_row,
            text="Lagre",
            width=60,
            height=28,
            command=self.save_timer,
            fg_color="transparent",
            hover_color=CARD_BG,
            text_color=ACCENT,
            border_width=1,
            border_color=ACCENT
        )

        self.save_timer_button.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(3, 0)
        )

        self.discard_timer_button = ctk.CTkButton(
            card,
            text="Kast økt",
            height=22,
            command=self.discard_timer,
            fg_color="transparent",
            hover_color=CARD_BG,
            text_color=MUTED_TEXT,
            font=ctk.CTkFont(size=11)
        )

        self.discard_timer_button.pack(
            pady=(4, 8)
        )

        self.update_timer_display()

    def update_timer_project_options(
        self,
        technology
    ):
        """Viser bare prosjekter som bruker valgt teknologi."""

        project_names = [
            "Ingen prosjekt"
        ]

        if technology != "Ingen teknologi":

            for project in self.data[
                "projects"
            ]:

                technologies = project.get(
                    "technologies",
                    []
                )

                if technology in technologies:

                    project_names.append(
                        project["name"]
                    )

        current_project = (
            self.timer_project_menu.get()
        )

        self.timer_project_menu.configure(
            values=project_names
        )

        # Behold valgt prosjekt dersom det fortsatt
        # passer med teknologien.
        if current_project in project_names:

            self.timer_project_menu.set(
                current_project
            )

        else:

            self.timer_project_menu.set(
                "Ingen prosjekt"
            )

    def start_timer(self):

        if self.timer_running:
            return

        self.timer_started_at = time.monotonic()
        self.timer_running = True

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

    def toggle_timer(self):
        """Brukes av Start/Pause-knappen."""

        if self.timer_running:
            self.pause_timer()
        else:
            self.start_timer()

    def get_timer_seconds(self):

        total = self.timer_elapsed_seconds

        if self.timer_running:

            total += (
                time.monotonic()
                - self.timer_started_at
            )

        return int(total)

    def update_timer_display(self):
        """Oppdaterer mini-timeren fem ganger i sekundet."""

        total_seconds = (
            self.get_timer_seconds()
        )

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        self.set_text_if_changed(
            self.timer_label,
            f"{hours:02}:{minutes:02}:{seconds:02}"
        )

        if self.timer_running:
            button_text = "Pause"
            status_text = "● Pågår"
            status_color = ACCENT

        elif total_seconds > 0:
            button_text = "Fortsett"
            status_text = "Pause"
            status_color = MUTED_TEXT

        else:
            button_text = "Start"
            status_text = "Timer"
            status_color = MUTED_TEXT

        self.set_text_if_changed(
            self.start_timer_button,
            button_text
        )

        if (
            self.timer_status_label.cget("text")
            != status_text
        ):
            self.timer_status_label.configure(
                text=status_text,
                text_color=status_color
            )

        self.after(
            200,
            self.update_timer_display
        )

    def set_text_if_changed(self, widget, text):
        """Endrer teksten bare hvis den er ny.
        Ellers tegnes knapper og tekster på nytt
        fem ganger i sekundet helt unødvendig."""

        if widget.cget("text") != text:
            widget.configure(text=text)

    def save_timer(self):
        """Pauser timeren og åpner vinduet der
        du kan skrive hva du jobbet med."""

        # Ta med tiden helt frem til Lagre ble trykket.
        self.pause_timer()

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

        self.open_save_session_window(
            technology,
            project,
            total_seconds
        )

    def open_save_session_window(
        self,
        technology,
        project,
        total_seconds
    ):
        """Vinduet som spør hva du jobbet med."""

        # Ikke åpne to slike vinduer samtidig
        if (
            hasattr(self, "save_session_window")
            and self.save_session_window.winfo_exists()
        ):
            self.save_session_window.focus()
            return

        window = ctk.CTkToplevel(self)
        window.title("Lagre økt")
        window.geometry("420x370")
        window.resizable(False, False)
        window.configure(fg_color=APP_BG)
        window.transient(self)

        self.save_session_window = window

        # grab_set gjør at du må svare i dette vinduet
        # før du kan bruke resten av appen. Vi venter
        # litt, fordi vinduet må vises på skjermen først.
        def grab():
            try:
                window.grab_set()
            except tk.TclError:
                pass

        window.after(100, grab)

        small_title = ctk.CTkLabel(
            window,
            text="Økt ferdig",
            text_color=MUTED_TEXT
        )

        small_title.pack(
            anchor="w",
            padx=25,
            pady=(22, 0)
        )

        title = ctk.CTkLabel(
            window,
            text=(
                f"{self.format_duration(total_seconds)} "
                f"med {technology}"
            ),
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(
                size=22,
                weight="bold"
            )
        )

        title.pack(
            anchor="w",
            padx=25
        )

        if project:
            project_label = ctk.CTkLabel(
                window,
                text=f"Prosjekt: {project}",
                text_color=MUTED_TEXT
            )

            project_label.pack(
                anchor="w",
                padx=25
            )

        question = ctk.CTkLabel(
            window,
            text="Hva jobbet du med? (valgfritt)",
            text_color=TEXT_COLOR
        )

        question.pack(
            anchor="w",
            padx=25,
            pady=(16, 4)
        )

        self.session_description_box = ctk.CTkTextbox(
            window,
            height=120,
            corner_radius=8,
            border_width=1,
            border_color=BORDER_COLOR,
            fg_color=CARD_LIGHT,
            text_color=TEXT_COLOR,
            wrap="word"
        )

        self.session_description_box.pack(
            fill="x",
            padx=25
        )

        self.session_as_note_checkbox = ctk.CTkCheckBox(
            window,
            text="Lagre også som notat",
            text_color=TEXT_COLOR,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            border_color=BORDER_COLOR
        )

        self.session_as_note_checkbox.pack(
            anchor="w",
            padx=25,
            pady=(12, 0)
        )

        button_row = ctk.CTkFrame(
            window,
            fg_color="transparent"
        )

        button_row.pack(
            fill="x",
            padx=25,
            pady=(20, 20),
            side="bottom"
        )

        save_button = ctk.CTkButton(
            button_row,
            text="Lagre økt",
            width=120,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=lambda: self.finish_save_session(
                technology,
                project,
                total_seconds
            )
        )

        save_button.pack(
            side="right"
        )

        cancel_button = ctk.CTkButton(
            button_row,
            text="Avbryt",
            width=100,
            fg_color="transparent",
            hover_color=CARD_BG,
            text_color=TEXT_COLOR,
            border_width=1,
            border_color=BORDER_COLOR,
            command=window.destroy
        )

        cancel_button.pack(
            side="right",
            padx=(0, 8)
        )

        self.session_description_box.focus()

    def finish_save_session(
        self,
        technology,
        project,
        total_seconds
    ):
        """Lagrer økten (og eventuelt notatet)
        når du trykker «Lagre økt»."""

        # "1.0" betyr linje 1, tegn 0, altså starten.
        # "end" betyr slutten av teksten.
        description = (
            self.session_description_box
            .get("1.0", "end")
            .strip()
        )

        save_as_note = (
            self.session_as_note_checkbox.get() == 1
        )

        now = datetime.now()

        session = {
            "date": now.isoformat(
                timespec="seconds"
            ),
            "technology": technology,
            "project": project,
            "seconds": total_seconds
        }

        if description:
            session["description"] = description

        self.data["sessions"].append(session)
        self.data["total_seconds"] += total_seconds

        if save_as_note and description:

            # Første linje blir tittelen, maks 40 tegn
            first_line = description.splitlines()[0]

            if len(first_line) > 40:
                first_line = first_line[:40].rstrip() + "…"

            self.data["notes"].append({
                "title": first_line,
                "text": description,
                "technology": technology,
                "project": project,
                "date": now.isoformat(
                    timespec="minutes"
                )
            })

        self.save_data()

        self.save_session_window.destroy()

        self.reset_timer()

        self.refresh_home_page()
        self.refresh_stats_page()
        self.refresh_notes_list()
        self.refresh_project_list()
        self.refresh_technology_list()

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

    # -------------------------
    # STATISTIKK
    # -------------------------

    def create_stats_page(self):

        page = self.create_main_scroll_area(
            "stats"
        )

        self.create_page_title(
            page,
            "Statistikk",
            "Slik har du brukt tiden din."
        )

        # Tre små tall øverst
        summary_row = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )

        summary_row.pack(
            fill="x",
            padx=PAGE_PADDING,
            pady=(20, 12)
        )

        summary_row.grid_columnconfigure(
            (0, 1, 2),
            weight=1,
            uniform="summary"
        )

        self.stats_total_label = self.create_stats_number(
            summary_row,
            0,
            "Siste 12 uker"
        )

        self.stats_days_label = self.create_stats_number(
            summary_row,
            1,
            "Dager du kodet"
        )

        self.stats_average_label = self.create_stats_number(
            summary_row,
            2,
            "Snitt per kodedag"
        )

        # Aktivitetskalender
        activity_card = self.create_stats_card(
            page,
            "Aktivitet siste 12 uker"
        )

        # Kalenderen tegnes på et Canvas,
        # et "lerret" vi kan tegne firkanter på.
        self.heatmap_canvas = tk.Canvas(
            activity_card,
            height=170,
            bg=CARD_LIGHT,
            highlightthickness=0,
            borderwidth=0
        )

        self.heatmap_canvas.pack(
            anchor="w",
            padx=16,
            pady=(0, 12)
        )

        # Tid per teknologi
        technology_card = self.create_stats_card(
            page,
            "Tid per teknologi"
        )

        self.stats_technology_frame = ctk.CTkFrame(
            technology_card,
            fg_color="transparent"
        )

        self.stats_technology_frame.pack(
            fill="x",
            padx=16,
            pady=(0, 14)
        )

        self.stats_technology_frame.grid_columnconfigure(
            1,
            weight=1
        )

        # Økter
        sessions_title = ctk.CTkLabel(
            page,
            text="Økter",
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(
                size=18,
                weight="bold"
            )
        )

        sessions_title.pack(
            anchor="w",
            padx=PAGE_PADDING,
            pady=(14, 4)
        )

        self.session_history_frame = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )

        self.session_history_frame.pack(
            fill="x",
            padx=PAGE_PADDING,
            pady=(0, 20)
        )

        self.refresh_stats_page()

    def create_stats_number(self, parent, column, title):
        """Et lite kort med en overskrift og et stort tall."""

        card = ctk.CTkFrame(
            parent,
            corner_radius=CARD_CORNER_RADIUS,
            fg_color=CARD_LIGHT,
            border_width=1,
            border_color=BORDER_COLOR
        )

        card.grid(
            row=0,
            column=column,
            sticky="nsew",
            padx=(0 if column == 0 else 4, 0 if column == 2 else 4)
        )

        title_label = ctk.CTkLabel(
            card,
            text=title,
            text_color=MUTED_TEXT
        )

        title_label.pack(
            anchor="w",
            padx=14,
            pady=(10, 0)
        )

        value_label = ctk.CTkLabel(
            card,
            text="0 min",
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            )
        )

        value_label.pack(
            anchor="w",
            padx=14,
            pady=(0, 10)
        )

        return value_label

    def create_stats_card(self, parent, title):
        """Et kort med overskrift. Innholdet legges
        inn i kortet etterpå."""

        card = ctk.CTkFrame(
            parent,
            corner_radius=CARD_CORNER_RADIUS,
            fg_color=CARD_LIGHT,
            border_width=1,
            border_color=BORDER_COLOR
        )

        card.pack(
            fill="x",
            padx=PAGE_PADDING,
            pady=6
        )

        title_label = ctk.CTkLabel(
            card,
            text=title,
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(
                size=15,
                weight="bold"
            )
        )

        title_label.pack(
            anchor="w",
            padx=16,
            pady=(12, 6)
        )

        return card

    def refresh_stats_page(self):

        # -------------------------
        # TALLENE ØVERST
        # -------------------------

        daily_seconds = self.get_daily_seconds(12 * 7)

        total_seconds = sum(daily_seconds.values())

        # Teller dagene der du har logget mer enn 0 sekunder
        coding_days = 0

        for seconds in daily_seconds.values():
            if seconds > 0:
                coding_days += 1

        if coding_days > 0:
            average = total_seconds // coding_days
        else:
            average = 0

        self.stats_total_label.configure(
            text=self.format_time(total_seconds)
        )

        self.stats_days_label.configure(
            text=str(coding_days)
        )

        self.stats_average_label.configure(
            text=self.format_time(average)
        )

        self.draw_heatmap(daily_seconds)
        self.refresh_stats_technologies()
        self.refresh_session_history()

    def draw_heatmap(self, daily_seconds):
        """Tegner én rute per dag, som på GitHub.
        Kolonnene er uker, radene er ukedager."""

        canvas = self.heatmap_canvas
        canvas.delete("all")

        cell = 15
        gap = 4
        left = 28
        top = 20

        # Fem nyanser fra "ingenting" til "mye".
        # mix_colors blander bakgrunnsfargen og
        # hovedfargen, så kalenderen følger
        # fargene i styles.py.
        shades = [
            self.mix_colors(CARD_BG, ACCENT, amount)
            for amount in (0, 0.3, 0.55, 0.8, 1)
        ]

        today = date.today()

        # Første dag i kalenderen er mandagen
        # for 11 uker siden.
        this_monday = today - timedelta(days=today.weekday())
        first_day = this_monday - timedelta(weeks=11)

        # Ukedager til venstre
        for row, letter in ((0, "M"), (2, "O"), (4, "F")):
            canvas.create_text(
                left - 10,
                top + row * (cell + gap) + cell / 2,
                text=letter,
                fill=MUTED_TEXT,
                font=("TkDefaultFont", 10)
            )

        last_month = None

        day = first_day

        while day <= today:

            column = (day - first_day).days // 7
            row = day.weekday()

            x = left + column * (cell + gap)
            y = top + row * (cell + gap)

            seconds = daily_seconds.get(day, 0)

            if seconds == 0:
                level = 0
            elif seconds < 30 * 60:
                level = 1
            elif seconds < 60 * 60:
                level = 2
            elif seconds < 2 * 60 * 60:
                level = 3
            else:
                level = 4

            canvas.create_rectangle(
                x,
                y,
                x + cell,
                y + cell,
                fill=shades[level],
                outline=ACCENT if day == today else ""
            )

            # Månedsnavn over første uke i hver måned
            if row == 0 and day.month != last_month:
                canvas.create_text(
                    x,
                    top - 10,
                    text=MONTHS[day.month - 1][:3],
                    anchor="w",
                    fill=MUTED_TEXT,
                    font=("TkDefaultFont", 10)
                )
                last_month = day.month

            day += timedelta(days=1)

        # Forklaring under kalenderen
        legend_y = top + 7 * (cell + gap) + 6

        canvas.create_text(
            left,
            legend_y + cell / 2,
            text="Mindre",
            anchor="w",
            fill=MUTED_TEXT,
            font=("TkDefaultFont", 10)
        )

        for index, shade in enumerate(shades):
            x = left + 58 + index * (cell + 3)
            canvas.create_rectangle(
                x,
                legend_y,
                x + cell,
                legend_y + cell,
                fill=shade,
                outline=""
            )

        canvas.create_text(
            left + 58 + 5 * (cell + 3) + 4,
            legend_y + cell / 2,
            text="Mer",
            anchor="w",
            fill=MUTED_TEXT,
            font=("TkDefaultFont", 10)
        )

        canvas.configure(
            width=left + 12 * (cell + gap),
            height=legend_y + cell + 4
        )

    def mix_colors(self, color1, color2, amount):
        """Blander to farger. amount=0 gir color1,
        amount=1 gir color2, 0.5 gir midt imellom."""

        # "#3F7A5A" -> (63, 122, 90)
        red1 = int(color1[1:3], 16)
        green1 = int(color1[3:5], 16)
        blue1 = int(color1[5:7], 16)

        red2 = int(color2[1:3], 16)
        green2 = int(color2[3:5], 16)
        blue2 = int(color2[5:7], 16)

        red = round(red1 + (red2 - red1) * amount)
        green = round(green1 + (green2 - green1) * amount)
        blue = round(blue1 + (blue2 - blue1) * amount)

        return f"#{red:02X}{green:02X}{blue:02X}"

    def refresh_stats_technologies(self):
        """Én rad per teknologi, med lengst tid øverst."""

        frame = self.stats_technology_frame

        for widget in frame.winfo_children():
            widget.destroy()

        # Ta med teknologier fra øktene også,
        # i tilfelle en teknologi er slettet
        # men fortsatt har gamle økter.
        technology_seconds = {}

        for session in self.data["sessions"]:
            technology = session.get(
                "technology",
                "Ukjent teknologi"
            )

            technology_seconds[technology] = (
                technology_seconds.get(technology, 0)
                + session.get("seconds", 0)
            )

        if not technology_seconds:
            empty_label = ctk.CTkLabel(
                frame,
                text="Ingen økter ennå.",
                text_color=MUTED_TEXT
            )

            empty_label.grid(
                row=0,
                column=0,
                sticky="w"
            )

            return

        # sorted med key= sorterer etter tiden,
        # og reverse=True gir størst først.
        sorted_technologies = sorted(
            technology_seconds.items(),
            key=lambda item: item[1],
            reverse=True
        )

        most_seconds = sorted_technologies[0][1] or 1

        for row, (technology, seconds) in enumerate(
            sorted_technologies
        ):

            name_label = ctk.CTkLabel(
                frame,
                text=technology,
                text_color=TEXT_COLOR,
                width=100,
                anchor="w"
            )

            name_label.grid(
                row=row,
                column=0,
                sticky="w",
                pady=2
            )

            bar = ctk.CTkProgressBar(
                frame,
                height=10,
                progress_color=ACCENT,
                fg_color=CARD_BG
            )

            bar.grid(
                row=row,
                column=1,
                sticky="ew",
                padx=10
            )

            bar.set(seconds / most_seconds)

            time_label = ctk.CTkLabel(
                frame,
                text=self.format_time(seconds),
                text_color=MUTED_TEXT,
                width=80,
                anchor="e"
            )

            time_label.grid(
                row=row,
                column=2,
                sticky="e"
            )

    def refresh_session_history(self):
        """Viser øktene, nyeste først, gruppert per dag."""

        frame = self.session_history_frame

        for widget in frame.winfo_children():
            widget.destroy()

        sessions = self.data["sessions"]

        if not sessions:
            empty_label = ctk.CTkLabel(
                frame,
                text="Ingen registrerte økter ennå.",
                text_color=MUTED_TEXT
            )

            empty_label.pack(
                anchor="w"
            )

            return

        # Vi trenger plasseringen (index) til hver økt
        # for å kunne slette den, så vi lager en liste
        # med (index, økt) og sorterer den etter dato.
        indexed_sessions = list(enumerate(sessions))

        indexed_sessions.sort(
            key=lambda item: item[1].get("date", ""),
            reverse=True
        )

        max_sessions = 60

        last_day = None

        for index, session in indexed_sessions[:max_sessions]:

            day = self.get_session_day(session)

            # Ny overskrift hver gang dagen endrer seg
            if day != last_day:
                heading = ctk.CTkLabel(
                    frame,
                    text=self.format_day_heading(day).upper(),
                    text_color=MUTED_TEXT,
                    font=ctk.CTkFont(
                        size=11,
                        weight="bold"
                    )
                )

                heading.pack(
                    anchor="w",
                    pady=(10, 2)
                )

                last_day = day

            self.create_session_row(
                index,
                session
            )

        if len(sessions) > max_sessions:
            more_label = ctk.CTkLabel(
                frame,
                text=f"Viser de {max_sessions} siste øktene.",
                text_color=MUTED_TEXT
            )

            more_label.pack(
                anchor="w",
                pady=(8, 0)
            )

    def create_session_row(self, index, session):
        """Én økt: klokkeslett, hva, beskrivelse og tid."""

        row = ctk.CTkFrame(
            self.session_history_frame,
            corner_radius=8,
            fg_color=CARD_LIGHT,
            border_width=1,
            border_color=BORDER_COLOR
        )

        row.pack(
            fill="x",
            pady=3
        )

        row.grid_columnconfigure(
            1,
            weight=1
        )

        try:
            clock = datetime.fromisoformat(
                session["date"]
            ).strftime("%H:%M")
        except (KeyError, TypeError, ValueError):
            clock = ""

        clock_label = ctk.CTkLabel(
            row,
            text=clock,
            text_color=MUTED_TEXT,
            width=50,
            anchor="w"
        )

        clock_label.grid(
            row=0,
            column=0,
            sticky="nw",
            padx=(14, 0),
            pady=8
        )

        technology = session.get(
            "technology",
            "Ukjent teknologi"
        )

        project = session.get("project")

        if project:
            title_text = f"{technology} · {project}"
        else:
            title_text = technology

        text_frame = ctk.CTkFrame(
            row,
            fg_color="transparent"
        )

        text_frame.grid(
            row=0,
            column=1,
            sticky="ew",
            pady=6
        )

        title_label = ctk.CTkLabel(
            text_frame,
            text=title_text,
            text_color=TEXT_COLOR,
            anchor="w",
            font=ctk.CTkFont(
                weight="bold"
            )
        )

        title_label.pack(
            anchor="w"
        )

        description = session.get("description")

        if description:
            description_label = ctk.CTkLabel(
                text_frame,
                text=description,
                text_color=MUTED_TEXT,
                anchor="w",
                justify="left",
                wraplength=320
            )

            description_label.pack(
                anchor="w"
            )

        duration_label = ctk.CTkLabel(
            row,
            text=self.format_duration(
                session.get("seconds", 0)
            ),
            text_color=TEXT_COLOR
        )

        duration_label.grid(
            row=0,
            column=2,
            sticky="ne",
            padx=8,
            pady=8
        )

        delete_button = ctk.CTkButton(
            row,
            text="Slett",
            width=44,
            height=24,
            fg_color="transparent",
            hover_color=CARD_BG,
            text_color=MUTED_TEXT,
            font=ctk.CTkFont(size=11),
            command=lambda: self.delete_session(index)
        )

        delete_button.grid(
            row=0,
            column=3,
            sticky="ne",
            padx=(0, 8),
            pady=8
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
                f"{self.format_duration(total_seconds)}"
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
        self.refresh_stats_page()
        self.refresh_home_page()
        self.refresh_project_list()
        self.refresh_technology_list()

    # -------------------------
    # NOTATER
    # -------------------------

    def create_notes_page(self):

        page = self.create_main_scroll_area(
            "notes"
        )

        header = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )

        header.pack(
            fill="x",
            padx=PAGE_PADDING,
            pady=(35, 0)
        )

        title = ctk.CTkLabel(
            header,
            text="Notater",
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(
                size=26,
                weight="bold"
            )
        )

        title.pack(
            side="left"
        )

        new_button = ctk.CTkButton(
            header,
            text="+ Nytt notat",
            width=110,
            command=lambda: self.open_note_window(),
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER
        )

        new_button.pack(
            side="right"
        )

        # -------------------------
        # SØK OG FILTER
        # -------------------------

        filter_row = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )

        filter_row.pack(
            fill="x",
            padx=PAGE_PADDING,
            pady=(16, 10)
        )

        self.note_search_entry = ctk.CTkEntry(
            filter_row,
            placeholder_text="Søk i notater …",
            fg_color=CARD_LIGHT,
            border_color=BORDER_COLOR,
            text_color=TEXT_COLOR
        )

        self.note_search_entry.pack(
            side="left",
            fill="x",
            expand=True
        )

        # <KeyRelease> skjer hver gang du slipper en tast,
        # så listen oppdateres mens du skriver.
        self.note_search_entry.bind(
            "<KeyRelease>",
            lambda event: self.refresh_notes_list()
        )

        self.note_filter_menu = ctk.CTkOptionMenu(
            filter_row,
            values=["Alle teknologier"],
            width=150,
            fg_color=CARD_BG,
            button_color=CARD_BG,
            button_hover_color=BORDER_COLOR,
            text_color=TEXT_COLOR,
            command=lambda value: self.refresh_notes_list()
        )

        self.note_filter_menu.pack(
            side="right",
            padx=(8, 0)
        )

        # -------------------------
        # LISTE OG NOTAT
        # -------------------------

        panes = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )

        panes.pack(
            fill="x",
            padx=PAGE_PADDING,
            pady=(0, 20)
        )

        # Listen til venstre er smalere enn notatet
        panes.grid_columnconfigure(0, weight=2, uniform="notes")
        panes.grid_columnconfigure(1, weight=3, uniform="notes")

        self.notes_list_frame = ctk.CTkFrame(
            panes,
            corner_radius=CARD_CORNER_RADIUS,
            fg_color=CARD_LIGHT,
            border_width=1,
            border_color=BORDER_COLOR
        )

        self.notes_list_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 6)
        )

        self.note_detail_frame = ctk.CTkFrame(
            panes,
            corner_radius=CARD_CORNER_RADIUS,
            fg_color=CARD_LIGHT,
            border_width=1,
            border_color=BORDER_COLOR
        )

        self.note_detail_frame.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(6, 0)
        )

        # Hvilket notat som vises til høyre
        self.selected_note_index = None

        # Tekster som skal brytes etter hvor bred
        # listen og notatet er
        self.note_list_labels = []
        self.note_detail_labels = []

        self.notes_list_frame.bind(
            "<Configure>",
            lambda event: self.wrap_labels(
                self.note_list_labels,
                event.width - 40
            ),
            add="+"
        )

        self.note_detail_frame.bind(
            "<Configure>",
            lambda event: self.wrap_labels(
                self.note_detail_labels,
                event.width - 50
            ),
            add="+"
        )

        self.refresh_notes_list()

    def get_filtered_notes(self):
        """Gir notatene som passer med søket og filteret,
        nyeste først, som en liste med (index, notat)."""

        search = self.note_search_entry.get().strip().lower()
        wanted_technology = self.note_filter_menu.get()

        result = []

        for index, note in enumerate(self.data["notes"]):

            if (
                wanted_technology != "Alle teknologier"
                and note.get("technology") != wanted_technology
            ):
                continue

            # Søk i tittel, tekst, teknologi og prosjekt.
            # lower() gjør at store og små bokstaver
            # ikke spiller noen rolle.
            searchable = " ".join([
                note.get("title", ""),
                note.get("text", ""),
                note.get("technology") or "",
                note.get("project") or ""
            ]).lower()

            if search and search not in searchable:
                continue

            result.append((index, note))

        result.sort(
            key=lambda item: item[1].get("date", ""),
            reverse=True
        )

        return result

    def refresh_notes_list(self):

        # Filteret skal vise teknologiene som faktisk
        # finnes i notatene
        technologies = []

        for note in self.data["notes"]:
            technology = note.get("technology")

            if technology and technology not in technologies:
                technologies.append(technology)

        self.note_filter_menu.configure(
            values=["Alle teknologier"] + technologies
        )

        if self.note_filter_menu.get() not in (
            ["Alle teknologier"] + technologies
        ):
            self.note_filter_menu.set("Alle teknologier")

        for widget in self.notes_list_frame.winfo_children():
            widget.destroy()

        self.note_list_labels = []

        notes = self.get_filtered_notes()

        if not notes:
            if self.data["notes"]:
                empty_text = "Ingen notater passer med søket."
            else:
                empty_text = "Ingen notater ennå."

            empty_label = ctk.CTkLabel(
                self.notes_list_frame,
                text=empty_text,
                text_color=MUTED_TEXT
            )

            empty_label.pack(
                anchor="w",
                padx=14,
                pady=14
            )

            self.selected_note_index = None
            self.show_note_detail()
            return

        # Hvis notatet som var valgt ikke lenger er
        # med i listen, velger vi det nyeste.
        visible_indexes = [index for index, note in notes]

        if self.selected_note_index not in visible_indexes:
            self.selected_note_index = visible_indexes[0]

        for index, note in notes:
            self.create_note_list_item(index, note)

        self.wrap_labels(
            self.note_list_labels,
            self.notes_list_frame.winfo_width() - 40
        )

        self.show_note_detail()

    def create_note_list_item(self, index, note):

        selected = index == self.selected_note_index

        item = ctk.CTkFrame(
            self.notes_list_frame,
            corner_radius=8,
            fg_color=CARD_BG if selected else "transparent"
        )

        item.pack(
            fill="x",
            padx=6,
            pady=(6, 0)
        )

        title_label = ctk.CTkLabel(
            item,
            text=note.get("title", ""),
            text_color=TEXT_COLOR,
            anchor="w",
            justify="left",
            wraplength=170,
            font=ctk.CTkFont(weight="bold")
        )

        title_label.pack(
            anchor="w",
            padx=10,
            pady=(6, 0)
        )

        self.note_list_labels.append(title_label)

        # Første linje av teksten, forkortet
        preview = note.get("text", "").strip().splitlines()

        if preview:
            preview_text = preview[0]

            if len(preview_text) > 40:
                preview_text = preview_text[:40].rstrip() + "…"

            preview_label = ctk.CTkLabel(
                item,
                text=preview_text,
                text_color=MUTED_TEXT,
                anchor="w",
                height=18,
                font=ctk.CTkFont(size=12)
            )

            preview_label.pack(
                anchor="w",
                padx=10
            )

        meta_parts = []

        if note.get("technology"):
            meta_parts.append(note["technology"])

        meta_parts.append(
            self.format_short_date(note.get("date"))
        )

        meta_label = ctk.CTkLabel(
            item,
            text=" · ".join(meta_parts),
            text_color=ACCENT,
            anchor="w",
            height=18,
            font=ctk.CTkFont(size=11, weight="bold")
        )

        meta_label.pack(
            anchor="w",
            padx=10,
            pady=(0, 6)
        )

        self.make_clickable(
            item,
            lambda: self.select_note(index)
        )

    def select_note(self, index):

        self.selected_note_index = index
        self.refresh_notes_list()

    def show_note_detail(self):
        """Viser det valgte notatet til høyre."""

        frame = self.note_detail_frame

        for widget in frame.winfo_children():
            widget.destroy()

        self.note_detail_labels = []

        if self.selected_note_index is None:
            empty_label = ctk.CTkLabel(
                frame,
                text="Velg et notat i listen.",
                text_color=MUTED_TEXT
            )

            empty_label.pack(
                anchor="w",
                padx=18,
                pady=18
            )

            return

        index = self.selected_note_index
        note = self.data["notes"][index]

        # Teknologi og prosjekt øverst
        tags = []

        if note.get("technology"):
            tags.append(note["technology"])

        if note.get("project"):
            tags.append(note["project"])

        if tags:
            tags_label = ctk.CTkLabel(
                frame,
                text="  ·  ".join(tags),
                text_color=ACCENT,
                font=ctk.CTkFont(size=12, weight="bold")
            )

            tags_label.pack(
                anchor="w",
                padx=18,
                pady=(14, 0)
            )

        title_label = ctk.CTkLabel(
            frame,
            text=note.get("title", ""),
            text_color=TEXT_COLOR,
            anchor="w",
            justify="left",
            wraplength=300,
            font=ctk.CTkFont(size=20, weight="bold")
        )

        title_label.pack(
            anchor="w",
            padx=18,
            pady=(14 if not tags else 0, 0)
        )

        self.note_detail_labels.append(title_label)

        day = None

        try:
            day = datetime.fromisoformat(note.get("date", "")).date()
        except (TypeError, ValueError):
            pass

        if day is not None:
            date_label = ctk.CTkLabel(
                frame,
                text=self.format_day_heading(day),
                text_color=MUTED_TEXT
            )

            date_label.pack(
                anchor="w",
                padx=18
            )

        self.create_note_body(
            frame,
            note.get("text", "")
        )

        button_row = ctk.CTkFrame(
            frame,
            fg_color="transparent"
        )

        button_row.pack(
            anchor="w",
            padx=12,
            pady=(6, 12)
        )

        edit_button = ctk.CTkButton(
            button_row,
            text="Rediger",
            width=80,
            height=26,
            fg_color="transparent",
            hover_color=CARD_BG,
            text_color=ACCENT,
            border_width=1,
            border_color=ACCENT,
            command=lambda: self.open_note_window(index)
        )

        edit_button.pack(
            side="left",
            padx=(6, 6)
        )

        delete_button = ctk.CTkButton(
            button_row,
            text="Slett",
            width=60,
            height=26,
            fg_color="transparent",
            hover_color=CARD_BG,
            text_color=MUTED_TEXT,
            command=lambda: self.delete_note(index)
        )

        delete_button.pack(
            side="left"
        )

        self.wrap_labels(
            self.note_detail_labels,
            frame.winfo_width() - 50
        )

    def wrap_labels(self, labels, width):
        """Setter hvor bred teksten kan være før den
        brytes til en ny linje."""

        # Før vinduet er tegnet er bredden 1,
        # så da venter vi på neste <Configure>.
        if width < 80:
            return

        for label in labels:
            if label.winfo_exists():
                label.configure(wraplength=width)

    def create_note_body(self, parent, text):
        """Viser notatteksten. Det som står mellom
        ``` og ``` vises som kode, i en mørk boks
        med skrift der alle tegn er like brede."""

        # split deler teksten ved hver ```.
        # Da blir annenhver del vanlig tekst og kode:
        # "a ```b``` c" -> ["a ", "b", " c"]
        parts = text.split("```")

        for number, part in enumerate(parts):

            is_code = number % 2 == 1

            part = part.strip("\n")

            if not part.strip():
                continue

            if is_code:
                code_label = ctk.CTkLabel(
                    parent,
                    text=part,
                    anchor="w",
                    justify="left",
                    corner_radius=8,
                    fg_color=CODE_BG,
                    text_color=CODE_TEXT,
                    font=ctk.CTkFont(
                        family="Menlo",
                        size=12
                    )
                )

                code_label.pack(
                    fill="x",
                    padx=18,
                    pady=6,
                    ipadx=10,
                    ipady=8
                )

            else:
                text_label = ctk.CTkLabel(
                    parent,
                    text=part.strip(),
                    text_color=TEXT_COLOR,
                    anchor="w",
                    justify="left",
                    wraplength=300
                )

                text_label.pack(
                    anchor="w",
                    padx=18,
                    pady=(8, 4)
                )

                self.note_detail_labels.append(text_label)

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
            "430x620"
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

        # Behold teknologien selv om den er slettet
        if editing and note.get("technology") not in technology_values:
            technology_values.append(note.get("technology"))

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
        # PROSJEKT
        # -------------------------

        project_label = ctk.CTkLabel(
            self.note_window,
            text="Prosjekt"
        )

        project_label.pack(
            anchor="w",
            padx=25
        )

        project_values = ["Ingen prosjekt"]

        for project in self.data["projects"]:
            project_values.append(project["name"])

        self.note_project_menu = ctk.CTkOptionMenu(
            self.note_window,
            values=project_values,
            fg_color=ACCENT,
            button_color=ACCENT,
            button_hover_color=ACCENT_HOVER
        )

        self.note_project_menu.pack(
            fill="x",
            padx=25,
            pady=(5, 15)
        )

        if editing and note.get("project") in project_values:
            self.note_project_menu.set(note["project"])
        else:
            self.note_project_menu.set("Ingen prosjekt")

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
            height=180,
            wrap="word"
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

        code_tip = ctk.CTkLabel(
            self.note_window,
            text="Tips: skriv kode mellom ``` og ``` for å vise den som kode.",
            text_color=MUTED_TEXT,
            font=ctk.CTkFont(size=11)
        )

        code_tip.pack(
            anchor="w",
            padx=25,
            pady=(0, 4)
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

        project = self.note_project_menu.get()

        if project == "Ingen prosjekt":
            project = None

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
            "project": project,
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

        # Vis notatet du nettopp lagret
        if self.editing_note_index is not None:
            self.selected_note_index = self.editing_note_index
        else:
            self.selected_note_index = len(self.data["notes"]) - 1

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

        # Notatene etter dette har flyttet seg ett hakk,
        # så vi lar listen velge på nytt.
        self.selected_note_index = None

        self.save_data()
        self.refresh_notes_list()

    # -------------------------
    # FELLES
    # -------------------------

    def handle_main_scroll(self, event):
        """Scroller den aktive hovedsiden med vanlig Canvas."""

        canvas = self.active_scroll_canvas

        if canvas is None:
            return

        try:
            if not canvas.winfo_exists():
                return
        except tk.TclError:
            return

        if event.delta == 0:
            return "break"

        first, last = canvas.yview()

        # Hvis alt innhold allerede er synlig,
        # er det ingenting å scrolle.
        if (
            first <= 0.0
            and last >= 1.0
        ):
            return "break"

        if sys.platform == "darwin":

            scroll_speed = 3

            scroll_amount = int(
                -event.delta
                * scroll_speed
            )

        else:

            scroll_amount = int(
                -event.delta / 120
            )

        if scroll_amount == 0:

            if event.delta > 0:
                scroll_amount = -1

            else:
                scroll_amount = 1

        first, last = canvas.yview()

        # Ikke prøv å scrolle forbi toppen.
        if (
            scroll_amount < 0
            and first <= 0.001
        ):
            return "break"

        # Ikke prøv å scrolle forbi bunnen.
        if (
            scroll_amount > 0
            and last >= 0.999
        ):
            return "break"

        canvas.yview_scroll(
            scroll_amount,
            "units"
        )

        return "break"


    def restore_window_geometry(self):
        """Gjenoppretter størrelse og plassering fra forrige gang."""

        if not WINDOW_STATE_FILE.exists():
            return

        try:
            with open(
                WINDOW_STATE_FILE,
                "r",
                encoding="utf-8"
            ) as file:
                state = json.load(file)

            geometry = state.get(
                "geometry"
            )

            if geometry:
                self.geometry(
                    geometry
                )

        except (
            OSError,
            json.JSONDecodeError
        ):
            # Hvis filen mangler eller er ødelagt,
            # bruker DevTrack standardstørrelsen.
            pass


    def save_window_geometry(self):
        """Lagrer vinduets størrelse og plassering."""

        APP_SUPPORT_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        state = {
            "geometry": self.geometry()
        }

        try:
            with open(
                WINDOW_STATE_FILE,
                "w",
                encoding="utf-8"
            ) as file:
                json.dump(
                    state,
                    file,
                    indent=4,
                    ensure_ascii=False
                )

        except OSError:
            # Appen skal fortsatt kunne lukkes
            # selv om vindusposisjonen ikke kan lagres.
            pass


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

        self.save_window_geometry()

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

    def format_duration(self, total_seconds):
        """Som format_time, men tar med sekunder
        for korte økter, f.eks. "4 min 30 sek"."""

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours} t {minutes} min"

        if minutes > 0 and seconds == 0:
            return f"{minutes} min"

        if minutes > 0:
            return f"{minutes} min {seconds} sek"

        return f"{seconds} sek"

    def format_short_date(self, iso_text):
        """Gjør "2026-10-18T19:00" om til "18. okt",
        eller "18. okt 2025" hvis det ikke er i år."""

        try:
            day = datetime.fromisoformat(iso_text).date()
        except (TypeError, ValueError):
            return ""

        text = f"{day.day}. {MONTHS[day.month - 1][:3]}"

        if day.year != date.today().year:
            text += f" {day.year}"

        return text

    def format_day_heading(self, day):
        """Gjør en dato om til "I dag", "I går"
        eller f.eks. "Mandag 13. oktober"."""

        if day is None:
            return "Ukjent dato"

        days_ago = (date.today() - day).days

        if days_ago == 0:
            return "I dag"

        if days_ago == 1:
            return "I går"

        weekday = WEEKDAYS[day.weekday()].capitalize()
        month = MONTHS[day.month - 1]

        text = f"{weekday} {day.day}. {month}"

        # Ta med året hvis det ikke er i år
        if day.year != date.today().year:
            text += f" {day.year}"

        return text

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

        technologies = self.data[
            "technologies"
        ]

        if technologies:

            technology_values = technologies

        else:

            technology_values = [
                "Ingen teknologi"
            ]

        self.timer_technology_menu.configure(
            values=technology_values
        )

        current_technology = (
            self.timer_technology_menu.get()
        )

        if (
            current_technology
            not in technology_values
        ):

            current_technology = (
                technology_values[0]
            )

            self.timer_technology_menu.set(
                current_technology
            )

        # -------------------------
        # PROSJEKTER
        # -------------------------

        self.update_timer_project_options(
            current_technology
        )

    def show_page(
        self,
        page_name
    ):

        # Statistikk-siden viser "I dag" og "I går",
        # så den oppdateres hver gang du åpner den.
        if page_name == "stats":
            self.refresh_stats_page()

        self.active_scroll_canvas = (
            self.main_scroll_canvases.get(
                page_name
            )
        )

        self.pages[
            page_name
        ].tkraise()

        # Siden for én teknologi hører til under
        # Teknologier i menyen.
        if page_name == "technology":
            menu_page = "technologies"
        else:
            menu_page = page_name

        # Marker knappen for siden vi er på
        for name, button in self.nav_buttons.items():
            if name == menu_page:
                button.configure(
                    fg_color=CARD_LIGHT,
                    text_color=ACCENT
                )
            else:
                button.configure(
                    fg_color="transparent",
                    text_color=TEXT_COLOR
                )
