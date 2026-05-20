import csv
import json
import locale
import os
import platform
import re
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog


APP_NAME = "NetPulse"
APP_VERSION = "1.8"
AUTHOR = "Hang3sui"
MAX_PING_COUNT = 500
MAX_TIME_SECONDS = 3600

if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).resolve().parent
else:
    APP_DIR = Path(__file__).resolve().parent

CONFIG_FILE = APP_DIR / "netpulse_config.json"
HISTORY_FILE = APP_DIR / "netpulse_history.csv"

DEFAULT_CONFIG = {
    "router_ip": "192.168.1.254",
    "dns_primary": "",
    "dns_secondary": "",
    "website": "google.com",
    "extra_targets": "",
    "recent_extra_targets": [],
    "target_suffix": ".com",
    "custom_suffix": "",
    "count": "20",
    "ping_mode": "count",
    "duration_seconds": "60",
    "ping_interval_seconds": "1",
    "language": "zh",
}

COMMON_WEBSITES = [
    "google.com",
    "youtube.com",
    "github.com",
    "microsoft.com",
    "cloudflare.com",
    "baidu.com",
    "bilibili.com",
    "taobao.com",
    "qq.com",
    "singtel.com",
]

DOMAIN_SUFFIXES = [
    ".com",
    ".cn",
    ".com.cn",
    ".net",
    ".org",
    ".xyz",
    ".io",
    ".dev",
    ".top",
    ".site",
    ".me",
    ".sg",
    "不添加 / None",
    "自定义 / Custom",
]

TEXT = {
    "zh": {
        "app_title": "NetPulse 网络卡顿检测器",
        "detect_settings": "检测设置",
        "router": "路由器：",
        "auto_detect": "自动识别",
        "auto_detect_all": "自动识别路由器和 DNS",
        "dns1": "DNS 1：",
        "dns2": "DNS 2：",
        "ping_count": "Ping 次数：",
        "ping_mode": "Ping 模式：",
        "mode_count": "按次数",
        "mode_time": "按时间",
        "duration_seconds": "持续时间：",
        "ping_interval": "Ping 间隔：",
        "website_test": "网站测试：",
        "extra_targets": "额外目标：",
        "suffix": "后缀：",
        "custom_suffix": "自定义后缀：",
        "active_extra_targets": "当前额外目标",
        "recent_extra_targets": "历史额外目标",
        "add_selected_history": "加入选中历史",
        "clear_recent_history": "清空历史",
        "history_hint": "历史目标在这里统一显示，双击也可以加入当前额外目标。",
        "cleared_history": "已清空历史额外目标。",
        "added_history_targets": "已从历史加入 {count} 个目标。",
        "add": "添加",
        "remove_selected": "删除选中",
        "clear": "清空",
        "extra_hint": "可以一次粘贴多个目标；添加后会直接显示在下面检测目标表里。没有后缀的内容会按右侧后缀下拉框补全，例如 baidu + .cn = baidu.cn。",
        "language": "语言：",
        "start": "开始检测",
        "stop": "停止",
        "copy_report": "复制报告",
        "export_txt": "导出 TXT",
        "export_csv": "导出 CSV",
        "open_history": "打开历史记录",
        "waiting": "待检测",
        "target_name": "检测目标",
        "target_addr": "地址",
        "loss": "丢包率",
        "avg": "平均延迟",
        "max": "最高延迟",
        "jitter": "抖动范围",
        "status": "状态",
        "diagnosis": "自动诊断",
        "log": "日志",
        "target_progress": "单独 Ping 进度",
        "initial_diagnosis": "点击“开始检测”后，这里会显示网络问题判断。双击表格行可以查看原始 ping 输出。",
        "program_started": "程序已启动。",
        "no_gateway": "没有自动识别到默认网关。可以手动填写，例如 192.168.1.1 或 192.168.1.254。",
        "not_detected": "未识别",
        "gateway_detected": "已自动识别默认网关: {gateway}",
        "need_extra": "请输入至少一个额外目标。",
        "hint": "提示",
        "added_extra": "已添加 {count} 个额外目标。",
        "select_remove": "请先选中目标。",
        "select_target_remove": "请在下面检测目标表中选中要删除的额外目标。",
        "only_extra_remove": "只能删除额外目标，路由器、DNS 和网站测试不能删除。",
        "removed_extra": "已删除 {count} 个额外目标。",
        "cleared_extra": "已清空额外目标。",
        "number_error": "Ping 次数必须是数字。",
        "count_range_error": "Ping 次数必须在 1 到 500 之间。",
        "duration_error": "持续秒数必须是数字。",
        "duration_range_error": "持续秒数必须在 1 到 3600 秒之间。",
        "dns_auto_only": "DNS 已自动识别，不能手动修改。",
        "dns_detected": "已自动识别当前 DNS: {dns}",
        "dns_not_detected": "未自动识别到当前 DNS。DNS 目标会被跳过。",
        "error": "错误",
        "need_target": "至少需要一个检测目标。",
        "running_text": "正在检测。每个目标的进度会独立显示。点击“停止”会停止后续 ping。",
        "start_log": "开始检测，共 {total} 个目标，每个目标 ping {count} 次。",
        "start_log_time": "开始检测，共 {total} 个目标，持续 {seconds} 秒，每 {interval} 秒 ping 一次。",
        "testing": "正在检测 {name} ({target})...",
        "stop_requested": "已请求停止。正在停止后续 ping。",
        "stopping": "正在停止。当前结果只包含已经完成的 ping。",
        "finished": "检测完成。",
        "copied": "报告已复制到剪贴板。",
        "copy_done": "报告已复制，可以直接粘贴。",
        "done": "完成",
        "no_result": "还没有检测结果。",
        "txt_exported": "TXT 报告已导出: {path}",
        "txt_done": "TXT 报告导出成功。",
        "csv_exported": "CSV 数据已导出: {path}",
        "csv_done": "CSV 数据导出成功。",
        "export_failed": "导出失败: {error}",
        "no_history": "还没有历史记录。完成一次检测后会自动生成。",
        "history": "历史记录",
        "open_history_failed": "无法打开历史记录: {error}",
        "raw_output": "原始输出",
        "no_raw": "没有原始输出。",
        "system": "系统",
        "report_title": "网络检测报告",
        "created_at": "生成时间",
        "result_section": "检测结果",
        "diagnosis_section": "自动诊断",
        "suggestion_section": "建议操作",
        "suggestions": [
            "路由器也丢包：优先检查 WiFi 信号、路由器距离、网卡驱动、路由器负载，必要时重启路由器。",
            "路由器正常但外网丢包：更像是运营商线路、DNS、国际出口或目标链路问题。",
            "最高延迟很高但丢包低：说明网络抖动，游戏、网页加载、视频会议会明显受影响。",
            "短测试正常但实际仍卡：把 Ping 次数调到 100 或 200，并在卡顿发生时重新检测。",
            "目标检测失败：可能是地址写错、DNS 解析失败，或目标服务器禁止 ping。",
        ],
        "normal": "正常",
        "slight_loss": "轻微丢包",
        "obvious_loss": "明显丢包",
        "severe_loss": "严重丢包",
        "obvious_jitter": "明显抖动",
        "severe_jitter": "严重抖动",
        "high_latency": "延迟偏高",
        "failed": "检测失败",
        "no_result_status": "无结果",
        "stopped": "已停止",
        "running": "检测中",
        "pending": "等待中",
        "partly_done": "部分完成",
    },
    "en": {
        "app_title": "NetPulse Network Diagnostic Tool",
        "detect_settings": "Test Settings",
        "router": "Router:",
        "auto_detect": "Auto Detect",
        "auto_detect_all": "Auto Detect Router & DNS",
        "dns1": "DNS 1:",
        "dns2": "DNS 2:",
        "ping_count": "Ping Count:",
        "ping_mode": "Ping Mode:",
        "mode_count": "By Count",
        "mode_time": "By Time",
        "duration_seconds": "Duration:",
        "ping_interval": "Ping Interval:",
        "website_test": "Website:",
        "extra_targets": "Extra Targets:",
        "suffix": "Suffix:",
        "custom_suffix": "Custom Suffix:",
        "active_extra_targets": "Current Extra Targets",
        "recent_extra_targets": "Recent Extra Targets",
        "add_selected_history": "Add Selected History",
        "clear_recent_history": "Clear History",
        "history_hint": "Recent targets are shown here. Double-click an item to add it to current extra targets.",
        "cleared_history": "Recent extra target history cleared.",
        "added_history_targets": "Added {count} target(s) from history.",
        "add": "Add",
        "remove_selected": "Remove Selected",
        "clear": "Clear",
        "extra_hint": "You can paste multiple targets at once. Added targets appear directly in the target table below. Targets without a suffix use the selected suffix, for example baidu + .cn = baidu.cn.",
        "language": "Language:",
        "start": "Start Test",
        "stop": "Stop",
        "copy_report": "Copy Report",
        "export_txt": "Export TXT",
        "export_csv": "Export CSV",
        "open_history": "Open History",
        "waiting": "Waiting",
        "target_name": "Target",
        "target_addr": "Address",
        "loss": "Loss",
        "avg": "Avg Latency",
        "max": "Max Latency",
        "jitter": "Jitter Range",
        "status": "Status",
        "diagnosis": "Diagnosis",
        "log": "Log",
        "target_progress": "Individual Ping Progress",
        "initial_diagnosis": "Click “Start Test” to diagnose the network. Double-click a table row to view raw ping output.",
        "program_started": "Program started.",
        "no_gateway": "No default gateway was detected. You can enter it manually, such as 192.168.1.1 or 192.168.1.254.",
        "not_detected": "Not detected",
        "gateway_detected": "Default gateway detected: {gateway}",
        "need_extra": "Please enter at least one extra target.",
        "hint": "Notice",
        "added_extra": "Added {count} extra target(s).",
        "select_remove": "Please select a target first.",
        "select_target_remove": "Please select the extra target(s) in the target table below.",
        "only_extra_remove": "Only extra targets can be removed. Router, DNS, and website targets cannot be removed.",
        "removed_extra": "Removed {count} extra target(s).",
        "cleared_extra": "Extra targets cleared.",
        "number_error": "Ping count must be a number.",
        "count_range_error": "Ping count must be between 1 and 500.",
        "duration_error": "Duration must be a number.",
        "duration_range_error": "Duration must be between 1 and 3600 seconds.",
        "dns_auto_only": "DNS is auto-detected and cannot be edited manually.",
        "dns_detected": "Current DNS auto-detected: {dns}",
        "dns_not_detected": "Current DNS was not detected. DNS targets will be skipped.",
        "error": "Error",
        "need_target": "At least one target is required.",
        "running_text": "Testing. Each target has its own progress bar. Click “Stop” to stop future pings.",
        "start_log": "Started test: {total} targets, {count} pings per target.",
        "start_log_time": "Started test: {total} targets, {seconds} seconds per target.",
        "testing": "Testing {name} ({target})...",
        "stop_requested": "Stop requested. Future pings will be stopped.",
        "stopping": "Stopping. Current results only include completed pings.",
        "finished": "Test finished.",
        "copied": "Report copied to clipboard.",
        "copy_done": "Report copied. You can paste it now.",
        "done": "Done",
        "no_result": "No test result yet.",
        "txt_exported": "TXT report exported: {path}",
        "txt_done": "TXT report exported successfully.",
        "csv_exported": "CSV data exported: {path}",
        "csv_done": "CSV data exported successfully.",
        "export_failed": "Export failed: {error}",
        "no_history": "No history yet. It will be created after the first completed test.",
        "history": "History",
        "open_history_failed": "Failed to open history: {error}",
        "raw_output": "Raw Output",
        "no_raw": "No raw output.",
        "system": "System",
        "report_title": "Network Diagnostic Report",
        "created_at": "Created At",
        "result_section": "Test Results",
        "diagnosis_section": "Diagnosis",
        "suggestion_section": "Suggested Actions",
        "suggestions": [
            "If the router also has packet loss, check Wi-Fi signal, router distance, network adapter driver, router load, and restart the router if needed.",
            "If the router is normal but external targets have packet loss, the issue is more likely related to ISP routing, DNS, international routing, or the target path.",
            "If max latency is high but packet loss is low, the network has jitter. Games, page loading, and video calls may be affected.",
            "If a short test looks normal but real usage is still laggy, set ping count to 100 or 200 and test during the lag.",
            "If a target fails, the address may be wrong, DNS may fail, or the target server may block ping.",
        ],
        "normal": "Normal",
        "slight_loss": "Slight Loss",
        "obvious_loss": "Packet Loss",
        "severe_loss": "Severe Loss",
        "obvious_jitter": "Jitter",
        "severe_jitter": "Severe Jitter",
        "high_latency": "High Latency",
        "failed": "Failed",
        "no_result_status": "No Result",
        "stopped": "Stopped",
        "running": "Running",
        "pending": "Pending",
        "partly_done": "Partly Done",
    },
}

