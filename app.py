def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"- [{timestamp}] {message}"
    
    # Render の「Logs」タブに出力
    print(log_entry, flush=True)

    # ローカルファイルにもログを記録
    with open(LOG_FILE, "a", encoding="utf-8") as log_file:
        log_file.write(log_entry + "\n")
