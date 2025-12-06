# Advanced Search Functionality Documentation

## Overview

The Synthera Core Backend API now includes comprehensive search functionality that works across all modules (Projects, Leads, Meetings). This system provides powerful querying capabilities with multiple search operators, pagination, sorting, and flexible filtering.

## Features

### 🔍 **Global Text Search**
- Search across multiple columns simultaneously
- Case-insensitive text matching
- Configurable search columns per model

### ⚙️ **Advanced Filtering**
- Multiple filter operators (equals, contains, greater_than, date_range, etc.)
- Combine multiple filters
- Support for different data types (text, numbers, dates)

### 📄 **Pagination & Sorting**
- Configurable page size
- Sort by any column (ascending/descending)
- Pagination metadata in responses

### 🛡️ **Error Handling**
- Graceful handling of invalid columns
- Robust error responses
- Input validation

## API Usage

### Basic Text Search

Search for text across default searchable columns:

```http
GET /projects?search=john
GET /leads?search=company
GET /meetings?search=quarterly
```

### Advanced Filtering

Use the `filter_` prefix with column names and operators:

```http
# Exact match
GET /projects?filter_lead_id__equals=69

# Text contains
GET /leads?filter_lead_first_name__contains=john

# Date range
GET /projects?filter_created_at__date_range=2025-01-01&filter_created_at__end=2025-12-31

# Greater than
GET /leads?filter_age__greater_than=25

# Multiple filters
GET /projects?filter_project_name__contains=API&filter_lead_id__equals=69
```

### Combined Search and Filtering

```http
# Text search + filter
GET /projects?search=integration&filter_lead_id__equals=69

# Complex search with pagination
GET /leads?search=john&filter_lead_status__equals=active&page=2&limit=5&sortBy=created_at&order=desc
```

### Pagination and Sorting

```http
# Basic pagination
GET /projects?page=2&limit=10

# With sorting
GET /leads?sortBy=lead_first_name&order=desc

# Complete example
GET /projects?search=test&page=1&limit=5&sortBy=created_at&order=desc
```

## Available Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `equals` | Exact match | `filter_status__equals=active` |
| `not_equals` | Not equal to | `filter_status__not_equals=inactive` |
| `contains` | Text contains (case-insensitive) | `filter_name__contains=john` |
| `not_contains` | Text does not contain | `filter_name__not_contains=test` |
| `starts_with` | Text starts with | `filter_name__starts_with=Dr` |
| `ends_with` | Text ends with | `filter_email__ends_with=gmail.com` |
| `greater_than` | Greater than | `filter_age__greater_than=18` |
| `greater_than_equal` | Greater than or equal | `filter_score__greater_than_equal=80` |
| `less_than` | Less than | `filter_age__less_than=65` |
| `less_than_equal` | Less than or equal | `filter_score__less_than_equal=100` |
| `in` | Value in list | `filter_status__in=active,pending` |
| `not_in` | Value not in list | `filter_status__not_in=inactive,deleted` |
| `is_null` | Field is null | `filter_description__is_null=true` |
| `is_not_null` | Field is not null | `filter_description__is_not_null=true` |
| `date_range` | Date between start and end | `filter_created_at__date_range=2025-01-01` |
| `numeric_range` | Number between min and max | `filter_price__numeric_range=100` |
| `regex` | Regular expression match | `filter_phone__regex=^\\+1` |

## Date Range Filtering

For date range filtering, you can specify start and/or end dates:

```http
# From a specific date onwards
GET /projects?filter_created_at__date_range=2025-01-01

# Up to a specific date
GET /projects?filter_created_at__date_range=&filter_created_at__end=2025-12-31

# Between two dates
GET /projects?filter_created_at__date_range=2025-01-01&filter_created_at__end=2025-06-30
```

## Searchable Columns by Model

### Projects
- **Default Search Columns**: `project_name`, `project_description`, `lead_full_name`
- **All Searchable Columns**: `project_name`, `project_description`, `lead_full_name`, `s3_url_transcription`, `s3_url_sow_ppt`
- **Filterable Columns**: `lead_id`, `project_name`, `lead_full_name`, `created_at`, `updated_at`

### Leads
- **Default Search Columns**: `lead_first_name`, `lead_last_name`, `lead_email`, `lead_company_name`
- **All Searchable Columns**: `lead_first_name`, `lead_last_name`, `lead_email`, `lead_company_name`, `lead_phone_number`, `lead_address`
- **Filterable Columns**: `lead_first_name`, `lead_last_name`, `lead_email`, `lead_company_name`, `lead_status`, `created_at`

### Meetings
- **Default Search Columns**: `meeting_name`, `meeting_description`, `meeting_location`
- **All Searchable Columns**: `meeting_name`, `meeting_description`, `meeting_location`
- **Filterable Columns**: `meeting_name`, `meeting_status`, `meeting_date`, `created_at`

## Response Format

All search endpoints return a consistent response format:

