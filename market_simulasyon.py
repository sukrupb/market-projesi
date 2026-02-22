import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="PAÜ Sanal Market Deneyi", page_icon="🛒", layout="wide")

# --- GOOGLE SHEETS BAĞLANTISI ---
def google_sheet_baglan():
    # Streamlit Secrets'tan bilgileri alacağız (Bulutta burası çalışır)
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Secrets yapısını dictionary'ye çevirip credentials oluşturuyoruz
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    # Tabloyu aç (Tablo adının Google Sheets'teki adla AYNI olması lazım)
    sheet = client.open("Market_Deney_Verileri").sheet1 
    return sheet

# --- ÜRÜN KATALOĞU ---
urunler = {
    "Temel Gıda": [
        {"ad": "Ekmek", "fiyat": 10, "emoji": "🍞"},
        {"ad": "Süt (1L)", "fiyat": 25, "emoji": "🥛"},
        {"ad": "Yumurta (15'li)", "fiyat": 60, "emoji": "🥚"},
        {"ad": "Peynir", "fiyat": 120, "emoji": "🧀"},
    ],
    "Atıştırmalık (Dürtüsel)": [
        {"ad": "Çikolata", "fiyat": 15, "emoji": "🍫"},
        {"ad": "Cips", "fiyat": 20, "emoji": "🍟"},
        {"ad": "Kola", "fiyat": 30, "emoji": "🥤"},
        {"ad": "Dondurma", "fiyat": 25, "emoji": "🍦"},
    ],
    "Temizlik & Diğer": [
        {"ad": "Deterjan", "fiyat": 150, "emoji": "🧼"},
        {"ad": "Kağıt Havlu", "fiyat": 80, "emoji": "🧻"},
        {"ad": "Şampuan", "fiyat": 75, "emoji": "🧴"},
        {"ad": "Pil", "fiyat": 40, "emoji": "🔋"},
    ]
}

# --- OTURUM YÖNETİMİ ---
if 'sepet' not in st.session_state:
    st.session_state.sepet = []
if 'sayfa' not in st.session_state:
    st.session_state.sayfa = 'anket'
if 'kullanici_verisi' not in st.session_state:
    st.session_state.kullanici_verisi = {}

def sepete_ekle(urun_adi, fiyat):
    st.session_state.sepet.append({"ad": urun_adi, "fiyat": fiyat})
    st.success(f"{urun_adi} sepete eklendi! 🛒")

def veriyi_kaydet():
    try:
        # Verileri hazırla
        data = st.session_state.kullanici_verisi.copy()
        toplam_tutar = sum(item['fiyat'] for item in st.session_state.sepet)
        sepet_icerigi = ", ".join([item['ad'] for item in st.session_state.sepet])
        durtusel_urunler = ["Çikolata", "Cips", "Kola", "Dondurma"]
        durtusel_skor = sum(1 for item in st.session_state.sepet if item['ad'] in durtusel_urunler)
        
        # Google Sheets'e eklenecek satır (Liste formatında olmalı)
        satir = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data.get("Yas"),
            data.get("Cinsiyet"),
            data.get("Gelir_Algisi"),
            data.get("Planlilik_Skoru"),
            toplam_tutar,
            len(st.session_state.sepet),
            durtusel_skor,
            sepet_icerigi
        ]
        
        # Bağlan ve Gönder
        sheet = google_sheet_baglan()
        sheet.append_row(satir)
        return True
    except Exception as e:
        st.error(f"Hata oluştu: {e}")
        return False

# --- SAYFA AKIŞI ---
if st.session_state.sayfa == 'anket':
    st.title("🛒 PAÜ Sanal Market Deneyi")
    with st.form("giris_formu"):
        col1, col2 = st.columns(2)
        with col1:
            yas = st.number_input("Yaşınız:", 18, 90, 22)
            cinsiyet = st.selectbox("Cinsiyet:", ["Kadın", "Erkek", "Belirtmek İstemiyorum"])
        with col2:
            gelir = st.selectbox("Gelir Algınız:", ["Düşük", "Orta", "Yüksek"])
            planli_mi = st.slider("Alışverişte planlı mısınız?", 1, 5, 3)
        
        if st.form_submit_button("🏪 Alışverişe Başla"):
            st.session_state.kullanici_verisi = {"Yas": yas, "Cinsiyet": cinsiyet, "Gelir_Algisi": gelir, "Planlilik_Skoru": planli_mi}
            st.session_state.sayfa = 'market'
            st.rerun()

elif st.session_state.sayfa == 'market':
    st.title("Sanal Market")
    st.info(f"Sepet Tutarı: {sum(item['fiyat'] for item in st.session_state.sepet)} TL")
    if st.button("✅ Ödemeyi Tamamla"):
        basarili = veriyi_kaydet()
        if basarili:
            st.session_state.sayfa = 'bitis'
            st.rerun()
    
    for kategori, urun_listesi in urunler.items():
        st.subheader(kategori)
        cols = st.columns(4)
        for i, urun in enumerate(urun_listesi):
            with cols[i % 4]:
                st.write(f"### {urun['emoji']}")
                st.write(f"**{urun['ad']}** - {urun['fiyat']} TL")
                if st.button("Sepete Ekle", key=f"{kategori}_{i}"):
                    sepete_ekle(urun['ad'], urun['fiyat'])

elif st.session_state.sayfa == 'bitis':
    st.balloons()
    st.success("Veriler Google Sheets'e başarıyla kaydedildi! 🎉")
    if st.button("Yeni Katılımcı"):
        st.session_state.clear()
        st.rerun()