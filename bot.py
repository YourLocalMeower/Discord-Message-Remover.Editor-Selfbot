import os
import sys
import math
import time
import random
import requests
from collections import deque
from dotenv import load_dotenv
from datetime import datetime, timedelta

API = "https://discord.com/api/v9"
DISCORD_EPOCH = 1420070400000
MAX_LEN = 2000

MIN_DELAY = 1
MAX_DELAY = 15 * 60
BREAK_MIN = 6 * 60
BREAK_MAX = 20 * 60

os.system("")  # kolory ANSI w konsoli Windows


class C:
    R = "\033[0m"
    B = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GRN = "\033[92m"
    YEL = "\033[93m"
    BLU = "\033[94m"
    MAG = "\033[95m"
    CYN = "\033[96m"


def fmt_time(s):
    s = int(max(0, s))
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h:d}:{m:02d}:{sec:02d}" if h else f"{m:02d}:{sec:02d}"


def clock(ts):
    """Godzina; jeśli to inny dzień niż dziś, dodaje datę."""
    dt = datetime.fromtimestamp(ts)
    if dt.date() == datetime.now().date():
        return dt.strftime("%H:%M:%S")
    return dt.strftime("%d.%m %H:%M")


def bar(done, total, width=30):
    filled = int(width * done / total) if total else width
    return f"{C.GRN}{'█' * filled}{C.DIM}{'░' * (width - filled)}{C.R}"


def preview(text, n=70):
    t = (text or "").replace("\n", " ⏎ ").strip()
    if not t:
        return f"{C.DIM}[brak tekstu - załącznik/embed]{C.R}"
    return t if len(t) <= n else t[:n - 1] + "…"


def mean(q, default):
    return sum(q) / len(q) if q else default


# ---------------- wejście ----------------

def ask_yn(prompt):
    while True:
        a = input(prompt).strip().lower()
        if a in ("y", "t"):
            return True
        if a == "n":
            return False
        print("Wpisz Y lub N.")


def ask_date(prompt):
    """Zwraca datę (bez strefy) - interpretowana później jako czas LOKALNY."""
    while True:
        try:
            return datetime.strptime(input(prompt).strip(), "%Y-%m-%d")
        except ValueError:
            print("Zły format, użyj YYYY-MM-DD.")


def ask_choice(prompt, options):
    while True:
        a = input(prompt).strip()
        if a in options:
            return a
        print(f"Wpisz jedną z opcji: {', '.join(options)}.")


def ask_float(prompt, lo, hi, allow_empty=False):
    while True:
        a = input(prompt).strip().replace(",", ".")
        if not a and allow_empty:
            return None
        try:
            v = float(a)
            if lo <= v <= hi:
                return v
        except ValueError:
            pass
        print(f"Podaj liczbę z zakresu {lo}-{hi}.")


def ask_range():
    """Zwraca (od, do) jako daty naiwne albo None (= początek / koniec konwersacji)."""
    while True:
        print("\nPoczątek zakresu:")
        print("  [1] Od podanej daty")
        print("  [2] Od początku konwersacji")
        fc = ask_choice("Wybór: ", ("1", "2"))
        d_from = ask_date("Data od (YYYY-MM-DD): ") if fc == "1" else None

        print("\nKoniec zakresu:")
        print("  [1] Do podanej daty (włącznie)")
        print("  [2] Do końca konwersacji (najnowsze wiadomości)")
        tc = ask_choice("Wybór: ", ("1", "2"))
        d_to = ask_date("Data do (YYYY-MM-DD): ") if tc == "1" else None

        if d_from and d_to and d_from > d_to:
            print(f"{C.RED}Data „od” ({d_from:%Y-%m-%d}) jest późniejsza niż „do” "
                  f"({d_to:%Y-%m-%d}). Podaj zakres ponownie.{C.R}")
            continue
        return d_from, d_to


def find_txt_files():
    folders = {os.path.dirname(os.path.abspath(__file__)), os.getcwd()}
    found = []
    for folder in folders:
        try:
            for name in sorted(os.listdir(folder)):
                if name.lower().endswith(".txt") and name.lower() != "requirements.txt":
                    found.append(os.path.join(folder, name))
        except OSError:
            pass
    return found


def read_text_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read().strip()
    except OSError as e:
        print(f"Nie można odczytać pliku: {e}")
        return None
    if not text:
        print("Plik jest pusty.")
        return None
    if len(text) > MAX_LEN:
        print(f"Tekst ma {len(text)} znaków, limit Discorda to {MAX_LEN}.")
        return None
    return text


