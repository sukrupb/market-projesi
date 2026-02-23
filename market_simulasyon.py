import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Kampüs Market Deneyi", page_icon="🛵")

# --- KUSURSUZ CSS HİZALAMA VE TEMA ---
st.markdown("""
    <style>
    .stApp { background-color: #5d3ebc !important; }
    h1, h2, h3, h4, p, span, label, div[data-testid="stMarkdownContainer"] { color: white !important; }
    
    .product-img {
        width: 100%; height: 150px !important; object-fit: cover !important;
        border-radius: 12px; border: 2px solid #ffd300; margin-bottom: 5px;
    }
    .product-text-box {
        height: 60px; display: flex; flex-direction: column;
        justify-content: flex-start; text-align: center;
    }
    .product-title { font-weight: 700; font-size: 15px; line-height: 1.2; margin-bottom: 3px; color: white; }
    .product-price { color: #ffd300; font-weight: 800; font-size: 16px; }

    div.stButton > button:first-child {
        background-color: #ffd300 !important; color: #5d3ebc !important;
        border: none !important; border-radius: 8px !important;
        font-weight: 900 !important; padding: 5px !important;
    }
    div.stButton > button:hover { background-color: #ffecb3 !important; transform: scale(1.02); }
    
    .quantity-text { text-align: center; font-weight: 900; font-size: 20px; color: #ffd300; padding-top: 5px; }
    
    div[data-testid="stMetricLabel"] { color: #e0e0e0 !important; }
    div[data-testid="stMetricValue"] { color: #ffd300 !important; }
    div[data-baseweb="select"] > div { background-color: #4a329c !important; color: white !important; }
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
urunler = {
    "Atıştırmalık & Cips": [
        {"ad": "Patates Cipsi (Büyük)", "fiyat": 45, "resim": "https://images.unsplash.com/photo-1566478989037-e124c1b55523?auto=format&fit=crop&w=400&q=80"},
        {"ad": "Sütlü Çikolata", "fiyat": 25, "resim": "https://images.unsplash.com/photo-1549007994-cb92caebd54b?auto=format&fit=crop&w=400&q=80"},
        {"ad": "Çubuk Kraker", "fiyat": 10, "resim": "https://images.unsplash.com/photo-1599490659213-e2b9527bd087?auto=format&fit=crop&w=400&q=80"},
        {"ad": "Karışık Kuruyemiş", "fiyat": 80, "resim": "https://images.unsplash.com/photo-1599598425947-330026296d11?auto=format&fit=crop&w=400&q=80"},
    ],
    "İçecek & Enerji": [
        {"ad": "Kola (Kutu 330ml)", "fiyat": 30, "resim": "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?auto=format&fit=crop&w=400&q=80"},
        {"ad": "Enerji İçeceği", "fiyat": 50, "resim": "https://images.unsplash.com/photo-1622543925917-763c34d1a86e?auto=format&fit=crop&w=400&q=80"},
        {"ad": "Soğuk Çay", "fiyat": 25, "resim": "https://images.unsplash.com/photo-1556679343-c7306c1976bc?auto=format&fit=crop&w=400&q=80"},
        {"ad": "Doğal Su (1.5L)", "fiyat": 15, "resim": "https://images.unsplash.com/photo-1523362628745-0c100150b504?auto=format&fit=crop&w=400&q=80"},
    ],
    "Pratik Yemek & Dondurma": [
        {"ad": "Dondurulmuş Pizza", "fiyat": 120, "resim": "https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=400&q=80"},
        {"ad": "Hazır Noodle", "fiyat": 15, "resim": "https://images.unsplash.com/photo-1612929633738-8fe01f72810c?auto=format&fit=crop&w=400&q=80"},
        {"ad": "Ton Balığı (3'lü)", "fiyat": 140, "resim": "https://images.unsplash.com/photo-1610832958506-aa56368176cf?auto=format&fit=crop&w=400&q=80"},
        {"ad": "Çubuk Dondurma", "fiyat": 45, "resim": "https://images.unsplash.com/photo-1563805042-7684c8e9e533?auto=format&fit=crop&w=400&q=80"},
    ]
}

# --- OTURUM YÖNETİMİ ---
if 'sepet' not in st.session_state: st.session_state.sepet = []
if 'sayfa' not in st.session_state: st.session_state.sayfa = 'anket'
if 'kullanici_verisi' not in st.session_state: st.session_state.kullanici_verisi = {}

def sepete_ekle(urun_adi, fiyat): st.session_state.sepet.append({"ad": urun_adi, "fiyat": fiyat})
def sepetten_cikar(urun_adi):
    for i, item in enumerate(st.session_state.sepet):
        if item['ad'] == urun_adi:
            st.session_state.sepet.pop(i); break

def veriyi_kaydet():
    try:
        data = st.session_state.kullanici_verisi.copy()
        toplam_tutar = sum(item['fiyat'] for item in st.session_state.sepet)
        sepet_icerigi = ", ".join([item['ad'] for item in st.session_state.sepet])
        durtusel_liste = ["Patates Cipsi (Büyük)", "Sütlü Çikolata", "Kola (Kutu 330ml)", "Enerji İçeceği", "Çubuk Dondurma"]
        durtusel_skor = sum(1 for item in st.session_state.sepet if item['ad'] in durtusel_liste)
        
        satir = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data.get("Cinsiyet"),
            data.get("Sinif"), 
            data.get("Tutum_Skoru"), # Yeni Eklendi: Hipotez 1 için
            data.get("Aclik_Durumu"), # Hipotez 2 için
            toplam_tutar,
            len(st.session_state.sepet),
            durtusel_skor,
            sepet_icerigi
        ]
        
        sheet = google_sheet_baglan()
        if sheet: sheet.append_row(satir); return True
        return False
    except Exception as e: return False

# --- SAYFA 1: GİRİŞ ANKETİ (Hipotez Odaklı) ---
if st.session_state.sayfa == 'anket':
    st.title("Kampüs Market Anketi 🛵")
    st.markdown("""
    <div style='background-color: #4a329c; padding: 15px; border-radius: 10px; border: 1px solid #ffd300;'>
    <b>Senaryo:</b> Saat gece 23:00. Kredi kartında son <b>400 TL</b> limitin var. 
    İstediğin ürünleri sepetine ekle ve siparişi tamamla.
    </div>
    """, unsafe_allow_html=True)
    st.write("") 

    with st.form("giris_formu"):
        col1, col2 = st.columns(2)
        with col1:
            cinsiyet = st.selectbox("Cinsiyetiniz:", ["Kadın", "Erkek", "Belirtmek İstemiyorum"])
            sinif = st.selectbox("Sınıfınız:", ["Hazırlık", "1. Sınıf", "2. Sınıf", "3. Sınıf", "4. Sınıf"])
        with col2:
            # Kritik Araştırma Soruları
            tutum_skoru = st.slider("Maddi konularda kendini nasıl tanımlarsın? (1: Savurgan, 5: Çok Tutumlu)", 1, 5, 3)
            aclik_durumu = st.slider("Şu an fiziksel olarak ne kadar açsın? (1: Tok, 5: Çok Aç)", 1, 5, 3)
        
        if st.form_submit_button("🛒 Markete Gir (Kalan Bakiye: 400 TL)", use_container_width=True):
            st.session_state.kullanici_verisi = {"Cinsiyet": cinsiyet, "Sinif": sinif, "Tutum_Skoru": tutum_skoru, "Aclik_Durumu": aclik_durumu}
            st.session_state.sayfa = 'market'
            st.rerun()

# --- SAYFA 2: SİPARİŞ EKRANI ---
elif st.session_state.sayfa == 'market':
    tutar = sum(item['fiyat'] for item in st.session_state.sepet)
    butce = 400
    kalan = butce - tutar
    
    st.title("Dakikalar İçinde Kapında! ⚡")
    
    with st.container():
        col1, col2, col3 = st.columns(3)
        col1.metric("Kart Limiti", f"{butce} TL")
        col2.metric("Sepet Tutarı", f"{tutar} TL")
        col3.metric("Kalan Limit", f"{kalan} TL", delta_color="normal" if kalan >= 0 else "inverse")
    
    if kalan < 0: st.error("⚠️ Bakiye yetersiz! Lütfen sepetini ayarla.")
    
    col_onay, col_bosalt = st.columns([2, 1])
    with col_onay:
        if st.button("💳 Siparişi Onayla", use_container_width=True):
            if kalan < 0: st.warning("Kart bakiyen yetersiz!")
            elif tutar == 0: st.warning("Sepetin boş!")
            else:
                if veriyi_kaydet(): st.session_state.sayfa = 'bitis'; st.rerun()
                else: st.error("Sipariş kaydedilemedi. İnternet sorunu olabilir.")
    with col_bosalt:
        if st.button("🗑️ Boşalt", use_container_width=True): st.session_state.sepet = []; st.rerun()

    st.markdown("---")

    for kategori, urun_listesi in urunler.items():
        st.subheader(kategori)
        cols = st.columns(3) 
        for i, urun in enumerate(urun_listesi):
            adet = sum(1 for item in st.session_state.sepet if item['ad'] == urun['ad'])
            with cols[i % 3]:
                st.markdown(f"<img src='{urun['resim']}' class='product-img'>", unsafe_allow_html=True)
                st.markdown(f"<div class='product-text-box'><div class='product-title'>{urun['ad']}</div><div class='product-price'>{urun['fiyat']} TL</div></div>", unsafe_allow_html=True)
                
                if adet == 0:
                    if st.button("Sepete Ekle", key=f"add_{kategori}_{i}", use_container_width=True): sepete_ekle(urun['ad'], urun['fiyat']); st.rerun()
                else:
                    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
                    with btn_col1:
                        if st.button("➖", key=f"min_{kategori}_{i}", use_container_width=True): sepetten_cikar(urun['ad']); st.rerun()
                    with btn_col2: st.markdown(f"<div class='quantity-text'>{adet}</div>", unsafe_allow_html=True)
                    with btn_col3:
                        if st.button("➕", key=f"plus_{kategori}_{i}", use_container_width=True): sepete_ekle(urun['ad'], urun['fiyat']); st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)

# --- SAYFA 3: BİTİŞ VE DAVRANIŞSAL ANALİZ ŞOVU ---
elif st.session_state.sayfa == 'bitis':
    st.balloons()
    st.success("Siparişin alındı! Katılımın için teşekkürler.")
    
    # --- YENİ: PSİKOLOJİK GERİ BİLDİRİM (BEYAN SAPMASI) ---
    tutar = sum(item['fiyat'] for item in st.session_state.sepet)
    tutum_beyani = st.session_state.kullanici_verisi.get("Tutum_Skoru", 3)
    
    st.markdown("### 🧠 Tüketici Profili Analizin:")
    
    if tutum_beyani >= 4 and tutar > 250:
        st.error("🚨 **BEYAN SAPMASI TESPİT EDİLDİ!**\nGirişte kendini 'Çok Tutumlu' olarak tanımlamıştın ama 400 TL'lik kısıtlı bütçenin büyük kısmını harcadın. Dijital uyaranlar rasyonel karar almanı engellemiş olabilir!")
    elif tutum_beyani <= 2 and tutar > 250:
        st.warning("💸 **TUTARLI SAVURGAN:**\nAnkette belirttiğin gibi parayı harcamaktan çekinmedin. Kısıtlı bütçe seni strese sokmamış görünüyor.")
    elif tutum_beyani >= 4 and tutar <= 150:
        st.info("🛡️ **ÇELİK İRADE:**\nHem tutumluyum dedin hem de gerçekten az para harcadın. Dijital pazarlama taktikleri senin üzerinde işe yaramıyor!")
    else:
        st.info("⚖️ **DENGELİ TÜKETİCİ:**\nBütçeni ve anlık isteklerini dengeli bir şekilde yönettin.")
        
    st.write("### Sipariş Özeti:")
    st.markdown("""<style>div[data-testid="stDataFrame"] {background-color: white; padding: 10px; border-radius: 10px;}</style>""", unsafe_allow_html=True)
    sepet_df = pd.DataFrame(st.session_state.sepet)
    st.dataframe(sepet_df, use_container_width=True)
        
    if st.button("Yeni Katılımcı İçin Başa Dön", use_container_width=True):
        st.session_state.clear()
        st.rerun()
