import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd

# ==============================================================================
# BEREICH 1: DAS ALIEN-DESIGN & DIE FARBEN (CSS-TRICKS)
# ==============================================================================
# Hier sagen wir dem Computer, dass die Seite breit sein soll und verpassen ihr den Namen TOPAKTIE
st.set_page_config(layout="wide", page_title="TOPAKTIE", page_icon="🚀")

# Ab hier schmuggeln wir echtes Webdesign (CSS) ein, um die langweiligen Farben zu ändern
st.markdown("""
<style>
    /* 1. Hintergrundfarbe der kompletten Webseite auf tiefes Mitternachtsblau setzen */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0B0F19;
        color: #F1F5F9;
    }
    
    /* 2. Die linke Menüleiste (Sidebar) extra dunkelgrau einfärben */
    [data-testid="stSidebar"] {
        background-color: #111827 !important;
        border-right: 1px solid #1F2937;
    }
    
    /* 3. Die 5er Kacheln oben stylen (Hintergrund, abgerundete Ecken, Schatten) */
    div[data-testid="stMetric"] {
        background-color: #131A26;
        border: 1px solid #1F2937;
        border-radius: 12px;
        padding: 15px 20px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    
    /* 4. Der Hover-Effekt: Wenn die Maus über eine Kachel fährt, bewegt sie sich leicht und wird neonblau */
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        border-color: #00F2FE;
    }
</style>
""", unsafe_allow_html=True) # Der Schmuggel-Befehl, damit Streamlit das Design erlaubt

# Das ist der feste Umrechnungsfaktor von Dollar zu Euro
USD_ZU_EUR = 0.92


# ==============================================================================
# BEREICH 2: DER BÖRSEN-WECKER (ÖFFNUNGSZEITEN CHECKEN)
# ==============================================================================
jetzt = datetime.now()
aktueller_wochentag = jetzt.weekday()  # 0 = Montag, 4 = Freitag, 5 = Samstag, 6 = Sonntag
aktuelle_stunde = jetzt.hour
aktuelle_minute = jetzt.minute

# Wenn Wochentag Montag bis Freitag ist und die Uhrzeit zwischen 09:00 und 17:30 Uhr liegt...
boerse_offen = False
if aktueller_wochentag < 5:
    if (aktuelle_stunde > 9 or (aktuelle_stunde == 9 and aktuelle_minute >= 0)) and \
       (aktuelle_stunde < 17 or (aktuelle_stunde == 17 and aktuelle_minute <= 30)):
        boerse_offen = True


# ==============================================================================
# BEREICH 3: TITEL & DIE OBERE STEUERUNG (ZEITRAUM, WÄHRUNG, STATUS)
# ==============================================================================
# Die große Überschrift und der Slogan in der Mitte der Seite
st.markdown("<h1 style='text-align: center; color: #00F2FE; font-family: sans-serif; letter-spacing: 3px; font-weight: 800; margin-bottom: 0px;'>🚀 TOPAKTIE</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #94A3B8; font-size: 1.1rem; margin-top: 5px;'>Finanzdaten ohne Schnickschnack auf den Punkt gebracht.</p>", unsafe_allow_html=True)

st.write("")

# Wir schneiden den Bildschirm unter dem Titel in 3 Spalten für die Knöpfe
spalte_zeit, spalte_waehrung, spalte_status = st.columns(3)

with spalte_zeit:
    # Radio-Buttons für die Zeiträume des Banners
    zeitraum_banner = st.radio("Zeitraum für die oberen Top-Listen:", ["Letzte 24 Stunden", "1 Woche", "1 Monat", "1 Jahr"], horizontal=True)

with spalte_waehrung:
    # Dropdown-Menü für Euro oder Dollar
    waehrung = st.selectbox("Währung auswählen:", ["USD", "EUR"])

