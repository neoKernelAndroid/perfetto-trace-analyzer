# Perfetto Trace Analyzer

A powerful tool for analyzing Android Perfetto trace files, focusing on CPU/GPU performance metrics, thread analysis, and SurfaceFlinger composition statistics.

## Features

- **CPU MCPS Analysis**: Calculate CPU cycles and MCPS (Million Cycles Per Second) for different processes
- **GPU Frequency Tracking**: Monitor GPU frequency changes and intervals during trace periods
- **SurfaceFlinger Analysis**: Analyze GPU composition frames and timing
- **Thread Count Monitoring**: Track thread creation and lifecycle
- **Batch Processing**: Analyze multiple trace files automatically
- **Excel Reports**: Generate detailed Excel reports with multiple sheets

## Quick Start

### Prerequisites

- Windows 10/11
- Python 3.8 or higher
- Internet connection (for first-time setup)

### Installation

1. **Extract the release package**
   ```bash
   unzip PerfettoTraceAnalyzer_v1.0_Source.zip
   cd PerfettoTraceAnalyzer_v1.0_Source
   ```

2. **Run installation script**
   ```bash
   INSTALL.bat
   ```
   
   This will:
   - Check Python installation
   - Install required dependencies
   - Download trace_processor.exe
   - Verify the installation

3. **Verify installation**
   ```bash
   verify_installation.bat
   ```

### Basic Usage

#### Single Trace Analysis

```bash
run_cpu_gpu_analysis_quick.bat
```

Edit the batch file to configure:
- `TRACE_FILE`: Path to your trace file
- `START_TAG`: Animation start tag
- `END_TAG`: Animation end tag
- `PROCESS_NAME`: Target process name

#### Batch Analysis

```bash
batch_analyze_all_traces_cpu_gpu.bat
```

Place multiple trace files in subdirectories and analyze them all at once.

### Configuration

Edit `configs/mcps_config.json` to customize:

```json
{
  "cpu_frequencies": {
    "cpu0": [500000, 1000000, 1500000, 2000000],
    "cpu4": [800000, 1200000, 1800000, 2400000]
  },
  "animation_tags": {
    "start": "animation_start",
    "end": "animation_end"
  }
}
```

## Output

The tool generates Excel files with multiple sheets:

- **Summary**: Overall statistics and metrics
- **CPU Frequency Intervals**: CPU frequency changes over time
- **GPU Frequency Intervals**: GPU frequency changes over time
- **Thread Analysis**: Thread count and lifecycle
- **SurfaceFlinger GPU**: GPU composition frame statistics

## Advanced Usage

### Custom Analysis Scripts

- `run_click_to_settings.bat`: Analyze click-to-settings transitions
- `run_openApp_Window.bat`: Analyze app launch performance
- `run_surfaceflinger_analysis.bat`: Dedicated SurfaceFlinger analysis

### Configuration Files

- `configs/mcps_config.json`: CPU/GPU frequency configuration
- `configs/config_open_transition.json`: Transition analysis settings
- `configs/LAUNCHER_APP_SWIPE_TO_RECENTS.json`: Launcher gesture settings

## Troubleshooting

### Permission Denied Error

**Solution 1** (Recommended): Copy trace file to tool directory
```bash
copy "path\to\trace.html" .
```

**Solution 2**: Run batch file as Administrator

### trace_processor.exe Not Found

Run the setup script:
```bash
setup_trace_processor.bat
```

### Python Not Found

Install Python 3.8+ from [python.org](https://www.python.org/downloads/) and add to PATH.

### Missing Dependencies

```bash
install_dependencies.bat
```

Or manually:
```bash
pip install -r requirements.txt
```

## Project Structure

```
PerfettoTraceAnalyzer/
├── modules/                    # Python modules
│   ├── common/                # Common utilities
│   ├── PerfettoSql/          # Perfetto SQL interface
│   ├── services/             # Analysis services
│   └── TraceHtml/            # HTML trace processing
├── configs/                   # Configuration files
├── tools/                     # External tools (trace_processor.exe)
├── output/                    # Analysis output directory
├── logs/                      # Log files
├── run_*.bat                  # Analysis scripts
├── INSTALL.bat               # Installation script
└── README.md                 # This file
```

## Development

### Source Code

This is an open-source project. The source code is available for:
- Customization and extension
- Bug fixes and improvements
- Learning and research

### Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

### Building from Source

The tool can be packaged using PyInstaller:
```bash
pyinstaller PerfettoAnalyzer.spec
```

## License

[Specify your license here - MIT, Apache 2.0, GPL, etc.]

## Support

For issues, questions, or feature requests:
- Open an issue on GitHub
- Contact: [your-email@example.com]

## Changelog

### v1.0 (2026-03-06)
- Initial release
- CPU MCPS analysis
- GPU frequency tracking
- SurfaceFlinger GPU composition analysis
- Batch processing support
- Excel report generation

## Acknowledgments

- Perfetto project for the trace_processor tool
- xlwt library for Excel file generation

