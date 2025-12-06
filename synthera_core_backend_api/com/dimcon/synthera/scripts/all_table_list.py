# from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, TIMESTAMP, Boolean, ARRAY, JSON, LargeBinary, text
# from sqlalchemy.orm import declarative_base, relationship, sessionmaker
# from datetime import datetime
# import pytz
# from connect_aurora import get_engine

# engine = get_engine()

# Base = declarative_base()

# class Role(Base):
#     __tablename__ = 'roles'
#     role_id = Column(Integer, primary_key=True, autoincrement=True)
#     role_name = Column(String(50), unique=True, nullable=False)
#     short_name = Column(String(20), unique=True, nullable=False)
#     description = Column(Text)
#     created_by = Column(Integer)
#     updated_by = Column(Integer)
#     created_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))
#     updated_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))

#     @classmethod
#     def create_table(cls, engine):
#         Base.metadata.create_all(engine)

#     @classmethod
#     def drop_table(cls, engine):
#         Base.metadata.drop_all(engine)

#     @classmethod
#     def alter_table(cls, engine):
#         with engine.connect() as connection:
#             connection.execute(text("ALTER TABLE roles ADD COLUMN new_column VARCHAR(255);"))

#     @classmethod
#     def insert_table(cls, engine, role_name, short_name, description=None, created_by=None, updated_by=None):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         new_role = cls(
#             role_name=role_name,
#             short_name=short_name,
#             description=description,
#             created_by=created_by,
#             updated_by=updated_by
#         )
#         session.add(new_role)
#         session.commit()
#         session.close()

#     @classmethod
#     def update_table(cls, engine, role_id, **kwargs):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         role = session.query(cls).filter_by(role_id=role_id).first()
#         for key, value in kwargs.items():
#             setattr(role, key, value)
#         session.commit()
#         session.close()

# class User(Base):
#     __tablename__ = 'users'
#     user_id = Column(Integer, primary_key=True, autoincrement=True)
#     username = Column(String(255), unique=True, nullable=False)
#     email = Column(String(255), unique=True, nullable=False)
#     password_hash = Column(Text, nullable=False)
#     role_short_name = Column(String(20), ForeignKey('roles.short_name'))
#     created_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))
#     updated_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))
#     role = relationship("Role")

#     @classmethod
#     def create_table(cls, engine):
#         Base.metadata.create_all(engine)

#     @classmethod
#     def drop_table(cls, engine):
#         Base.metadata.drop_all(engine)

#     @classmethod
#     def alter_table(cls, engine):
#         with engine.connect() as connection:
#             connection.execute(text("ALTER TABLE users ADD COLUMN new_column VARCHAR(255);"))

#     @classmethod
#     def insert_table(cls, engine, username, email, password_hash, role_short_name):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         new_user = cls(
#             username=username,
#             email=email,
#             password_hash=password_hash,
#             role_short_name=role_short_name
#         )
#         session.add(new_user)
#         session.commit()
#         session.close()

#     @classmethod
#     def update_table(cls, engine, user_id, **kwargs):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         user = session.query(cls).filter_by(user_id=user_id).first()
#         for key, value in kwargs.items():
#             setattr(user, key, value)
#         session.commit()
#         session.close()

# class Status(Base):
#     __tablename__ = 'status'
#     status_id = Column(Integer, primary_key=True, autoincrement=True)
#     status_name = Column(String(50), unique=True, nullable=False)

#     @classmethod
#     def create_table(cls, engine):
#         Base.metadata.create_all(engine)

#     @classmethod
#     def drop_table(cls, engine):
#         Base.metadata.drop_all(engine)

#     @classmethod
#     def alter_table(cls, engine):
#         with engine.connect() as connection:
#             connection.execute(text("ALTER TABLE status ADD COLUMN new_column VARCHAR(255);"))

#     @classmethod
#     def insert_table(cls, engine, status_name):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         new_status = cls(status_name=status_name)
#         session.add(new_status)
#         session.commit()
#         session.close()

#     @classmethod
#     def update_table(cls, engine, status_id, **kwargs):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         status = session.query(cls).filter_by(status_id=status_id).first()
#         for key, value in kwargs.items():
#             setattr(status, key, value)
#         session.commit()
#         session.close()

# class OrganizationEntity(Base):
#     __tablename__ = 'Organization_Entity'
#     Organization_id = Column(Integer, primary_key=True, autoincrement=True)
#     Organization_name = Column(String(255), nullable=False)
#     org_contact_number = Column(String(50))
#     org_email = Column(String(255))
#     org_address = Column(String(255))
#     Created_by = Column(Integer, ForeignKey('users.user_id'))
#     created_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))
#     updated_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))
#     Updated_by = Column(Integer, ForeignKey('users.user_id'))

#     @classmethod
#     def create_table(cls, engine):
#         Base.metadata.create_all(engine)

#     @classmethod
#     def drop_table(cls, engine):
#         Base.metadata.drop_all(engine)

#     @classmethod
#     def alter_table(cls, engine):
#         with engine.connect() as connection:
#             connection.execute(text("ALTER TABLE Organization_Entity ADD COLUMN new_column VARCHAR(255);"))

#     @classmethod
#     def insert_table(cls, engine, Organization_name, org_contact_number=None, org_email=None, org_address=None, Created_by=None, Updated_by=None):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         new_org = cls(
#             Organization_name=Organization_name,
#             org_contact_number=org_contact_number,
#             org_email=org_email,
#             org_address=org_address,
#             Created_by=Created_by,
#             Updated_by=Updated_by
#         )
#         session.add(new_org)
#         session.commit()
#         session.close()

#     @classmethod
#     def update_table(cls, engine, Organization_id, **kwargs):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         org = session.query(cls).filter_by(Organization_id=Organization_id).first()
#         for key, value in kwargs.items():
#             setattr(org, key, value)
#         session.commit()
#         session.close()

