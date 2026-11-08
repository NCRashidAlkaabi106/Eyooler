import re
import tkinter as tk
import webbrowser
from tkinter import messagebox, ttk
from urllib.parse import quote_plus, urlparse


BACKGROUND = "#171b1c"
SURFACE = "#222829"
FIELD = "#2c3435"
TEXT = "#f3f0e8"
MUTED = "#a4b0ad"
ACCENT = "#f08a62"
MINT = "#9bd4bd"


class DomainSearchBrowser:
	def __init__(self, root: tk.Tk) -> None:
		self.root = root
		self.root.title("Domain Search Browser")
		self.root.geometry("760x650")
		self.root.minsize(620, 580)
		self.root.configure(bg=BACKGROUND)

		self.domain = tk.StringVar()
		self.terms = tk.StringVar()
		self.phrase = tk.StringVar()
		self.authorized = tk.BooleanVar(value=False)
		self.query_preview = tk.StringVar(value="Your scoped Google query will appear here.")

		self._configure_styles()
		self._build_interface()
		self.terms.trace_add("write", self._refresh_preview)
		self.phrase.trace_add("write", self._refresh_preview)
		self.domain.trace_add("write", self._refresh_preview)
		self.root.bind("<Return>", lambda _event: self.search())

	def _configure_styles(self) -> None:
		style = ttk.Style()
		style.theme_use("clam")
		style.configure(
			"TEntry",
			fieldbackground=FIELD,
			foreground=TEXT,
			insertcolor=TEXT,
			bordercolor=FIELD,
			padding=(12, 10),
		)
		style.configure(
			"Search.TButton",
			background=ACCENT,
			foreground="#201916",
			font=("Segoe UI", 11, "bold"),
			padding=(18, 12),
			borderwidth=0,
		)
		style.map("Search.TButton", background=[("active", "#ffab84")])
		style.configure(
			"TCheckbutton",
			background=BACKGROUND,
			foreground=TEXT,
			font=("Segoe UI", 10),
			padding=(0, 5),
		)
		style.map("TCheckbutton", background=[("active", BACKGROUND)])

	def _build_interface(self) -> None:
		outer = tk.Frame(self.root, bg=BACKGROUND, padx=42, pady=34)
		outer.pack(fill="both", expand=True)

		tk.Label(
			outer,
			text="AUTHORIZED SITE SEARCH",
			bg=BACKGROUND,
			fg=MINT,
			font=("Segoe UI", 9, "bold"),
		).pack(anchor="w")
		tk.Label(
			outer,
			text="Domain Search",
			bg=BACKGROUND,
			fg=TEXT,
			font=("Georgia", 30),
		).pack(anchor="w", pady=(7, 4))
		tk.Label(
			outer,
			text="Explore public pages indexed for a domain you manage.",
			bg=BACKGROUND,
			fg=MUTED,
			font=("Segoe UI", 11),
		).pack(anchor="w", pady=(0, 27))

		self._field(outer, "TARGET DOMAIN", self.domain)
		self._field(outer, "WORDS TO FIND", self.terms)
		self._field(outer, "EXACT PHRASE (OPTIONAL)", self.phrase)

		ttk.Checkbutton(
			outer,
			text="I own this domain or have permission to assess it",
			variable=self.authorized,
		).pack(anchor="w", pady=(4, 17))

		preview = tk.Frame(outer, bg=SURFACE, padx=16, pady=14)
		preview.pack(fill="x", pady=(0, 17))
		tk.Label(
			preview,
			text="SEARCH PREVIEW",
			bg=SURFACE,
			fg=MINT,
			font=("Segoe UI", 8, "bold"),
		).pack(anchor="w", pady=(0, 7))
		tk.Label(
			preview,
			textvariable=self.query_preview,
			bg=SURFACE,
			fg=TEXT,
			font=("Consolas", 10),
			justify="left",
			wraplength=620,
		).pack(anchor="w", fill="x")

		ttk.Button(outer, text="Search Google", style="Search.TButton", command=self.search).pack(
			anchor="w"
		)
		tk.Label(
			outer,
			text="Searches are limited to the domain above and use ordinary text terms.",
			bg=BACKGROUND,
			fg=MUTED,
			font=("Segoe UI", 9),
		).pack(anchor="w", pady=(15, 0))

	def _field(self, parent: tk.Frame, label: str, variable: tk.StringVar) -> None:
		section = tk.Frame(parent, bg=BACKGROUND)
		section.pack(fill="x", pady=(0, 17))
		tk.Label(
			section,
			text=label,
			bg=BACKGROUND,
			fg=MUTED,
			font=("Segoe UI", 8, "bold"),
		).pack(anchor="w", pady=(0, 7))
		entry = ttk.Entry(section, textvariable=variable, font=("Segoe UI", 11))
		entry.pack(fill="x")

	@staticmethod
	def _normalize_domain(value: str) -> str | None:
		raw = value.strip()
		if not raw or any(char.isspace() for char in raw):
			return None
		parsed = urlparse(raw if "://" in raw else f"https://{raw}")
		host = (parsed.hostname or "").lower().rstrip(".")
		if not host or "." not in host or not re.fullmatch(r"[a-z0-9.-]+", host):
			return None
		if ".." in host or host.startswith(".") or host.endswith("."):
			return None
		return host

	@staticmethod
	def _plain_terms(value: str) -> str | None:
		text = value.strip()
		if re.search(r"[:\"'<>]", text):
			return None
		return " ".join(text.split())

	def _make_query(self) -> str | None:
		domain = self._normalize_domain(self.domain.get())
		terms = self._plain_terms(self.terms.get())
		phrase = self._plain_terms(self.phrase.get())
		if domain is None or terms is None or phrase is None:
			return None
		if not terms and not phrase:
			return None
		pieces = [f"site:{domain}"]
		if terms:
			pieces.append(terms)
		if phrase:
			pieces.append(f'"{phrase}"')
		return " ".join(pieces)

	def _refresh_preview(self, *_args: object) -> None:
		query = self._make_query()
		self.query_preview.set(query or "Enter a valid domain and plain-text search terms.")

	def search(self) -> None:
		if not self.authorized.get():
			messagebox.showwarning("Permission required", "Confirm you are authorized to assess this domain.")
			return
		query = self._make_query()
		if query is None:
			messagebox.showerror(
				"Check your search",
				"Enter a valid domain and at least one search term. Use plain text, not search operators.",
			)
			return
		webbrowser.open_new_tab(f"https://www.google.com/search?q={quote_plus(query)}")


def main() -> None:
	root = tk.Tk()
	DomainSearchBrowser(root)
	root.mainloop()


if __name__ == "__main__":
	main()
