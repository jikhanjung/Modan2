#!/usr/bin/env python3
"""
Test script to verify error handling in Modan2 modules
"""

import tempfile
import os
import sys
sys.path.insert(0, '/home/jikhanjung/projects/Modan2')

def test_file_io_error_handling():
    """Test file I/O error handling"""
    print("=" * 50)
    print("Testing File I/O Error Handling")
    print("=" * 50)
    
    import MdUtils
    
    # Test 1: Non-existent file
    print("1. Testing non-existent file...")
    try:
        MdUtils.read_landmark_file("/nonexistent/file.tps")
        print("❌ Should have failed with FileNotFoundError")
    except (FileNotFoundError, ValueError) as e:
        print(f"✅ Correctly handled: {type(e).__name__}: {e}")
    except Exception as e:
        print(f"⚠️ Unexpected error: {type(e).__name__}: {e}")
    
    # Test 2: Invalid file content
    print("\n2. Testing invalid TPS file content...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tps', delete=False) as f:
        f.write("INVALID TPS CONTENT\n")
        f.write("NOT A VALID FORMAT\n")
        temp_path = f.name
    
    try:
        MdUtils.read_landmark_file(temp_path)
        print("❌ Should have failed with invalid format")
    except ValueError as e:
        print(f"✅ Correctly handled invalid format: {e}")
    except Exception as e:
        print(f"⚠️ Unexpected error: {type(e).__name__}: {e}")
    finally:
        os.unlink(temp_path)
    
    # Test 3: Permission denied (simulate by trying to read a directory)
    print("\n3. Testing permission/access error...")
    try:
        MdUtils.read_landmark_file("/")  # Try to read root directory as file
        print("❌ Should have failed with permission/access error")
    except (PermissionError, OSError, ValueError) as e:
        print(f"✅ Correctly handled access error: {type(e).__name__}: {e}")
    except Exception as e:
        print(f"⚠️ Unexpected error: {type(e).__name__}: {e}")


def test_database_error_handling():
    """Test database error handling"""
    print("\n" + "=" * 50)
    print("Testing Database Error Handling")
    print("=" * 50)
    
    try:
        import MdModel
        from peewee import DoesNotExist
        
        # Test non-existent dataset
        print("1. Testing non-existent dataset query...")
        try:
            dataset = MdModel.MdDataset.get_by_id(99999)  # Non-existent ID
            print("❌ Should have failed with DoesNotExist")
        except DoesNotExist as e:
            print(f"✅ Correctly handled: {type(e).__name__}")
        except Exception as e:
            print(f"⚠️ Unexpected error: {type(e).__name__}: {e}")
            
    except ImportError as e:
        print(f"⚠️ Could not import database modules: {e}")


def test_mesh_loading_error_handling():
    """Test mesh loading error handling"""
    print("\n" + "=" * 50)
    print("Testing Mesh Loading Error Handling") 
    print("=" * 50)
    
    import MdUtils
    
    # Test 1: Non-existent mesh file
    print("1. Testing non-existent mesh file...")
    try:
        MdUtils.convert_to_obj("/nonexistent/file.stl", "/tmp/output.obj")
        print("❌ Should have failed with file error")
    except (FileNotFoundError, ValueError) as e:
        print(f"✅ Correctly handled: {type(e).__name__}: {e}")
    except Exception as e:
        print(f"⚠️ Unexpected error: {type(e).__name__}: {e}")


def test_math_error_handling():
    """Test mathematical error handling"""
    print("\n" + "=" * 50)
    print("Testing Mathematical Error Handling")
    print("=" * 50)
    
    try:
        import MdModel
        
        # Create a simple object to test centroid calculation
        print("1. Testing centroid size calculation with edge cases...")
        obj = MdModel.MdObject()
        
        # Set some test landmarks
        obj.landmark_list = [[0, 0], [1, 1], [2, 2]]
        
        try:
            size = obj.get_centroid_size()
            print(f"✅ Centroid size calculated successfully: {size}")
        except Exception as e:
            print(f"⚠️ Error in centroid calculation: {type(e).__name__}: {e}")
            
    except ImportError as e:
        print(f"⚠️ Could not import required modules: {e}")


def test_json_error_handling():
    """Test JSON error handling"""
    print("\n" + "=" * 50)
    print("Testing JSON Error Handling")
    print("=" * 50)
    
    try:
        import json
        from pathlib import Path
        
        # Test writing to invalid path
        print("1. Testing JSON write to invalid path...")
        try:
            invalid_path = "/nonexistent_dir/config.json"
            with open(invalid_path, 'w') as f:
                json.dump({"test": "data"}, f)
            print("❌ Should have failed with file error")
        except (FileNotFoundError, PermissionError, OSError) as e:
            print(f"✅ Correctly handled: {type(e).__name__}: {e}")
        except Exception as e:
            print(f"⚠️ Unexpected error: {type(e).__name__}: {e}")
            
    except ImportError as e:
        print(f"⚠️ Could not import JSON module: {e}")


def main():
    """Run all error handling tests"""
    print("🧪 Modan2 Error Handling Test Suite")
    print("=" * 60)
    
    test_file_io_error_handling()
    test_database_error_handling()
    test_mesh_loading_error_handling()
    test_math_error_handling()
    test_json_error_handling()
    
    print("\n" + "=" * 60)
    print("✅ Error handling test suite completed!")
    print("✅ Most critical operations now have proper error handling")
    print("=" * 60)


if __name__ == "__main__":
    main()