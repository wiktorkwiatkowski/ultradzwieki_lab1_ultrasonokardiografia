# Ultradźwięki – lab 1: ultrasonokardiografia

Sprawozdanie w LaTeX-u. Projekt jest połączony z Overleafem przez GitHuba
(gałąź `main`).

## Struktura

| Ścieżka | Zawartość |
|---|---|
| `main.tex` | treść sprawozdania |
| `obliczenia.xlsx` | **wszystkie obliczenia i wykresy** (pomiary, układ OX, RMSE) – oddajemy prowadzącemu |
| `obliczenia.py` | eksport wyników z Excela do `tabele/` |
| `tabele/` | tabele (`.tex`) i wykresy (`wykresy.pdf`) generowane z Excela – **nie edytować ręcznie** |
| `img/` | rysunki i zdjęcia z USG użyte w sprawozdaniu |
| `materialy/` | rzeczywiste pomiary zastawki (PDF) i surowe zdjęcia z USG |

## Edycja tekstu (Overleaf)

1. W Overleafie: *Menu → GitHub → Pull GitHub changes into Overleaf*, żeby mieć
   najnowszą wersję.
2. Edytuj `main.tex`.
3. *Menu → GitHub → Push Overleaf changes to GitHub*.

Overleaf nie uruchomi skryptu, dlatego `tabele/` są w repo. Obliczeń nie zmieniamy
w Overleafie.

## Zmiana obliczeń (lokalnie)

Potrzebne: Python 3.9+, LibreOffice (skrypt używa go do przeliczenia formuł;
sam Excel do edycji wystarczy, ale do eksportu potrzebny jest LibreOffice) i git.

1. `git pull`
2. Otwórz `obliczenia.xlsx` (Excel lub LibreOffice) i popraw dane wejściowe
   w arkuszach przypadków: rzeczywiste `y` oraz odczyty `Δy` z fantomu.
   Pozostałe komórki to formuły – nie nadpisuj ich. Zapisz jako `.xlsx`.
3. Wygeneruj tabele i wykresy:
   ```bash
   python3 obliczenia.py
   ```
   (na Windows: `py obliczenia.py`)
4. Sprawdź `git diff`. **Liczby w tekście** (np. RMSE w sekcjach z omówieniem
   i we wnioskach) są wpisane ręcznie w `main.tex` – popraw je, jeśli się zmieniły.
5. `git add obliczenia.xlsx tabele main.tex`, commit, `git push`, potem
   *Pull* w Overleafie.

Najmniejszy RMSE jest pogrubiony w arkuszu `Podsumowanie` i w wierszach RMSE arkuszy
przypadków (formatowanie warunkowe) oraz w tabelach w sprawozdaniu (wg tej samej reguły).

## Kompilacja lokalnie (opcjonalnie)

```bash
podman run --rm -v "$PWD":/work:Z -w /work docker.io/texlive/texlive:latest latexmk -pdf main.tex
```
