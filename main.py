import customtkinter as ctk


# -------------------------
# APP-INNSTILLINGER
# -------------------------

WINDOW_WIDTH = 760
WINDOW_HEIGHT = 680

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class DevTrackApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("DevTrack")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(650, 600)

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

        self.create_stat_card(
            stats_frame,
            "Total tid",
            "0 t"
        )

        self.create_stat_card(
            stats_frame,
            "Prosjekter",
            "0"
        )

        self.create_stat_card(
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

        placeholder = ctk.CTkLabel(
            page,
            text=(
                "Her kommer Python, SQL, JavaScript\n"
                "og andre teknologier du legger til."
            ),
            justify="left"
        )

        placeholder.pack(
            anchor="w",
            padx=30
        )

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

        button = ctk.CTkButton(
            page,
            text="+ Legg til teknologi"
        )

        button.pack(
            anchor="w",
            padx=30,
            pady=20
        )

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
            text="+ Nytt prosjekt"
        )

        button.pack(
            anchor="w",
            padx=30,
            pady=20
        )

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
    # FELLES FUNKSJONER
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