# class EmployeeProfileEntity(Base):
#     __tablename__ = 'Employee_profile_entity'
#     Emp_id = Column(Integer, primary_key=True, autoincrement=True)
#     Organization_id = Column(Integer, ForeignKey('Organization_Entity.Organization_id'))
#     employee_name = Column(String(255), nullable=False)
#     emp_org_email = Column(String(255))
#     emp_contact_number = Column(String(50))
#     emp_address = Column(String(255))
#     emp_role = Column(ARRAY(Text), default=['employee'])
#     emp_status = Column(ARRAY(Text), default=['active'])
#     Created_by = Column(Integer, ForeignKey('users.user_id'))
#     created_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))
#     updated_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))
#     Updated_by = Column(Integer, ForeignKey('users.user_id'))

#     @classmethod
#     def create_table(cls, engine):
#         Base.metadata.create_all(engine)

#     @classmethod
#     def drop_table(cls, engine):
#         Base.metadata.drop_all(engine)

#     @classmethod
#     def alter_table(cls, engine):
#         with engine.connect() as connection:
#             connection.execute(text("ALTER TABLE Employee_profile_entity ADD COLUMN new_column VARCHAR(255);"))

#     @classmethod
#     def insert_table(cls, engine, Organization_id, employee_name, emp_org_email=None, emp_contact_number=None, emp_address=None, emp_role=None, emp_status=None, Created_by=None, Updated_by=None):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         new_employee = cls(
#             Organization_id=Organization_id,
#             employee_name=employee_name,
#             emp_org_email=emp_org_email,
#             emp_contact_number=emp_contact_number,
#             emp_address=emp_address,
#             emp_role=emp_role or ['employee'],
#             emp_status=emp_status or ['active'],
#             Created_by=Created_by,
#             Updated_by=Updated_by
#         )
#         session.add(new_employee)
#         session.commit()
#         session.close()

#     @classmethod
#     def update_table(cls, engine, Emp_id, **kwargs):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         employee = session.query(cls).filter_by(Emp_id=Emp_id).first()
#         for key, value in kwargs.items():
#             setattr(employee, key, value)
#         session.commit()
#         session.close()

# class LeadStage(Base):
#     __tablename__ = 'Lead_Stages'
#     lead_stage_id = Column(Integer, primary_key=True, autoincrement=True)
#     stage_name = Column(String(50), unique=True, nullable=False)
#     created_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))
#     updated_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))

#     @classmethod
#     def create_table(cls, engine):
#         Base.metadata.create_all(engine)

#     @classmethod
#     def drop_table(cls, engine):
#         Base.metadata.drop_all(engine)

#     @classmethod
#     def alter_table(cls, engine):
#         with engine.connect() as connection:
#             connection.execute(text("ALTER TABLE Lead_Stages ADD COLUMN new_column VARCHAR(255);"))

#     @classmethod
#     def insert_table(cls, engine, stage_name):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         new_stage = cls(stage_name=stage_name)
#         session.add(new_stage)
#         session.commit()
#         session.close()

#     @classmethod
#     def update_table(cls, engine, lead_stage_id, **kwargs):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         stage = session.query(cls).filter_by(lead_stage_id=lead_stage_id).first()
#         for key, value in kwargs.items():
#             setattr(stage, key, value)
#         session.commit()
#         session.close()

# class LeadDetail(Base):
#     __tablename__ = 'Leads_details'
#     lead_id = Column(Integer, primary_key=True, autoincrement=True)
#     lead_first_name = Column(String(255))
#     lead_last_name = Column(String(255))
#     company = Column(String(255))
#     email = Column(String(255))
#     contact_number = Column(String(50))
#     job_title = Column(String(255))
#     department = Column(String(255))
#     industry = Column(String(255))
#     website_url = Column(String(255))
#     address_line_1 = Column(String(255))
#     address_line_2 = Column(String(255))
#     city = Column(String(255))
#     state_province = Column(String(255))
#     postal_code = Column(String(255))
#     country = Column(String(255))
#     linkedin_profile_url = Column(String(255))
#     preferred_contact_method = Column(String(255))
#     budget_range = Column(Integer)
#     meeting_availability = Column(TIMESTAMP(timezone=True))
#     lead_source = Column(String(255))
#     lead_stage_id = Column(Integer, ForeignKey('Lead_Stages.lead_stage_id'))
#     created_by = Column(Integer, ForeignKey('users.user_id'))
#     created_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))
#     updated_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))
#     updated_by = Column(Integer, ForeignKey('users.user_id'))

#     @classmethod
#     def create_table(cls, engine):
#         Base.metadata.create_all(engine)

#     @classmethod
#     def drop_table(cls, engine):
#         Base.metadata.drop_all(engine)

#     @classmethod
#     def alter_table(cls, engine):
#         with engine.connect() as connection:
#             connection.execute(text("ALTER TABLE Leads_details ADD COLUMN new_column VARCHAR(255);"))

#     @classmethod
#     def insert_table(cls, engine, lead_first_name=None, lead_last_name=None, company=None, email=None, contact_number=None, job_title=None, department=None, industry=None, website_url=None, address_line_1=None, address_line_2=None, city=None, state_province=None, postal_code=None, country=None, linkedin_profile_url=None, preferred_contact_method=None, budget_range=None, meeting_availability=None, lead_source=None, lead_stage_id=None, created_by=None, updated_by=None):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         new_lead = cls(
#             lead_first_name=lead_first_name,
#             lead_last_name=lead_last_name,
#             company=company,
#             email=email,
#             contact_number=contact_number,
#             job_title=job_title,
#             department=department,
#             industry=industry,
#             website_url=website_url,
#             address_line_1=address_line_1,
#             address_line_2=address_line_2,
#             city=city,
#             state_province=state_province,
#             postal_code=postal_code,
#             country=country,
#             linkedin_profile_url=linkedin_profile_url,
#             preferred_contact_method=preferred_contact_method,
#             budget_range=budget_range,
#             meeting_availability=meeting_availability,
#             lead_source=lead_source,
#             lead_stage_id=lead_stage_id,
#             created_by=created_by,
#             updated_by=updated_by
#         )
#         session.add(new_lead)
#         session.commit()
#         session.close()

