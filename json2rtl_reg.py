import json
import logging
import argparse
import os

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def json_to_verilog(json_file, verilog_file=None, apb_data_width=32):
    """
    将 JSON 文件转换为支持 APB 接口访问寄存器的 RTL Verilog 代码。

    Args:
        json_file (str): JSON 文件的路径。
        verilog_file (str, optional): Verilog 文件的路径。如果为 None，则使用 MODULE_NAME 作为文件名，默认为 None。
        apb_data_width (int): APB 数据宽度，默认为 32。
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        module_name = data["MODULE_NAME"]

        # 如果 verilog_file 为 None，则使用 MODULE_NAME 作为文件名
        if verilog_file is None:
            verilog_file = f"{module_name}.v"

        registers = data["REGISTERS"]

        # 生成 Verilog 代码
        verilog_code = generate_verilog(module_name, registers, apb_data_width)

        # 写入 Verilog 文件
        with open(verilog_file, 'w', encoding='utf-8') as f:
            f.write(verilog_code)

        logging.info(f"JSON 文件 '{json_file}' 已成功转换为 Verilog 文件 '{verilog_file}'")

    except FileNotFoundError:
        logging.error(f"错误：文件 '{json_file}' 未找到。")
    except Exception as e:
        logging.exception(f"发生错误：{e}")

def generate_verilog(module_name, registers, apb_data_width):
    """
    根据模块名称和寄存器信息生成 Verilog 代码。

    Args:
        module_name (str): 模块名称。
        registers (list): 寄存器信息列表。
        apb_data_width (int): APB 数据宽度。

    Returns:
        str: 生成的 Verilog 代码。
    """

    # 模块端口定义
    port_list = f"""
    input wire PCLK,
    input wire PRESETn,
    input wire PSEL,
    input wire PENABLE,
    input wire [31:0] PADDR,
    input wire PWRITE,
    input wire [{apb_data_width}-1:0] PWDATA,
    output wire [{apb_data_width}-1:0] PRDATA,
    output wire PREADY,
    output wire PSLVERROR,
    """

    # 添加寄存器字段端口
    for register in registers:
        reg_name = register["REG_NAME"]
        reg_type = register["REG_TYPE"]
        fields = register["FIELDS"]  # 获取字段信息

        for field in fields:
            field_name = field["NAME"]
            field_width = field["WIDTH"]

            if reg_type == "RO":
                port_list += f"    input wire [{int(field_width) - 1}:0] {reg_name}_{field_name}_i,\n"
            else:
                port_list += f"    output wire [{int(field_width) - 1}:0] {reg_name}_{field_name}_o,\n"

    # Remove the last comma and newline
    port_list = port_list.rstrip(",\n") + "\n"

    ports = f"""
