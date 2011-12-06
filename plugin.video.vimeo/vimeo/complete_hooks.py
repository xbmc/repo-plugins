def progress_bar(chunk_info):
    completed = (chunk_info["chunk_id"] + 1) * chunk_info["chunk_size"]
    print completed // chunk_info["total_size"] * 100, "%"
