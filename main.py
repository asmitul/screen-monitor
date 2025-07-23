import logging
import os
import time
import json
import traceback
import asyncio
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import ImageGrab, Image
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, 
    ContextTypes, 
    CommandHandler, 
    MessageHandler,
    filters
)
from telegram.constants import ParseMode
import html

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
# ignor httpx warning
logging.getLogger("httpx").setLevel(logging.WARNING)

# Configuration
class Config:
    DEVELOPER_CHAT_ID = os.getenv("DEVELOPER_CHAT_ID")
    TOKEN = os.getenv("TOKEN")
    X = int(os.getenv("X", 10))
    Y = int(os.getenv("Y", 90))
    WIDTH = int(os.getenv("WIDTH", 50))  # Fixed typo from WIGHT
    HEIGHT = int(os.getenv("HEIGHT", 190))
    SCREENSHOT_INTERVAL = int(os.getenv("SCREENSHOT_INTERVAL", 10))  # seconds
    DIFFERENCE_THRESHOLD = int(os.getenv("DIFFERENCE_THRESHOLD", 30))
    MIN_CONTOUR_AREA = int(os.getenv("MIN_CONTOUR_AREA", 100))  # minimum area to consider as change
    
    # File paths
    ORIGINAL_IMAGE_PATH = "original_image.png"
    CURRENT_IMAGE_PATH = "current_image.png"
    DIFF_IMAGE_PATH = "diff_region.jpg"
    NOW_IMAGE_PATH = "Now_Image.png"
    FULL_SCREEN_CHANGE_PATH = "full_screen_change.png"  # 新增：变化时的大截图路径

    @classmethod
    def validate(cls) -> bool:
        """Validate configuration"""
        if not cls.TOKEN:
            logger.error("TOKEN environment variable is required")
            return False
        if not cls.DEVELOPER_CHAT_ID:
            logger.error("DEVELOPER_CHAT_ID environment variable is required")
            return False
        if cls.WIDTH <= 0 or cls.HEIGHT <= 0:
            logger.error("WIDTH and HEIGHT must be positive values")
            return False
        return True

