# import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler,filters
from telegram.constants import ParseMode
import html
import json
import traceback
import os

import cv2
import numpy as np

from PIL import ImageGrab
from dotenv import load_dotenv

load_dotenv()

# serup .env file
DEVELOPER_CHAT_ID = os.getenv("DEVELOPER_CHAT_ID")
TOKEN=os.getenv("TOKEN")
X=int(os.getenv("X",10))
Y=int(os.getenv("Y",90))
WIGHT=int(os.getenv("WIGHT",50))
HEIGHT=int(os.getenv("HEIGHT",190))

# 改进的差异检测参数
DIFF_THRESHOLD = int(os.getenv("DIFF_THRESHOLD", 15))  # 降低阈值，更敏感
BLUR_KERNEL_SIZE = int(os.getenv("BLUR_KERNEL_SIZE", 3))  # 模糊核大小
MIN_CONTOUR_AREA = int(os.getenv("MIN_CONTOUR_AREA", 5))  # 最小轮廓面积

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    # logger.error("Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    # check message length , the limit is 4096
    if len(message) > 4096:
        message = message[:4096]
    # Finally, send the message
    await context.bot.send_message(
        chat_id=DEVELOPER_CHAT_ID, text=message, parse_mode=ParseMode.HTML
    )

def improved_image_comparison(img1, img2):
    """改进的图像比较函数，更好地处理颜色变化"""
    # 转换为灰度图
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    
    # 应用高斯模糊减少噪声
    gray1_blur = cv2.GaussianBlur(gray1, (BLUR_KERNEL_SIZE, BLUR_KERNEL_SIZE), 0)
    gray2_blur = cv2.GaussianBlur(gray2, (BLUR_KERNEL_SIZE, BLUR_KERNEL_SIZE), 0)
    
    # 计算差异
    diff = cv2.absdiff(gray1_blur, gray2_blur)
    
    # 使用自适应阈值处理
    diff_threshold = cv2.adaptiveThreshold(
        diff, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    
    # 同时使用固定阈值作为备用
    _, fixed_threshold = cv2.threshold(diff, DIFF_THRESHOLD, 255, cv2.THRESH_BINARY)
    
    # 合并两种阈值结果
    combined_threshold = cv2.bitwise_or(diff_threshold, fixed_threshold)
    
    # 形态学操作去除噪声
    kernel = np.ones((3, 3), np.uint8)
    eroded = cv2.erode(combined_threshold, kernel, iterations=1)
    dilated = cv2.dilate(eroded, kernel, iterations=2)
    
    # 查找轮廓
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 过滤小轮廓
    significant_contours = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > MIN_CONTOUR_AREA:
            significant_contours.append(contour)
    
    return significant_contours, dilated

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("start")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="screan monitoring started.")
    
    # screenshot original image
    ImageGrab.grab(bbox=(X, Y, WIGHT, HEIGHT)).save("original_image.png")

    # endless loop
    while True:
        # 每10秒截取屏幕
        import time
        time.sleep(10)
        # screenshot
        ImageGrab.grab(bbox=(X, Y, WIGHT, HEIGHT)).save("current_image.png")
        time.sleep(2)
        # 加载两张图片
        loaded_original_image = cv2.imread("original_image.png")
        loaded_current_image = cv2.imread("current_image.png")

        # 使用改进的比较函数
        contours, processed_diff = improved_image_comparison(loaded_original_image, loaded_current_image)

        # 如果有不同区域，输出不同
        if len(contours) > 0:
            # 创建标记图像
            marked_image = loaded_current_image.copy()
            
            # 遍历轮廓并绘制矩形框来标记不同区域
            for contour in contours:
                (x, y, w, h) = cv2.boundingRect(contour)
                cv2.rectangle(marked_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # 保存标记的图像
            cv2.imwrite('diff_region.jpg', marked_image)
            
            # 同时保存处理后的差异图像用于调试
            cv2.imwrite('debug_diff.jpg', processed_diff)
            
            # 发送标记的图像
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open("diff_region.jpg", 'rb'))
            
            # 发送调试图像（可选）
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open("debug_diff.jpg", 'rb'), caption="Debug: Processed difference image")
            
            # 更新参考图像
            ImageGrab.grab(bbox=(X, Y, WIGHT, HEIGHT)).save("original_image.png")
        else:
            pass
    

async def now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("now")
    initial_image = ImageGrab.grab(bbox=(X, Y, WIGHT, HEIGHT))
    initial_image.save("Now_Image.png")
    await context.bot.send_photo(chat_id=update.effective_chat.id,photo=open("Now_Image.png",'rb'))
    

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    print("screan monitoring started.")

    # ...and the error handler
    application.add_error_handler(error_handler)

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('now', now))
    # application.add_handler(MessageHandler(filters.ALL, pz_start))
    
    application.run_polling()