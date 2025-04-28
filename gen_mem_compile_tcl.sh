#!/usr/bin/env bash
# 文件：generate_compile_script.sh

# 输出 Tcl 脚本路径
TCL_SCRIPT="compile_all_libs.tcl"

# 1) 写入脚本头部
echo "# Auto-generated library compile script" > "$TCL_SCRIPT"

# 2) 遍历 memory 目录下所有 .pglib 文件
#    使用 -print0 和 xargs -0 为了支持文件名中带空格或特殊字符&#8203;:contentReference[oaicite:3]{index=3}
find memory -type f -name '*.pglib' -print0 \
  | xargs -0 -n1 echo \
  | while IFS= read -r lib; do
    # 3) 提取库名（去掉路径和 .pglib 后缀）&#8203;:contentReference[oaicite:4]{index=4}
    name=$(basename "$lib" .pglib)
    # 4) 写入 read_lib 与 write_lib 命令
    echo "read_lib $lib" >> "$TCL_SCRIPT"
    echo "write_lib $name -format db -output memory/${name}.db" >> "$TCL_SCRIPT"
done

# 5) 添加退出命令
echo "quit" >> "$TCL_SCRIPT"
