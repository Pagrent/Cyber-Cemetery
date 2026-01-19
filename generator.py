#!/usr/bin/env python3
"""
墓碑列表静态网站生成器

此脚本读取 'tombstones_raw' 目录下的 JSON 文件，
验证数据，排序，分页，并将结果注入到前端模板中，
最终生成的静态网站文件保存在 'dist' 目录。
现在从 config.yaml 文件读取配置。
"""

import json
import os
import shutil
from pathlib import Path
import math
import yaml # 导入 PyYAML

# --- 从 YAML 配置文件加载配置 ---
CONFIG_FILE_PATH = "config.yaml" # 配置文件名

try:
    with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
except FileNotFoundError:
    print(f"错误：找不到配置文件 '{CONFIG_FILE_PATH}'。请确保配置文件存在。")
    exit(1) # 配置文件缺失，直接退出
except yaml.YAMLError as e:
    print(f"错误：解析配置文件 '{CONFIG_FILE_PATH}' 时出错。详情: {e}")
    exit(1)
except Exception as e:
    print(f"错误：读取配置文件 '{CONFIG_FILE_PATH}' 时发生未知错误。详情: {e}")
    exit(1)

# 从配置中读取变量
PER_PAGE = config.get("per_page", 20) # 默认值 20
INPUT_DIR_NAME = config.get("input_dir_name", "tombstones_raw") # 默认值
OUTPUT_DIR_NAME = config.get("output_dir_name", "dist") # 默认值
TEMPLATE_INDEX_PATH = config.get("template_index_path", "index.html") # 默认值
TEMPLATE_JS_PATH = config.get("template_js_path", "js/main.js") # 默认值
TEMPLATE_CSS_PATH = config.get("template_css_path", "css/styles.css") # 默认值
ASSETS_DIR_NAME = config.get("assets_dir_name", "assets") # 默认值
TEMPLATE_PAGE_NAME_FORMAT = config.get("template_page_name_format", "page_{}.html") # 默认值

# --- 常量 ---
DIST_JS_DIR = "js"
DIST_CSS_DIR = "css"
DIST_ASSETS_DIR = ASSETS_DIR_NAME

# --- 其余代码保持不变 ---

def validate_and_load_json(filepath):
    """验证单个 JSON 文件的格式和内容，并返回解析后的数据"""
    filename_without_ext = filepath.stem
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"错误：'{filepath}' 不是有效的 JSON 文件。详情: {e}")
        return None
    except Exception as e:
        print(f"错误：无法读取文件 '{filepath}'。详情: {e}")
        return None

    # 验证必需字段
    required_fields = ["id", "name", "avatar", "epitaph"]
    for field in required_fields:
        if field not in data:
            print(f"错误：'{filepath}' 缺少必需字段 '{field}'")
            return None

    # 验证 ID 类型和格式
    id_str = data.get("id")
    if not isinstance(id_str, str):
        print(f"错误：'{filepath}' 中的 'id' 字段必须是字符串")
        return None

    try:
        id_int = int(id_str)
        if id_int <= 0:
            raise ValueError("ID 必须是正整数")
    except ValueError:
        print(f"错误：'{filepath}' 中的 'id' '{id_str}' 不是有效的正整数")
        return None

    # 验证 ID 与文件名是否匹配
    if str(id_int) != filename_without_ext:
        print(f"错误：'{filepath}' 的文件名 '{filename_without_ext}' 与其 JSON 内容中的 'id' '{id_str}' 不匹配")
        return None

    # 验证可选字段 links 的格式
    links = data.get("links", [])
    if not isinstance(links, list):
        print(f"错误：'{filepath}' 中的 'links' 字段必须是数组")
        return None
    for i, link in enumerate(links):
        if not isinstance(link, dict):
            print(f"错误：'{filepath}' 中的 'links' 数组第 {i} 项不是对象")
            return None
        if "url" not in link or "title" not in link:
            print(f"错误：'{filepath}' 中的 'links' 数组第 {i} 项缺少 'url' 或 'title'")
            return None

    return data

