#!/usr/bin/env python
"""Test script for EONET API endpoint"""
from datasources.eonet_source import EONETSource

def test_eonet():
    print("Testing EONET API...")
    try:
        src = EONETSource(status="open", days=30, limit=10)
        events = src.fetch_and_parse()
        print(f"Success! Found {len(events)} events")
        if events:
            print(f"  First event: {events[0].title}")
            print(f"  Categories: {events[0].categories}")
            print(f"  Status: {events[0].status}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_eonet()