```json
{
  "statusCode": 200,
  "body": {
    "message": "Search completed successfully",
    "data": [
      {
        "project_id": 5,
        "project_name": "AI Integration Project",
        "project_description": "A comprehensive AI integration project...",
        "lead_full_name": "John Doe",
        "created_at": "2025-07-28T21:52:35.646640+00:00"
      }
    ],
    "total_count": 25,
    "page": 1,
    "limit": 10,
    "total_pages": 3,
    "has_next": true,
    "has_prev": false,
    "search_metadata": {
      "search_text": "integration",
      "filters_applied": true,
      "searchable_columns": ["project_name", "project_description", "lead_full_name"]
    }
  }
}
```

## Real-World Examples

### 1. Find all projects for a specific lead containing "API"
```http
GET /projects?search=API&filter_lead_id__equals=69
```

### 2. Find leads created in the last month with "gmail" email
```http
GET /leads?filter_email__contains=gmail&filter_created_at__date_range=2025-07-01&sortBy=created_at&order=desc
```

### 3. Search for active leads named "John" or "Jane"
```http
GET /leads?search=john jane&filter_lead_status__equals=active
```

### 4. Find projects with descriptions, sorted by creation date
```http
GET /projects?filter_project_description__is_not_null=true&sortBy=created_at&order=desc
```

### 5. Paginated search through meetings this year
```http
GET /meetings?filter_meeting_date__date_range=2025-01-01&page=2&limit=20&sortBy=meeting_date&order=asc
```

## Implementation Details

### Architecture
- **SearchUtility**: Core search engine with SQLAlchemy integration
- **ModelSearchConfig**: Configuration for each model's searchable columns
- **Service Layer**: Integration of search with existing business logic
- **Router Layer**: HTTP parameter parsing and routing

### Performance Considerations
- Database indexes recommended on frequently searched/filtered columns
- Text search uses database ILIKE operations for case-insensitive matching
- Pagination prevents large result sets from impacting performance
- Proper session management ensures connection efficiency

### Backward Compatibility
The search functionality maintains full backward compatibility with existing APIs. Standard query parameters continue to work as before, while new search features are opt-in through the `search` parameter and `filter_` prefixed parameters.

## Error Handling

### Invalid Column Names
```json
{
  "statusCode": 200,
  "body": {
    "message": "Search completed successfully",
    "data": [...],
    "search_metadata": {
      "warnings": ["Column 'invalid_column' not found in model Project"]
    }
  }
}
```

### Invalid Operators
```json
{
  "statusCode": 400,
  "body": {
    "error": "Invalid operator 'invalid_op' for column 'project_name'"
  }
}
```

### Malformed Dates
```json
{
  "statusCode": 400,
  "body": {
    "error": "Invalid date format for 'created_at'. Expected ISO format (YYYY-MM-DD)"
  }
}
```

## Frontend Integration

### JavaScript/React Example
```javascript
// Search for projects
const searchProjects = async (searchText, filters, page = 1) => {
  const params = new URLSearchParams({
    search: searchText,
    page: page.toString(),
    limit: '10',
    sortBy: 'created_at',
    order: 'desc'
  });
  
  // Add filters
  Object.entries(filters).forEach(([key, value]) => {
    if (value.operator) {
      params.append(`filter_${key}__${value.operator}`, value.value);
    } else {
      params.append(`filter_${key}__equals`, value);
    }
  });
  
  const response = await fetch(`/api/projects?${params}`);
  return response.json();
};

// Usage
const results = await searchProjects('integration', {
  lead_id: { operator: 'equals', value: '69' },
  created_at: { operator: 'date_range', value: '2025-01-01' }
});
```

### Angular Example
```typescript
export class SearchService {
  searchProjects(searchText: string, filters: any, page: number = 1): Observable<any> {
    let params = new HttpParams()
      .set('search', searchText)
      .set('page', page.toString())
      .set('limit', '10');
      
    // Add advanced filters
    Object.entries(filters).forEach(([key, value]: [string, any]) => {
      const filterKey = value.operator ? 
        `filter_${key}__${value.operator}` : 
        `filter_${key}__equals`;
      params = params.set(filterKey, value.value || value);
    });
    
    return this.http.get(`/api/projects`, { params });
  }
}
```

## Future Enhancements

### Planned Features
- **Saved Searches**: Allow users to save and reuse complex search queries
- **Search Analytics**: Track popular search terms and optimize accordingly
- **Faceted Search**: Provide search result breakdowns by categories
- **Full-Text Search**: Integration with Elasticsearch for advanced text search
- **Search Suggestions**: Auto-complete and search term suggestions
- **Export Results**: CSV/Excel export of search results

### Customization Options
- **Per-User Search Preferences**: Customizable default columns and sort orders
- **Model-Specific Operators**: Additional operators for specific data types
- **Custom Search Aliases**: User-friendly names for complex filter combinations

This search functionality provides a solid foundation for powerful data querying across the Synthera platform, with room for future enhancements based on user needs and feedback.