module {module_name} (
{port_list}
);
"""

    # 寄存器地址定义
    address_definitions = ""
    for i, register in enumerate(registers):
        address = register["ADDRESS"].replace("0x", "32'h")
        reg_name = register["REG_NAME"]
        address_definitions += f"    localparam ADDR_{reg_name.upper()} = {address};\n"

    # 内部信号定义
    internal_signals = f"""
    reg [{apb_data_width}-1:0] register_data [0:{len(registers) - 1}];
    reg PREADY_reg;
    reg PSLVERROR_reg;
    reg [{apb_data_width}-1:0] PRDATA_reg;
    """

    # 寄存器读写逻辑
    register_rw_logic = f"""
    always @(posedge PCLK) begin
        if (!PRESETn) begin
            PREADY_reg <= 1'b0;
            PSLVERROR_reg <= 1'b0;
            PRDATA_reg <= {apb_data_width}'b0;
            // 初始化寄存器
            {"\n ".join([f"register_data[{i}] <= {apb_data_width}'h0;" for i in range(len(registers))])}
        end else begin
            PREADY_reg <= 1'b0;
            PSLVERROR_reg <= 1'b0;
            if (PSEL) begin
                if (PADDR inside {{ {", ".join(["ADDR_" + register["REG_NAME"].upper() for register in registers])} }}) begin
                    PREADY_reg <= 1'b1;
                    PSLVERROR_reg <= 1'b0;
                    if (PWRITE) begin
                        // 写操作
                        case (PADDR)
                            {"\n ".join([generate_write_case(register, i, apb_data_width) for i, register in enumerate(registers)])}
                            default: begin
                                PSLVERROR_reg <= 1'b1;
                            end
                        endcase
                    end else begin
                        // 读操作
                        case (PADDR)
                            {"\n ".join([generate_read_case(register, i, apb_data_width) for i, register in enumerate(registers)])}
                            default: begin
                                PSLVERROR_reg <= 1'b1;
                                PRDATA_reg <= {apb_data_width}'b0;
                            end
                        endcase
                    end
                end else begin
                    PREADY_reg <= 1'b0;
                    PSLVERROR_reg <= 1'b1;
                end
            end
        end
    end
    """

    # 输出信号赋值
    output_assignments = """
    assign PREADY = PREADY_reg;
    assign PSLVERROR = PSLVERROR_reg;
    assign PRDATA = PRDATA_reg;
    """

    # 添加字段输出赋值
    for i, register in enumerate(registers):
        reg_name = register["REG_NAME"]
        reg_type = register["REG_TYPE"]
        fields = register["FIELDS"]

        # 计算每个字段的起始位
        bit_offset = 0
        for field in fields:
            field_name = field["NAME"]
            field_width = field["WIDTH"]

            if reg_type == "RO":
                # 对于 RO 寄存器，将输入值赋值给 register_data 的相应位
                output_assignments += f" always @* begin register_data[{i}][{bit_offset + field_width - 1}:{bit_offset}] = {reg_name}_{field_name}_i; end\n"
            else:
                # 对于 RW 寄存器，将 register_data 的相应位赋值给输出
                output_assignments += f" assign {reg_name}_{field_name}_o = register_data[{i}][{bit_offset + field_width - 1}:{bit_offset}];\n"

            # 更新下一个字段的起始位
            bit_offset += field_width

    # 模块结束
    module_end = """
endmodule
"""

    verilog_code = ports + address_definitions + internal_signals + register_rw_logic + output_assignments + module_end

    return verilog_code

def generate_write_case(register, index, apb_data_width):
    """
    生成单个寄存器写操作的 case 语句。

    Args:
        register (dict): 寄存器信息。
        index (int): 寄存器索引。
        apb_data_width (int): APB 数据宽度。

    Returns:
        str: 生成的 case 语句。
    """
    reg_name = register["REG_NAME"]
    reg_type = register["REG_TYPE"]
    if reg_type == "RW":
        return f"""
        ADDR_{reg_name.upper()}: begin
            register_data[{index}] <= PWDATA;
        end
        """
    else:
        # 对于 RO 寄存器，忽略写操作
        return f"""
        ADDR_{reg_name.upper()}: begin
            // Read-only register, write ignored
        end
        """

def generate_read_case(register, index, apb_data_width):
    """
    生成单个寄存器读操作的 case 语句。

    Args:
        register (dict): 寄存器信息。
        index (int): 寄存器索引。
        apb_data_width (int): APB 数据宽度。

    Returns:
        str: 生成的 case 语句。
    """
    reg_name = register["REG_NAME"]
    return f"""
    ADDR_{reg_name.upper()}: begin
        PRDATA_reg <= register_data[{index}];
    end
    """

if __name__ == "__main__":
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description="将 JSON 文件转换为支持 APB 接口访问寄存器的 RTL Verilog 代码。")
    parser.add_argument("json_file", help="JSON 文件的路径")
    parser.add_argument("--verilog_file", help="Verilog 文件的路径。如果省略，则使用 MODULE_NAME 作为文件名。", default=None)
    parser.add_argument("--apb_data_width", type=int, help="APB 数据宽度，默认为 32", default=32)

    # 解析命令行参数
    args = parser.parse_args()

    # 调用 json_to_verilog 函数
    json_to_verilog(args.json_file, args.verilog_file, args.apb_data_width)