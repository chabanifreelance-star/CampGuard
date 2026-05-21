import streamlit as st
import pandas as pd
import json
from datetime import datetime, date, time, timedelta
import random
import os

# ─── CONFIG ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CampGuard — Sécurité Camping",
    page_icon="⛺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Exo+2:wght@300;400;600&display=swap');

:root {
    --bg: #0a0f1a;
    --bg2: #111827;
    --card: #161f30;
    --border: #1e3a5f;
    --accent: #00d4ff;
    --accent2: #ff6b35;
    --green: #00e676;
    --red: #ff1744;
    --yellow: #ffd740;
    --text: #e8f4f8;
    --muted: #7a9ab5;
}

html, body, [class*="css"] {
    font-family: 'Exo 2', sans-serif;
    background-color: var(--bg);
    color: var(--text);
}

h1, h2, h3 { font-family: 'Rajdhani', sans-serif; letter-spacing: 1px; }

.stApp { background: var(--bg); }

section[data-testid="stSidebar"] {
    background: var(--bg2) !important;
    border-right: 1px solid var(--border);
}

.metric-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px;
    text-align: center;
    border-top: 3px solid var(--accent);
}
.metric-card .val { font-size: 2.5rem; font-weight: 700; color: var(--accent); font-family: 'Rajdhani'; }
.metric-card .lbl { font-size: 0.8rem; color: var(--muted); text-transform: uppercase; letter-spacing: 2px; }