def read_and_validate_data(input_dir_path):
    """读取并验证 input_dir_path 下的所有 JSON 文件"""
    tombstones = []
    json_files = list(input_dir_path.glob("*.json"))

    if not json_files:
        print(f"警告：在 '{input_dir_path}' 目录中未找到任何 .json 文件。")
        return tombstones

    for file_path in json_files:
        print(f"正在处理文件: {file_path.name}")
        data = validate_and_load_json(file_path)
        if data:
            tombstones.append(data)
        # 如果 data 为 None，validate_and_load_json 已打印错误信息，跳过该文件

    return tombstones

def sort_and_paginate_data(all_tombstones, per_page=PER_PAGE): # per_page 参数现在来自配置
    """按 ID 排序并分页"""
    if not all_tombstones:
        print("没有有效的数据进行排序和分页。")
        return [], 0

    # 按 ID 的数值排序
    sorted_tombstones = sorted(all_tombstones, key=lambda x: int(x["id"]))

    total_items = len(sorted_tombstones)
    total_pages = math.ceil(total_items / per_page)

    pages = []
    for page_num in range(1, total_pages + 1):
        start_idx = (page_num - 1) * per_page
        end_idx = start_idx + per_page
        page_data = sorted_tombstones[start_idx:end_idx]
        pages.append({
            "page_num": page_num,
            "data": page_data,
            "total_pages": total_pages
        })

    print(f"排序完成，共 {total_items} 个有效墓碑，分为 {total_pages} 页。")
    return pages, total_pages

def inject_data_to_html_template(template_content, page_data, current_page_num, total_pages):
    """将分页数据注入到 HTML 模板中"""
    # 将 Python 数据结构转换为 JSON 字符串，用于注入到 JavaScript
    page_data_json = json.dumps(page_data, ensure_ascii=False)
    
    # 替换 HTML 模板中的占位符
    # 注意：这里假设 index.html 中有特定的 script 标签用于注入数据
    # 原来的 index.html 结构是这样的：
    # <script>
    #     window.PAGE_DATA = [];
    #     window.CURRENT_PAGE_NUMBER = 1;
    #     window.TOTAL_PAGES = 1;
    # </script>
    # 我们需要替换 [] 和数字
    
    # 使用字符串替换注入数据
    # 查找并替换 PAGE_DATA
    start_marker = 'window.PAGE_DATA = '
    end_marker = '];' # 注意查找 ']'
    start_pos = template_content.find(start_marker)
    if start_pos == -1:
        print("错误：在 HTML 模板中找不到 'window.PAGE_DATA' 的注入点。")
        return template_content # 或者 raise
    start_pos += len(start_marker)
    end_pos = template_content.find(end_marker, start_pos) + 1 # +1 to include ']'
    if end_pos == -1:
        print("错误：在 HTML 模板中找不到 'window.PAGE_DATA' 的结束标记 ']'.")
        return template_content # 或者 raise
    before_data = template_content[:start_pos]
    after_data = template_content[end_pos:]
    new_content = before_data + page_data_json + after_data

    # 替换 CURRENT_PAGE_NUMBER
    # 查找并替换 CURRENT_PAGE_NUMBER
    marker = 'window.CURRENT_PAGE_NUMBER = '
    pos = new_content.find(marker)
    if pos == -1:
        print("错误：在 HTML 模板中找不到 'window.CURRENT_PAGE_NUMBER' 的注入点。")
        return new_content # 或者 raise
    pos += len(marker)
    # 找到数字结束的位置 (通常是分号前)
    num_end_pos = new_content.find(';', pos)
    if num_end_pos == -1:
        print("错误：在 HTML 模板中找不到 'window.CURRENT_PAGE_NUMBER' 的结束分号。")
        return new_content # 或者 raise
    before_num = new_content[:pos]
    after_num = new_content[num_end_pos:]
    new_content = before_num + str(current_page_num) + after_num

    # 替换 TOTAL_PAGES
    marker = 'window.TOTAL_PAGES = '
    pos = new_content.find(marker)
    if pos == -1:
        print("错误：在 HTML 模板中找不到 'window.TOTAL_PAGES' 的注入点。")
        return new_content # 或者 raise
    pos += len(marker)
    num_end_pos = new_content.find(';', pos)
    if num_end_pos == -1:
        print("错误：在 HTML 模板中找不到 'window.TOTAL_PAGES' 的结束分号。")
        return new_content # 或者 raise
    before_num = new_content[:pos]
    after_num = new_content[num_end_pos:]
    final_content = before_num + str(total_pages) + after_num

    return final_content