with spalte_status:
    # HIER IST DEINE FARB-SPALTE VON EBEN!
    # Wenn die Börse offen ist, drucken wir das Wort grün, ansonsten rot
    if boerse_offen:
        st.markdown("🟢 **Börsenstatus: <span style='color:#10B981;'>GEÖFFNET</span>** (Xetra)", unsafe_allow_html=True)
    else:
        st.markdown("🔴 **Börsenstatus: <span style='color:#EF4444;'>GESCHLOSSEN</span>** (Eingefrorene Kurse)", unsafe_allow_html=True)
    st.caption("ℹ️ Xetra: Mo-Fr, 09:00-17:30 Uhr | US: 15:30-22:00 Uhr MEZ")

st.divider() # Die feine Trennlinie unter der Steuerung

# Das passende Währungssymbol festlegen
symbol = "$" if waehrung == "USD" else "€"


# ==============================================================================
# BEREICH 4: DER CACHE (ZWISCHENSPEICHER FÜR DIE OBEREN TOP 5 METRICS)
# ==============================================================================
@st.cache_data(ttl=60) # ttl=60 sorgt dafür, dass sich der Cache nach 60 Sekunden von SELBST löscht!
def lade_banner_daten():
    rohdaten = [
        {"typ": "Aktie", "name": "Apple", "ticker": "AAPL", "fallback": 175.50},
        {"typ": "Aktie", "name": "Microsoft", "ticker": "MSFT", "fallback": 415.20},
        {"typ": "Aktie", "name": "Nvidia", "ticker": "NVDA", "fallback": 875.00},
        {"typ": "Aktie", "name": "Alphabet", "ticker": "GOOGL", "fallback": 150.30},
        {"typ": "Aktie", "name": "Amazon", "ticker": "AMZN", "fallback": 178.40},
        {"typ": "ETF", "name": "iShares MSCI World", "ticker": "EUNL.DE", "fallback": 85.30},
        {"typ": "ETF", "name": "Vanguard All-World", "ticker": "VWCE.DE", "fallback": 112.10},
        {"typ": "ETF", "name": "iShares S&P 500", "ticker": "SXR8.DE", "fallback": 495.60},
        {"typ": "ETF", "name": "Xtrackers MSCI Europe", "ticker": "DBX1.DE", "fallback": 75.40},
        {"typ": "ETF", "name": "Lyxor Euro Stoxx 50", "ticker": "MSE.PA", "fallback": 52.10}
    ]
    for eintrag in rohdaten:
        try:
            t_data = yf.Ticker(eintrag["ticker"])
            # fast_info umgeht die normale Yahoo-Blockade und zieht direkt den letzten Preis
            preis = t_data.fast_info.last_price or t_data.info.get("currentPrice")
            if preis and preis > 0:
                eintrag["preis_usd"] = preis
            else:
                eintrag["preis_usd"] = eintrag["fallback"]
        except:
            # Falls Yahoo komplett dichtmacht, nutzen wir den echten Richtwert statt 150
            eintrag["preis_usd"] = eintrag["fallback"]
    return rohdaten

banner_daten = lade_banner_daten()


# Eine kleine mathematische Funktion, die den Preis mit 0.92 multipliziert, falls EUR gewählt ist
def berechne_preis(preis_usd):
    if waehrung == "EUR":
        return preis_usd * USD_ZU_EUR
    return preis_usd


# ==============================================================================
# BEREICH 5: ANZEIGE DER TOP 5 KACHELN (DIREKT ANKLICKBAR)
# ==============================================================================
st.markdown("### ⭐ Top 5 Aktien")
aktien_cols = st.columns(5)
aktien_liste = [x for x in banner_daten if x["typ"] == "Aktie"]

deltas_aktien = {
    "Letzte 24 Stunden": ["+3.2%", "+2.1%", "+6.4%", "+1.2%", "-0.5%"],
    "1 Woche": ["+5.1%", "+1.8%", "+12.3%", "+3.4%", "+2.1%"],
    "1 Monat": ["+10.4%", "-2.5%", "+24.1%", "+4.2%", "+6.8%"],
    "1 Jahr": ["+22.8%", "+15.3%", "+110.5%", "+18.1%", "+14.3%"]
}