.badge-actif { background: #003d1f; color: var(--green); border: 1px solid var(--green); padding: 3px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
.badge-absent { background: #3d0a00; color: var(--red); border: 1px solid var(--red); padding: 3px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
.badge-attente { background: #3d2600; color: var(--yellow); border: 1px solid var(--yellow); padding: 3px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
.badge-nuit { background: #1a0040; color: #bf80ff; border: 1px solid #bf80ff; padding: 3px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }

.incident-card {
    background: var(--card);
    border-left: 4px solid var(--accent2);
    border-radius: 6px;
    padding: 14px 18px;
    margin-bottom: 10px;
}
.incident-card.haute { border-left-color: var(--red); }
.incident-card.moyenne { border-left-color: var(--yellow); }
.incident-card.basse { border-left-color: var(--green); }

.shift-block {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px;
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.shift-nuit { border-color: #4a2080; background: #0e0a1a; }

.zone-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px;
    text-align: center;
    cursor: pointer;
}
.zone-card.active { border-color: var(--green); }
.zone-card.alert { border-color: var(--red); }

.header-bar {
    background: linear-gradient(135deg, #0a1628, #0f2040);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 28px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    gap: 16px;
}

.stButton > button {
    border-radius: 6px !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 1px !important;
}

div[data-testid="stSelectbox"] > div { background: var(--card) !important; }
div[data-testid="stTextInput"] > div > div { background: var(--card) !important; }

.rapport-section {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 16px;
}
</style>
""", unsafe_allow_html=True)

# ─── STATE INIT ────────────────────────────────────────────────────────────────
def init_state():
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        st.session_state.role = None
        st.session_state.logged_user = None

        # Gardes (exemple 20 personnes pour démo)
        st.session_state.gardes = [
            {"id": i, "nom": n, "telephone": f"06{random.randint(10000000,99999999)}",
             "equipe": ["Alpha","Beta","Gamma"][i%3], "actif": True}
            for i, n in enumerate([
                "Ahmed B.", "Karim M.", "Youssef T.", "Omar R.", "Bilal H.",
                "Anas K.", "Zakaria L.", "Hamza F.", "Ilyas N.", "Mehdi A.",
                "Rachid O.", "Samir D.", "Nabil S.", "Tariq E.", "Fadel J.",
                "Hicham P.", "Mourad C.", "Jamal V.", "Redouane W.", "Nassim X."
            ])
        ]

        # Créneaux 4h sur 24h
        slots = [
            ("00:00","04:00",True), ("04:00","08:00",False),
            ("08:00","12:00",False), ("12:00","16:00",False),
            ("16:00","20:00",False), ("20:00","00:00",True)
        ]

        today = date.today()
        st.session_state.shifts = []
        sid = 0
        for i, (debut, fin, nuit) in enumerate(slots):
            gardes_slot = [i*2 % 20, (i*2+1) % 20] if nuit else [i*2 % 20]
            st.session_state.shifts.append({
                "id": sid, "date": str(today), "debut": debut, "fin": fin,
                "nuit": nuit, "gardes": gardes_slot,
                "zone": ["Entrée Principale","Périmètre Nord","Périmètre Sud",
                         "Zone Sanitaires","Parking","Entrée Secondaire"][i],
                "confirme": i < 3,
                "notes": ""
            })
            sid += 1

        # Incidents
        st.session_state.incidents = [
            {
                "id": 0, "datetime": str(datetime.now() - timedelta(hours=3)),
                "type": "Photo non autorisée", "zone": "Piscine",
                "gravite": "moyenne", "rapporte_par": "Ahmed B.",
                "description": "Personne extérieure photographiait les familles",
                "resolu": True
            },
            {
                "id": 1, "datetime": str(datetime.now() - timedelta(hours=1)),
                "type": "Intrusion tentative", "zone": "Entrée Principale",
                "gravite": "haute", "rapporte_par": "Karim M.",
                "description": "Véhicule inconnu tentant d'entrer sans badge",
                "resolu": False
            },
        ]

        st.session_state.zones = [
            {"nom": "Entrée Principale", "icon": "🚪", "statut": "actif", "garde_actuel": "Ahmed B."},
            {"nom": "Entrée Secondaire", "icon": "🚧", "statut": "actif", "garde_actuel": "Karim M."},
            {"nom": "Périmètre Nord", "icon": "🌲", "statut": "actif", "garde_actuel": "Youssef T."},
            {"nom": "Périmètre Sud", "icon": "🌲", "statut": "alert", "garde_actuel": "VACANT"},
            {"nom": "Parking", "icon": "🅿️", "statut": "actif", "garde_actuel": "Omar R."},
            {"nom": "Zone Sanitaires", "icon": "🚿", "statut": "actif", "garde_actuel": "Bilal H."},
        ]

        st.session_state.check_ins = {}  # garde_id -> datetime
        st.session_state.admin_code = "CAMP2024"
        st.session_state.garde_codes = {g["id"]: f"G{g['id']:03d}" for g in st.session_state.gardes}
        st.session_state.next_incident_id = 2

init_state()

# ─── LOGIN ──────────────────────────────────────────────────────────────────────
def page_login():
    st.markdown("""
    <div style="text-align:center; padding: 40px 0 20px;">
        <div style="font-size:4rem">⛺</div>
        <h1 style="font-family:'Rajdhani';font-size:2.8rem;color:#00d4ff;margin:0;">CAMPGUARD</h1>
        <p style="color:#7a9ab5;letter-spacing:3px;font-size:0.9rem;">SYSTÈME DE SÉCURITÉ CAMPING</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,1.2,1])
    with col2:
        st.markdown("---")
        mode = st.radio("Connexion en tant que :", ["🔑 Administrateur", "👮 Garde"], horizontal=True)

        if mode == "🔑 Administrateur":
            code = st.text_input("Code Admin", type="password", placeholder="Entrez le code admin")
            if st.button("CONNEXION ADMIN", use_container_width=True, type="primary"):
                if code == st.session_state.admin_code:
                    st.session_state.role = "admin"
                    st.session_state.logged_user = "Administrateur"
                    st.rerun()
                else:
                    st.error("❌ Code incorrect")
        else:
            garde_options = {f"{g['nom']} (Code: G{g['id']:03d})": g["id"]
                            for g in st.session_state.gardes if g["actif"]}
            selection = st.selectbox("Sélectionnez votre nom", list(garde_options.keys()))
            code = st.text_input("Votre code personnel", type="password")
            if st.button("CONNEXION GARDE", use_container_width=True, type="primary"):
                gid = garde_options[selection]
                if code == f"G{gid:03d}":
                    st.session_state.role = "garde"
                    st.session_state.logged_user = gid
                    st.rerun()
                else:
                    st.error("❌ Code incorrect")

# ─── SIDEBAR ────────────────────────────────────────────────────────────────────
def sidebar():
    with st.sidebar:
        st.markdown(f"""
        <div style='text-align:center;padding:10px 0;'>
            <div style='font-size:2rem'>⛺</div>
            <div style='font-family:Rajdhani;font-size:1.4rem;color:#00d4ff;font-weight:700;'>CAMPGUARD</div>
            <div style='font-size:0.7rem;color:#7a9ab5;'>300 résidents · Sécurité Active</div>
        </div>
        """, unsafe_allow_html=True)
        st.divider()

        now = datetime.now()
        st.markdown(f"<div style='text-align:center;color:#7a9ab5;font-size:0.8rem;'>{now.strftime('%d/%m/%Y — %H:%M')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center;font-size:0.85rem;margin-bottom:12px;'>👤 <b>{st.session_state.logged_user if st.session_state.role == 'admin' else next((g['nom'] for g in st.session_state.gardes if g['id'] == st.session_state.logged_user), '')}</b></div>", unsafe_allow_html=True)

        if st.session_state.role == "admin":
            pages = {
                "📊 Tableau de Bord": "dashboard",
                "⏱ Gestion des Shifts": "shifts",
                "🗺 Carte des Zones": "zones",
                "👮 Équipe de Gardes": "gardes",
                "🚨 Registre d'Incidents": "incidents",
                "📋 Rapport de Nuit": "rapport",
            }
        else:
            pages = {
                "🏠 Mon Shift": "mon_shift",
                "✅ Check-in Présence": "checkin",
                "🚨 Signaler Incident": "signaler",
            }

        if "page" not in st.session_state:
            st.session_state.page = list(pages.values())[0]

        for label, key in pages.items():
            if st.button(label, use_container_width=True,
                         type="primary" if st.session_state.page == key else "secondary"):
                st.session_state.page = key
                st.rerun()

        st.divider()
        if st.button("🚪 Déconnexion", use_container_width=True):
            st.session_state.role = None
            st.session_state.logged_user = None
            st.session_state.page = "dashboard"
            st.rerun()

# ─── PAGES ADMIN ────────────────────────────────────────────────────────────────
def page_dashboard():
    st.markdown("<h1 style='font-family:Rajdhani;color:#00d4ff;'>📊 Tableau de Bord</h1>", unsafe_allow_html=True)

    now = datetime.now()
    heure = now.strftime("%H:%M")
    nuit = now.hour >= 22 or now.hour < 6

    shifts_today = [s for s in st.session_state.shifts if s["date"] == str(date.today())]
    confirmed = [s for s in shifts_today if s["confirme"]]
    incidents_open = [i for i in st.session_state.incidents if not i["resolu"]]
    zones_alert = [z for z in st.session_state.zones if z["statut"] == "alert"]

    c1, c2, c3, c4 = st.columns(4)
    metrics = [
        (len(confirmed), f"/{len(shifts_today)}", "Shifts Confirmés", c1),
        (len(st.session_state.gardes), "", "Gardes Enregistrés", c2),
        (len(incidents_open), " ouverts", "Incidents", c3),
        (len(zones_alert), " en alerte", "Zones Alertes", c4),
    ]
    for val, suf, lbl, col in metrics:
        col.markdown(f"""
        <div class='metric-card'>
            <div class='val'>{val}<span style='font-size:1rem;color:#7a9ab5;'>{suf}</span></div>
            <div class='lbl'>{lbl}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_a, col_b = st.columns([1.5, 1])

    with col_a:
        st.markdown("### ⏱ Shifts du Jour")
        for s in shifts_today[:4]:
            nuit_badge = "🌙 NUIT" if s["nuit"] else "☀️ JOUR"
            garde_noms = [g["nom"] for g in st.session_state.gardes if g["id"] in s["gardes"]]
            conf_icon = "✅" if s["confirme"] else "⏳"
            st.markdown(f"""
            <div class='shift-block {"shift-nuit" if s["nuit"] else ""}'>
                <div>
                    <b>{s['debut']} – {s['fin']}</b> &nbsp; {nuit_badge}<br>
                    <span style='color:#7a9ab5;font-size:0.85rem;'>{s['zone']}</span>
                </div>
                <div style='text-align:right'>
                    <span style='font-size:0.9rem'>{', '.join(garde_noms)}</span><br>
                    <span style='font-size:1.2rem'>{conf_icon}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_b:
        st.markdown("### 🚨 Incidents Récents")
        for inc in st.session_state.incidents[-3:][::-1]:
            st.markdown(f"""
            <div class='incident-card {inc["gravite"]}'>
                <b>{inc["type"]}</b><br>
                <span style='color:#7a9ab5;font-size:0.8rem;'>📍 {inc["zone"]} · {inc["rapporte_par"]}</span><br>
                <span style='font-size:0.8rem;'>{"✅ Résolu" if inc["resolu"] else "🔴 En cours"}</span>
            </div>
            """, unsafe_allow_html=True)

def page_shifts():
    st.markdown("<h1 style='font-family:Rajdhani;color:#00d4ff;'>⏱ Gestion des Shifts</h1>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📅 Shifts Aujourd'hui", "➕ Créer un Shift"])

    with tab1:
        for s in st.session_state.shifts:
            garde_noms = [g["nom"] for g in st.session_state.gardes if g["id"] in s["gardes"]]
            with st.expander(f"{'🌙' if s['nuit'] else '☀️'} {s['debut']}–{s['fin']} | {s['zone']} | {'✅' if s['confirme'] else '⏳'}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Zone :** {s['zone']}")
                    st.write(f"**Nuit :** {'Oui 🌙' if s['nuit'] else 'Non'}")
                    st.write(f"**Gardes :** {', '.join(garde_noms)}")
                with col2:
                    st.write(f"**Confirmé :** {'✅ Oui' if s['confirme'] else '⏳ Non'}")
                    if not s["confirme"]:
                        if st.button(f"✅ Confirmer", key=f"conf_{s['id']}"):
                            s["confirme"] = True
                            st.rerun()
                notes = st.text_input("Notes", value=s.get("notes",""), key=f"notes_{s['id']}")
                s["notes"] = notes

    with tab2:
        st.markdown("#### Nouveau Shift")
        col1, col2 = st.columns(2)
        with col1:
            debut = st.selectbox("Heure début", ["00:00","04:00","08:00","12:00","16:00","20:00"])
            fin_map = {"00:00":"04:00","04:00":"08:00","08:00":"12:00","12:00":"16:00","16:00":"20:00","20:00":"00:00"}
            fin = fin_map[debut]
            st.info(f"Fin automatique : **{fin}** (créneau 4h)")
            zone = st.selectbox("Zone", [z["nom"] for z in st.session_state.zones])
        with col2:
            nuit = debut in ["20:00","00:00"]
            min_gardes = 2 if nuit else 1
            st.info(f"{'🌙 Créneau de NUIT — 2 gardes obligatoires' if nuit else '☀️ Créneau de JOUR — 1 garde minimum'}")
            gardes_dispo = [g["nom"] for g in st.session_state.gardes if g["actif"]]
            selections = st.multiselect(f"Gardes (min {min_gardes})", gardes_dispo)

        if st.button("Créer le Shift", type="primary"):
            if len(selections) < min_gardes:
                st.error(f"⚠️ Minimum {min_gardes} garde(s) requis pour ce créneau")
            else:
                garde_ids = [g["id"] for g in st.session_state.gardes if g["nom"] in selections]
                new_shift = {
                    "id": len(st.session_state.shifts), "date": str(date.today()),
                    "debut": debut, "fin": fin, "nuit": nuit,
                    "gardes": garde_ids, "zone": zone, "confirme": False, "notes": ""
                }
                st.session_state.shifts.append(new_shift)
                st.success("✅ Shift créé avec succès !")
                st.rerun()

def page_zones():
    st.markdown("<h1 style='font-family:Rajdhani;color:#00d4ff;'>🗺 Carte des Zones</h1>", unsafe_allow_html=True)

    cols = st.columns(3)
    for i, zone in enumerate(st.session_state.zones):
        with cols[i % 3]:
            color = "#00e676" if zone["statut"] == "actif" else "#ff1744"
            st.markdown(f"""
            <div class='zone-card {"alert" if zone["statut"]=="alert" else "active"}'>
                <div style='font-size:2.5rem'>{zone['icon']}</div>
                <div style='font-weight:700;font-size:1rem;margin:8px 0'>{zone['nom']}</div>
                <div style='color:{color};font-size:0.85rem;font-weight:600;'>● {zone['statut'].upper()}</div>
                <div style='color:#7a9ab5;font-size:0.8rem;margin-top:6px;'>👮 {zone['garde_actuel']}</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

    st.divider()
    st.markdown("### ✏️ Modifier une Zone")
    zone_select = st.selectbox("Zone", [z["nom"] for z in st.session_state.zones])
    z = next(z for z in st.session_state.zones if z["nom"] == zone_select)
    col1, col2 = st.columns(2)
    with col1:
        nouveau_statut = st.selectbox("Statut", ["actif","alert"], index=0 if z["statut"]=="actif" else 1)
    with col2:
        gardes_noms = ["VACANT"] + [g["nom"] for g in st.session_state.gardes]
        nouveau_garde = st.selectbox("Garde assigné", gardes_noms,
                                      index=gardes_noms.index(z["garde_actuel"]) if z["garde_actuel"] in gardes_noms else 0)
    if st.button("💾 Mettre à jour la zone", type="primary"):
        z["statut"] = nouveau_statut
        z["garde_actuel"] = nouveau_garde
        st.success("✅ Zone mise à jour")
        st.rerun()

def page_gardes():
    st.markdown("<h1 style='font-family:Rajdhani;color:#00d4ff;'>👮 Équipe de Gardes</h1>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Liste des Gardes", "➕ Ajouter un Garde"])

    with tab1:
        df = pd.DataFrame([{
            "Nom": g["nom"], "Équipe": g["equipe"],
            "Tél": g["telephone"], "Code": f"G{g['id']:03d}",
            "Statut": "✅ Actif" if g["actif"] else "❌ Inactif"
        } for g in st.session_state.gardes])
        st.dataframe(df, use_container_width=True, hide_index=True)

    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            nom = st.text_input("Nom complet")
            tel = st.text_input("Téléphone")
        with col2:
            equipe = st.selectbox("Équipe", ["Alpha", "Beta", "Gamma"])
        if st.button("Ajouter le Garde", type="primary"):
            if nom:
                new_id = len(st.session_state.gardes)
                st.session_state.gardes.append({
                    "id": new_id, "nom": nom, "telephone": tel,
                    "equipe": equipe, "actif": True
                })
                st.session_state.garde_codes[new_id] = f"G{new_id:03d}"
                st.success(f"✅ {nom} ajouté ! Code : **G{new_id:03d}**")
                st.rerun()

def page_incidents():
    st.markdown("<h1 style='font-family:Rajdhani;color:#00d4ff;'>🚨 Registre d'Incidents</h1>", unsafe_allow_html=True)

    ouverts = [i for i in st.session_state.incidents if not i["resolu"]]
    if ouverts:
        st.error(f"⚠️ {len(ouverts)} incident(s) non résolu(s) !")

    for inc in st.session_state.incidents[::-1]:
        col1, col2 = st.columns([4,1])
        with col1:
            st.markdown(f"""
            <div class='incident-card {inc["gravite"]}'>
                <b>#{inc["id"]} — {inc["type"]}</b> &nbsp;
                <span style='font-size:0.8rem;color:#7a9ab5;'>{inc["datetime"][:16]}</span><br>
                <span style='color:#aaa;font-size:0.85rem;'>📍 {inc["zone"]} &nbsp;|&nbsp; 👮 {inc["rapporte_par"]}</span><br>
                <span style='font-size:0.85rem;'>{inc["description"]}</span><br>
                <span style='color:{"#00e676" if inc["resolu"] else "#ff1744"};font-size:0.85rem;font-weight:600;'>
                    {"✅ Résolu" if inc["resolu"] else "🔴 En cours"}
                </span>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            if not inc["resolu"]:
                if st.button("✅ Résoudre", key=f"res_{inc['id']}"):
                    inc["resolu"] = True
                    st.rerun()

def page_rapport():
    st.markdown("<h1 style='font-family:Rajdhani;color:#00d4ff;'>📋 Rapport de Nuit</h1>", unsafe_allow_html=True)

    today = date.today()
    shifts = [s for s in st.session_state.shifts if s["date"] == str(today)]
    incidents_today = st.session_state.incidents

    col1, col2, col3 = st.columns(3)
    col1.metric("Shifts Planifiés", len(shifts))
    col2.metric("Shifts Confirmés", len([s for s in shifts if s["confirme"]]))
    col3.metric("Incidents Total", len(incidents_today))

    st.markdown(f"""
    <div class='rapport-section'>
        <h3 style='font-family:Rajdhani;color:#00d4ff;'>📅 Rapport du {today.strftime("%d/%m/%Y")}</h3>
        <b>Résumé :</b> {len(shifts)} shifts programmés, {len([s for s in shifts if s["confirme"]])} confirmés,
        {len([i for i in incidents_today if not i["resolu"]])} incidents en cours.<br><br>
        <b>Incidents non résolus :</b><br>
        {"".join([f"• #{i['id']} — {i['type']} ({i['zone']})<br>" for i in incidents_today if not i["resolu"]]) or "Aucun ✅"}
    </div>
    """, unsafe_allow_html=True)

    # CSV Export
    rapport_data = [{
        "Shift": f"{s['debut']}–{s['fin']}", "Zone": s["zone"],
        "Nuit": "Oui" if s["nuit"] else "Non",
        "Gardes": ", ".join([g["nom"] for g in st.session_state.gardes if g["id"] in s["gardes"]]),
        "Confirmé": "Oui" if s["confirme"] else "Non"
    } for s in shifts]

    df = pd.DataFrame(rapport_data)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Télécharger le Rapport CSV", csv,
                       f"rapport_{today}.csv", "text/csv", use_container_width=True)

# ─── PAGES GARDE ────────────────────────────────────────────────────────────────
def page_mon_shift():
    gid = st.session_state.logged_user
    garde = next(g for g in st.session_state.gardes if g["id"] == gid)
    st.markdown(f"<h1 style='font-family:Rajdhani;color:#00d4ff;'>🏠 Bonjour, {garde['nom']}</h1>", unsafe_allow_html=True)

    mes_shifts = [s for s in st.session_state.shifts if gid in s["gardes"] and s["date"] == str(date.today())]

    if not mes_shifts:
        st.info("Aucun shift prévu pour vous aujourd'hui.")
        return

    for s in mes_shifts:
        now = datetime.now().strftime("%H:%M")
        actif = s["debut"] <= now < s["fin"] or (s["fin"] == "00:00" and now >= s["debut"])
        st.markdown(f"""
        <div class='shift-block {"shift-nuit" if s["nuit"] else ""}'>
            <div>
                <div style='font-size:1.4rem;font-weight:700;font-family:Rajdhani;'>{s["debut"]} – {s["fin"]}</div>
                <div style='color:#7a9ab5;'>📍 {s["zone"]} &nbsp; {'🌙 Créneau de nuit' if s["nuit"] else '☀️ Créneau de jour'}</div>
            </div>
            <div>
                <span class='{"badge-actif" if actif else "badge-attente"}'> {"EN COURS" if actif else "À VENIR"}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

def page_checkin():
    gid = st.session_state.logged_user
    garde = next(g for g in st.session_state.gardes if g["id"] == gid)
    st.markdown(f"<h1 style='font-family:Rajdhani;color:#00d4ff;'>✅ Check-in Présence</h1>", unsafe_allow_html=True)

    last_checkin = st.session_state.check_ins.get(gid)
    if last_checkin:
        st.success(f"✅ Dernier check-in : **{last_checkin}**")
    else:
        st.warning("⏳ Aucun check-in enregistré aujourd'hui")

    st.markdown("### Confirmer votre présence à votre poste")
    zone_select = st.selectbox("Votre zone actuelle", [z["nom"] for z in st.session_state.zones])
    code_confirm = st.text_input("Code de confirmation (votre code garde)", type="password")

    if st.button("✅ JE SUIS À MON POSTE", type="primary", use_container_width=True):
        if code_confirm == f"G{gid:03d}":
            now_str = datetime.now().strftime("%H:%M:%S")
            st.session_state.check_ins[gid] = now_str
            st.success(f"✅ Présence confirmée à {now_str} — Zone: {zone_select}")
            st.balloons()
        else:
            st.error("❌ Code incorrect")

def page_signaler():
    gid = st.session_state.logged_user
    garde = next(g for g in st.session_state.gardes if g["id"] == gid)
    st.markdown("<h1 style='font-family:Rajdhani;color:#ff1744;'>🚨 Signaler un Incident</h1>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        type_inc = st.selectbox("Type d'incident", [
            "Photo non autorisée", "Intrusion tentative", "Personne suspecte",
            "Bruit/Perturbation", "Véhicule non identifié", "Autre"
        ])
        zone = st.selectbox("Zone de l'incident", [z["nom"] for z in st.session_state.zones])
    with col2:
        gravite = st.select_slider("Gravité", ["basse","moyenne","haute"])
        st.markdown(f"<br><span class='badge-{'actif' if gravite=='basse' else 'absent' if gravite=='haute' else 'attente'}'>{gravite.upper()}</span>", unsafe_allow_html=True)

    description = st.text_area("Description de l'incident", placeholder="Décrivez ce que vous avez observé...")

    if st.button("🚨 SIGNALER CET INCIDENT", type="primary", use_container_width=True):
        if description:
            new_inc = {
                "id": st.session_state.next_incident_id,
                "datetime": str(datetime.now()),
                "type": type_inc, "zone": zone, "gravite": gravite,
                "rapporte_par": garde["nom"],
                "description": description, "resolu": False
            }
            st.session_state.incidents.append(new_inc)
            st.session_state.next_incident_id += 1
            st.error(f"🚨 Incident #{new_inc['id']} signalé ! L'administrateur a été notifié.")
        else:
            st.warning("Veuillez décrire l'incident")

# ─── ROUTER ─────────────────────────────────────────────────────────────────────
if st.session_state.role is None:
    page_login()
else:
    sidebar()
    page = st.session_state.get("page", "dashboard")

    if st.session_state.role == "admin":
        if page == "dashboard": page_dashboard()
        elif page == "shifts": page_shifts()
        elif page == "zones": page_zones()
        elif page == "gardes": page_gardes()
        elif page == "incidents": page_incidents()
        elif page == "rapport": page_rapport()
    else:
        if page == "mon_shift": page_mon_shift()
        elif page == "checkin": page_checkin()
        elif page == "signaler": page_signaler()
