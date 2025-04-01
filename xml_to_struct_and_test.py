import xml.etree.ElementTree as ET
import random
import os


# 解析 IPXACT 格式的 XML 文件
def parse_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    registers = []
    namespace = {'ipxact': 'http://www.accellera.org/XMLSchema/IPXACT/1685-2014'}
    address_blocks = root.findall('.//ipxact:addressBlock', namespace)

    # 检查 addressBlock 数量
    if len(address_blocks) == 0:
        print("错误：未找到任何 addressBlock。")
        return [], ""
    elif len(address_blocks) > 1:
        print(f"警告：检测到 {len(address_blocks)} 个 addressBlock，仅解析第一个。")

    # 解析第一个 addressBlock
    address_block = address_blocks[0]
    register_elements = address_block.findall('.//ipxact:register', namespace)
    for register in register_elements:
        name = register.find('ipxact:name', namespace).text

        offset_elem = register.find('ipxact:addressOffset', namespace)
        offset = offset_elem.text if offset_elem is not None else "0x0"

        access_elem = register.find('ipxact:access', namespace)
        access = access_elem.text if access_elem is not None else "unknown"

        desc_elem = register.find('ipxact:description', namespace)
        desc = desc_elem.text if desc_elem is not None else ""

        reset_value_elem = register.find('.//ipxact:reset/ipxact:value', namespace)
        reset_value = reset_value_elem.text if reset_value_elem is not None else "0x0"

        registers.append((name, offset, access, desc, reset_value))

    memory_map_name = root.find('.//ipxact:memoryMap/ipxact:name', namespace).text
    module_name = memory_map_name.split('_')[0]

    return registers, module_name


# 生成寄存器结构体 C 代码
def generate_struct_code(registers, module_name):
    # 按偏移量排序寄存器
    registers.sort(key=lambda x: int(x[1], 16))

    code = f"#ifndef {module_name}_H\n"
    code += f"#define {module_name}_H\n\n"
    code += f"/*------------------------------- MODULE_NAME: {module_name} -----------------------*/\n\n"
    code += "typedef struct\n{\n"

    prev_offset = 0
    for i, (name, offset, access, _, _) in enumerate(registers):
        current_offset = int(offset, 16)
        if i > 0 and current_offset > prev_offset + 4:
            # 计算需要插入的保留寄存器数量
            num_reserved = (current_offset - prev_offset - 4) // 4
            for j in range(num_reserved):
                reserved_name = f"RESERVED_{prev_offset + 4 + j * 4:08X}"
                code += f"    uint32_t {reserved_name}; /* Offset: 0x{prev_offset + 4 + j * 4:08X} (reserved) */\n"

        if access == "read-write":
            access_type = "_IO"
        elif access == "read-only":
            access_type = "_O"
        elif access == "write-only":
            access_type = "_I"
        elif access == "reserved":
            access_type = ""
        else:
            access_type = ""

        if access_type:
            code += f"    {access_type} uint32_t {name}; /* Offset: {offset} ({access}) */\n"
        else:
            code += f"    uint32_t {name}; /* Offset: {offset} ({access}) */\n"

        prev_offset = current_offset

    code += f"}} {module_name}_TypeDef;\n\n"

    for name, offset, _, _, _ in registers:
        code += f"#define {module_name}_{name}_OFFSET ({offset})\n"

    code += f"\n#endif /* {module_name}_H */\n"
    return code