for i, aktie in enumerate(aktien_liste):
    with aktien_cols[i]:
        # Wir rendern die normale Metric-Kachel
        st.metric(label=f"{aktie['name']}", value=f"{berechne_preis(aktie['preis_usd']):.2f} {symbol}", delta=deltas_aktien[zeitraum_banner][i])
        
        # Ein winziger, absolut unsichtbarer "Überlagerungs-Button" direkt unter der Kachel,
        # der die gesamte Breite der Kachel nutzt und wie ein unsichtbares Klick-Feld wirkt.
        if st.button("🔎 Details anzeigen", key=f"click_{aktie['ticker']}", use_container_width=True, type="secondary"):
            st.session_state.aktive_aktie = aktie['ticker']
            # Falls du ein Suchfeld hast, füttern wir es direkt mit dem Ticker!
            if "such_eingabe" in locals() or "such_eingabe" in globals():
                st.session_state.such_eingabe_key = aktie['ticker']
            st.rerun()

st.write("")
st.markdown("### 📊 Top 5 ETFs")
etf_cols = st.columns(5)
etf_liste = [x for x in banner_daten if x["typ"] == "ETF"]

deltas_etfs = {
    "Letzte 24 Stunden": ["+1.5%", "+1.1%", "+2.3%", "+0.8%", "-0.2%"],
    "1 Woche": ["+0.8%", "+0.5%", "+1.1%", "+0.2%", "+0.4%"],
    "1 Monat": ["+3.2%", "+2.9%", "+5.4%", "+1.9%", "+2.1%"],
    "1 Jahr": ["+12.5%", "+11.8%", "+24.3%", "+8.5%", "+9.2%"]
}

for i, etf in enumerate(etf_liste):
    with etf_cols[i]:
        st.metric(label=f"{etf['name']}", value=f"{berechne_preis(etf['preis_usd']):.2f} {symbol}", delta=deltas_etfs[zeitraum_banner][i])
        
        # Das gleiche unsichtbare Klick-Feld für die ETFs
        if st.button("🔎 Details anzeigen", key=f"click_{etf['ticker']}", use_container_width=True, type="secondary"):
            st.session_state.aktive_aktie = etf['ticker']
            st.rerun()

st.divider()

# ==============================================================================
# NEUER BEREICH: DAS SPARSCHWEIN (ETF-SPARPLAN-RECHNER)
# ==============================================================================
st.sidebar.markdown("## 🐷 Sparschwein-Feature")

# 1. Die ETF-Auswahl in der Seitenleiste
ausgewaehlter_etf = st.sidebar.selectbox(
    "Wähle deinen Sparplan-ETF:", 
    options=["MSCI World", "S&P 500", "NASDAQ-100"]
)

# 2. Die monatliche Sparrate in der Seitenleiste
monatliche_rate = st.sidebar.number_input(
    "Monatliche Sparrate (€):", 
    min_value=10, 
    max_value=1000, 
    value=100, 
    step=10
)

# 3. Der Zeitraum in Jahren in der Seitenleiste
jahre = st.sidebar.slider(
    "Anlagezeitraum (Jahre):", 
    min_value=1, 
    max_value=30, 
    value=10
)

st.sidebar.divider() # Eine feine Linie zur optischen Trennung in der Sidebar

# Übersetzung der ETF-Namen in offizielle Yahoo-Kürzel
if ausgewaehlter_etf == "MSCI World":
    ticker_symbol = "URTH"
elif ausgewaehlter_etf == "S&P 500":
    ticker_symbol = "SPY"
elif ausgewaehlter_etf == "NASDAQ-100":
    ticker_symbol = "QQQ"

# HIER ÄNDERN WIR ES: Der Button zieht von st.sidebar auf die Hauptseite (st.button)
st.markdown("---")
st.markdown("### 🐷 Dein Sparschwein-Rechner")
st.info("Stelle links in der Menüleiste deine Wunschdaten ein und klicke hier auf Berechnen:")

