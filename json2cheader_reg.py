import json
import logging
import argparse
import os

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def json_to_cheader(json_file="output.json", cheader_file=None):
    """
    将 JSON 文件转换为 C 语言头文件代码。

    Args:
        json_file (str): JSON 文件的路径，默认为 "output.json"。
        cheader_file (str, optional): C 语言头文件的路径。如果为 None，则使用 MODULE_NAME 作为文件名，默认为 None。
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        module_name = data["MODULE_NAME"]

        # 如果 cheader_file 为 None，则使用 MODULE_NAME 作为文件名
        if cheader_file is None:
            cheader_file = f"{module_name}.h"

        registers = data["REGISTERS"]

        # 生成 C 语言头文件代码
        cheader_code = generate_cheader(module_name, registers)

        # 写入 C 语言头文件
        with open(cheader_file, 'w', encoding='utf-8') as f:
            f.write(cheader_code)

        logging.info("JSON 文件 '{}' 已成功转换为 C 语言头文件 '{}'".format(json_file, cheader_file))

    except FileNotFoundError:
        logging.error(f"错误：文件 '{json_file}' 未找到。")
    except Exception as e:
        logging.exception(f"发生错误：{e}")

def generate_cheader(module_name, registers):
    """
    根据模块名称和寄存器信息生成 C 语言头文件。

    Args:
        module_name (str): 模块名称。
        registers (list): 寄存器信息列表。

    Returns:
        str: 生成的 C 语言头文件代码。
    """

    # 头文件保护
    header_guard = f"""
#ifndef {module_name.upper()}_H
#define {module_name.upper()}_H
"""

    # 头文件注释
    header_comment = f"""
/*------------------------------- MODULE_NAME: {module_name.upper()} -----------------------*/
"""

    # 结构体定义开始
    struct_definition_start = f"""
typedef struct
{{
"""

    # 结构体成员定义
    struct_members = ""
    for register in registers:
        reg_name = register["REG_NAME"].upper()
        reg_type = register["REG_TYPE"]
        reg_address = int(register["ADDRESS"], 16)  # 将地址转换为整数
        reg_desc = register["DESC"]

        if reg_type == "RO":
            access_type = "__I"  # 只读
            reg_address_hex = register["ADDRESS"]
        else:
            access_type = "__IO"  # 读写
            reg_address_hex = register["ADDRESS"]

        struct_members += f"    {access_type} uint32_t {reg_name}; /* Offset: {reg_address_hex} ({reg_type}) {reg_desc} Register */\n"

    # 结构体定义结束
    struct_definition_end = f"""
}} {module_name.upper()}_TypeDef;
"""

    # 地址偏移宏定义
    address_offset_macros = ""
    for register in registers:
        reg_name = register["REG_NAME"].upper()
        reg_address = int(register["ADDRESS"], 16)
        address_offset_macros += f"#define {module_name.upper()}_{reg_name}_OFFSET (0x{reg_address:X})\n"

    # 头文件保护结束
    header_guard_end = f"""
#endif /* {module_name.upper()}_H */
"""

    # 将所有部分组合在一起
    cheader_code = header_guard + header_comment + struct_definition_start + struct_members + struct_definition_end + address_offset_macros + header_guard_end

    return cheader_code

if __name__ == "__main__":
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description="将 JSON 文件转换为 C 语言头文件代码。")
    parser.add_argument("--json_file", help="JSON 文件的路径，默认为 output.json", default="output.json")
    parser.add_argument("--cheader_file", help="C 语言头文件的路径。如果省略，则使用 MODULE_NAME 作为文件名。", default=None)

    # 解析命令行参数
    args = parser.parse_args()

    # 调用 json_to_cheader 函数
    json_to_cheader(args.json_file, args.cheader_file)