STATUS_LEVEL = {
    "normal": "good",
    "slight_loss": "warn",
    "obvious_loss": "bad",
    "severe_loss": "bad",
    "obvious_jitter": "warn",
    "severe_jitter": "bad",
    "high_latency": "bad",
    "failed": "fail",
    "no_result_status": "fail",
    "stopped": "warn",
    "running": "info",
    "pending": "info",
    "partly_done": "warn",
}


def decode_bytes(data):
    encodings = [locale.getpreferredencoding(False), "gbk", "utf-8", "big5"]
    for encoding in encodings:
        try:
            return data.decode(encoding, errors="ignore")
        except Exception:
            continue
    return data.decode("utf-8", errors="ignore")


def load_config():
    if not CONFIG_FILE.exists():
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        config = DEFAULT_CONFIG.copy()
        config.update(data)
        return config
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as file:
            json.dump(config, file, ensure_ascii=False, indent=2)
    except Exception:
        pass


def clean_target(value):
    value = str(value).strip()
    value = value.replace("https://", "").replace("http://", "")
    value = value.split("/")[0]
    return value.strip()


def is_ipv4_address(value):
    parts = value.split(".")
    if len(parts) != 4:
        return False
    try:
        return all(part.isdigit() and 0 <= int(part) <= 255 for part in parts)
    except ValueError:
        return False


def normalize_suffix(selected_suffix, custom_suffix=""):
    selected_suffix = str(selected_suffix or "").strip()
    custom_suffix = str(custom_suffix or "").strip()

    if selected_suffix in {"不添加 / None", "None", "none", ""}:
        return ""
    if selected_suffix in {"自定义 / Custom", "Custom", "custom"}:
        suffix = custom_suffix
    else:
        suffix = selected_suffix

    suffix = suffix.strip()
    if not suffix:
        return ""
    if not suffix.startswith("."):
        suffix = "." + suffix
    return suffix


def apply_target_suffix(value, selected_suffix=".com", custom_suffix=""):
    target = clean_target(value)
    if not target:
        return ""

    lower_target = target.lower()
    if lower_target == "localhost":
        return target
    if "." in target or ":" in target:
        return target
    if is_ipv4_address(target):
        return target

    suffix = normalize_suffix(selected_suffix, custom_suffix)
    if suffix:
        return f"{target}{suffix}"
    return target


def split_extra_targets(extra_targets, selected_suffix=".com", custom_suffix=""):
    if isinstance(extra_targets, list):
        raw_text = " ".join(str(item) for item in extra_targets)
    else:
        raw_text = str(extra_targets)

    for separator in [",", "，", ";", "；", chr(10), chr(9), chr(13)]:
        raw_text = raw_text.replace(separator, " ")

    clean_items = []
    seen = set()
    for item in raw_text.split():
        target = apply_target_suffix(item, selected_suffix, custom_suffix)
        if not target:
            continue
        key = target.lower()
        if key in seen:
            continue
        seen.add(key)
        clean_items.append(target)
    return clean_items