def load_text():
    files = find_txt_files()
    while True:
        path = None
        if files:
            print(f"\n{C.B}Znalezione pliki .txt:{C.R}")
            for i, p in enumerate(files, 1):
                print(f"  [{i}] {os.path.basename(p)} {C.DIM}({os.path.getsize(p)} B){C.R}")
            print("  [0] Podaj ścieżkę ręcznie")
            if len(files) == 1:
                if ask_yn(f"Użyć pliku {os.path.basename(files[0])}? (Y/N): "):
                    path = files[0]
            else:
                a = input("Wybierz numer: ").strip()
                if a.isdigit() and 1 <= int(a) <= len(files):
                    path = files[int(a) - 1]
        if path is None:
            path = input("Ścieżka do pliku .txt: ").strip().strip('"')
        text = read_text_file(path)
        if text is None:
            continue
        print(f"{C.DIM}Podgląd: {preview(text, 100)} ({len(text)} znaków){C.R}")
        if ask_yn("Zatwierdzić ten tekst? (Y/N): "):
            return text


def to_snowflake(dt):
    return (int(dt.timestamp() * 1000) - DISCORD_EPOCH) << 22


# ---------------- tempo ----------------

class Pacer:
    """Planuje odstępy i na bieżąco szacuje pozostały czas na podstawie realnego tempa pracy."""

    def __init__(self, total, budget_s=None, manual=None, fast=False):
        self.total = total
        self.budget_s = budget_s
        self.manual = manual  # (min_s, max_s) albo None
        self.fast = fast      # FAST-RISKY: zero odstępu
        self.start = time.time()
        self.done = 0
        self.recent = deque()
        self.slow = 1.0
        self.hits429 = 0
        self.burst_left = random.randint(3, 6)
        # statystyki do szacowania czasu
        self.req_times = deque(maxlen=30)    # czas samej akcji (z ewentualnym rate limitem)
        self.wait_times = deque(maxlen=20)   # odstępy w trybie ręcznym/normalnym
        self.short_times = deque(maxlen=20)  # krótkie odstępy w serii (auto)
        self.break_times = deque(maxlen=5)   # długie przerwy (auto)

    def penalize(self):
        self.hits429 += 1
        self.slow = min(self.slow * 1.5, 6.0)

    def record(self):
        now = time.time()
        self.recent.append(now)
        while self.recent and now - self.recent[0] > 3600:
            self.recent.popleft()
        self.done += 1

    def load(self):
        return min(1.0, len(self.recent) / 30)

    def short_delay(self):
        d = random.triangular(MIN_DELAY, 15, 4) * self.slow
        return min(max(d, MIN_DELAY), MAX_DELAY)

    def _plan_break(self, left):
        base = BREAK_MIN + (BREAK_MAX - BREAK_MIN) * self.load()
        if self.budget_s:
            remaining = self.budget_s - (time.time() - self.start)
            bursts_left = max(math.ceil(left / 4.5), 1)
            need = remaining - left * 6
            base = need / max(bursts_left - 1, 1) if bursts_left > 1 else BREAK_MIN
        return min(max(base * self.slow, BREAK_MIN), BREAK_MAX)

    def long_break(self):
        left = self.total - self.done
        val = self._plan_break(left) * random.uniform(0.85, 1.15)
        return min(max(val, BREAK_MIN), BREAK_MAX)

    def next_wait(self):
        """Zwraca (sekundy, rodzaj) po zakończonej akcji."""
        if self.fast:
            return 0, "odstęp"
        if self.manual:
            lo, hi = self.manual
            return min(max(random.uniform(lo, hi) * self.slow, MIN_DELAY), MAX_DELAY), "odstęp"
        self.burst_left -= 1
        if self.burst_left <= 0:
            self.burst_left = random.randint(3, 6)
            return self.long_break(), "PRZERWA"
        return self.short_delay(), "odstęp"

    # --- statystyki ---
    def note_request(self, seconds):
        self.req_times.append(seconds)

    def note_wait(self, kind, seconds):
        if self.fast:
            return
        if self.manual:
            self.wait_times.append(seconds)
        elif kind == "PRZERWA":
            self.break_times.append(seconds)
        else:
            self.short_times.append(seconds)

    def eta(self, left):
        """Szacowany czas przetworzenia `left` pozostałych akcji (z odstępami między nimi)."""
        if left <= 0:
            return 0.0
        req = mean(self.req_times, 0.4)
        waits = left - 1
        if self.fast:
            return left * req
        if self.manual:
            lo, hi = self.manual
            exp = min(max((lo + hi) / 2 * self.slow, MIN_DELAY), MAX_DELAY)
            w = mean(self.wait_times, exp) if len(self.wait_times) >= 3 else exp
            return left * req + waits * w

        # tryb auto: serie + długie przerwy
        short_exp = min(max(((MIN_DELAY + 15 + 4) / 3) * self.slow, MIN_DELAY), MAX_DELAY)
        short = mean(self.short_times, short_exp) if len(self.short_times) >= 3 else short_exp
        if len(self.break_times) >= 2:
            brk = mean(self.break_times, BREAK_MIN)
        elif self.budget_s:
            brk = self._plan_break(left)
        else:
            brk = min(max((BREAK_MIN + BREAK_MAX) / 2 * self.slow, BREAK_MIN), BREAK_MAX)

        if waits < self.burst_left:
            breaks = 0
        else:
            breaks = 1 + int((waits - self.burst_left) / 4.5)
        breaks = min(breaks, waits)
        shorts = waits - breaks
        return left * req + shorts * short + breaks * brk


