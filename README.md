# Bluetooth Oximeter Integration for Home Assistant

Eine Home Assistant Integration für Bluetooth Pulsoximeter.

## Features

- **Echtzeit-Überwachung** - SpO₂, Pulsfrequenz und Perfusionsindex
- **Automatische Erkennung** - Findet kompatible Geräte via Bluetooth
- **Bluetooth Proxys** - Nutzt ESPHome Bluetooth Proxys für größere Reichweite
- **Diagnostics** - Umfangreiche Debug-Informationen für Fehlersuche
- **Mehrsprachig** - Deutsch und Englisch
- **Energiesparend** - Geht schonend mit den Gerätebatterien um

## Unterstützte Geräte

- **JKS50F** (Guangdong Health Medical Technology Co., Ltd.)

## Installation

### Via HACS (Empfohlen)

1. HACS öffnen → **Integrations**
2. **⋮** (Menü oben rechts) → **Custom repositories**
3. Repository hinzufügen:
   ```
   Repository: https://github.com/Boerni89/ha_bt_oximeter
   Category: Integration
   ```
4. **Bluetooth Oximeter** suchen und installieren
5. Home Assistant neu starten

### Manuelle Installation

1. `bt_oximeter` Ordner nach `custom_components/` kopieren
2. Home Assistant neu starten

## Einrichtung

1. **Oximeter einschalten**
2. In Home Assistant: **Einstellungen** → **Geräte & Dienste** → **Integration hinzufügen**
3. Nach **"Bluetooth Oximeter"** suchen
4. Gerätemodell aus der Liste auswählen
5. Gerätename und MAC-Adresse bestätigen
6. Fertig! Die Sensoren werden automatisch erstellt.

> **Tipp:** Für bessere Reichweite können [ESPHome Bluetooth Proxys](https://esphome.io/components/bluetooth_proxy.html) verwendet werden.

## Sensoren

Nach der Einrichtung werden folgende Entitäten erstellt:

### Messwerte
- **SpO₂ (Sauerstoffsättigung)** - in Prozent (%)
- **Pulsfrequenz** - Schläge pro Minute (BPM)
- **Perfusionsindex** - in Prozent (%)

### Status
- **Finger erkannt** - An, wenn der Finger korrekt eingeführt ist

> **Hinweis:** Alle Sensoren zeigen "Nicht verfügbar", wenn keine gültigen Messwerte empfangen werden (z.B. wenn das Gerät ausgeschaltet ist).

## Diagnostics

Für die Fehlersuche können umfangreiche Diagnostics-Daten heruntergeladen werden:

1. **Einstellungen** → **Geräte & Dienste**
2. Dein Oximeter auswählen
3. **⋮** (Menü) → **Diagnostics herunterladen**

Die Diagnostics enthalten:
- Buffer-Status und rohe BLE-Daten
- Connection-Status
- Letzte Messwerte
- Bluetooth-Geräteinformationen

## Fehlerbehebung

### Gerät wird nicht gefunden
- Oximeter einschalten und warten bis es bereit ist
- Bluetooth am Home Assistant Host aktivieren
- Gerät darf nicht mit einer anderen App verbunden sein
- Näher an den Bluetooth-Adapter gehen

### Verbindung schlägt fehl
- Gerät von anderen Apps trennen (z.B. Hersteller-App)
- Bluetooth-Signal verbessern (näher gehen)
- Home Assistant neu starten

## Lizenz

MIT License - siehe [LICENSE](LICENSE) Datei
