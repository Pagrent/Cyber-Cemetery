import json
import os

def generate_json_files(count):
    """
    根据给定的数量，生成指定个数的JSON文件。

    Args:
        count (int): 要生成的文件数量。
    """
    if count <= 0:
        print("请输入一个大于0的数字。")
        return

    # 定义基础数据结构
    base_data = {
        "avatar": "/assets/m.png",
        "epitaph": "Here lies the echo of a digital dream.\nA fragment of consciousness, forever linked to the void.",
        "created": "2026-01-18",
        "links": [
            {"url": "http://example.com", "title": "Example Link"},
            {"url": "https://github.com/cybersoul", "title": "GitHub Profile"}
        ]
    }

    for i in range(1, count + 1):
        # 构建每个文件的唯一数据
        data_to_save = base_data.copy()
        data_to_save["id"] = str(i)
        data_to_save["name"] = f"CyberSoul{i}"
        # 将序号追加到epitaph的末尾
        data_to_save["epitaph"] = base_data["epitaph"] + f"\n{i}"

        # 文件名与ID一致
        filename = f"{i}.json"

        # 写入文件
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)

        print(f"已生成: {filename}")

if __name__ == "__main__":
    try:
        num_files_str = input("请输入要生成的 JSON 文件数量: ")
        num_files = int(num_files_str)
        generate_json_files(num_files)
    except ValueError:
        print("输入无效，请输入一个整数。")