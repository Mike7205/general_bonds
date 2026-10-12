# general_bonds

Fork / pełna kopia **Mike7205/General_F2** (Global Economy Multivariate NN D+5 Forecast Dashboard) z dodatkową zakładką poświęconą polskim obligacjom skarbowym.

## Struktura

- `Fore2.py` – entry point (nawigacja: Forecast Desktop, Tech Analytical Desktop, **Obligacje Skarbowe**)
- `pages/Bonds_Desktop.py` – nowa strona: lista obligacji notowanych + detalicznych, planowane przetargi (najbliższe ~3 kwartały), cena / rentowność, sekcja inflacyjna dla COI/EDO/ROS/ROD
- Pozostałe pliki skopiowane z General_F2 (LSTM forecast, news buckets, Tech Analytical Desktop)

## Uruchomienie

```bash
pip install -r requirements.txt
streamlit run Fore2.py
```

Wymagane sekrety Streamlit (jak w oryginale): `XAI_API_KEY` dla części LLM.

## Uwagi do zakładki obligacji

- Lista zawiera przykładowe serie hurtowe (DS, PS, OK, NZ, IZ) oraz aktualną ofertę detaliczną (OTS, ROR, DOR, TOS, COI, EDO, ROS, ROD).
- Planowane przetargi na podstawie publicznego kalendarza MF (październik 2026 i kolejne miesiące).
- Dla obligacji indeksowanych inflacją pokazywana jest marża nad CPI i szacunkowe bieżące oprocentowanie.
- Historia cen: yfinance ma ograniczone pokrycie polskich obligacji – strona jest przygotowana pod podłączenie lepszego źródła (Catalyst, Notoria, BondSpot lub własne CSV).

Dane orientacyjne, nie stanowią porady inwestycyjnej.
