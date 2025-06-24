import os
import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import sqlalchemy as sa
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import JSON

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL')

# Create engine with SSL configuration for Replit
if DATABASE_URL:
    # Add SSL configuration for Replit's database
    engine = create_engine(
        DATABASE_URL,
        connect_args={"sslmode": "require"} if DATABASE_URL.startswith('postgresql') else {}
    )
else:
    engine = None

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None
Base = declarative_base()

class Dataset(Base):
    __tablename__ = "datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    rows_count = Column(Integer)
    columns_count = Column(Integer)
    columns_info = Column(JSON)  # Store column names and types
    file_size = Column(Integer)  # File size in bytes
    description = Column(Text)

class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, sa.ForeignKey("datasets.id"))
    session_name = Column(String(255))
    created_date = Column(DateTime, default=datetime.utcnow)
    filters_applied = Column(JSON)  # Store applied filters
    demographic_targets = Column(JSON)  # Store target percentages
    analysis_results = Column(JSON)  # Store calculated results
    notes = Column(Text)

class DataRecord(Base):
    __tablename__ = "data_records"
    
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, sa.ForeignKey("datasets.id"))
    grade = Column(String(50))
    entity_desc = Column(Text)
    component_desc = Column(String(255))
    total = Column(Integer)
    demographic_data = Column(JSON)  # Store all demographic columns as JSON
    row_index = Column(Integer)  # Original row number from uploaded file

