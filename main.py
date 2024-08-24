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
Y=int(os.getenv("Y",120))
WIGHT=int(os.getenv("WIGHT",50))
HEIGHT=int(os.getenv("HEIGHT",190))


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

        # 将两张图片转换为灰度图像
        gray1 = cv2.cvtColor(loaded_original_image, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(loaded_current_image, cv2.COLOR_BGR2GRAY)
        
        # 计算两张灰度图像的差异
        diff = cv2.absdiff(gray1, gray2)

        
        # 对差异图像进行阈值处理，以便找到明显的不同区域
        _, threshold = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)

        # 对阈值图像进行腐蚀和膨胀操作，以去除噪声并连接相邻的不同区域
        kernel = np.ones((3, 3), np.uint8)
        threshold = cv2.erode(threshold, kernel, iterations=2)
        threshold = cv2.dilate(threshold, kernel, iterations=2)

        # 查找不同区域的轮廓
        contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 如果有不同区域，输出不同
        if len(contours) > 0:
            # 遍历轮廓并绘制矩形框来标记不同区域，并保存截图
            for contour in contours:
                    (x, y, w, h) = cv2.boundingRect(contour)
                    cv2.rectangle(loaded_current_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.imwrite('diff_region.jpg', loaded_current_image)
            
            await context.bot.send_photo(chat_id=update.effective_chat.id,photo=open("diff_region.jpg",'rb'))
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