import plotly.express as px
import plotly
import streamlit as st
import pandas as pd
#import openai
   
# ===== USER CREDENTIALS =====
from openai import OpenAI
from io import BytesIO
from functools import reduce
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode


# ===== USER CREDENTIALS =====
USER_CREDENTIALS = {
    "admin": "admin123",
    "user1": "pertamina1",
    "rifyal": "rifyal2025"
}

# ===== SESSION LOGIN CHECK =====
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

def login_page():
    st.title("🔐 Login Aplikasi narasight")
    username = st.text_input("👤 Username")
    password = st.text_input("🔑 Password", type="password")

    if st.button("🔓 Login"):
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success(f"✅ Selamat datang, {username}!")
            st.rerun()
        else:
            st.error("❌ Username atau password salah.")

# ===== JALANKAN LOGIN JIKA BELUM MASUK =====
if not st.session_state.logged_in:
    login_page()
    st.stop()

# ===== PAGE CONFIG =====
st.set_page_config(page_title="Join Data App", layout="wide", page_icon="📊")
st.markdown("""
    <style>
        html, body, [class*="css"]  {
            font-family: 'Segoe UI', sans-serif;
        }
        .stApp {
            background-color: #f0f8ff;
        }
        .block-container {
            padding: 2rem 2rem;
        }
        .stSidebar {
            background-color: #dbeafe;
        }
        .stButton>button, .stDownloadButton>button {
            background-color: #3b82f6;
            color: white;
            border-radius: 0.5rem;
            padding: 0.5rem 1rem;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #1e3a8a;
        }

        /* === RUNNING TEXT (Marquee) === */
        .marquee-container {
            width: 100%;
            overflow: hidden;
            white-space: nowrap;
            box-sizing: border-box;
            background: #fef9c3;
            padding: 8px 0;
            border: 1px solid #fde68a;
            border-radius: 6px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            margin-top: 1rem;
            margin-bottom: 1.5rem;
        }
        .marquee-text {
            display: inline-block;
            padding-left: 100%;
            animation: marquee 55s linear infinite; 
            font-weight: bold;
            color: #92400e;
            font-size: 1rem;
        }
        @keyframes marquee {
            0%   { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }

        .narasi-ai {
            background-color: white;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border: 1px solid #e5e7eb;
            margin-top: 1rem;
            color: #111827;
            font-size: 1rem;
        }
    </style>

    <!-- RUNNING TEXT HTML -->
    <div class="marquee-container">
        <div class="marquee-text">
            📢 Info Penting: File utama wajib diupload! Pastikan minimal input 2 file agar proses join data berhasil.
        </div>
    </div>
""", unsafe_allow_html=True)

# ===== SIDEBAR =====
with st.sidebar:
    st.markdown("## 📊 Join Multiple Excel")
    st.markdown("*Tentukan Parameter Key") #Travel Request Number, Booking ID, Invoice No atau Company Code
    st.markdown("---")

# ===== FILE UPLOAD =====
st.subheader("📥 Upload File Excel")

data_utama_file = st.file_uploader("🗂️ File Utama (Wajib)", type=["xlsx"], key="mandatory")

col1, col2 = st.columns(2)
data_files = []

with col1:
    data_files.append(st.file_uploader("📄 File Data 1 (Wajib)", type=["xlsx"], key="data1"))
    multi_files = st.file_uploader("📂 File Data 2 (Multi Upload)", type=["xlsx"], accept_multiple_files=True, key="data2")

with col2:
    multi_files = st.file_uploader("📂 File Data 3 (Multi Upload)", type=["xlsx"], accept_multiple_files=True, key="data3")
    multi_files = st.file_uploader("📂 File Data 4 (Multi Upload)", type=["xlsx"], accept_multiple_files=True, key="data4")
    if multi_files:
        data_files.extend(multi_files)
    else:
        data_files.append(None)

# ===== CLEANING FUNCTION =====
def clean_and_cast_columns(df):
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.strip()
            try:
                df[col] = pd.to_numeric(df[col], errors='raise')
            except:
                df[col] = df[col].astype(str)
        elif pd.api.types.is_numeric_dtype(df[col]):
            df[col] = pd.to_numeric(df[col], errors='coerce')
        else:
            df[col] = df[col]
    return df

