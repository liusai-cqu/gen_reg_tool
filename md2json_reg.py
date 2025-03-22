import markdown
from bs4 import BeautifulSoup
import json
import re
import logging
import argparse

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_register_info(reg_rows):
    """从寄存器信息行中提取寄存器信息"""
    register_name = reg_rows[0].find_all('th')[1].text.strip() if len(reg_rows[0].find_all('th')) > 1 else None
    register_description = reg_rows[1].find_all('td')[1].text.strip() if len(reg_rows[1].find_all('td')) > 1 else None
    register_type = reg_rows[2].find_all('td')[1].text.strip() if len(reg_rows[2].find_all('td')) > 1 else None
    return register_name, register_description, register_type

def markdown_to_json(markdown_file, json_file="output.json", html_file="output.html", start_address=0, address_step=4):
    """
    解析 Markdown 文件并将其转换为包含多个寄存器信息的 JSON 格式，并添加地址分配功能。

    Args:
        markdown_file (str): Markdown 文件的路径。
        json_file (str): JSON 文件的路径，默认为 "output.json"。
        html_file (str): HTML 文件的路径，默认为 "output.html"。
        start_address (int): 起始地址，默认为 0。
        address_step (int): 地址步进，默认为 4。
    """
    try:
        with open(markdown_file, 'r', encoding='utf-8') as f:
            markdown_text = f.read()

        # 将 Markdown 内容转换为 HTML
        html = markdown.markdown(markdown_text, extensions=['tables'])

        # 将 HTML 写入文件
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html)

        # 使用 BeautifulSoup 解析 HTML
        soup = BeautifulSoup(html, 'html.parser')

        # 提取模块名称
        module_name_element = soup.find(string=re.compile(r"MODULE_NAME:"))
        module_name = module_name_element.find_parent("h2").text.strip() if module_name_element else None
        if module_name:
            module_name = module_name.replace("MODULE_NAME:", "").strip()

        # 提取所有表格
        tables = soup.find_all('table')

        # 存储寄存器信息的列表
        registers = []

        # 当前地址
        current_address = start_address

        # 循环处理每两个表格（一个寄存器信息表，一个字段信息表）
        for i in range(0, len(tables), 2):
            # 确保存在配对的表格
            if i + 1 >= len(tables):
                logging.warning("缺少与寄存器信息表配对的字段信息表。")
                continue

            reg_table = tables[i]
            field_table = tables[i + 1]

            # 提取寄存器信息
            register_name, register_description, register_type = extract_register_info(reg_table.find_all('tr'))

            # 提取字段信息
            fields = []
            total_width = 0  # 初始化寄存器总宽度
            if field_table:
                field_rows = field_table.find_all('tr')[1:]  # Skip header row
                for row in field_rows:
                    cols = row.find_all('td')
                    if len(cols) == 5:
                        try:
                            field = {
                                "NAME": cols[0].text.strip(),
                                "WIDTH": int(cols[1].text.strip()),  # 转换为整数
                                "RESET": cols[2].text.strip(),
                                "TYPE": cols[3].text.strip(),
                                "DESC": cols[4].text.strip()
                            }
                            fields.append(field)
                            total_width += field["WIDTH"]  # 累加字段宽度
                        except ValueError as e:
                            logging.error(f"字段宽度不是有效的整数：{e}")
                            continue

            # 构建寄存器数据
            register = {
                "REG_NAME": register_name,
                "DESC": register_description,
                "REG_TYPE": register_type,
                "ADDRESS": hex(current_address),  # 添加地址信息
                "FIELDS": fields,
                "WIDTH": total_width  # 添加寄存器总宽度
            }
            registers.append(register)

            # 更新地址
            current_address += address_step

        # 构建 JSON 数据
        data = {
            "MODULE_NAME": module_name,
            "REGISTERS": registers
        }

        # 写入 JSON 文件
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        logging.info(f"Markdown 文件 '{markdown_file}' 已成功转换为 JSON 文件 '{json_file}'")
        logging.info(f"HTML 文件已写入 '{html_file}'")

    except FileNotFoundError:
        logging.error(f"错误：文件 '{markdown_file}' 未找到。")
    except Exception as e:
        logging.exception(f"发生错误：{e}")

if __name__ == "__main__":
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description="将 Markdown 文件转换为包含寄存器信息的 JSON 文件。")
    parser.add_argument("markdown_file", help="Markdown 文件的路径")
    parser.add_argument("--json_file", help="JSON 文件的路径，默认为 output.json", default="output.json")
    parser.add_argument("--html_file", help="HTML 文件的路径，默认为 output.html", default="output.html")
    parser.add_argument("--start_address", type=lambda x: int(x, 0), help="起始地址，默认为 0", default=0)
    parser.add_argument("--address_step", type=int, help="地址步进，默认为 4", default=4)

    # 解析命令行参数
    args = parser.parse_args()

    # 调用 markdown_to_json 函数
    markdown_to_json(args.markdown_file, args.json_file, args.html_file, args.start_address, args.address_step)