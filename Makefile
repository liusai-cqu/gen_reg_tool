# Makefile

# 用户可配置的变量
MARKDOWN_FILE ?= README.md  # 默认的 Markdown 文件名
JSON_FILE ?= output.json      # 默认的 JSON 文件名

# Python 脚本
MD2JSON_SCRIPT = md2json_reg.py
JSON2RTL_SCRIPT = json2rtl_reg.py
JSON2CHEADER_SCRIPT = json2cheader_reg.py
JSON2RAL_SCRIPT = json2ral_reg.py

# 获取 MODULE_NAME 的函数 (需要 Python)
GET_MODULE_NAME = python -c 'import json; with open("$(JSON_FILE)", "r") as f: data = json.load(f); print(data["MODULE_NAME"])'

# 默认文件名 (依赖于 MODULE_NAME)
MODULE_NAME = $(shell $(GET_MODULE_NAME))
CHEADER_FILE ?= $(MODULE_NAME).h
RAL_FILE ?= ral_$(MODULE_NAME).sv
RTL_FILE ?= $(MODULE_NAME).v

# 目标
all: generate_output

generate_output: generate_json generate_cheader generate_ral generate_rtl

generate_json: $(MARKDOWN_FILE)
 python $(MD2JSON_SCRIPT) $(MARKDOWN_FILE) $(JSON_FILE)

generate_cheader: $(JSON_FILE)
 python $(JSON2CHEADER_SCRIPT) --json_file $(JSON_FILE) --cheader_file $(CHEADER_FILE)

generate_ral: $(JSON_FILE)
 python $(JSON2RAL_SCRIPT) --json_file $(JSON_FILE) --ral_file $(RAL_FILE)

generate_rtl: $(JSON_FILE)
 python $(JSON2RTL_SCRIPT) --json_file $(JSON_FILE) --rtl_file $(RTL_FILE)

# 清理
clean:
 rm -f $(JSON_FILE) $(CHEADER_FILE) $(RAL_FILE) $(RTL_FILE)

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
 @echo " clean - 删除所有生成的文件"
 @echo ""
 @echo "VARIABLES:"
 @echo " MARKDOWN_FILE - Markdown 文件名 (default: $(MARKDOWN_FILE))"
 @echo " JSON_FILE - JSON 文件名 (default: $(JSON_FILE))"
 @echo " CHEADER_FILE - C 头文件名 (default: $(CHEADER_FILE) or MODULE_NAME.h)"
 @echo " RAL_FILE - RAL 模型文件名 (default: $(RAL_FILE) or ral_MODULE_NAME.sv)"
 @echo " RTL_FILE - RTL 文件名 (default: $(RTL_FILE) or MODULE_NAME.v)"
 @echo ""
 @echo "Example: make MARKDOWN_FILE=my_design.md"