# ===== JOIN PROSES =====
if data_utama_file:
    try:
        # Load main data
        df_main = pd.read_excel(data_utama_file)
        if "Travel Request Number" not in df_main.columns:
            st.markdown('<div class="warning-box">❌ <strong>Error:</strong> Column "Travel Request Number" not found in main file.</div>', unsafe_allow_html=True)
            st.stop()

        # Data preprocessing
        df_main["Travel Request Number"] = df_main["Travel Request Number"].astype(str).str.strip()
        df_main = df_main.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        df_list = [df_main]

        # Process additional files
        processed_files = 0
        for file in data_files:
            if file:
                df = pd.read_excel(file)
                if "Travel Request Number" not in df.columns:
                    st.markdown(f'<div class="warning-box">⚠️ <strong>Warning:</strong> File "{file.name}" does not have "Travel Request Number" column. Skipped.</div>', unsafe_allow_html=True)
                    continue
                df["Travel Request Number"] = df["Travel Request Number"].astype(str).str.strip()
                df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
                df_list.append(df)
                processed_files += 1

        # Display file processing summary
        if processed_files > 0:
            st.markdown(f'<div class="success-box">🎉 <strong>Success:</strong> Processed {processed_files + 1} files successfully!</div>', unsafe_allow_html=True)

        # Merge function with priority
        def merge_with_priority(df1, df2):
            df_merged = pd.merge(df1, df2, on="Travel Request Number", how="outer", suffixes=("", "_dup"))
            for col in df2.columns:
                if col != "Travel Request Number" and col in df1.columns:
                    df_merged[col] = df_merged[col].combine_first(df_merged[f"{col}_dup"])
                    df_merged.drop(columns=[f"{col}_dup"], inplace=True)
            return df_merged

        join_result = reduce(merge_with_priority, df_list)

        # Hapus kolom kosong total (semua NaN)
        join_result.dropna(axis=1, how='all', inplace=True)

        # Hapus baris yang semua nilainya kosong
        join_result.dropna(how='all', inplace=True)

        # Ganti NaT di kolom datetime menjadi string kosong agar aman untuk diproses dan ditampilkan
        for col in join_result.select_dtypes(include=["datetime", "datetimetz"]).columns:
            join_result[col] = join_result[col].fillna(pd.NaT).astype(str).replace("NaT", "")

        # ===== FITUR SEARCH DI SIDEBAR =====
        st.sidebar.markdown("## 🕵️ Pencarian Data")
        search_keyword = st.sidebar.text_input("🔍 Cari Kata Kunci (semua kolom & semua tipe data)")

        if search_keyword:
            keyword = search_keyword.strip().lower()
            # Konversi semua isi baris menjadi string dan gabungkan
            mask = join_result.apply(lambda row: keyword in ' '.join(row.map(str).str.lower()), axis=1)
            join_result = join_result[mask]

        # ===== FILTER DATA USER-FRIENDLY =====
        st.sidebar.markdown("## 🗂️ Filter Tanggal")

        if 'Check-In Date' in join_result.columns and 'Check-Out Date' in join_result.columns:
            # Pastikan kolom tanggal dalam format datetime
            join_result['Check-In Date'] = pd.to_datetime(join_result['Check-In Date'], errors='coerce')
            join_result['Check-Out Date'] = pd.to_datetime(join_result['Check-Out Date'], errors='coerce')

            # Tentukan rentang minimum dan maksimum
            min_checkin = join_result['Check-In Date'].min()
            max_checkout = join_result['Check-Out Date'].max()

            # Pilihan rentang tanggal dari pengguna
            st.sidebar.markdown("Pilih rentang tanggal untuk menampilkan data:")
            selected_date_range = st.sidebar.date_input(
                label="📅 Periode Tanggal (Check-In s.d Check-Out)",
                value=(min_checkin, max_checkout),
                min_value=min_checkin,
                max_value=max_checkout
            )

            if isinstance(selected_date_range, tuple) and len(selected_date_range) == 2:
                start_date, end_date = selected_date_range
                filtered = join_result[
                    (join_result['Check-In Date'] <= pd.to_datetime(end_date)) &
                    (join_result['Check-Out Date'] >= pd.to_datetime(start_date))
                ]
                join_result = filtered

                # Tampilkan keterangan hasil filter
                st.sidebar.success(
                    f"📆 Menampilkan data dari {start_date.strftime('%d %b %Y')} - {end_date.strftime('%d %b %Y')}\n"
                    f"📄 Jumlah data: {len(join_result)}"
                )
        else:
            st.sidebar.warning("Kolom 'Check-In Date' dan/atau 'Check-Out Date' tidak ditemukan.")

        if 'Company Code' in join_result.columns:
            labels = ['Semua'] + sorted(join_result['Company Code'].dropna().astype(str).unique().tolist())
            selected_code = st.sidebar.selectbox("🎫 Company Code", labels)
            if selected_code != "Semua":
                join_result = join_result[join_result['Company Code'].astype(str) == selected_code]

        # ===== PREVIEW DATA INTERAKTIF =====
        st.markdown("## 👀 Preview Data")
        gb = GridOptionsBuilder.from_dataframe(join_result)
        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
        gb.configure_default_column(filterable=True, sortable=True, resizable=True)
        gridOptions = gb.build()
        AgGrid(
            join_result,
            gridOptions=gridOptions,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            fit_columns_on_grid_load=False,  # penting! biar gak rata semua
            height=400,
            enable_enterprise_modules=False,
            allow_unsafe_jscode=True,  # supaya bisa JS auto resize
            custom_js="""
            function(e) {
                let api = e.api;
                api.sizeColumnsToFit();
                setTimeout(function() {
                    const allColumnIds = [];
                    api.getColumnDefs().forEach(function(colDef) {
                        allColumnIds.push(colDef.field);
                    });
                    api.autoSizeColumns(allColumnIds, false);
                }, 100);
            }
            """
        )

        # ===== INSIGHT =====
        st.markdown("---")
        st.markdown("## 🗂️ File Info")

        # Hitung ukuran dan info dasar
        data_size_bytes = join_result.memory_usage(deep=True).sum()
        data_size_mb = data_size_bytes / (1024 ** 2)

        # Voucher counts
        voucher_counts = {}
        if 'Voucher Hotel' in join_result.columns:
            join_result['Voucher Hotel'] = join_result['Voucher Hotel'].astype(str).str.strip()
            voucher_counts = join_result['Voucher Hotel'].value_counts(dropna=False).to_dict()

        # Ambil nilai spesifik untuk 'Yes' dan 'nan'
        voucher_yes = voucher_counts.get('Yes', 0)
        voucher_no = voucher_counts.get('No', 0)
        voucher_nan = voucher_counts.get('nan', 0)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("📁 Ukuran Join Data", f"{data_size_mb:.2f} MB")
            st.metric("🧾 Total Baris", f"{len(join_result)}")
            st.metric("📊 Total Kolom", f"{join_result.shape[1]}")
            st.metric("🎟️ Voucher 'nan' (blank)", f"{voucher_nan}")

        with col2:
            st.metric("🏢 Perusahaan Unik", f"{join_result['Company Code'].nunique() if 'Company Code' in join_result.columns else 0}")
            st.metric("🧑‍💼 Employee Number", f"{join_result['Employee Number'].nunique() if 'Employee Number' in join_result.columns else 0}")
            st.metric("🎟️ Voucher 'Yes'", f"{voucher_yes}")

        with col3:
            st.metric("🏨 Hotel Unik", f"{join_result['Hotel Name'].nunique() if 'Hotel Name' in join_result.columns else 0}")
            if 'Number of Rooms Night' in join_result.columns:
                total_night = join_result['Number of Rooms Night'].sum()
                st.metric("🛏️ Total Room Night", f"{total_night:,.0f}")
                st.metric("🎟️ Voucher 'No'", f"{voucher_no}")


        # 1 Kilobyte (KB) = 1024 Bytes
        # 1 Megabyte (MB) = 1024 KB = 1024 × 1024 = 1,048,576 Bytes
        # Jadi:
        # Bytes ÷ (1024 ** 2) = Megabytes (MB)

        # st.markdown(f"- Total Ukuran Data Gabungan: **{data_size_mb:.2f} MB**")
        # st.markdown(f"- Total Baris Data: **{len(join_result)}**")
        # st.markdown(f"- Total Kolom Data: **{join_result.shape[1]}**")
        # st.markdown(f"- Perusahaan Unik: **{join_result['Company Code'].nunique() if 'Company Code' in join_result.columns else 0}**")
        # st.markdown(f"- Employee Number: **{join_result['Employee Number'].nunique() if 'Employee Number' in join_result.columns else 0}**")
        #st.markdown(f"- Nama Hotel Unik: **{join_result['Hotel Name'].nunique() if 'Hotel Name' in join_result.columns else 0}**")

        #if 'Number of Rooms Night' in join_result.columns:
            #st.markdown(f"- Total Room Night: **{join_result['Number of Rooms Night'].sum():,.0f}**")

        # if 'Voucher Hotel' in join_result.columns:
            # join_result['Voucher Hotel'] = join_result['Voucher Hotel'].astype(str).str.strip()
            # voucher_counts = join_result['Voucher Hotel'].value_counts(dropna=False)
            # for value, count in voucher_counts.items():
                # st.markdown(f"- Jumlah Data Voucher Hotel = '{value}': **{count}**")

        # ===== ANALISA TOP 10 (PLOTLY + TABEL) =====
        st.markdown("## 📊 Summarized")
        def plot_top(df, col, title):
                top = df[col].value_counts().head(10).sort_values(ascending=True).reset_index()
                top.columns = [col, 'Jumlah']
                col1, col2 = st.columns([3, 1])  # 60:40
                with col1:
                    fig = px.bar(
                        top,
                        x='Jumlah',
                        y=col,
                        orientation='h',
                        title=title,
                        text='Jumlah'
                    )
                    fig.update_layout(yaxis=dict(categoryorder='total ascending'))
                    st.plotly_chart(fig, use_container_width=True)
                with col2:
                    st.markdown(f"#### 📋 Top 10: {col}")
                    st.dataframe(top.sort_values("Jumlah", ascending=False), use_container_width=True)

        if 'City' in join_result.columns:
            plot_top(join_result, 'City', '🏙️ Top 10 City')
        else:
            st.info("Kolom 'City' tidak ditemukan.")

        if 'Name' in join_result.columns:
            plot_top(join_result, 'Name', '👤 Top 10 Employee Name')
        else:
            st.info("Kolom 'Employee Name' tidak ditemukan.")

        if 'Traveling Purpose' in join_result.columns:
            plot_top(join_result, 'Traveling Purpose', '👤 Top 10 Traveling Purpose')
        else:
            st.info("Kolom 'Traveling Purpose' tidak ditemukan.")

        possible_dirs = [c for c in join_result.columns if 'direktorat' in c.lower() or 'directorate' in c.lower()]
        if possible_dirs:
            plot_top(join_result, possible_dirs[0], f"🏢 Top 10 {possible_dirs[0]}")
        else:
            st.info("Kolom 'Direktorat' tidak ditemukan.")

        if 'Nama Fungsi' in join_result.columns:
            plot_top(join_result, 'Nama Fungsi', '🧩 Top 10 Nama Fungsi')
        else:
            st.info("Kolom 'Nama Fungsi' tidak ditemukan.")        

        #if 'Hotel Name' in join_result.columns:
            #plot_top(join_result, 'Hotel Name', '🏨 Top 10 Hotel Name by Room Night')
        #else:
            #st.info("Kolom 'Hotel Name' tidak ditemukan.")
        
        # ===== FUNGSI ANALISA ROOM NIGHT =====
        def show_room_night_analysis(df):
            #st.markdown("## 🛏️ Analisa Berdasarkan Room Night")

            if 'Hotel Name' in df.columns and 'Number of Rooms Night' in df.columns:
                #st.markdown("### 🏨 Top 10 Hotel berdasarkan Total Room Night")
                df['Number of Rooms Night'] = pd.to_numeric(df['Number of Rooms Night'], errors='coerce')
                top_hotel_rooms = (
                    df.groupby('Hotel Name')['Number of Rooms Night']
                    .sum()
                    .sort_values(ascending=False)
                    .head(10)
                    .reset_index()
                )

                col1, col2 = st.columns([3, 1])
                with col1:
                    fig_top_hotel = px.bar(
                        top_hotel_rooms,
                        x='Number of Rooms Night',
                        y='Hotel Name',
                        orientation='h',
                        title='🏨 Top 10 Hotel berdasarkan Jumlah Room Night',
                        text='Number of Rooms Night'
                    )
                    fig_top_hotel.update_layout(yaxis=dict(categoryorder='total ascending'))
                    st.plotly_chart(fig_top_hotel, use_container_width=True)
                with col2:
                    st.markdown("#### 📋 Tabel Top 10 Hotel")
                    st.dataframe(top_hotel_rooms, use_container_width=True)
            else:
                st.info("Data tidak memiliki kolom 'Hotel Name' dan/atau 'Number of Rooms Night'.")

            if 'Check-In Date' in df.columns and 'Number of Rooms Night' in df.columns:
                #st.markdown("### 📈 Time Series: Jumlah Room Night per Tanggal Check-In")
                df['Check-In Date'] = pd.to_datetime(df['Check-In Date'], errors='coerce')
                df['Number of Rooms Night'] = pd.to_numeric(df['Number of Rooms Night'], errors='coerce')

                df_ts = (
                    df.groupby('Check-In Date')['Number of Rooms Night']
                    .sum()
                    .reset_index()
                    .sort_values('Check-In Date')
                )

                fig_ts = px.line(
                    df_ts,
                    x='Check-In Date',
                    y='Number of Rooms Night',
                    markers=True,
                    title='📅 Tren Room Night per Tanggal Check-In'
                )
                fig_ts.update_traces(line=dict(color="#1e40af"))
                fig_ts.update_layout(xaxis_title="Tanggal Check-In", yaxis_title="Jumlah Room Night")
                st.plotly_chart(fig_ts, use_container_width=True)
            else:
                st.info("Data tidak memiliki kolom 'Check-In Date' dan/atau 'Number of Rooms Night'.")
        
        def show_voucher_amount_analysis(df):
            if 'Check-In Date' in df.columns and 'Voucher Hotel Amount' in df.columns:
                df['Check-In Date'] = pd.to_datetime(df['Check-In Date'], errors='coerce')
                # Bersihkan data angka dari simbol atau string
                #df['Voucher Hotel Amount'] = df['Voucher Hotel Amount'].astype(str).replace('[^\d.]', '', regex=True).astype(float)
                df['Voucher Hotel Amount'] = (
                    df['Voucher Hotel Amount']
                    .astype(str)
                    .replace('[^\d.,]', '', regex=True)
                    .str.replace(',', '', regex=False)  # hilangkan koma ribuan jika ada
                )

                df['Voucher Hotel Amount'] = pd.to_numeric(df['Voucher Hotel Amount'], errors='coerce')                

                df_voucher_ts = (
                    df.groupby('Check-In Date')['Voucher Hotel Amount']
                    .sum()
                    .reset_index()
                    .sort_values('Check-In Date')
                )

                fig_voucher_ts = px.line(
                    df_voucher_ts,
                    x='Check-In Date',
                    y='Voucher Hotel Amount',
                    markers=True,
                    title='💵 Tren Voucher Hotel Amount per Tanggal Check-In'
                )
                fig_voucher_ts.update_traces(line=dict(color="#047857"))
                fig_voucher_ts.update_layout(
                    xaxis_title="Tanggal Check-In",
                    yaxis_title="Jumlah Voucher Hotel (Amount)",
                    yaxis_tickformat=',.0f'
                )
                st.plotly_chart(fig_voucher_ts, use_container_width=True)
            else:
                st.info("Data tidak memiliki kolom 'Check-In Date' dan/atau 'Voucher Hotel Amount'.")

        def show_forecasting_travel_request(df):
            st.markdown("### Prediksi Jumlah Perjalanan (Travel Request)")

            # Deskripsi kecil menggunakan HTML <small>
            st.markdown(
                """
                <small style='color:gray'>
                Prophet adalah alat bantu untuk memprediksi data berdasarkan waktu, seperti jumlah pemesanan hotel atau penjualan setiap hari.<br>
                Prophet mengenali pola berulang seperti musim liburan, hari kerja vs akhir pekan, atau jam sibuk harian.<br>
                Prophet is open source software released by Facebook’s Core Data Science team.<br>
                <br>
                </small>
                """,
                unsafe_allow_html=True
            )

            if 'Check-In Date' not in df.columns:
                st.warning("Kolom 'Check-In Date' tidak ditemukan.")
                return

            if st.button("Analyze Forecast"):
                df = df.copy()
                df['Check-In Date'] = pd.to_datetime(df['Check-In Date'], errors='coerce')
                df['month'] = df['Check-In Date'].dt.to_period('M').dt.to_timestamp()
                df_monthly = df.groupby('month').agg({'Travel Request Number': 'count'}).reset_index()
                df_monthly.columns = ['ds', 'y']

                # Filter data kosong
                df_monthly = df_monthly[df_monthly['y'] > 0]

                if df_monthly.empty or len(df_monthly) < 4:
                    st.warning("Data tidak cukup untuk membuat prediksi.")
                    return

                from prophet import Prophet
                import plotly.graph_objs as go

                with st.spinner("🔄 Memprediksi tren perjalanan..."):
                    model = Prophet()
                    model.fit(df_monthly)

                    future = model.make_future_dataframe(periods=6, freq='M')
                    forecast = model.predict(future)

                    # Plot hasil aktual dan prediksi
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=df_monthly['ds'], y=df_monthly['y'], mode='lines+markers', name='Aktual'))
                    fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], mode='lines', name='Prediksi'))

                    fig.update_layout(
                        title='📈 Prediksi Jumlah Perjalanan (Travel Request) per Bulan',
                        xaxis_title='Bulan',
                        yaxis_title='Jumlah Travel Request',
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig, use_container_width=True)


        # ===== PANGGIL FUNGSI ANALISA ROOM NIGHT & VOUCHER AMOUNT =====
        show_room_night_analysis(join_result)
        show_voucher_amount_analysis(join_result)
        show_forecasting_travel_request(join_result)

                # ===== OPEN AI =====
        #openai.api_key = st.secrets["OPENAI_API_KEY"]  # Pastikan ini ditaruh di atas
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

        def generate_narrative(df, topic="summary"):
            """Menghasilkan narasi analitik dari data menggunakan OpenAI"""
            try:
                if df.empty:
                    return "Data tidak tersedia untuk dianalisis."

                sample_text = df.head(20).to_string(index=False)
                prompt = f"""
        Berikan analisa naratif singkat dan mudah dipahami dari data berikut terkait topik: {topic}. 
        Gunakan gaya bahasa profesional, dan tonjolkan insight menarik jika ada.

        Data:
        {sample_text}
                """

                response = client.chat.completions.create(
                    model="gpt-4",  # Atau gpt-3.5-turbo jika belum punya akses gpt-4
                    messages=[
                        {"role": "system", "content": "Kamu adalah asisten data yang profesional dan mudah dimengerti."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.4,
                    max_tokens=500
                )

                return response.choices[0].message.content

            except Exception as e:
                return f"Gagal menghasilkan narasi: {e}"

        # ===== NARASI GPT BERDASARKAN DATA =====

        with st.expander("🦖 Aku Bantu Kasih Narasi, MAU? (Klik untuk lihat narasi)"):
            topic_desc = st.text_input("Jelaskan topik narasi (misal: ringkasan tren hotel, analisa room night, dsb)", value="..........")
            if st.button("Berikan Narasi"):
                with st.spinner("AI Sedang membuat narasi..."):
                    narrative = generate_narrative(join_result, topic_desc)
                    st.markdown("**Berikut hasilnya:**")
                    st.markdown(f"""<div class="narasi-ai">{narrative}</div>""", unsafe_allow_html=True)

        # ===== DOWNLOAD BUTTON =====
        if st.checkbox("✅ Aktifkan Download"):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                join_result.to_excel(writer, index=False, sheet_name='Joined Data')
            output.seek(0)
            st.download_button(
                "⬇️ Download Excel",
                data=output,
                file_name="joined_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"❌ Terjadi kesalahan saat join/filter: {e}")
else:
    st.info("⬆️ Silakan upload file utama terlebih dahulu.")    

# ===== FOOTER =====
st.markdown("""
<hr style="margin-top: 3rem; margin-bottom: 1rem; border: none; border-top: 1px solid #ccc;" />
<div style='text-align: center; font-size: 0.85rem; color: gray;'>
    📊 Aplikasi Data Relasional narasight | Dibuat dengan ❤️ oleh <a href='https://www.linkedin.com/in/rifyalt/'>Rifyal Tumber</a><br>
    © 2025 - Versi 1.0 | Hubungi +62 878 8103 3781 jika ada kendala teknis
</div>
""", unsafe_allow_html=True)