def countdown(seconds, kind, next_label):
    end = time.monotonic() + seconds
    color = C.MAG if kind == "PRZERWA" else C.YEL
    wake = clock(time.time() + seconds)
    while True:
        left = end - time.monotonic()
        if left <= 0:
            break
        sys.stdout.write(
            f"\r   {color}⏳ {kind}{C.R} {C.B}{fmt_time(left)}{C.R} "
            f"{C.DIM}(do {wake}) → {next_label}{C.R}   "
        )
        sys.stdout.flush()
        time.sleep(min(0.25, max(left, 0.01)))
    sys.stdout.write("\r" + " " * 110 + "\r")


# ---------------- API ----------------

def request(session, pacer, method, url, **kwargs):
    kwargs.setdefault("timeout", (10, 30))  # połączenie 10 s, odpowiedź 30 s
    attempts = 0
    while True:
        try:
            r = session.request(method, url, **kwargs)
        except (requests.exceptions.Timeout,
                requests.exceptions.ConnectionError) as e:
            attempts += 1
            if attempts > 6:
                sys.exit(f"{C.RED}Brak połączenia z Discordem po {attempts - 1} próbach "
                         f"({type(e).__name__}). Sprawdź internet i uruchom skrypt "
                         f"ponownie - nieprzetworzone wiadomości zostaną wznowione.{C.R}")
            wait = min(5 * 2 ** (attempts - 1), 120) + random.uniform(0, 3)
            print(f"   {C.YEL}⚠ problem z połączeniem ({type(e).__name__}) - "
                  f"próba {attempts}/6 za {wait:.0f}s{C.R}")
            time.sleep(wait)
            continue

        if r.status_code == 429:
            try:
                wait = float(r.json().get("retry_after", 5))
            except ValueError:
                wait = 5
            if pacer:
                pacer.penalize()
            wait += random.uniform(0.5, 2.0)
            print(f"   {C.RED}⚠ rate limit{C.R} - czekam {wait:.1f}s"
                  + (f", tempo ×{pacer.slow:.1f}" if pacer else ""))
            time.sleep(wait)
            continue
        if r.status_code == 401:
            sys.exit(f"{C.RED}Token odrzucony (401). Zatrzymuję.{C.R}")
        return r


def banner():
    print(f"{C.CYN}{C.B}")
    print("╔════════════════════════════════════════╗")
    print("║        Discord Message Cleaner         ║")
    print("╚════════════════════════════════════════╝" + C.R)