class PingResult:
    def __init__(self, name, target, target_count=0, mode="count", duration_seconds=0):
        self.name = name
        self.target = target
        self.target_count = target_count
        self.mode = mode
        self.duration_seconds = duration_seconds
        self.progress_total = duration_seconds if mode == "time" else target_count
        self.progress_value = 0
        self.completed = 0
        self.sent = 0
        self.received = 0
        self.lost = 0
        self.loss_rate = None
        self.min_ms = None
        self.max_ms = None
        self.avg_ms = None
        self._total_ms = 0
        self.raw_output = ""
        self.error = ""
        self.stopped = False
        self.running = False
        self.created_at = datetime.now()

    @property
    def jitter_ms(self):
        if self.min_ms is None or self.max_ms is None:
            return None
        return self.max_ms - self.min_ms

    def status_key(self):
        if self.running:
            return "running"
        if self.stopped:
            return "stopped" if self.completed == 0 else "partly_done"
        if self.error and self.received == 0:
            return "failed"
        if self.sent == 0:
            return "pending"
        if self.loss_rate is None:
            return "no_result_status"
        if self.loss_rate >= 8:
            return "severe_loss"
        if self.loss_rate >= 3:
            return "obvious_loss"
        if self.loss_rate >= 1:
            return "slight_loss"
        if self.max_ms is not None and self.max_ms >= 800:
            return "severe_jitter"
        if self.max_ms is not None and self.max_ms >= 300:
            return "obvious_jitter"
        if self.avg_ms is not None and self.avg_ms >= 150:
            return "high_latency"
        return "normal"

    def status_text(self, language="zh"):
        return TEXT.get(language, TEXT["zh"]).get(self.status_key(), self.status_key())

    def merge_single_result(self, single):
        self.completed += 1
        if self.mode == "count":
            self.progress_value = self.completed
        if single.raw_output:
            self.raw_output += f"\n===== Ping {self.completed} =====\n{single.raw_output}\n"

        if single.sent > 0:
            self.sent += single.sent
            self.received += single.received
            self.lost += single.lost
        else:
            self.sent += 1
            self.lost += 1

        if single.received > 0 and single.avg_ms is not None:
            self._total_ms += single.avg_ms * single.received
            self.avg_ms = round(self._total_ms / max(1, self.received))

            if single.min_ms is not None:
                self.min_ms = single.min_ms if self.min_ms is None else min(self.min_ms, single.min_ms)
            if single.max_ms is not None:
                self.max_ms = single.max_ms if self.max_ms is None else max(self.max_ms, single.max_ms)

        if single.error and self.received == 0:
            self.error = single.error

        if self.sent > 0:
            self.loss_rate = round((self.lost / self.sent) * 100)

    def to_row(self, language="zh"):
        return {
            "time": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "name": self.name,
            "target": self.target,
            "completed": self.completed,
            "target_count": self.target_count,
            "mode": self.mode,
            "duration_seconds": self.duration_seconds,
            "sent": self.sent,
            "received": self.received,
            "lost": self.lost,
            "loss_rate": "" if self.loss_rate is None else self.loss_rate,
            "min_ms": "" if self.min_ms is None else self.min_ms,
            "max_ms": "" if self.max_ms is None else self.max_ms,
            "avg_ms": "" if self.avg_ms is None else self.avg_ms,
            "jitter_ms": "" if self.jitter_ms is None else self.jitter_ms,
            "status": self.status_text(language),
            "error": self.error,
        }

    def to_report_text(self, language="zh"):
        t = TEXT.get(language, TEXT["zh"])
        lines = [
            f"[{self.name}] {self.target}",
            f"{t['status']}: {self.status_text(language)}",
            f"Progress: {self.completed} ping(s)" if self.mode == "time" else f"Progress: {self.completed}/{self.target_count}",
            f"Duration: {self.duration_seconds} seconds" if self.mode == "time" else "",
            f"Sent: {self.sent}",
            f"Received: {self.received}",
            f"Lost: {self.lost}",
            f"{t['loss']}: {self.loss_rate if self.loss_rate is not None else 'N/A'}%",
            f"Min Latency: {self.min_ms if self.min_ms is not None else 'N/A'} ms",
            f"{t['max']}: {self.max_ms if self.max_ms is not None else 'N/A'} ms",
            f"{t['avg']}: {self.avg_ms if self.avg_ms is not None else 'N/A'} ms",
            f"{t['jitter']}: {self.jitter_ms if self.jitter_ms is not None else 'N/A'} ms",
        ]
        lines = [line for line in lines if line != ""]
        if self.error:
            lines.append(f"Error: {self.error}")
        return "\n".join(lines)


def parse_ping_output(name, target, output):
    result = PingResult(name, target, target_count=1)
    result.raw_output = output

    packet_patterns = [
        r"已发送\s*=\s*(\d+).*?已接收\s*=\s*(\d+).*?丢失\s*=\s*(\d+).*?\((\d+)%",
        r"Sent\s*=\s*(\d+).*?Received\s*=\s*(\d+).*?Lost\s*=\s*(\d+).*?\((\d+)%",
    ]
    for pattern in packet_patterns:
        match = re.search(pattern, output, re.S | re.I)
        if match:
            result.sent = int(match.group(1))
            result.received = int(match.group(2))
            result.lost = int(match.group(3))
            result.loss_rate = int(match.group(4))
            break

    time_patterns = [
        r"最短\s*=\s*(\d+)ms.*?最长\s*=\s*(\d+)ms.*?平均\s*=\s*(\d+)ms",
        r"Minimum\s*=\s*(\d+)ms.*?Maximum\s*=\s*(\d+)ms.*?Average\s*=\s*(\d+)ms",
        r"time[=<]\s*(\d+)ms",
        r"时间[=<]\s*(\d+)ms",
    ]
    for pattern in time_patterns:
        match = re.search(pattern, output, re.S | re.I)
        if match:
            if len(match.groups()) == 3:
                result.min_ms = int(match.group(1))
                result.max_ms = int(match.group(2))
                result.avg_ms = int(match.group(3))
            else:
                value = int(match.group(1))
                result.min_ms = value
                result.max_ms = value
                result.avg_ms = value
            break

    if result.loss_rate is None:
        lowered = output.lower()
        if "could not find host" in lowered or "找不到主机" in output:
            result.error = "DNS resolution failed or the target address is incorrect."
        elif "general failure" in lowered or "一般故障" in output:
            result.error = "The local network stack returned a general failure. Restart the adapter or check network settings."
        elif "request timed out" in lowered or "请求超时" in output:
            result.sent = 1
            result.received = 0
            result.lost = 1
            result.loss_rate = 100
            result.error = "Request timed out."
        else:
            result.error = "Ping output could not be parsed. The target may be unreachable or the output format is unsupported."

    return result


def build_ping_command(target, count=1):
    if platform.system().lower().startswith("windows"):
        return ["ping", "-n", str(count), target]
    return ["ping", "-c", str(count), target]


def run_ping_once(name, target):
    result = PingResult(name, target, target_count=1)
    try:
        completed = subprocess.run(
            build_ping_command(target, 1),
            capture_output=True,
            timeout=8,
        )
        output = decode_bytes(completed.stdout + completed.stderr)
        return parse_ping_output(name, target, output)
    except subprocess.TimeoutExpired:
        result.sent = 1
        result.lost = 1
        result.loss_rate = 100
        result.error = "Ping command timed out."
        return result
    except FileNotFoundError:
        result.error = "The ping command was not found."
        return result
    except Exception as exc:
        result.error = str(exc)
        return result


def get_default_gateway():
    if not platform.system().lower().startswith("windows"):
        return ""
    try:
        completed = subprocess.run(["ipconfig"], capture_output=True, timeout=8)
        output = decode_bytes(completed.stdout + completed.stderr)
        patterns = [
            r"Default Gateway[^:]*:\s*([0-9]+(?:\.[0-9]+){3})",
            r"默认网关[^:：]*[:：]\s*([0-9]+(?:\.[0-9]+){3})",
        ]
        for pattern in patterns:
            match = re.search(pattern, output, re.I)
            if match:
                return match.group(1)
    except Exception:
        return ""
    return ""


def get_dns_servers():
    if not platform.system().lower().startswith("windows"):
        return []
    try:
        completed = subprocess.run(["ipconfig", "/all"], capture_output=True, timeout=8)
        output = decode_bytes(completed.stdout + completed.stderr)
    except Exception:
        return []

    servers = []
    collecting = False
    label_pattern = re.compile(r"(DNS Servers|DNS 服务器|DNS 伺服器)", re.I)
    ip_pattern = re.compile(r"(?:\d{1,3}\.){3}\d{1,3}")

    for line in output.splitlines():
        if label_pattern.search(line):
            collecting = True
            for ip in ip_pattern.findall(line):
                if ip not in servers:
                    servers.append(ip)
            continue

        if collecting:
            ips = ip_pattern.findall(line)
            if ips:
                for ip in ips:
                    if ip not in servers:
                        servers.append(ip)
                continue

            stripped = line.strip()
            if stripped and ":" in stripped:
                collecting = False

        if len(servers) >= 2:
            break

    return servers[:2]


def make_targets(config):
    candidates = [
        ("Router" if config.get("language") == "en" else "路由器", config.get("router_ip", "")),
        ("DNS 1", config.get("dns_primary", "")),
        ("DNS 2", config.get("dns_secondary", "")),
        ("Website" if config.get("language") == "en" else "网站测试", config.get("website", "")),
    ]

    extra_targets = split_extra_targets(
        config.get("extra_targets", ""),
        config.get("target_suffix", ".com"),
        config.get("custom_suffix", ""),
    )
    custom_prefix = "Custom" if config.get("language") == "en" else "自定义"
    for index, item in enumerate(extra_targets, start=1):
        candidates.append((f"{custom_prefix}{index}", item))

    targets = []
    seen = set()
    for name, target in candidates:
        target = clean_target(target)
        if not target:
            continue
        key = target.lower()
        if key in seen:
            continue
        seen.add(key)
        targets.append((name, target))
    return targets


def has_loss(result, threshold):
    return result and result.loss_rate is not None and result.loss_rate >= threshold


def has_jitter(result, threshold):
    return result and result.max_ms is not None and result.max_ms >= threshold


