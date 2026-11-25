import os
import sys
import math
import time
import random
import requests
from collections import deque
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

API = "https://discord.com/api/v9"
DISCORD_EPOCH = 1420070400000
MAX_LEN = 2000

MIN_DELAY = 1
MAX_DELAY = 15 * 60 ##15
BREAK_MIN = 2 * 60 ##?
BREAK_MAX = 20 * 60 ##20

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
    return datetime.fromtimestamp(ts).strftime("%H:%M:%S")


def bar(done, total, width=30):
    filled = int(width * done / total) if total else width
    return f"{C.GRN}{'█' * filled}{C.DIM}{'░' * (width - filled)}{C.R}"


def preview(text, n=70):
    t = (text or "").replace("\n", " ⏎ ").strip()
    if not t:
        return f"{C.DIM}[brak tekstu - załącznik/embed]{C.R}"
    return t if len(t) <= n else t[:n - 1] + "…"


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
    while True:
        try:
            return datetime.strptime(input(prompt).strip(), "%Y-%m-%d").replace(tzinfo=timezone.utc)
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
    """Planuje odstępy: serie szybkich akcji + długie przerwy skalowane obciążeniem."""

    def __init__(self, total, budget_s=None, manual=None):
        self.total = total
        self.budget_s = budget_s
        self.manual = manual  # (min_s, max_s) albo None
        self.start = time.time()
        self.done = 0
        self.recent = deque()
        self.slow = 1.0
        self.burst_left = random.randint(3, 6)

    def penalize(self):
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

    def long_break(self):
        base = BREAK_MIN + (BREAK_MAX - BREAK_MIN) * self.load()
        if self.budget_s:
            remaining = self.budget_s - (time.time() - self.start)
            left = self.total - self.done
            bursts_left = max(math.ceil(left / 4.5), 1)
            need = remaining - left * 6
            base = need / max(bursts_left - 1, 1) if bursts_left > 1 else BREAK_MIN
        val = base * self.slow * random.uniform(0.85, 1.15)
        return min(max(val, BREAK_MIN), BREAK_MAX)

    def next_wait(self):
        """Zwraca (sekundy, rodzaj) po zakończonej akcji."""
        if self.manual:
            lo, hi = self.manual
            return min(max(random.uniform(lo, hi) * self.slow, MIN_DELAY), MAX_DELAY), "odstęp"
        self.burst_left -= 1
        if self.burst_left <= 0:
            self.burst_left = random.randint(3, 6)
            return self.long_break(), "PRZERWA"
        return self.short_delay(), "odstęp"

    def estimate(self):
        if self.manual:
            avg = (self.manual[0] + self.manual[1]) / 2
            return self.total * avg
        if self.budget_s:
            return self.budget_s
        bursts = self.total / 4.5
        return self.total * 6 + bursts * ((BREAK_MIN + BREAK_MAX) / 2)


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
    sys.stdout.write("\r" + " " * 100 + "\r")


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
    date_from = ask_date("Data od (YYYY-MM-DD): ")
    date_to = ask_date("Data do (YYYY-MM-DD): ") + timedelta(days=1)
    mode = ask_choice("Tryb: [1] Usuń  [2] Zamień na tekst z pliku: ", ("1", "2"))

    new_text = None
    if mode == "2":
        new_text = load_text()
        include_edited = ask_yn("Zmieniać też już edytowane? (Y/N): ")
        print("\nCo robić z wiadomościami z załącznikiem/embedem (obraz, plik, podgląd linku)?")
        print("  [1] Tylko edytuj tekst (załącznik zostaje)")
        print("  [2] Usuń całą wiadomość")
        print("  [3] Pomiń takie wiadomości")
        media_choice = ask_choice("Wybór: ", ("1", "2", "3"))
    else:
        include_edited = ask_yn("Usuwać edytowane? (Y/N): ")
        media_choice = "2"

    print("\nTempo:")
    print("  [1] Normalne  - odstęp losowo 1-20 s")
    print("  [2] Auto      - serie + przerwy 6-20 min")
    print("  [3] Ręczne    - własny zakres")
    pace_mode = ask_choice("Wybór: ", ("1", "2", "3"))
    budget_s, manual = None, None
    if pace_mode == "1":
        manual = (1, 20)
    elif pace_mode == "2":
        h = ask_float("Maks. czas całości w godzinach (Enter = auto wg obciążenia): ",
                      0.1, 500, allow_empty=True)
        budget_s = h * 3600 if h else None
    else:
        lo = ask_float("Min. odstęp w sekundach (1-900): ", MIN_DELAY, MAX_DELAY)
        hi = ask_float("Maks. odstęp w sekundach (1-900): ", lo, MAX_DELAY)
        manual = (lo, hi)

    # --- zbieranie ---
    print(f"\n{C.BLU}🔍 Skanuję kanał...{C.R}")
    targets = []
    cursor = to_snowflake(date_to)
    done = False
    scanned = 0
    skipped_media = 0
    while not done:
        r = request(session, None, "GET", f"{API}/channels/{channel_id}/messages",
                    params={"limit": 100, "before": cursor})
        if r.status_code != 200:
            sys.exit(f"{C.RED}Błąd pobierania: {r.status_code} {r.text}{C.R}")
        batch = r.json()
        if not batch:
            break
        scanned += len(batch)
        for m in batch:
            ts = datetime.fromisoformat(m["timestamp"])
            if ts < date_from:
                done = True
                continue
            if m["author"]["id"] != my_id or m["type"] not in (0, 19):
                continue
            if m.get("edited_timestamp") and not include_edited:
                continue

            has_media = bool(m.get("attachments")) or bool(m.get("embeds"))
            if mode == "1":
                action = "delete"
            elif has_media and media_choice == "2":
                action = "delete"
            elif has_media and media_choice == "3":
                skipped_media += 1
                continue
            else:
                action = "edit"
                if m.get("content") == new_text:
                    continue  # już ma ten tekst

            targets.append({"id": m["id"], "content": m.get("content", ""),
                            "date": ts.astimezone().strftime("%Y-%m-%d %H:%M"),
                            "media": has_media, "action": action})
        cursor = batch[-1]["id"]
        sys.stdout.write(f"\r   przeskanowano {scanned}, pasuje {len(targets)}   ")
        sys.stdout.flush()
        time.sleep(random.uniform(0.5, 1.2))

    total = len(targets)
    n_edit = sum(1 for t in targets if t["action"] == "edit")
    n_del = total - n_edit
    n_media = sum(1 for t in targets if t["media"])
    print(f"\n\n{C.B}Znaleziono {total} wiadomości.{C.R}")
    if mode == "2":
        print(f"  do edycji: {n_edit} · do usunięcia: {n_del} · "
              f"z załącznikiem/embedem: {n_media} · pominięte (media): {skipped_media}")
    if total == 0:
        return

    pacer = Pacer(total, budget_s, manual)
    est = pacer.estimate()
    print(f"Szacowany czas: {C.B}{fmt_time(est)}{C.R} "
          f"(koniec ok. {clock(time.time() + est)})")
    if budget_s and budget_s < total * 6 + (total / 4.5 - 1) * BREAK_MIN:
        print(f"{C.YEL}⚠ Podany limit jest krótszy niż minimum przy przerwach 6 min - "
              f"skrypt zrobi to najszybciej, jak pozwalają zasady, więc może się nie zmieścić.{C.R}")

    if mode == "1":
        question = "usunąć"
    elif n_del:
        question = f"zmienić {n_edit} i USUNĄĆ {n_del} wiadomości"
    else:
        question = "zmienić na tekst z pliku"
    if not ask_yn(f"\nCzy na pewno {question}? (Y/N): "):
        print("Anulowano.")
        return
    print("Ctrl+C = bezpieczne zatrzymanie.\n")

    ok_count = fail_count = skipped = 0

    try:
        for i, t in enumerate(targets, 1):
            url = f"{API}/channels/{channel_id}/messages/{t['id']}"
            is_delete = t["action"] == "delete"
            media_tag = f" {C.MAG}📎{C.R}" if t["media"] else ""
            act_tag = f"{C.RED}USUŃ{C.R}" if is_delete else f"{C.BLU}EDYTUJ{C.R}"
            print(f"{C.CYN}{C.B}[{i}/{total}]{C.R} {bar(i - 1, total)} "
                  f"{C.DIM}{t['date']} · id {t['id']}{C.R}")
            print(f"   ✉  {preview(t['content'])}{media_tag}  → {act_tag}")

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
                nxt = f"następna: {preview(targets[i]['content'], 40)}"
                countdown(wait, kind, nxt)
                elapsed = time.time() - pacer.start
                eta = (elapsed / i) * (total - i)
                print(f"   {C.DIM}Upłynęło {fmt_time(elapsed)} · "
                      f"zostało ok. {fmt_time(eta)} · tempo ×{pacer.slow:.1f}{C.R}\n")
    except KeyboardInterrupt:
        print(f"\n\n{C.YEL}⏹ Zatrzymano przez użytkownika.{C.R}")

    print(f"\n{C.B}══════ Podsumowanie ══════{C.R}")
    print(f"{C.GRN}Sukces: {ok_count}{C.R}  {C.RED}Błędy: {fail_count}{C.R}  "
          f"{C.YEL}Pominięte: {skipped}{C.R}")
    print(f"Czas: {fmt_time(time.time() - pacer.start)}")
    print("Gotowe.")


if __name__ == "__main__":
    main()