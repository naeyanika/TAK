import streamlit as st
import pandas as pd
import numpy as np
import io

st.title('Aplikasi Pengolahan TAK')

# Function to format numbers
def format_no(no):
    try:
        if pd.notna(no):
            return f'{int(no):02d}.'
        else:
            return ''
    except (ValueError, TypeError):
        return str(no)

def format_center(center):
    try:
        if pd.notna(center):
            return f'{int(center):03d}'
        else:
            return ''
    except (ValueError, TypeError):
        return str(center)

def format_kelompok(kelompok):
    try:
        if pd.notna(kelompok):
            return f'{int(kelompok):02d}'
        else:
            return ''
    except (ValueError, TypeError):
        return str(kelompok)

# File upload
uploaded_files = st.file_uploader("Unggah file CSV", accept_multiple_files=True)

if uploaded_files:
    # Read CSV files
    dfs = {}
    for file in uploaded_files:
        df = pd.read_csv(file, delimiter=';', low_memory=False)
        dfs[file.name] = df

    # Process DbSimpanan
    if 'DbSimpanan.csv' in dfs:
        df1 = dfs['DbSimpanan.csv']
        df1.columns = df1.columns.str.strip()
        
        temp_client_id = df1['Client ID'].copy()
        df1['Client ID'] = df1['Account No']
        df1['Account No'] = temp_client_id
        
        df1.columns = ['NO.', 'DOCUMENT NO.', 'ID ANGGOTA', 'NAMA', 'CENTER', 'KELOMPOK', 'HARI', 'JAM', 'SL', 'JENIS SIMPANAN'] + list(df1.columns[10:])
        
        df1['NO.'] = df1['NO.'].apply(format_no)
        df1['CENTER'] = df1['CENTER'].apply(format_center)
        df1['KELOMPOK'] = df1['KELOMPOK'].apply(format_kelompok)
        
        st.write("DbSimpanan setelah diproses:")
        st.write(df1)
        
    # Process TAK
    if 'TAK.csv' in dfs:
        df2 = dfs['TAK.csv']
        df2.columns = df2.columns.str.strip()
        
        if 'TRANS. DATE' in df2.columns and 'ENTRY DATE' in df2.columns:
            df2['TRANS. DATE'] = pd.to_datetime(df2['TRANS. DATE'], format='%d/%m/%Y', errors='coerce')
            df2['ENTRY DATE'] = pd.to_datetime(df2['ENTRY DATE'], format='%d/%m/%Y', errors='coerce')
            
            st.write("TAK setelah diproses:")
            st.write(df2)
        else:
            st.error("Kolom 'TRANS. DATE' atau 'ENTRY DATE' tidak ditemukan dalam TAK.csv.")
            
    # Merge untuk simpanan
    if 'df2' in locals() and 'df1' in locals():
        df2_merged = pd.merge(df2, df1[['DOCUMENT NO.', 'ID ANGGOTA', 'NAMA', 'CENTER', 'KELOMPOK', 'HARI', 'JAM', 'SL', 'JENIS SIMPANAN']], on='DOCUMENT NO.', how='left')

        st.write("TAK setelah VLOOKUP:")
        st.write(df2_merged)

        #Pivot tabel 
        df2_merged['TRANS. DATE'] = pd.to_datetime(df2_merged['TRANS. DATE'], format='%d/%m/%Y').dt.strftime('%d%m%Y')
        df2_merged['DUMMY'] = df2_merged['ID ANGGOTA'] + '' + df2_merged['TRANS. DATE']

        pivot_table1 = pd.pivot_table(df2_merged,
                                      values=['DEBIT', 'CREDIT'],
                                      index=['ID ANGGOTA', 'DUMMY', 'NAMA', 'CENTER', 'KELOMPOK', 'HARI', 'JAM', 'SL', 'TRANS. DATE'],
                                      columns='JENIS SIMPANAN',
                                      aggfunc={'DEBIT': list, 'CREDIT': list},
                                      fill_value=0)

        pivot_table1 = pivot_table1.applymap(sum_lists)
        pivot_table1.columns = [f'{col[0]}_{col[1]}' for col in pivot_table1.columns]
        pivot_table1.reset_index(inplace=True)
        pivot_table1['TRANS. DATE'] = pd.to_datetime(pivot_table1['TRANS. DATE'], format='%d%m%Y').dt.strftime('%d/%m/%Y')

        new_columns5 = [
            'DEBIT_Simpanan Pensiun',
            'DEBIT_Simpanan Pokok',
            'DEBIT_Simpanan Sukarela',
            'DEBIT_Simpanan Wajib',
            'DEBIT_Simpanan Hari Raya',
            'DEBIT_Simpanan Qurban',
            'DEBIT_Simpanan Sipadan',
            'DEBIT_Simpanan Khusus',
            'CREDIT_Simpanan Pensiun',
            'CREDIT_Simpanan Pokok',
            'CREDIT_Simpanan Sukarela',
            'CREDIT_Simpanan Wajib',
            'CREDIT_Simpanan Hari Raya',
            'CREDIT_Simpanan Qurban',
            'CREDIT_Simpanan Sipadan',
            'CREDIT_Simpanan Khusus'
        ]

        for col in new_columns5:
            if col not in pivot_table1.columns:
                pivot_table1[col] = 0

        pivot_table1['DEBIT_TOTAL'] = pivot_table1.filter(like='DEBIT').sum(axis=1)
        pivot_table1['CREDIT_TOTAL'] = pivot_table1.filter(like='CREDIT').sum(axis=1)

        rename_dict = {
            'KELOMPOK': 'KEL',
            'DEBIT_Simpanan Hari Raya': 'Db Sihara',
            'DEBIT_Simpanan Pensiun': 'Db Pensiun',
            'DEBIT_Simpanan Pokok': 'Db Pokok',
            'DEBIT_Simpanan Sukarela': 'Db Sukarela',
            'DEBIT_Simpanan Wajib': 'Db Wajib',
            'DEBIT_Simpanan Qurban': 'Db Qurban',
            'DEBIT_Simpanan Sipadan': 'Db SIPADAN',
            'DEBIT_Simpanan Khusus': 'Db Khusus',
            'DEBIT_TOTAL': 'Db Total',
            'CREDIT_Simpanan Hari Raya': 'Cr Sihara',
            'CREDIT_Simpanan Pensiun': 'Cr Pensiun',
            'CREDIT_Simpanan Pokok': 'Cr Pokok',
            'CREDIT_Simpanan Sukarela': 'Cr Sukarela',
            'CREDIT_Simpanan Wajib': 'Cr Wajib',
            'CREDIT_Simpanan Qurban': 'Cr Qurban',
            'CREDIT_Simpanan Sipadan': 'Cr SIPADAN',
            'CREDIT_Simpanan Khusus': 'Cr Khusus',
            'CREDIT_TOTAL': 'Cr Total'
        }

        pivot_table1 = pivot_table1.rename(columns=rename_dict)
        desired_order = [
                'ID ANGGOTA', 'DUMMY', 'NAMA', 'CENTER', 'KEL', 'HARI', 'JAM', 'SL', 'TRANS. DATE',
                'Db Qurban', 'Cr Qurban', 'Db Khusus', 'Cr Khusus', 'Db Sihara', 'Cr Sihara', 'Db Pensiun', 'Cr Pensiun', 'Db Pokok', 'Cr Pokok',
                'Db SIPADAN', 'Cr SIPADAN', 'Db Sukarela', 'Cr Sukarela', 'Db Wajib', 'Cr Wajib', 'Db Total', 'Cr Total'
            ]
        # Tambahkan kolom yang mungkin belum ada dalam DataFrame
        for col in desired_order:
            if col not in pivot_table1.columns:
                pivot_table1[col] = 0

        pivot_table1 = pivot_table1[desired_order]
            
        st.write("Pivot Table TAK:")
        st.write(pivot_table1)

        # Download links for pivot tables
        for name, df in {
            'TAK.xlsx': pivot_table1
        }.items():
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1')
            buffer.seek(0)
            st.download_button(
                label=f"Unduh {name}",
                data=buffer.getvalue(),
                file_name=name,
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