# 生成寄存器读写属性测试 C 代码
def generate_test_code(registers, module_name, base_address):
    code = "#include <stdio.h>\n"
    code += "#include <stdlib.h>\n"
    code += "#include <time.h>\n"
    code += f"#include \"{module_name}.h\"\n\n"

    # 定义 read_ahb32 和 write_ahb32 函数
    code += "unsigned long read_ahb32(unsigned long ahb_addr) {\n"
    code += "    volatile unsigned long retval;\n"
    code += "    retval = *(volatile unsigned long *)ahb_addr;\n"
    code += "    return retval;\n"
    code += "}\n\n"
    code += "void write_ahb32(unsigned long ahb_addr, volatile unsigned long write_value) {\n"
    code += "    *(volatile unsigned long *)ahb_addr = write_value;\n"
    code += "}\n\n"

    # 重新定义 read_reg 和 write_reg 函数，使用 read_ahb32 和 write_ahb32
    code += "uint32_t read_reg(uint32_t address) {\n"
    code += "    return (uint32_t)read_ahb32((unsigned long)address);\n"
    code += "}\n\n"
    code += "void write_reg(uint32_t address, uint32_t value) {\n"
    code += "    write_ahb32((unsigned long)address, (volatile unsigned long)value);\n"
    code += "}\n\n"

    code += "void test_register_access(uint32_t base_addr) {\n"
    code += "    srand(time(NULL));\n"
    for name, offset, access, _, reset_value in registers:
        if access == "read-only":
            code += f"    uint32_t rand_val = rand();\n"
            code += f"    uint32_t reg_addr = base_addr + {offset};\n"
            code += f"    write_reg(reg_addr, rand_val);\n"
            code += f"    uint32_t read_val = read_reg(reg_addr);\n"
            code += f"    if (read_val != {reset_value}) {{\n"
            code += f"        printf(\"Error: Read - only register {name} write test failed!\\n\");\n"
            code += "    }\n"
        elif access == "read-write":
            code += f"    uint32_t rand_val = rand();\n"
            code += f"    uint32_t reg_addr = base_addr + {offset};\n"
            code += f"    write_reg(reg_addr, rand_val);\n"
            code += f"    uint32_t read_val = read_reg(reg_addr);\n"
            code += f"    if (read_val != rand_val) {{\n"
            code += f"        printf(\"Error: Read - write register {name} read - write test failed!\\n\");\n"
            code += "    }\n"
        elif access == "write-only":
            code += f"    uint32_t rand_val = rand();\n"
            code += f"    uint32_t reg_addr = base_addr + {offset};\n"
            code += f"    write_reg(reg_addr, rand_val);\n"
            code += f"    printf(\"Write - only register {name} written with value 0x%08X.\\n\", rand_val);\n"
        elif access == "reserved":
            code += f"    uint32_t reg_addr = base_addr + {offset};\n"
            code += f"    uint32_t read_val = read_reg(reg_addr);\n"
            code += f"    if (read_val != 0) {{\n"
            code += f"        printf(\"Error: Reserved register {name} read test failed!\\n\");\n"
            code += "    }\n"
    code += "    printf(\"All register access tests completed.\\n\");\n"
    code += "}\n\n"
    code += "int main() {\n"
    code += f"    uint32_t base_addr = {base_address};\n"
    code += "    test_register_access(base_addr);\n"
    code += "    return 0;\n"
    code += "}\n"
    return code


# 主函数
def main():
    xml_file = input("请输入 XML 文件的路径（若不输入，将使用脚本运行目录下的 XML 文件）: ")
    if not xml_file:
        current_dir = os.getcwd()
        xml_files = [f for f in os.listdir(current_dir) if f.endswith('.xml')]
        if not xml_files:
            print("脚本运行目录下未找到 XML 文件，请手动指定文件路径。")
            return
        xml_file = os.path.join(current_dir, xml_files[0])

    base_address = input("请输入寄存器基地址（十六进制，如 0x10000000）: ")

    registers, module_name = parse_xml(xml_file)

    struct_code = generate_struct_code(registers, module_name)
    test_code = generate_test_code(registers, module_name, base_address)

    with open(f"{module_name}.h", "w") as f:
        f.write(struct_code)

    with open(f"{module_name}_test.c", "w") as f:
        f.write(test_code)


if __name__ == "__main__":
    main()
    