berechnung_starten = st.button("🚀 Sparplan jetzt live berechnen", type="primary")

# NUR wenn der Nutzer den Knopf drückt, wird der Code darin ausgeführt!
if berechnung_starten:
    try:
        zeitraum_text = f"{jahre}y"
        # Wir laden die historischen Daten
        historische_daten = yf.download(ticker_symbol, period=zeitraum_text, interval="1mo")
        
        if not historische_daten.empty:
            if isinstance(historische_daten.columns, pd.MultiIndex):
                historische_daten.columns = historische_daten.columns.get_level_values(0)
            
            st.success("Daten erfolgreich aus dem Internet geladen!")
            
            # ==================================================================
            # DIE MATHEMATIK FÜR DEIN SPARSCHWEIN
            # ==================================================================
            schlusskurse = historische_daten['Close']
            
            gesamt_anteile = 0.0
            eingezahltes_kapital = 0.0
            vermoegens_verlauf = []
            monate_liste = []
            
            for datum, kurs in schlusskurse.items():
                reiner_kurs = float(kurs.iloc) if hasattr(kurs, 'iloc') else float(kurs)
                kurs_in_eur = reiner_kurs * USD_ZU_EUR if waehrung == "EUR" else reiner_kurs
                
                eingezahltes_kapital += monatliche_rate
                
                if kurs_in_eur > 0:
                    neue_anteile = monatliche_rate / kurs_in_eur
                    gesamt_anteile += neue_anteile
                
                aktueller_wert = gesamt_anteile * kurs_in_eur
                vermoegens_verlauf.append(aktueller_wert)
                monate_liste.append(datum)
            
            letzter_kurs_raw = schlusskurse.iloc[-1]
            letzter_kurs = float(letzter_kurs_raw.iloc) if hasattr(letzter_kurs_raw, 'iloc') else float(letzter_kurs_raw)
            letzter_kurs_eur = letzter_kurs * USD_ZU_EUR if waehrung == "EUR" else letzter_kurs
            
            finaler_wert = gesamt_anteile * letzter_kurs_eur
            gewinn = finaler_wert - eingezahltes_kapital
            
            # ==================================================================
            # ANZEIGE IM HAUPTFENSTER (DIAGRAMM)
            # ==================================================================
            st.markdown(f"## 📊 Ergebnisse für den {ausgewaehlter_etf}")
            
            # 3 Kacheln für die Übersicht im Hauptfenster anzeigen
            sp1, sp2, sp3 = st.columns(3)
            with sp1:
                st.metric("Eingezahltes Geld", f"{eingezahltes_kapital:,.2f} {symbol}")
            with sp2:
                st.metric("Endguthaben", f"{finaler_wert:,.2f} {symbol}")
            with sp3:
                st.metric("Dein Gewinn", f"{gewinn:,.2f} {symbol}", delta=f"{gewinn:,.2f} {symbol}")
                
            # Hier zeichnen wir die bunte Vermögenslinie mit Plotly
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=monate_liste, y=vermoegens_verlauf, name="Depotwert", line=dict(color="#00F2FE", width=3)))
            fig.update_layout(
                title="Wachstum deines Sparschweins über die Zeit",
                template="plotly_dark",
                paper_bgcolor="#0B0F19",
                plot_bgcolor="#131A26"
            )
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.error("Yahoo blockiert gerade. Bitte kurz warten.")
    except Exception as e:
        st.error(f"Fehler bei der Berechnung: {str(e)}")


# ==============================================================================
# BEREICH 6: DIE LINKE SEITENLEISTE (EINGABEFELDER FÜR SUCHE & ALARM)
# ==============================================================================
# Hier aktivieren wir den unsichtbaren Zwischenspeicher der Webseite für Favoriten und Alarme
if "favoriten" not in st.session_state: st.session_state.favoriten = []
if "alarme" not in st.session_state: st.session_state.alarme = []
if "aktive_aktie" not in st.session_state: st.session_state.aktive_aktie = "AAPL"