class DatabaseManager:
    def __init__(self):
        self.engine, self.SessionLocal = create_db_connection()
        self.available = self.engine is not None and self.SessionLocal is not None
        
        if not self.available:
            raise Exception("Database connection unavailable - running in memory mode")
        
    def init_db(self):
        """Initialize database tables"""
        if not self.available:
            raise Exception("Database not available - DATABASE_URL not configured")
        
        try:
            Base.metadata.create_all(bind=self.engine)
        except Exception as e:
            raise Exception(f"Failed to initialize database: {str(e)}")
    
    def save_dataset(self, df: pd.DataFrame, filename: str, name: str = None, description: str = None) -> int:
        """
        Save a dataset to the database
        
        Args:
            df: DataFrame to save
            filename: Original filename
            name: Display name for dataset
            description: Optional description
            
        Returns:
            Dataset ID
        """
        if not self.available:
            raise Exception("Database not available")
            
        if name is None:
            name = filename.split('.')[0]
            
        # Prepare columns info
        columns_info = {}
        for col in df.columns:
            columns_info[col] = {
                'dtype': str(df[col].dtype),
                'non_null_count': int(df[col].count()),
                'unique_count': int(df[col].nunique())
            }
        
        # Create dataset record
        with self.SessionLocal() as session:
            dataset = Dataset(
                name=name,
                filename=filename,
                rows_count=len(df),
                columns_count=len(df.columns),
                columns_info=columns_info,
                description=description
            )
            session.add(dataset)
            session.commit()
            session.refresh(dataset)
            dataset_id = dataset.id
            
            # Save individual records
            self._save_data_records(session, df, dataset_id)
            session.commit()
            
        return dataset_id
    
    def _save_data_records(self, session, df: pd.DataFrame, dataset_id: int):
        """Save individual data records"""
        # Identify demographic columns
        demographic_patterns = ['AAM', 'AAF', 'PCM', 'PCF', 'LGBTF', 'LGBTM', 
                               'OTHER_M', 'OTHER_F', 'WM', 'WF', 'HM', 'HF', 
                               'AM', 'AF', 'NAM', 'NAF']
        
        for idx, row in df.iterrows():
            # Extract demographic data
            demographic_data = {}
            for col in df.columns:
                if (col.upper() in demographic_patterns or 
                    any(pattern in col.upper() for pattern in ['_M', '_F', 'MALE', 'FEMALE'])):
                    if col != 'TOTAL':
                        demographic_data[col] = float(row[col]) if pd.notna(row[col]) else 0.0
            
            # Create data record
            record = DataRecord(
                dataset_id=dataset_id,
                grade=str(row.get('Grade', '')),
                entity_desc=str(row.get('EntityDesc', '')),
                component_desc=str(row.get('Component Desc', '')),
                total=int(row.get('TOTAL', 0)) if pd.notna(row.get('TOTAL')) else 0,
                demographic_data=demographic_data,
                row_index=idx
            )
            session.add(record)
    
    def get_datasets(self) -> List[Dict]:
        """Get list of all datasets"""
        if not self.available:
            return []
        with self.SessionLocal() as session:
            datasets = session.query(Dataset).order_by(Dataset.upload_date.desc()).all()
            return [
                {
                    'id': d.id,
                    'name': d.name,
                    'filename': d.filename,
                    'upload_date': d.upload_date,
                    'rows_count': d.rows_count,
                    'columns_count': d.columns_count,
                    'description': d.description
                }
                for d in datasets
            ]
    
    def get_dataset_by_id(self, dataset_id: int) -> Optional[Dict]:
        """Get dataset information by ID"""
        with self.SessionLocal() as session:
            dataset = session.query(Dataset).filter(Dataset.id == dataset_id).first()
            if dataset:
                return {
                    'id': dataset.id,
                    'name': dataset.name,
                    'filename': dataset.filename,
                    'upload_date': dataset.upload_date,
                    'rows_count': dataset.rows_count,
                    'columns_count': dataset.columns_count,
                    'columns_info': dataset.columns_info,
                    'description': dataset.description
                }
        return None
    
    def load_dataset_data(self, dataset_id: int) -> pd.DataFrame:
        """Load dataset data as DataFrame"""
        with self.SessionLocal() as session:
            records = session.query(DataRecord).filter(DataRecord.dataset_id == dataset_id).all()
            
            if not records:
                return pd.DataFrame()
            
            # Convert to DataFrame
            data = []
            for record in records:
                row_data = {
                    'Grade': record.grade,
                    'EntityDesc': record.entity_desc,
                    'Component Desc': record.component_desc,
                    'TOTAL': record.total
                }
                # Add demographic data
                if record.demographic_data:
                    row_data.update(record.demographic_data)
                
                data.append(row_data)
            
            return pd.DataFrame(data)
    
    def save_analysis_session(self, dataset_id: int, session_name: str, 
                            filters_applied: Dict, demographic_targets: Dict,
                            analysis_results: Dict, notes: str = None) -> int:
        """Save an analysis session"""
        with self.SessionLocal() as session:
            analysis = AnalysisSession(
                dataset_id=dataset_id,
                session_name=session_name,
                filters_applied=filters_applied,
                demographic_targets=demographic_targets,
                analysis_results=analysis_results,
                notes=notes
            )
            session.add(analysis)
            session.commit()
            session.refresh(analysis)
            return analysis.id
    
    def get_analysis_sessions(self, dataset_id: int = None) -> List[Dict]:
        """Get analysis sessions, optionally filtered by dataset"""
        with self.SessionLocal() as session:
            query = session.query(AnalysisSession)
            if dataset_id:
                query = query.filter(AnalysisSession.dataset_id == dataset_id)
            
            sessions = query.order_by(AnalysisSession.created_date.desc()).all()
            return [
                {
                    'id': s.id,
                    'dataset_id': s.dataset_id,
                    'session_name': s.session_name,
                    'created_date': s.created_date,
                    'filters_applied': s.filters_applied,
                    'demographic_targets': s.demographic_targets,
                    'notes': s.notes
                }
                for s in sessions
            ]
    
    def delete_dataset(self, dataset_id: int) -> bool:
        """Delete a dataset and all related records"""
        with self.SessionLocal() as session:
            # Delete analysis sessions
            session.query(AnalysisSession).filter(
                AnalysisSession.dataset_id == dataset_id
            ).delete()
            
            # Delete data records
            session.query(DataRecord).filter(
                DataRecord.dataset_id == dataset_id
            ).delete()
            
            # Delete dataset
            deleted = session.query(Dataset).filter(Dataset.id == dataset_id).delete()
            session.commit()
            
            return deleted > 0
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        if not self.available:
            return {'total_datasets': 0, 'total_records': 0, 'total_analyses': 0}
        with self.SessionLocal() as session:
            dataset_count = session.query(Dataset).count()
            total_records = session.query(DataRecord).count()
            analysis_count = session.query(AnalysisSession).count()
            
            return {
                'total_datasets': dataset_count,
                'total_records': total_records,
                'total_analyses': analysis_count
            }

# Global database manager instance
db_manager = DatabaseManager()