#     @classmethod
#     def update_table(cls, engine, lead_id, **kwargs):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         lead = session.query(cls).filter_by(lead_id=lead_id).first()
#         for key, value in kwargs.items():
#             setattr(lead, key, value)
#         session.commit()
#         session.close()

# class EmployeeLeadStage(Base):
#     __tablename__ = 'Employee_Lead_Stages'
#     emp_lead_stage_id = Column(Integer, primary_key=True, autoincrement=True)
#     emp_id = Column(Integer, ForeignKey('Employee_profile_entity.Emp_id'))
#     lead_stage_id = Column(Integer, ForeignKey('Lead_Stages.lead_stage_id'))
#     lead_id = Column(Integer, ForeignKey('Leads_details.lead_id'))
#     assigned_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))
#     updated_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))

#     @classmethod
#     def create_table(cls, engine):
#         Base.metadata.create_all(engine)

#     @classmethod
#     def drop_table(cls, engine):
#         Base.metadata.drop_all(engine)

#     @classmethod
#     def alter_table(cls, engine):
#         with engine.connect() as connection:
#             connection.execute(text("ALTER TABLE Employee_Lead_Stages ADD COLUMN new_column VARCHAR(255);"))

#     @classmethod
#     def insert_table(cls, engine, emp_id, lead_stage_id, lead_id):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         new_emp_lead_stage = cls(
#             emp_id=emp_id,
#             lead_stage_id=lead_stage_id,
#             lead_id=lead_id
#         )
#         session.add(new_emp_lead_stage)
#         session.commit()
#         session.close()

#     @classmethod
#     def update_table(cls, engine, emp_lead_stage_id, **kwargs):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         emp_lead_stage = session.query(cls).filter_by(emp_lead_stage_id=emp_lead_stage_id).first()
#         for key, value in kwargs.items():
#             setattr(emp_lead_stage, key, value)
#         session.commit()
#         session.close()

# class Integration(Base):
#     __tablename__ = 'integration'
#     integration_id = Column(Integer, primary_key=True, autoincrement=True)
#     integration_name = Column(String(255), nullable=False)
#     status_id = Column(Integer, ForeignKey('status.status_id'))
#     created_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))
#     updated_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))

#     @classmethod
#     def create_table(cls, engine):
#         Base.metadata.create_all(engine)

#     @classmethod
#     def drop_table(cls, engine):
#         Base.metadata.drop_all(engine)

#     @classmethod
#     def alter_table(cls, engine):
#         with engine.connect() as connection:
#             connection.execute(text("ALTER TABLE integration ADD COLUMN new_column VARCHAR(255);"))

#     @classmethod
#     def insert_table(cls, engine, integration_name, status_id):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         new_integration = cls(
#             integration_name=integration_name,
#             status_id=status_id
#         )
#         session.add(new_integration)
#         session.commit()
#         session.close()

#     @classmethod
#     def update_table(cls, engine, integration_id, **kwargs):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         integration = session.query(cls).filter_by(integration_id=integration_id).first()
#         for key, value in kwargs.items():
#             setattr(integration, key, value)
#         session.commit()
#         session.close()

# class AppIntegration(Base):
#     __tablename__ = 'app_integration'
#     app_integration_id = Column(Integer, primary_key=True, autoincrement=True)
#     integration_name = Column(String(255), nullable=False)
#     app_key = Column(Text)
#     app_secret = Column(Text)
#     base_url = Column(String(255))
#     status_id = Column(Integer, ForeignKey('status.status_id'))
#     workflow_status_id = Column(Integer)
#     created_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))
#     updated_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))
#     created_by = Column(Integer, ForeignKey('users.user_id'))
#     updated_by = Column(Integer, ForeignKey('users.user_id'))

#     @classmethod
#     def create_table(cls, engine):
#         Base.metadata.create_all(engine)

#     @classmethod
#     def drop_table(cls, engine):
#         Base.metadata.drop_all(engine)

#     @classmethod
#     def alter_table(cls, engine):
#         with engine.connect() as connection:
#             connection.execute(text("ALTER TABLE app_integration ADD COLUMN new_column VARCHAR(255);"))

#     @classmethod
#     def insert_table(cls, engine, integration_name, app_key=None, app_secret=None, base_url=None, status_id=None, workflow_status_id=None, created_by=None, updated_by=None):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         new_app_integration = cls(
#             integration_name=integration_name,
#             app_key=app_key,
#             app_secret=app_secret,
#             base_url=base_url,
#             status_id=status_id,
#             workflow_status_id=workflow_status_id,
#             created_by=created_by,
#             updated_by=updated_by
#         )
#         session.add(new_app_integration)
#         session.commit()
#         session.close()

#     @classmethod
#     def update_table(cls, engine, app_integration_id, **kwargs):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         app_integration = session.query(cls).filter_by(app_integration_id=app_integration_id).first()
#         for key, value in kwargs.items():
#             setattr(app_integration, key, value)
#         session.commit()
#         session.close()

# class AppWorkflowStatus(Base):
#     __tablename__ = 'app_workflow_status'
#     workflow_status_id = Column(Integer, primary_key=True, autoincrement=True)
#     app_integration_id = Column(Integer, ForeignKey('app_integration.app_integration_id'))
#     assigned_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))

#     @classmethod
#     def create_table(cls, engine):
#         Base.metadata.create_all(engine)

#     @classmethod
#     def drop_table(cls, engine):
#         Base.metadata.drop_all(engine)

