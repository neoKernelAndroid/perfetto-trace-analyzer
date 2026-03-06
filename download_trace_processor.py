# -*- coding: utf-8 -*-
# @Time     : 2025/1/19
# @Author   : chao.liu8
# @File     : download_trace_processor.py
# @Description: 下载 trace_processor

import sys
import os
import io
import urllib.request
import shutil
import ssl

# 设置标准输出编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 创建不验证 SSL 的上下文
ssl_context = ssl._create_unverified_context()


def download_trace_processor():
    """下载 trace_processor"""
    print("="*80)
    print("  下载 trace_processor")
    print("="*80)
    print()
    
    # 确定平台
    if sys.platform == 'win32':
        platform = 'windows-amd64'
        filename = 'trace_processor.exe'
    elif sys.platform == 'darwin':
        platform = 'darwin-amd64'
        filename = 'trace_processor'
    else:
        platform = 'linux-amd64'
        filename = 'trace_processor'
    
    # 下载 URL（使用最新版本）
    # 注意：perfetto 的发布格式可能不同，尝试多个可能的 URL
    version = 'v48.0'  # 尝试不同版本
    
    # 可能的 URL 格式
    urls = [
        f'https://github.com/google/perfetto/releases/download/{version}/trace_processor-{platform}',
        f'https://github.com/google/perfetto/releases/download/{version}/trace_processor-{platform}.exe' if platform == 'windows-amd64' else None,
        f'https://commondatastorage.googleapis.com/perfetto-luci-artifacts/{version}/windows-amd64/trace_processor.exe' if platform == 'windows-amd64' else None,
    ]
    
    urls = [u for u in urls if u is not None]
    
    print(f"平台: {platform}")
    print(f"尝试下载 trace_processor...")
    print()
    
    # 目标目录
    target_dir = os.path.expanduser('~/.local/share/perfetto')
    os.makedirs(target_dir, exist_ok=True)
    
    target_path = os.path.join(target_dir, filename)
    
    print(f"目标路径: {target_path}")
    print()
    
    # 下载文件
    print("正在下载... (可能需要几分钟)")
    print("如果下载失败，请使用 VPN 或手动下载")
    print()
    
    success = False
    for url in urls:
        try:
            print(f"尝试: {url}")
            
            # 添加进度显示
            def reporthook(count, block_size, total_size):
                if total_size > 0:
                    percent = int(count * block_size * 100 / total_size)
                    sys.stdout.write(f"\r进度: {percent}% ({count * block_size / 1024 / 1024:.1f}MB / {total_size / 1024 / 1024:.1f}MB)")
                    sys.stdout.flush()
            
            # 使用不验证 SSL 的上下文
            opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl_context))
            urllib.request.install_opener(opener)
            urllib.request.urlretrieve(url, target_path, reporthook)
            print()
            print()
            print("[OK] 下载成功!")
            success = True
            break
            
        except Exception as e:
            print()
            print(f"[WARN] 此 URL 失败: {e}")
            print()
            continue
    
    if success:
        # 设置执行权限（Linux/Mac）
        if sys.platform != 'win32':
            os.chmod(target_path, 0o755)
            print("[OK] 已设置执行权限")
        
        print()
        print("="*80)
        print("  安装完成!")
        print("="*80)
        print()
        print("现在可以运行线程监控工具了:")
        print("  python monitor_thread_count.py trace.perfetto-trace")
        print()
        
        return True
    else:
        print()
        print(f"[ERROR] 所有下载尝试都失败了")
        print()
        print("请手动下载:")
        print(f"1. 访问: https://github.com/google/perfetto/releases")
        print(f"2. 下载: trace_processor-{platform}")
        print(f"3. 保存到: {target_path}")
        print()
        return False


if __name__ == '__main__':
    success = download_trace_processor()
    
    if not success:
        print()
        print("如果无法访问 GitHub，可以:")
        print("1. 使用 VPN")
        print("2. 使用代理")
        print("3. 从其他渠道获取 trace_processor")
        print()
    
    sys.exit(0 if success else 1)