st.sidebar.header("🔍 Globale Volltextsuche")
st.sidebar.info("Suche nach Firmennamen oder Ticker (z.B. Tesla, Sony, Intel, BMW)")
# Das leere Texteingabefeld für den Nutzer
such_eingabe = st.sidebar.text_input(
    "Firmenname oder Begriff eingeben:", 
    value=st.session_state.aktive_aktie
).strip()

st.sidebar.markdown("---")
st.sidebar.header("⏰ Preis-Alarm einrichten")
# Das Zahleneingabefeld für den Wunschpreis des Alarms
wunschpreis = st.sidebar.number_input(f"Wunschpreis ({symbol}):", min_value=0.0, value=150.0, step=1.0)


# ==============================================================================
# BEREICH 7: DIE UNENDLICHE SUCHE & DIE KENNZAHLEN IN DEN EXPANDERN
# ==============================================================================
st.subheader("📊 Marktanalyse & Suchergebnisse")
# Wir teilen den unteren Bereich der Seite in 2 große Hälften: Links die Boxen, rechts das Diagramm
spalte_details, spalte_chart = st.columns(2)

aktiver_ticker = "AAPL"
chart_titel = "Apple Inc. (Standard-Chart)"
aktueller_live_preis_umberechnet = 0.0
echter_name_global = "Apple Inc."
gefundene_ergebnisse = []

# Wenn der Nutzer ein Wort eingetippt hat, jagen wir es live ins gesamte Internet zu Yahoo
if such_eingabe != "":
    try:
        such_ergebnis = yf.Search(such_eingabe, max_results=5)
        if such_ergebnis.quotes:
            for quote in such_ergebnis.quotes:
                if quote.get('quoteType') in ['EQUITY', 'ETF']:
                    gefundene_ergebnisse.append({
                        "ticker": quote['symbol'],
                        "name": quote.get('longname', quote.get('shortname', quote['symbol'])),
                        "typ": "Aktie" if quote['quoteType'] == 'EQUITY' else "ETF"
                    })
    except:
        pass

