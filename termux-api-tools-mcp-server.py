#!/usr/bin/env python3
from fastmcp import FastMCP
import subprocess
import json
import os
import sys
import argparse
import paramiko
import time
from typing import Union, Dict, List, Any, Optional

class TermuxSSHClient:
    """通过SSH连接到Termux设备执行命令的客户端"""
    
    def __init__(self, host: str, port: int = 8022, username: str = None, 
                password: str = None, key_file: str = None):
        """初始化SSH客户端"""
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.key_file = key_file
        self.client = None
        self.connected = False
    
    def connect(self) -> bool:
        """建立SSH连接"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            connect_kwargs = {
                'hostname': self.host,
                'port': self.port,
                'username': self.username,
            }
            
            if self.password:
                connect_kwargs['password'] = self.password
            elif self.key_file:
                connect_kwargs['key_filename'] = self.key_file
            
            self.client.connect(**connect_kwargs)
            self.connected = True
            return True
        except Exception as e:
            print(f"SSH连接失败: {str(e)}")
            self.connected = False
            return False
    
    def ensure_connected(self) -> bool:
        """确保SSH连接已建立"""
        if not self.connected or not self.client:
            return self.connect()
        return True
    
    def execute_command(self, command: str) -> tuple:
        """执行SSH命令并返回结果"""
        if not self.ensure_connected():
            return None, f"SSH连接失败", 1
        
        try:
            stdin, stdout, stderr = self.client.exec_command(command)
            exit_code = stdout.channel.recv_exit_status()
            stdout_data = stdout.read().decode('utf-8')
            stderr_data = stderr.read().decode('utf-8')
            return stdout_data, stderr_data, exit_code
        except Exception as e:
            return None, f"执行命令失败: {str(e)}", 1
    
    def execute_termux_command(self, command: List[str], input_data: str = None) -> tuple:
        """执行Termux API命令"""
        # 启动termux-api服务
        self.execute_command("termux-api-start")
        
        # 构建完整命令
        full_command = " ".join([f"'{arg}'" if ' ' in arg else arg for arg in command])
        
        # 如果有输入数据，则通过管道传递
        if input_data:
            full_command = f"echo '{input_data}' | {full_command}"
        
        return self.execute_command(full_command)
    
    def close(self):
        """关闭SSH连接"""
        if self.client:
            self.client.close()
            self.connected = False


# 全局SSH客户端实例
ssh_client = None

def get_ssh_client() -> TermuxSSHClient:
    """获取或创建全局SSH客户端实例"""
    global ssh_client
    if ssh_client is None:
        args = parse_args()
        ssh_client = TermuxSSHClient(
            host=args.host,
            port=args.port,
            username=args.username,
            password=args.password,
            key_file=args.key_file
        )
        ssh_client.connect()
    return ssh_client

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='Termux API MCP Server')
    parser.add_argument('--host', help='SSH主机地址', default=os.environ.get('TERMUX_SSH_HOST'))
    parser.add_argument('--port', type=int, help='SSH端口', default=int(os.environ.get('TERMUX_SSH_PORT', 8022)))
    parser.add_argument('--username', help='SSH用户名', default=os.environ.get('TERMUX_SSH_USER'))
    parser.add_argument('--password', help='SSH密码', default=os.environ.get('TERMUX_SSH_PASSWORD'))
    parser.add_argument('--key-file', help='SSH密钥文件路径', default=os.environ.get('TERMUX_SSH_KEY_FILE'))
    return parser.parse_args()

mcp = FastMCP("TermuxApiMcpTools")


@mcp.tool()
def termux_battery_status() -> dict:
    """获取设备电池状态信息，以JSON格式返回"""
    try:
        client = get_ssh_client()
        stdout, stderr, exit_code = client.execute_termux_command(["termux-battery-status"])
        
        if exit_code == 0 and stdout:
            return json.loads(stdout)
        else:
            return {"error": stderr or "无输出"}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def termux_brightness(brightness: str) -> str:
    """设置屏幕亮度，范围为0-255或auto"""
    try:
        client = get_ssh_client()
        stdout, stderr, exit_code = client.execute_termux_command(["termux-brightness", brightness])
        
        return "亮度已设置" if exit_code == 0 else f"错误: {stderr}"
    except Exception as e:
        return f"错误: {str(e)}"

@mcp.tool()
def termux_call_log(limit: int = 10, offset: int = 0) -> list:
    """获取通话记录，可指定数量和偏移量"""
    try:
        cmd = ["termux-call-log"]
        if limit != 10:
            cmd.extend(["-l", str(limit)])
        if offset != 0:
            cmd.extend(["-o", str(offset)])
        
        client = get_ssh_client()
        stdout, stderr, exit_code = client.execute_termux_command(cmd)
        
        if exit_code == 0 and stdout:
            return json.loads(stdout)
        else:
            return {"error": stderr or "无输出"}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def termux_camera_info() -> dict:
    """获取设备摄像头信息，以JSON格式返回"""
    try:
        client = get_ssh_client()
        stdout, stderr, exit_code = client.execute_termux_command(["termux-camera-info"])
        
        if exit_code == 0 and stdout:
            return json.loads(stdout)
        else:
            return {"error": stderr or "无输出"}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def termux_camera_photo(output_file: str, camera_id: int = 0) -> str:
    """使用指定的摄像头拍照并保存为JPEG格式"""
    try:
        cmd = ["termux-camera-photo"]
        if camera_id != 0:
            cmd.extend(["-c", str(camera_id)])
        cmd.append(output_file)
        
        client = get_ssh_client()
        stdout, stderr, exit_code = client.execute_termux_command(cmd)
        
        return f"照片已保存到: {output_file}" if exit_code == 0 else f"错误: {stderr}"
    except Exception as e:
        return f"错误: {str(e)}"

@mcp.tool()
def termux_clipboard_get() -> str:
    """获取系统剪贴板文本内容"""
    try:
        client = get_ssh_client()
        stdout, stderr, exit_code = client.execute_termux_command(["termux-clipboard-get"])
        
        return stdout if exit_code == 0 else f"错误: {stderr}"
    except Exception as e:
        return f"错误: {str(e)}"

@mcp.tool()
def termux_clipboard_set(text: str = None) -> str:
    """设置系统剪贴板文本内容"""
    try:
        if text is None:
            # 从标准输入读取内容
            text = sys.stdin.read()
        
        client = get_ssh_client()
        stdout, stderr, exit_code = client.execute_termux_command(["termux-clipboard-set"], input_data=text)
        
        return "剪贴板已设置" if exit_code == 0 else f"错误: {stderr}"
    except Exception as e:
        return f"错误: {str(e)}"

@mcp.tool()
def termux_contact_list() -> list:
    """获取所有联系人列表，以JSON格式返回"""
    try:
        client = get_ssh_client()
        stdout, stderr, exit_code = client.execute_termux_command(["termux-contact-list"])
        
        if exit_code == 0 and stdout:
            return json.loads(stdout)
        else:
            return {"error": stderr or "无输出"}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def termux_dialog(widget: str = "text", title: str = None, options: dict = None) -> dict:
    """显示对话框小部件，获取用户输入"""
    try:
        cmd = ["termux-dialog", widget]
        if title:
            cmd.extend(["-t", title])
        
        # 处理特定小部件的选项
        if options:
            for key, value in options.items():
                if key == "hint" and value:
                    cmd.extend(["-i", value])
                elif key == "values" and value:
                    cmd.extend(["-v", value])
                elif key == "range" and value:
                    cmd.extend(["-r", value])
                elif key == "multiple" and value:
                    cmd.append("-m")
                elif key == "number" and value:
                    cmd.append("-n")
                elif key == "password" and value:
                    cmd.append("-p")
                elif key == "date_format" and value:
                    cmd.extend(["-d", value])
        
        client = get_ssh_client()
        stdout, stderr, exit_code = client.execute_termux_command(cmd)
        
        if exit_code == 0 and stdout:
            return json.loads(stdout)
        else:
            return {"error": stderr or "无输出"}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def termux_download(url: str, title: str = None, description: str = None, path: str = None) -> str:
    """使用系统下载管理器下载资源"""
    try:
        cmd = ["termux-download"]
        if title:
            cmd.extend(["-t", title])
        if description:
            cmd.extend(["-d", description])
        if path:
            cmd.extend(["-p", path])
        cmd.append(url)
        
        client = get_ssh_client()
        stdout, stderr, exit_code = client.execute_termux_command(cmd)
        
        return "下载已开始" if exit_code == 0 else f"错误: {stderr}"
    except Exception as e:
        return f"错误: {str(e)}"

@mcp.tool()
def termux_fingerprint() -> dict:
    """使用设备指纹传感器进行身份验证"""
    try:
        client = get_ssh_client()
        stdout, stderr, exit_code = client.execute_termux_command(["termux-fingerprint"])
        
        if exit_code == 0 and stdout:
            return json.loads(stdout)
        else:
            return {"error": stderr or "无输出"}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def termux_infrared_frequencies() -> dict:
    """查询红外发射器支持的载波频率"""
    try:
        client = get_ssh_client()
        stdout, stderr, exit_code = client.execute_termux_command(["termux-infrared-frequencies"])
        
        if exit_code == 0 and stdout:
            return json.loads(stdout)
        else:
            return {"error": stderr or "无输出"}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def termux_infrared_transmit(frequency: int, pattern: str) -> str:
    """发送红外模式信号"""
    try:
        cmd = ["termux-infrared-transmit", "-f", str(frequency), pattern]
        
        client = get_ssh_client()
        stdout, stderr, exit_code = client.execute_termux_command(cmd)
        
        return "红外信号已发送" if exit_code == 0 else f"错误: {stderr}"
    except Exception as e:
        return f"错误: {str(e)}"

@mcp.tool()
def termux_location(provider: str = "gps", request: str = "once") -> dict:
    """获取设备位置信息"""
    try:
        cmd = ["termux-location"]
        if provider and provider != "gps":
            cmd.extend(["-p", provider])
        if request and request != "once":
            cmd.extend(["-r", request])
        
        client = get_ssh_client()
        stdout, stderr, exit_code = client.execute_termux_command(cmd)
        
        if exit_code == 0 and stdout:
            return json.loads(stdout)
        else:
            return {"error": stderr or "无输出"}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def termux_media_player(command: str, file_path: str = None) -> str:
    """播放媒体文件或控制媒体播放"""
    try:
        cmd = ["termux-media-player", command]
        if command == "play" and file_path:
            cmd.append(file_path)
        
        client = get_ssh_client()
        stdout, stderr, exit_code = client.execute_termux_command(cmd)
        
        response = stdout.strip() if stdout else ""
        return response if response else f"媒体播放器命令 '{command}' 已执行"
    except Exception as e:
        return f"错误: {str(e)}"

@mcp.tool()
def termux_media_scan(files: list, recursive: bool = False, verbose: bool = False) -> str:
    """扫描指定文件并添加到媒体内容提供程序"""
    try:
        cmd = ["termux-media-scan"]
        if recursive:
            cmd.append("-r")
        if verbose:
            cmd.append("-v")
        cmd.extend(files)
        
        client = get_ssh_client()
        stdout, stderr, exit_code = client.execute_termux_command(cmd)
        
        return stdout if stdout else "媒体扫描已完成"
    except Exception as e:
        return f"错误: {str(e)}"

@mcp.tool()
def termux_microphone_record(action: str, options: dict = None) -> str:
    """使用设备麦克风录音"""
    try:
        cmd = ["termux-microphone-record"]
        
        if action == "start":
            # 默认启动录音
            cmd.append("-d")
            
            # 处理选项
            if options:
                if "file" in options:
                    cmd.extend(["-f", options["file"]])
                if "limit" in options:
                    cmd.extend(["-l", str(options["limit"])])
                if "encoder" in options:
                    cmd.extend(["-e", options["encoder"]])
                if "bitrate" in options:
                    cmd.extend(["-b", str(options["bitrate"])])
                if "rate" in options:
                    cmd.extend(["-r", str(options["rate"])])
                if "channels" in options:
                    cmd.extend(["-c", str(options["channels"])])
        elif action == "info":
            cmd.append("-i")
        elif action == "stop":
            cmd.append("-q")
        
        client = get_ssh_client()
        stdout, stderr, exit_code = client.execute_termux_command(cmd)
        
        if action == "start":
            return "录音已开始"
        elif action == "info":
            try:
                return json.loads(stdout) if stdout else {"error": "无输出"}
            except:
                return stdout
        elif action == "stop":
            return "录音已停止"
    except Exception as e:
        return f"错误: {str(e)}"

@mcp.tool()
def termux_notification(content: str = None, title: str = None, id: str = None, options: dict = None) -> str:
    """显示系统通知"""
    try:
        cmd = ["termux-notification"]
        
        if content:
            cmd.extend(["--content", content])
        if title:
            cmd.extend(["--title", title])
        if id:
            cmd.extend(["--id", id])
        
        # 处理其他选项
        if options:
            for key, value in options.items():
                if key == "action" and value:
                    cmd.extend(["--action", value])
                elif key == "alert_once" and value:
                    cmd.append("--alert-once")
                elif key == "button1" and value:
                    cmd.extend(["--button1", value])
                elif key == "button1_action" and value:
                    cmd.extend(["--button1-action", value])
                elif key == "button2" and value:
                    cmd.extend(["--button2", value])
                elif key == "button2_action" and value:
                    cmd.extend(["--button2-action", value])
                elif key == "button3" and value:
                    cmd.extend(["--button3", value])
                elif key == "button3_action" and value:
                    cmd.extend(["--button3-action", value])
                elif key == "group" and value:
                    cmd.extend(["--group", value])
                elif key == "image_path" and value:
                    cmd.extend(["--image-path", value])
                elif key == "led_color" and value:
                    cmd.extend(["--led-color", value])
                elif key == "led_off" and value:
                    cmd.extend(["--led-off", str(value)])
                elif key == "led_on" and value:
                    cmd.extend(["--led-on", str(value)])
                elif key == "on_delete" and value:
                    cmd.extend(["--on-delete", value])
                elif key == "ongoing" and value:
                    cmd.append("--ongoing")
                elif key == "priority" and value:
                    cmd.extend(["--priority", value])
                elif key == "sound" and value:
                    cmd.append("--sound")
                elif key == "vibrate" and value:
                    cmd.extend(["--vibrate", value])
                elif key == "type" and value:
                    cmd.extend(["--type", value])
                # 媒体控制选项
                elif key == "media_next" and value:
                    cmd.extend(["--media-next", value])
                elif key == "media_pause" and value:
                    cmd.extend(["--media-pause", value])
                elif key == "media_play" and value:
                    cmd.extend(["--media-play", value])
                elif key == "media_previous" and value:
                    cmd.extend(["--media-previous", value])
        
        client = get_ssh_client()
        stdout, stderr, exit_code = client.execute_termux_command(cmd)
        
        return "通知已显示" if exit_code == 0 else f"错误: {stderr}"
    except Exception as e:
        return f"错误: {str(e)}"

@mcp.tool()
def termux_notification_remove(id: str) -> str:
    """移除先前显示的通知"""
    try:
        cmd = ["termux-notification-remove", id]
        
        client = get_ssh_client()
        stdout, stderr, exit_code = client.execute_termux_command(cmd)
        
        return f"通知 ID '{id}' 已移除" if exit_code == 0 else f"错误: {stderr}"
    except Exception as e:
        return f"错误: {str(e)}"

@mcp.tool()
def termux_sensor(action: str = "list", options: dict = None) -> dict:
    """获取传感器信息和实时数据"""
    try:
        cmd = ["termux-sensor"]
        
        if action == "list":
            cmd.append("-l")
        elif action == "all":
            cmd.append("-a")
        elif action == "cleanup":
            cmd.append("-c")
        elif action == "sensors" and options and "sensors" in options:
            cmd.extend(["-s", options["sensors"]])
        
        # 其他选项
        if options:
            if "delay" in options:
                cmd.extend(["-d", str(options["delay"])])
            if "limit" in options:
                cmd.extend(["-n", str(options["limit"])])
        
        client = get_ssh_client()
        stdout, stderr, exit_code = client.execute_termux_command(cmd)
        
        if action == "cleanup":
            return "传感器资源已释放" if exit_code == 0 else f"错误: {stderr}"
        
        try:
            return json.loads(stdout) if stdout else {"error": "无输出"}
        except:
            return stdout
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def termux_share(file_path: str = None, content: str = None, options: dict = None) -> str:
    """分享文件或文本内容"""
    try:
        cmd = ["termux-share"]
        
        # 处理选项
        if options:
            if "action" in options:
                cmd.extend(["-a", options["action"]])
            if "content_type" in options:
                cmd.extend(["-c", options["content_type"]])
            if "default_receiver" in options and options["default_receiver"]:
                cmd.append("-d")
            if "title" in options:
                cmd.extend(["-t", options["title"]])
        
        client = get_ssh_client()
        
        # 添加文件路径或使用内容
        if file_path:
            cmd.append(file_path)
            stdout, stderr, exit_code = client.execute_termux_command(cmd)
        elif content:
            stdout, stderr, exit_code = client.execute_termux_command(cmd, input_data=content)
        else:
            return "错误: 必须提供文件路径或内容"
        
        return "内容已分享" if exit_code == 0 else f"错误: {stderr}"
    except Exception as e:
        return f"错误: {str(e)}"

@mcp.tool()
def termux_sms_list(limit: int = 10, offset: int = 0, show_dates: bool = False, 
                   show_numbers: bool = False, type: str = "inbox") -> list:
    """列出短信消息"""
    try:
        cmd = ["termux-sms-list"]
        
        if show_dates:
            cmd.append("-d")
        if limit != 10:
            cmd.extend(["-l", str(limit)])
        if show_numbers:
            cmd.append("-n")
        if offset != 0:
            cmd.extend(["-o", str(offset)])
        if type != "inbox":
            cmd.extend(["-t", type])
        
        client = get_ssh_client()
        stdout, stderr, exit_code = client.execute_termux_command(cmd)
        
        if exit_code == 0 and stdout:
            return json.loads(stdout)
        else:
            return {"error": stderr or "无输出"}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def termux_sms_send(numbers: str, text: str = None, slot: int = None) -> str:
    """发送短信到指定号码"""
    try:
        cmd = ["termux-sms-send", "-n", numbers]
        
        if slot is not None:
            cmd.extend(["-s", str(slot)])
        
        client = get_ssh_client()
        
        if text:
            cmd.append(text)
            stdout, stderr, exit_code = client.execute_termux_command(cmd)
        else:
            # 从标准输入读取内容
            text = sys.stdin.read()
            stdout, stderr, exit_code = client.execute_termux_command(cmd, input_data=text)
        
        return "短信已发送" if exit_code == 0 else f"错误: {stderr}"
    except Exception as e:
        return f"错误: {str(e)}"

@mcp.tool()
def termux_storage_get(output_file: str) -> str:
    """从系统请求文件并输出到指定路径"""
    try:
        cmd = ["termux-storage-get", output_file]
        
        client = get_ssh_client()
        stdout, stderr, exit_code = client.execute_termux_command(cmd)
        
        return f"文件已保存到: {output_file}" if exit_code == 0 else f"错误: {stderr}"
    except Exception as e:
        return f"错误: {str(e)}"

@mcp.tool()
def termux_telephony_call(number: str) -> str:
    """拨打电话号码"""
    try:
        cmd = ["termux-telephony-call", number]
        
        client = get_ssh_client()
        stdout, stderr, exit_code = client.execute_termux_command(cmd)
        
        return f"正在拨打电话: {number}" if exit_code == 0 else f"错误: {stderr}"
    except Exception as e:
        return f"错误: {str(e)}"

@mcp.tool()
def termux_telephony_cellinfo() -> dict:
    """获取设备上所有无线电模块（如蜂窝网络、Wi-Fi 等）检测到的 基站（Cell）信息，包括（Primary Cell）和（Neighboring Cells）的详细信息。"""
    try:
        client = get_ssh_client()
        stdout, stderr, exit_code = client.execute_termux_command(["termux-telephony-cellinfo"])
        
        if exit_code == 0 and stdout:
            return json.loads(stdout)
        else:
            return {"error": stderr or "无输出"}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def termux_telephony_deviceinfo() -> dict:
    """获取电话设备信息"""
    try:
        client = get_ssh_client()
        stdout, stderr, exit_code = client.execute_termux_command(["termux-telephony-deviceinfo"])
        
        if exit_code == 0 and stdout:
            return json.loads(stdout)
        else:
            return {"error": stderr or "无输出"}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def termux_toast(text: str = None, background: str = None, color: str = None, 
                position: str = None, short: bool = False) -> str:
    """显示一个短暂的弹出通知"""
    try:
        cmd = ["termux-toast"]
        
        if background:
            cmd.extend(["-b", background])
        if color:
            cmd.extend(["-c", color])
        if position:
            cmd.extend(["-g", position])
        if short:
            cmd.append("-s")
        
        client = get_ssh_client()
        
        if text:
            cmd.append(text)
            stdout, stderr, exit_code = client.execute_termux_command(cmd)
        else:
            # 从标准输入读取内容
            text = sys.stdin.read()
            stdout, stderr, exit_code = client.execute_termux_command(cmd, input_data=text)
        
        return "Toast 通知已显示" if exit_code == 0 else f"错误: {stderr}"
    except Exception as e:
        return f"错误: {str(e)}"

@mcp.tool()
def termux_torch(state: str) -> str:
    """切换设备的LED手电筒"""
    try:
        cmd = ["termux-torch", state]
        
        client = get_ssh_client()
        stdout, stderr, exit_code = client.execute_termux_command(cmd)
        
        return f"手电筒已{state}" if exit_code == 0 else f"错误: {stderr}"
    except Exception as e:
        return f"错误: {str(e)}"

@mcp.tool()
def termux_tts_engines() -> list:
    """获取可用的文本转语音引擎信息"""
    try:
        client = get_ssh_client()
        stdout, stderr, exit_code = client.execute_termux_command(["termux-tts-engines"])
        
        if exit_code == 0 and stdout:
            return json.loads(stdout)
        else:
            return {"error": stderr or "无输出"}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def termux_tts_speak(text: str = None, options: dict = None) -> str:
    """使用系统文本转语音引擎朗读文本"""
    try:
        cmd = ["termux-tts-speak"]
        # 选项处理
        if options:
            if "engine" in options:
                cmd.extend(["-e", options["engine"]])
            if "language" in options:
                cmd.extend(["-l", options["language"]])
            if "region" in options:
                cmd.extend(["-n", options["region"]])
            if "variant" in options:
                cmd.extend(["-v", options["variant"]])
            if "pitch" in options:
                cmd.extend(["-p", str(options["pitch"])])
            if "rate" in options:
                cmd.extend(["-r", str(options["rate"])])
            if "stream" in options:
                cmd.extend(["-s", options["stream"]])
        
        client = get_ssh_client()
        
        if text:
            cmd.append(text)
            stdout, stderr, exit_code = client.execute_termux_command(cmd)
        else:
            # 从标准输入读取内容
            text = sys.stdin.read()
            stdout, stderr, exit_code = client.execute_termux_command(cmd, input_data=text)
        
        return "文本朗读已启动" if exit_code == 0 else f"错误: {stderr}"
    except Exception as e:
        return f"错误: {str(e)}"

@mcp.tool()
def termux_usb(action: str = "list", device: str = None, show_request: bool = False, command: str = None) -> dict:
    """列出或访问USB设备"""
    try:
        cmd = ["termux-usb"]
        
        if action == "list":
            cmd.append("-l")
            client = get_ssh_client()
            stdout, stderr, exit_code = client.execute_termux_command(cmd)
            
            if exit_code == 0 and stdout:
                return json.loads(stdout)
            else:
                return {"error": stderr or "无输出"}
        elif action == "access" and device:
            if show_request:
                cmd.append("-r")
            if command:
                cmd.extend(["-e", command])
            cmd.append(device)
            
            client = get_ssh_client()
            stdout, stderr, exit_code = client.execute_termux_command(cmd)
            
            return stdout if exit_code == 0 else {"error": stderr}
        else:
            return {"error": "无效的操作或参数"}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def termux_vibrate(duration: int = 1000, force: bool = False) -> str:
    """使设备振动"""
    try:
        cmd = ["termux-vibrate"]
        
        if duration != 1000:
            cmd.extend(["-d", str(duration)])
        if force:
            cmd.append("-f")
        
        client = get_ssh_client()
        stdout, stderr, exit_code = client.execute_termux_command(cmd)
        
        return "设备振动已触发" if exit_code == 0 else f"错误: {stderr}"
    except Exception as e:
        return f"错误: {str(e)}"

@mcp.tool()
def termux_volume(stream: str = None, volume: int = None) -> dict:
    """更改音频流的音量"""
    try:
        cmd = ["termux-volume"]
        
        if stream:
            cmd.append(stream)
            if volume is not None:
                cmd.append(str(volume))
        
        client = get_ssh_client()
        stdout, stderr, exit_code = client.execute_termux_command(cmd)
        
        if not stream or (stream and volume is None):
            # 返回音量信息
            if exit_code == 0 and stdout:
                return json.loads(stdout)
            else:
                return {"error": stderr or "无输出"}
        else:
            # 设置音量
            return f"{stream} 音量已设置为 {volume}" if exit_code == 0 else f"错误: {stderr}"
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def termux_wallpaper(file_path: str = None, url: str = None, lockscreen: bool = False) -> str:
    """更改设备壁纸"""
    try:
        cmd = ["termux-wallpaper"]
        
        if file_path:
            cmd.extend(["-f", file_path])
        elif url:
            cmd.extend(["-u", url])
        else:
            return "错误: 必须提供文件路径或URL"
        
        if lockscreen:
            cmd.append("-l")
        
        client = get_ssh_client()
        stdout, stderr, exit_code = client.execute_termux_command(cmd)
        
        return "壁纸已设置" if exit_code == 0 else f"错误: {stderr}"
    except Exception as e:
        return f"错误: {str(e)}"

@mcp.tool()
def termux_wifi_connectioninfo() -> dict:
    """获取当前WiFi连接信息"""
    try:
        client = get_ssh_client()
        stdout, stderr, exit_code = client.execute_termux_command(["termux-wifi-connectioninfo"])
        
        if exit_code == 0 and stdout:
            return json.loads(stdout)
        else:
            return {"error": stderr or "无输出"}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def termux_wifi_enable(state: bool) -> str:
    """开启或关闭WiFi"""
    try:
        cmd = ["termux-wifi-enable", str(state).lower()]
        
        client = get_ssh_client()
        stdout, stderr, exit_code = client.execute_termux_command(cmd)
        
        status = "开启" if state else "关闭"
        return f"WiFi已{status}" if exit_code == 0 else f"错误: {stderr}"
    except Exception as e:
        return f"错误: {str(e)}"

@mcp.tool()
def termux_wifi_scaninfo() -> dict:
    """获取最近WiFi扫描信息"""
    try:
        client = get_ssh_client()
        stdout, stderr, exit_code = client.execute_termux_command(["termux-wifi-scaninfo"])
        
        if exit_code == 0 and stdout:
            return json.loads(stdout)
        else:
            return {"error": stderr or "无输出"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # 解析命令行参数并启动MCP服务器
    args = parse_args()
    
    # 确保至少有SSH主机信息
    if not args.host:
        print("错误: 需要提供SSH主机地址。请使用--host参数或设置TERMUX_SSH_HOST环境变量。")
        sys.exit(1)
    
    print(f"正在连接到Termux SSH: {args.host}:{args.port}")
    
    # 创建并连接SSH客户端
    ssh_client = TermuxSSHClient(
        host=args.host,
        port=args.port,
        username=args.username,
        password=args.password,
        key_file=args.key_file
    )
    
    if not ssh_client.connect():
        print("SSH连接失败，请检查连接信息。")
        sys.exit(1)
    
    print("SSH连接成功，启动Termux API MCP服务...")
    
    # 启动MCP服务器
    mcp.run(transport='stdio')