#     @classmethod
#     def alter_table(cls, engine):
#         with engine.connect() as connection:
#             connection.execute(text("ALTER TABLE app_workflow_status ADD COLUMN new_column VARCHAR(255);"))

#     @classmethod
#     def insert_table(cls, engine, app_integration_id):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         new_workflow_status = cls(app_integration_id=app_integration_id)
#         session.add(new_workflow_status)
#         session.commit()
#         session.close()

#     @classmethod
#     def update_table(cls, engine, workflow_status_id, **kwargs):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         workflow_status = session.query(cls).filter_by(workflow_status_id=workflow_status_id).first()
#         for key, value in kwargs.items():
#             setattr(workflow_status, key, value)
#         session.commit()
#         session.close()

# class AppFilesForIntegration(Base):
#     __tablename__ = 'app_files_for_integration'
#     file_id = Column(Integer, primary_key=True, autoincrement=True)
#     app_integration_id = Column(Integer, ForeignKey('app_integration.app_integration_id'))
#     file_name = Column(String(255))
#     file_type = Column(ARRAY(String(255)))
#     file_path = Column(String(255))
#     uploaded_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))
#     updated_by = Column(Integer, ForeignKey('users.user_id'))

#     @classmethod
#     def create_table(cls, engine):
#         Base.metadata.create_all(engine)

#     @classmethod
#     def drop_table(cls, engine):
#         Base.metadata.drop_all(engine)

#     @classmethod
#     def alter_table(cls, engine):
#         with engine.connect() as connection:
#             connection.execute(text("ALTER TABLE app_files_for_integration ADD COLUMN new_column VARCHAR(255);"))

#     @classmethod
#     def insert_table(cls, engine, app_integration_id, file_name=None, file_type=None, file_path=None, updated_by=None):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         new_file = cls(
#             app_integration_id=app_integration_id,
#             file_name=file_name,
#             file_type=file_type,
#             file_path=file_path,
#             updated_by=updated_by
#         )
#         session.add(new_file)
#         session.commit()
#         session.close()

#     @classmethod
#     def update_table(cls, engine, file_id, **kwargs):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         file = session.query(cls).filter_by(file_id=file_id).first()
#         for key, value in kwargs.items():
#             setattr(file, key, value)
#         session.commit()
#         session.close()

# class AppDocument(Base):
#     __tablename__ = 'app_documents'
#     doc_id = Column(Integer, primary_key=True, autoincrement=True)
#     app_integration_id = Column(Integer, ForeignKey('app_integration.app_integration_id'))
#     doc_title = Column(String(255))
#     doc_url = Column(String(500))
#     uploaded_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))
#     updated_by = Column(Integer, ForeignKey('users.user_id'))

#     @classmethod
#     def create_table(cls, engine):
#         Base.metadata.create_all(engine)

#     @classmethod
#     def drop_table(cls, engine):
#         Base.metadata.drop_all(engine)

#     @classmethod
#     def alter_table(cls, engine):
#         with engine.connect() as connection:
#             connection.execute(text("ALTER TABLE app_documents ADD COLUMN new_column VARCHAR(255);"))

#     @classmethod
#     def insert_table(cls, engine, app_integration_id, doc_title=None, doc_url=None, updated_by=None):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         new_doc = cls(
#             app_integration_id=app_integration_id,
#             doc_title=doc_title,
#             doc_url=doc_url,
#             updated_by=updated_by
#         )
#         session.add(new_doc)
#         session.commit()
#         session.close()

#     @classmethod
#     def update_table(cls, engine, doc_id, **kwargs):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         doc = session.query(cls).filter_by(doc_id=doc_id).first()
#         for key, value in kwargs.items():
#             setattr(doc, key, value)
#         session.commit()
#         session.close()

# class LeadIntegration(Base):
#     __tablename__ = 'leads_integrations'
#     lead_integration_id = Column(Integer, primary_key=True, autoincrement=True)
#     lead_id = Column(Integer, ForeignKey('Leads_details.lead_id'))
#     integration_id = Column(Integer, ForeignKey('integration.integration_id'))
#     app_integration_id = Column(Integer, ForeignKey('app_integration.app_integration_id'))
#     status = Column(ARRAY(Text), default=['active'])
#     created_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))
#     created_by = Column(Integer, ForeignKey('users.user_id'))

#     @classmethod
#     def create_table(cls, engine):
#         Base.metadata.create_all(engine)

#     @classmethod
#     def drop_table(cls, engine):
#         Base.metadata.drop_all(engine)

#     @classmethod
#     def alter_table(cls, engine):
#         with engine.connect() as connection:
#             connection.execute(text("ALTER TABLE leads_integrations ADD COLUMN new_column VARCHAR(255);"))

#     @classmethod
#     def insert_table(cls, engine, lead_id, integration_id, app_integration_id, status=None, created_by=None):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         new_lead_integration = cls(
#             lead_id=lead_id,
#             integration_id=integration_id,
#             app_integration_id=app_integration_id,
#             status=status or ['active'],
#             created_by=created_by
#         )
#         session.add(new_lead_integration)
#         session.commit()
#         session.close()

#     @classmethod
#     def update_table(cls, engine, lead_integration_id, **kwargs):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         lead_integration = session.query(cls).filter_by(lead_integration_id=lead_integration_id).first()
#         for key, value in kwargs.items():
#             setattr(lead_integration, key, value)
#         session.commit()
#         session.close()

# class DocumentCategory(Base):
#     __tablename__ = 'document_categories'
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     document_category_name = Column(String(50), unique=True, nullable=False)

#     @classmethod
#     def create_table(cls, engine):
#         Base.metadata.create_all(engine)

#     @classmethod
#     def drop_table(cls, engine):
#         Base.metadata.drop_all(engine)

#     @classmethod
#     def alter_table(cls, engine):
#         with engine.connect() as connection:
#             connection.execute(text("ALTER TABLE document_categories ADD COLUMN new_column VARCHAR(255);"))

