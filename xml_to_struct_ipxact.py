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

    for addr_block in address_blocks:
        register_elements = addr_block.findall('.//ipxact:register', namespace)
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
    code = f"#ifndef {module_name}_H\n"
    code += f"#define {module_name}_H\n\n"
    code += f"/*------------------------------- MODULE_NAME: {module_name} -----------------------*/\n\n"
    code += "typedef struct\n{\n"

    for name, offset, access, _, _ in registers:
        access_type = "__IO" if access == "read-write" else "__I" if access == "read-only" else "__O"
        code += f"    {access_type} uint32_t {name}; /* Offset: {offset} ({access}) */\n"

    code += f"}} {module_name}_TypeDef;\n\n"

    for name, offset, _, _, _ in registers:
        code += f"#define {module_name}_{name}_OFFSET ({offset})\n"

    code += f"\n#endif /* {module_name}_H */\n"
    return code


# 生成寄存器读写属性测试 C 代码
def generate_test_code(registers, module_name):
    code = "#include <stdio.h>\n"
    code += "#include <stdlib.h>\n"
    code += "#include <time.h>\n"
    code += f"#include \"{module_name}.h\"\n\n"
    code += "// 假设的 read_reg 和 write_reg 函数\n"
    code += "uint32_t read_reg(uint32_t address) {\n"
    code += "    // 这里需要实现具体的读取逻辑\n"
    code += "    return 0;\n"
    code += "}\n\n"
    code += "void write_reg(uint32_t address, uint32_t value) {\n"
    code += "    // 这里需要实现具体的写入逻辑\n"
    code += "}\n\n"

    code += "void test_register_access() {\n"
    code += "    srand(time(NULL));\n"
    for name, offset, access, _, reset_value in registers:
        if access == "read-only":
            random_value = random.randint(0, 0xFFFFFFFF)
            code += f"    uint32_t rand_val = {random_value};\n"
            code += f"    write_reg(0x{offset}, rand_val);\n"
            code += f"    uint32_t read_val = read_reg(0x{offset});\n"
            code += f"    if (read_val != {reset_value}) {{\n"
            code += f"        printf(\"Error: Read - only register {name} write test failed!\\n\");\n"
            code += "    }\n"
        elif access == "read-write":
            random_value = random.randint(0, 0xFFFFFFFF)
            code += f"    uint32_t rand_val = {random_value};\n"
            code += f"    write_reg(0x{offset}, rand_val);\n"
            code += f"    uint32_t read_val = read_reg(0x{offset});\n"
            code += f"    if (read_val != rand_val) {{\n"
            code += f"        printf(\"Error: Read - write register {name} read - write test failed!\\n\");\n"
            code += "    }\n"
        elif access == "reserved":
            code += f"    uint32_t read_val = read_reg(0x{offset});\n"
            code += f"    if (read_val != 0) {{\n"
            code += f"        printf(\"Error: Reserved register {name} read test failed!\\n\");\n"
            code += "    }\n"
    code += "    printf(\"All register access tests completed.\\n\");\n"
    code += "}\n\n"
    code += "int main() {\n"
    code += "    test_register_access();\n"
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

    registers, module_name = parse_xml(xml_file)

    struct_code = generate_struct_code(registers, module_name)
    test_code = generate_test_code(registers, module_name)

    with open(f"{module_name}.h", "w") as f:
        f.write(struct_code)

    with open(f"{module_name}_test.c", "w") as f:
        f.write(test_code)


if __name__ == "__main__":
    main()
    