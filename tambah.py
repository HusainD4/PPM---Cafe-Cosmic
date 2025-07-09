import pandas as pd
import numpy as np

# Buat daftar untuk menampung data
data = []

# Inisialisasi ID_PENILAIAN
id_penilaian = 1

# Jumlah user dan alternatif
jumlah_user = 5
jumlah_alternatif = 30
jumlah_kriteria = 5

# Nilai-nilai dummy (realistis)
np.random.seed(42)
for id_user in range(1, jumlah_user + 1):
    for id_alternatif in range(1, jumlah_alternatif + 1):
        for id_kriteria in range(1, jumlah_kriteria + 1):
            # Nilai disesuaikan berdasarkan jenis kriteria
            if id_kriteria == 1:
                nilai = round(np.random.uniform(1.0, 5.0), 1)  # misalnya: rating performa
            elif id_kriteria == 2:
                nilai = round(np.random.uniform(10.0, 100.0), 1)  # efisiensi daya
            elif id_kriteria == 3:
                nilai = np.random.randint(500000, 3000000)  # harga dalam rupiah
            elif id_kriteria == 4:
                nilai = np.random.randint(1, 10)  # jumlah core
            elif id_kriteria == 5:
                nilai = np.random.randint(1, 16)  # jumlah thread
            data.append([id_penilaian, id_user, id_alternatif, id_kriteria, nilai])
            id_penilaian += 1

# Buat DataFrame
df_penilaian = pd.DataFrame(data, columns=["ID_PENILAIAN", "ID_USER", "ID_ALTERNATIF", "ID_KRITERIA", "NILAI"])

# Simpan ke file Excel
output_path = "penilaian_lengkap.xlsx"
df_penilaian.to_excel(output_path, index=False)

output_path
