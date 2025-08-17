"""
Chess Analysis with Visualizations Launcher
Easy-to-use script to run complete chess analysis with research visualizations
"""

import subprocess
import sys
import os

def check_dependencies():
    """Check if all required packages are installed"""
    
    required_packages = [
        'matplotlib', 'seaborn', 'pandas', 'numpy', 
        'networkx', 'plotly', 'chess', 'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nInstall with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ All required packages are installed")
    return True

def run_analysis_with_visualizations(username=None, platform=None):
    """Run the complete chess analysis with visualizations"""
    
    print("🏁 Starting Complete Chess Analysis with Visualizations")
    print("=" * 60)
    
    # Check dependencies first
    if not check_dependencies():
        print("Please install missing packages before continuing.")
        return False
    
    # Prepare command
    cmd = [sys.executable, "chess_analyzer_complete.py"]
    
    if username:
        cmd.append(username)
    if platform:
        cmd.append(platform)
    
    try:
        # Run the analysis
        print(f"🔍 Running analysis command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=False, text=True)
        
        if result.returncode == 0:
            print("\n✅ Analysis completed successfully!")
            print("📁 Check the 'visualizations' folder for generated charts")
            return True
        else:
            print(f"\n❌ Analysis failed with return code: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ Error running analysis: {e}")
        return False

def main():
    """Main launcher function"""
    
    print("🎯 Chess Analysis & Research Visualization Launcher")
    print("=" * 55)
    
    # Get user input
    if len(sys.argv) > 2:
        username = sys.argv[1]
        platform = sys.argv[2]
        print(f"Using command line arguments: {username} on {platform}")
    elif len(sys.argv) > 1:
        username = sys.argv[1]
        platform = None
        print(f"Using username: {username}")
    else:
        print("You can run this in two ways:")
        print("1. Interactive mode (will prompt for input)")
        print("2. Command line: python launch_analysis.py <username> <platform>")
        print("\nPlatform options: chess.com or lichess")
        print("\nStarting interactive mode...")
        username = None
        platform = None
    
    # Run the analysis
    success = run_analysis_with_visualizations(username, platform)
    
    if success:
        print("\n🎉 COMPLETE SUCCESS! 🎉")
        print("=" * 30)
        print("Your analysis is ready with:")
        print("📊 Performance heatmaps")
        print("📈 Tactical error analysis")
        print("🔍 Experience vs performance plots")
        print("🕸️ Strategy network graphs")
        print("📊 Weakness radar charts")
        print("🌟 Interactive 3D visualizations")
        print("📋 Research paper template")
        print("\n📁 All files saved in 'visualizations' folder")
        print("📄 See 'visualization_report.md' for descriptions")
    else:
        print("\n❌ Analysis incomplete. Check error messages above.")

if __name__ == "__main__":
    main()
