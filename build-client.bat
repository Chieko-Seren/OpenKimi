@echo off
REM OpenKimi客户端构建脚本
REM 使用: build-client.bat [windows|linux|macos|all]

REM 检查scripts目录是否存在
if not exist scripts (
  echo ❌ 错误: 找不到scripts目录
  exit /b 1
)

REM 检查是否安装了Rust
where cargo >nul 2>&1
if %ERRORLEVEL% neq 0 (
  echo ❌ 错误: 未安装Rust，请访问 https://rustup.rs/ 安装Rust工具链
  exit /b 1
)

REM 进入scripts目录并编译Rust项目
cd scripts
cargo build --release
if %ERRORLEVEL% neq 0 (
  echo ❌ 错误: Rust编译失败，请检查错误信息
  exit /b 1
)

REM 获取参数
set PLATFORM=%1
if "%PLATFORM%"=="" set PLATFORM=all

REM 运行编译后的二进制文件
.\target\release\build-client.exe %PLATFORM%

cd ..
echo.
echo 按任意键退出...
pause >nul 