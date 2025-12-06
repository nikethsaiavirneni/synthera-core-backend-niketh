-- 1. Roles table
CREATE TABLE roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL,
    short_name VARCHAR(20) UNIQUE NOT NULL,
    description TEXT,
    created_by INT,
    updated_by INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Users table
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role_short_name VARCHAR(20) REFERENCES roles(short_name),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Status table
CREATE TABLE status (
    status_id SERIAL PRIMARY KEY,
    status_name VARCHAR(50) UNIQUE NOT NULL
);

-- 4. Organization table
CREATE TABLE Organization_Entity (
    Organization_id SERIAL PRIMARY KEY,
    Organization_name VARCHAR(255) NOT NULL,
    org_contact_number VARCHAR(50),
    org_email VARCHAR(255),
    org_address VARCHAR(255),
    Created_by INT REFERENCES users(user_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    Updated_by INT REFERENCES users(user_id)
);

-- 5. Employee Profile table
CREATE TABLE Employee_profile_entity (
    Emp_id SERIAL PRIMARY KEY,
    Organization_id INT REFERENCES Organization_Entity(Organization_id),
    employee_name VARCHAR(255) NOT NULL,
    emp_org_email VARCHAR(255),
    emp_contact_number VARCHAR(50),
    emp_address VARCHAR(255),
    emp_role TEXT[] DEFAULT ARRAY['employee'],
    emp_status TEXT[] DEFAULT ARRAY['active'],
    Created_by INT REFERENCES users(user_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    Updated_by INT REFERENCES users(user_id)
);

-- 6. Lead Stages table
CREATE TABLE Lead_Stages (
    lead_stage_id SERIAL PRIMARY KEY,
    stage_name VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Leads Details table
CREATE TABLE Leads_details (
    lead_id SERIAL PRIMARY KEY,
    lead_first_name VARCHAR(255),
    lead_last_name VARCHAR(255),
    company VARCHAR(255),
    email VARCHAR(255),
    contact_number VARCHAR(50),
    job_title VARCHAR(255),
    department VARCHAR(255),
    industry VARCHAR(255),
    website_url VARCHAR(255),
    address_line_1 VARCHAR(255),
    address_line_2 VARCHAR(255),
    city VARCHAR(255),
    state_province VARCHAR(255),
    postal_code VARCHAR(255),
    country VARCHAR(255),
    linkedin_profile_url VARCHAR(255),
    preferred_contact_method VARCHAR(255),
    budget_range INT,
    meeting_availability TIMESTAMP WITH TIME ZONE,
    lead_source VARCHAR(255),
    lead_stage_id INT REFERENCES Lead_Stages(lead_stage_id),
    created_by INT REFERENCES users(user_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by INT REFERENCES users(user_id)
);

-- 8. Employee Lead Stages table
CREATE TABLE Employee_Lead_Stages (
    emp_lead_stage_id SERIAL PRIMARY KEY,
    emp_id INT REFERENCES Employee_profile_entity(Emp_id),
    lead_stage_id INT REFERENCES Lead_Stages(lead_stage_id),
    lead_id INT REFERENCES Leads_details(lead_id),
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 9. Integration table
CREATE TABLE integration (
    integration_id SERIAL PRIMARY KEY,
    integration_name VARCHAR(255) NOT NULL,
    status_id INT REFERENCES status(status_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 10. App Integration table
CREATE TABLE app_integration (
    app_integration_id SERIAL PRIMARY KEY,
    integration_name VARCHAR(255) NOT NULL,
    app_key TEXT,
    app_secret TEXT,
    base_url VARCHAR(255),
    status_id INT REFERENCES status(status_id),
    workflow_status_id INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INT REFERENCES users(user_id),
    updated_by INT REFERENCES users(user_id)
);

-- 11. App Workflow Status table
CREATE TABLE app_workflow_status (
    workflow_status_id SERIAL PRIMARY KEY,
    app_integration_id INT REFERENCES app_integration(app_integration_id),
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 12. App Files for Integration table
CREATE TABLE app_files_for_integration (
    file_id SERIAL PRIMARY KEY,
    app_integration_id INT REFERENCES app_integration(app_integration_id),
    file_name VARCHAR(255),
    file_type VARCHAR(255)[],
    file_path VARCHAR(255),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by INT REFERENCES users(user_id)
);

-- 13. App Documents table
CREATE TABLE app_documents (
    doc_id SERIAL PRIMARY KEY,
    app_integration_id INT REFERENCES app_integration(app_integration_id),
    doc_title VARCHAR(255),
    doc_url VARCHAR(500),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by INT REFERENCES users(user_id)
);

-- 14. Leads Integrations table
CREATE TABLE leads_integrations (
    lead_integration_id SERIAL PRIMARY KEY,
    lead_id INT REFERENCES Leads_details(lead_id),
    integration_id INT REFERENCES integration(integration_id),
    app_integration_id INT REFERENCES app_integration(app_integration_id),
    status TEXT[] DEFAULT ARRAY['active'],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INT REFERENCES users(user_id)
);

-- 15. Document Categories table
CREATE TABLE document_categories (
    id SERIAL PRIMARY KEY,
    document_category_name VARCHAR(50) UNIQUE NOT NULL
);

-- 16. Document Types table
CREATE TABLE Document_Types (
    document_type_id SERIAL PRIMARY KEY,
    document_type VARCHAR(50) UNIQUE NOT NULL
);

-- 17. Documents table
CREATE TABLE Documents (
    document_id SERIAL PRIMARY KEY,
    document_name VARCHAR(255),
    document_type_id INT REFERENCES Document_Types(document_type_id),
    uploaded_by INT REFERENCES users(user_id),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    file_url TEXT,
    document_category_name VARCHAR(50) REFERENCES document_categories(document_category_name),
    is_archived BOOLEAN DEFAULT FALSE,
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by INT REFERENCES users(user_id),
    doc_related_lead INT REFERENCES Leads_details(lead_id),
    current_version INT DEFAULT 1
);

-- 18. Documents History table
CREATE TABLE Documents_History (
    history_id SERIAL PRIMARY KEY,
    document_id INT REFERENCES Documents(document_id),
    modified_by INT REFERENCES users(user_id),
    modified_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    modification_type VARCHAR(50),
    historical_version INT
);

-- 19. Documents Recently Viewed table
CREATE TABLE Documents_Recently_Viewed (
    emp_id INT REFERENCES Employee_profile_entity(Emp_id),
    document_id INT REFERENCES Documents(document_id),
    viewed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (emp_id, document_id)
);

-- 20. Document Sub Categories table
CREATE TABLE Document_Sub_Categories (
    id SERIAL PRIMARY KEY,
    document_category_id INT REFERENCES document_categories(id),
    subcategory_name VARCHAR(255),
    created_by INT REFERENCES users(user_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by INT REFERENCES users(user_id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 21. Files Data table
CREATE TABLE Files_Data (
    id SERIAL PRIMARY KEY,
    subcategory_id INT REFERENCES Document_Sub_Categories(id),
    file_data BYTEA,
    file_url VARCHAR(255),
    created_by INT REFERENCES users(user_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by INT REFERENCES users(user_id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 22. Task Status table
CREATE TABLE Task_Status (
    status_id SERIAL PRIMARY KEY,
    status_name VARCHAR(50) UNIQUE NOT NULL
);

-- 23. Task Priority table
CREATE TABLE Task_Priority (
    priority_id SERIAL PRIMARY KEY,
    priority_name VARCHAR(50) UNIQUE NOT NULL
);

-- 24. Tasks table
CREATE TABLE Tasks (
    task_id SERIAL PRIMARY KEY,
    task_name VARCHAR(255),
    last_date TIMESTAMP WITH TIME ZONE,
    status_id INT REFERENCES Task_Status(status_id),
    priority_id INT REFERENCES Task_Priority(priority_id),
    related_lead INT REFERENCES Leads_details(lead_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 25. Task Completed table
CREATE TABLE Task_Completed (
    completed_id SERIAL PRIMARY KEY,
    task_id INT REFERENCES Tasks(task_id),
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 26. Meeting Call Type table
CREATE TABLE Meating_Call_Type (
    call_type_id SERIAL PRIMARY KEY,
    call_type_name VARCHAR(50) UNIQUE NOT NULL
);

-- 27. Meeting Priority Level table
CREATE TABLE meating_Priority_Level (
    priority_id SERIAL PRIMARY KEY,
    priority_name VARCHAR(50) UNIQUE NOT NULL
);

-- 28. Meeting table
CREATE TABLE Meeting (
    meeting_id SERIAL PRIMARY KEY,
    lead_id INT REFERENCES Leads_details(lead_id),
    call_type_id INT REFERENCES Meating_Call_Type(call_type_id),
    start_time TIMESTAMP WITH TIME ZONE,
    call_duration INT,
    priority_id INT REFERENCES meating_Priority_Level(priority_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 29. Meetings Completed table
CREATE TABLE Meetings_Completed (
    completed_meeting_id SERIAL PRIMARY KEY,
    meeting_id INT REFERENCES Meeting(meeting_id),
    score INT,
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    employee_id INT REFERENCES Employee_profile_entity(Emp_id)
);

-- 30. Calendar table
CREATE TABLE Calendar (
    calendar_id SERIAL PRIMARY KEY,
    event_type_id INT,
    activity_id INT,
    title VARCHAR(255),
    description TEXT,
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    priority_id INT,
    status_id INT DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 31. Meeting Status table
CREATE TABLE Meating_Status (
    status_id SERIAL PRIMARY KEY,
    status_name VARCHAR(50) UNIQUE NOT NULL
);

-- -- 32. Meeting Priority Level table
CREATE TABLE Meating_Priority_Level (
    priority_id SERIAL PRIMARY KEY,
    priority_name VARCHAR(50) UNIQUE NOT NULL
);

-- 33. Meeting Event Type table
CREATE TABLE Meating_Event_Type (
    event_type_id SERIAL PRIMARY KEY,
    event_type_name VARCHAR(50) UNIQUE NOT NULL
);