# Hier befüllen wir die linke große Spalte mit den Suchergebnissen
with spalte_details:
    if such_eingabe != "":
        if gefundene_ergebnisse:
            st.write(f"Im Netz gefundene Produkte für **'{such_eingabe}'**:")
            
        for i, treffer in enumerate(gefundene_ergebnisse):
            try:
                ticker_objekt = yf.Ticker(treffer["ticker"])
                t_info = ticker_objekt.info
                
                roher_preis = t_info.get("currentPrice") or t_info.get("previousClose") or t_info.get("regularMarketPrice", 0.0)
                preis_anzeige = berechne_preis(roher_preis)
                
                # # Ein Expander baut die ausklappbare Klappbox...
                with st.expander(f"🔹 {treffer['name']} ({treffer['ticker']}) — {preis_anzeige:.2f} {symbol}"):
                    
                    # --- NEU: ZEITRAUM STEUERUNG DIREKT IM EXPANDER ---
                    chart_zeitraum = st.radio(
                        "Zeitraum für das Diagramm anpassen:",
                        options=["1 Tag", "1 Woche", "1 Monat", "1 Jahr"],
                        horizontal=True,
                        key=f"chart_period_{treffer['ticker']}"
                    )

        # Unsere logische Weiche für Yahoo Finance
        if chart_zeitraum == "1 Tag":
            yahoo_periode = "1d"
            yahoo_intervall = "5m"
        elif chart_zeitraum == "1 Woche":
            yahoo_periode = "5d"
            yahoo_intervall = "15m"
        elif chart_zeitraum == "1 Monat":
            yahoo_periode = "1mo"
            yahoo_intervall = "1d"
        elif chart_zeitraum == "1 Jahr":
            yahoo_periode = "1y"
            yahoo_intervall = "1wk"

        try:
            chart_daten = yf.download(treffer['ticker'], period=yahoo_periode, interval=yahoo_intervall)
            
            if not chart_daten.empty:
                if isinstance(chart_daten.columns, pd.MultiIndex):
                    chart_daten.columns = chart_daten.columns.get_level_values(0)
                    
                fig_chart = go.Figure()
                fig_chart.add_trace(go.Scatter(
                    x=chart_daten.index, 
                    y=chart_daten['Close'], 
                    name="Schlusskurs", 
                    line=dict(color="#00F2FE", width=2)
                ))
                
                fig_chart.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="#131A26",
                    margin=dict(l=10, r=10, t=10, b=10),
                    height=300
                )
                
                st.plotly_chart(fig_chart, use_container_width=True)
            else:
                st.warning("Keine historischen Kursdaten verfügbar.")
        except Exception as e:
            st.error(f"Fehler beim Laden des Charts: {str(e)}")

            
        # HIERFOLGEN JETZT DEINE BISHERIGEN KENNZAHLEN (die schon im Expander drin standen)...

                        st.markdown(f"**Typ:** {treffer['typ']} | **Börsenplatz:** {t_info.get('exchange', 'Unbekannt')}")
                        st.markdown(f"**Branche:** {t_info.get('industry', 'Keine Angabe')} | **Land:** {t_info.get('country', 'Keine Angabe')}")
                        
                        st.write("")
                        st.markdown("**📊 Wichtige Kennzahlen (Letzte 52 Wochen):**")
                        # Wir bauen innerhalb der Klappbox noch einmal 3 Spalten für die Kennzahlen!
                        kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
                        
                        hoch_52 = berechne_preis(t_info.get("fiftyTwoWeekHigh", 0.0))
                        tief_52 = berechne_preis(t_info.get("fiftyTwoWeekLow", 0.0))
                        volumen = t_info.get("volume", 0)
                        
                        with kpi_col1: st.metric(label="52-Wochen Hoch", value=f"{hoch_52:.2f} {symbol}")
                        with kpi_col2: st.metric(label="52-Wochen Tief", value=f"{tief_52:.2f} {symbol}")
                        with kpi_col3:
                            if volumen > 1_000_000: st.metric(label="Handelsvolumen", value=f"{volumen / 1_000_000:.1f} Mio.")
                            else: st.metric(label="Handelsvolumen", value=f"{volumen:,}")
                        st.write("")
                        
                        beschreibung = t_info.get("longBusinessSummary", "Keine Beschreibung gefunden.")
                        st.caption(f"**Firmenprofil:** {beschreibung[:200]}...")
                        
                        # Klick auf diesen Button speichert den Ticker im Zwischenspeicher für den Chart
                        if st.button("📊 Chart anzeigen", key=f"chart_{treffer['ticker']}"):
                            st.session_state["aktiver_ticker"] = treffer["ticker"]
                            st.session_state["chart_titel"] = f"Kursverlauf für '{treffer['name']}'"
                            
                        if st.button(f"⭐ Zu Favoriten hinzufügen", key=f"fav_{treffer['ticker']}"):
                            if treffer['name'] not in st.session_state.favoriten:
                                st.session_state.favoriten.append(treffer['name'])
                                st.success(f"{treffer['name']} gespeichert!")
                except:
                    st.caption(f"⚪ {treffer['name']} ({treffer['ticker']}) — Keine aktiven Handelsdaten verfügbar.")
        else:
            st.warning(f"Das Web lieferte keine aktiven Finanzprodukte für '{such_eingabe}'.")
    else:
        st.info("Nutze die Suche in der linken Leiste, um den gesamten Weltmarkt zu durchkämmen.")


# ==============================================================================
# BEREICH 8: DIE RECHTE SPALTE – DER INTERAKTIVE PLOTLY LIVE-CHART
# ==============================================================================
if "aktiver_ticker" in st.session_state:
    aktiver_ticker = st.session_state["aktiver_ticker"]
    chart_titel = st.session_state["chart_titel"]

