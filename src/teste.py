import gdown

file_ids = [
    '1TdIUpSkghOxLmVwWwbYH1GI9ICMUxWv0',  # 2023 (~206 MB)
    '13PSlOxY1JUhN9eJIcDzEUg4Wq5FC0XRJ',  # 2024 (~222 MB)
    '1BUikMurrueItOiAJCEd8YAyNdlrNahMG',  # 2025 (~213 MB)
    'https://drive.google.com/file/d/1ueZjH0-bmqzztEM-x94dAFuZGkTyJoz6/view?usp=drive_link',
]

for idx, file_id in enumerate(file_ids, start=1):
    output_path = f"teste_prf_{file_id}.csv"
    print(f"[{idx}/{len(file_ids)}] Testando download do ID: {file_id}...")
    try:
        # fuzzy=True ajuda a capturar o ID mesmo se houver redirecionamentos do Drive
        result = gdown.download(id=file_id, output=output_path, quiet=False, fuzzy=True)
        if result:
            print(f"-> Sucesso: arquivo baixado em '{output_path}'\n")
        else:
            print(f"-> Falha: não foi possível baixar o ID {file_id}\n")
    except Exception as e:
        print(f"-> Erro ao baixar ID {file_id}: {e}\n")
