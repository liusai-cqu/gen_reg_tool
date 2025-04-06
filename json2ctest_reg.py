import json
import sys


def generate_test_code(json_file, base_address, test_code_file):
    try:
        # 打开并读取 JSON 文件
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        module_name = data["MODULE_NAME"]
        registers = data["REGISTERS"]

        # 将 base_address 转为整数（支持16进制输入）
        base_addr_int = int(base_address, 16)

        # 生成代码的头部信息
        code = f"#include <stdio.h>\n"
        code += f"#include <stdlib.h>\n"
        code += f"#include <time.h>\n"
        code += f"#include \"{module_name}.h\"\n\n"

        # 定义读写寄存器函数
        code += """
unsigned long read_ahb32(unsigned long ahb_addr) {
    volatile unsigned long retval;
    retval = *(volatile unsigned long *)ahb_addr;
    return retval;
}

void write_ahb32(unsigned long ahb_addr, volatile unsigned long write_value) {
    *(volatile unsigned long *)ahb_addr = write_value;
}

uint32_t read_reg(uint32_t address) {
    return (uint32_t)read_ahb32((unsigned long)address);
}

void write_reg(uint32_t address, uint32_t value) {
    write_ahb32((unsigned long)address, (volatile unsigned long)value);
}
"""

        # 测试函数定义
        code += "\nvoid test_register_access(uint32_t base_addr) {\n"
        code += "    srand(time(NULL));\n"

        for reg in registers:
            reg_name = reg["REG_NAME"]
            reg_type = reg["REG_TYPE"]
            address = reg["ADDRESS"]
            reset_value = reg.get("RESET_VALUE", "0x0")
            address_int = int(address, 16)

            # 生成寄存器测试逻辑
            code += f"    // Testing register: {reg_name}\n"
            code += f"    uint32_t reg_addr = base_addr + 0x{address_int:X};\n"

            if reg_type == "RW":
                # Read-Write 测试逻辑
                code += f"    uint32_t rand_val = rand();\n"
                code += f"    write_reg(reg_addr, rand_val);\n"
                code += f"    uint32_t read_val = read_reg(reg_addr);\n"
                code += f"    if (read_val != rand_val) {{\n"
                code += f"        printf(\"Error: Read-Write register {reg_name} failed!\\n\");\n"
                code += f"    }} else {{\n"
                code += f"        printf(\"{reg_name} passed Read-Write test.\\n\");\n"
                code += f"    }}\n\n"

            elif reg_type == "RO":
                # Read-Only 新的测试逻辑：先写随机值，再读，确保返回复位值
                code += f"    uint32_t rand_val = rand();\n"
                code += f"    write_reg(reg_addr, rand_val); // Trying to write to Read-Only register\n"
                code += f"    uint32_t read_val = read_reg(reg_addr);\n"
                code += f"    if (read_val != {reset_value}) {{\n"
                code += f"        printf(\"Error: Read-Only register {reg_name} failed! Expected: {reset_value}, Got: 0x%X\\n\", read_val);\n"
                code += f"    }} else {{\n"
                code += f"        printf(\"{reg_name} passed Read-Only test.\\n\");\n"
                code += f"    }}\n\n"

            elif reg_type == "WO":
                # Write-Only 测试逻辑
                code += f"    uint32_t rand_val = rand();\n"
                code += f"    write_reg(reg_addr, rand_val);\n"
                code += f"    printf(\"Write-Only register {reg_name} written successfully with value 0x%08X.\\n\", rand_val);\n\n"

            elif reg_type == "reserved":
                # Reserved 寄存器测试逻辑
                code += f"    uint32_t read_val = read_reg(reg_addr);\n"
                code += f"    if (read_val != 0) {{\n"
                code += f"        printf(\"Error: Reserved register {reg_name} is not zero as expected!\\n\");\n"
                code += f"    }} else {{\n"
                code += f"        printf(\"{reg_name} is correctly reserved.\\n\");\n"
                code += f"    }}\n\n"

        # 测试结束
        code += "    printf(\"All register access tests completed.\\n\");\n"
        code += "}\n\n"

        # 主函数
        code += "int main() {\n"
        code += f"    uint32_t base_addr = 0x{base_addr_int:X};\n"
        code += "    test_register_access(base_addr);\n"
        code += "    return 0;\n"
        code += "}\n"

        # 写入测试 C 代码文件
        with open(test_code_file, 'w', encoding='utf-8') as f:
            f.write(code)

        print(f"生成的测试代码已保存到：{test_code_file}")

    except FileNotFoundError:
        print(f"错误：文件 '{json_file}' 未找到。")
    except ValueError as e:
        print(f"错误：地址或文件格式无效 - {e}")
    except Exception as e:
        print(f"发生错误：{e}")


# 主函数
if __name__ == "__main__":
    # 参数解析
    if len(sys.argv) < 4:
        print("用法: python3 json2ctest_reg.py <json_file> <base_address> --test_code_file <test_code_file>")
        sys.exit(1)

    json_file = sys.argv[1]
    base_address = sys.argv[2]
    test_code_file = None

    if sys.argv[3] == "--test_code_file" and len(sys.argv) == 5:
        test_code_file = sys.argv[4]
    else:
        print("用法: python3 json2ctest_reg.py <json_file> <base_address> --test_code_file <test_code_file>")
        sys.exit(1)

    # 生成测试代码
    generate_test_code(json_file, base_address, test_code_file)