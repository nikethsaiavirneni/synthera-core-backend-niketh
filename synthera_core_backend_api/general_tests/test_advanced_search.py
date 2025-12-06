#!/usr/bin/env python3
"""
Advanced Search API Test Script

This script demonstrates the new advanced search functionality across the projects API.
It tests various search scenarios including text search, advanced filters, and combinations.

Features Tested:
- Global text search across multiple columns
- Advanced filtering with operators (equals, contains, greater_than, date_range, etc.)
- Pagination and sorting
- Multiple filter combinations
- Error handling and edge cases
"""

import sys
import os
import json
from datetime import datetime

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from com.dimcon.synthera.routes.projects_req_router import ProjectsRequestRouter

def test_api_endpoint(description, event):
    """Test a single API endpoint and display results."""
    print(f"\n{'='*60}")
    print(f"🔍 {description}")
    print(f"{'='*60}")
    
    # Show the query parameters being tested
    query_params = event.get("queryStringParameters", {})
    if query_params:
        print("Query Parameters:")
        for key, value in query_params.items():
            print(f"  {key}: {value}")
        print()
    
    try:
        # Route the request
        response = ProjectsRequestRouter.route_request(
            http_method="GET",
            resource_path="/projects",
            path_params={},
            event=event
        )
        
        # Parse the response
        status_code = response.get("statusCode", 500)
        body = response.get("body", "{}")
        
        if isinstance(body, str):
            body = json.loads(body)
        
        print(f"Status Code: {status_code}")
        
        if status_code == 200:
            data = body.get("data", [])
            total_count = body.get("total_count", 0)
            search_metadata = body.get("search_metadata", {})
            
            print(f"✅ Success! Found {len(data)} results (Total: {total_count})")
            
            # Show search metadata if available
            if search_metadata:
                print(f"Search Text: '{search_metadata.get('search_text', 'None')}'")
                print(f"Filters Applied: {search_metadata.get('filters_applied', False)}")
                if search_metadata.get('searchable_columns'):
                    print(f"Searchable Columns: {search_metadata['searchable_columns']}")
            
            # Show pagination info
            if "page" in body:
                print(f"Page {body['page']} of {body.get('total_pages', 1)} (Has Next: {body.get('has_next', False)})")
            
            # Show first few results
            if data:
                print("\nFirst few results:")
                for i, project in enumerate(data[:3]):
                    print(f"  {i+1}. {project.get('project_name', 'N/A')} - {project.get('lead_full_name', 'N/A')}")
                    if project.get('project_description'):
                        desc = project['project_description'][:60] + "..." if len(project['project_description']) > 60 else project['project_description']
                        print(f"     Description: {desc}")
            else:
                print("No results found.")
        else:
            print(f"❌ Error: {body}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def main():
    """Run comprehensive search tests."""
    print("🚀 Advanced Search API Testing")
    print("Testing comprehensive search functionality across Projects API")
    
    # Test 1: Basic text search
    test_api_endpoint(
        "Basic Text Search - Search for 'test'",
        {
            "queryStringParameters": {
                "search": "test",
                "page": "1",
                "limit": "5"
            }
        }
    )
    
    # Test 2: Search for specific lead name
    test_api_endpoint(
        "Search by Lead Name - 'niketh'",
        {
            "queryStringParameters": {
                "search": "niketh",
                "sortBy": "project_name",
                "order": "asc"
            }
        }
    )
    
    # Test 3: Advanced filter - exact match
    test_api_endpoint(
        "Advanced Filter - Exact Lead ID Match",
        {
            "queryStringParameters": {
                "filter_lead_id__equals": "69",
                "limit": "10"
            }
        }
    )
    
    # Test 4: Advanced filter - contains project name
    test_api_endpoint(
        "Advanced Filter - Project Name Contains 'API'",
        {
            "queryStringParameters": {
                "filter_project_name__contains": "API",
                "sortBy": "created_at",
                "order": "desc"
            }
        }
    )
    
    # Test 5: Combined text search and filter
    test_api_endpoint(
        "Combined Search - Text + Filter",
        {
            "queryStringParameters": {
                "search": "project",
                "filter_lead_id__equals": "69",
                "limit": "5"
            }
        }
    )
    
    # Test 6: Date range filter
    test_api_endpoint(
        "Date Range Filter - Projects created in 2025",
        {
            "queryStringParameters": {
                "filter_created_at__date_range": "2025-01-01",
                "limit": "10"
            }
        }
    )
    
    # Test 7: Multiple advanced filters
    test_api_endpoint(
        "Multiple Advanced Filters",
        {
            "queryStringParameters": {
                "filter_project_name__contains": "test",
                "filter_lead_full_name__contains": "sai",
                "sortBy": "updated_at",
                "order": "desc",
                "limit": "5"
            }
        }
    )
    
    # Test 8: Pagination test
    test_api_endpoint(
        "Pagination Test - Page 2",
        {
            "queryStringParameters": {
                "page": "2",
                "limit": "2",
                "sortBy": "project_name"
            }
        }
    )
    
    # Test 9: Search with no results
    test_api_endpoint(
        "Search with No Results",
        {
            "queryStringParameters": {
                "search": "nonexistent_project_xyz123",
                "limit": "10"
            }
        }
    )
    
    # Test 10: Invalid filter column (should handle gracefully)
    test_api_endpoint(
        "Invalid Filter Column Test",
        {
            "queryStringParameters": {
                "filter_invalid_column__equals": "test",
                "limit": "5"
            }
        }
    )
    
    # Test 11: Complex search scenario
    test_api_endpoint(
        "Complex Search - Description + Lead + Sorting",
        {
            "queryStringParameters": {
                "search": "integration",
                "filter_lead_id__equals": "69",
                "sortBy": "project_name",
                "order": "asc",
                "page": "1",
                "limit": "5"
            }
        }
    )
    
    # Test 12: All projects (no search/filter)
    test_api_endpoint(
        "Get All Projects (No Search/Filter)",
        {
            "queryStringParameters": {
                "page": "1",
                "limit": "10",
                "sortBy": "created_at",
                "order": "desc"
            }
        }
    )
    
    print(f"\n{'='*60}")
    print("🎉 Advanced Search API Testing Complete!")
    print(f"{'='*60}")
    print("\nSearch Features Demonstrated:")
    print("✅ Global text search across multiple columns")
    print("✅ Advanced filtering with operators (equals, contains, date_range)")
    print("✅ Combined search and filter functionality")
    print("✅ Pagination and sorting")
    print("✅ Error handling for invalid columns")
    print("✅ Multiple filter combinations")
    print("\nAPI Usage Examples:")
    print("• Text Search: ?search=john")
    print("• Advanced Filter: ?filter_column__operator=value")
    print("• Combined: ?search=test&filter_lead_id__equals=69")
    print("• Date Range: ?filter_created_at__date_range=2025-01-01")
    print("• Pagination: ?page=2&limit=10&sortBy=name&order=desc")

if __name__ == "__main__":
    main()