class ScreenMonitor:
    def __init__(self):
        self.is_monitoring = False
        self.monitoring_task: Optional[asyncio.Task] = None
        
    async def start_monitoring(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start screen monitoring"""
        if self.is_monitoring:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text="Screen monitoring is already running."
            )
            return
            
        self.is_monitoring = True
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="Screen monitoring started. Use /stop to stop monitoring."
        )
        
        # Create initial screenshot
        try:
            self._take_screenshot(Config.ORIGINAL_IMAGE_PATH)
            logger.info("Initial screenshot saved")
        except Exception as e:
            logger.error(f"Failed to take initial screenshot: {e}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Failed to take initial screenshot. Please try again."
            )
            self.is_monitoring = False
            return
        
        # Start monitoring task
        self.monitoring_task = asyncio.create_task(
            self._monitor_loop(update, context)
        )
        
    async def stop_monitoring(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Stop screen monitoring"""
        if not self.is_monitoring:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Screen monitoring is not running."
            )
            return
            
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
                
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Screen monitoring stopped."
        )
        
    def _take_screenshot(self, filepath: str) -> None:
        """Take a screenshot and save it"""
        try:
            screenshot = ImageGrab.grab(bbox=(Config.X, Config.Y, Config.X + Config.WIDTH, Config.Y + Config.HEIGHT))
            screenshot.save(filepath)
            logger.debug(f"Screenshot saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            raise
            
    def _take_full_screenshot(self, filepath: str) -> None:
        """Take a full screen screenshot and save it"""
        try:
            # 拍摄更大的区域，包含监控区域周围的更多内容
            # 扩展监控区域，使其更大
            expanded_x = max(0, Config.X - 200)  # 向左扩展200像素
            expanded_y = max(0, Config.Y - 200)  # 向上扩展200像素
            expanded_width = Config.WIDTH + 400   # 宽度增加400像素
            expanded_height = Config.HEIGHT + 400 # 高度增加400像素
            
            screenshot = ImageGrab.grab(bbox=(expanded_x, expanded_y, expanded_x + expanded_width, expanded_y + expanded_height))
            screenshot.save(filepath)
            logger.debug(f"Full screenshot saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to take full screenshot: {e}")
            raise
            
    async def _monitor_loop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Wait for interval
                await asyncio.sleep(Config.SCREENSHOT_INTERVAL)
                
                if not self.is_monitoring:
                    break
                    
                # Take current screenshot
                self._take_screenshot(Config.CURRENT_IMAGE_PATH)
                
                # Compare images
                if await self._detect_changes():
                    # Send notification with diff image
                    await self._send_diff_notification(update, context)
                    # Update original image
                    self._take_screenshot(Config.ORIGINAL_IMAGE_PATH)
                    
            except asyncio.CancelledError:
                logger.info("Monitoring loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"Error during monitoring: {str(e)}"
                )
                
    async def _detect_changes(self) -> bool:
        """Detect changes between original and current images"""
        try:
            # Load images
            original = cv2.imread(Config.ORIGINAL_IMAGE_PATH)
            current = cv2.imread(Config.CURRENT_IMAGE_PATH)
            
            if original is None or current is None:
                logger.error("Failed to load images for comparison")
                return False
                
            # Convert to grayscale
            gray_original = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
            gray_current = cv2.cvtColor(current, cv2.COLOR_BGR2GRAY)
            
            # Calculate difference
            diff = cv2.absdiff(gray_original, gray_current)
            
            # Apply threshold
            _, threshold = cv2.threshold(diff, Config.DIFFERENCE_THRESHOLD, 255, cv2.THRESH_BINARY)
            
            # Morphological operations to reduce noise
            kernel = np.ones((3, 3), np.uint8)
            threshold = cv2.erode(threshold, kernel, iterations=2)
            threshold = cv2.dilate(threshold, kernel, iterations=2)
            
            # Find contours
            contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter contours by area
            significant_changes = [
                contour for contour in contours 
                if cv2.contourArea(contour) > Config.MIN_CONTOUR_AREA
            ]
            
            if significant_changes:
                # Draw rectangles around changes
                result_image = current.copy()
                for contour in significant_changes:
                    x, y, w, h = cv2.boundingRect(contour)
                    cv2.rectangle(result_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                # Save diff image
                cv2.imwrite(Config.DIFF_IMAGE_PATH, result_image)
                logger.info(f"Detected {len(significant_changes)} significant changes")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error detecting changes: {e}")
            return False
            
    async def _send_diff_notification(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send difference notification with image"""
        try:
            # 拍摄更大的截图
            self._take_full_screenshot(Config.FULL_SCREEN_CHANGE_PATH)
            
            with open(Config.FULL_SCREEN_CHANGE_PATH, 'rb') as photo:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=photo,
                    caption=f"Screen changes detected at {time.strftime('%Y-%m-%d %H:%M:%S')}"
                )
        except Exception as e:
            logger.error(f"Failed to send diff notification: {e}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Screen changes detected but failed to send image: {str(e)}"
            )

# Global monitor instance
screen_monitor = ScreenMonitor()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await screen_monitor.start_monitoring(update, context)

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stop command"""
    await screen_monitor.stop_monitoring(update, context)

async def now_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /now command - take immediate screenshot"""
    try:
        screen_monitor._take_screenshot(Config.NOW_IMAGE_PATH)
        with open(Config.NOW_IMAGE_PATH, 'rb') as photo:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=photo,
                caption=f"Current screen at {time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
    except Exception as e:
        logger.error(f"Failed to take immediate screenshot: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Failed to take screenshot: {str(e)}"
        )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command - show monitoring status"""
    status = "running" if screen_monitor.is_monitoring else "stopped"
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Screen monitoring status: {status}"
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    logger.error("Exception while handling an update:", exc_info=context.error)

    # Build error message
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    # Truncate message if too long
    if len(message) > 4096:
        message = message[:4096]
        
    # Send error message
    try:
        await context.bot.send_message(
            chat_id=Config.DEVELOPER_CHAT_ID, 
            text=message, 
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Failed to send error message: {e}")

def main():
    """Main function"""
    # Validate configuration
    if not Config.validate():
        logger.error("Configuration validation failed")
        return
        
    # Create application
    application = ApplicationBuilder().token(Config.TOKEN).build()
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Add command handlers
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('stop', stop_command))
    application.add_handler(CommandHandler('now', now_command))
    application.add_handler(CommandHandler('status', status_command))
    
    # Add help handler
    help_text = """
Available commands:
/start - Start screen monitoring
/stop - Stop screen monitoring  
/now - Take immediate screenshot
/status - Show monitoring status
    """
    application.add_handler(CommandHandler('help', lambda u, c: c.bot.send_message(u.effective_chat.id, help_text)))
    
    logger.info("Screen monitoring bot started")
    application.run_polling()

if __name__ == '__main__':
    main()