def copy_static_assets(output_dir_path):
    """复制 JS, CSS, Assets 文件到输出目录"""
    static_dirs_to_copy = [DIST_JS_DIR, DIST_CSS_DIR, DIST_ASSETS_DIR]

    for dir_name in static_dirs_to_copy:
        source_dir = Path(dir_name)
        dest_dir = output_dir_path / dir_name

        if source_dir.is_dir():
            print(f"正在复制静态文件: {source_dir} -> {dest_dir}")
            if dest_dir.exists():
                shutil.rmtree(dest_dir)
            shutil.copytree(source_dir, dest_dir)
        else:
            print(f"警告：静态资源目录 '{source_dir}' 不存在，跳过复制。")

def generate_website():
    """主生成函数"""
    print("--- 开始生成网站 ---")

    input_dir = Path(INPUT_DIR_NAME)
    output_dir = Path(OUTPUT_DIR_NAME)

    if not input_dir.is_dir():
        print(f"错误：输入目录 '{input_dir}' 不存在。请确保它存在并包含 JSON 文件。")
        return

    # 1. 读取并验证数据
    print("步骤 1: 读取并验证源数据...")
    all_tombstones = read_and_validate_data(input_dir)
    if not all_tombstones:
        print("没有有效的数据可以处理，生成终止。")
        return

    # 2. 排序和分页 (现在使用从配置文件读取的 PER_PAGE)
    print("步骤 2: 排序和分页数据...")
    pages, total_pages = sort_and_paginate_data(all_tombstones)

    if total_pages == 0:
        print("分页后没有页面需要生成，生成终止。")
        return

    # 3. 读取 HTML 模板
    print("步骤 3: 读取 HTML 模板...")
    try:
        with open(TEMPLATE_INDEX_PATH, 'r', encoding='utf-8') as f:
            html_template = f.read()
    except FileNotFoundError:
        print(f"错误：找不到 HTML 模板文件 '{TEMPLATE_INDEX_PATH}'")
        return
    except Exception as e:
        print(f"错误：无法读取 HTML 模板文件 '{TEMPLATE_INDEX_PATH}'。详情: {e}")
        return

    # 4. 创建输出目录
    print(f"步骤 4: 创建输出目录 '{output_dir}'...")
    output_dir.mkdir(exist_ok=True)

    # 5. 生成每一页的 HTML 文件
    print("步骤 5: 生成 HTML 页面...")
    for page_info in pages:
        page_num = page_info["page_num"]
        page_data = page_info["data"]

        # 注入数据到模板
        html_content = inject_data_to_html_template(
            html_template,
            page_data,
            page_num,
            total_pages
        )

        # 确定输出文件名 (现在使用从配置文件读取的格式)
        if page_num == 1:
            output_file_path = output_dir / "index.html" # 第一页命名为 index.html
        else:
            output_file_name = TEMPLATE_PAGE_NAME_FORMAT.format(page_num) # 例如 page_2.html
            output_file_path = output_dir / output_file_name

        # 写入文件
        print(f"  正在生成: {output_file_path}")
        try:
            with open(output_file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
        except Exception as e:
            print(f"错误：无法写入文件 '{output_file_path}'。详情: {e}")

    # 6. 复制静态资源 (JS, CSS, Assets)
    print("步骤 6: 复制静态资源...")
    copy_static_assets(output_dir)

    print("--- 网站生成完成 ---")
    print(f"生成的文件已保存在 '{output_dir.absolute()}' 目录中。")

if __name__ == "__main__":
    generate_website()