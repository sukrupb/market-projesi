import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Hızlı Market Deneyi", page_icon="🛵", layout="wide")

# --- CSS İLE GETİR TEMASI (MOR VE SARI) ---
st.markdown("""
    <style>
    /* Ana Arka Plan ve Yazı Tipleri */
    .stApp {
        background-color: #f7f7f7;
    }
    h1, h2, h3 {
        color: #5d3ebc !important; /* Getir Moru */
        font-weight: 800 !important;
    }
    /* Buton Tasarımı (Getir Sarısı) */
    div.stButton > button:first-child {
        background-color: #ffd300 !important;
        color: #5d3ebc !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 900 !important;
        padding: 10px !important;
        transition: 0.2s;
    }
    div.stButton > button:hover {
        background-color: #ffc000 !important;
        transform: scale(1.03);
    }
    /* Üst Bilgi Kutuları (Sepet Tutarı vs) */
    div[data-testid="stMetricValue"] {
        color: #5d3ebc !important;
        font-weight: 900 !important;
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

# --- YENİ ÜRÜN KATALOĞU (GERÇEK RESİMLİ) ---
# Telif hakkı olmaması için yüksek kaliteli stok ve temsili linkler kullanıldı.
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
        
        # Dürtüsel Ürünler Analizi
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
            st.error("Bağlantı hatası. API ayarlarını kontrol et.")
            return False
    except Exception as e:
        st.error(f"Hata: {e}")
        return False

# --- SAYFA 1: GİRİŞ ANKETİ ---
if st.session_state.sayfa == 'anket':
    st.title("Hızlı Market Tüketim Anketi 🛵")
    st.markdown("""
    **Senaryo:** Karnın aç veya canın bir şeyler çekiyor. Uygulamada **400 TL** bakiyen var. 
    İstediğin ürünleri sepetine ekle ve siparişi tamamla. (Ürünler 10-15 dk içinde kapında varsayıyoruz).
    """)
    
    with st.form("giris_formu"):
        col1, col2 = st.columns(2)
        with col1:
            cinsiyet = st.selectbox("Cinsiyetiniz:", ["Kadın", "Erkek"])
            sinif = st.selectbox("Sınıfınız:", ["Hazırlık", "1. Sınıf", "2. Sınıf", "3. Sınıf", "4. Sınıf"])
        with col2:
            yurt_ev = st.selectbox("Yaşam Alanı:", ["KYK Yurdu", "Özel Yurt", "Öğrenci Evi", "Aile Yanı"])
            aclik_durumu = st.slider("Şu an fiziksel olarak ne kadar açsın? (1: Tok, 5: Çok Aç)", 1, 5, 3)
        
        if st.form_submit_button("🛒 Markete Gir (Bakiye: 400 TL)"):
            st.session_state.kullanici_verisi = {
                "Cinsiyet": cinsiyet, "Sinif": sinif, "Yurt_Ev": yurt_ev, "Aclik_Durumu": aclik_durumu
            }
            st.session_state.sayfa = 'market'
            st.rerun()

# --- SAYFA 2: SİPARİŞ EKRANI (Menü Görünümü) ---
elif st.session_state.sayfa == 'market':
    # Üst Bilgi Paneli (Getir Tarzı Yapışkan Hissiyat)
    tutar = sum(item['fiyat'] for item in st.session_state.sepet)
    butce = 400
    kalan = butce - tutar
    
    st.title("Dakikalar İçinde Kapında! ⚡")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Kart Limiti", f"{butce} TL")
    col2.metric("Sepet Tutarı", f"{tutar} TL")
    col3.metric("Kalan Limit", f"{kalan} TL", delta_color="normal" if kalan >= 0 else "inverse")

    if kalan < 0:
        st.error("⚠️ Bakiye yetersiz! Lütfen sepetini ayarla.")
    
    col_onay, col_bosalt = st.columns([1, 1])
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
        if st.button("🗑️ Sepeti Boşalt", use_container_width=True):
            st.session_state.sepet = []
            st.rerun()

    st.markdown("---")

    # Ürün Listeleme (Menü Tarzı, Resimli)
    for kategori, urun_listesi in urunler.items():
        st.subheader(kategori)
        cols = st.columns(4) # Yan yana 4 ürün
        for i, urun in enumerate(urun_listesi):
            with cols[i % 4]:
                st.markdown("<div class='product-card'>", unsafe_allow_html=True)
                # GERÇEK RESİM BURADA ÇAĞRILIYOR
                st.image(urun['resim'], use_container_width=True) 
                st.markdown(f"**{urun['ad']}**")
                st.write(f"*{urun['fiyat']} TL*")
                if st.button("Sepete Ekle", key=f"{kategori}_{i}", use_container_width=True):
                    sepete_ekle(urun['ad'], urun['fiyat'])
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

# --- SAYFA 3: BİTİŞ ---
elif st.session_state.sayfa == 'bitis':
    st.balloons()
    st.success("Siparişin alındı! 🛵 Depo görevlimiz ürünlerini hazırlıyor.")
    
    sepet = st.session_state.sepet
    st.write("### Sipariş Özeti:")
    sepet_df = pd.DataFrame(sepet)
    st.dataframe(sepet_df)
        
    if st.button("Yeni Katılımcı İçin Başa Dön", use_container_width=True):
        st.session_state.clear()
        st.rerun()