#     @classmethod
#     def insert_table(cls, engine, document_category_name):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         new_category = cls(document_category_name=document_category_name)
#         session.add(new_category)
#         session.commit()
#         session.close()

#     @classmethod
#     def update_table(cls, engine, id, **kwargs):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         category = session.query(cls).filter_by(id=id).first()
#         for key, value in kwargs.items():
#             setattr(category, key, value)
#         session.commit()
#         session.close()

# class DocumentType(Base):
#     __tablename__ = 'Document_Types'
#     document_type_id = Column(Integer, primary_key=True, autoincrement=True)
#     document_type = Column(String(50), unique=True, nullable=False)

#     @classmethod
#     def create_table(cls, engine):
#         Base.metadata.create_all(engine)

#     @classmethod
#     def drop_table(cls, engine):
#         Base.metadata.drop_all(engine)

#     @classmethod
#     def alter_table(cls, engine):
#         with engine.connect() as connection:
#             connection.execute(text("ALTER TABLE Document_Types ADD COLUMN new_column VARCHAR(255);"))

#     @classmethod
#     def insert_table(cls, engine, document_type):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         new_doc_type = cls(document_type=document_type)
#         session.add(new_doc_type)
#         session.commit()
#         session.close()

#     @classmethod
#     def update_table(cls, engine, document_type_id, **kwargs):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         doc_type = session.query(cls).filter_by(document_type_id=document_type_id).first()
#         for key, value in kwargs.items():
#             setattr(doc_type, key, value)
#         session.commit()
#         session.close()

# class Document(Base):
#     __tablename__ = 'Documents'
#     document_id = Column(Integer, primary_key=True, autoincrement=True)
#     document_name = Column(String(255))
#     document_type_id = Column(Integer, ForeignKey('Document_Types.document_type_id'))
#     uploaded_by = Column(Integer, ForeignKey('users.user_id'))
#     uploaded_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))
#     file_url = Column(Text)
#     document_category_name = Column(String(50), ForeignKey('document_categories.document_category_name'))
#     is_archived = Column(Boolean, default=False)
#     last_modified = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))
#     updated_by = Column(Integer, ForeignKey('users.user_id'))
#     doc_related_lead = Column(Integer, ForeignKey('Leads_details.lead_id'))
#     current_version = Column(Integer, default=1)

#     @classmethod
#     def create_table(cls, engine):
#         Base.metadata.create_all(engine)

#     @classmethod
#     def drop_table(cls, engine):
#         Base.metadata.drop_all(engine)

#     @classmethod
#     def alter_table(cls, engine):
#         with engine.connect() as connection:
#             connection.execute(text("ALTER TABLE Documents ADD COLUMN new_column VARCHAR(255);"))

#     @classmethod
#     def insert_table(cls, engine, document_name=None, document_type_id=None, uploaded_by=None, file_url=None, document_category_name=None, is_archived=False, updated_by=None, doc_related_lead=None, current_version=1):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         new_document = cls(
#             document_name=document_name,
#             document_type_id=document_type_id,
#             uploaded_by=uploaded_by,
#             file_url=file_url,
#             document_category_name=document_category_name,
#             is_archived=is_archived,
#             updated_by=updated_by,
#             doc_related_lead=doc_related_lead,
#             current_version=current_version
#         )
#         session.add(new_document)
#         session.commit()
#         session.close()

#     @classmethod
#     def update_table(cls, engine, document_id, **kwargs):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         document = session.query(cls).filter_by(document_id=document_id).first()
#         for key, value in kwargs.items():
#             setattr(document, key, value)
#         session.commit()
#         session.close()

# class DocumentHistory(Base):
#     __tablename__ = 'Documents_History'
#     history_id = Column(Integer, primary_key=True, autoincrement=True)
#     document_id = Column(Integer, ForeignKey('Documents.document_id'))
#     modified_by = Column(Integer, ForeignKey('users.user_id'))
#     modified_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))
#     modification_type = Column(String(50))
#     historical_version = Column(Integer)

#     @classmethod
#     def create_table(cls, engine):
#         Base.metadata.create_all(engine)

#     @classmethod
#     def drop_table(cls, engine):
#         Base.metadata.drop_all(engine)

#     @classmethod
#     def alter_table(cls, engine):
#         with engine.connect() as connection:
#             connection.execute(text("ALTER TABLE Documents_History ADD COLUMN new_column VARCHAR(255);"))

#     @classmethod
#     def insert_table(cls, engine, document_id, modified_by, modification_type, historical_version):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         new_history = cls(
#             document_id=document_id,
#             modified_by=modified_by,
#             modification_type=modification_type,
#             historical_version=historical_version
#         )
#         session.add(new_history)
#         session.commit()
#         session.close()

#     @classmethod
#     def update_table(cls, engine, history_id, **kwargs):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         history = session.query(cls).filter_by(history_id=history_id).first()
#         for key, value in kwargs.items():
#             setattr(history, key, value)
#         session.commit()
#         session.close()

# class DocumentRecentlyViewed(Base):
#     __tablename__ = 'Documents_Recently_Viewed'
#     emp_id = Column(Integer, ForeignKey('Employee_profile_entity.Emp_id'), primary_key=True)
#     document_id = Column(Integer, ForeignKey('Documents.document_id'), primary_key=True)
#     viewed_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))

#     @classmethod
#     def create_table(cls, engine):
#         Base.metadata.create_all(engine)

#     @classmethod
#     def drop_table(cls, engine):
#         Base.metadata.drop_all(engine)

#     @classmethod
#     def alter_table(cls, engine):
#         with engine.connect() as connection:
#             connection.execute(text("ALTER TABLE Documents_Recently_Viewed ADD COLUMN new_column VARCHAR(255);"))

