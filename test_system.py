#!/usr/bin/env python3
"""
SkyWatch System Test Script
Tests basic functionality without requiring camera connection
"""
import sys
import importlib.util

def test_imports():
    """Test if all required packages are installed"""
    print("Testing package imports...")
    required_packages = {
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn',
        'cv2': 'opencv-python',
        'numpy': 'numpy',
        'PIL': 'Pillow',
        'yaml': 'PyYAML',
        'astral': 'astral',
    }
    
    failed = []
    for module, package in required_packages.items():
        try:
            __import__(module)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} - NOT INSTALLED")
            failed.append(package)
    
    if failed:
        print(f"\nMissing packages: {', '.join(failed)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("\n✓ All packages installed\n")
    return True

def test_config():
    """Test configuration loading"""
    print("Testing configuration...")
    try:
        from app.config import load_config
        settings = load_config()
        print(f"  ✓ Configuration loaded")
        print(f"  ✓ RTSP URL: {settings.camera.rtsp_url[:30]}...")
        print(f"  ✓ Storage: {settings.storage.base_path}")
        print(f"  ✓ Port: {settings.server.port}")
        print(f"  ✓ Timelapse: {'enabled' if settings.timelapse.enabled else 'disabled'}")
        print(f"  ✓ Solargraph: {'enabled' if settings.solargraph.enabled else 'disabled'}")
        print(f"  ✓ Lunar: {'enabled' if settings.lunar.enabled else 'disabled'}")
        print(f"  ✓ Motion: {'enabled' if settings.motion.enabled else 'disabled'}")
        print("\n✓ Configuration valid\n")
        return True
    except Exception as e:
        print(f"  ✗ Configuration error: {e}")
        return False

def test_storage():
    """Test storage directories"""
    print("Testing storage...")
    try:
        from pathlib import Path
        from app.config import load_config
        settings = load_config()
        
        base_path = Path(settings.storage.base_path)
        if not base_path.exists():
            base_path.mkdir(parents=True, exist_ok=True)
            print(f"  ✓ Created storage directory: {base_path}")
        else:
            print(f"  ✓ Storage directory exists: {base_path}")
        
        # Test write permissions
        test_file = base_path / ".test"
        test_file.write_text("test")
        test_file.unlink()
        print(f"  ✓ Storage is writable")
        
        print("\n✓ Storage ready\n")
        return True
    except Exception as e:
        print(f"  ✗ Storage error: {e}")
        return False

def test_modules():
    """Test SkyWatch modules"""
    print("Testing SkyWatch modules...")
    try:
        from app.camera import CameraManager
        from app.services.timelapse import TimelapseService
        from app.services.solargraph import SolargraphService
        from app.services.lunar import LunarService
        from app.services.motion import MotionDetectionService
        
        print(f"  ✓ Camera module")
        print(f"  ✓ Timelapse service")
        print(f"  ✓ Solargraph service")
        print(f"  ✓ Lunar service")
        print(f"  ✓ Motion detection service")
        
        print("\n✓ All modules loaded\n")
        return True
    except Exception as e:
        print(f"  ✗ Module error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("SkyWatch System Test")
    print("=" * 50)
    print()
    
    tests = [
        ("Package Imports", test_imports),
        ("Configuration", test_config),
        ("Storage", test_storage),
        ("Modules", test_modules),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ {name} failed with exception: {e}")
            results.append((name, False))
    
    print("=" * 50)
    print("Test Results")
    print("=" * 50)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} {name}")
    
    print()
    
    if all(r[1] for r in results):
        print("✓ All tests passed! SkyWatch is ready to run.")
        print()
        print("Next steps:")
        print("  1. Edit config.yaml or config.local.yaml with your camera URL")
        print("  2. Run: ./start.sh")
        print("  3. Open browser to: http://localhost:8080")
        return 0
    else:
        print("✗ Some tests failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