def diagnose(results, language="zh"):
    if not results:
        return "暂无诊断结果。" if language == "zh" else "No diagnosis yet."

    is_en = language == "en"
    router_names = {"路由器", "Router"}
    site_names = {"网站测试", "Website"}
    router = next((item for item in results if item.name in router_names), None)
    external = [item for item in results if item.name not in router_names]
    parsed = [item for item in results if item.sent > 0]
    failed = [item for item in results if item.error and item.received == 0]

    if not parsed:
        return (
            "所有目标都没有得到可解析结果。请确认电脑当前网络可用、目标地址正确，并检查系统是否允许 ping。"
            if not is_en else
            "No target returned a usable result. Check whether the computer is online, targets are correct, and ping is allowed."
        )

    advice = []

    if has_loss(router, 2):
        advice.append(
            "电脑到路由器已经丢包：问题优先考虑本机 WiFi、无线信号、路由器距离、路由器负载、网卡驱动，而不是网站本身。"
            if not is_en else
            "Packet loss already appears between this computer and the router. Check Wi-Fi signal, router distance, router load, and network adapter driver first."
        )
    elif router and router.loss_rate == 0:
        bad_external = [item for item in external if has_loss(item, 2)]
        if bad_external:
            advice.append(
                "路由器不丢包，但外网目标丢包：更像是运营商线路、DNS、国际出口、目标服务器链路或当前网络拥堵。"
                if not is_en else
                "The router is stable, but external targets have packet loss. This is more likely related to ISP routing, DNS, international routing, target path, or congestion."
            )

    if router and router.loss_rate == 0:
        dns_bad = [item for item in results if item.name.startswith("DNS") and has_loss(item, 2)]
        site_bad = [item for item in results if item.name in site_names and has_loss(item, 2)]
        if dns_bad and site_bad:
            advice.append("DNS 和网站都丢包：整体外网链路可能不稳定。" if not is_en else "Both DNS and website targets have packet loss. The external network path may be unstable.")
        elif dns_bad:
            advice.append("DNS 目标丢包：可以尝试更换 DNS，或测试运营商默认 DNS。" if not is_en else "DNS targets have packet loss. Try another DNS server or test your ISP's default DNS.")
        elif site_bad:
            advice.append("DNS 正常但网站测试异常：可能是该网站链路或跨区访问问题。" if not is_en else "DNS looks normal, but the website target is abnormal. It may be a site path or cross-region issue.")

    jitter_items = [item for item in parsed if has_jitter(item, 300)]
    if jitter_items:
        names = ", ".join(item.name for item in jitter_items)
        advice.append(
            f"检测到明显延迟尖峰：{names}。这种情况会造成网页偶尔转圈、游戏瞬移、语音/视频会议卡顿。"
            if not is_en else
            f"Latency spikes detected: {names}. This can cause page loading stalls, game lag, and video call stutters."
        )

    high_latency_items = [item for item in parsed if item.avg_ms is not None and item.avg_ms >= 150]
    if high_latency_items:
        names = ", ".join(item.name for item in high_latency_items)
        advice.append(
            f"平均延迟偏高：{names}。如果只有网站偏高，可能只是跨区访问慢；如果 DNS 也高，说明整体线路质量偏差。"
            if not is_en else
            f"Average latency is high: {names}. If only the website is high, it may be cross-region access; if DNS is also high, the overall path quality may be poor."
        )

    if failed:
        names = ", ".join(item.name for item in failed)
        advice.append(
            f"以下目标检测失败：{names}。可能是地址写错、DNS 解析失败、目标服务器禁 ping，或网络严重不可达。"
            if not is_en else
            f"The following targets failed: {names}. The address may be wrong, DNS may fail, the server may block ping, or the network may be unreachable."
        )

    stopped = [item for item in results if item.stopped]
    if stopped:
        advice.append("检测已停止，结果只包含已完成的 ping。" if not is_en else "The test was stopped. Results only include completed pings.")

    if not advice:
        return (
            "本次检测没有发现明显丢包、严重抖动或高延迟。若实际仍卡，建议把 Ping 次数调到 100 或 200，并在卡顿发生时重新检测。"
            if not is_en else
            "No obvious packet loss, severe jitter, or high latency was found. If it still lags, set ping count to 100 or 200 and test during the lag."
        )

    return "\n".join(f"{index}. {text}" for index, text in enumerate(advice, start=1))


def build_completion_summary(results, diagnosis, language="zh"):
    is_en = language == "en"
    total = len(results)
    completed = sum(1 for item in results if item.completed > 0)
    failed = [item for item in results if item.status_key() == "failed"]
    severe = [item for item in results if item.status_key() in {"severe_loss", "obvious_loss", "severe_jitter", "high_latency"}]
    warning = [item for item in results if item.status_key() in {"slight_loss", "obvious_jitter", "partly_done", "stopped"}]
    normal = [item for item in results if item.status_key() == "normal"]

    def fmt_items(items):
        if not items:
            return "None" if is_en else "无"
        lines = []
        for item in items[:8]:
            loss = "N/A" if item.loss_rate is None else f"{item.loss_rate}%"
            avg = "N/A" if item.avg_ms is None else f"{item.avg_ms}ms"
            max_ms = "N/A" if item.max_ms is None else f"{item.max_ms}ms"
            lines.append(f"- {item.name} ({item.target}): {item.status_text(language)}, loss {loss}, avg {avg}, max {max_ms}")
        if len(items) > 8:
            lines.append((f"... and {len(items) - 8} more" if is_en else f"... 还有 {len(items) - 8} 个"))
        return "\n".join(lines)

    if failed or severe:
        overall = "Network issue found" if is_en else "检测到网络问题"
    elif warning:
        overall = "Minor issue found" if is_en else "检测到轻微问题"
    else:
        overall = "Network looks normal" if is_en else "网络状态正常"

    if is_en:
        lines = [
            f"Result: {overall}",
            f"Targets completed: {completed}/{total}",
            "",
            f"Normal targets: {len(normal)}",
            f"Warning targets: {len(warning)}",
            f"Severe targets: {len(severe)}",
            f"Failed targets: {len(failed)}",
            "",
            "Severe / high-latency targets:",
            fmt_items(severe),
            "",
            "Failed targets:",
            fmt_items(failed),
            "",
            "Diagnosis:",
            diagnosis,
        ]
    else:
        lines = [
            f"结果：{overall}",
            f"完成目标：{completed}/{total}",
            "",
            f"正常目标：{len(normal)} 个",
            f"轻微问题：{len(warning)} 个",
            f"严重/高延迟：{len(severe)} 个",
            f"检测失败：{len(failed)} 个",
            "",
            "严重或高延迟目标：",
            fmt_items(severe),
            "",
            "检测失败目标：",
            fmt_items(failed),
            "",
            "诊断结论：",
            diagnosis,
        ]
    return "\n".join(lines)


