import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- SAYFA AYARLARI ---
# "layout='wide'" kaldırıldı ki ürünler çok yayılmasın, daha derli toplu dursun.
st.set_page_config(page_title="Hızlı Market Deneyi", page_icon="🛵")

# --- CSS İLE GETİR TEMASI (MOR ARKA PLAN - BEYAZ YAZI) VE RESİM DÜZENİ ---
st.markdown("""
    <style>
    /* 1. ANA TEMA RENGİ: GETİR MORU */
    .stApp {
        background-color: #5d3ebc !important;
    }
    /* 2. TÜM YAZILARI BEYAZ YAP (Okunabilirlik için) */
    h1, h2, h3, h4, h5, h6, p, span, div, label {
        color: white !important;
    }
    /* 3. RESİM BOYUTLARINI SABİTLEME (Grid Düzeni İçin Kritik) */
    div[data-testid="column"] img {
        height: 150px !important;       /* Hepsini 150px yüksekliğe zorla */
        width: 100% !important;         /* Genişliği kutuya yay */
        object-fit: cover !important;   /* Resmi esnetme, kutuya sığacak şekilde kırp */
        border-radius: 12px !important; /* Kenarları yuvarlat */
        border: 2px solid #ffd300 !important; /* Etrafına sarı çerçeve ekle */
    }
    /* 4. BUTON TASARIMI (GETİR SARISI) */
    div.stButton > button:first-child {
        background-color: #ffd300 !important;
        color: #5d3ebc !important; /* Buton yazısı mor */
        border: none !important;
        border-radius: 8px !important;
        font-weight: 900 !important;
        padding: 10px !important;
    }
    div.stButton > button:hover {
        background-color: #ffecb3 !important; /* Üzerine gelince açık sarı */
        color: #5d3ebc !important;
        border: 2px solid #5d3ebc !important;
    }
    /* 5. ÜST BİLGİ KUTULARI (Metric) */
    div[data-testid="stMetricLabel"] {
        color: #e0e0e0 !important; /* Etiketler açık gri */
    }
    div[data-testid="stMetricValue"] {
        color: #ffd300 !important; /* Rakamlar sarı */
    }
    /* Form elemanları (Selectbox vb.) arka planı */
    div[data-baseweb="select"] > div {
        background-color: #4a329c !important; /* Daha koyu mor */
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

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

# --- ÜRÜN KATALOĞU ---
# Resimlerin hepsi CSS ile aynı boyuta getirilecek.
urunler = {
    "Atıştırmalık & Cips": [
        {"ad": "Patates Cipsi (Büyük Boy)", "fiyat": 45, "resim": "https://images.unsplash.com/photo-1566478989037-e124c1B55523?w=400&q=80"},
        {"ad": "Sütlü Çikolata", "fiyat": 25, "resim": "https://images.unsplash.com/photo-1549007994-cb92caebd54b?w=400&q=80"},
        {"ad": "Çubuk Kraker", "fiyat": 10, "resim": "https://images.unsplash.com/photo-1600952841320-1c62eb0cb006?w=400&q=80"},
        {"ad": "Karışık Kuruyemiş", "fiyat": 80, "resim": "https://images.unsplash.com/photo-1599598425947-330026296d11?w=400&q=80"},
    ],
    "İçecek & Enerji": [
        {"ad": "Kola (Kutu 330ml)", "fiyat": 30, "resim": "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=400&q=80"},
        {"ad": "Enerji İçeceği", "fiyat": 50, "resim": "https://images.unsplash.com/photo-1622543925917-763c34d1a86e?w=400&q=80"},
        {"ad": "Soğuk Çay (Şeftali)", "fiyat": 25, "resim": "https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=400&q=80"},
        {"ad": "Doğal Kaynak Suyu (1.5L)", "fiyat": 15, "resim": "https://images.unsplash.com/photo-1523362628745-0c100150b504?w=400&q=80"},
    ],
    "Pratik Yemek & Dondurma": [
        {"ad": "Dondurulmuş Pizza", "fiyat": 120, "resim": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400&q=80"},
        {"ad": "Hazır Noodle (Körili)", "fiyat": 15, "resim": "https://images.unsplash.com/photo-1612929633738-8fe01f72810c?w=400&q=80"},
        {"ad": "Ton Balığı (3'lü)", "fiyat": 140, "resim": "https://images.unsplash.com/photo-1610832958506-aa56368176cf?w=400&q=80"},
        {"ad": "Çubuk Dondurma (Bademli)", "fiyat": 45, "resim": "https://images.unsplash.com/photo-1563805042-7684c8e9e533?w=400&q=80"},
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
    st.toast(f"{urun_adi} sepete atıldı! 🛵", icon="✅") 

def veriyi_kaydet():
    try:
        data = st.session_state.kullanici_verisi.copy()
        toplam_tutar = sum(item['fiyat'] for item in st.session_state.sepet)
        sepet_icerigi = ", ".join([item['ad'] for item in st.session_state.sepet])
        durtusel_liste = ["Patates Cipsi (Büyük Boy)", "Sütlü Çikolata", "Kola (Kutu 330ml)", "Enerji İçeceği", "Çubuk Dondurma (Bademli)"]
        durtusel_skor = sum(1 for item in st.session_state.sepet if item['ad'] in durtusel_liste)
        
        satir = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data.get("Cinsiyet"),
            data.get("Sinif"), 
            data.get("Yurt_Ev"), 
            data.get("Aclik_Durumu"),
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
            st.error("Bağlantı hatası.")
            return False
    except Exception as e:
        st.error(f"Hata: {e}")
        return False

# --- SAYFA 1: GİRİŞ ANKETİ ---
if st.session_state.sayfa == 'anket':
    st.title("Hızlı Market Tüketim Anketi 🛵")
    st.markdown("""
    <div style='background-color: #4a329c; padding: 15px; border-radius: 10px;'>
    <b>Senaryo:</b> Karnın aç veya canın bir şeyler çekiyor. Uygulamada <b>400 TL</b> bakiyen var. 
    İstediğin ürünleri sepetine ekle ve siparişi tamamla. (Ürünler 10-15 dk içinde kapında varsayıyoruz).
    </div>
    """, unsafe_allow_html=True)
    
    st.write("") # Boşluk

    with st.form("giris_formu"):
        col1, col2 = st.columns(2)
        with col1:
            cinsiyet = st.selectbox("Cinsiyetiniz:", ["Kadın", "Erkek", "Belirtmek İstemiyorum"])
            sinif = st.selectbox("Sınıfınız:", ["Hazırlık", "1. Sınıf", "2. Sınıf", "3. Sınıf", "4. Sınıf"])
        with col2:
            yurt_ev = st.selectbox("Yaşam Alanı:", ["KYK Yurdu", "Özel Yurt", "Öğrenci Evi", "Aile Yanı"])
            aclik_durumu = st.slider("Şu an fiziksel olarak ne kadar açsın? (1: Tok, 5: Çok Aç)", 1, 5, 3)
        
        st.write("") # Boşluk
        if st.form_submit_button("🛒 Markete Gir (Bakiye: 400 TL)", use_container_width=True):
            st.session_state.kullanici_verisi = {
                "Cinsiyet": cinsiyet, "Sinif": sinif, "Yurt_Ev": yurt_ev, "Aclik_Durumu": aclik_durumu
            }
            st.session_state.sayfa = 'market'
            st.rerun()

# --- SAYFA 2: SİPARİŞ EKRANI (Menü Görünümü) ---
elif st.session_state.sayfa == 'market':
    tutar = sum(item['fiyat'] for item in st.session_state.sepet)
    butce = 400
    kalan = butce - tutar
    
    st.title("Dakikalar İçinde Kapında! ⚡")
    
    # Üst Bilgi Paneli
    with st.container():
        col1, col2, col3 = st.columns(3)
        col1.metric("Kart Limiti", f"{butce} TL")
        col2.metric("Sepet Tutarı", f"{tutar} TL")
        col3.metric("Kalan Limit", f"{kalan} TL", delta_color="normal" if kalan >= 0 else "inverse")
    
    if kalan < 0:
        st.error("⚠️ Bakiye yetersiz! Lütfen sepetini ayarla.")
    
    # Butonlar
    col_onay, col_bosalt = st.columns([2, 1])
    with col_onay:
        if st.button("💳 Siparişi Onayla", use_container_width=True):
            if kalan < 0:
                st.warning("Kart bakiyen yetersiz!")
            elif tutar == 0:
                st.warning("Sepetin boş!")
            else:
                basarili = veriyi_kaydet()
                if basarili:
                    st.session_state.sayfa = 'bitis'
                    st.rerun()
    with col_bosalt:
        if st.button("🗑️ Boşalt", use_container_width=True):
            st.session_state.sepet = []
            st.rerun()

    st.markdown("---")

    # Ürün Listeleme (Grid Yapısı)
    for kategori, urun_listesi in urunler.items():
        st.subheader(kategori)
        # "wide" modu kapattığımız için 4 yerine 3 sütun daha iyi durur
        cols = st.columns(3) 
        for i, urun in enumerate(urun_listesi):
            with cols[i % 3]:
                # Resim CSS ile kontrol ediliyor
                st.image(urun['resim'], use_container_width=True) 
                st.markdown(f"**{urun['ad']}**")
                st.write(f"*{urun['fiyat']} TL*")
                if st.button("Sepete Ekle", key=f"{kategori}_{i}", use_container_width=True):
                    sepete_ekle(urun['ad'], urun['fiyat'])
                    st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)

# --- SAYFA 3: BİTİŞ ---
elif st.session_state.sayfa == 'bitis':
    st.balloons()
    st.success("Siparişin alındı! 🛵 Depo görevlimiz ürünlerini hazırlıyor.")
    
    sepet = st.session_state.sepet
    st.write("### Sipariş Özeti:")
    
    # Veri tablosunu beyaz yapalım ki okunsun
    st.markdown("""<style>div[data-testid="stDataFrame"] {background-color: white; padding: 10px; border-radius: 10px;}</style>""", unsafe_allow_html=True)
    sepet_df = pd.DataFrame(sepet)
    st.dataframe(sepet_df, use_container_width=True)
        
    if st.button("Yeni Katılımcı İçin Başa Dön", use_container_width=True):
        st.session_state.clear()
        st.rerun()