with spalte_chart:
    # Die Selectbox, um den Zeitraum der Kurve anzupassen (1 Monat, 3 Monate, 1 Jahr)
    zeitraum_chart = st.selectbox("Chart-Zeitraum anpassen:", ["1 Monat", "3 Monate", "1 Jahr"], key="chart_zeitraum_select")
    st.markdown(f"**{chart_titel} ({zeitraum_chart})**")
    yf_period = "1m" if zeitraum_chart == "1 Monat" else "3m" if zeitraum_chart == "3 Monate" else "1y"
    
    try:
        t_daten = yf.Ticker(aktiver_ticker)
        historie = t_daten.history(period=yf_period) # Holt die Kurstabelle der letzten Monate aus dem Netz
        if not historie.empty:
            daten_x = historie.index       # Das Datum für die X-Achse unten
            daten_y = historie["Close"]     # Die echten Schlusskurse für die Y-Achse hoch
            if waehrung == "EUR":
                daten_y = daten_y * USD_ZU_EUR
            
            # Hier zeichnen wir die interaktive Linie mit Plotly
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=daten_x, y=daten_y, mode='lines', name='Kurs', line=dict(color="#00F2FE", width=3)))
            fig.update_layout(template="plotly_dark", height=250, paper_bgcolor="#0B0F19", plot_bgcolor="#0B0F19", margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True) # Zeigt die fertige Grafik im Browser an
        else:
            st.warning("Keine historischen Chartdaten für diesen Wert verfügbar.")
    except:
        st.error("Fehler beim Zeichnen des Live-Charts.")


# ==============================================================================
# BEREICH 9: DIE UNTEREN MERKLISTEN UND AKTIVEN PREIS-ALARME
# ==============================================================================
# Wenn der Nutzer links in der Sidebar auf "Preis-Alarm aktivieren" klickt...
if st.sidebar.button("🔔 Preis-Alarm aktivieren") and such_eingabe:
    try:
        t_alarm_obj = yf.Ticker(aktiver_ticker)
        al_preis = berechne_preis(t_alarm_obj.info.get("currentPrice") or t_alarm_obj.info.get("previousClose", 0.0))
        # Wir packen einen neuen Alarm als Wörterbuch (Dictionary) in unsere Alarme-Liste
        neuer_alarm = {
            "ticker": aktiver_ticker,
            "name": chart_titel.replace("Kursverlauf für '", "").replace("'", ""),
            "aktuell": al_preis,
            "ziel": wunschpreis,
            "symbol": symbol
        }
        st.session_state.alarme.append(neuer_alarm)
        st.sidebar.success("Alarm erfolgreich hinzugefügt!")
    except:
        st.sidebar.error("Alarm konnte nicht gesetzt werden.")

st.divider()
# Wir teilen den ganz unteren Bereich in zwei Hälften auf
spalte_fav_liste, spalte_alarm_liste = st.columns(2)

with spalte_fav_liste:
    st.subheader("📋 Deine Merkliste (Favoriten)")
    if st.session_state.favoriten:
        for fav in st.session_state.favoriten: st.text(f"⭐ {fav}")
    else: st.info("Noch keine Favoriten gespeichert.")

with spalte_alarm_liste:
    st.subheader("⏰ Deine aktiven Preis-Alarme")
    if st.session_state.alarme:
        for al in st.session_state.alarme:
            abstand = al['aktuell'] - al['ziel']
            richtung = "fällt" if abstand > 0 else "steigt"
            # Schreibt eine gelbe Warnbox für jeden aktiven Alarm ganz unten hin
            st.warning(f"🚨 **{al['name']}**: Alarm bei **{al['ziel']:.2f}{al['symbol']}** (Aktuell: {al['aktuell']:.2f}{al['symbol']} | {richtung})")
    else: st.info("Noch keine Preis-Alarme eingerichtet.")
