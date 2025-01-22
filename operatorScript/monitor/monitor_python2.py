#coding=utf-8
import psutil
import datetime
import pytz
import time


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
            cpu_percent = p.cpu_percent(interval=0.1)  # 使用更短的间隔
            memory_mb = p.memory_info().rss / (1024 * 1024)  # 转为 MB
            processes.append((proc.info['name'], cpu_percent, memory_mb))
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            # 捕获异常，避免程序崩溃
            print("无法获取进程 {} 信息: {}".format(proc.info['pid'], e))
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
        f.write("开机时间: {}\n".format(boot_time_beijing))
        f.write("内存总量: {:.2f} MB\n".format(total_memory))
        f.write("内存已用: {:.2f} MB\n".format(used_memory))
        f.write("内存剩余: {:.2f} MB\n".format(available_memory))
        f.write("网络发送: {:.2f} MB\n".format(sent_data))
        f.write("网络接收: {:.2f} MB\n".format(received_data))
        f.write("CPU 负载 (1/5/15 分钟): {}\n".format(cpu_load))
        f.write("CPU 平均使用率: {:.2f} %\n".format(cpu_avg_usage))
        f.write("硬盘总量: {:.2f} MB\n".format(total_disk))
        f.write("硬盘已用: {:.2f} MB\n".format(used_disk))
        f.write("硬盘剩余: {:.2f} MB\n".format(free_disk))
        f.write("\n===== 占用资源前五名的进程 =====\n")
        f.write("{:<20}{:<15}{:<20}\n".format('进程名称', 'CPU 使用率 (%)', '内存使用量 (MB)'))
        for name, cpu, memory in top_processes:
            f.write("{:<20}{:<15.2f}{:<20.2f}\n".format(name, cpu, memory))
        f.write("=========================\n")


if __name__ == "__main__":
    # 设置输出文件路径
    output_file = "server_resources_monitoring.txt"

    # 监控服务器资源并写入文件
    monitor_server_resources(output_file)
    print("监控结果已保存至: {}".format(output_file))