def append_history(results, language="zh"):
    if not results:
        return
    fieldnames = list(results[0].to_row(language).keys())
    file_exists = HISTORY_FILE.exists()
    try:
        with open(HISTORY_FILE, "a", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            for result in results:
                writer.writerow(result.to_row(language))
    except Exception:
        pass


class NetPulseApp:
    def __init__(self, root):
        self.root = root
        self.config = load_config()
        self.language = self.config.get("language", "zh") if self.config.get("language") in TEXT else "zh"
        self.results = []
        self.result_by_iid = {}
        self.tree_iid_by_result = {}
        self.progress_widgets = {}
        self.is_running = False
        self.stop_event = threading.Event()
        self.result_lock = threading.Lock()
        self.active_extra_targets = split_extra_targets(
            self.config.get("extra_targets", ""), "不添加 / None", ""
        )

        self.refresh_dns_servers(show_log=False, update_widgets=False)
        self.root.title(f"{APP_NAME} v{APP_VERSION} - {AUTHOR}")
        self.root.geometry("1180x760")
        self.root.minsize(760, 560)
        self.setup_style()
        self.create_widgets()

    def tr(self, key):
        return TEXT.get(self.language, TEXT["zh"]).get(key, key)

    def setup_style(self):
        style = ttk.Style()
        # The Windows "vista" theme can ignore Treeview tag background colors.
        # "default" keeps row colors reliable; fall back to "clam" if needed.
        for theme_name in ("clam", "default"):
            try:
                style.theme_use(theme_name)
                break
            except tk.TclError:
                continue
        style.configure("Treeview", rowheight=28, background="white", fieldbackground="white", foreground="#111111")
        style.map("Treeview", background=[("selected", "#4a6984")], foreground=[("selected", "white")])
        style.configure("TButton", padding=6)
        style.configure("Header.TLabel", font=("Microsoft YaHei", 18, "bold"))
        style.configure("Sub.TLabel", font=("Microsoft YaHei", 9))

    def create_widgets(self):
        for child in self.root.winfo_children():
            child.destroy()

        # Use a scrollable main area so the bottom UI remains reachable on
        # small screens or high Windows display-scaling settings.
        outer_frame = ttk.Frame(self.root)
        outer_frame.pack(fill="both", expand=True)

        self.main_canvas = tk.Canvas(outer_frame, highlightthickness=0)
        self.main_scrollbar = ttk.Scrollbar(outer_frame, orient="vertical", command=self.main_canvas.yview)
        self.main_canvas.configure(yscrollcommand=self.main_scrollbar.set)

        self.main_scrollbar.pack(side="right", fill="y")
        self.main_canvas.pack(side="left", fill="both", expand=True)

        self.content_frame = ttk.Frame(self.main_canvas)
        self.content_window = self.main_canvas.create_window((0, 0), window=self.content_frame, anchor="nw")

        def update_scroll_region(event=None):
            self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))

        def update_content_width(event):
            self.main_canvas.itemconfigure(self.content_window, width=event.width)

        def on_mousewheel(event):
            if event.delta:
                self.main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.content_frame.bind("<Configure>", update_scroll_region)
        self.main_canvas.bind("<Configure>", update_content_width)
        self.main_canvas.bind_all("<MouseWheel>", on_mousewheel)

        parent = self.content_frame

        header_frame = ttk.Frame(parent, padding=(14, 12, 14, 6))
        header_frame.pack(fill="x")

        ttk.Label(header_frame, text=self.tr("app_title"), style="Header.TLabel").pack(side="left")
        ttk.Label(header_frame, text=f"v{APP_VERSION} | Author: {AUTHOR}", style="Sub.TLabel").pack(side="left", padx=(10, 0), pady=(8, 0))

        language_frame = ttk.Frame(parent, padding=(14, 0, 14, 8))
        language_frame.pack(fill="x")
        ttk.Label(language_frame, text=self.tr("language")).pack(side="left", padx=(0, 4))
        self.language_var = tk.StringVar(value="English" if self.language == "en" else "中文")
        language_combo = ttk.Combobox(
            language_frame,
            textvariable=self.language_var,
            values=["中文", "English"],
            width=12,
            state="readonly",
        )
        language_combo.pack(side="left")
        language_combo.bind("<<ComboboxSelected>>", self.change_language)

        settings = ttk.LabelFrame(parent, text=self.tr("detect_settings"), padding=10)
        settings.pack(fill="x", padx=14, pady=(0, 8))

        self.router_var = tk.StringVar(value=self.config.get("router_ip", DEFAULT_CONFIG["router_ip"]))
        self.dns1_var = tk.StringVar(value=self.config.get("dns_primary", DEFAULT_CONFIG["dns_primary"]))
        self.dns2_var = tk.StringVar(value=self.config.get("dns_secondary", DEFAULT_CONFIG["dns_secondary"]))
        self.website_var = tk.StringVar(value=self.config.get("website", DEFAULT_CONFIG["website"]))
        self.extra_input_var = tk.StringVar(value="")
        self.target_suffix_var = tk.StringVar(value=self.config.get("target_suffix", DEFAULT_CONFIG["target_suffix"]))
        self.custom_suffix_var = tk.StringVar(value=self.config.get("custom_suffix", DEFAULT_CONFIG["custom_suffix"]))
        self.count_var = tk.StringVar(value=self.config.get("count", DEFAULT_CONFIG["count"]))
        stored_ping_mode = self.config.get("ping_mode", DEFAULT_CONFIG["ping_mode"])
        if stored_ping_mode in {"time", "按时间", "By Time"}:
            ping_mode_display = self.tr("mode_time")
        else:
            ping_mode_display = self.tr("mode_count")
        self.ping_mode_var = tk.StringVar(value=ping_mode_display)
        self.duration_var = tk.StringVar(value=self.config.get("duration_seconds", DEFAULT_CONFIG["duration_seconds"]))
        self.ping_interval_var = tk.StringVar(value=self.config.get("ping_interval_seconds", DEFAULT_CONFIG["ping_interval_seconds"]))

        # Row 0: network identity. Keep these fields on separate rows so they do not
        # disappear when the window becomes narrow or Windows display scaling is high.
        ttk.Label(settings, text=self.tr("router")).grid(row=0, column=0, sticky="w", padx=(0, 4), pady=4)
        ttk.Entry(settings, textvariable=self.router_var, width=20).grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=4)

        ttk.Label(settings, text=self.tr("dns1")).grid(row=0, column=2, sticky="w", padx=(0, 4), pady=4)
        self.dns1_entry = ttk.Entry(settings, textvariable=self.dns1_var, width=20, state="readonly")
        self.dns1_entry.grid(row=0, column=3, sticky="ew", padx=(0, 10), pady=4)

        ttk.Label(settings, text=self.tr("dns2")).grid(row=0, column=4, sticky="w", padx=(0, 4), pady=4)
        self.dns2_entry = ttk.Entry(settings, textvariable=self.dns2_var, width=20, state="readonly")
        self.dns2_entry.grid(row=0, column=5, sticky="ew", padx=(0, 10), pady=4)

        ttk.Button(settings, text=self.tr("auto_detect_all"), command=self.auto_detect_network).grid(
            row=0, column=6, sticky="ew", padx=(4, 0), pady=4
        )

        # Row 1: website and extra-target input.
        ttk.Label(settings, text=self.tr("website_test")).grid(row=1, column=0, sticky="w", padx=(0, 4), pady=4)
        self.website_combo = ttk.Combobox(settings, textvariable=self.website_var, values=COMMON_WEBSITES, width=30)
        self.website_combo.grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=4)

        ttk.Label(settings, text=self.tr("extra_targets")).grid(row=1, column=2, sticky="w", padx=(0, 4), pady=4)
        self.extra_entry = ttk.Entry(settings, textvariable=self.extra_input_var)
        self.extra_entry.grid(row=1, column=3, columnspan=3, sticky="ew", pady=4)
        ttk.Button(settings, text=self.tr("add"), command=self.add_extra_targets_from_input).grid(
            row=1, column=6, sticky="ew", padx=(4, 0), pady=4
        )

        # Row 2: suffix controls. Custom suffix stays disabled unless Custom is selected.
        ttk.Label(settings, text=self.tr("suffix")).grid(row=2, column=0, sticky="w", padx=(0, 4), pady=4)
        self.suffix_combo = ttk.Combobox(settings, textvariable=self.target_suffix_var, values=DOMAIN_SUFFIXES, width=18, state="readonly")
        self.suffix_combo.grid(row=2, column=1, sticky="ew", padx=(0, 10), pady=4)
        self.suffix_combo.bind("<<ComboboxSelected>>", self.update_custom_suffix_state)

        ttk.Label(settings, text=self.tr("custom_suffix")).grid(row=2, column=2, sticky="w", padx=(0, 4), pady=4)
        self.custom_suffix_entry = ttk.Entry(settings, textvariable=self.custom_suffix_var, width=18)
        self.custom_suffix_entry.grid(row=2, column=3, sticky="ew", padx=(0, 10), pady=4)
        self.update_custom_suffix_state()

        ttk.Button(settings, text=self.tr("remove_selected"), command=self.remove_selected_extra_targets).grid(row=2, column=4, sticky="ew", padx=(0, 4), pady=4)
        ttk.Button(settings, text=self.tr("clear"), command=self.clear_extra_targets).grid(row=2, column=5, sticky="ew", padx=(0, 4), pady=4)

        # Row 3: ping mode. Count and time are visually separated and the inactive
        # inputs are disabled by update_ping_mode_state().
        ttk.Label(settings, text=self.tr("ping_mode")).grid(row=3, column=0, sticky="w", padx=(0, 4), pady=(10, 4))
        self.ping_mode_combo = ttk.Combobox(
            settings,
            textvariable=self.ping_mode_var,
            values=[self.tr("mode_count"), self.tr("mode_time")],
            width=12,
            state="readonly",
        )
        self.ping_mode_combo.grid(row=3, column=1, sticky="ew", padx=(0, 10), pady=(10, 4))
        self.ping_mode_combo.bind("<<ComboboxSelected>>", self.update_ping_mode_state)

        ttk.Label(settings, text=self.tr("ping_count")).grid(row=3, column=2, sticky="w", padx=(0, 4), pady=(10, 4))
        self.count_combo = ttk.Combobox(
            settings,
            textvariable=self.count_var,
            values=["4", "10", "20", "50", "100", "200", "500"],
            width=10,
            state="readonly",
        )
        self.count_combo.grid(row=3, column=3, sticky="ew", padx=(0, 10), pady=(10, 4))

        ttk.Label(settings, text=self.tr("duration_seconds")).grid(row=3, column=4, sticky="w", padx=(0, 4), pady=(10, 4))
        self.duration_combo = ttk.Combobox(
            settings,
            textvariable=self.duration_var,
            values=["10", "30", "60", "120", "300", "600", "1800", "3600"],
            width=10,
            state="readonly",
        )
        self.duration_combo.grid(row=3, column=5, sticky="ew", padx=(0, 10), pady=(10, 4))

        ttk.Label(settings, text=self.tr("ping_interval")).grid(row=3, column=6, sticky="w", padx=(0, 4), pady=(10, 4))
        self.interval_combo = ttk.Combobox(
            settings,
            textvariable=self.ping_interval_var,
            values=["1", "2", "3", "5", "10", "30", "60"],
            width=10,
            state="readonly",
        )
        self.interval_combo.grid(row=3, column=7, sticky="ew", pady=(10, 4))

        ttk.Label(settings, text=self.tr("extra_hint")).grid(row=4, column=0, columnspan=8, sticky="w", pady=(4, 2))
        for column in range(8):
            settings.columnconfigure(column, weight=1)
        self.update_ping_mode_state()

        history_frame = ttk.LabelFrame(parent, text=self.tr("recent_extra_targets"), padding=10)
        history_frame.pack(fill="x", padx=14, pady=(0, 8))
        ttk.Label(history_frame, text=self.tr("history_hint")).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 4))
        self.recent_listbox = tk.Listbox(history_frame, height=6, selectmode="extended")
        self.recent_listbox.grid(row=1, column=0, sticky="ew", padx=(0, 8))
        recent_scroll = ttk.Scrollbar(history_frame, orient="vertical", command=self.recent_listbox.yview)
        recent_scroll.grid(row=1, column=1, sticky="ns", padx=(0, 8))
        self.recent_listbox.configure(yscrollcommand=recent_scroll.set)
        history_buttons = ttk.Frame(history_frame)
        history_buttons.grid(row=1, column=2, sticky="n")
        ttk.Button(history_buttons, text=self.tr("add_selected_history"), command=self.add_selected_recent_targets).pack(fill="x", pady=(0, 6))
        ttk.Button(history_buttons, text=self.tr("clear_recent_history"), command=self.clear_recent_extra_targets).pack(fill="x")
        self.recent_listbox.bind("<Double-1>", lambda event: self.add_selected_recent_targets())
        history_frame.columnconfigure(0, weight=1)
        self.refresh_recent_history_listbox()

        control = ttk.Frame(parent, padding=(14, 0, 14, 8))
        control.pack(fill="x")

        self.start_button = ttk.Button(control, text=self.tr("start"), command=self.start_test)
        self.start_button.pack(side="left")
        self.stop_button = ttk.Button(control, text=self.tr("stop"), command=self.stop_test, state="disabled")
        self.stop_button.pack(side="left", padx=8)
        self.copy_button = ttk.Button(control, text=self.tr("copy_report"), command=self.copy_report, state="disabled")
        self.copy_button.pack(side="left")
        self.txt_button = ttk.Button(control, text=self.tr("export_txt"), command=self.export_txt, state="disabled")
        self.txt_button.pack(side="left", padx=8)
        self.csv_button = ttk.Button(control, text=self.tr("export_csv"), command=self.export_csv, state="disabled")
        self.csv_button.pack(side="left")
        self.open_history_button = ttk.Button(control, text=self.tr("open_history"), command=self.open_history)
        self.open_history_button.pack(side="left", padx=8)

        self.progress = ttk.Progressbar(control, mode="determinate")
        self.progress.pack(side="left", padx=12, fill="x", expand=True)
        self.progress_var = tk.StringVar(value=self.tr("waiting"))
        ttk.Label(control, textvariable=self.progress_var, width=18).pack(side="right")

        table_frame = ttk.Frame(parent, padding=(14, 0, 14, 8))
        table_frame.pack(fill="both", expand=True)

        columns = ("name", "target", "loss", "avg", "max", "jitter", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=8)
        self.tree.heading("name", text=self.tr("target_name"))
        self.tree.heading("target", text=self.tr("target_addr"))
        self.tree.heading("loss", text=self.tr("loss"))
        self.tree.heading("avg", text=self.tr("avg"))
        self.tree.heading("max", text=self.tr("max"))
        self.tree.heading("jitter", text=self.tr("jitter"))
        self.tree.heading("status", text=self.tr("status"))
        self.tree.column("name", width=120, anchor="center")
        self.tree.column("target", width=210, anchor="center")
        self.tree.column("loss", width=90, anchor="center")
        self.tree.column("avg", width=110, anchor="center")
        self.tree.column("max", width=110, anchor="center")
        self.tree.column("jitter", width=110, anchor="center")
        self.tree.column("status", width=130, anchor="center")
        self.tree.tag_configure("good", background="#C8E6C9", foreground="#0B3D0B")   # Success / low latency: green
        self.tree.tag_configure("warn", background="#FFF3B0", foreground="#5C4400")   # Slight issue: yellow
        self.tree.tag_configure("bad", background="#FFCDD2", foreground="#7A0000")    # Severe loss / high latency: red
        self.tree.tag_configure("fail", background="#D7CCC8", foreground="#3E2723")   # Failed target: brown/gray
        self.tree.tag_configure("info", background="#BBDEFB", foreground="#0D47A1")   # Pending / running: blue
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", self.show_raw_output)
        self.refresh_target_preview()

        progress_frame = ttk.LabelFrame(parent, text=self.tr("target_progress"), padding=10)
        progress_frame.pack(fill="x", padx=14, pady=(0, 8))
        self.progress_container = ttk.Frame(progress_frame)
        self.progress_container.pack(fill="x")

        diagnosis_frame = ttk.LabelFrame(parent, text=self.tr("diagnosis"), padding=10)
        diagnosis_frame.pack(fill="x", padx=14, pady=(0, 8))
        self.diagnosis_var = tk.StringVar(value=self.tr("initial_diagnosis"))
        ttk.Label(diagnosis_frame, textvariable=self.diagnosis_var, wraplength=1040, justify="left").pack(fill="x")

        log_frame = ttk.LabelFrame(parent, text=self.tr("log"), padding=10)
        log_frame.pack(fill="both", padx=14, pady=(0, 14))
        self.log_text = tk.Text(log_frame, height=5, wrap="word")
        self.log_text.pack(fill="both", expand=True)
        self.log(self.tr("program_started"))
        detected_dns = [item for item in [self.config.get("dns_primary", ""), self.config.get("dns_secondary", "")] if item]
        if detected_dns:
            self.log(self.tr("dns_detected").format(dns=", ".join(detected_dns)))
        else:
            self.log(self.tr("dns_not_detected"))

        self.set_running_state(False)

    def change_language(self, event=None):
        if self.is_running:
            return
        self.config = self.get_current_config()
        self.language = "en" if self.language_var.get() == "English" else "zh"
        self.config["language"] = self.language
        save_config(self.config)
        self.results = []
        self.active_extra_targets = split_extra_targets(
            self.config.get("extra_targets", ""), "不添加 / None", ""
        )
        self.create_widgets()

    def update_custom_suffix_state(self, event=None):
        if not hasattr(self, "custom_suffix_entry"):
            return
        selected = self.target_suffix_var.get()
        is_custom = selected in {"自定义 / Custom", "Custom", "custom"}
        self.custom_suffix_entry.config(state="normal" if is_custom else "disabled")

    def update_ping_mode_state(self, event=None):
        if not hasattr(self, "count_combo"):
            return
        is_time = self.ping_mode_var.get().strip() in {self.tr("mode_time"), "time", "按时间", "By Time"}
        if is_time:
            self.count_combo.config(state="disabled")
            self.duration_combo.config(state="readonly")
            self.interval_combo.config(state="readonly")
        else:
            self.count_combo.config(state="readonly")
            self.duration_combo.config(state="disabled")
            self.interval_combo.config(state="disabled")

    def get_preview_config(self):
        return {
            "router_ip": self.router_var.get().strip(),
            "dns_primary": self.dns1_var.get().strip(),
            "dns_secondary": self.dns2_var.get().strip(),
            "website": self.website_var.get().strip(),
            "extra_targets": list(self.active_extra_targets),
            "target_suffix": "不添加 / None",
            "custom_suffix": "",
            "count": self.count_var.get().strip(),
            "ping_mode": "time" if self.ping_mode_var.get().strip() in {self.tr("mode_time"), "time", "按时间", "By Time"} else "count",
            "duration_seconds": self.duration_var.get().strip(),
            "ping_interval_seconds": self.ping_interval_var.get().strip(),
            "language": self.language,
        }

    def refresh_target_preview(self):
        if not hasattr(self, "tree") or self.is_running:
            return
        self.clear_table()
        preview_config = self.get_preview_config()
        for name, target in make_targets(preview_config):
            result = PingResult(name, target, 0)
            iid = self.tree.insert(
                "",
                "end",
                values=(name, target, "N/A", "N/A", "N/A", "N/A", self.tr("pending")),
                tags=("info",),
            )
            self.result_by_iid[iid] = result

    def refresh_dns_servers(self, show_log=True, update_widgets=True):
        servers = get_dns_servers()
        dns1 = servers[0] if len(servers) >= 1 else ""
        dns2 = servers[1] if len(servers) >= 2 else ""
        self.config["dns_primary"] = dns1
        self.config["dns_secondary"] = dns2

        if update_widgets and hasattr(self, "dns1_var"):
            self.dns1_var.set(dns1)
            self.dns2_var.set(dns2)

        if show_log and hasattr(self, "log"):
            if servers:
                self.log(self.tr("dns_detected").format(dns=", ".join(servers)))
            else:
                self.log(self.tr("dns_not_detected"))
        return servers


    def auto_gateway(self):
        gateway = get_default_gateway()
        if gateway:
            self.router_var.set(gateway)
            self.log(self.tr("gateway_detected").format(gateway=gateway))
        else:
            messagebox.showwarning(self.tr("not_detected"), self.tr("no_gateway"))

    def auto_detect_network(self):
        gateway = get_default_gateway()
        if gateway:
            self.router_var.set(gateway)
            self.log(self.tr("gateway_detected").format(gateway=gateway))
        else:
            messagebox.showwarning(self.tr("not_detected"), self.tr("no_gateway"))

        self.refresh_dns_servers(show_log=True, update_widgets=True)
        self.config = self.get_current_config()
        save_config(self.config)
        self.refresh_target_preview()

    def log(self, message):
        now = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{now}] {message}\n")
        self.log_text.see("end")

    def get_recent_extra_targets(self):
        recent = self.config.get("recent_extra_targets", [])
        if not isinstance(recent, list):
            return []
        clean_items = []
        seen = set()
        for item in recent:
            item = clean_target(str(item))
            if not item:
                continue
            key = item.lower()
            if key in seen:
                continue
            seen.add(key)
            clean_items.append(item)
        return clean_items[:60]

    def refresh_recent_history_listbox(self):
        if not hasattr(self, "recent_listbox"):
            return
        self.recent_listbox.delete(0, "end")
        for target in self.get_recent_extra_targets():
            self.recent_listbox.insert("end", target)

    def update_recent_extra_targets(self, targets):
        # History stores completed target names only. Do not append suffix again here.
        if isinstance(targets, list):
            new_targets = split_extra_targets(targets, "不添加 / None", "")
        else:
            new_targets = split_extra_targets(targets, self.target_suffix_var.get(), self.custom_suffix_var.get())
        if not new_targets:
            return
        old_items = self.get_recent_extra_targets()
        merged = []
        seen = set()
        for item in new_targets + old_items:
            key = item.lower()
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)
        self.config["recent_extra_targets"] = merged[:60]
        self.refresh_recent_history_listbox()

    def add_targets_to_active_list(self, targets):
        existing = set(item.lower() for item in self.active_extra_targets)
        added = 0
        for target in targets:
            target = clean_target(target)
            if not target:
                continue
            if target.lower() in existing:
                continue
            self.active_extra_targets.append(target)
            existing.add(target.lower())
            added += 1
        if added:
            self.results = []
            self.refresh_target_preview()
            self.set_running_state(False)
        return added

    def add_extra_targets_from_input(self):
        targets = split_extra_targets(self.extra_input_var.get(), self.target_suffix_var.get(), self.custom_suffix_var.get())
        if not targets:
            messagebox.showwarning(self.tr("hint"), self.tr("need_extra"))
            return
        added = self.add_targets_to_active_list(targets)
        self.update_recent_extra_targets(targets)
        self.extra_input_var.set("")
        self.log(self.tr("added_extra").format(count=added))

    def add_selected_recent_targets(self):
        if not hasattr(self, "recent_listbox"):
            return
        selected = list(self.recent_listbox.curselection())
        if not selected:
            messagebox.showwarning(self.tr("hint"), self.tr("select_remove"))
            return
        targets = [self.recent_listbox.get(index) for index in selected]
        added = self.add_targets_to_active_list(targets)
        self.log(self.tr("added_history_targets").format(count=added))

    def clear_recent_extra_targets(self):
        self.config["recent_extra_targets"] = []
        self.refresh_recent_history_listbox()
        self.log(self.tr("cleared_history"))

    def remove_selected_extra_targets(self):
        if self.is_running:
            return
        if not hasattr(self, "tree"):
            return
        selected = list(self.tree.selection())
        if not selected:
            messagebox.showwarning(self.tr("hint"), self.tr("select_target_remove"))
            return

        active_set = set(item.lower() for item in self.active_extra_targets)
        targets_to_remove = []
        for iid in selected:
            result = self.result_by_iid.get(iid)
            if not result:
                continue
            if result.target.lower() in active_set:
                targets_to_remove.append(result.target)

        if not targets_to_remove:
            messagebox.showwarning(self.tr("hint"), self.tr("only_extra_remove"))
            return

        remove_set = set(item.lower() for item in targets_to_remove)
        self.active_extra_targets = [
            item for item in self.active_extra_targets
            if item.lower() not in remove_set
        ]
        self.results = []
        self.refresh_target_preview()
        self.set_running_state(False)
        self.log(self.tr("removed_extra").format(count=len(remove_set)))

    def clear_extra_targets(self):
        if self.is_running:
            return
        count = len(self.active_extra_targets)
        self.active_extra_targets = []
        self.results = []
        self.refresh_target_preview()
        self.set_running_state(False)
        self.log(self.tr("cleared_extra") if count else self.tr("cleared_extra"))

    def get_extra_targets_list(self):
        return list(self.active_extra_targets)

    def get_current_config(self):
        current_extra_targets = self.get_extra_targets_list()
        self.update_recent_extra_targets(current_extra_targets)
        return {
            "router_ip": self.router_var.get().strip(),
            "dns_primary": self.dns1_var.get().strip(),
            "dns_secondary": self.dns2_var.get().strip(),
            "website": self.website_var.get().strip(),
            "extra_targets": current_extra_targets,
            "recent_extra_targets": self.config.get("recent_extra_targets", []),
            "target_suffix": self.target_suffix_var.get().strip(),
            "custom_suffix": self.custom_suffix_var.get().strip(),
            "count": self.count_var.get().strip(),
            "ping_mode": "time" if self.ping_mode_var.get().strip() in {self.tr("mode_time"), "time", "按时间", "By Time"} else "count",
            "duration_seconds": self.duration_var.get().strip(),
            "ping_interval_seconds": self.ping_interval_var.get().strip(),
            "language": self.language,
        }

    def set_running_state(self, running):
        self.is_running = running
        self.start_button.config(state="disabled" if running else "normal")
        self.stop_button.config(state="normal" if running else "disabled")
        state = "disabled" if running or not self.results else "normal"
        self.copy_button.config(state=state)
        self.txt_button.config(state=state)
        self.csv_button.config(state=state)

    def clear_table(self):
        self.result_by_iid.clear()
        self.tree_iid_by_result.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)

    def clear_progress_bars(self):
        self.progress_widgets.clear()
        for child in self.progress_container.winfo_children():
            child.destroy()

    def create_progress_rows(self, results):
        self.clear_progress_bars()
        for row, result in enumerate(results):
            label = ttk.Label(self.progress_container, text=f"{result.name} ({result.target})", width=30)
            label.grid(row=row, column=0, sticky="w", padx=(0, 8), pady=2)
            bar = ttk.Progressbar(self.progress_container, maximum=result.progress_total, mode="determinate")
            bar.grid(row=row, column=1, sticky="ew", padx=(0, 8), pady=2)
            suffix = "s" if result.mode == "time" else ""
            text_var = tk.StringVar(value=f"0 / {result.progress_total}{suffix}")
            text_label = ttk.Label(self.progress_container, textvariable=text_var, width=14)
            text_label.grid(row=row, column=2, sticky="e", pady=2)
            self.progress_widgets[result] = {"bar": bar, "text": text_var}
        self.progress_container.columnconfigure(1, weight=1)

    def add_initial_result_to_table(self, result):
        iid = self.tree.insert(
            "",
            "end",
            values=(result.name, result.target, "N/A", "N/A", "N/A", "N/A", result.status_text(self.language)),
            tags=(STATUS_LEVEL.get(result.status_key(), "warn"),),
        )
        self.result_by_iid[iid] = result
        self.tree_iid_by_result[result] = iid

    def update_result_display(self, result):
        iid = self.tree_iid_by_result.get(result)
        if not iid:
            return
        loss_text = "N/A" if result.loss_rate is None else f"{result.loss_rate}%"
        avg_text = "N/A" if result.avg_ms is None else f"{result.avg_ms} ms"
        max_text = "N/A" if result.max_ms is None else f"{result.max_ms} ms"
        jitter_text = "N/A" if result.jitter_ms is None else f"{result.jitter_ms} ms"
        self.tree.item(
            iid,
            values=(result.name, result.target, loss_text, avg_text, max_text, jitter_text, result.status_text(self.language)),
            tags=(STATUS_LEVEL.get(result.status_key(), "warn"),),
        )
        widgets = self.progress_widgets.get(result)
        if widgets:
            widgets["bar"]["value"] = result.progress_value
            suffix = "s" if result.mode == "time" else ""
            widgets["text"].set(f"{result.progress_value} / {result.progress_total}{suffix}")

    def start_test(self):
        if self.is_running:
            return
        self.refresh_dns_servers(show_log=True, update_widgets=True)
        config = self.get_current_config()
        save_config(config)
        self.config = config

        try:
            count = int(config["count"])
        except ValueError:
            messagebox.showerror(self.tr("error"), self.tr("number_error"))
            return
        if count < 1 or count > MAX_PING_COUNT:
            messagebox.showerror(self.tr("error"), self.tr("count_range_error"))
            return

        try:
            duration_seconds = int(config.get("duration_seconds", "60"))
        except ValueError:
            messagebox.showerror(self.tr("error"), self.tr("duration_error"))
            return
        if duration_seconds < 1 or duration_seconds > MAX_TIME_SECONDS:
            messagebox.showerror(self.tr("error"), self.tr("duration_range_error"))
            return

        try:
            ping_interval_seconds = int(config.get("ping_interval_seconds", "1"))
        except ValueError:
            ping_interval_seconds = 1
        if ping_interval_seconds < 1:
            ping_interval_seconds = 1
        if ping_interval_seconds > 60:
            ping_interval_seconds = 60

        ping_mode = config.get("ping_mode", "count")
        if ping_mode not in ("count", "time"):
            ping_mode = "count"

        targets = make_targets(config)
        if not targets:
            messagebox.showerror(self.tr("error"), self.tr("need_target"))
            return

        self.stop_event.clear()
        if ping_mode == "time":
            self.results = [PingResult(name, target, duration_seconds, mode="time", duration_seconds=duration_seconds) for name, target in targets]
        else:
            self.results = [PingResult(name, target, count, mode="count", duration_seconds=0) for name, target in targets]

        self.ping_interval_seconds = ping_interval_seconds

        self.clear_table()
        for result in self.results:
            self.add_initial_result_to_table(result)
        self.create_progress_rows(self.results)

        total_progress = sum(result.progress_total for result in self.results)
        self.progress["value"] = 0
        self.progress["maximum"] = total_progress
        self.progress_var.set(f"0 / {total_progress}")
        self.diagnosis_var.set(self.tr("running_text"))
        self.set_running_state(True)

        if ping_mode == "time":
            self.log(self.tr("start_log_time").format(total=len(self.results), seconds=duration_seconds, interval=ping_interval_seconds))
        else:
            self.log(self.tr("start_log").format(total=len(self.results), count=count))

        for result in self.results:
            thread = threading.Thread(target=self.run_target_worker, args=(result,), daemon=True)
            thread.start()

        watcher = threading.Thread(target=self.watch_workers, daemon=True)
        watcher.start()

    def stop_test(self):
        if not self.is_running:
            return
        self.stop_event.set()
        self.log(self.tr("stop_requested"))
        self.diagnosis_var.set(self.tr("stopping"))

    def run_target_worker(self, result):
        result.running = True
        self.root.after(0, self.update_result_display, result)
        self.root.after(0, self.log, self.tr("testing").format(name=result.name, target=result.target))

        if result.mode == "time":
            start_time = time.monotonic()
            end_time = start_time + result.duration_seconds
            interval = max(1, int(getattr(self, "ping_interval_seconds", 1)))
            while time.monotonic() < end_time:
                if self.stop_event.is_set():
                    result.stopped = True
                    break
                single = run_ping_once(result.name, result.target)
                with self.result_lock:
                    result.merge_single_result(single)
                    result.progress_value = min(result.progress_total, int(round(time.monotonic() - start_time)))
                self.root.after(0, self.update_result_display, result)
                self.root.after(0, self.update_total_progress)
                if single.error and "DNS resolution failed" in single.error:
                    break

                next_time = time.monotonic() + interval
                while time.monotonic() < next_time and time.monotonic() < end_time:
                    if self.stop_event.is_set():
                        result.stopped = True
                        break
                    with self.result_lock:
                        result.progress_value = min(result.progress_total, int(round(time.monotonic() - start_time)))
                    self.root.after(0, self.update_result_display, result)
                    self.root.after(0, self.update_total_progress)
                    time.sleep(0.1)
                if result.stopped:
                    break

            if not self.stop_event.is_set() and not (result.error and result.received == 0):
                result.progress_value = result.progress_total
        else:
            for _ in range(result.target_count):
                if self.stop_event.is_set():
                    result.stopped = True
                    break
                single = run_ping_once(result.name, result.target)
                with self.result_lock:
                    result.merge_single_result(single)
                self.root.after(0, self.update_result_display, result)
                self.root.after(0, self.update_total_progress)
                if single.error and "DNS resolution failed" in single.error:
                    break

        result.running = False
        if self.stop_event.is_set() and result.progress_value < result.progress_total:
            result.stopped = True
        self.root.after(0, self.update_result_display, result)
        self.root.after(0, self.update_total_progress)

    def watch_workers(self):
        while True:
            if not self.is_running:
                return
            if all((not result.running) and (result.progress_value >= result.progress_total or result.stopped or (result.error and result.received == 0)) for result in self.results):
                break
            threading.Event().wait(0.2)
        append_history(self.results, self.language)
        final_diagnosis = diagnose(self.results, self.language)
        self.root.after(0, self.finish_test, final_diagnosis)

    def update_total_progress(self):
        total_done = sum(result.progress_value for result in self.results)
        total_target = sum(result.progress_total for result in self.results)
        self.progress["value"] = total_done
        self.progress_var.set(f"{total_done} / {total_target}")

    def finish_test(self, final_diagnosis):
        self.set_running_state(False)
        self.update_total_progress()
        self.diagnosis_var.set(final_diagnosis)
        self.log(self.tr("finished"))

        summary = build_completion_summary(self.results, final_diagnosis, self.language)
        title = "检测完成" if self.language == "zh" else "Test Finished"
        messagebox.showinfo(title, summary)

    def build_report(self):
        t = TEXT.get(self.language, TEXT["zh"])
        lines = [
            f"{APP_NAME} v{APP_VERSION} {t['report_title']}",
            f"Author: {AUTHOR}",
            f"{t['created_at']}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"{t['system']}: {platform.system()} {platform.release()}",
            "",
            f"==== {t['result_section']} ====",
        ]
        for result in self.results:
            lines.append(result.to_report_text(self.language))
            lines.append("")
        lines.extend([f"==== {t['diagnosis_section']} ====", self.diagnosis_var.get(), "", f"==== {t['suggestion_section']} ===="])
        for index, suggestion in enumerate(t["suggestions"], start=1):
            lines.append(f"{index}. {suggestion}")
        return "\n".join(lines)

    def copy_report(self):
        if not self.results:
            messagebox.showwarning(self.tr("hint"), self.tr("no_result"))
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(self.build_report())
        self.root.update()
        self.log(self.tr("copied"))
        messagebox.showinfo(self.tr("done"), self.tr("copy_done"))

    def export_txt(self):
        if not self.results:
            messagebox.showwarning(self.tr("hint"), self.tr("no_result"))
            return
        default_name = "NetPulse_Report_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".txt"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=default_name,
        )
        if not file_path:
            return
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(self.build_report())
            self.log(self.tr("txt_exported").format(path=file_path))
            messagebox.showinfo(self.tr("done"), self.tr("txt_done"))
        except Exception as exc:
            messagebox.showerror(self.tr("error"), self.tr("export_failed").format(error=exc))

    def export_csv(self):
        if not self.results:
            messagebox.showwarning(self.tr("hint"), self.tr("no_result"))
            return
        default_name = "NetPulse_Data_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=default_name,
        )
        if not file_path:
            return
        try:
            fieldnames = list(self.results[0].to_row(self.language).keys())
            with open(file_path, "w", encoding="utf-8-sig", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                for result in self.results:
                    writer.writerow(result.to_row(self.language))
            self.log(self.tr("csv_exported").format(path=file_path))
            messagebox.showinfo(self.tr("done"), self.tr("csv_done"))
        except Exception as exc:
            messagebox.showerror(self.tr("error"), self.tr("export_failed").format(error=exc))

    def open_history(self):
        if not HISTORY_FILE.exists():
            messagebox.showinfo(self.tr("history"), self.tr("no_history"))
            return
        try:
            os.startfile(HISTORY_FILE)
        except Exception as exc:
            messagebox.showerror(self.tr("error"), self.tr("open_history_failed").format(error=exc))

    def show_raw_output(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        result = self.result_by_iid.get(selected[0])
        if not result:
            return
        window = tk.Toplevel(self.root)
        window.title(f"{self.tr('raw_output')} - {result.name} ({result.target})")
        window.geometry("780x500")
        text = tk.Text(window, wrap="word")
        text.pack(fill="both", expand=True, padx=10, pady=10)
        content = result.raw_output.strip() or result.error or self.tr("no_raw")
        text.insert("1.0", content)
        text.config(state="disabled")


def main():
    root = tk.Tk()
    NetPulseApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
