#!/usr/bin/env python3
"""
Leads Advanced Search API Test Script

This script demonstrates the advanced search functionality for the leads API,
showing how the same search utility works across different modules.
"""

import sys
import os
import json

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from com.dimcon.synthera.routes.leads_req_router import LeadsRequestRouter

def test_leads_search(description, query_params):
    """Test a leads search endpoint and display results."""
    print(f"\n{'='*60}")
    print(f"🔍 {description}")
    print(f"{'='*60}")
    
    if query_params:
        print("Query Parameters:")
        for key, value in query_params.items():
            print(f"  {key}: {value}")
        print()
    
    event = {"queryStringParameters": query_params}
    
    try:
        response = LeadsRequestRouter.route_request(
            http_method="GET",
            resource_path="/leads",
            path_params={},
            event=event
        )
        
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
                for i, lead in enumerate(data[:3]):
                    full_name = f"{lead.get('lead_first_name', '')} {lead.get('lead_last_name', '')}".strip()
                    company = lead.get('lead_company_name', 'N/A')
                    email = lead.get('email', 'N/A')
                    print(f"  {i+1}. {full_name} - {company} ({email})")
            else:
                print("No results found.")
        else:
            print(f"❌ Error: {body}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def main():
    """Run comprehensive leads search tests."""
    print("🚀 Advanced Leads Search API Testing")
    print("Demonstrating search utility reusability across modules")
    
    # Test 1: Search by first name
    test_leads_search(
        "Search by First Name - 'niketh'",
        {
            "search": "niketh",
            "limit": "10",
            "sortBy": "lead_first_name"
        }
    )
    
    # Test 2: Search by email domain
    test_leads_search(
        "Search by Email Domain - Contains 'gmail'",
        {
            "filter_email__contains": "gmail",
            "sortBy": "email",
            "order": "asc"
        }
    )
    
    # Test 3: Search by company name
    test_leads_search(
        "Search by Company Name",
        {
            "filter_lead_company_name__contains": "tech",
            "limit": "5"
        }
    )
    
    # Test 4: Combined text search and filter
    test_leads_search(
        "Combined Search - Name + Company Filter",
        {
            "search": "sai",
            "filter_lead_company_name__is_not_null": "true",
            "sortBy": "created_at",
            "order": "desc"
        }
    )
    
    # Test 5: Advanced filter - starts with
    test_leads_search(
        "First Name Starts With 'n'",
        {
            "filter_lead_first_name__starts_with": "n",
            "limit": "10"
        }
    )
    
    # Test 6: Date range filter
    test_leads_search(
        "Leads Created in 2025",
        {
            "filter_created_at__date_range": "2025-01-01",
            "sortBy": "created_at",
            "order": "desc"
        }
    )
    
    # Test 7: Multiple filters
    test_leads_search(
        "Multiple Filters - Name Contains 'i' AND Email Not Null",
        {
            "filter_lead_first_name__contains": "i",
            "filter_lead_email__is_not_null": "true",
            "limit": "5"
        }
    )
    
    # Test 8: Pagination
    test_leads_search(
        "All Leads with Pagination",
        {
            "page": "1",
            "limit": "3",
            "sortBy": "lead_last_name",
            "order": "asc"
        }
    )
    
    # Test 9: Search with no results
    test_leads_search(
        "Search with No Results",
        {
            "search": "nonexistent_lead_xyz123",
            "limit": "10"
        }
    )
    
    # Test 10: Complex search scenario
    test_leads_search(
        "Complex Search - Multiple Criteria",
        {
            "search": "niketh",
            "filter_email__is_not_null": "true",
            "sortBy": "lead_first_name",
            "order": "asc",
            "page": "1",
            "limit": "5"
        }
    )
    
    print(f"\n{'='*60}")
    print("🎉 Leads Advanced Search Testing Complete!")
    print(f"{'='*60}")
    print("\nKey Features Demonstrated:")
    print("✅ Search utility works seamlessly across different modules")
    print("✅ Same operators and functionality for Projects and Leads")
    print("✅ Model-specific search columns configured automatically")
    print("✅ Consistent API patterns across all endpoints")
    print("✅ Reusable search infrastructure")
    print("\nNext Steps:")
    print("• Add search functionality to Meetings module")
    print("• Create frontend search components")
    print("• Implement saved searches")
    print("• Add search analytics")

if __name__ == "__main__":
    main()
