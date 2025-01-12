from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from telegram.constants import ParseMode
import html
import json
import traceback
import os

import cv2
import numpy as np

from PIL import Image, ImageGrab
from dotenv import load_dotenv

import asyncio

import win32gui
import win32ui
import win32con
import win32api
from ctypes import windll

load_dotenv()

# 设置 .env 文件中的变量
DEVELOPER_CHAT_ID = os.getenv("DEVELOPER_CHAT_ID")
TOKEN = os.getenv("TOKEN")
X = int(os.getenv("X", 10))
Y = int(os.getenv("Y", 90))
WIDTH = int(os.getenv("WIDTH", 50))  # 修正了 "WIGHT" 为 "WIDTH"
HEIGHT = int(os.getenv("HEIGHT", 190))

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """记录错误并发送通知给开发者。"""
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"在处理更新时发生异常\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    # 检查消息长度，限制为 4096 字符
    if len(message) > 4096:
        message = message[:4096]
    # 发送消息
    await context.bot.send_message(
        chat_id=DEVELOPER_CHAT_ID, text=message, parse_mode=ParseMode.HTML
    )

def screenshot(bbox=None):
    """截取屏幕的函数，支持无用户登录状态"""
    try:
        # 首先尝试使用 ImageGrab
        return ImageGrab.grab(bbox=bbox)
    except OSError:
        # 如果 ImageGrab 失败，使用 win32 方法
        left, top, right, bottom = bbox
        width = right - left
        height = bottom - top

        # 获取主显示器的句柄
        hwnd = win32gui.GetDesktopWindow()
        
        # 设置进程DPI感知
        try:
            windll.user32.SetProcessDPIAware()
        except:
            pass

        try:
            # 创建设备上下文和内存设备上下文
            hwndDC = win32gui.GetWindowDC(hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()
            
            # 创建位图对象
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)
            
            # 复制屏幕到内存设备上下文
            result = saveDC.BitBlt(
                (0, 0), 
                (width, height), 
                mfcDC, 
                (left, top), 
                win32con.SRCCOPY
            )
            
            # 转换为PIL Image
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)
            im = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRX', 0, 1)
            
            # 清理资源
            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwndDC)
            
            return im
            
        except Exception as e:
            # 如果出现任何错误，创建一个空白图像
            print(f"Screenshot failed: {str(e)}")
            return Image.new('RGB', (width, height), 'black')

async def monitor_screen(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    # 使用新的screenshot函数替换ImageGrab.grab
    screenshot(bbox=(X, Y, WIDTH, HEIGHT)).save("original_image.png")
    while True:
        await asyncio.sleep(10)
        screenshot(bbox=(X, Y, WIDTH, HEIGHT)).save("current_image.png")
        await asyncio.sleep(2)
        # 加载图片
        loaded_original_image = cv2.imread("original_image.png")
        loaded_current_image = cv2.imread("current_image.png")

        # 转为灰度图像
        gray1 = cv2.cvtColor(loaded_original_image, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(loaded_current_image, cv2.COLOR_BGR2GRAY)
        
        # 计算差异
        diff = cv2.absdiff(gray1, gray2)

        # 阈值处理以找到差异区域
        _, threshold = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)

        # 腐蚀和膨胀以去除噪声
        kernel = np.ones((3, 3), np.uint8)
        threshold = cv2.erode(threshold, kernel, iterations=2)
        threshold = cv2.dilate(threshold, kernel, iterations=2)

        # 查找轮廓
        contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 如果检测到差异
        if contours:
            # 绘制矩形框并保存差异图像
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(loaded_current_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.imwrite('diff_region.jpg', loaded_current_image)
            
            # 发送照片
            with open("diff_region.jpg", 'rb') as photo:
                await context.bot.send_photo(chat_id=chat_id, photo=photo)
            # 更新原始图像
            screenshot(bbox=(X, Y, WIDTH, HEIGHT)).save("original_image.png")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="屏幕监控已启动。")
    chat_id = update.effective_chat.id
    # 启动监控任务
    context.application.create_task(monitor_screen(context, chat_id))

async def now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 使用新的screenshot函数替换ImageGrab.grab
    initial_image = screenshot(bbox=(X, Y, WIDTH, HEIGHT))
    initial_image.save("Now_Image.png")
    with open("Now_Image.png", 'rb') as photo:
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo)

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()

    # 添加错误处理器
    application.add_error_handler(error_handler)

    # 添加命令处理器
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('now', now))

    application.run_polling()