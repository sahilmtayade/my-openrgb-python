# my-openrgb-python

## Project Overview
This project provides a Python script to control the RGB lighting of Asiahorse CosmicQ fans and RGB PSU cables using the OpenRGB API. The script is designed to run on startup for a one time effect and then run continuously.

## Features
- Detects connected RGB devices.
- Manages LED configurations for Asiahorse CosmicQ fans and RGB PSU cables and GSkill Neo Trident Ram.
- Has startup animation and infinite animations.

## Setup Instructions
1. **Clone the Repository**
   ```bash
   git clone https://github.com/sahilmtayade/my-openrgb-python.git
   cd my-openrgb-python
   ```

2. **Install Dependencies**
   Ensure you have Python installed, then run:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Script**
   You can run the script manually using:
   ```bash
   python src/main.py
   ```
   To run the script on Windows startup, you can create a scheduled task or place a shortcut in the Startup folder.

## Usage Guidelines
- Modify the `src/main.py` file to set your desired lighting effects and colors.
- Use the `src/utils/openrgb_helper.py` for additional functionality and customization.

## RGB Configurations
- The Asiahorse CosmicQ fans can be configured for various lighting effects such as static colors, breathing effects, and color cycling.
- RGB PSU cables can also be customized to match the fans or set to different effects.

## Contributing
Feel free to submit issues or pull requests for improvements and additional features. 

## License
This project is licensed under the MIT License. See the LICENSE file for more details.