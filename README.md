# RGB Startup Controller

## Project Overview
A sophisticated Python controller for synchronized RGB lighting effects across Asiahorse CosmicQ fans, RGB PSU cables, and GSkill Neo Trident RAM using the OpenRGB API. The controller provides a polished startup animation sequence followed by customizable idle effects.

## Features
- Synchronized RGB control across multiple devices
- Smooth transitions and effects using HSV color space
- Modular effect system for easy customization
- Smart device detection and configuration
- Environment-based configuration
- High-performance rendering engine

## Installation

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -e .  # Install in development mode
   ```

2. **Start OpenRGB Server**
   Make sure the OpenRGB server is running:
   ```bash
   openrgb --server
   ```

3. **Run the Controller**
   ```bash
   rgb-startup-controller
   ```

4. **Configure Environment Variables**  
   Create a `.env` file to customize the behavior:
   ```ini
   # Debug mode
   DEBUG=1
   
   ```

5. **Autostart Configuration**
   - **Linux**: Add to your desktop environment's startup applications
   - **Windows**: Create a scheduled task or add to the Startup folder
## Architecture

The project uses a modular architecture with these key components:

### Core Components
- `StageManager`: High-performance rendering engine that manages effect calculations and device updates
- `RGBController`: Main controller orchestrating the animation sequence
- `Effect`: Base class for all lighting effects
- `ColorSource`: HSV color data provider with advanced gradient support

### Project Structure
```
src/
├── config.py         # Configuration management
├── controller.py     # Main RGB controller
├── gradients.py      # Predefined color gradients
├── main.py          # Entry point
├── stage_manager.py  # Effect rendering engine
└── utils/
    ├── effects/     # Effect implementations
    └── openrgb_helper.py  # OpenRGB integration
```

### Available Effects
- `LiquidFill`: Fluid-like filling animation
- `Chase`: LED chase effect
- `ChaseRamp`: Accelerating chase effect
- `Breathing`: Smooth brightness pulsing
- `FadeIn`/`FadeToBlack`: Smooth transitions
- `Static`: Solid colors

## RGB Hardware Support
- **Asiahorse CosmicQ Fans**: Fully supported with all effects
- **RGB PSU Cables**: Complete integration with synchronized effects
- **GSkill Neo Trident RAM**: Full support with offset animations

## Development

### Adding New Effects
1. Create a new effect class in `src/utils/effects/`
2. Inherit from the `Effect` base class
3. Implement the `_update_brightness()` method
4. Update `__init__.py` if needed

### Color System
The project uses HSV color space for natural-looking transitions and blending:
- Hue: Color selection (0-1.0)
- Saturation: Color intensity (0-1.0)
- Value: Brightness (0-1.0)

## Contributing
1. Fork the repository
2. Create a feature branch
3. Submit a pull request with a clear description of changes

## License
This project is licensed under the MIT License. See the LICENSE file for details.