#     @classmethod
#     def insert_table(cls, engine, emp_id, document_id):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         new_view = cls(emp_id=emp_id, document_id=document_id)
#         session.add(new_view)
#         session.commit()
#         session.close()

#     @classmethod
#     def update_table(cls, engine, emp_id, document_id, **kwargs):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         view = session.query(cls).filter_by(emp_id=emp_id, document_id=document_id).first()
#         for key, value in kwargs.items():
#             setattr(view, key, value)
#         session.commit()
#         session.close()

# class DocumentSubCategory(Base):
#     __tablename__ = 'Document_Sub_Categories'
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     document_category_id = Column(Integer, ForeignKey('document_categories.id'))
#     subcategory_name = Column(String(255))
#     created_by = Column(Integer, ForeignKey('users.user_id'))
#     created_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))
#     updated_by = Column(Integer, ForeignKey('users.user_id'))
#     updated_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))

#     @classmethod
#     def create_table(cls, engine):
#         Base.metadata.create_all(engine)

#     @classmethod
#     def drop_table(cls, engine):
#         Base.metadata.drop_all(engine)

#     @classmethod
#     def alter_table(cls, engine):
#         with engine.connect() as connection:
#             connection.execute(text("ALTER TABLE Document_Sub_Categories ADD COLUMN new_column VARCHAR(255);"))

#     @classmethod
#     def insert_table(cls, engine, document_category_id, subcategory_name, created_by=None, updated_by=None):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         new_subcategory = cls(
#             document_category_id=document_category_id,
#             subcategory_name=subcategory_name,
#             created_by=created_by,
#             updated_by=updated_by
#         )
#         session.add(new_subcategory)
#         session.commit()
#         session.close()

#     @classmethod
#     def update_table(cls, engine, id, **kwargs):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         subcategory = session.query(cls).filter_by(id=id).first()
#         for key, value in kwargs.items():
#             setattr(subcategory, key, value)
#         session.commit()
#         session.close()

# class FileData(Base):
#     __tablename__ = 'Files_Data'
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     subcategory_id = Column(Integer, ForeignKey('Document_Sub_Categories.id'))
#     file_data = Column(LargeBinary)
#     file_url = Column(String(255))
#     created_by = Column(Integer, ForeignKey('users.user_id'))
#     created_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))
#     updated_by = Column(Integer, ForeignKey('users.user_id'))
#     updated_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))

#     @classmethod
#     def create_table(cls, engine):
#         Base.metadata.create_all(engine)

#     @classmethod
#     def drop_table(cls, engine):
#         Base.metadata.drop_all(engine)

#     @classmethod
#     def alter_table(cls, engine):
#         with engine.connect() as connection:
#             connection.execute(text("ALTER TABLE Files_Data ADD COLUMN new_column VARCHAR(255);"))

#     @classmethod
#     def insert_table(cls, engine, subcategory_id, file_data=None, file_url=None, created_by=None, updated_by=None):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         new_file_data = cls(
#             subcategory_id=subcategory_id,
#             file_data=file_data,
#             file_url=file_url,
#             created_by=created_by,
#             updated_by=updated_by
#         )
#         session.add(new_file_data)
#         session.commit()
#         session.close()

#     @classmethod
#     def update_table(cls, engine, id, **kwargs):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         file_data = session.query(cls).filter_by(id=id).first()
#         for key, value in kwargs.items():
#             setattr(file_data, key, value)
#         session.commit()
#         session.close()

# class TaskStatus(Base):
#     __tablename__ = 'Task_Status'
#     status_id = Column(Integer, primary_key=True, autoincrement=True)
#     status_name = Column(String(50), unique=True, nullable=False)

#     @classmethod
#     def create_table(cls, engine):
#         Base.metadata.create_all(engine)

#     @classmethod
#     def drop_table(cls, engine):
#         Base.metadata.drop_all(engine)

#     @classmethod
#     def alter_table(cls, engine):
#         with engine.connect() as connection:
#             connection.execute(text("ALTER TABLE Task_Status ADD COLUMN new_column VARCHAR(255);"))

#     @classmethod
#     def insert_table(cls, engine, status_name):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         new_status = cls(status_name=status_name)
#         session.add(new_status)
#         session.commit()
#         session.close()

#     @classmethod
#     def update_table(cls, engine, status_id, **kwargs):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         status = session.query(cls).filter_by(status_id=status_id).first()
#         for key, value in kwargs.items():
#             setattr(status, key, value)
#         session.commit()
#         session.close()

# class TaskPriority(Base):
#     __tablename__ = 'Task_Priority'
#     priority_id = Column(Integer, primary_key=True, autoincrement=True)
#     priority_name = Column(String(50), unique=True, nullable=False)

#     @classmethod
#     def create_table(cls, engine):
#         Base.metadata.create_all(engine)

#     @classmethod
#     def drop_table(cls, engine):
#         Base.metadata.drop_all(engine)

#     @classmethod
#     def alter_table(cls, engine):
#         with engine.connect() as connection:
#             connection.execute(text("ALTER TABLE Task_Priority ADD COLUMN new_column VARCHAR(255);"))

#     @classmethod
#     def insert_table(cls, engine, priority_name):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         new_priority = cls(priority_name=priority_name)
#         session.add(new_priority)
#         session.commit()
#         session.close()

#     @classmethod
#     def update_table(cls, engine, priority_id, **kwargs):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         priority = session.query(cls).filter_by(priority_id=priority_id).first()
#         for key, value in kwargs.items():
#             setattr(priority, key, value)
#         session.commit()
#         session.close()

# class Task(Base):
#     __tablename__ = 'Tasks'
#     task_id = Column(Integer, primary_key=True, autoincrement=True)
#     task_name = Column(String(255))
#     last_date = Column(TIMESTAMP(timezone=True))
#     status_id = Column(Integer, ForeignKey('Task_Status.status_id'))
#     priority_id = Column(Integer, ForeignKey('Task_Priority.priority_id'))
#     related_lead = Column(Integer, ForeignKey('Leads_details.lead_id'))
#     created_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))
#     updated_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))

