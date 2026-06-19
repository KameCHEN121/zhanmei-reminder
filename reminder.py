#!/usr/bin/env python3
"""
占美茶饮 — 值班提醒脚本（云端版）
通过企业微信群机器人 Webhook 定时推送。
UTC 时间由 GitHub Actions 触发。
"""

import json
import datetime
import sys
import os
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "holidays.json")
WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=6c004cc8-2d42-4a17-970a-5982789b3f98"


def load_config():
    with open(CONFIG_FILE) as f:
        return json.load(f)


def get_day_type():
    """判断今天是 工作日/周末/节假日，考虑调休"""
    config = load_config()
    today = datetime.date.today()
    day_str = today.isoformat()
    weekday = today.weekday()  # 0=Mon ... 6=Sun
    is_weekend = weekday >= 5

    if day_str in config["holidays"]:
        return "holiday"
    elif is_weekend and day_str not in config.get("makeup_workdays", []):
        return "weekend"
    else:
        return "workday"


def push_to_wecom(msg):
    """推送消息到企业微信群"""
    data = json.dumps({
        "msgtype": "text",
        "text": {"content": msg}
    }).encode("utf-8")

    req = urllib.request.Request(
        WEBHOOK_URL,
        data=data,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            if result.get("errcode") == 0:
                print("SUCCESS: 消息推送成功")
                return True
            else:
                print(f"FAILED: {result}")
                sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("用法: python3 reminder.py <morning|noon|check|evening>")
        sys.exit(1)

    mode = sys.argv[1]
    day_type = get_day_type()

    if mode == "morning":
        msg = "⏰ 提醒：请于11:00前提交日常巡检内容。"

    elif mode == "noon":
        count = 3 if day_type in ("weekend", "holiday") else 2
        msg = (
            f"⏰ 午高峰提醒：14:00-16:00为午高峰时段，需要{count}人在店。\n"
            "如有特殊情况需要暂离，请按以下步骤操作：\n"
            "① 填写暂离卡并打卡，将内容截图发到群里；\n"
            '② 在"惠州天益城店"工作群内按模板报备，@店长和@中台同事；\n'
            "③ 获得店长同意后，完成以上步骤再离开。"
        )

    elif mode == "check":
        msg = "⏰ 提醒：今天大件盘点完成了吗？"

    elif mode == "evening":
        msg = (
            "⏰ 晚高峰提醒：19:00-21:00为晚高峰时段，需要2人在店。\n"
            "如有特殊情况需要暂离，请按以下步骤操作：\n"
            "① 填写暂离卡并打卡，将内容截图发到群里；\n"
            '② 在"惠州天益城店"工作群内按模板报备，@店长和@中台同事；\n'
            "③ 获得店长同意后，完成以上步骤再离开。"
        )

    else:
        print(f"未知模式: {mode}")
        sys.exit(1)

    print(f"day_type={day_type}")
    print(msg)
    push_to_wecom(msg)


if __name__ == "__main__":
    main()
