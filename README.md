# Dashboard Analisis Bike Sharing

Dashboard interaktif untuk analisis data penyewaan sepeda.


## Struktur Folder

```
submission
├── dashboard
│   ├── dashboard.py
│   ├── main_data.csv
│   └── day_data.csv
├── data
│   ├── day.csv
│   └── hour.csv
├── Ray_Siraj_Proyek_Analisis_Data_DS.ipynb
├── README.md
├── requirements.txt
└── url.txt
```

## Setup Environment - Anaconda

```
conda create --name main-ds python=3.11
conda activate main-ds
pip install -r requirements.txt
```

## Setup Environment - Shell/Terminal

```
cd submission
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

## Run Streamlit App

Jalankan dari folder utama proyek (`submission`):

```
streamlit run dashboard/dashboard.py
```