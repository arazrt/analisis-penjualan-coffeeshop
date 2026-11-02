# Analisis Penjualan Coffee Shop

Dashboard analisis penjualan coffee shop berbasis Streamlit untuk memvisualisasikan performa penjualan dari data transaksi harian toko kopi di beberapa lokasi. Proyek ini membantu melihat tren pendapatan, performa per toko, kategori produk, pola waktu penjualan, dan ringkasan metrik utama secara interaktif.

## Fitur utama

- Dashboard KPI: total pendapatan, jumlah transaksi, total item terjual, rata-rata per hari, dan rata-rata per transaksi
- Filter interaktif berdasarkan rentang tanggal, lokasi toko, kategori produk, dan jam operasional
- Visualisasi tren pendapatan bulanan dan harian
- Analisis per toko dan per kategori produk
- Analisis berdasarkan waktu operasional dan pola penjualan
- Fallback upload file CSV bila data tidak tersedia di folder aplikasi
- Design dashboard yang responsif untuk tampilan desktop

## Struktur proyek

- `app1.py` : dashboard analisis
- `coffee-shop-sales-revenue.csv` : dataset transaksi penjualan coffee shop
- `requirements.txt` : daftar dependency Python yang diperlukan
- `analisis_penjualan_coffeeshop.ipynb` : notebook eksplorasi data

## Dataset

Dataset berupa file CSV dengan pemisah `|` dan kolom utama seperti:

- `transaction_id`
- `transaction_date`
- `transaction_time`
- `transaction_qty`
- `store_id`
- `store_location`
- `product_id`
- `unit_price`
- `product_category`
- `product_type`
- `product_detail`

Data ini berisi transaksi coffee shop dengan pendapatan dihitung dari `transaction_qty * unit_price`.

## Persyaratan

Pastikan sudah terinstal:

- Python 3.9+
- pip

## Instalasi

1. Buka terminal atau command prompt di folder proyek.
2. Jalankan perintah berikut:

```bash
pip install -r requirements.txt
```

## Menjalankan aplikasi

Untuk menjalankan dashboard utama:

```bash
streamlit run app.py
```

Atau jika `streamlit` belum masuk ke PATH:

```bash
python -m streamlit run app.py
```

Setelah itu, buka browser dan akses URL yang ditampilkan, biasanya:

```text
http://localhost:8501
```

## Catatan penggunaan

- File dataset default yang dibaca adalah `coffee-shop-sales-revenue.csv` di direktori proyek.
- Jika file tersebut tidak ditemukan, aplikasi akan meminta pengguna untuk mengunggah file CSV melalui sidebar.
- `app1.py` bisa dijalankan dengan cara yang sama, misalnya:

```bash
streamlit run app1.py
```

## Ringkasan

Proyek ini dirancang untuk membantu analisis performa bisnis coffee shop secara visual dan interaktif, terutama untuk melihat tren penjualan, kontribusi produk, dan performa toko berdasarkan data transaksi.
