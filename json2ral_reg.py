import json
import logging
import argparse
import os

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def json_to_ral(json_file="output.json", ral_file=None):
    """
    将 JSON 文件转换为 UVM RAL 模型的 SystemVerilog 代码。

    Args:
    json_file (str): JSON 文件的路径，默认为 "output.json"。
    ral_file (str, optional): RAL 模型的 SystemVerilog 文件的路径。如果为 None，则使用 MODULE_NAME 加 ral_ 前缀命名，默认为 None。
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        module_name = data["MODULE_NAME"]

        # 如果 ral_file 为 None，则使用 MODULE_NAME 加 ral_ 前缀命名
        if ral_file is None:
            ral_file = f"ral_{module_name}.sv"

        registers = data["REGISTERS"]

        # 生成寄存器类代码
        register_classes_code = ""
        for register in registers:
            reg_name = f"ral_reg_{register["REG_NAME"]}"  # 添加前缀 ral_reg_
            reg_width = int(register["WIDTH"])
            fields = register["FIELDS"]
            register_classes_code += generate_register_class(reg_name, reg_width, fields)

        # 生成 RAL 模型代码
        ral_model_code = generate_ral_model(module_name, registers)

        # 将宏定义添加到文件开头
        file_header = f"""`ifndef {module_name.upper()}_RAL_MODEL_SV
`define {module_name.upper()}_RAL_MODEL_SV

import uvm_pkg::*;
"""

        # 将宏定义添加到文件结尾
        file_footer = """
`endif
"""

        # 写入 RAL 模型文件
        with open(ral_file, 'w', encoding='utf-8') as f:
            f.write(file_header + register_classes_code + ral_model_code + file_footer)

        logging.info(f"JSON 文件 '{json_file}' 已成功转换为 RAL 模型文件 '{ral_file}'")

    except FileNotFoundError:
        logging.error(f"错误：文件 '{json_file}' 未找到。")
    except Exception as e:
        logging.exception(f"发生错误：{e}")

def generate_ral_model(module_name, registers):
    """
    根据模块名称和寄存器信息生成 UVM RAL 模型的 SystemVerilog 代码。

    Args:
    module_name (str): 模块名称。
    registers (list): 寄存器信息列表。

    Returns:
    str: 生成的 RAL 模型代码。
    """
    ral_model_code = f"""
class ral_block_{module_name} extends uvm_reg_block;

    `uvm_object_utils(ral_block_{module_name})

    // 寄存器句柄
"""

    # 添加寄存器句柄
    for register in registers:
        reg_name = register["REG_NAME"]
        ral_reg_name = f"ral_reg_{register["REG_NAME"]}"
        ral_model_code += f"    rand {ral_reg_name} {reg_name};\n"

    ral_model_code += f"""

    function new (string name = "ral_block_{module_name}");
        super.new(name, UVM_NO_COVERAGE);
    endfunction

    virtual function void build();

        this.default_map = create_map("", 0, 4, UVM_LITTLE_ENDIAN, 0);
        // 创建寄存器
"""
    # 添加寄存器创建和配置代码
    for register in registers:
        ral_reg_name = f"ral_reg_{register["REG_NAME"]}"
        reg_name = register["REG_NAME"]
        reg_width = int(register["WIDTH"])
        reg_aceess = register.get("ACCESS", "RW")  # 默认为 RW
        reg_address = register["ADDRESS"].replace("0x", "32'h")  # 将 0x 替换为 'h
        ral_model_code += f"""
        {reg_name} = {ral_reg_name}::type_id::create("{reg_name}",,get_full_name());
        {reg_name}.configure(this, null, "{reg_name}");
        {reg_name}.build();
        this.default_map.add_reg(this.{reg_name}, {reg_address}, "{reg_aceess}", 0);
"""

    ral_model_code += f"""
    endfunction

endclass

"""

    return ral_model_code

def generate_register_class(reg_name, reg_width, fields):
    """
    生成 UVM 寄存器类的 SystemVerilog 代码。

    Args:
    reg_name (str): 寄存器名称。
    reg_width (int): 寄存器宽度。
    fields (list): 字段信息列表。

    Returns:
    str: 生成的寄存器类代码。
    """
    register_class_code = f"""
class {reg_name} extends uvm_reg;
    `uvm_object_utils({reg_name})

    rand uvm_reg_field {";\n    rand uvm_reg_field ".join([field["NAME"] for field in fields])};

    function new (string name = "{reg_name}");
        super.new(name, {reg_width}, UVM_NO_COVERAGE);
    endfunction

    virtual function void build();
        // 配置字段
        {"\n        ".join([generate_field_configuration(field, reg_name) for field in fields])}
    endfunction

endclass
"""
    return register_class_code

def generate_field_configuration(field, reg_name):
    """
    生成 UVM 寄存器字段的配置代码。

    Args:
    field (dict): 字段信息。
    reg_name (str): 寄存器名称。

    Returns:
    str: 生成的字段配置代码。
    """
    field_name = field["NAME"]
    field_width = int(field["WIDTH"])
    field_reset = field["RESET"].replace("0x", "'h")  # 将 0x 替换为 'h
    field_access = field.get("ACCESS", "RW")  # 默认为 RW
    field_lsb = field.get("LSB", 0)  # 尝试从 JSON 中获取 LSB，否则默认为 0

    return f"""
        this.{field_name} = uvm_reg_field::type_id::create("{field_name}");
        this.{field_name}.configure(this, {field_width}, {field_lsb}, "{field_access}", 0, {field_reset}, 1, 0, 0);"""

if __name__ == "__main__":
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description="将 JSON 文件转换为 UVM RAL 模型的 SystemVerilog 代码。")
    parser.add_argument("--json_file", help="JSON 文件的路径，默认为 output.json", default="output.json")
    parser.add_argument("--ral_file", help="RAL 模型的 SystemVerilog 文件的路径。如果省略，则使用 MODULE_NAME 加 ral_ 前缀命名。", default=None)

    # 解析命令行参数
    args = parser.parse_args()

    # 调用 json_to_ral 函数
    json_to_ral(args.json_file, args.ral_file)