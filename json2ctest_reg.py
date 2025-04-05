import json
import sys

def generate_test_code(json_file, base_address, test_code_file):
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        module_name = data["MODULE_NAME"]
        registers = data["REGISTERS"]

        # 这里可以使用之前提供的 generate_test_code 函数来生成测试 C 代码
        # 代码省略，你可以根据实际情况实现

        code = f"#include \"{module_name}.h\"\n\n"
        code += "uint32_t read_reg(uint32_t address) {\n"
        code += "    return *(volatile uint32_t*)address;\n"
        code += "}\n\n"
        code += "void write_reg(uint32_t address, uint32_t value) {\n"
        code += "    *(volatile uint32_t*)address = value;\n"
        code += "}\n\n"

        code += "void test_reg_access() {\n"
        code += "    uint32_t base_addr = 0x10000000;\n"
        code += "    uint32_t rand_val;\n"
        code += "    uint32_t read_val;\n\n"

        for reg in registers:
            reg_name = reg["REG_NAME"]
            reg_type = reg["REG_TYPE"]
            offset = reg["OFFSET"]
            reset_val = reg.get("RESET_VALUE", "0x0")

            if reg_type == "RW":
                code += f"    rand_val = rand();\n"
                code += f"    write_reg(base_addr + {offset}, rand_val);\n"
                code += f"    read_val = read_reg(base_addr + {offset});\n"
                code += f"    if (read_val != rand_val) {{\n"
                code += f"        printf(\"{reg_name} RW test failed!\\n\");\n"
                code += "    }\n\n"
            elif reg_type == "RO":
                code += f"    read_val = read_reg(base_addr + {offset});\n"
                code += f"    if (read_val != {reset_val}) {{\n"
                code += f"        printf(\"{reg_name} RO test failed!\\n\");\n"
                code += "    }\n\n"
            elif reg_type == "WO":
                code += f"    write_reg(base_addr + {offset}, 0xDEADBEEF);\n"
                code += f"    printf(\"{reg_name} WO test passed\\n\");\n\n"

        code += "}\n"

        # 写入测试 C 代码文件
        with open(test_code_file, 'w', encoding='utf-8') as f:
            f.write(code)

        print(f"寄存器测试 C 代码已生成：{test_code_file}")

    except FileNotFoundError:
        print(f"错误：文件 '{json_file}' 未找到。")
    except Exception as e:
        print(f"发生错误：{e}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("用法: python json2ctest_reg.py <json_file> <base_address> --test_code_file <test_code_file>")
        sys.exit(1)

    json_file = sys.argv[1]
    base_address = sys.argv[2]
    test_code_file = sys.argv[3]

    generate_test_code(json_file, base_address, test_code_file)