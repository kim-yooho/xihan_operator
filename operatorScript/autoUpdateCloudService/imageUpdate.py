#coding=utf-8
import os
import subprocess
import argparse
import json
import shutil


def replace_directory(source_dir, target_dir):
    """
    用源目录内容替换目标目录内容
    :param source_dir: 源目录路径
    :param target_dir: 目标目录路径
    """
    if not os.path.exists(source_dir):
        print(f"错误：源目录 {source_dir} 不存在！")
        return

    if os.path.exists(target_dir):
        print(f"清空目标目录 {target_dir}...")
        for item in os.listdir(target_dir):
            item_path = os.path.join(target_dir, item)
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
    else:
        print(f"目标目录 {target_dir} 不存在，正在创建...")
        os.makedirs(target_dir)

    print(f"复制 {source_dir} 的内容到 {target_dir}...")
    for item in os.listdir(source_dir):
        source_item = os.path.join(source_dir, item)
        target_item = os.path.join(target_dir, item)
        if os.path.isdir(source_item):
            shutil.copytree(source_item, target_item)
        else:
            shutil.copy2(source_item, target_item)
    print("目录替换完成！")


def build_image(dockerfile_dir, image_name):
    """
    切换到 Dockerfile 所在目录并构建镜像
    :param dockerfile_dir: Dockerfile 所在目录
    :param image_name: 构建的镜像名称
    """
    if not os.path.exists(dockerfile_dir):
        print(f"错误：Dockerfile 所在目录 {dockerfile_dir} 不存在！")
        return False

    if not os.path.exists(os.path.join(dockerfile_dir, "Dockerfile")):
        print(f"错误：目录 {dockerfile_dir} 中未找到 Dockerfile 文件！")
        return False

    original_dir = os.getcwd()
    try:
        os.chdir(dockerfile_dir)
        cmd_build = ["docker", "build", "-t", image_name, "."]
        print(f"正在切换到 {dockerfile_dir} 并构建镜像 {image_name}...")
        subprocess.run(cmd_build, check=True)
        print(f"镜像 {image_name} 构建成功！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"错误：镜像构建失败！\n{e}")
        return False
    finally:
        os.chdir(original_dir)


def push_image(image_name, registry=None):
    """
    推送镜像到指定的镜像仓库
    :param image_name: 构建的镜像名称
    :param registry: 镜像仓库地址（可选）
    """
    if registry:
        image_name_with_registry = f"{registry}/{image_name}"
        print(f"正在将镜像标记为 {image_name_with_registry}...")
        cmd_tag = ["docker", "tag", image_name, image_name_with_registry]
        try:
            subprocess.run(cmd_tag, check=True)
        except subprocess.CalledProcessError as e:
            print(f"错误：镜像标记失败！\n{e}")
            return

    cmd_push = ["docker", "push", image_name_with_registry if registry else image_name]
    print(f"正在推送镜像 {image_name} 到镜像仓库...")
    try:
        subprocess.run(cmd_push, check=True)
        print(f"镜像 {image_name} 推送成功！")
    except subprocess.CalledProcessError as e:
        print(f"错误：镜像推送失败！\n{e}")


def update_image(resource_type, namespace, new_image):
    """
    使用 kubectl 命令更新 Deployment 或 StatefulSet 中的镜像
    :param resource_type: 资源类型（deployment 或 statefulset）
    :param namespace: 命名空间
    :param new_image: 新的镜像名称
    """
    if resource_type not in ["deployment", "statefulset"]:
        print("错误：资源类型必须为 'deployment' 或 'statefulset'")
        return

    cmd_get = f"kubectl get {resource_type} -n {namespace} -o json"
    try:
        print(f"正在获取 {namespace} 命名空间中的 {resource_type} 列表...")
        result = subprocess.run(cmd_get, shell=True, check=True, capture_output=True, text=True)
        resources = json.loads(result.stdout)

        for item in resources["items"]:
            resource_name = item["metadata"]["name"]
            print(f"正在更新 {resource_type} {resource_name} 的镜像为 {new_image}...")
            cmd_set = (
                f"kubectl set image {resource_type}/{resource_name} "
                f"{item['spec']['template']['spec']['containers'][0]['name']}={new_image} -n {namespace}"
            )
            subprocess.run(cmd_set, shell=True, check=True)
        print(f"所有 {resource_type} 的镜像更新完成！")
    except subprocess.CalledProcessError as e:
        print(f"错误：执行命令失败！\n{e.stderr}")
    except json.JSONDecodeError as e:
        print(f"错误：解析 JSON 输出失败！\n{e}")


def main():
    parser = argparse.ArgumentParser(description="自动化运维程序，支持目录替换、镜像构建及推送、K8s镜像更新")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 替换目录
    parser_replace = subparsers.add_parser("replace", help="替换整个目录内容")
    parser_replace.add_argument("source_dir", help="源目录路径")
    parser_replace.add_argument("target_dir", help="目标目录路径")

    # 构建镜像
    parser_build = subparsers.add_parser("build", help="构建并推送镜像")
    parser_build.add_argument("dockerfile_dir", help="Dockerfile 所在目录")
    parser_build.add_argument("image_name", help="生成的镜像名称（包括版本号）")
    parser_build.add_argument("--registry", help="目标镜像仓库地址（可选）", default=None)

    # 更新 K8s 镜像
    parser_update = subparsers.add_parser("update", help="更新 K8s Deployment 或 StatefulSet 的镜像")
    parser_update.add_argument("resource_type", choices=["deployment", "statefulset"], help="资源类型")
    parser_update.add_argument("namespace", help="命名空间")
    parser_update.add_argument("new_image", help="新的镜像名称")

    args = parser.parse_args()

    if args.command == "replace":
        replace_directory(args.source_dir, args.target_dir)
    elif args.command == "build":
        if build_image(args.dockerfile_dir, args.image_name):
            push_image(args.image_name, args.registry)
    elif args.command == "update":
        update_image(args.resource_type, args.namespace, args.new_image)


if __name__ == "__main__":
    main()

# 1、替换目录
# python3 automation.py replace /path/to/source /path/to/target
# 2、构建并推送镜像
# python3 automation.py build /path/to/Dockerfile /path/to/context_dir my-image:1.0 --registry my.registry.com
# 3、更新 Kubernetes 镜像：
'''
python automation.py update deployment my-namespace my-image:1.0
'''