def main():
    load_dotenv()
    token = os.environ.get("TOKEN")
    if not token:
        sys.exit("Brak TOKEN w pliku .env")

    session = requests.Session()
    session.headers.update({"Authorization": token.strip()})

    me = request(session, None, "GET", f"{API}/users/@me")
    if me.status_code != 200:
        sys.exit("Nieprawidłowy token.")
    my_id = me.json()["id"]

    banner()
    print(f"{C.DIM}Zalogowano jako: {me.json().get('username')}{C.R}\n")

    channel_id = input("ID kanału: ").strip()

    # --- zakres dat (czas lokalny) ---
    d_from, d_to = ask_range()
    date_from = d_from.astimezone() if d_from else None                   # początek dnia (lokalnie)
    date_to = (d_to + timedelta(days=1)).astimezone() if d_to else None   # koniec dnia (lokalnie), wyłącznie
    left_txt = f"{d_from:%Y-%m-%d}" if d_from else "początek konwersacji"
    right_txt = f"{d_to:%Y-%m-%d}" if d_to else "koniec konwersacji"
    print(f"{C.DIM}Zakres (czas lokalny): {left_txt} → {right_txt}{C.R}")

    mode = ask_choice("\nTryb: [1] Usuń  [2] Zamień na tekst z pliku: ", ("1", "2"))

    new_text = None
    collapse = False
    keep_newest = True
    if mode == "2":
        new_text = load_text()
        include_edited = ask_yn("Zmieniać też już edytowane? (Y/N): ")
        print("\nCo robić z wiadomościami z załącznikiem/embedem (obraz, plik, podgląd linku)?")
        print("  [1] Tylko edytuj tekst (załącznik zostaje)")
        print("  [2] Usuń całą wiadomość")
        print("  [3] Pomiń takie wiadomości")
        media_choice = ask_choice("Wybór: ", ("1", "2", "3"))
        print("\nCo robić z wiadomościami, które są ODPOWIEDZIAMI na inne wiadomości?")
        print("  [1] Edytuj tekst")
        print("  [2] Usuń")
        print("  [3] Zostaw")
        rc = ask_choice("Wybór: ", ("1", "2", "3"))
        reply_action = {"1": "edit", "2": "delete", "3": "skip"}[rc]

        print("\nUsuwać nadmiarowe, następujące po sobie Twoje wiadomości?")
        print(f"{C.DIM}(maks. 1 Twoja wiadomość pod rząd, np. 4 Twoje, 1 cudza, 2 Twoje, 3 cudze"
              f" → 1 Twoja, 1 cudza, 1 Twoja, 3 cudze){C.R}")
        print(f"{C.DIM}Serie liczone są tylko w wybranym zakresie dat. Nadmiarowe wiadomości są usuwane,"
              f" chyba że wykluczają je Twoje reguły powyżej (edytowane / odpowiedzi / media).{C.R}")
        collapse = ask_yn("Włączyć? (Y/N): ")
        if collapse:
            print("  [1] Zostaw najnowszą wiadomość z serii")
            print("  [2] Zostaw najstarszą wiadomość z serii")
            keep_newest = ask_choice("Wybór: ", ("1", "2")) == "1"
    else:
        include_edited = ask_yn("Usuwać edytowane? (Y/N): ")
        media_choice = "2"
        print("\nCo robić z wiadomościami, które są ODPOWIEDZIAMI na inne wiadomości?")
        print("  [1] Usuń")
        print("  [2] Zostaw")
        rc = ask_choice("Wybór: ", ("1", "2"))
        reply_action = "delete" if rc == "1" else "skip"

    # --- tempo ---
    print("\nTempo:")
    print("  [1] Normalne  - odstęp losowo 1-20 s")
    print("  [2] Auto      - serie + przerwy 6-20 min")
    print("  [3] Ręczne    - własny zakres")
    print(f"  [4] {C.RED}FAST-RISKY{C.R}  - bez odstępów (0 s)")
    pace_mode = ask_choice("Wybór: ", ("1", "2", "3", "4"))
    budget_s, manual, fast = None, None, False
    if pace_mode == "1":
        manual = (1, 20)
    elif pace_mode == "2":
        h = ask_float("Maks. czas całości w godzinach (Enter = auto wg obciążenia): ",
                      0.1, 500, allow_empty=True)
        budget_s = h * 3600 if h else None
    elif pace_mode == "3":
        lo = ask_float("Min. odstęp w sekundach (1-900): ", MIN_DELAY, MAX_DELAY)
        hi = ask_float("Maks. odstęp w sekundach (1-900): ", lo, MAX_DELAY)
        manual = (lo, hi)
    else:
        what = "usuwania" if mode == "1" else "edycji"
        print(f"{C.RED}{C.B}⚠ FAST-RISKY:{C.R} akcje {what} wykonują się jedna po drugiej, bez przerw. "
              f"Discord będzie zwracał rate limity (skrypt je respektuje i czeka), "
              f"a ryzyko flagi lub blokady konta jest WYRAŹNIE wyższe"
              + (" - przy edycjach jeszcze bardziej niż przy usuwaniu." if mode == "2" else "."))
        if ask_yn("Na pewno użyć FAST-RISKY? (Y/N): "):
            fast = True
        else:
            print("Przełączam na tempo Normalne (1-20 s).")
            manual = (1, 20)

    # --- zbieranie ---
    print(f"\n{C.BLU}🔍 Skanuję kanał...{C.R}")
    msgs = []  # wiadomości z zakresu, od najnowszych do najstarszych
    seen_ids = set()
    cursor = to_snowflake(date_to) if date_to else None
    done = False
    scanned = 0
    while not done:
        params = {"limit": 100}
        if cursor:
            params["before"] = cursor
        r = request(session, None, "GET", f"{API}/channels/{channel_id}/messages", params=params)
        if r.status_code != 200:
            sys.exit(f"{C.RED}Błąd pobierania: {r.status_code} {r.text}{C.R}")
        batch = r.json()
        if not batch:
            break
        scanned += len(batch)
        for m in batch:
            if m["id"] in seen_ids:
                continue
            seen_ids.add(m["id"])
            ts = datetime.fromisoformat(m["timestamp"])
            if date_from and ts < date_from:
                done = True
                continue
            if date_to and ts >= date_to:
                continue
            m["_ts"] = ts
            msgs.append(m)
        cursor = batch[-1]["id"]
        sys.stdout.write(f"\r   przeskanowano {scanned}, w zakresie {len(msgs)}   ")
        sys.stdout.flush()
        if not fast:
            time.sleep(random.uniform(0.5, 1.2))

    # --- klasyfikacja ---
    stats = {"media": 0, "reply": 0}

    def mine_ok(m):
        return m["author"]["id"] == my_id and m["type"] in (0, 19)

    def decide(m, dup):
        """Zwraca 'edit' / 'delete' albo None (pomiń)."""
        if m.get("edited_timestamp") and not include_edited:
            return None
        is_reply = m["type"] == 19
        has_media = bool(m.get("attachments")) or bool(m.get("embeds"))
        if is_reply and reply_action == "skip":
            stats["reply"] += 1
            return None
        if not is_reply and has_media and mode == "2" and media_choice == "3":
            stats["media"] += 1
            return None
        if dup:
            return "delete"
        if is_reply:
            action = reply_action
        elif mode == "1":
            action = "delete"
        elif has_media and media_choice == "2":
            action = "delete"
        else:
            action = "edit"
        if action == "edit" and m.get("content") == new_text:
            return None  # już ma ten tekst
        return action

    targets = []

    def add(m, dup):
        action = decide(m, dup)
        if action is None:
            return
        targets.append({
            "id": m["id"], "content": m.get("content", ""),
            "date": m["_ts"].astimezone().strftime("%Y-%m-%d %H:%M"),
            "media": bool(m.get("attachments")) or bool(m.get("embeds")),
            "reply": m["type"] == 19, "action": action, "dup": dup,
        })

    if collapse:
        i = 0
        while i < len(msgs):
            if not mine_ok(msgs[i]):
                i += 1
                continue
            j = i
            while j < len(msgs) and mine_ok(msgs[j]):
                j += 1
            run = msgs[i:j]  # od najnowszej do najstarszej
            keep = run[0] if keep_newest else run[-1]
            for m in run:
                add(m, dup=(m is not keep))
            i = j
    else:
        for m in msgs:
            if mine_ok(m):
                add(m, dup=False)

    total = len(targets)
    n_dup = sum(1 for t in targets if t["dup"])
    n_edit = sum(1 for t in targets if t["action"] == "edit")
    n_del = total - n_edit
    n_media = sum(1 for t in targets if t["media"])
    n_reply = sum(1 for t in targets if t["reply"])
    print(f"\n\n{C.B}Znaleziono {total} wiadomości{C.R} "
          f"{C.DIM}(przeskanowano {scanned}, w zakresie {len(msgs)}){C.R}")
    print(f"  do edycji: {n_edit} · do usunięcia: {n_del}"
          + (f" (w tym nadmiarowe z serii: {n_dup})" if collapse else "")
          + f" · odpowiedzi: {n_reply} · z załącznikiem/embedem: {n_media}")
    print(f"  pominięte: odpowiedzi {stats['reply']} · media {stats['media']}")
    if total == 0:
        return

    pacer = Pacer(total, budget_s, manual, fast)
    est = pacer.eta(total)
    print(f"Szacowany czas: {C.B}{fmt_time(est)}{C.R} "
          f"(koniec ok. {clock(time.time() + est)}) "
          f"{C.DIM}- szacunek będzie korygowany na bieżąco{C.R}")
    if budget_s and budget_s < total * 6 + (total / 4.5 - 1) * BREAK_MIN:
        print(f"{C.YEL}⚠ Podany limit jest krótszy niż minimum przy przerwach 6 min - "
              f"skrypt zrobi to najszybciej, jak pozwalają zasady, więc może się nie zmieścić.{C.R}")

    if n_edit and n_del:
        question = f"zmienić {n_edit} i USUNĄĆ {n_del} wiadomości"
    elif n_del:
        question = f"USUNĄĆ {n_del} wiadomości"
    else:
        question = f"zmienić na tekst z pliku {n_edit} wiadomości"
    if not ask_yn(f"\nCzy na pewno {question}? (Y/N): "):
        print("Anulowano.")
        return
    print("Ctrl+C = bezpieczne zatrzymanie.\n")

    ok_count = fail_count = skipped = 0
    processed = set()  # zabezpieczenie: żadna wiadomość nie jest ruszana dwa razy

    try:
        for i, t in enumerate(targets, 1):
            if t["id"] in processed:
                continue
            processed.add(t["id"])

            url = f"{API}/channels/{channel_id}/messages/{t['id']}"
            is_delete = t["action"] == "delete"
            tags = ""
            if t["media"]:
                tags += f" {C.MAG}📎{C.R}"
            if t["reply"]:
                tags += f" {C.BLU}↩{C.R}"
            if is_delete:
                act_tag = f"{C.RED}USUŃ{C.R}" + (f" {C.DIM}(nadmiarowa z serii){C.R}" if t["dup"] else "")
            else:
                act_tag = f"{C.BLU}EDYTUJ{C.R}"
            print(f"{C.CYN}{C.B}[{i}/{total}]{C.R} {bar(i - 1, total)} "
                  f"{C.DIM}{t['date']} · id {t['id']}{C.R}")
            print(f"   ✉  {preview(t['content'])}{tags}  → {act_tag}")

            started = time.time()
            if is_delete:
                r = request(session, pacer, "DELETE", url)
                ok = r.status_code == 204
                label_ok = "Usunięto"
            else:
                r = request(session, pacer, "PATCH", url, json={"content": new_text})
                ok = r.status_code == 200
                label_ok = "Zmieniono" + (" (załącznik zostaje)" if t["media"] else "")
            took = time.time() - started
            pacer.note_request(took)

            if ok:
                ok_count += 1
                print(f"   {C.GRN}✔ {label_ok}{C.R} {C.DIM}({took:.1f}s){C.R}")
            elif r.status_code == 404:
                skipped += 1
                print(f"   {C.YEL}↷ Pominięto - wiadomość już nie istnieje{C.R}")
            else:
                fail_count += 1
                print(f"   {C.RED}✘ Błąd {r.status_code}: {r.text[:120]}{C.R}")
                if r.status_code == 403 and fail_count >= 3:
                    print(f"{C.RED}Powtarzające się 403 - zatrzymuję.{C.R}")
                    break

            pacer.record()
            if i < total:
                wait, kind = pacer.next_wait()
                pacer.note_wait(kind, wait)
                elapsed = time.time() - pacer.start
                remaining = wait + pacer.eta(total - i)
                rate = f" · ~{i / elapsed * 3600:.0f}/h" if elapsed > 5 else ""
                print(f"   {C.DIM}⏱ upłynęło {fmt_time(elapsed)} · zostało ok. {fmt_time(remaining)} · "
                      f"koniec ok. {clock(time.time() + remaining)} · "
                      f"tempo ×{pacer.slow:.1f}{rate}{C.R}")
                if wait > 0:
                    nxt = f"następna: {preview(targets[i]['content'], 40)}"
                    countdown(wait, kind, nxt)
                print()
    except KeyboardInterrupt:
        print(f"\n\n{C.YEL}⏹ Zatrzymano przez użytkownika.{C.R}")

    print(f"\n{C.B}══════ Podsumowanie ══════{C.R}")
    print(f"{C.GRN}Sukces: {ok_count}{C.R}  {C.RED}Błędy: {fail_count}{C.R}  "
          f"{C.YEL}Pominięte: {skipped}{C.R}")
    if fast and pacer.hits429:
        print(f"{C.YEL}Rate limity w trybie FAST-RISKY: {pacer.hits429}{C.R}")
    print(f"Czas: {fmt_time(time.time() - pacer.start)}")
    print("Gotowe.")


if __name__ == "__main__":
    main()