#     @classmethod
#     def create_table(cls, engine):
#         Base.metadata.create_all(engine)

#     @classmethod
#     def drop_table(cls, engine):
#         Base.metadata.drop_all(engine)

#     @classmethod
#     def alter_table(cls, engine):
#         with engine.connect() as connection:
#             connection.execute(text("ALTER TABLE Tasks ADD COLUMN new_column VARCHAR(255);"))

#     @classmethod
#     def insert_table(cls, engine, task_name=None, last_date=None, status_id=None, priority_id=None, related_lead=None):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         new_task = cls(
#             task_name=task_name,
#             last_date=last_date,
#             status_id=status_id,
#             priority_id=priority_id,
#             related_lead=related_lead
#         )
#         session.add(new_task)
#         session.commit()
#         session.close()

#     @classmethod
#     def update_table(cls, engine, task_id, **kwargs):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         task = session.query(cls).filter_by(task_id=task_id).first()
#         for key, value in kwargs.items():
#             setattr(task, key, value)
#         session.commit()
#         session.close()

# class TaskCompleted(Base):
#     __tablename__ = 'Task_Completed'
#     completed_id = Column(Integer, primary_key=True, autoincrement=True)
#     task_id = Column(Integer, ForeignKey('Tasks.task_id'))
#     completed_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))

#     @classmethod
#     def create_table(cls, engine):
#         Base.metadata.create_all(engine)

#     @classmethod
#     def drop_table(cls, engine):
#         Base.metadata.drop_all(engine)

#     @classmethod
#     def alter_table(cls, engine):
#         with engine.connect() as connection:
#             connection.execute(text("ALTER TABLE Task_Completed ADD COLUMN new_column VARCHAR(255);"))

#     @classmethod
#     def insert_table(cls, engine, task_id):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         new_completed_task = cls(task_id=task_id)
#         session.add(new_completed_task)
#         session.commit()
#         session.close()

#     @classmethod
#     def update_table(cls, engine, completed_id, **kwargs):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         completed_task = session.query(cls).filter_by(completed_id=completed_id).first()
#         for key, value in kwargs.items():
#             setattr(completed_task, key, value)
#         session.commit()
#         session.close()

# class MeetingCallType(Base):
#     __tablename__ = 'Meating_Call_Type'
#     call_type_id = Column(Integer, primary_key=True, autoincrement=True)
#     call_type_name = Column(String(50), unique=True, nullable=False)

#     @classmethod
#     def create_table(cls, engine):
#         Base.metadata.create_all(engine)

#     @classmethod
#     def drop_table(cls, engine):
#         Base.metadata.drop_all(engine)

#     @classmethod
#     def alter_table(cls, engine):
#         with engine.connect() as connection:
#             connection.execute(text("ALTER TABLE Meating_Call_Type ADD COLUMN new_column VARCHAR(255);"))

#     @classmethod
#     def insert_table(cls, engine, call_type_name):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         new_call_type = cls(call_type_name=call_type_name)
#         session.add(new_call_type)
#         session.commit()
#         session.close()

#     @classmethod
#     def update_table(cls, engine, call_type_id, **kwargs):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         call_type = session.query(cls).filter_by(call_type_id=call_type_id).first()
#         for key, value in kwargs.items():
#             setattr(call_type, key, value)
#         session.commit()
#         session.close()

# class MeetingPriorityLevel(Base):
#     __tablename__ = 'meating_Priority_Level'
#     priority_id = Column(Integer, primary_key=True, autoincrement=True)
#     priority_name = Column(String(50), unique=True, nullable=False)

#     @classmethod
#     def create_table(cls, engine):
#         Base.metadata.create_all(engine)

#     @classmethod
#     def drop_table(cls, engine):
#         Base.metadata.drop_all(engine)

#     @classmethod
#     def alter_table(cls, engine):
#         with engine.connect() as connection:
#             connection.execute(text("ALTER TABLE meating_Priority_Level ADD COLUMN new_column VARCHAR(255);"))

#     @classmethod
#     def insert_table(cls, engine, priority_name):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         new_priority = cls(priority_name=priority_name)
#         session.add(new_priority)
#         session.commit()
#         session.close()

#     @classmethod
#     def update_table(cls, engine, priority_id, **kwargs):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         priority = session.query(cls).filter_by(priority_id=priority_id).first()
#         for key, value in kwargs.items():
#             setattr(priority, key, value)
#         session.commit()
#         session.close()

# class Meeting(Base):
#     __tablename__ = 'Meeting'
#     meeting_id = Column(Integer, primary_key=True, autoincrement=True)
#     lead_id = Column(Integer, ForeignKey('Leads_details.lead_id'))
#     call_type_id = Column(Integer, ForeignKey('Meating_Call_Type.call_type_id'))
#     start_time = Column(TIMESTAMP(timezone=True))
#     call_duration = Column(Integer)
#     priority_id = Column(Integer, ForeignKey('meating_Priority_Level.priority_id'))
#     created_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))
#     updated_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))

#     @classmethod
#     def create_table(cls, engine):
#         Base.metadata.create_all(engine)

#     @classmethod
#     def drop_table(cls, engine):
#         Base.metadata.drop_all(engine)

#     @classmethod
#     def alter_table(cls, engine):
#         with engine.connect() as connection:
#             connection.execute(text("ALTER TABLE Meeting ADD COLUMN new_column VARCHAR(255);"))

#     @classmethod
#     def insert_table(cls, engine, lead_id, call_type_id, start_time, call_duration=None, priority_id=None):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         new_meeting = cls(
#             lead_id=lead_id,
#             call_type_id=call_type_id,
#             start_time=start_time,
#             call_duration=call_duration,
#             priority_id=priority_id
#         )
#         session.add(new_meeting)
#         session.commit()
#         session.close()

