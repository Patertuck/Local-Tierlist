# Local Tierlist

## Über das Projekt

Dies ist eine vibe-gecodete Tierlisten-App für gemeinsame Tierlisten mit meiner Freundin. Sie ist besonders für Künstler, Songs, Alben und andere persönliche Favoriten gedacht, funktioniert aber mit beliebigen Dingen.

Die App läuft lokal, speichert alle Änderungen als JSON und bietet mehrere Tierlisten mit einem gemeinsamen Element-Katalog.

## Starten

Doppelklicke auf `run.bat` und öffne anschließend <http://127.0.0.1:8000> im Browser.

Alternativ:

```powershell
python server.py
```

Die Tierliste wird in `tierlist.json` neben dem Programm gespeichert. Änderungen werden automatisch nach jeder Aktion gespeichert.

## Funktionen

- Elemente über das Eingabefeld hinzufügen.
- Elemente zwischen Reihen verschieben oder innerhalb einer Reihe neu anordnen.
- Ein Element doppelt anklicken, um es umzubenennen.
- Auf `×` klicken, um ein Element zu löschen.
- Ein Reihenlabel anklicken, um Name und Farbe zu ändern.
- Reihen mit den Pfeilen neu anordnen.
- Mit `+ Reihe hinzufügen` neue Reihen erstellen.
- Gelöschte Reihen verschieben ihre Elemente in „Nicht zugeordnet“.
- Mehrere Tierlisten als Tabs verwalten und mit `Strg + ←/→` wechseln.
- Eine Tierliste als PNG exportieren.
