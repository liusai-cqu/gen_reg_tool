# 用户可配置的变量
MARKDOWN_FILE ?= input.md  # 默认的 Markdown 文件名
JSON_FILE ?= output.json      # 默认的 JSON 文件名

# Python 脚本
MD2JSON_SCRIPT = md2json_reg.py
JSON2RTL_SCRIPT = json2rtl_reg.py
JSON2CHEADER_SCRIPT = json2cheader_reg.py
JSON2RAL_SCRIPT = json2ral_reg.py
JSON2CTEST_SCRIPT = json2ctest_reg.py
BASE_ADDRESS ?= 0x10000000  # 寄存器基地址

# 获取 MODULE_NAME 的函数 (需要 Python)
#GET_MODULE_NAME = python3 -c 'import json; with open("$(JSON_FILE)", "r") as f: data = json.load(f); print(data["MODULE_NAME"])'

# 默认文件名 (依赖于 MODULE_NAME)
MODULE_NAME ?= deadbeaf#$(shell $(GET_MODULE_NAME))
CHEADER_FILE ?= $(MODULE_NAME).h
RAL_FILE ?= ral_$(MODULE_NAME).sv
RTL_FILE ?= $(MODULE_NAME).v
TEST_CODE_FILE ?= $(MODULE_NAME)_test.c

# VCS 编译器设置
VCS = vcs
VLOGAN = vlogan
VCS_OPTS = -full64 -sverilog -debug_acc+all -timescale=1ns/1ps -l vcs_comp.log
# UVM 选项
UVM_OPTS = -ntb_opts uvm
# 编译输出目录
BUILD_DIR ?= build
LOG_DIR ?= logs

# 目标
all: generate_output

generate_output: generate_json generate_cheader generate_ral generate_rtl generate_ctest

generate_json: $(MARKDOWN_FILE)
	python3 $(MD2JSON_SCRIPT) $(MARKDOWN_FILE) --json_file $(JSON_FILE)

generate_cheader: $(JSON_FILE)
	python3 $(JSON2CHEADER_SCRIPT) --json_file $(JSON_FILE) --cheader_file $(CHEADER_FILE)

generate_ral: $(JSON_FILE)
	python3 $(JSON2RAL_SCRIPT) --json_file $(JSON_FILE) --ral_file $(RAL_FILE)

generate_rtl: $(JSON_FILE)
	python3 $(JSON2RTL_SCRIPT) $(JSON_FILE) --verilog_file $(RTL_FILE)

# 生成测试 C 代码
generate_ctest: $(JSON_FILE)
	python3 $(JSON2CTEST_SCRIPT) $(JSON_FILE) $(BASE_ADDRESS) --test_code_file $(TEST_CODE_FILE)
	@echo "寄存器测试 C 代码已生成：$(TEST_CODE_FILE)"

# 创建构建目录和日志目录
$(BUILD_DIR) $(LOG_DIR):
	mkdir -p $@

# 新增: 编译目标
compile: compile_rtl compile_ral

# 编译RTL文件
compile_rtl: generate_rtl $(BUILD_DIR) $(LOG_DIR)
	$(VLOGAN) $(VCS_OPTS) $(RTL_FILE) -l $(LOG_DIR)/vlogan_rtl.log
	@echo "RTL文件编译完成: $(RTL_FILE)"

# 编译RAL文件
compile_ral: 
	vcs -sverilog +v2k -full64 -debug_all -ntb_opts uvm -timescale=1ns/1ps -l vcs_comp.log $(RAL_FILE)

# 链接并生成可执行文件
elaborate: compile
	$(VCS) $(VCS_OPTS) $(UVM_OPTS) $(MODULE_NAME) -o $(BUILD_DIR)/simv -l $(LOG_DIR)/vcs_elab.log
	@echo "链接完成，可执行文件: $(BUILD_DIR)/simv"

# 运行仿真
simulate: elaborate
	$(BUILD_DIR)/simv -l $(LOG_DIR)/simulation.log
	@echo "仿真完成"

# 测试编译的RTL模块
test_rtl: compile_rtl
	@echo "可以在这里添加执行RTL测试的命令"

# 测试编译的RAL模型
test_ral: compile_ral
	@echo "可以在这里添加执行RAL测试的命令"

# 清理
clean:
	rm -f $(JSON_FILE) $(CHEADER_FILE) $(RAL_FILE) $(RTL_FILE)
	rm -rf $(BUILD_DIR) $(LOG_DIR)
	rm -rf AN.DB csrc simv* *.daidir *.vpd DVEfiles
	rm -rf *.key vc_hdrs.h ucli.key *.vdb *.log

# 帮助信息
help:
	@echo "Usage: make [TARGET] [VARIABLES]"
	@echo ""
	@echo "TARGETS:"
	@echo " all (default) - 生成所有输出文件"
	@echo " generate_json - 从 Markdown 文件生成 JSON 文件"
	@echo " generate_cheader - 从 JSON 文件生成 C 头文件"
	@echo " generate_ral - 从 JSON 文件生成 RAL 模型文件"
	@echo " generate_rtl - 从 JSON 文件生成 RTL 文件"
	@echo " compile - 编译生成的 RTL 和 RAL 文件"
	@echo " compile_rtl - 仅编译 RTL 文件"
	@echo " compile_ral - 仅编译 RAL 文件"
	@echo " elaborate - 链接并生成可执行文件"
	@echo " simulate - 运行仿真"
	@echo " test_rtl - 测试编译后的 RTL 模块"
	@echo " test_ral - 测试编译后的 RAL 模型"
	@echo " clean - 删除所有生成的文件"
	@echo ""
	@echo "VARIABLES:"
	@echo " MARKDOWN_FILE - Markdown 文件名 (default: $(MARKDOWN_FILE))"
	@echo " JSON_FILE - JSON 文件名 (default: $(JSON_FILE))"
	@echo " CHEADER_FILE - C 头文件名 (default: $(CHEADER_FILE) or MODULE_NAME.h)"
	@echo " RAL_FILE - RAL 模型文件名 (default: $(RAL_FILE) or ral_MODULE_NAME.sv)"
	@echo " RTL_FILE - RTL 文件名 (default: $(RTL_FILE) or MODULE_NAME.v)"
	@echo " BUILD_DIR - 编译输出目录 (default: $(BUILD_DIR))"
	@echo " LOG_DIR - 日志输出目录 (default: $(LOG_DIR))"
	@echo ""
	@echo "Example: make MARKDOWN_FILE=my_design.md"
	@echo "Example: make compile"
	@echo "Example: make simulate"
