# 图片随机测试

一个离线的 Windows 图片随机识别 / 记忆测试小工具。

## 使用方法

1. 运行 `图片随机测试.exe`。
2. 点击“选择文件夹”，选择存放图片的文件夹。
3. 设置本轮测试数量。
4. 点击“开始测试”。
5. 第一遍只看图片；按 `Enter` 或“确定”显示答案。
6. 再按一次 `Enter` / “确定”进入下一张。
7. 测试过程中可点击“上一张”回看上一张；返回后会重新进入该图片的未显示答案状态。
8. 最后一张完成后再次确认，进入“本轮测试完成！”页面。

## 支持格式

JPG / JPEG / PNG / BMP / GIF / WEBP。

默认只读取所选文件夹的直接子文件，不递归读取更深层的子文件夹。

答案使用完整文件名（去掉扩展名），不会改动中文、数字、空格、下划线、括号等内容。

## 快捷键

- `Enter`：确定 / 显示答案 / 下一张
- `Esc`：测试中返回设置；完成页返回设置

## 本地运行源码

需要 Python 3.x 和 Pillow：

```text
python -m pip install -r requirements.txt
python 图片随机测试.py
```

## Windows 单文件打包

在 Windows 电脑上，把本目录完整复制过去，双击 `build_windows.bat`。脚本会自动安装 PyInstaller，最后生成：

```text
dist\\图片随机测试.exe
```

注意：PyInstaller 通常需要在目标操作系统上构建，因此在 Linux 环境生成的可执行文件不是 Windows EXE。本开发环境为 Linux，无法在这里直接产出可供 Windows 双击运行的 EXE；`build_windows.bat` 用于在 Windows 上一键完成打包。
