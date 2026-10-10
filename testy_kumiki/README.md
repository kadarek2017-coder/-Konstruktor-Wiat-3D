# Połączenie czop–gniazdo w Kumiki

Oddzielny podgląd geometrii; główna aplikacja wiaty nie korzysta jeszcze z tego węzła.
Testowana wersja: Kumiki 0.8.0, Python 3.12.

## Uruchomienie na Macu

W folderze repozytorium:

```bash
python3 -m venv .venv-kumiki
source .venv-kumiki/bin/activate
python -m pip install -r testy_kumiki/requirements.txt
python testy_kumiki/generuj_czop.py
python -m streamlit run testy_kumiki/podglad_obj.py
```

Jeśli środowisko już istnieje, zacznij od polecenia `source`.

## Jednostki i położenie

Kumiki otrzymuje wymiary w **metrach**, przez `k.mm(...)`.
Eksport OBJ jest przeliczany na **milimetry** przed zapisaniem w `wyniki/`.
Podgląd wczytuje te same zweryfikowane pliki. Nie korzysta z wcześniejszego
katalogu eksperymentalnego `finite_joint` ani z modyfikacji prywatnych pól CSG.

- Słup: przekrój 200 × 200 mm, podstawa Z=0.
- Belka: długość 1600 mm w osi X, szerokość 100 mm w osi Y,
  wysokość 200 mm w osi Z.
- Oś belki: Z=2200 mm. Jej spód i bark słupa: Z=2100 mm.
- Koniec czopa: Z=2300 mm; to całkowita wysokość wyciętego słupa.
  Nominalne `length=2200 mm` w tym teście określa położenie węzła,
  a Kumiki przedłuża czop do góry belki.
- Czop ma 150 mm w osi X (wzdłuż belki) i 33,33 mm w osi Y.
  Gniazdo pozostawia pełne ścianki po obu stronach szerokości belki.
  Wymiary są przekazywane jawnie, ponieważ automatyczny wrapper Kumiki
  zamieniał osie czopa i otwierał gniazdo na boki belki.

Poprzedni skrypt przekazywał milimetry jako metry. Przy nieskończonym końcu
bryły triangulator stosował ograniczenie 1000 jednostek, przez co OBJ słupa
kończył się przed węzłem. Przeliczenie jednostek usuwa przyczynę problemu.

Eksport sprawdza wymiary, położenie, zamknięcie i ubytek objętości brył.
`wymiary.json` zapisuje wynik kontroli. Podgląd pokazuje wymiary i używa
pionowej osi Z. Wyniki i środowisko są pomijane przez Git.

## Test regresji

```bash
python -m unittest testy_kumiki.test_geometria -v
```

Test odczytuje zapisane pliki OBJ, sprawdza ich wymiary i objętości po
wycięciu, brak kolizji, orientację przekroju czopa oraz zamknięty obrys
gniazda na poziomie osi belki.

Geometria służy do podglądu. Wymiary połączenia i nośność wymagają
niezależnej weryfikacji projektowej przed wykonaniem konstrukcji.
