import customtkinter as ctk
import json
from pathlib import Path


# -------------------------
# APP-INNSTILLINGER
# -------------------------

WINDOW_WIDTH = 760
WINDOW_HEIGHT = 680

ctk.set_appearance_mode("light")

# data.json blir lagret i samme mappe som main.py
DATA_FILE = Path(__file__).parent / "data.json"


class DevTrackApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("DevTrack")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(650, 600)

        # Hent lagrede data
        self.data = self.load_data()

        # Vinduet deles i:
        # kolonne 0 = meny
        # kolonne 1 = innhold
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_sidebar()
        self.create_pages()

        self.show_page("home")

    # -------------------------
    # DATA
    # -------------------------

    def load_data(self):
        """Leser data fra data.json."""

        if DATA_FILE.exists():
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                return json.load(file)

        # Dette brukes første gang appen åpnes
        data = {
            "technologies": [
                "Python",
                "SQL",
                "JavaScript"
            ],
            "projects": [],
            "total_minutes": 0
        }

        self.save_data(data)

        return data

    def save_data(self, data=None):
        """Lagrer data i data.json."""

        if data is None:
            data = self.data

        with open(DATA_FILE, "w", encoding="utf-8") as file:
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
            width=150,
            corner_radius=0
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

        self.create_nav_button("Hjem", "home")
        self.create_nav_button("Teknologier", "technologies")
        self.create_nav_button("Prosjekter", "projects")
        self.create_nav_button("Timer", "timer")
        self.create_nav_button("Notater", "notes")

    def create_nav_button(self, text, page):
        button = ctk.CTkButton(
            self.sidebar,
            text=text,
            anchor="w",
            height=40,
            corner_radius=8,
            command=lambda: self.show_page(page)
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
            text="Hei! 👋",
            font=ctk.CTkFont(
                size=28,
                weight="bold"
            )
        )

        title.pack(
            anchor="w",
            padx=30,
            pady=(35, 5)
        )

        subtitle = ctk.CTkLabel(
            page,
            text="Her er oversikten over utviklingen din."
        )

        subtitle.pack(
            anchor="w",
            padx=30
        )

        stats_frame = ctk.CTkFrame(page)

        stats_frame.pack(
            fill="x",
            padx=30,
            pady=25
        )

        self.total_time_label = self.create_stat_card(
            stats_frame,
            "Total tid",
            "0 t"
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

        technologies_title = ctk.CTkLabel(
            page,
            text="Mine teknologier",
            font=ctk.CTkFont(
                size=18,
                weight="bold"
            )
        )

        technologies_title.pack(
            anchor="w",
            padx=30,
            pady=(10, 10)
        )

        self.home_technologies_frame = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )

        self.home_technologies_frame.pack(
            fill="x",
            padx=30
        )

        self.refresh_home_page()

    def create_stat_card(self, parent, title, value):
        card = ctk.CTkFrame(
            parent,
            height=90
        )

        card.pack(
            side="left",
            expand=True,
            fill="both",
            padx=5,
            pady=10
        )

        label = ctk.CTkLabel(
            card,
            text=title
        )

        label.pack(
            pady=(15, 0)
        )

        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(
                size=22,
                weight="bold"
            )
        )

        value_label.pack()

        return value_label

    def refresh_home_page(self):
        # Oppdater tallene øverst
        total_minutes = self.data["total_minutes"]

        hours = total_minutes // 60
        minutes = total_minutes % 60

        self.total_time_label.configure(
            text=f"{hours} t {minutes} min"
        )

        self.project_count_label.configure(
            text=str(len(self.data["projects"]))
        )

        self.technology_count_label.configure(
            text=str(len(self.data["technologies"]))
        )

        # Fjern gammel teknologiliste
        for widget in self.home_technologies_frame.winfo_children():
            widget.destroy()

        # Lag listen på nytt
        for technology in self.data["technologies"]:
            label = ctk.CTkLabel(
                self.home_technologies_frame,
                text=f"• {technology}",
                font=ctk.CTkFont(size=15)
            )

            label.pack(
                anchor="w",
                pady=3
            )

    # -------------------------
    # TEKNOLOGIER
    # -------------------------

    def create_technologies_page(self):
        page = self.pages["technologies"]

        self.create_page_title(
            page,
            "Teknologier",
            "Språk og verktøy du lærer."
        )

        add_button = ctk.CTkButton(
            page,
            text="+ Legg til teknologi",
            command=self.add_technology
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

        for technology in self.data["technologies"]:
            card = ctk.CTkFrame(
                self.technology_list_frame,
                height=55
            )

            card.pack(
                fill="x",
                pady=5
            )

            label = ctk.CTkLabel(
                card,
                text=technology,
                font=ctk.CTkFont(
                    size=16,
                    weight="bold"
                )
            )

            label.pack(
                side="left",
                padx=20,
                pady=15
            )

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

        if technology in self.data["technologies"]:
            return

        self.data["technologies"].append(technology)

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
            command=self.open_new_project_window
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
        # Fjern gammel prosjektliste
        for widget in self.project_list_frame.winfo_children():
            widget.destroy()

        # Hvis det ikke finnes prosjekter ennå
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

        # Vis hvert prosjekt
        for project in self.data["projects"]:
            card = ctk.CTkFrame(
                self.project_list_frame
            )

            card.pack(
                fill="x",
                pady=6
            )

            name_label = ctk.CTkLabel(
                card,
                text=project["name"],
                font=ctk.CTkFont(
                    size=17,
                    weight="bold"
                )
            )

            name_label.pack(
                anchor="w",
                padx=18,
                pady=(14, 2)
            )

            technologies = ", ".join(
                project.get("technologies", [])
            )

            info_text = (
                f"{technologies}  •  "
                f"{project.get('status', 'Aktivt')}"
            )

            info_label = ctk.CTkLabel(
                card,
                text=info_text
            )

            info_label.pack(
                anchor="w",
                padx=18
            )

            notes = project.get("notes", "")

            if notes:
                notes_label = ctk.CTkLabel(
                    card,
                    text=notes,
                    justify="left",
                    wraplength=450
                )

                notes_label.pack(
                    anchor="w",
                    padx=18,
                    pady=(6, 14)
                )
            else:
                info_label.pack_configure(
                    pady=(0, 14)
                )


    def open_new_project_window(self):
        self.project_window = ctk.CTkToplevel(self)

        self.project_window.title("Nytt prosjekt")
        self.project_window.geometry("420x500")
        self.project_window.resizable(False, False)

        self.project_window.transient(self)
        self.project_window.grab_set()

        title = ctk.CTkLabel(
            self.project_window,
            text="Nytt prosjekt",
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

        # Prosjektnavn
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

        # Teknologi
        technology_label = ctk.CTkLabel(
            self.project_window,
            text="Teknologi"
        )

        technology_label.pack(
            anchor="w",
            padx=25
        )

        technology_values = self.data["technologies"]

        if not technology_values:
            technology_values = ["Ingen"]

        self.project_technology_menu = ctk.CTkOptionMenu(
            self.project_window,
            values=technology_values
        )

        self.project_technology_menu.pack(
            fill="x",
            padx=25,
            pady=(5, 15)
        )

        # Status
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
            ]
        )

        self.project_status_menu.set("Aktivt")

        self.project_status_menu.pack(
            fill="x",
            padx=25,
            pady=(5, 15)
        )

        # Notater
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

        self.project_error_label = ctk.CTkLabel(
            self.project_window,
            text=""
        )

        self.project_error_label.pack()

        save_button = ctk.CTkButton(
            self.project_window,
            text="Lagre prosjekt",
            command=self.save_new_project
        )

        save_button.pack(
            pady=10
        )


    def save_new_project(self):
        name = self.project_name_entry.get().strip()

        if name == "":
            self.project_error_label.configure(
                text="Skriv inn et prosjektnavn."
            )
            return

        technology = self.project_technology_menu.get()
        status = self.project_status_menu.get()

        notes = self.project_notes_text.get(
            "1.0",
            "end"
        ).strip()

        if technology == "Ingen":
            technologies = []
        else:
            technologies = [technology]

        project = {
            "name": name,
            "status": status,
            "technologies": technologies,
            "notes": notes
        }

        self.data["projects"].append(project)

        self.save_data()

        self.refresh_project_list()
        self.refresh_home_page()

        self.project_window.destroy()

    # -------------------------
    # TIMER
    # -------------------------

    def create_timer_page(self):
        page = self.pages["timer"]

        self.create_page_title(
            page,
            "Timer",
            "Logg tiden du bruker på programmering."
        )

        timer_label = ctk.CTkLabel(
            page,
            text="00:00:00",
            font=ctk.CTkFont(
                size=42,
                weight="bold"
            )
        )

        timer_label.pack(
            pady=40
        )

        button = ctk.CTkButton(
            page,
            text="Start timer",
            width=160,
            height=45
        )

        button.pack()

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
            text="+ Nytt notat"
        )

        button.pack(
            anchor="w",
            padx=30,
            pady=20
        )

    # -------------------------
    # FELLES
    # -------------------------

    def create_page_title(self, page, title, subtitle):
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

    def show_page(self, page_name):
        self.pages[page_name].tkraise()

if __name__ == "__main__":
    app = DevTrackApp()
    app.mainloop()