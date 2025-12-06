-- Insert into roles
INSERT INTO roles (role_name, short_name, description, created_by, updated_by) 
VALUES 
('Administrator', 'admin', 'System Administrator', 1, 1),
('Manager', 'manager', 'Team Manager', 1, 1),
('Employee', 'employee', 'Regular Employee', 1, 1);

-- Insert into users
INSERT INTO users (username, email, password_hash, role_short_name) 
VALUES 
('admin_user', 'admin@example.com', 'hashed_password1', 'admin'),
('manager_user', 'manager@example.com', 'hashed_password2', 'manager'),
('employee_user', 'employee@example.com', 'hashed_password3', 'employee');

-- Insert into status
INSERT INTO status (status_name) 
VALUES 
('Active'), 
('Inactive'), 
('Pending');

-- Insert into Organization
INSERT INTO Organization_Entity (Organization_name, org_contact_number, org_email, org_address, Created_by, Updated_by) 
VALUES 
('TechCorp', '1234567890', 'contact@techcorp.com', '123 Tech Street', 1, 1);

-- Insert into Employee Profile
INSERT INTO Employee_profile_entity (Organization_id, employee_name, emp_org_email, emp_contact_number, emp_address, Created_by, Updated_by) 
VALUES 
(1, 'John Doe', 'johndoe@techcorp.com', '9876543210', '456 Corporate Blvd', 1, 1);

-- Insert into Lead Stages
INSERT INTO Lead_Stages (stage_name) 
VALUES 
('New'), 
('In Progress'), 
('Closed');

-- Insert into Leads Details
INSERT INTO Leads_details (lead_first_name, lead_last_name, company, email, contact_number, job_title, department, industry, lead_source, lead_stage_id, created_by, updated_by) 
VALUES 
('Alice', 'Smith', 'Company A', 'alice@companya.com', '1112223333', 'Manager', 'Sales', 'Tech', 'Referral', 1, 1, 1);

-- Insert into Employee Lead Stages
INSERT INTO Employee_Lead_Stages (emp_id, lead_stage_id, lead_id) 
VALUES 
(1, 1, 1);

-- Insert into integration
INSERT INTO integration (integration_name, status_id) 
VALUES 
('CRM Integration', 1);

-- Insert into app_integration
INSERT INTO app_integration (integration_name, app_key, app_secret, base_url, status_id, created_by, updated_by) 
VALUES 
('Salesforce', 'key123', 'secret123', 'https://api.salesforce.com', 1, 1, 1);

-- Insert into app_workflow_status
INSERT INTO app_workflow_status (app_integration_id) 
VALUES 
(1);

-- Insert into app_files_for_integration
INSERT INTO app_files_for_integration (app_integration_id, file_name, file_type, file_path, updated_by) 
VALUES 
(1, 'data.csv', ARRAY['csv'], '/files/data.csv', 1);

-- Insert into app_documents
INSERT INTO app_documents (app_integration_id, doc_title, doc_url, updated_by) 
VALUES 
(1, 'API Documentation', 'https://docs.salesforce.com', 1);

-- Insert into leads_integrations
INSERT INTO leads_integrations (lead_id, integration_id, app_integration_id, created_by) 
VALUES 
(1, 1, 1, 1);

-- Insert into document_categories
INSERT INTO document_categories (document_category_name) 
VALUES 
('Contracts'),
('Invoices');

-- Insert into Document Types
INSERT INTO Document_Types (document_type) 
VALUES 
('PDF'),
('Word Document');

-- Insert into Documents
INSERT INTO Documents (document_name, document_type_id, uploaded_by, file_url, document_category_name, doc_related_lead) 
VALUES 
('Contract_123', 1, 1, '/docs/contract_123.pdf', 'Contracts', 1);

-- Insert into Documents History
INSERT INTO Documents_History (document_id, modified_by, modification_type, historical_version) 
VALUES 
(1, 1, 'Updated', 1);

-- Insert into Documents Recently Viewed
INSERT INTO Documents_Recently_Viewed (emp_id, document_id) 
VALUES 
(1, 1);

-- Insert into Document Sub Categories
INSERT INTO Document_Sub_Categories (document_category_id, subcategory_name, created_by, updated_by) 
VALUES 
(1, 'Signed Contracts', 1, 1);

-- Insert into Files Data
INSERT INTO Files_Data (subcategory_id, file_data, file_url, created_by, updated_by) 
VALUES 
(1, NULL, '/files/signed_contract.pdf', 1, 1);

-- Insert into Task Status
INSERT INTO Task_Status (status_name) 
VALUES 
('Pending'), 
('Completed');

-- Insert into Task Priority
INSERT INTO Task_Priority (priority_name) 
VALUES 
('High'), 
('Medium'), 
('Low');

-- Insert into Tasks
INSERT INTO Tasks (task_name, last_date, status_id, priority_id, related_lead) 
VALUES 
('Follow-up Call', NOW(), 1, 1, 1);

-- Insert into Task Completed
INSERT INTO Task_Completed (task_id) 
VALUES 
(1);

-- Insert into Meeting Call Type
INSERT INTO Meating_Call_Type (call_type_name) 
VALUES 
('Phone Call'),
('Video Call');

-- Insert into Meeting Priority Level
INSERT INTO meating_Priority_Level (priority_name) 
VALUES 
('High'),
('Medium'),
('Low');

-- Insert into Meeting
INSERT INTO Meeting (lead_id, call_type_id) 
VALUES 
(1, 1);
