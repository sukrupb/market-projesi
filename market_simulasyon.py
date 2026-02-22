import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Kampüs Yemek Siparişi Deneyi", page_icon="🍔", layout="wide")

# --- GOOGLE SHEETS BAĞLANTISI ---
def google_sheet_baglan():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open("Market_Deney_Verileri").sheet1 
        return sheet
    except Exception as e:
        return None

# --- YENİ ÜRÜN KATALOĞU (YEMEKSEPETİ TARZI - GERÇEK MARKALAR) ---
urunler = {
    "Doyurucu Menüler (Ana Yemek)": [
        {"ad": "Burger King - Whopper Menü", "fiyat": 190, "emoji": "🍔"},
        {"ad": "Domino's - Bol Malzemos (Orta)", "fiyat": 220, "emoji": "🍕"},
        {"ad": "Tavuk Dünyası - Kekiklim", "fiyat": 210, "emoji": "🍗"},
        {"ad": "Komagene - Mega Çiğ Köfte Dürüm", "fiyat": 75, "emoji": "🌯"},
    ],
    "Gece Krizleri (Dürtüsel Atıştırmalıklar)": [
        {"ad": "Doritos Taco (Büyük Boy)", "fiyat": 45, "emoji": "🔺"},
        {"ad": "Magnum Badem", "fiyat": 40, "emoji": "🍦"},
        {"ad": "Ülker Çikolatalı Gofret", "fiyat": 10, "emoji": "🍫"},
        {"ad": "Eti Cin (Portakallı)", "fiyat": 15, "emoji": "🍪"},
    ],
    "İçecekler & Ekstralar": [
        {"ad": "Coca-Cola Zero (330ml)", "fiyat": 35, "emoji": "🥤"},
        {"ad": "Sütaş Ayran (300ml)", "fiyat": 15, "emoji": "🥛"},
        {"ad": "Red Bull (250ml)", "fiyat": 50, "emoji": "⚡"},
        {"ad": "Beypazarı Maden Suyu", "fiyat": 10, "emoji": "💧"},
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
    st.toast(f"{urun_adi} sepete eklendi!", icon="🛵") 

def veriyi_kaydet():
    try:
        data = st.session_state.kullanici_verisi.copy()
        toplam_tutar = sum(item['fiyat'] for item in st.session_state.sepet)
        sepet_icerigi = ", ".join([item['ad'] for item in st.session_state.sepet])
        
        # Dürtüsel ve Zehirli (Zevk) Ürünleri (Hoca için çok önemli analiz verisi)
        durtusel_liste = ["Doritos Taco (Büyük Boy)", "Magnum Badem", "Ülker Çikolatalı Gofret", "Eti Cin (Portakallı)", "Red Bull (250ml)", "Coca-Cola Zero (330ml)"]
        durtusel_skor = sum(1 for item in st.session_state.sepet if item['ad'] in durtusel_liste)
        
        satir = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data.get("Cinsiyet"),
            data.get("Sinif"), 
            data.get("Yurt_Ev"), 
            data.get("Aclik_Durumu"), # Yeni Değişken!
            toplam_tutar,
            len(st.session_state.sepet),
            durtusel_skor,
            sepet_icerigi
        ]
        
        sheet = google_sheet_baglan()
        if sheet:
            sheet.append_row(satir)
            return True
        else:
            st.error("Google Sheets bağlantısı başarısız oldu. API ayarlarını kontrol et.")
            return False
    except Exception as e:
        st.error(f"Hata: {e}")
        return False

# --- SAYFA 1: GİRİŞ ANKETİ ---
if st.session_state.sayfa == 'anket':
    st.title("🛵 Kampüs Yemek Siparişi Anketi")
    st.markdown("""
    **Senaryo:** Saat gece 23:00. Vize haftasındasın ve karnın çok aç. 
    Kredi kartında tam **400 TL** limitin var. Aşağıdaki uygulamadan akşam yemeği veya atıştırmalık siparişi vermelisin.
    """)
    
    with st.form("giris_formu"):
        col1, col2 = st.columns(2)
        with col1:
            cinsiyet = st.selectbox("Cinsiyet:", ["Kadın", "Erkek"])
            sinif = st.selectbox("Sınıf:", ["Hazırlık", "1. Sınıf", "2. Sınıf", "3. Sınıf", "4. Sınıf"])
        with col2:
            yurt_ev = st.selectbox("Nerede Kalıyorsun?", ["KYK Yurdu", "Özel Yurt", "Öğrenci Evi", "Aile Yanı"])
            aclik_durumu = st.slider("Şu an gerçek hayatta ne kadar açsın? (1: Tokum, 5: Kurt gibi açım)", 1, 5, 3)
        
        if st.form_submit_button("🍕 Siparişe Başla (Limit: 400 TL)"):
            st.session_state.kullanici_verisi = {
                "Cinsiyet": cinsiyet, 
                "Sinif": sinif, 
                "Yurt_Ev": yurt_ev, 
                "Aclik_Durumu": aclik_durumu
            }
            st.session_state.sayfa = 'market'
            st.rerun()

# --- SAYFA 2: SİPARİŞ EKRANI (Yemeksepeti Tarzı) ---
elif st.session_state.sayfa == 'market':
    # Üst Bilgi Paneli
    tutar = sum(item['fiyat'] for item in st.session_state.sepet)
    butce = 400
    kalan = butce - tutar
    
    st.title("Sipariş Ver 🛵")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Kart Limiti", f"{butce} TL")
    col2.metric("Sepet Tutarı", f"{tutar} TL")
    col3.metric("Kalan Limit", f"{kalan} TL", delta_color="normal" if kalan >= 0 else "inverse")

    if kalan < 0:
        st.error("⚠️ Bakiye yetersiz! Bazı ürünleri sepetten çıkarmalısın.")
    
    if st.button("💳 Siparişi Onayla"):
        if kalan < 0:
            st.warning("Kart bakiyen yetersiz, sipariş verilemedi!")
        elif tutar == 0:
            st.warning("Sepetin boş! Karnını doyurmadan mı çıkacaksın?")
        else:
            basarili = veriyi_kaydet()
            if basarili:
                st.session_state.sayfa = 'bitis'
                st.rerun()

    st.markdown("---")

    # Ürün Listeleme
    for kategori, urun_listesi in urunler.items():
        st.subheader(kategori)
        cols = st.columns(4)
        for i, urun in enumerate(urun_listesi):
            with cols[i % 4]:
                st.markdown(f"### {urun['emoji']}")
                st.markdown(f"**{urun['ad']}**")
                st.write(f"*{urun['fiyat']} TL*")
                if st.button("Sepete Ekle", key=f"{kategori}_{i}", use_container_width=True):
                    sepete_ekle(urun['ad'], urun['fiyat'])
                    st.rerun()
        st.markdown("---")
        
    # Sepeti Temizle Butonu
    if st.button("🗑️ Sepeti Boşalt"):
        st.session_state.sepet = []
        st.rerun()

# --- SAYFA 3: BİTİŞ ---
elif st.session_state.sayfa == 'bitis':
    st.balloons()
    st.success("Siparişin Yola Çıktı! 🛵 Katılımın için teşekkürler.")
    
    # Analiz Özeti Göster
    sepet = st.session_state.sepet
    durtusel_liste = ["Doritos Taco (Büyük Boy)", "Magnum Badem", "Ülker Çikolatalı Gofret", "Eti Cin (Portakallı)", "Red Bull (250ml)", "Coca-Cola Zero (330ml)"]
    durtusel_sayi = sum(1 for item in sepet if item['ad'] in durtusel_liste)
    
    st.write("### Sipariş Profilin:")
    if durtusel_sayi >= 3:
        st.warning("🚨 **Dürtüsel Tüketici:** Ana yemekten çok abur cubura para harcadın. Gece krizlerine yenik düştün!")
    elif durtusel_sayi == 0:
        st.info("🥩 **Odaklı ve Doyurucu:** Sadece ana yemeğini alıp çıktın, tebrikler.")
    else:
        st.info("⚖️ **Dengeli:** Hem yemeğini yedin hem de keyif yaptın.")
        
    if st.button("Yeni Katılımcı İçin Başa Dön"):
        st.session_state.clear()
        st.rerun()
