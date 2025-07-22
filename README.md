# Screen Monitor Telegram Bot

A Python-based Telegram bot that monitors screen changes in a specified region and sends notifications when changes are detected.

## Features

- **Real-time monitoring**: Continuously monitors a specified screen region
- **Change detection**: Uses computer vision to detect significant changes
- **Telegram integration**: Sends notifications with annotated images
- **Configurable**: Customizable monitoring area, intervals, and sensitivity
- **Async operation**: Non-blocking monitoring using asyncio
- **Error handling**: Comprehensive error handling and logging

## Commands

- `/start` - Start screen monitoring
- `/stop` - Stop screen monitoring
- `/now` - Take immediate screenshot
- `/status` - Show monitoring status
- `/help` - Show available commands

## Installation

### Prerequisites

- Python 3.8 or higher
- Telegram Bot Token (get from [@BotFather](https://t.me/botfather))

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd screen-monitor
   ```

2. **Create virtual environment**
   ```bash
   # On Windows
   python -m venv venv
   venv\Scripts\activate
   
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create .env file**
   ```bash
   # Create .env file with your configuration
   TOKEN=your_telegram_bot_token
   DEVELOPER_CHAT_ID=your_chat_id
   X=10
   Y=90
   WIDTH=50
   HEIGHT=190
   SCREENSHOT_INTERVAL=10
   DIFFERENCE_THRESHOLD=30
   MIN_CONTOUR_AREA=100
   ```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `TOKEN` | Telegram Bot Token | - | Yes |
| `DEVELOPER_CHAT_ID` | Chat ID for error notifications | - | Yes |
| `X` | X coordinate of monitoring area | 10 | No |
| `Y` | Y coordinate of monitoring area | 90 | No |
| `WIDTH` | Width of monitoring area | 50 | No |
| `HEIGHT` | Height of monitoring area | 190 | No |
| `SCREENSHOT_INTERVAL` | Screenshot interval in seconds | 10 | No |
| `DIFFERENCE_THRESHOLD` | Threshold for change detection (0-255) | 30 | No |
| `MIN_CONTOUR_AREA` | Minimum area to consider as change | 100 | No |

### Getting Your Chat ID

1. Start a conversation with your bot
2. Send any message to the bot
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Find your `chat_id` in the response

## Usage

1. **Start the bot**
   ```bash
   python main.py
   ```

2. **In Telegram**
   - Send `/start` to begin monitoring
   - Send `/stop` to stop monitoring
   - Send `/now` for immediate screenshot
   - Send `/status` to check monitoring status

## How It Works

1. **Initialization**: Takes a baseline screenshot of the specified area
2. **Monitoring Loop**: 
   - Takes screenshots at specified intervals
   - Compares current screenshot with baseline
   - Detects changes using computer vision algorithms
3. **Change Detection**:
   - Converts images to grayscale
   - Calculates absolute difference
   - Applies threshold filtering
   - Uses morphological operations to reduce noise
   - Finds contours of changed regions
4. **Notification**: Sends annotated image with highlighted changes

## Building Executable

### Using PyInstaller

```bash
pip install pyinstaller
pyinstaller --onefile --hidden-import=PIL._tkinter_finder main.py
```

### Using cx_Freeze

```bash
pip install cx_Freeze
python setup.py build
```

## Troubleshooting

### Common Issues

1. **"Failed to take screenshot"**
   - Ensure you have proper permissions
   - Check if the specified coordinates are valid
   - On Linux, ensure X11 forwarding is enabled

2. **"Configuration validation failed"**
   - Check your `.env` file
   - Ensure all required variables are set
   - Verify your bot token is correct

3. **"Failed to send diff notification"**
   - Check your internet connection
   - Verify your chat ID is correct
   - Ensure the bot has permission to send photos

### Logs

The bot provides detailed logging. Check the console output for:
- Configuration validation
- Screenshot operations
- Change detection events
- Error messages

## Security Considerations

- Keep your bot token secure
- Don't commit `.env` files to version control
- Consider using environment variables in production
- Monitor bot usage to prevent abuse

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs for error messages
3. Create an issue with detailed information