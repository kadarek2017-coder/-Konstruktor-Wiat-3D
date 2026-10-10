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

W podglądzie wersji 7 przycisk **Wygeneruj poprawiony model** uruchamia
generator tym samym Pythonem co Streamlit i od razu wczytuje nowe pliki.
Każde wyświetlenie sprawdza geometrię OBJ, w tym orientację przekroju
czopa. Stary, błędny model jest blokowany, nawet jeśli pozostał po nim
plik `wymiary.json`. Tabela wymiarów pochodzi bezpośrednio z OBJ.

Pole **Połóż belkę płasko** przełącza przekrój między szerokością 100 mm
i wysokością 200 mm a szerokością 200 mm i wysokością 100 mm. Zmiana
automatycznie generuje dopasowany czop i gniazdo. Oś belki pozostaje na
Z=2200 mm; płaska belka ma spód na 2150 mm, a koniec czopa na 2250 mm.
Czop ma wtedy 150 × 66,67 mm i długość 100 mm.

Suwak **Uniesienie belki** w widoku 3D przesuwa belkę o 0–500 mm w osi Z.
**Rozsuń elementy** ustawia 350 mm, a **Złóż połączenie** przywraca 0 mm.
Rozsuwanie służy do oglądania czopa i gniazda; nie zmienia plików OBJ.
Belkę płasko można wygenerować także poleceniem:

```bash
python testy_kumiki/generuj_czop.py --flat
```

## Pełna rama i przesuwanie elementów

Opcja **Pełna rama** tworzy dwa słupy 200 × 200 mm w rozstawie osiowym
2400 mm i jedną belkę długości 3000 mm. Belka ma dwa rzeczywiste gniazda.
Można ją ustawić na sztorc lub płasko. Podgląd jest dostępny także
przez link **Rama z rzeczywistymi połączeniami** w głównej aplikacji.
Ta strona wymaga osobnych zależności z tego folderu; rama pozostaje
odrębnym modelem i nie zmienia jeszcze pełnej wiaty.

- Kliknij słup lub belkę albo wybierz nazwę w polu **Element**.
- Chwyć sam słup lub belkę lewym przyciskiem i przeciągnij. Element przesuwa się
  w płaszczyźnie ekranu, bez przeskoku do środka i bez obracania kamery.
- Przeciągnięcie tła obraca kamerę; rolka przybliża, prawy przycisk przesuwa widok.
- Opcjonalnie włącz **Strzałki do precyzyjnego przesuwania**, aby przesuwać
  element w wybranej osi X, Y lub Z.
- Pola X/Y/Z pokazują przesunięcie względem pozycji złożonej, w mm.
- **Przywróć element** zeruje jego przesunięcie.
- **Ukryj element** usuwa go z widoku. Ponowny wybór pokazuje go z powrotem.
- **Złóż całą ramę** przywraca pozycje i widoczność wszystkich elementów.
- **Pobierz element OBJ** zapisuje wybraną geometrię z aktualnym przesunięciem
  w milimetrach, bez przesunięcia kamery używanego do centrowania widoku.

Przesuwanie i ukrywanie nie zmienia źródłowych plików ani dopasowania
połączeń. Odświeżenie widoku przywraca złożoną ramę.

```bash
python testy_kumiki/generuj_czop.py --frame
python testy_kumiki/generuj_czop.py --frame --flat
```

## Szkielet przestrzenny

Włącz **Szkielet przestrzenny — dwie ramy i belki łączące**.
Model zawiera cztery słupy, dwie belki ram długości 3000 mm i dwie
belki łączące w osi Y. Ramy mają rozstaw 3000 mm, a słupy każdej ramy
rozstaw 2400 mm. Każdy element można chwycić i przeciągnąć osobno,
ukryć, przywrócić lub pobrać jako OBJ.

Obie ramy mają rzeczywiste czopy i gniazda. Belki łączące leżą na
belkach ram, z równym końcem na zewnętrznych krawędziach podpór:
mają długość 3100 mm na sztorc albo 3200 mm płasko. Nie mają jeszcze
wycięć ani łączników. Miecze i krokwie będą dodane w kolejnych etapach.
Suwak uniesienia podnosi wszystkie belki razem; przeciąganie pozostaje
niezależne dla każdego elementu. To model poglądowy, nie ukończony
projekt wykonawczy.

```bash
python testy_kumiki/generuj_czop.py --skeleton
python testy_kumiki/generuj_czop.py --skeleton --flat
```

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
