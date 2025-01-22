#coding=utf-8
import psutil
import datetime
import pytz  # 使用 pytz 模块处理时区

def format_timestamp_to_beijing(timestamp):
    """将时间戳转换为北京时间"""
    utc_time = datetime.datetime.fromtimestamp(timestamp, tz=pytz.utc)  # 转为 UTC 时间
    beijing_tz = pytz.timezone("Asia/Shanghai")  # 设置北京时间
    beijing_time = utc_time.astimezone(beijing_tz)  # 转换为北京时间
    return beijing_time.strftime("%Y-%m-%d %H:%M:%S")


def get_top_processes_by_resource():
    """获取占用资源前五名的进程信息"""
    processes = []
    for proc in psutil.process_iter(attrs=['pid', 'name']):
        try:
            # 获取每个进程的 CPU 使用率和内存使用情况
            p = psutil.Process(proc.info['pid'])
            cpu_percent = p.cpu_percent(interval=1)  # 获取 CPU 使用率
            memory_mb = p.memory_info().rss / (1024 * 1024)  # 转为 MB
            processes.append((proc.info['name'], cpu_percent, memory_mb))
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    # 按 CPU 使用率排序，取前 5 名
    top_processes = sorted(processes, key=lambda x: x[1], reverse=True)[:5]
    return top_processes


def monitor_server_resources(output_file):
    # 获取开机时间
    boot_time = psutil.boot_time()
    boot_time_beijing = format_timestamp_to_beijing(boot_time)

    # 获取内存使用情况
    memory = psutil.virtual_memory()
    total_memory = memory.total / (1024 * 1024)  # 转换为 MB
    used_memory = memory.used / (1024 * 1024)
    available_memory = memory.available / (1024 * 1024)

    # 获取网络 I/O
    net_io = psutil.net_io_counters()
    sent_data = net_io.bytes_sent / (1024 * 1024)  # 转换为 MB
    received_data = net_io.bytes_recv / (1024 * 1024)

    # 获取 CPU 负载和平均使用率
    cpu_load = psutil.getloadavg()  # 返回最近1分钟、5分钟和15分钟的负载
    cpu_avg_usage = psutil.cpu_percent(interval=1)  # 平均使用率，间隔1秒采样

    # 获取硬盘剩余空间
    disk = psutil.disk_usage('/')
    total_disk = disk.total / (1024 * 1024)  # 转换为 MB
    used_disk = disk.used / (1024 * 1024)
    free_disk = disk.free / (1024 * 1024)

    # 获取占用资源前五名的进程
    top_processes = get_top_processes_by_resource()

    # 打开输出文件并写入监控结果
    with open(output_file, 'w',encoding="utf-8") as f:
        f.write("===== 服务器资源监控 =====\n")
        f.write(f"开机时间: {boot_time_beijing}\n")
        f.write(f"内存总量: {total_memory:.2f} MB\n")
        f.write(f"内存已用: {used_memory:.2f} MB\n")
        f.write(f"内存剩余: {available_memory:.2f} MB\n")
        f.write(f"网络发送: {sent_data:.2f} MB\n")
        f.write(f"网络接收: {received_data:.2f} MB\n")
        f.write(f"CPU 负载 (1/5/15 分钟): {cpu_load}\n")
        f.write(f"CPU 平均使用率: {cpu_avg_usage:.2f} %\n")
        f.write(f"硬盘总量: {total_disk:.2f} MB\n")
        f.write(f"硬盘已用: {used_disk:.2f} MB\n")
        f.write(f"硬盘剩余: {free_disk:.2f} MB\n")
        f.write("\n===== 占用资源前五名的进程 =====\n")
        f.write(f"{'进程名称':<20}{'CPU 使用率 (%)':<15}{'内存使用量 (MB)':<20}\n")
        for name, cpu, memory in top_processes:
            f.write(f"{name:<20}{cpu:<15.2f}{memory:<20.2f}\n")
        f.write("=========================\n")


if __name__ == "__main__":
    # 设置输出文件路径
    output_file = "monitor.txt"

    # 监控服务器资源并写入文件
    monitor_server_resources(output_file)
    print(f"监控结果已保存至: {output_file}")
    with open(output_file, 'r', encoding="utf-8") as f:
        f.readlines()

