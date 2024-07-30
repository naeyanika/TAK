import io
import chardet

dimport streamlit as st
import pandas as pd
import numpy as np
import io
import csv

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

# Function to sum lists or return 0 if input is not a list
def sum_lists(x):
    return sum(x) if isinstance(x, list) else 0

def detect_delimiter(file):
    try:
        sample = file.read(1024).decode('utf-8')
        file.seek(0)
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(sample)
        return dialect.delimiter
    except Exception as e:
        st.error(f"Error saat mendeteksi delimiter: {str(e)}")
        return None

def read_csv_with_detected_delimiter(file):
    try:
        delimiter = detect_delimiter(file)
        if delimiter is None:
            st.error("Tidak dapat mendeteksi delimiter. Menggunakan koma sebagai default.")
            delimiter = ','
        
        df = pd.read_csv(file, delimiter=delimiter, low_memory=False, encoding='utf-8')
        return df
    except Exception as e:
        st.error(f"Error saat membaca file CSV: {str(e)}")
        return None

# File upload
uploaded_files = st.file_uploader("Unggah file CSV", accept_multiple_files=True, type=['csv'])

# Membaca file
dfs = {}
for file in uploaded_files:
    if file is not None:
        df = read_csv_with_detected_delimiter(file)
        if df is not None:
            dfs[file.name] = df
        else:
            st.error(f"Tidak dapat membaca file: {file.name}")

# Process DbSimpanan
if 'DbSimpanan.csv' in dfs:
    df1 = dfs['DbSimpanan.csv']
    df1.columns = df1.columns.str.strip()
    
    st.write("Columns in DbSimpanan.csv:", df1.columns.tolist())
    
    required_columns = ['Client ID', 'Account No']
    if all(col in df1.columns for col in required_columns):
        temp_client_id = df1['Client ID'].copy()
        df1['Client ID'] = df1['Account No']
        df1['Account No'] = temp_client_id
        
        new_column_names = ['NO.', 'DOCUMENT NO.', 'ID ANGGOTA', 'NAMA', 'CENTER', 'KELOMPOK', 'HARI', 'JAM', 'SL', 'JENIS SIMPANAN']
        df1.columns = new_column_names + list(df1.columns[len(new_column_names):])
        
        if 'NO.' in df1.columns:
            df1['NO.'] = df1['NO.'].apply(format_no)
        if 'CENTER' in df1.columns:
            df1['CENTER'] = df1['CENTER'].apply(format_center)
        if 'KELOMPOK' in df1.columns:
            df1['KELOMPOK'] = df1['KELOMPOK'].apply(format_kelompok)
        
        st.write("DbSimpanan setelah diproses:")
        st.write(df1)
    else:
        st.error("Required columns missing in DbSimpanan.csv")

# Process TAK
if 'TAK.csv' in dfs:
    df2 = dfs['TAK.csv']
    df2.columns = df2.columns.str.strip()
    
    st.write("Columns in TAK.csv:", df2.columns.tolist())
    
    required_columns = ['TRANS. DATE', 'ENTRY DATE', 'DOCUMENT NO.']
    if all(col in df2.columns for col in required_columns):
        df2['TRANS. DATE'] = pd.to_datetime(df2['TRANS. DATE'], format='%d/%m/%Y', errors='coerce')
        df2['ENTRY DATE'] = pd.to_datetime(df2['ENTRY DATE'], format='%d/%m/%Y', errors='coerce')
        
        st.write("TAK setelah diproses:")
        st.write(df2)

        # Merge untuk simpanan
        if 'DbSimpanan.csv' in dfs and 'DOCUMENT NO.' in df1.columns:
            merge_columns = ['DOCUMENT NO.', 'ID ANGGOTA', 'NAMA', 'CENTER', 'KELOMPOK', 'HARI', 'JAM', 'SL', 'JENIS SIMPANAN']
            df2_merged = pd.merge(df2, df1[merge_columns], on='DOCUMENT NO.', how='left')

            st.write("TAK setelah VLOOKUP:")
            st.write(df2_merged)

            # Pivot tabel
            if 'ID ANGGOTA' in df2_merged.columns and 'TRANS. DATE' in df2_merged.columns:
                df2_merged['TRANS. DATE'] = df2_merged['TRANS. DATE'].dt.strftime('%d%m%Y')
                df2_merged['DUMMY'] = df2_merged['ID ANGGOTA'].astype(str) + '' + df2_merged['TRANS. DATE'].astype(str)

                pivot_columns = ['ID ANGGOTA', 'DUMMY', 'NAMA', 'CENTER', 'KELOMPOK', 'HARI', 'JAM', 'SL', 'TRANS. DATE']
                if all(col in df2_merged.columns for col in pivot_columns):
                    pivot_table1 = pd.pivot_table(df2_merged,
                                                  values=['DEBIT', 'CREDIT'],
                                                  index=pivot_columns,
                                                  columns='JENIS SIMPANAN',
                                                  aggfunc={'DEBIT': list, 'CREDIT': list},
                                                  fill_value=0)

                    pivot_table1 = pivot_table1.applymap(sum_lists)
                    pivot_table1.columns = [f'{col[0]}_{col[1]}' for col in pivot_table1.columns]
                    pivot_table1.reset_index(inplace=True)
                    pivot_table1['TRANS. DATE'] = pd.to_datetime(pivot_table1['TRANS. DATE'], format='%d%m%Y').dt.strftime('%d/%m/%Y')

                    new_columns5 = [
                        'DEBIT_Simpanan Pensiun', 'DEBIT_Simpanan Pokok', 'DEBIT_Simpanan Sukarela',
                        'DEBIT_Simpanan Wajib', 'DEBIT_Simpanan Hari Raya', 'DEBIT_Simpanan Qurban',
                        'DEBIT_Simpanan Sipadan', 'DEBIT_Simpanan Khusus', 'CREDIT_Simpanan Pensiun',
                        'CREDIT_Simpanan Pokok', 'CREDIT_Simpanan Sukarela', 'CREDIT_Simpanan Wajib',
                        'CREDIT_Simpanan Hari Raya', 'CREDIT_Simpanan Qurban', 'CREDIT_Simpanan Sipadan',
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
                        'Db Qurban', 'Cr Qurban', 'Db Khusus', 'Cr Khusus', 'Db Sihara', 'Cr Sihara',
                        'Db Pensiun', 'Cr Pensiun', 'Db Pokok', 'Cr Pokok', 'Db SIPADAN', 'Cr SIPADAN',
                        'Db Sukarela', 'Cr Sukarela', 'Db Wajib', 'Cr Wajib', 'Db Total', 'Cr Total'
                    ]

                    for col in desired_order:
                        if col not in pivot_table1.columns:
                            pivot_table1[col] = 0

                    pivot_table1 = pivot_table1[desired_order]
                    
                    st.write("Pivot Table TAK:")
                    st.write(pivot_table1)

                    # Download links for pivot tables
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                        pivot_table1.to_excel(writer, index=False, sheet_name='Sheet1')
                    buffer.seek(0)
                    st.download_button(
                        label="Unduh TAK.xlsx",
                        data=buffer.getvalue(),
                        file_name="TAK.xlsx",
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )
                else:
                    st.error("Required columns for pivot table are missing")
            else:
                st.error("Required columns for DUMMY creation are missing")
        else:
            st.error("Required data for merging is missing")
    else:
        st.error("Required columns missing in TAK.csv")