#     @classmethod
#     def update_table(cls, engine, meeting_id, **kwargs):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         meeting = session.query(cls).filter_by(meeting_id=meeting_id).first()
#         for key, value in kwargs.items():
#             setattr(meeting, key, value)
#         session.commit()
#         session.close()

# class MeetingCompleted(Base):
#     __tablename__ = 'Meetings_Completed'
#     completed_meeting_id = Column(Integer, primary_key=True, autoincrement=True)
#     meeting_id = Column(Integer, ForeignKey('Meeting.meeting_id'))
#     score = Column(Integer)
#     completed_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))
#     employee_id = Column(Integer, ForeignKey('Employee_profile_entity.Emp_id'))

#     @classmethod
#     def create_table(cls, engine):
#         Base.metadata.create_all(engine)

#     @classmethod
#     def drop_table(cls, engine):
#         Base.metadata.drop_all(engine)

#     @classmethod
#     def alter_table(cls, engine):
#         with engine.connect() as connection:
#             connection.execute(text("ALTER TABLE Meetings_Completed ADD COLUMN new_column VARCHAR(255);"))

#     @classmethod
#     def insert_table(cls, engine, meeting_id, score=None, employee_id=None):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         new_completed_meeting = cls(
#             meeting_id=meeting_id,
#             score=score,
#             employee_id=employee_id
#         )
#         session.add(new_completed_meeting)
#         session.commit()
#         session.close()

#     @classmethod
#     def update_table(cls, engine, completed_meeting_id, **kwargs):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         completed_meeting = session.query(cls).filter_by(completed_meeting_id=completed_meeting_id).first()
#         for key, value in kwargs.items():
#             setattr(completed_meeting, key, value)
#         session.commit()
#         session.close()

# class Calendar(Base):
#     __tablename__ = 'Calendar'
#     calendar_id = Column(Integer, primary_key=True, autoincrement=True)
#     event_type_id = Column(Integer)
#     activity_id = Column(Integer)
#     title = Column(String(255))
#     description = Column(Text)
#     start_time = Column(TIMESTAMP(timezone=True))
#     end_time = Column(TIMESTAMP(timezone=True))
#     priority_id = Column(Integer)
#     status_id = Column(Integer, default=1)
#     created_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))
#     updated_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))

#     @classmethod
#     def create_table(cls, engine):
#         Base.metadata.create_all(engine)

#     @classmethod
#     def drop_table(cls, engine):
#         Base.metadata.drop_all(engine)

#     @classmethod
#     def alter_table(cls, engine):
#         with engine.connect() as connection:
#             connection.execute(text("ALTER TABLE Calendar ADD COLUMN new_column VARCHAR(255);"))

#     @classmethod
#     def insert_table(cls, engine, event_type_id=None, activity_id=None, title=None, description=None, start_time=None, end_time=None, priority_id=None, status_id=1):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         new_calendar = cls(
#             event_type_id=event_type_id,
#             activity_id=activity_id,
#             title=title,
#             description=description,
#             start_time=start_time,
#             end_time=end_time,
#             priority_id=priority_id,
#             status_id=status_id
#         )
#         session.add(new_calendar)
#         session.commit()
#         session.close()

#     @classmethod
#     def update_table(cls, engine, calendar_id, **kwargs):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         calendar = session.query(cls).filter_by(calendar_id=calendar_id).first()
#         for key, value in kwargs.items():
#             setattr(calendar, key, value)
#         session.commit()
#         session.close()

# class MeetingStatus(Base):
#     __tablename__ = 'Meating_Status'
#     status_id = Column(Integer, primary_key=True, autoincrement=True)
#     status_name = Column(String(50), unique=True, nullable=False)

#     @classmethod
#     def create_table(cls, engine):
#         Base.metadata.create_all(engine)

#     @classmethod
#     def drop_table(cls, engine):
#         Base.metadata.drop_all(engine)

#     @classmethod
#     def alter_table(cls, engine):
#         with engine.connect() as connection:
#             connection.execute(text("ALTER TABLE Meating_Status ADD COLUMN new_column VARCHAR(255);"))

#     @classmethod
#     def insert_table(cls, engine, status_name):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         new_status = cls(status_name=status_name)
#         session.add(new_status)
#         session.commit()
#         session.close()

#     @classmethod
#     def update_table(cls, engine, status_id, **kwargs):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         status = session.query(cls).filter_by(status_id=status_id).first()
#         for key, value in kwargs.items():
#             setattr(status, key, value)
#         session.commit()
#         session.close()

# class MeetingEventType(Base):
#     __tablename__ = 'Meating_Event_Type'
#     event_type_id = Column(Integer, primary_key=True, autoincrement=True)
#     event_type_name = Column(String(50), unique=True, nullable=False)

#     @classmethod
#     def create_table(cls, engine):
#         Base.metadata.create_all(engine)

#     @classmethod
#     def drop_table(cls, engine):
#         Base.metadata.drop_all(engine)

#     @classmethod
#     def alter_table(cls, engine):
#         with engine.connect() as connection:
#             connection.execute(text("ALTER TABLE Meating_Event_Type ADD COLUMN new_column VARCHAR(255);"))

#     @classmethod
#     def insert_table(cls, engine, event_type_name):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         new_event_type = cls(event_type_name=event_type_name)
#         session.add(new_event_type)
#         session.commit()
#         session.close()

#     @classmethod
#     def update_table(cls, engine, event_type_id, **kwargs):
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         event_type = session.query(cls).filter_by(event_type_id=event_type_id).first()
#         for key, value in kwargs.items():
#             setattr(event_type, key, value)
#         session.commit()
#         session.close()

# Base.metadata.create_all(engine)

# if __name__ == '__main__':
#     print("Tables created successfully.")